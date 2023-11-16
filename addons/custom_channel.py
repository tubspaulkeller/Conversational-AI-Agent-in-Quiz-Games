import asyncio
import aiohttp
import json
import logging
from copy import deepcopy
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    Update,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Message,
)
from aiogram.utils.exceptions import TelegramAPIError
from typing import Dict, Text, Any, List, Optional, Callable, Awaitable

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
from rasa.shared.constants import INTENT_MESSAGE_PREFIX
from rasa.shared.core.constants import USER_INTENT_RESTART
from rasa.shared.exceptions import RasaException
from rasa_sdk import Tracker
import time
import datetime
from telegram import Bot as TelegramBot

# actions
from actions.common.common import get_credentials, async_connect_to_db, ask_openai, setup_logging
from actions.timestamps.timestamphandler import TimestampHandler
from actions.groups.grouphandler import GroupHandler
logger = setup_logging()


class TelegramOutput(Bot, OutputChannel):
    """Output channel for Telegram."""

    # skipcq: PYL-W0236
    @classmethod
    def name(cls) -> Text:
        return "telegram"

    def __init__(self, access_token: Optional[Text]) -> None:
        super().__init__(access_token)

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        """Sends text message."""
        try:
            for message_part in text.strip().split("\n\n"):
                await self.send_message(recipient_id, message_part)
        except Exception as e:
            logger.exception(e)

    async def send_image_url(
        self, recipient_id: Text, image: Text, **kwargs: Any
    ) -> None:
        """Sends an image."""
        await self.send_photo(recipient_id, image)

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        button_type: Optional[Text] = "inline",
        **kwargs: Any,
    ) -> None:
        """Sends a message with keyboard.

        For more information: https://core.telegram.org/bots#keyboards

        :button_type inline: horizontal inline keyboard

        :button_type vertical: vertical inline keyboard

        :button_type reply: reply keyboard
        """
        if button_type == "inline":
            reply_markup = InlineKeyboardMarkup()
            button_list = [
                InlineKeyboardButton(s["title"], callback_data=s["payload"])
                for s in buttons
            ]
            reply_markup.row(*button_list)

        elif button_type == "vertical":
            reply_markup = InlineKeyboardMarkup()
            [
                reply_markup.row(
                    InlineKeyboardButton(
                        s["title"], callback_data=s["payload"])
                )
                for s in buttons
            ]

        elif button_type == "reply":
            reply_markup = ReplyKeyboardMarkup(
                resize_keyboard=False, one_time_keyboard=True
            )
            # drop button_type from button_list
            button_list = [b for b in buttons if b.get("title")]
            for idx, button in enumerate(buttons):
                if isinstance(button, list):
                    reply_markup.add(KeyboardButton(
                        s["title"]) for s in button)
                else:
                    reply_markup.add(KeyboardButton(button["title"]))
        else:
            logger.error(
                "Trying to send text with buttons for unknown "
                "button type {}".format(button_type)
            )
            return
        await self.send_message(recipient_id, text, reply_markup=reply_markup)

    async def send_custom_json(
        self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any
    ) -> None:
        """Sends a message with a custom json payload."""
        json_message = deepcopy(json_message)

        recipient_id = json_message.pop("chat_id", recipient_id)

        send_functions = {
            ("text",): "send_message",
            ("photo",): "send_photo",
            ("audio",): "send_audio",
            ("document",): "send_document",
            ("sticker",): "send_sticker",
            ("video",): "send_video",
            ("video_note",): "send_video_note",
            ("animation",): "send_animation",
            ("voice",): "send_voice",
            ("media",): "send_media_group",
            ("latitude", "longitude", "title", "address"): "send_venue",
            ("latitude", "longitude"): "send_location",
            ("phone_number", "first_name"): "send_contact",
            ("game_short_name",): "send_game",
            ("action",): "send_chat_action",
            (
                "title",
                "decription",
                "payload",
                "provider_token",
                "start_parameter",
                "currency",
                "prices",
            ): "send_invoice",
        }

        for params in send_functions.keys():
            if all(json_message.get(p) is not None for p in params):
                args = [json_message.pop(p) for p in params]
                api_call = getattr(self, send_functions[params])
                await api_call(recipient_id, *args, **json_message)


