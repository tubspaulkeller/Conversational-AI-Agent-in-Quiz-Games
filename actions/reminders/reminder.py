import datetime
from rasa_sdk.events import ReminderScheduled, ReminderCancelled, FollowupAction, SlotSet
from rasa_sdk import Action
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import asyncio
from actions.common.common import print_current_tracker_state, get_requested_slot, get_credentials, ben_is_typing, get_dp_inmemory_db
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.gamification.countdown.countdown import Countdown
from actions.quests.multipleresponsequest import MultipleResponseQuest
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.achievements.achievementshandler import AchievementHandler
from actions.session.sessionhandler import SessionHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.timestamps.timestamp import Timestamp
import logging
logger = logging.getLogger(__name__)

######## Reminder for Countdown during non quiz and quiz slots ##########

class SetReminderCountdownMsgQuestions(Action):
    """Schedules a reminder, supplied with the last message's entities."""

    def name(self) -> Text:
        return "action_set_reminder_countdown_msg"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        trigger_sec = datetime.datetime.now() + datetime.timedelta(seconds=int(get_credentials("INTERVALL"))- int(get_credentials("REMINDER_DELAY")))
        reminder = ReminderScheduled(
            "EXTERNAL_reminder_countdown_msg",
            trigger_date_time=trigger_sec,
            name = "reminder_group_%s"%tracker.sender_id,
            kill_on_user_message=False,
        )
        return [reminder] 


class ReactToReminderCountdownMsgQuestions(Action):
    """Reminds the user to call someone."""

    def name(self) -> Text:
        return "action_react_to_reminder_countdown_msg"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        try: 
            countdownhandler = CountdownHandler()
            competition_mode_handler = CompetitionModeHandler()

            ''' get current ID of question'''
            requested_slot = get_requested_slot(tracker)
            ''' get countdown'''
            countdown = tracker.get_slot("countdown")
            multiple_response_quest = MultipleResponseQuest(requested_slot)
            active_loop = tracker.active_loop.get('name')

            if "_goal" in requested_slot or "introduction" == requested_slot or "team_name" == requested_slot:
                # handle non quest slots
                return await countdownhandler.update_countdown_text(countdown, dispatcher, 'action_set_reminder_countdown_msg', active_loop, tracker.get_slot("my_group"))
            else:
                # handle slots for quiz
                session_handler = SessionHandler()
                filter = session_handler.get_session_filter(tracker)
                return await countdownhandler.update_countdown_question(countdown, dispatcher, 'action_set_reminder_countdown_msg', multiple_response_quest, competition_mode_handler,active_loop, tracker.get_slot("my_group"), tracker.sender_id, filter, tracker.get_slot("opponent_id"))
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("\033[91m Reminder, Method: react reminder, Error occurred:\033[0m %s", e)
            error_message = "Oops! Something went wrong. Please restart the game with @Ben restart"
            dispatcher.utter_message(text=error_message)
            return[]

class ForgetReminders(Action):
    """Cancels all reminders."""

    def name(self) -> Text:
        return "action_forget_reminders"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        return [ReminderCancelled(name="reminder_group_%s"%tracker.sender_id)]




######## Reminder for Competition Mode ##########

class SetReminderCompetition(Action):
    """Schedules a reminder, supplied with the last message's entities."""

    def name(self) -> Text:
        return "action_set_reminder_competition"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        trigger_sec = datetime.datetime.now() +  datetime.timedelta(seconds=int(get_credentials("COMPETITION_REMINDER")))
        print("SET REMINDER GOT CALLED")
        reminder = ReminderScheduled(
            "EXTERNAL_reminder_competition",
            trigger_date_time=trigger_sec,
            name = "reminder_group_%s"%tracker.sender_id,
            kill_on_user_message=False,
      
        )
        return [reminder] 


