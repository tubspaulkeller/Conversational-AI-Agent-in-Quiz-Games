from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
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
from actions.common.common import get_credentials, async_connect_to_db
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.gamification.countdown.countdown import Countdown
from actions.timestamps.timestamphandler import TimestampHandler
from actions.timestamps.timestamp import Timestamp
from actions.session.sessionhandler import SessionHandler
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.session.sessionhandler import SessionHandler
from actions.quests.question import Question
import logging
logger = logging.getLogger(__name__)

class MultipleResponseQuest:
    def __init__(self, quest_id):
        self.quest_id = quest_id
        self.db = get_credentials("DB_NAME")

    async def get_quest(self):
            collection = async_connect_to_db(self.db, 'Questions')
            filter = {"question_id": self.quest_id}
            question = await collection.find_one(filter)
            return question

    def create_btns_for_single_choice(self, question_object):
        """Returns an array of Buttons for all the answers of the selected question
        """
        try:
            btn_lst = []
            abc = ["A", "B", "C", "D", "E", "F"]
            btn_action = '/multiple_response_quest{"multiple_response_quest":'
            wrong_correct = ['"wrong"', '"correct"']
            for v in range(len(question_object["answer"])):
                btn_actionv = btn_action + (wrong_correct[0] if int(question_object['answer'][v][1]) == 0 else wrong_correct[1]) + '}'
                btn = {"title": abc[v],
                        "payload": btn_actionv}
                btn_lst.append(btn)
            return btn_lst
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e) 

    
    def create_btns_for_multiple_choice(self, question_object):
        """Returns an array of Buttons for all the answers of the selected question
        """
        try:
            btn_lst = []
            abc = ["A", "B", "C", "D", "E", "F"]
            btn_action = '/multiple_response_quest{"multiple_response_quest":'
            wrong_correct = ['"wrong"', '"correct"']
            for combination in range(len(question_object["button_combination"])):
                btn_actionv = btn_action + (wrong_correct[0] if int(question_object['button_combination'][combination][-1]) == 0 else wrong_correct[1]) + '}'
                btn = {"title": ", ".join(question_object['button_combination'][combination][:-1]),
                        "payload": btn_actionv}
                btn_lst.append(btn)
            return btn_lst
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e) 
    

    def create_text_for_question(self, question_object,display):
        """Returns a string with the question and all the answers correctly formatted"""
        text_lst = [display]

        for v in question_object["answer"]:
            text_lst.append(v[0])
        return "\n".join(text_lst)

    async def run_question(self, tracker):
        try: 
            if tracker.get_slot("flag") is None: 
                competition_mode_handler = CompetitionModeHandler() 
                session_handler = SessionHandler()
                filter = {
                    "channel_id": tracker.sender_id,
                    "other_group": session_handler.get_opponent(tracker)
                }
                active_loop = tracker.active_loop.get('name') 
                # check if session exists, otherwise create a new session 
                if await session_handler.exist_session(filter, active_loop, tracker.sender_id, tracker.get_slot("my_group")):               
                    ''' create countdown '''
                    countdown = Countdown(tracker.sender_id, self.quest_id, active_loop)
                    countdownhandler = CountdownHandler()
                    
                    ''' get the session entry of the group/user'''
                    session_object = await session_handler.session_collection.find_one(filter)
                    if len(session_object['questions']) == 0 or not await competition_mode_handler.check_status('evaluated', self.quest_id, filter, competition_mode_handler.session_collection):    
                        quest_object = Question(self.quest_id, 0, None).to_dict()
                        questions = session_object['questions']
                        questions.append(quest_object)
                        update_questions = {
                            "$set": {
                                "questions": questions
                            }
                        }
                        await session_handler.session_collection.update_one(filter, update_questions)
                    
                    ''' get the question for quiz'''
                    question =await self.get_quest()          
                    display = question["display_question"]

                    if self.quest_id[-1] == 'o':
                        display_question=display
                    else:
                        display_question = self.create_text_for_question(question, display)

                    
                    ''' display handling for the question'''
                    loop = '_'.join(active_loop.split('_')[2:])
                    number_of_team_mates = 0
                    if loop == 'KLOK':
                        number_of_team_mates=len(tracker.get_slot('my_group')['users'])

                    message_id = await countdownhandler.send_countdown_mesage(countdown, display_question, loop, session_object, self.quest_id, tracker.sender_id, number_of_team_mates)
                    countdown.message_id = message_id
                    countdown.question = question
                    await countdownhandler.pin_countdown_message(countdown)

                    ''' insert a timestamp into db '''
                    timestamp_handler = TimestampHandler()
                    new_timestamp = Timestamp(tracker.sender_id, self.quest_id, active_loop, filter['other_group']).to_dict()
                    timestamp_handler.insert_new_timestamp(new_timestamp, 'waiting')
                    return [SlotSet("flag", True), SlotSet("game_modus", active_loop), SlotSet("countdown",countdown.to_dict()), SlotSet("opponent_id", filter['other_group']), FollowupAction("action_set_reminder_countdown_msg")]

                else:
                    print("\033[94mSESSION OBJECT DOES NOT EXIST\033[0m")

                    return [FollowupAction("action_restart")]

            else:
               # print("Slot question %s: None" %self.quest_id)
                return []
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e) 