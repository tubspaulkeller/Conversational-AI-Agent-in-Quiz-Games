## Rasa 
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    UserUtteranceReverted,
    FollowupAction,
    AllSlotsReset,
    Restarted,
    SlotSet,
    EventType,
    LoopInterrupted,
    ActionExecutionRejected
)
import threading
import asyncio
## Telethon Client
from actions.telegram_members.telethonhandler import TelethonHandler
from actions.users.userhandler import UserHandler
from actions.users.user import User
from actions.groups.grouphandler import GroupHandler
from actions.common.common import get_credentials
import logging
logger = logging.getLogger(__name__)

class ActionGetChannelMembers(Action):

    def name(self) -> Text:
        return "action_get_channel_members"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            if not tracker.get_slot('my_group'): 
                user_handler = UserHandler() 
                telethon_handler = TelethonHandler()
                team_mates, is_user = await telethon_handler.get_users(tracker.sender_id) 
                print("\033[94mTEAM_MATES:\033[0m \n%s" %team_mates)
                if '_id' in team_mates:
                    team_mates['_id'] = str(team_mates['_id'])
                return[SlotSet('is_user', is_user), SlotSet('my_group',team_mates), FollowupAction("action_start")]
            else:
                print("\033[94mdont call get members again\033[0m")
        except Exception as e:
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return[SlotSet('is_user', is_user), SlotSet('my_group',team_mates), FollowupAction("action_start")]
