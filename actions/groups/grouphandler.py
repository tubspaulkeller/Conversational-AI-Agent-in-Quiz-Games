

from actions.common.common import async_connect_to_db, get_credentials
from actions.groups.group import Group
from actions.groups.groupanswer import GroupAnswer
import logging
logger = logging.getLogger(__name__)
class GroupHandler:
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.group_collection = async_connect_to_db(self.db, 'Groups')

    async def create_group(self, users, group_id, group_title):
        '''
        create group dict with channel_id as key and a list of user with id and name as value
        '''
        new_group = Group(group_id, group_title)
        for user in users:
            if await self.check_user_same_name(new_group, user):
                new_group.add_user({'username': user['username'] + ' ' + user['lastname'] ,'lastname' : user['lastname'], 'user_id': user['user_id']})
            new_group.add_user({'username': user['username'], 'lastname' : user['lastname'], 'user_id': user['user_id']})
        return new_group.to_dict()

    async def get_group(self, group_id):
        '''
        get credentials of requested group
        '''

        filter = {"group_id": str(group_id)}
        try:
            existing_group = await self.group_collection.find_one(filter)
            if existing_group:
                return existing_group 
            else:
                return None 
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  

    def get_group_slot(self, tracker):
        '''
        get the members of the group through using slot
        '''
        try:
            return tracker.get_slot("my_group")
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  
            
    async def check_user_list_changes(self, existing_users, new_users, group_id, group_title):
        '''
        check if users of the group have changed
        '''
        try:
             # Convert existing_users to a list if it's a dictionary
            existing_user_ids = {user['user_id'] for user in existing_users}
            new_user_ids = {user['user_id'] for user in new_users}
            
            # Find removed users
            removed_users = [user for user in existing_users if user['user_id'] not in new_user_ids]
            if removed_users:
                for removed_user in removed_users:
                    print(removed_user)
                    existing_users.remove(removed_user)
            if existing_user_ids == new_user_ids and len(removed_users) == 0:
                return None
            return await self.create_group(new_users, group_id, group_title)
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  

    async def check_user_same_name(self, group, user):
        '''
        Check if a user with the same name already exists in the group
        @ True: change the username of the existing user to firstname + lastname
        '''
        try:
            for existing_user in group.users:
                if existing_user['username'] == user['username']:
                    # Update the user's username in the database
                    filter = {"group_id": group.group_id}
                    group_object = await self.group_collection.find_one(filter)
                    for index, user in enumerate(group_object['users']):
                        if user['user_id'] == existing_user['user_id']:                        
                            update_username = {"$set": {f"users.{str(index)}.username":  existing_user['username'] + ' ' + existing_user['lastname']}}
                            username_filter = {
                                "channel_id": session_object['channel_id'], 
                                "users.user_id": existing_user['user_id']
                                }
                        self.group_collection.update_one(username_filter, update_username)
                    return True
                return False
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  
            return False

    async def checked_and_updated_group(self, new_users, channel_id, group_title):
        """
        Check if a group with the specified ID exists.
        If the group exists, update it with the new group users.
        If the group does not exist or has no distinct users, create a new group with the ID and group users.
        Return True if the group already exists or is updated successfully.
        Return False if an error occurred.
        """
        filter = {"group_id": str(channel_id)}
        try:
            existing_group = await self.group_collection.find_one(filter)
            if existing_group:
                existing_users = existing_group['users']
                new_group = await self.check_user_list_changes(existing_users, new_users, channel_id, group_title)
                if  new_group is not None:
                    # delete old group 
                    await self.group_collection.delete_one(filter)
                    # add group with new users
                    print("\033[94mGruppe existiert, es gibt neue User\033[0m")
                    result = await self.group_collection.insert_one(new_group)
                    return new_group
                print("\033[94mGruppe existiert, es gibt keine Änderungen\033[0m")
                return existing_group
            # Create a new group with the ID and group users
            new_group = await self.create_group(new_users, channel_id, group_title)
            await self.group_collection.insert_one(new_group)
            return new_group
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e)  
            return False

    def created_group_answer(self, channel_id, question_id, answer):
        '''
            return dict with user cred and answer, if no value is None
        '''
        group_answer = GroupAnswer(
            channel_id = channel_id,
            question_id = question_id,
            answer = answer ).to_dict()
        all_values_not_none = all(value is not None for value in group_answer.values())

        if all_values_not_none:
            return group_answer
        else: 
            return None
