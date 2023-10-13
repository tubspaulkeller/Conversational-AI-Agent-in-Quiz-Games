from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import UserUtteranceReverted, FollowupAction
from rasa_sdk.executor import CollectingDispatcher
from actions.common.common import ask_openai, async_connect_to_db, get_requested_slot, get_credentials, get_dp_inmemory_db
from actions.session.sessionhandler import SessionHandler
import logging
logger = logging.getLogger(__name__)

class ActionAskBen(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return "action_ask_ben"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        try:
            # Get Message from User with Question to Ben 
            message = " "
            for event in reversed(tracker.events):
                    if event['event'] == 'user':
                        #print("EVENT",event )
                        if 'ask_ben' in event['metadata']:
                            message = event['metadata']['ask_ben']
                            print("MSG", message)
                            break
                           
            # talk to Ben 
            session_handler = SessionHandler()
            opponent_id = session_handler.get_opponent(tracker)
            # mygroup
            filter = {
                    "channel_id": tracker.sender_id,     
                    "other_group": opponent_id
            }

            session_obj = await session_handler.session_collection.find_one(filter)
            my_points = session_obj['total_points'] if session_obj else 0
            my_badges = len(session_obj['achievements']) if session_obj else 0
            my_level = session_obj['level'] if session_obj else 0
            
            # opponent 
            filter_opponent = {
                "channel_id": str(opponent_id),
                "other_group": int(tracker.sender_id)

            }
            # get achievements 
            loop = tracker.active_loop.get('name') 
            session_obj_opponent = await session_handler.session_collection.find_one(filter_opponent)
            points_opponent = session_obj_opponent['total_points'] if session_obj_opponent else 0
            badges_opponent = len(session_obj_opponent['achievements']) if session_obj_opponent else 0
            level_opponent = session_obj_opponent['level'] if session_obj_opponent else 0
            game_modus = '_'.join(loop.split('_')[2:]) if loop else None
            team_name = tracker.get_slot("team_name") if team_name else None
            goal = tracker.get_slot("goal") if goal else None
            game_information = "Bislang hat die Gruppe von Spieler oder der Spieler keinen Spielmodus ausgewählt."
            # role for Ben 
            role = "Du bist ein sehr guter Student von einem höheren Semester. Du hast herausragendes Wissen über die Vorlesung 'Einführung in die Wirtschaftsinfomratik.\
            Du befindest dich mitten in einem Quiz-Spiel wobei Studierende der Wirtschaftsinformatik versuchen Quizfragen zu lösen.\
            Das Quiz-Spiel besteht aus sechs Fragen (2x Single-Choice, 2x Multiple-Choice und 2x Offene Fragen).\
            Du bist ein Chatbot namens Ben, der als Moderator dient und auch für Fragen im Thema der Wirtschaftsinformatik \
            zu Verfügung steht. Falls die einkommende Nachricht Chitchat ist, versuche sie lustig und motivierend zu beantworten (1 Satz).\
            Andere Fragen beantwortest du kurz und gibst eine Hifleistung/Tipp.\
            Du gibst aber nicht die Lösung preis, sondern versuchst eher die Studierenden zur Lösung hinzuführen.\
            Bei Beleidungen, kannst du gerne daraufhinweisen, dass dieses Verhalten während des Quizes nicht gestattet ist und zu Bestrafungen führen kann.\
            Verwende bei deinen Antworten motivierende Emojis."
        
            ask_group_achievements_score_competition = "Fragt dich die Gruppe nach deren Punkte-, Sterne- oder Abzeichenstand sowie deren Stände des Gegners beantworte dies!\
                Aber gehe nicht auf die aktuelle Quizfrage ein und beantworte nur den Teil zu dem gefragten Leistungsstand.\
                Punktestand der Gruppe: %s, Punktestand des Gegners/anderen Gruppe: %s,\
                Abzeichenstand der Gruppe: %s, Abzeichenstand des Gegners/anderen Gruppe: %s und Levelstand der Gruppe/Studenten: %s sowie Levelstand des Gegners/anderen Gruppe: %s"%(my_points, points_opponent, my_badges, badges_opponent, my_level, level_opponent)
            ask_group_play_score = "Fragt dich die Gruppe nach ihrem Punkte-, Sterne- oder Abzeichenstand, beantworte dies, aber gehe nicht auf die aktuelle Quizfrage ein und beantworte nur den Teil zu dem gefragten Leistungsstand"%(my_points, my_badges, my_level)
            ask_single_play_score = "Fragt dich der Student nach seinem Punkte-, Sterne- oder Abzeichenstand, beantworte dies, aber gehe nicht auf die aktuelle Quizfrage ein und beantworte nur den Teil zu dem gefragten Leistungsstand"%(my_points, my_badges, my_level)
            
            print("GAME_MODUS", game_modus)
            if game_modus == "KLOK": 
                KLOK_modus = "In diesem Spielmodus spielen die Studierenden in Teams, haben jedoch keine Möglichkeit, sich abzustimmen, während sie gleichzeitig gegen ein anderes Team antreten. Ihre Punkte werden auf ein Gemeinschaftspunktekonto gelegt und mit dem gegnerischen Punktekonto verglichen, wordurch der Wettbewerb entsteht."
                game_information = ask_group_achievements_score_competition + KLOK_modus + "Der Teamname des Teams ist: %s"%team_name 
            
            elif game_modus == "KLMK":
                KLMK_modus = "In diesem Modus treten die Studierenden gegen ein anderes Team an und haben die Möglichkeit, sich innerhalb ihres eigenen Teams abzustimmen, bevor sie die Quizfrage beantworten."
                game_information = ask_group_achievements_score_competition + KLMK_modus + "Der Teamname des Teams ist: %s. Das Ziel des Teams ist: %s"%(team_name, goal)
            
            elif game_modus == "KL": 
                KL_modus = "Die Studierende spielen nicht gegen ein anderes Team, sondern lösen die Quizfragen gemeinsam."
                game_information = ask_group_play_score + KL_modus + + "Der Teamname des Teams ist: %s. Das Ziel des Teams ist: %s"%(team_name, goal)
            elif game_modus == "OKK":
                OKK_modus = "Jeder Spieler spielt das Quiz individuell und alleine, ohne ein Team oder ein anderes Team als Gegner zu haben."
                game_information = ask_single_play_score + game_modus
            

            db = get_credentials("DB_NAME")
            collection = async_connect_to_db(db, 'Questions')
            quest_id = get_requested_slot(tracker)
            filter = {"question_id": quest_id}
            question = await collection.find_one(filter)
            # get current question of game
            if question:
                curr_question = "Die aktuelle Quizfrage ist %s" %question['display_question']
                role = role + game_information + curr_question
            
            # ask openai with role and question from the use
            ben_answer = ask_openai(role, message)
            dispatcher.utter_message(text = ben_answer)
            return [UserUtteranceReverted()]
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return [UserUtteranceReverted()]
