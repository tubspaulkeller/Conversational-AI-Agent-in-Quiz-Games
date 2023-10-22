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
    LoopInterrupted,
    ActionExecutionRejected,
    UserUttered
)
import datetime
from actions.common.common import get_groupuser_id_and_answer, get_credentials, get_json_msg, get_countdown_value, get_requested_slot
from actions.users.userhandler import UserHandler
from actions.game.gamemodehandler import GameModeHandler
from actions.groups.grouphandler import GroupHandler
from pymongo import MongoClient
import time
import asyncio
import threading
from motor.motor_asyncio import AsyncIOMotorClient
from sanic.exceptions import ServiceUnavailable
from sanic.config import Config
import random
from actions.common.debug import debug
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.gamification.countdown.countdown import Countdown
from actions.timestamps.timestamphandler import TimestampHandler
from actions.timestamps.timestamp import Timestamp
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.session.sessionhandler import SessionHandler
from actions.quests.question import Question
from actions.goal.goalhandler import GoalHandler
from actions.session.session import Session
from actions.achievements.achievementshandler import AchievementHandler
from actions.common.common import ask_openai, ben_is_typing, setup_logging
from actions.quests.introduction import set_introduction
from actions.quests.teamname import set_team_name
from actions.users.klokanswerhandler import KlokAnswersHandler
import logging
logger = setup_logging()

'''
Gruppen:
A: KLMK 
B: KLOK
C: KL 
D: OKK 
In this file will be placed all validations for the four different modi
'''


