from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted, SlotSet, EventType

from actions.achievements.achievementshandler import AchievementHandler
from actions.session.sessionhandler import SessionHandler

class ActionScore(Action):
    def name(self) -> Text:
        return "action_give_score"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """ total points are given to the user/group """

        achievements_handler = AchievementHandler()
        session_handler = SessionHandler() 
        filter = session_handler.get_session_filter(tracker)
        total_points = await achievements_handler.get_total_points_of_group(filter)
        if tracker.get_slot('is_user') and total_points == 0:
            answer = "Bisher keine Punkte 📉, aber keine Sorge! Starte die Aufgaben 🚀 oder bleibe dran, um bald Punkte einzusammeln und erfolgreich abzuräumen! 💪😊"
        elif not tracker.get_slot('is_user') and total_points == 0:
            answer= "Eure Gruppe hat bislang noch keine Punkte 📉 gesammelt, aber keine Sorge! Startet gemeinsam die Aufgaben 🚀 oder bleibt dran, um bald gemeinsam Punkte einzusammeln und erfolgreich abzuräumen! 💪😊"
        
        elif not tracker.get_slot('is_user') and total_points > 0:
            answer = "Euer Punktestand beträgt: %s Punkte! 🎉💯 Macht weiter so und holt euch noch mehr Punkte! 💪😎"%total_points
        
        elif tracker.get_slot('is_user') and total_points > 0:
            answer = "Dein aktueller Punktestand beträgt: %s Punkte! 🎉💯 Du machst großartige Fortschritte! 💪😎"%total_points
        dispatcher.utter_message(text=answer)
        return [UserUtteranceReverted()]#, FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionBadges(Action):
    def name(self) -> Text:
        return "action_give_badges"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Total badges are given to the user/group"""

        achievements_handler = AchievementHandler()
        session_handler = SessionHandler() 
        session = await session_handler.get_session_object(tracker)
        total_badges = len(session['achievements'])

        if tracker.get_slot('is_user') and total_badges == 0:
            answer = "Bisher noch keine Badges 🏅, aber mach dir keine Sorgen! Sammle Badges, indem du an Aufgaben teilnimmst und coole Erfolge freischaltest! 🚀😊"
        elif not tracker.get_slot('is_user') and total_badges == 0:
            answer= "Eure Gruppe hat bislang noch keine Badges 🏅 gesammelt, aber keine Sorge! Sammelt gemeinsam Badges, indem ihr an Aufgaben teilnehmt und tolle Erfolge erzielt! 💪😊"
        
        elif tracker.get_slot('is_user') and total_badges > 0:
            answer = "Dein aktueller Badge-Score beträgt: %s Badges! 🎉🏅 Mache weiter so und schalte noch mehr coole Erfolge frei! 💪😎"%total_badges
        
        elif not tracker.get_slot('is_user') and total_badges > 0:
            answer = "Euer Gruppen-Badge-Score beträgt: %s Badges! 🎉🏅 Macht weiter so und sammelt gemeinsam noch mehr coole Erfolge! 💪😎"%total_badges

        dispatcher.utter_message(text=answer)
        return [UserUtteranceReverted()]



class ActionScoreOpponent(Action):
    def name(self) -> Text:
        return "action_give_score_opponent"
    
    async def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """ total points are given to opponent """

        achievements_handler = AchievementHandler()
        session_handler = SessionHandler() 
        filter = session_handler.get_session_filter(tracker)
        opponent_score = await achievements_handler.get_total_points_of_group(filter['other_group'])

        if opponent_score is not None:
            answer = "Der Punktestand eures Gegners beträgt: %s Punkte! 🎯💪"%opponent_score
        else:
            answer = "Es tut mir leid, ich konnte den Punktestand eures Gegners nicht abrufen. 🙁"

        dispatcher.utter_message(text=answer)
        return [UserUtteranceReverted()]#, FollowupAction(tracker.active_form.get('latest_action_name'))]


class ActionBadgeOpponent(Action):
    def name(self) -> Text:
        return "action_give_badges_opponent"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """ total badges are given to opponent """

        achievements_handler = AchievementHandler()
        session_handler = SessionHandler() 
        filter = session_handler.get_session_filter(tracker)
        opponent_badge = await achievements_handler.get_total_points_of_group(filter['other_group'])

        if opponent_badge is not None:
            answer = "Der Abzeichenstand eures Gegners beträgt: %s Abzeichen! 🎯💪"%opponent_badge
        else:
            answer = "Es tut mir leid, ich konnte den Abzeichenstand eures Gegners nicht abrufen. 🙁"

        dispatcher.utter_message(text=answer)
        return [UserUtteranceReverted()]#, FollowupAction(tracker.active_form.get('latest_action_name'))]




class ActionWhyPointsBadgesStars(Action):
    def name(self) -> Text:
        return "action_why_points_badges_stars"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: "Tracker", domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entities = tracker.latest_message.get('entities')
        value = []
        valid_combinations = [
            ("sterne", "punkte"),
            ("stars", "punkte"),
            ("punkte", "sterne"),
            ("punkte", "stars"),
            ("abzeichen", "punkte"),
            ("badges", "punkte"),
            ("punkte", "abzeichen"),
            ("punkte", "badges")
        ]

        try:
            for entity in entities:
                value.append(entity['value'].lower())
            # Punkte und Sterne oder Abzeichen
            if len(value) == 2:
                if (value[0].lower(), value[1].lower()) in valid_combinations or (value[1].lower(), value[0].lower()) in valid_combinations:
                   dispatcher.utter_message(text="Die Punkte zeigen an, wie gut/schnell die Aufgabe gelöst wird. Die volle Punktzahl wird vergeben, sobald die Aufgabe innerhalb des Zeitlimits beantwortet wird. Je länger gebraucht wird, desto weniger Punkte werden verteilt.\nDie Sterne oder Abzeichen zeigen den Erfolg in einem bestimmten Bereich an. Sie werden für mittelfristige Erfolge vergeben.")
            elif len(value) == 1:
                if value[0] == "punkte":
                    dispatcher.utter_message(text="Die Punkte zeigen an, wie gut/schnell die Aufgabe gelöst wird. Die volle Punktzahl wird vergeben, sobald die Aufgabe innerhalb des Zeitlimits beantwortet wird. Je länger gebraucht wird, desto weniger Punkte werden verteilt.")
                elif value[0] == "abzeichen" or value[0] == "badges":
                    dispatcher.utter_message(text="Abzeichen werden für besondere Erfolge vergeben. Sie stellen also Errungenschaften dar, wenn besonders erfolgreich agiert wurde. Zum Beispiel wird ein Abzeichen vergeben, wenn alle Aufgaben auf Anhieb richtig gelöst wurden.")
                elif value[0] == "sterne" or value[0] == "stars":
                    dispatcher.utter_message(text="Die Sterne zeigen den Erfolg in einem bestimmten Bereich an. Sie werden für mittelfristige Erfolge vergeben.")
            return [UserUtteranceReverted()]
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  