class ReactToReminderCompetition(Action):
    """Reminds the user to call someone."""

    def name(self) -> Text:
        return "action_react_to_reminder_competition"

    async def handle_non_quest_slots(self, last_requested_slot, quest_id, active_loop, filter, session_handler, tracker, dispatcher):
        try: 
            competition_mode_handler = CompetitionModeHandler()
            # check if my group got evaluated
            if await competition_mode_handler.check_status("evaluated", last_requested_slot, filter, session_handler.session_collection):
                # check if opponent has answered
                opponent_has_answered, waiting_countdown, exceeded = await competition_mode_handler.waiting_of_opponent(last_requested_slot, tracker.sender_id, filter['other_group'], tracker.get_slot("waiting_countdown"), active_loop, dispatcher)
                if not opponent_has_answered and not exceeded:
                    # another round to wait
                    return [FollowupAction('action_set_reminder_competition'), SlotSet("waiting_countdown",waiting_countdown)]
                elif not opponent_has_answered and exceeded:
                    # other group did not answered 
                    dispatcher.utter_message(text= "Das andere Team möchte nicht mehr weiterspielen...\nIhr seid die Sieger 🏆")
                    achievement = "GESAMTSIEGER"
                    achievement_handler = AchievementHandler()
                    if await achievement_handler.insert_achievement(filter, achievement):
                        badges = get_dp_inmemory_db("./badges.json")
                        dispatcher.utter_message(image = badges[achievement])
                else:
                    # other group answered
                    dispatcher.utter_message(response="utter_continue")
                    await ben_is_typing(tracker.get_slot('countdown'), competition_mode_handler)
                    return [SlotSet(last_requested_slot, "answered"), SlotSet("random_person", None), SlotSet("flag", None), SlotSet("countdown", None),SlotSet("answered", None), SlotSet("waiting_countdown", None), FollowupAction("action_forget_reminders_competition")]   
            else:
                # set my group to evaluated, create waiting countdown 
                await competition_mode_handler.set_status('evaluated', quest_id, filter, session_handler.session_collection, True)
                waiting_countdown, utter_message = await competition_mode_handler.msg_check_evaluation_status_of_opponent(filter['other_group'], last_requested_slot, tracker.sender_id, active_loop, False)
                #dispatcher.utter_message(response=utter_message)
                return [SlotSet("waiting_countdown", waiting_countdown.to_dict()), FollowupAction('action_set_reminder_competition')] 
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("\033[91m Method: handle_non_quest_slots, Error occurred:\033[0m %s", e)
    
    async def handle_quest_slots(self, last_requested_slot, quest_id, active_loop, filter, session_handler, tracker, dispatcher):
        try:
            competition_mode_handler = CompetitionModeHandler()
            # check if my group got evaluated
            if await competition_mode_handler.check_status("evaluated", last_requested_slot, filter, session_handler.session_collection):
                # check if opponent has answered
                opponent_has_answered, waiting_countdown, exceeded = await competition_mode_handler.waiting_of_opponent(last_requested_slot, tracker.sender_id, filter['other_group'], tracker.get_slot("waiting_countdown"), active_loop, dispatcher)
                if not opponent_has_answered and not exceeded:
                    # another round to wait
                    return [FollowupAction('action_set_reminder_competition'), SlotSet("waiting_countdown",waiting_countdown)]
                elif not opponent_has_answered and exceeded:
                    # other group did not answered
                    dispatcher.utter_message(text= "Das andere Team möchte nicht mehr weiterspielen...\nIhr seid die Sieger 🏆")
                    achievement = "GESAMTSIEGER"
                    achievement_handler = AchievementHandler()
                    if await achievement_handler.insert_achievement(filter, achievement):
                        badges = get_dp_inmemory_db("./badges.json")
                        dispatcher.utter_message(image = badges[achievement])
                    #get achievements
                    await achievement_handler.earn_achievement(filter, tracker.slots.keys(),tracker.sender_id)
                    return [FollowupAction("action_leaderboard")] 
                else:
                    # other group answered, get winner 
                    return await competition_mode_handler.get_winner_of_round(last_requested_slot, tracker.get_slot("earned_points"), tracker.get_slot("solution"), tracker.get_slot("group_answer"), tracker.get_slot("level_up"),  tracker.sender_id, tracker.get_slot('countdown'), tracker.slots.keys(), filter, active_loop)
            else:
                # set my group to evaluated and calc points, level
                sender_id = tracker.sender_id 
                group_answer = tracker.get_slot("group_answer")
                quest = tracker.get_slot("countdown")['question']['display_question']
                num_of_my_group = len(tracker.get_slot("my_group")['users'])
                return await competition_mode_handler.handle_validation_of_group_answer(last_requested_slot, filter, dispatcher, active_loop, sender_id, group_answer, quest, num_of_my_group)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("\033[91m Method: handle_quest_slots, Error occurred:\033[0m %s", e)
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        print("REACT REMINDER GOT CALLED") 
        try: 
 
            
            timestamp_handler = TimestampHandler()
            session_handler = SessionHandler()
            '''get Filter of session '''
            filter = session_handler.get_session_filter(tracker)
            ''' get countdown and last requested slot'''
            countdown = tracker.get_slot("countdown")
            last_requested_slot = countdown['quest_id']
            timestamp, active_loop, quest_id, opponent_id = timestamp_handler.get_timestamp(filter['channel_id'], 'waiting')

           
            #print("Info:\nlast_requested_slot: %s\n quest_id: %s\nloop: %s"%(last_requested_slot, quest_id, active_loop))

            if quest_id == "introduction" or quest_id == "team_name" or quest_id == "competive_goal": 
                # slots before quiz game
                return await self.handle_non_quest_slots(last_requested_slot, quest_id, active_loop, filter, session_handler, tracker, dispatcher)
            else:
                # quiz game
                return await self.handle_quest_slots(last_requested_slot, quest_id, active_loop, filter, session_handler, tracker, dispatcher)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("\033[91m Competition Reminder, Method: react reminder competition, Error occurred:\033[0m %s", e)
            error_message = "Oops! Something went wrong. 🚨🔴 Please restart the game with '# neues Spiel'"
            dispatcher.utter_message(text=error_message)
            return[]

