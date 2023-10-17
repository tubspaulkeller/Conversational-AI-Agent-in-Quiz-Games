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
# get custom actions
from actions.quests.multipleresponsequest import MultipleResponseQuest
from actions.quests.send_countdown_task import send_countdown_task
from actions.quests.introduction import Introduction
from actions.quests.teamname import TeamName
from actions.common.common import print_current_tracker_state,get_requested_slot, setup_logging
from actions.goal.goal import Goal
from actions.game.gamemodehandler import GameModeHandler
from actions.session.sessionhandler import SessionHandler
import logging
logger = setup_logging()


class GiveIntroduction(Action):
    def name(self) -> Text:
        return "action_ask_introduction"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set ready status, users are ready if they read the instruction'''
        try:
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                modus = '_'.join(active_loop.split('_')[2:])
                introduction = Introduction(modus = modus)
                return await send_countdown_task(introduction.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class GiveTeamName(Action):
    def name(self) -> Text:
        return "action_ask_team_name"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' '''
        try:
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                slot_id = "team_name"
                if not active_loop == "quiz_form_OKK":
                    is_group = True 
                else: 
                    is_group = False
                team_name = TeamName(is_group,slot_id)
                return await send_countdown_task(team_name.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class CompetiveGoal(Action):
    def name(self) -> Text:
        return "action_ask_competive_goal"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set goal '''
        try:
            if tracker.get_slot("flag") is None: 
                slot_id = "competive_goal"
                is_group = False
                goal = Goal(is_group, slot_id)
                return await send_countdown_task(goal.to_dict(), tracker)
        except Exception as e:
            logger.exception(e)

class NonCompetiveGoal(Action):
    def name(self) -> Text:
        return "action_ask_non_competive_goal"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set goal '''
        try:
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                slot_id = "non_competive_goal"
                if not active_loop == "quiz_form_OKK":
                    is_group = True 
                else: 
                    is_group = False
                goal = Goal(is_group, slot_id)
                return await send_countdown_task(goal.to_dict(), tracker)
        except Exception as e:
            logger.exception(e)

class Quest01(Action):
    def name(self) -> Text:
        return "action_ask_frage_01_s"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' get ID of current question'''
   
        if tracker.get_slot("flag") is None: 
            active_loop = tracker.active_loop.get('name') 
            game_mode_handler = GameModeHandler()
            session_handler = SessionHandler()
            filter = session_handler.get_session_filter(tracker)
            await game_mode_handler.increase_stars(filter)
            if active_loop == 'quiz_form_OKK':
                text = "Super gemacht! Du hast die Einleitung geschafft! Du verdienst dir einen Stern! 🌟"
            else:
                text = "Super gemacht! Ihr habt die Einleitung geschafft! Ihr verdient euch einen Stern! 🌟"
            await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
            
            quest_id = "frage_01_s" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)


class Quest02(Action):
    def name(self) -> Text:
        return "action_ask_frage_02_s"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        if tracker.get_slot("flag") is None: 
            quest_id = "frage_02_s" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)

class Quest03(Action):
    def name(self) -> Text:
        return "action_ask_frage_03_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        if tracker.get_slot("flag") is None: 
            quest_id = "frage_03_m" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)


class Quest04(Action):
    def name(self) -> Text:
        return "action_ask_frage_04_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        if tracker.get_slot("flag") is None: 
            quest_id = "frage_04_m" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)


class Quest05(Action):
    def name(self) -> Text:
        return "action_ask_frage_05_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        if tracker.get_slot("flag") is None: 
            quest_id = "frage_05_o" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)


class Quest06(Action):
    def name(self) -> Text:
        return "action_ask_frage_06_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        if tracker.get_slot("flag") is None: 
            quest_id = "frage_06_o" 
            multiple_response_quest = MultipleResponseQuest(quest_id)
            return await multiple_response_quest.run_question(tracker)