class MyIO(InputChannel):
    """Telegram input channel"""

    @classmethod
    def name(cls) -> Text:
        return "telegram"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(
            credentials.get("access_token"),
            credentials.get("verify"),
            credentials.get("webhook_url"),
        )

    def __init__(
        self,
        access_token: Optional[Text],
        verify: Optional[Text],
        webhook_url: Optional[Text],
        debug_mode: bool = True,

    ) -> None:
        self.access_token = access_token
        self.verify = verify
        self.webhook_url = webhook_url
        self.debug_mode = debug_mode
        self.collab_dict = {}
        self.db = get_credentials("DB_NAME")
        self.collab_collection = async_connect_to_db(self.db, 'Collaboration')
        self.session_collection = async_connect_to_db(self.db, 'Session')
        self.bot = TelegramBot(token=get_credentials("TELEGRAM_ACCESS_TOKEN"))

    @staticmethod
    def _is_location(message: Message) -> bool:
        return message is not None and message.location is not None

    @staticmethod
    def _is_user_message(message: Message) -> bool:
        return message is not None and message.text is not None

    @staticmethod
    def _is_edited_message(message: Update) -> bool:
        return message.edited_message is not None

    @staticmethod
    def _is_button(message: Update) -> bool:
        return message.callback_query is not None

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        telegram_webhook = Blueprint("telegram_webhook", __name__)
        out_channel = self.get_output_channel()

        @telegram_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @telegram_webhook.route("/set_webhook", methods=["GET", "POST"])
        async def set_webhook(_: Request) -> HTTPResponse:
            s = await out_channel.set_webhook(self.webhook_url)
            if s:
                logger.info("Webhook Setup Successful")
                return response.text("Webhook setup successful")
            else:
                logger.warning("Webhook Setup Failed")
                return response.text("Invalid webhook")

        @telegram_webhook.route("/webhook", methods=["GET", "POST"])
        async def message(request: Request) -> Any:
            if request.method == "POST":
                request_dict = request.json
                if isinstance(request_dict, Text):
                    request_dict = json.loads(request_dict)
                # Debug
              #  print("\033[94mrequest_dict\033[0m\n%s" % request_dict)
                #### added Logic#####

                loop = None
                text_message = None
                button_message = None
                date = None
                try:
                    # textmsg
                    if not 'callback_query' in request_dict:
                        #group_id = request_dict['message']['chat']['id']
                        group_id = request_dict['message']['chat']['id'] if 'message' in request_dict and 'chat' in request_dict[
                            'message'] and 'id' in request_dict['message']['chat'] else None
                        if request_dict['message']['from']['is_bot'] == False:
                            timestamp_handler = TimestampHandler()
                            timestamp, loop, quest_id, opponent_id = await timestamp_handler.get_timestamp(group_id, 'waiting')
                            text_message = request_dict['message']['text']
                            date = request_dict['message']['date']

                    # Messages with @Ben pass through Rasa to call openai
                    if text_message and ('@Ben' in text_message or '@ben' in text_message or get_credentials("BOT_NAME") in text_message):
                        # + text_message
                        request_dict['message']['text'] = '/ask_ben'
                   #     print("msg",  request_dict['message']['text'])
                    # telegram start
                    elif (text_message and '/start' in text_message):
                        text_message = ""
                        text_message = "# restart"
                        request_dict['message']['text'] = text_message

                    # Messages with # do not ignore for answering questions
                    elif (text_message and '#' not in text_message):
                     #   print("\033[94mIGNORE MESSAGE..\033[0m")
                      #  print("\033[94mMESSAGE: %s..\033[0m" % text_message)
                        if loop == 'quiz_form_KLOK' or loop == 'quiz_form_KLMK':

                            if "@Gegner" in text_message or "@gegner" in text_message:
                                replacement = "@Von der anderen Gruppe: "
                                if "@Gegner" in text_message:
                                    new_text = text_message.replace(
                                        "@Gegner", replacement)
                                elif "@gegner" in text_message:
                                    new_text = text_message.replace(
                                        "@Gegner", replacement)
                                await out_channel.send_text_message(str(opponent_id), new_text)

                        # boost collaboration
                        if loop == 'quiz_form_KL' or loop == 'quiz_form_KLMK':
                            '''
                            create an groupuser_object with a counter, which gives information about how much a person has said
                            '''
                            filter = {"group_id": group_id}
                            existing_group = await self.collab_collection.find_one(filter)
                            if not existing_group:
                                self.collab_dict = {
                                    'group_id': request_dict['message']['chat']['id'], 'users': []}
                                grouphandler = GroupHandler()
                                my_group = await grouphandler.get_group(request_dict['message']['chat']['id'])
                                for user in my_group['users']:
                                    user_dict = {
                                        'user_id': user['user_id'],
                                        'username': user['username'],
                                        'group_id': my_group['group_id'],
                                        'counter': 0
                                    }
                                    self.collab_dict['users'].append(user_dict)
                                await self.collab_collection.insert_one(self.collab_dict)
                                existing_group = self.collab_dict

                            # if a person says something, increase counter for this person
                            for user in existing_group['users']:
                                if user['user_id'] == request_dict['message']['from']['id'] and user['group_id'] == str(request_dict['message']['chat']['id']):
                                    user['counter'] += 1
                                    break
                            # update in DB
                            update_counter = {
                                "$set": {'users': existing_group['users']}}
                            await self.collab_collection.update_one(filter, update_counter)
                        return response.text("", status=204)
                    #else:
                        #print("\033[94m PASS MESSAGE THROUGH TO RASA\033[0m")
                except Exception as e:
                    logger.exception(e)

            ######### Logic end ########
                update = Update(**request_dict)
                credentials = await out_channel.get_me()

                ### added ###
                # get User Credentials
                # a telegram group has a unique ID, if we are interested in which perosn has given a answer we need to get the user ID, therefore we add into the metadata of the message the
                # ID of the which has answered
                try:
                    if update.callback_query:
                        group_user_cred = update.callback_query
                        groupuser_id = str(group_user_cred["from"]["id"])
                        groupuser_name = str(
                            group_user_cred["from"]["first_name"])

                    else:
                        group_user_cred = update
                        groupuser_id = str(
                            group_user_cred["message"]["from"]["id"])
                        groupuser_name = str(
                            group_user_cred["message"]["from"]["first_name"])
                except Exception as e:
                    logger.exception(e)

                ############

                if not credentials.username == self.verify:
                    logger.debug(
                        "Invalid access token, check it matches Telegram")
                    return response.text("failed")
                if self._is_button(update):
                    msg = update.callback_query.message
                    text = update.callback_query.data

                elif self._is_edited_message(update):
                    msg = update.edited_message
                    text = update.edited_message.text
                else:
                    msg = update.message
                    if self._is_user_message(msg):
                        text = msg.text.replace("/bot", "")
                    elif self._is_location(msg):
                        text = '{{"lng":{0}, "lat":{1}}}'.format(
                            msg.location.longitude, msg.location.latitude
                        )
                    else:
                        return response.text("success")
                sender_id = msg.chat.id
                metadata = self.get_metadata(request)

                ###### ADDED #########
                # put groupuser_id and question for ben to Metadata, so you have access through tracker (e.g. tracker_current_state)
                if metadata is None:
                    metadata = {}
                    try:
                        metadata.update({"ask_ben": text_message})
                        metadata.update(
                            {"groupuser_id": groupuser_id, "groupuser_name": groupuser_name})
                    except Exception as e:
                        logger.exception(e)
                else:
                    try:
                        metadata.update({"ask_ben": text_message})
                        metadata.update({"groupuser_id": groupuser_id})
                    except Exception as e:
                        logger.exception(e)
                ####################################################################################
                try:
                    if text == (INTENT_MESSAGE_PREFIX + USER_INTENT_RESTART):
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                        await on_new_message(
                            UserMessage(
                                "/start",
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                    else:
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                except Exception as e:
                    logger.error(
                        f"Exception when trying to handle message.{e}")
                    logger.exception(e)
                    logger.debug(e, exc_info=True)
                    if self.debug_mode:
                        raise
                    pass

                return response.text("success")

        return telegram_webhook

    def get_output_channel(self) -> TelegramOutput:
        """Loads the telegram channel."""
        channel = TelegramOutput(self.access_token)

        try:

            asyncio.run(channel.set_webhook(url=self.webhook_url))
        except TelegramAPIError as error:
            raise RasaException(
                "Failed to set channel webhook: " + str(error)
            ) from error

        return channel
