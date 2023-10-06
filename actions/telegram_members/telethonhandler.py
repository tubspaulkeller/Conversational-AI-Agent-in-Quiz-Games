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
from actions.common.common import get_credentials
import threading
import sqlite3
from rasa_sdk.events import ReminderScheduled, ReminderCancelled, FollowupAction, SlotSet
import logging
logger = logging.getLogger(__name__)
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
                if sender_id.startswith("-"):
                    telethon_object = await client.get_entity(get_credentials(sender_id + '_' +'TELEGRAM_INVITE_LINK')) #await client.get_entity(int(sender_id))
                else: 
                    telethon_object = await client.get_entity(int(sender_id)) #await client.get_entity(int(sender_id))

                print("TELETHONOBJECT", telethon_object)
                if isinstance(telethon_object, telethon.tl.types.Channel):
                    users = await client.get_participants(telethon_object)
                else:
                    existing_user = await user_handler.user_collection.find_one({"user_id": int(telethon_object.id)})
                    if not existing_user:
                        new_user = User(username=telethon_object.first_name, lastname=telethon_object.last_name, user_id=telethon_object.id)
                        await user_handler.inserted_user(new_user)
                        existing_user = new_user.to_dict()
                    return existing_user, True

                users_list = []
                for user in users:
                    # if user is me or bot: 
                    if not (str(user.id) == get_credentials('ADMIN_ID') or str(user.id) == get_credentials('JOHN_ID')  or user.bot):
                        existing_user = await user_handler.user_collection.find_one({"user_id": int(user.id)})
                        if not existing_user and str(user.id) != str(sender_id):
                            new_user = User(username=user.first_name, lastname=user.last_name, user_id=user.id)
                            users_list.append(new_user.to_dict())
                            await user_handler.inserted_user(new_user)
                        elif existing_user:
                            users_list.append(existing_user)

                return await group_handler.checked_and_updated_group(users_list, sender_id, telethon_object.title), False
            
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    print("\033[91mcatched Exception:\033[0m")
                    await asyncio.sleep(2)  

            except Exception as e:
                logger.exception("\033[91Exception: %s\033[0m" %e)
                return FollowupAction("action_restart")

            return None, False







