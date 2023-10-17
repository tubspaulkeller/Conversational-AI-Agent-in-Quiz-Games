from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted
from actions.game.gamemodehandler import GameModeHandler
from actions.common.common import get_requested_slot, async_connect_to_db,get_dp_inmemory_db, get_random_person, setup_logging
from actions.common.reset import reset_points
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.session.sessionhandler import SessionHandler 
from actions.groups.grouphandler import GroupHandler
import asyncio
from rasa_sdk.events import (
    UserUtteranceReverted,
    FollowupAction,
    AllSlotsReset,
    Restarted,
    SlotSet,
    EventType,
)
import logging
logger = setup_logging()
class ActionLeaderboard(Action):
    def name(self) -> Text:
        return "action_winner"

    async def run(self, dispatcher, tracker, domain):
        try:
            if tracker.get_slot("winner") is None:
                session_handler = SessionHandler()
                competition_mode_handler = CompetitionModeHandler()
                filter = session_handler.get_session_filter(tracker)
                game_modus = tracker.get_slot("game_modus")
                # sende Siegererhung bild über Bot
                badges = get_dp_inmemory_db("./badges.json")
                print("warten...")
                await asyncio.sleep(4)

                # Stern 

                await competition_mode_handler.increase_stars(filter)
                if game_modus == 'quiz_form_OKK':
                    text = "Super gemacht! Du hast das Quiz geschafft! Du verdienst dir einen weiteren Stern! 🌟"
                else:
                    text = "Super gemacht! Ihr habt das Quiz geschafft! Ihr verdient euch einen weiteren Stern! 🌟"
                await competition_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)

                if game_modus == 'quiz_form_KLMK' or game_modus == 'quiz_form_KLOK':
                    await competition_mode_handler.telegram_bot_send_message('photo', tracker.sender_id, badges['SIEGEREHRUNG'])

                else: 
                    await competition_mode_handler.telegram_bot_send_message('photo', tracker.sender_id, badges['ENDE_SPIELTAG'])
                # waiting bcs of sended resultbadge
                await asyncio.sleep(1)
                if game_modus == 'quiz_form_KLOK' or  game_modus == 'quiz_form_OKK':
                    await competition_mode_handler.telegram_bot_send_message('text', tracker.sender_id, "Ich berechne eben den Punktestand...")
                else:
                    await competition_mode_handler.telegram_bot_send_message('text', tracker.sender_id, "Ich berechne eben den Punktestand...\nAnschließend gebe ich euch noch Feedback zu eurem festgelegten Ziel.")
                await asyncio.sleep(4)
                await competition_mode_handler.bot.unpin_all_chat_messages(tracker.sender_id)

                if game_modus == 'quiz_form_OKK':
                    random_user_username=""
                else:
                    group_handler = GroupHandler()
                    random_user = get_random_person(tracker.get_slot("my_group"))
                    random_user_username = random_user['username']

                if game_modus ==  'quiz_form_KLMK' or game_modus == 'quiz_form_KLOK':
                    winner = await competition_mode_handler.get_winner(filter['channel_id'], filter['other_group'], dispatcher)   
                else:
                    winner = "mygroup"
                
                btn_lst = [{"title": "Spieltaganalyse 📊", "payload": "/leaderboard"}]
                dispatcher.utter_message(text="👋 %s bitte drücke den Button, um zur Spieltagsanalyse zu kommen."%random_user_username, buttons=btn_lst)  

                return [SlotSet("winner", winner)]
            else:
                return
        except Exception as e: 
            
            logger.exception(e)