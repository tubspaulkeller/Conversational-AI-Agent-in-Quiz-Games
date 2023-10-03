import datetime
class Question:
    def __init__(self, id, points, answer):
        self.id = id
        self.points = points
        self.answer = answer
        self.correct = False
        self.evaluated = False
        self.exceeded = False
        self.collaboration = False
        self.in_time = False
        self. timestamp =  datetime.datetime.now().timestamp()

    def to_dict(self):
        return {
            'id': self.id,
            'points': self.points,
            'correct': self.correct,
            'evaluated': self.evaluated,
            'exceeded': self.exceeded,
            'collaboration': self.collaboration,
            'in_time': self.in_time,
            'answer': self.answer,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        id = data['id']
        points = data['points']
        correct = data['correct']
        evaluated = data['evaluated']
        exceeded = ['exceeded']
        collaboration = ['collaboration']
        in_time = ['in_time']
        answer = ['answer']
        timestamp = ['timestamp']
        return cls(id, points, correct, evaluated, exceeded, collaboration, in_time, timestamp)