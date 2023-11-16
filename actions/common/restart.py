import asyncio
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted, SlotSet, ReminderCancelled
from actions.game.gamemodehandler import GameModeHandler
from actions.common.common import async_connect_to_db, setup_logging, get_random_person
from actions.common.reset import reset_points
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.session.sessionhandler import SessionHandler
from actions.users.klokanswerhandler import KlokAnswersHandler
import logging
logger = setup_logging()

async def delete_session_in_db(tracker): 
    '''
    delete entry in session table
    '''
    session_handler = SessionHandler()
    game_modus = tracker.get_slot("game_modus")
    if game_modus is None:
        session = await session_handler.session_collection.find_one({"channel_id": tracker.sender_id})
        if session:
            game_modus =  "quiz_form_%s"%session['questions'][0]['modus']
        else:
            return
    await session_handler.session_collection.delete_one({"channel_id": tracker.sender_id})

    ''' 
    delete timestamps for specifc group
    '''
    timestamp_hanlder = TimestampHandler()
    await timestamp_hanlder.delete_timestamps_for_group(tracker.sender_id, 'answer')
    await timestamp_hanlder.delete_timestamps_for_group(tracker.sender_id, 'waiting')

    # delete Kollaboration
    if game_modus == "quiz_form_KL" or game_modus == "quiz_form_KLMK":
        collab_filter = {
        "group_id": int(tracker.sender_id)     
        }
        countdown_handler = CountdownHandler()
        await countdown_handler.collab_collection.delete_one(collab_filter)  


    # delete KLOK ARRAY
    if game_modus == 'quiz_form_KLOK':
        klok_handler = KlokAnswersHandler()
        klok_handler.clear_group_answers(tracker.sender_id)


class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    async def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Neues 🎮 wird gestartet...🤖")
        await delete_session_in_db(tracker)
        return [AllSlotsReset(), Restarted(), FollowupAction("action_send_greet")]



class ActionNewGame(Action):
    def name(self) -> Text:
        return "action_new_game"

    async def run(self, dispatcher, tracker, domain):
        btn_lst = [
            {"title": "Let's go, neues Spiel 🎮✨",
                "payload": "/i_restart_conversation"}
        ]
        text = "Neues Spiel starten 🕹️?"
        await asyncio.sleep(3)
        dispatcher.utter_message(text=text, buttons=btn_lst)

class ActionPrevQuestAgain(Action):
    def name(self) -> Text:
        return "action_prev_quest_again"

    async def run(self, dispatcher, tracker, domain):
        try: 
            session_handler = SessionHandler()
            channel_id = tracker.sender_id
            prev_quest = None 
            session = await session_handler.session_collection.find_one({"channel_id": channel_id})
            if session:
                loop =  tracker.get_slot("game_modus")
                game_mode = '_'.join(loop.split('_')[2:])
                if len(session['questions']) >= 1:
                    mode = session['questions'][0]['modus'] 
                else: 
                    mode = game_mode         
                filter = {
                    "channel_id": channel_id,     
                    "other_group": session.get('other_group')  
                } 
                if len(session['questions']) >= 1:
                    prev_quest = await update_session(session, session_handler,channel_id, filter, -1)
                else:
                    return
            else:
                return             
            loop = "quiz_form_" + mode if mode else None
            prev_quest = mode + "_" + prev_quest
            print("PREVQUEST", prev_quest)
            if mode == 'KLMK' or mode == 'KLOK':
                return [SlotSet(prev_quest, None), SlotSet("%s_competition"%prev_quest, None), SlotSet("winner", None), SlotSet("random_person", None),SlotSet("activated_reminder_comp", None), SlotSet("flag", None), SlotSet("countdown", None), SlotSet("answered", None), SlotSet("waiting_countdown", None), ReminderCancelled(name="reminder_group_%s" % tracker.sender_id),ReminderCancelled(name="reminder_comp_group_%s" % tracker.sender_id), FollowupAction(loop)]
            else: 
                return [SlotSet(prev_quest, None), SlotSet("random_person", None), SlotSet("flag", None), SlotSet("countdown", None), SlotSet("answered", None), SlotSet("waiting_countdown", None), ReminderCancelled(name="reminder_group_%s" % tracker.sender_id), FollowupAction(loop)]

        except Exception as e:
            logger.exception(e)


async def update_session(session, session_handler,channel_id, filter, index):
    try:
        prev_quest = session['questions'][index]['id']
        points =  session['questions'][index].get('points', 0)
        old_total_points = session['total_points'] - points
        level = session.get('level', 0)
        max_points = await session_handler.max_points()
        
        if old_total_points < 7: 
            level = 0
        elif old_total_points < (max_points - 53):
            level = 1
        elif old_total_points < (max_points - 43):
            level = 2
        elif old_total_points < (max_points - 22):
            level = 3
        elif old_total_points < max_points:
            level = 4
        # delete last quest entry in list of session entry in DB
        for index, question in reversed(list(enumerate(session['questions']))):
            if question['id'] == prev_quest:
                # delete quest entry in session
                set_update = {
                    "$set": {
                        "total_points": old_total_points,
                        "stars": 1,
                        "level": level
                    }
                }
                await session_handler.session_collection.update_one(filter, set_update)

                pull_update = {
                    "$pull": {"questions": {"id": prev_quest}}
                }
                await session_handler.session_collection.update_one(filter, pull_update)

        
        return prev_quest
    except Exception as e:
        logger.exception(e)