### Telegram 
import telethon
from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from actions.users.userhandler import UserHandler
from telethon.sessions import StringSession
from actions.users.user import User
from actions.groups.grouphandler import GroupHandler
from actions.common.common import get_credentials, setup_logging
import threading
import sqlite3
from rasa_sdk.events import ReminderScheduled, ReminderCancelled, FollowupAction, SlotSet
import logging
logger = setup_logging()


class TelethonHandler:
    def __init__(self):
        self.api_id = int(get_credentials('API_ID'))
        self.api_hash = get_credentials('API_HASH')
        self.phone_number = get_credentials('PHONE_NUMBER')
        self.session_string = get_credentials('SESSION_STRING')
        


    async def get_users(self, sender_id):
        async with TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash) as client:            
            user_handler = UserHandler()
            group_handler = GroupHandler()

            try:
                print("SENDER", sender_id)
                telethon_object = None
                if sender_id.startswith("-"):
                    # ID is a Group_ID we want the credentials for each group member, therefore we use the invite_link
                    telethon_object = await client.get_entity(get_credentials(sender_id + '_' +'TELEGRAM_INVITE_LINK')) #await client.get_entity(int(sender_id)) 
                    #print("TELETHONOBJECT", telethon_object)
                else:
                    # in single mode we are not interessted in user credentials so we define a fake user
                    existing_user = await user_handler.user_collection.find_one({"user_id": sender_id})
                    if not existing_user:
                        new_user = User(username="John", lastname="Doe", user_id=sender_id)
                        await user_handler.inserted_user(new_user)
                        existing_user = new_user.to_dict()
                    return existing_user, True
                
                if isinstance(telethon_object, telethon.tl.types.Channel):
                    # get users for a group
                    users = await client.get_participants(telethon_object)
                    # otherwise we creeate a user lists for the group
                    users_list = []
                    for user in users:
                        # if user is me, or John, or bot: 
                        # set ADMIN_ID to -1 so, I can play with others in the group, if my person has to be ignored set ADMIN_ID to my ID, same for JOHN_ID, which is the second Account, which I used for testing 
                        # or str(user.id) == get_credentials('JOHN_ID') or str(user.id) == get_credentials('LOTTA_ID') or str(user.id) == get_credentials('TOM_ID')
                        if not (str(user.id) == get_credentials('ADMIN_ID') or user.bot):
                            # check if user exists otherwise create a new user
                            existing_user = await user_handler.user_collection.find_one({"user_id": int(user.id)})
                            if not existing_user and str(user.id) != str(sender_id):
                                new_user = User(username=user.first_name, lastname=user.last_name, user_id=user.id)
                                users_list.append(new_user.to_dict())
                                await user_handler.inserted_user(new_user)
                            elif existing_user:
                                users_list.append(existing_user)
                    # check if there are any changes due to users in the group, e.g. a user left the group or a new user joint the group
                    return await group_handler.checked_and_updated_group(users_list, sender_id, telethon_object.title), False
                else: 
                    return FollowupAction("action_restart")
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    print("\033[91mcatched Exception:\033[0m")
                    await asyncio.sleep(2)  

            except Exception as e:
                logger.exception(e)
                return FollowupAction("action_restart")








