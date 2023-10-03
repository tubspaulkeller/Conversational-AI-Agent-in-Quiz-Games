
import datetime
class GroupAnswer:
    def __init__(self, channel_id, question_id, answer):
        self.channel_id = channel_id
        self.question_id = question_id
        self.answer = answer
        self. timestamp =  datetime.datetime.now().timestamp()

    def to_dict(self):
        return {
            'channel_id': self.channel_id,
            'question_id': self.question_id,
            'answer': self.answer,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        channel_id = data['channel_id']
        question_id = data['question_id']
        answer = data['answer']
        return cls(channel_id, question_id, user_id, username, answer)

