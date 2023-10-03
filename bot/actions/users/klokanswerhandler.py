import json
import threading
import logging
from collections import OrderedDict
logger = logging.getLogger(__name__)

class KlokAnswersHandler:
    def __init__(self):
        self.KLOK_ANSWERS = OrderedDict()
        self.lock = threading.Lock()
        self.file_path = "./klok_answers.json"
        self.load_klok_answers_from_file()

    def get_klok_answers_for_group(self, group_id):
        with self.lock:
            return self.KLOK_ANSWERS.get(group_id, [])

    def process_user_answer(self, group_id, user_answer, dispatcher):
        with self.lock:
            if group_id not in self.KLOK_ANSWERS:
                self.KLOK_ANSWERS[group_id] = []
            
            # Überprüfen, ob die Antwort bereits vorhanden ist, bevor sie hinzugefügt wird
            existing_answers = [answer for answer in self.KLOK_ANSWERS[group_id] if answer['user_id'] == user_answer['user_id']]
            if not existing_answers:
                text = "%s 👤  hat eine Antwort abgegeben." % user_answer['username']
                dispatcher.utter_message(text=text)
                self.KLOK_ANSWERS[group_id].append(user_answer)
                self.save_klok_answers_to_file()

    def clear_group_answers(self, group_id):
        with self.lock:
            if group_id in self.KLOK_ANSWERS:
                del self.KLOK_ANSWERS[group_id]
                self.save_klok_answers_to_file()


    def save_klok_answers_to_file(self):
        try:
            with open(self.file_path, "w") as file:
                json.dump(list(self.KLOK_ANSWERS.items()), file)
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" % e)

    def load_klok_answers_from_file(self):
        try:
            with open(self.file_path, "r") as file:
                items = json.load(file)
                self.KLOK_ANSWERS = OrderedDict(items)
        except FileNotFoundError as e:
            # If the file doesn't exist, create an empty OrderedDict
            self.KLOK_ANSWERS = OrderedDict()
            logger.exception("\033[91Exception: %s\033[0m" % e)
