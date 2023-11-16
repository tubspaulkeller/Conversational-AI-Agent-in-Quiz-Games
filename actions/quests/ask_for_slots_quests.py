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
from actions.common.common import print_current_tracker_state, setup_logging
from actions.goal.goal import Goal
from actions.game.gamemodehandler import GameModeHandler
from actions.session.sessionhandler import SessionHandler
import logging
logger = setup_logging()



def set_reminder_comp(tracker):
    try:
        if tracker.get_slot("activated_reminder_comp") is None:
            return [SlotSet("activated_reminder_comp", True), FollowupAction("action_set_reminder_competition")]

    except Exception as e:
        logger.exception(e) 

####### KLOK ###### 

class KLOKGiveIntroduction(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_introduction"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set ready status, users are ready if they read the instruction'''
        try:
            active_loop = tracker.active_loop.get('name') 
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                modus = '_'.join(active_loop.split('_')[2:])
                introduction = Introduction(modus = modus)
                return await send_countdown_task(introduction.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 

class KLOKIntroductionCompetition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_introduction_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLOKQuest01(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_01_s"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                game_mode_handler = GameModeHandler()
                session_handler = SessionHandler()
                filter = session_handler.get_session_filter(tracker)
                session = await session_handler.get_session_object(tracker)
                stars = session.get('stars') if session is not None else 0
                if stars == 0: 
                    await game_mode_handler.increase_stars(filter)
                    text = "Super gemacht! Ihr habt die Einleitung geschafft! Ihr verdient euch einen Stern! 🌟"
                    await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
                quest_id = "frage_01_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLOKFrage01Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_01_s_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLOKQuest02(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_02_s"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_02_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLOKFrage02Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_02_s_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLOKQuest03(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_03_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_03_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLOKFrage03Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_03_m_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLOKQuest04(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_04_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_04_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLOKFrage04Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_04_m_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLOKQuest05(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_05_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_05_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLOKFrage05Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_05_o_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLOKQuest06(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_06_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_06_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLOKFrage06Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLOK_frage_06_o_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


#### KLMK #### 

class KLMKGiveIntroduction(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_introduction"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set ready status, users are ready if they read the instruction'''
        try:
            active_loop = tracker.active_loop.get('name') 
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                modus = '_'.join(active_loop.split('_')[2:])
                introduction = Introduction(modus = modus)
                return await send_countdown_task(introduction.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 

class KLMKIntroductionCompetition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_introduction_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLMKGiveTeamName(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_team_name"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' '''
        try:
            if tracker.get_slot("flag") is None: 
                slot_id = "team_name"
                is_group = True 
                team_name = TeamName(is_group,slot_id)
                return await send_countdown_task(team_name.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class KLMKTeamNameCompetition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_team_name_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLMKCompetiveGoal(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_competive_goal"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set goal '''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "competive_goal"
                is_group = True
                goal = Goal(is_group, quest_id)
                return await send_countdown_task(goal.to_dict(), tracker)
        except Exception as e:
            logger.exception(e)

class KLMKCompetiveGoalCompetition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_competive_goal_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLMKQuest01(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_01_s"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                game_mode_handler = GameModeHandler()
                session_handler = SessionHandler()
                filter = session_handler.get_session_filter(tracker)
                session = await session_handler.get_session_object(tracker)
                stars = session.get('stars') if session is not None else 0
                if stars == 0: 
                    await game_mode_handler.increase_stars(filter)
                    text = "Super gemacht! Ihr habt die Einleitung geschafft! Ihr verdient euch einen Stern! 🌟"
                    await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
                quest_id = "frage_01_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLMKFrage01Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_01_s_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLMKQuest02(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_02_s"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_02_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLMKFrage02Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_02_s_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLMKQuest03(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_03_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_03_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLMKFrage03Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_03_m_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLMKQuest04(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_04_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_04_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLMKFrage04Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_04_m_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 

class KLMKQuest05(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_05_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_05_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

class KLMKFrage05Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_05_o_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


class KLMKQuest06(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_06_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_06_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLMKFrage06Competition(Action):
    def name(self) -> Text:
        return "action_ask_KLMK_frage_06_o_competition"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        try:
            return set_reminder_comp(tracker)
        except Exception as e:
            logger.exception(e) 


################### KL ############ 
class KLGiveIntroduction(Action):
    def name(self) -> Text:
        return "action_ask_KL_introduction"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set ready status, users are ready if they read the instruction'''
        try:
            active_loop = tracker.active_loop.get('name') 
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                modus = '_'.join(active_loop.split('_')[2:])
                introduction = Introduction(modus = modus)
                return await send_countdown_task(introduction.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class KLGiveTeamName(Action):
    def name(self) -> Text:
        return "action_ask_KL_team_name"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' '''
        try:
            if tracker.get_slot("flag") is None: 
                slot_id = "team_name"
                is_group = True 
                team_name = TeamName(is_group,slot_id)
                return await send_countdown_task(team_name.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class NonCompetiveGoal(Action):
    def name(self) -> Text:
        return "action_ask_KL_non_competive_goal"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set goal '''
        try:
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                quest_id = "non_competive_goal"
                is_group = True 
                goal = Goal(is_group, quest_id)
                return await send_countdown_task(goal.to_dict(), tracker)
        except Exception as e:
            logger.exception(e)

class KLQuest01(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_01_s"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                game_mode_handler = GameModeHandler()
                session_handler = SessionHandler()
                filter = session_handler.get_session_filter(tracker)
                session = await session_handler.get_session_object(tracker)
                stars = session.get('stars') if session is not None else 0
                if stars == 0: 
                    await game_mode_handler.increase_stars(filter)
                    text = "Super gemacht! Ihr habt die Einleitung geschafft! Ihr verdient euch einen Stern! 🌟"
                    await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
                quest_id = "frage_01_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLQuest02(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_02_s"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_02_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLQuest03(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_03_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_03_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class KLQuest04(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_04_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_04_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class Quest05(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_05_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_05_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)




class KLQuest06(Action):
    def name(self) -> Text:
        return "action_ask_KL_frage_06_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_06_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)

##### OKK #### 
class OKKGiveIntroduction(Action):
    def name(self) -> Text:
        return "action_ask_OKK_introduction"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' set ready status, users are ready if they read the instruction'''
        try:
            active_loop = tracker.active_loop.get('name') 
            if tracker.get_slot("flag") is None: 
                active_loop = tracker.active_loop.get('name') 
                modus = '_'.join(active_loop.split('_')[2:])
                introduction = Introduction(modus = modus)
                return await send_countdown_task(introduction.to_dict(), tracker)
        except Exception as e:
            logger.exception(e) 


class OKKQuest01(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_01_s"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                game_mode_handler = GameModeHandler()
                session_handler = SessionHandler()
                filter = session_handler.get_session_filter(tracker)
                session = await session_handler.get_session_object(tracker)
                stars = session.get('stars') if session is not None else 0
                if stars == 0: 
                    await game_mode_handler.increase_stars(filter)
                    text = "Super gemacht! Du hast die Einleitung geschafft! Du verdienst dir einen Stern! 🌟"
                    await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
                quest_id = "frage_01_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class OKKQuest02(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_02_s"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_02_s" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class OKKQuest03(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_03_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_03_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class OKKQuest04(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_04_m"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_04_m" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)


class OKKQuest05(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_05_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_05_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)




class OKKQuest06(Action):
    def name(self) -> Text:
        return "action_ask_OKK_frage_06_o"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        ''' get ID of current question'''
        try:
            if tracker.get_slot("flag") is None: 
                quest_id = "frage_06_o" 
                multiple_response_quest = MultipleResponseQuest(quest_id)
                await asyncio.sleep(2)
                return await multiple_response_quest.run_question(tracker)
        except Exception as e:
            logger.exception(e)