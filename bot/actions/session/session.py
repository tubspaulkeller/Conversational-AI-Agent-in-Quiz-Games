class Session:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.group_title = None
        self.other_group = None
        self.users = None
        self.questions = []
        self.achievements = []
        self.level = 0
        self.total_points = 0
        self.goal = None
        self.stars = 0

    def to_dict(self):
        return {
            'channel_id': self.channel_id,
            'group_title': self.group_title,
            'users': self.users,
            'questions': self.questions,
            'achievements': self.achievements,
            'total_points': self.total_points,
            'other_group': self.other_group,
            'level': self.level,
            'goal': self.goal,
            'stars': self.stars
        }
    def set_other_group(self, other_group):
        try: 
            self.other_group = other_group
        except Exception as e:
            print("\033[91mException:\033[0m session, Method: set_other_group %s", e)

    def set_group_title(self, title):
        try:
            self.group_title = title
        except Exception as e:
            print("\033[91mException:\033[0m session, Method: set_other_group %s", e)


    def set_users(self, users):
        self.users = users
    @classmethod
    def from_dict(cls, data):
        channel_id = data['channel_id']
        group_title = data['group_title']
        other_group = date['other_group']
        users = data['users']
        questions = data['questions']
        achievements = data['achievements']
        total_points = ['total_points']
        level = ['level']
        goal = ['goal']
        stars = ['stars']
        return cls(channel_id, group_title, other_group,users , questions, achievements, total_points, level, goal,stars)
