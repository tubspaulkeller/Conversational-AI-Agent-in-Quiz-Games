from actions.common.common import get_credentials, get_dp_inmemory_db, get_countdown_value
class Countdown: 
    def __init__(self,sender_id, quest_id, loop, message_id = None, question = None, text = None):
        self.countdown = get_countdown_value(quest_id, loop)
        self.intervall = int(get_credentials('INTERVALL'))
        self.sender_id = sender_id 
        self.quest_id = quest_id
        self.message_id = message_id
        self.question = question
        self.text = text
        self.buttons = []

    def to_dict(self):
        countdown_dict = {
            'countdown': self.countdown,
            'intervall': self.intervall,
            'sender_id': self.sender_id,
            'quest_id': self.quest_id,
            'message_id': self.message_id,
            'question': self.question,
            'text': self.text,
            'buttons': self.buttons
        }
        if self.message_id is not None:
            countdown_dict['message_id'] = self.message_id
        if self.question is not None:
            countdown_dict['question'] = self.question
        if self.text is not None:
            countdown_dict['text'] = self.text
        return countdown_dict
    
    def __setitem__(self, key, value):
        if not key is None:
            self.key = value
        else:
            raise KeyError("Invalid key")
    
    @classmethod
    def from_dict(cls, countdown_dict):
        countdown = countdown_dict['countdown']
        intervall = countdown_dict['intervall']
        sender_id = countdown_dict['sender_id']
        quest_id = countdown_dict['quest_id']
        message_id = countdown_dict.get('message_id')
        question = countdown_dict['question']
        text = countdown_dict['text']
        buttons = countdown_dict['buttons']
        return cls(countdown, intervall, sender_id, quest_id, message_id, question, text, buttons)
