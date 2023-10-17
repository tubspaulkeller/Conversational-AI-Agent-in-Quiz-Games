
from actions.common.common import async_connect_to_db, get_credentials, setup_logging
from actions.users.useranswer import UserAnswer
import logging
logger = setup_logging()


class UserHandler:
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.user_collection = async_connect_to_db(self.db, 'Users')

        
    async def _user_exists(self,user):
        '''
        return True, if user allready exists 
        return False, if user does not exist or Error
        '''
        filter = {'user_id': user.user_id}
        try:
            existing_user = await self.user_collection.find_one(filter)
            if existing_user is None:
                return False
            else:
                return True
        except Exception as e:
            
            logger.exception(e)
            return False

    async def get_user(self, sender_id):
        filter = {"user_id": int(sender_id)}
        try:
            existing_user = await self.user_collection.find_one(filter)
            if existing_user:
                return existing_user 
            else:
                return None 
        except Exception as e: 
            logger.exception(e)  

    async def inserted_user(self, user):
        '''
        return True, if user got inserted 
        return False, if user allready exists or Error
        '''
        try:
            if not await self._user_exists(user):
                try:
                    result = await self.user_collection.insert_one(user.to_dict())
                    if result.inserted_id:
                        return True
                    else:
                        print("\033[91mFehler:\033[0m beim Einfügen des Users.")
                        return False
                except Exception as e:
                    print("\033[91mException:\033[0m user inserting into DB: %s" %e)
                    return False
            else:
                return False
        except Exception as e: 
            logger.exception(e)  


    def created_user_answer(self, channel_id, question_id, user_id, username, answer):
        '''
            return dict with user cred and answer, if no value is None
        '''
        try:
            user_answer = UserAnswer(
                channel_id = channel_id,
                question_id = question_id,
                user_id = user_id,
                username = username, 
                answer = answer ).to_dict()
            all_values_not_none = all(value is not None for value in user_answer.values())

            if all_values_not_none:
                return user_answer
            else: 
                return None
        except Exception as e: 
            logger.exception(e)  


