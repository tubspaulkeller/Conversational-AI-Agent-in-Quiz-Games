from rasa_sdk.events import (
    UserUtteranceReverted,
    FollowupAction,
    AllSlotsReset,
    Restarted,
    SlotSet,
    EventType,
)
import datetime
import asyncio
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.gamification.countdown.countdown import Countdown
from actions.timestamps.timestamphandler import TimestampHandler
from actions.timestamps.timestamp import Timestamp
from actions.quests.question import Question
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.session.sessionhandler import SessionHandler
import logging
logger = logging.getLogger(__name__)

async def send_countdown_task(object, tracker):
    try:
        session_handler = SessionHandler()
        competition_mode_handler = CompetitionModeHandler() 
        countdownhandler = CountdownHandler()
        if tracker.get_slot("flag") is None: 
            filter = {
                    "channel_id": tracker.sender_id,
                    "other_group": session_handler.get_opponent(tracker)
            }
            active_loop = tracker.active_loop.get('name') 

            if await session_handler.exist_session(filter, active_loop, tracker.sender_id, tracker.get_slot("my_group")):  
                ''' set countdown '''
                countdown = Countdown(tracker.sender_id, object['id'], active_loop)
                session_object = await session_handler.session_collection.find_one(filter)
                if len(session_object['questions']) == 0 or not await competition_mode_handler.check_status('evaluated', object['id'], filter, competition_mode_handler.session_collection):    
                    questions = session_object['questions']
                    questions.append(object)
                    update_questions = {
                        "$set": {
                            "questions": questions
                        }
                    }
                    await session_handler.session_collection.update_one(filter, update_questions)

                ''' display handling for text'''
                countdown.text = object['text']
                countdown.question = object['task']
                message_id = await countdownhandler.send_waiting_countdown_message(countdown)
                countdown.message_id = message_id
                if isinstance(object, dict) and 'buttons' in object:
                    countdown.buttons = object['buttons']

                await countdownhandler.pin_countdown_message(countdown)

                ''' insert a timestamp into db '''
                timestamp_handler = TimestampHandler()
                new_timestamp = Timestamp(tracker.sender_id, object['id'], active_loop, filter['other_group']).to_dict()
                timestamp_handler.insert_new_timestamp(new_timestamp, 'waiting')
                return [SlotSet("flag", True), SlotSet("game_modus", active_loop), SlotSet("countdown",countdown.to_dict()), SlotSet("opponent_id", filter['other_group']), FollowupAction("action_set_reminder_countdown_msg")]

            else:
                print("\033[94mSESSION OBJECT DOES NOT EXIST\033[0m")
                return [FollowupAction("action_restart")]
        else:
                #print("None")
                return []
    except Exception as e:
        logger.exception("\033[91Exception: %s\033[0m" %e) 




    