class ForgetReminderCompetition(Action):
    """Cancels all reminders."""

    def name(self) -> Text:
        return "action_forget_reminders_competition"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Cancel all reminders
        session_handler = SessionHandler()
        '''get Filter of session '''
        filter = session_handler.get_session_filter(tracker)
        timestamp_handler = TimestampHandler()
        _, active_loop, quest_id, opponent_id = timestamp_handler.get_timestamp(filter['channel_id'], 'waiting')
        slots = [key for key in tracker.slots.keys() if key.startswith('frage_')]   
        # Last slot: -2 dann frage_05_o bei -1: frage_06_o
        if quest_id == slots[int(get_credentials("LAST_SLOT"))]:
            return [ReminderCancelled(name="reminder_group_%s"%tracker.sender_id), FollowupAction("action_winner")] 
        # starte Form wieder, Form beginnt mit dem nächsten Slot, der noch None ist aus der Slotliste
        if active_loop == 'quiz_form_KLMK':
            return [ReminderCancelled(name="reminder_group_%s"%tracker.sender_id), FollowupAction("quiz_form_KLMK")]
        else: 
            return [ReminderCancelled(name="reminder_group_%s"%tracker.sender_id), FollowupAction("quiz_form_KLOK")]



class ActionStopCountdown(Action):
    def name(self) -> Text:
        return "action_stop_countdown"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:        
        

        # TIMESTAMPHANDLING?
        timestamp_handler = TimestampHandler()
        session_handler = SessionHandler()
        '''get Filter of session '''
        filter = session_handler.get_session_filter(tracker)

        timestamp, active_loop, quest_id, opponent_id = timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
        timestamp_handler.delete_timestamps_for_group(tracker.sender_id, 'waiting')
        # create new timestamp 
        new_timestamp = Timestamp(tracker.sender_id, quest_id, active_loop, filter['other_group']).to_dict()
        # A large number must be subtracted from the new timestamp so that it is smaller than timestamp + countdown
        new_timestamp['timestamp'] = new_timestamp['timestamp'] - 500
        timestamp_handler.insert_new_timestamp(new_timestamp, 'waiting')

        if tracker.get_slot("countdown") is None:
            default_countdown = Countdown(tracker.sender_id, quest_id, active_loop)
            mqr = MultipleResponseQuest(quest_id)
            question =await mqr.get_quest() 
            default_countdown.question = question
            default_countdown.countdown = 10
            return [FollowupAction('action_react_to_reminder_countdown_msg'), SlotSet("countdown",default_countdown.to_dict())]
        else: 
            default_countdown = tracker.get_slot("countdown")
            default_countdown['countdown'] = 10
            return [FollowupAction('action_react_to_reminder_countdown_msg'), SlotSet("countdown",default_countdown)]
        