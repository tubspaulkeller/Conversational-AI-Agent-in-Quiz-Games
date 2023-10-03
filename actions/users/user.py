class User:
    def __init__(self, username, lastname, user_id):
        self.username = username
        self.lastname = lastname
        self.user_id = user_id

    def to_dict(self):
        return {
            'username': self.username,
            'lastname': self.lastname,
            'user_id': self.user_id,
        }

    @classmethod
    def from_dict(cls, data):
        username = data['username']
        lastname = data['lastname']
        user_id = data['user_id']
        return cls(username, lastname, user_id)
