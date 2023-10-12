from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import UserUtteranceReverted, FollowupAction
from rasa_sdk.executor import CollectingDispatcher
from actions.common.common import ask_openai, async_connect_to_db, get_requested_slot, get_credentials, get_dp_inmemory_db
import logging
logger = logging.getLogger(__name__)

class ActionFallback(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return "action_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        try:
            # if tracker.active_loop.get('name') == 'dp1_form' or tracker.active_loop.get('name') == 'dp3_form' or tracker.active_loop.get('name') == 'dp3_form_voc' or tracker.active_loop.get('name') == 'dp3_form_gram' or tracker.active_loop.get('name') == 'dp2_form' or tracker.active_loop.get('name') == 'get_dp_form':
            #     return [FollowupAction("action_repeat_last_quest")]
            msg = tracker.latest_message.get('text')
            print("\033[94mFALLBACK - ASK BEN: %s\033[0m"%msg)
            role ="Du bist ein sehr guter Student von einem höheren Semester. Du hast herausragendes Wissen über die Vorlesung 'Einführung in die Wirtschaftsinfomratik.\
            Du befindest dich mitten in einem Quiz-Spiel wobei Studierende der Wirtschaftsinformatik versuchen Quizfragen zu lösen.\
            Das Quiz-Spiel besteht aus sechs Fragen (2x Single-Choice, 2x Multiple-Choice und 2x Offene Fragen).\
            Du bist ein Chatbot namens Ben, der als Moderator dient und auch für Fragen im Thema der Wirtschaftsinformatik \
            zu Verfügung steht. Falls die einkommende Nachricht Chitchat ist, versuche sie lustig und motivierend zu beantworten (1 Satz).\
            Andere Fragen beantwortest du kurz und gibst eine Hifleistung/Tipp.\
            Du gibst aber nicht die Lösung preis, sondern versuchst eher die Studierenden zur Lösung hinzuführen.\
            Bei Beleidungen, kannst du gerne daraufhinweisen, dass dieses Verhalten während des Quizes nicht gestattet ist und zu Bestrafungen führen kann.\
            Verwende bei deinen Antworten motivierende Emojis.\
            Fragt dich der Student nach seinem Punkte,Sterne \
            oder Abzeichen-stand sowie das des Gegners, weise ihn darauf hin, dass er seine Frage nochmal anders formuliere müsste, da du sie so nicht verarbeiten kannst."
            requested_slot = get_requested_slot(tracker)
            db = get_credentials("DB_NAME")
            collection = async_connect_to_db(db, 'Questions')
            filter = {"question_id": requested_slot}
            question = await collection.find_one(filter)
            if question:
                curr_question = "Die aktuelle Quizfrag ist %s" %question['display_question']
                role = role + curr_question
            ben_answer = ask_openai(role, msg)
            dispatcher.utter_message(text = ben_answer)
            return [UserUtteranceReverted()]
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return [UserUtteranceReverted()]
