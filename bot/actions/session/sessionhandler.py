
from actions.session.session import Session
from actions.common.common import async_connect_to_db, get_credentials
import logging
logger = logging.getLogger(__name__)
class SessionHandler:
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.session_collection = async_connect_to_db(self.db, 'Session')
        self.solution_collection = async_connect_to_db(self.db, 'Solutions')


    async def exist_session(self, filter, active_loop, sender_id, group):
        try: 
            existing_session_object = await self.session_collection.find_one(filter)
            if existing_session_object is None:
                new_session = Session(sender_id)
                new_session.set_other_group(filter['other_group'])
                if active_loop != 'quiz_form_OKK':
                    new_session.set_group_title(group['title'])
                    new_session.set_users(group['users'])
                res = await self.session_collection.insert_one(new_session.to_dict())
                if res.inserted_id:
                    return True
            return True
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  
            return False


    def get_session_filter(self, tracker):
        filter = {
            "channel_id": tracker.sender_id,     
            "other_group": tracker.get_slot("opponent_id")
        }
        return filter

    def get_opponent(self, tracker):
        active_loop = tracker.active_loop.get('name') 
        ''' get opponent if exists'''
        if active_loop == 'quiz_form_KLOK' or active_loop == 'quiz_form_KLMK':
            group_id_opponent = int(get_credentials(tracker.sender_id))
            return int(group_id_opponent)
        elif active_loop == 'quiz_form_KL' or active_loop == 'quiz_form_OKK':
            group_id_opponent = "-1"
            return group_id_opponent

    async def get_session_object(self, tracker):
        collection = self.session_collection
        filter = self.get_session_filter(tracker)
        return await collection.find_one(filter)

    async def max_points(self):
        solution_collection = async_connect_to_db("rasa_ben", 'Solutions')
        try:
            max_points = 0 
            cursor = solution_collection.find()
            solutions = await cursor.to_list(length=None) 
            for solution in solutions:
                max_points += solution['points']
            return max_points
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  
            return 0
