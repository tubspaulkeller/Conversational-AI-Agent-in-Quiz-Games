from actions.common.common import get_requested_slot, ben_is_typing
from actions.game.gamemodehandler import GameModeHandler
import random
import string
class Introduction:
    def __init__(self, modus):
        self.id = 'introduction'
        self.modus = modus
        self.exceeded = False
        self.evaluated = False
        self.task = "🔴 Achtung!\nEs ist Zeit, den Button zu drücken, um den Spielmodus zu starten.\nViel Spaß und Erfolg! 🎮🌟\n\n👋 %s bitte drücke den Button."
        self.buttons = [{"title": "Ready! ✅ ", "payload": '/introduction_%s{"e_introduction_%s":"set_introduction"}'%(self.modus, self.modus)}]
        if self.modus == "KLOK":
            self.text = "In diesem interessanten Spielmodus spielt ihr in Teams, aber ihr habt keine Möglichkeit zur Absprache, während ihr gleichzeitig gegen ein anderes Team antritt. Jedes Teammitglied gibt seine eigene Antwort auf die Fragen ab, die individuell bewertet wird, und die Punkte werden dann zusammengezählt. Zeigt euren Ehrgeiz und handelt im Teamgeist! 👥🧠\n\n❗SPIELHINWEIS❗\nIhr trefft auf Single-Choice und Multiple-Choice Fragen, bei denen ihr Buttons für die Antworten erhaltet. Bei offenen Fragen fügt ihr einfach ein '#' zur Antwort hinzu.\nZudem könnt ihr Nachrichten an die andere Gruppe senden, indem ihr am Anfang eurer Nachricht '@Gegner' verwendet."
        elif self.modus == "KLMK":
            self.text = "In diesem spannenden Spielmodus spielt ihr gemeinsam gegen ein anderes Team, ihr habt die Möglichkeit, euch innerhalb eures eigenen Teams vor der Beantwortung der Fragen abzustimmen. 💪👥 Setzt eure Köpfe zusammen, diskutiert eure Antworten und kämpft gemeinsam gegen euren Gegner! 🤝💡 Zeigt, wie gut ihr als Team harmoniert und euer geballtes Wissen zum Sieg führen kann! 🏆🌟\n\n❗SPIELHINWEIS❗\nIhr trefft auf Single-Choice und Multiple-Choice Fragen, bei denen ihr Buttons für die Antworten erhaltet. Bei offenen Fragen fügt ihr einfach ein '#' zur Antwort hinzu.\nZudem könnt ihr Nachrichten an die andere Gruppe senden, indem ihr am Anfang eurer Nachricht '@Gegner' verwendet."
        elif self.modus == "KL":
            self.text = "In diesem spannenden Spielmodus spielt ihr gemeinsam. 👥💡 Tauscht euch vor der Beantwortung jeder Frage aus, sodass ihr euer Wissen und eure Stärken vereint, um die Herausforderungen zu meistern! 🤝🏆 Lasst die Teamarbeit den Weg zum Erfolg ebnen! 🌟💪\n\n❗SPIELHINWEIS❗\nIhr trefft auf Single-Choice und Multiple-Choice Fragen, bei denen ihr Buttons für die Antworten erhaltet. Bei offenen Fragen fügt ihr einfach ein '#' zur Antwort hinzu."
        elif self.modus == "OKK":
            self.text = "In diesem herausfordernden Spielmodus spielst du alleine und du kannst dein eigenes Wissen und deine Fähigkeiten unter Beweis stellen, während du dich den Quizfragen stellst! 💡🧠 Lass deinen Ehrgeiz entfachen und zeig, was du alleine draufhast!\n\n❗SPIELHINWEIS❗\nDu triffst auf Single-Choice und Multiple-Choice Fragen, bei denen du Buttons für die Antworten erhältst. Bei offenen Fragen füge einfach ein '#' zur Antwort hinzu."

    def to_dict(self):
        return {
            'id': self.id,
            'modus': self.modus,
            'exceeded': self.exceeded,
            'evaluated': self.evaluated,
            'task': self.task, 
            'text': self.text,
            'buttons': self.buttons
        }

async def set_introduction(slot_value, tracker, dispatcher, competition_mode_handler, session_handler):
    requested_slot = get_requested_slot(tracker)
    if requested_slot and  'introduction' in requested_slot and "set_introduction" in slot_value:
        active_loop = tracker.active_loop.get('name') 
        modus = '_'.join(active_loop.split('_')[2:])
        
        '''
        check if opponent group has answered
        '''
        if modus == 'KLMK':
            dispatcher.utter_message(response="utter_waiting_of_opponent")
            return {requested_slot: 'answered', "random_person": None, "flag": None,  "countdown": None}

        filter = session_handler.get_session_filter(tracker)
        await competition_mode_handler.set_status('evaluated', 'modus', filter, session_handler.session_collection, True)

        # set random teamname for KLOK Modus
        if modus == 'KLOK':
            team_name = generate_unique_team_id()
            text = f"Ich habe euren Teamnamen festgelegt. Der Teamname für euch lautet: {team_name} 🚀💥"
            game_mode_handler = GameModeHandler()
            await game_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)
            await ben_is_typing(tracker.get_slot('countdown'), competition_mode_handler)
            dispatcher.utter_message(response="utter_waiting_of_opponent")
            return { requested_slot: 'answered',"teamname_value": team_name,  "random_person": None, "flag": None,  "countdown": None}
        else:
            await ben_is_typing(tracker.get_slot('countdown'), competition_mode_handler)

            return {requested_slot: 'answered', "random_person": None, "flag": None,  "countdown": None, "activated_reminder_comp": None}
    else:
        print("DEBUG: VALIDATE  INTRODUCTION")
        return{requested_slot: "answered"}


def generate_unique_team_id(length=3):
    characters = string.ascii_letters + string.digits
    return 'Team-' + ''.join(random.choice(characters) for _ in range(length))
