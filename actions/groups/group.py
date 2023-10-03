class Group:
    def __init__(self, group_id, title):
        self.group_id = group_id
        self.title = title
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def get_users(self):
        return self.users
    
    def to_dict(self):
        return {
            'group_id': self.group_id,
            'title':self.title, 
            'users': self.users
        }
    
    @classmethod
    def from_dict(cls, data):
        group_id = data['group_id']
        title = data['title']
        group = cls(group_id)
        group.users = data['users']
        return group