class ValidateQuizFormKLOK(FormValidationAction):
    def name(self) -> Text:
        # Unique identifier of the form"
        return "validate_quiz_form_KLOK"
    '''
    Mode Competitives Learning w/o Collaboration = CLWOC (german = Kompetitives Lernen Ohne Kollaboration = KLOK)
    '''
    async def validate_introduction(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        session_handler = SessionHandler()
        competition_mode_handler = CompetitionModeHandler()
        return await set_introduction(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_team_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_team_name(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_competive_goal(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        goalhandler = GoalHandler()
        return await goalhandler.set_competive_goal(slot_value, tracker, dispatcher)

    def create_validation_function_for_slots_in_quiz_form_klok(name_of_slot):

        async def validate_slot(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> Dict[Text, Any]:
            """Validate user input."""
            print("\033[91m  IN VALIDATION - KLOK  \033[0m ")

            # Prevent: user can not answer earlie by open quests
            timestamp_handler = TimestampHandler()
            timestamp, loop, _, _ = await timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
            countdown = get_countdown_value(name_of_slot, loop)
            now = datetime.datetime.now().timestamp()
            if name_of_slot[-1] == "o" and (now < timestamp + countdown):
                return {name_of_slot: None}

            if slot_value != "answered" and name_of_slot == get_requested_slot(tracker):
                '''
                get user credentials
                '''
                groupuser_id, groupuser_name, group_user_answer = get_groupuser_id_and_answer(
                    tracker)

                user_handler = UserHandler()
                session_handler = SessionHandler()
                competition_mode_handler = CompetitionModeHandler()
                klok_handler = KlokAnswersHandler()
                '''
                create user answer
                '''
                user_answer = user_handler.created_user_answer(
                    tracker.sender_id, name_of_slot, groupuser_id, groupuser_name, group_user_answer)
                if user_answer is None:
                    return {name_of_slot: None}

                '''
                create put user answer into dict for specific group id
                '''
                klok_handler.process_user_answer(
                    tracker.sender_id, user_answer, dispatcher)
                '''
                get session through filter
                '''
                filter = session_handler.get_session_filter(tracker)
                group_id_opponent = filter['other_group']

                '''
                get the number of current team mates in group 
                check IF all team mates of own group have answered through comparison of length
                '''
                number_of_team_mates = competition_mode_handler.number_of_team_mates_slot(
                    tracker, "my_group")
                klok_answers = klok_handler.get_klok_answers_for_group(
                    tracker.sender_id)
                if not len(klok_answers) == number_of_team_mates:
                    return {name_of_slot: None}
                else:
                    ''' 
                    if my group exceed time than he has to go to the next question
                    '''

                    if await competition_mode_handler.check_status('exceeded', name_of_slot, filter, competition_mode_handler.session_collection):
                        dispatcher.utter_message(
                            text="⏰😬 Ihr habt die Zeit überzogen und verliert das Spiel. 😔👎")
                        klok_handler.clear_group_answers(tracker.sender_id)
                        return {"answered": False, name_of_slot: "exceeded", "requested_slot": None}

                group_answers = klok_handler.get_klok_answers_for_group(
                    tracker.sender_id)
                klok_handler.clear_group_answers(tracker.sender_id)

                print("GROUP_ANSWERS", group_answers)
                dispatcher.utter_message(
                    response="utter_waiting_msg_evaluate_answers")
                # cancel form  and call reminder
                return {"answered": True, "group_answer": group_answers, name_of_slot: "answered", "requested_slot": None}
            else:
                print("validation action None: %s", name_of_slot)
                return {name_of_slot: "answered"}
        return validate_slot

    validate_frage_01_s = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_01_s")
    validate_frage_02_s = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_02_s")
    validate_frage_03_m = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_03_m")
    validate_frage_04_m = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_04_m")
    validate_frage_05_o = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_05_o")
    validate_frage_06_o = create_validation_function_for_slots_in_quiz_form_klok(
        name_of_slot="frage_06_o")

####################################################################################################################################################################################################################################################


class ValidateQuizFormKLMK(FormValidationAction):
    def name(self) -> Text:
        # Unique identifier of the form"
        return "validate_quiz_form_KLMK"

    '''
    Mode Competitives Learning w Collaboration = CLWC (german = Kompetitives Lernen Mit Kollaboration = KLMK)
    '''
    async def validate_introduction(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_introduction(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_team_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_team_name(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_competive_goal(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        goalhandler = GoalHandler()
        return await goalhandler.set_competive_goal(slot_value, tracker, dispatcher)

    def create_validation_function_for_slots_in_quiz_form_klmk(name_of_slot):
        async def validate_slot(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> Dict[Text, Any]:
            game_mode_handler = GameModeHandler()
            group_handler = GroupHandler()
            session_handler = SessionHandler()
            competition_mode_handler = CompetitionModeHandler()
            """Validate user input."""

            # Prevent: user can not answer earlie by open quests
            timestamp_handler = TimestampHandler()
            timestamp, loop, _, _ = await timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
            countdown = get_countdown_value(name_of_slot, loop)
            now = datetime.datetime.now().timestamp()
            if name_of_slot[-1] == "o" and (now < timestamp + countdown):
                return {name_of_slot: None}

            if slot_value != "answered" and name_of_slot == get_requested_slot(tracker):
                '''
                get user credentials to validate if selected Person has given the answer
                '''
                groupuser_id, groupuser_name, _ = get_groupuser_id_and_answer(
                    tracker)

                '''
                check if the selected person answers
                '''
                r_user_id = tracker.get_slot("random_person")
                if not str(r_user_id) == str(groupuser_id):
                    dispatcher.utter_message(
                        text="❌ Nicht die auserwählte Person hat geanwortet 😉")
                    return {name_of_slot: None}

                '''
                get session through filter
                '''
                filter = session_handler.get_session_filter(tracker)
                group_id_opponent = filter['other_group']
                '''
                check if an answer got allready evaluated, that prevents that user can give multiple answers
                '''
                if await game_mode_handler.check_status('evaluated', name_of_slot, filter, competition_mode_handler.session_collection):
                    return {name_of_slot: 'answered'}

                '''
                create group answer
                '''
                group_answer = group_handler.created_group_answer(
                    tracker.sender_id, name_of_slot, slot_value)
                if group_answer is None:
                    return {name_of_slot: None}
                ''' 
                if my group exceed time than he has to go to the next question
                '''
                if await game_mode_handler.check_status('exceeded', name_of_slot, filter, competition_mode_handler.session_collection):
                    dispatcher.utter_message(
                        text="⏰😬 Ihr habt die Zeit überzogen und verliert das Spiel. 😔👎")
                    return {"answered": False, name_of_slot: "exceeded", "requested_slot": None}

                dispatcher.utter_message(
                    response="utter_waiting_msg_evaluate_answer")
                # cancel form  and call reminder
                return {"answered": True, "group_answer": group_answer, name_of_slot: "answered", "requested_slot": None}
            else:
                print("validation action None: %s" % name_of_slot)
                print(tracker.get_slot(name_of_slot))
                return {name_of_slot: "answered"}
        return validate_slot

    validate_frage_01_s = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_01_s")
    validate_frage_02_s = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_02_s")
    validate_frage_03_m = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_03_m")
    validate_frage_04_m = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_04_m")
    validate_frage_05_o = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_05_o")
    validate_frage_06_o = create_validation_function_for_slots_in_quiz_form_klmk(
        name_of_slot="frage_06_o")

####################################################################################################################################################################################################################################################


class ValidateQuizFormKL(FormValidationAction):
    def name(self) -> Text:
        # Unique identifier of the form"
        return "validate_quiz_form_KL"

    '''
    Mode Collaborative Learning = CL (german = Kollaboratives Lernen = KL)
    '''

    async def validate_introduction(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_introduction(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_team_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_team_name(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_non_competive_goal(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        goalhandler = GoalHandler()
        return await goalhandler.set_non_competive_goal(slot_value, tracker, dispatcher)

    def create_validation_function_for_slots_in_quiz_form_kl(name_of_slot):
        async def validate_slot(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> Dict[Text, Any]:
            """Validate user input."""
            try:
                # user can not answer earlie by open quests
                timestamp_handler = TimestampHandler()
                timestamp, loop, _, _ = await timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
                countdown = get_countdown_value(name_of_slot, loop)
                now = datetime.datetime.now().timestamp()
                if name_of_slot[-1] == "o" and (now < timestamp + countdown):
                    return {name_of_slot: None}

                game_mode_handler = GameModeHandler()
                group_handler = GroupHandler()
                session_handler = SessionHandler()
                '''
                get user credentials to validate if selected Person has given the answer
                '''
                groupuser_id, groupuser_name, _ = get_groupuser_id_and_answer(
                    tracker)
                '''
                check if the selected person answers
                '''
                r_user_id = tracker.get_slot("random_person")
                if not str(r_user_id) == str(groupuser_id):
                    dispatcher.utter_message(
                        text="❌ Nicht die auserwählte Person hat geanwortet 😉")
                    return {name_of_slot: None}

                # check if allready evaluated
                filter = session_handler.get_session_filter(tracker)
                if await game_mode_handler.check_status('evaluated', name_of_slot, filter, game_mode_handler.session_collection):
                    print("User can not submit two times")
                    return {name_of_slot: 'answered'}
                '''
                create group answer
                '''
                group_answer = group_handler.created_group_answer(
                    tracker.sender_id, name_of_slot, slot_value)
                if group_answer is None:
                    return {name_of_slot: None}

                '''
                caluclate points, level, badges 
                '''
                earned_points, solution, solution_points = await game_mode_handler.calc_earned_points(filter, group_answer, name_of_slot, tracker.sender_id, tracker.get_slot('countdown'))
                total_points, level_up = await game_mode_handler.update_session(filter, name_of_slot, earned_points, group_answer['answer'])
                await game_mode_handler.set_status("evaluated", name_of_slot, filter, game_mode_handler.session_collection, True)
                await game_mode_handler.utter_points(solution, group_answer, earned_points, level_up, tracker.sender_id, False, name_of_slot, solution_points)
                achievements_handler = AchievementHandler()
                await achievements_handler.earn_achievement(filter, tracker.slots.keys(), tracker.sender_id)
                await ben_is_typing(tracker.get_slot('countdown'), game_mode_handler)
                return {name_of_slot: "answered", "random_person": None, "flag": None,  "countdown": None}
            except Exception as e:
                logger.exception(e)
            return {name_of_slot: None}
        return validate_slot

    validate_frage_01_s = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_01_s")
    validate_frage_02_s = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_02_s")
    validate_frage_03_m = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_03_m")
    validate_frage_04_m = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_04_m")
    validate_frage_05_o = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_05_o")
    validate_frage_06_o = create_validation_function_for_slots_in_quiz_form_kl(
        name_of_slot="frage_06_o")


####################################################################################################################################################################################################################################################

class ValidateQuizFormOKK(FormValidationAction):
    def name(self) -> Text:
        # Unique identifier of the form"
        return "validate_quiz_form_OKK"

    '''
    Mode Without Competition and Collaboration = WOCC (german = Ohne Kompetition und Kollaboration = OKK)
    '''
    async def validate_introduction(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        competition_mode_handler = CompetitionModeHandler()
        session_handler = SessionHandler()
        return await set_introduction(slot_value, tracker, dispatcher, competition_mode_handler, session_handler)

    async def validate_non_competive_goal(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict",) -> Dict[Text, Any]:
        goalhandler = GoalHandler()
        return await goalhandler.set_non_competive_goal(slot_value, tracker, dispatcher)

    def create_validation_function_for_slots_in_quiz_form_okk(name_of_slot):
        async def validate_slot(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> Dict[Text, Any]:
            """Validate user input."""

            # user can not answer earlie by open quests
            timestamp_handler = TimestampHandler()
            timestamp, loop, _, _ = await timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
            countdown = get_countdown_value(name_of_slot, loop)
            now = datetime.datetime.now().timestamp()
            if name_of_slot[-1] == "o" and (now < timestamp + countdown):
                return {name_of_slot: None}

            game_mode_handler = GameModeHandler()
            group_handler = GroupHandler()
            session_handler = SessionHandler()
            user_handler = UserHandler()
            '''
            get session obj through filter
            '''
            filter = session_handler.get_session_filter(tracker)
            if await game_mode_handler.check_status('evaluated', name_of_slot, filter, game_mode_handler.session_collection):
                return {name_of_slot: 'answered'}

            '''
            get user credentials
            '''
            user = tracker.get_slot("my_group")
            '''
            create user answer
            '''
            user_answer = user_handler.created_user_answer(
                tracker.sender_id, name_of_slot, user["user_id"], user["username"], slot_value)
            if user_answer is None:
                return {name_of_slot: None}

            '''
            caluclate points, level, badges 
            '''
            earned_points, solution, solution_points = await game_mode_handler.calc_earned_points(filter, user_answer, name_of_slot, tracker.sender_id, tracker.get_slot('countdown'))
            total_points, level_up = await game_mode_handler.update_session(filter, name_of_slot, earned_points, user_answer['answer'])
            await game_mode_handler.set_status("evaluated", name_of_slot, filter, game_mode_handler.session_collection, True)
            await game_mode_handler.utter_points(solution, user_answer, earned_points, level_up, tracker.sender_id, True, name_of_slot, solution_points)

            # get achievements
            achievements_handler = AchievementHandler()
            await achievements_handler.earn_achievement(filter, tracker.slots.keys(), tracker.sender_id)
            await ben_is_typing(tracker.get_slot('countdown'), game_mode_handler)
            return {name_of_slot: "answered", "flag": None,  "countdown": None}
        return validate_slot

    validate_frage_01_s = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_01_s")
    validate_frage_02_s = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_02_s")
    validate_frage_03_m = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_03_m")
    validate_frage_04_m = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_04_m")
    validate_frage_05_o = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_05_o")
    validate_frage_06_o = create_validation_function_for_slots_in_quiz_form_okk(
        name_of_slot="frage_06_o")
