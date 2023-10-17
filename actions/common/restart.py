from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted
from actions.game.gamemodehandler import GameModeHandler
from actions.common.common import get_requested_slot, async_connect_to_db, setup_logging
from actions.common.reset import reset_points
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.session.sessionhandler import SessionHandler
from actions.users.klokanswerhandler import KlokAnswersHandler
import logging
logger = setup_logging()

class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    async def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Neues 🎮 wird gestartet...🤖")
        '''
        delete entry in session table
        '''
        session_handler = SessionHandler()
        game_modus = tracker.get_slot("game_modus") 
        
        #if not game_modus is None: 
        session_filter = session_handler.get_session_filter(tracker)
        await session_handler.session_collection.delete_one(session_filter)   

        ''' 
        delete timestamps for specifc group
        '''
        timestamp_hanlder = TimestampHandler()
        timestamp_hanlder.delete_timestamps_for_group(tracker.sender_id, 'answer')
        timestamp_hanlder.delete_timestamps_for_group(tracker.sender_id, 'waiting')

        # delete KLOK ARRAY 

        if game_modus == 'quiz_form_KLOK':
            klok_handler = KlokAnswersHandler()
            klok_handler.clear_group_answers(tracker.sender_id)

        return [AllSlotsReset(), Restarted(), FollowupAction("action_send_greet")]


        