import datetime

class Timestamp:
    def __init__(self,sender_id, quest_id, loop, opponent_id):
        self.group_id = sender_id
        self.quest_id = quest_id
        self.loop = loop
        self.timestamp = datetime.datetime.now().timestamp() 
        self.opponent_id = opponent_id

    def to_dict(self):
        return {
            'group_id': self.group_id,
            'quest_id': self.quest_id,
            'timestamp': self.timestamp,
            'loop': self.loop,
            'opponent_id': self.opponent_id
        }