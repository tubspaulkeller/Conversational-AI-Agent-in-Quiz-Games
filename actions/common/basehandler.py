import asyncio
import httpx
import pymongo
import aiofiles
from actions.common.common import async_connect_to_db, get_credentials, setup_logging
from telegram import Bot
import logging
logger = setup_logging()



class BaseHandler:
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.bot = Bot(token=get_credentials("TELEGRAM_ACCESS_TOKEN"))
        self.send_msg_semaphore = asyncio.Semaphore(1)
        self.message_queue = []  # Neue Liste zum Speichern der eingehenden Nachrichten

    async def telegram_bot_send_message(self, type, sender_id, msg, message_id=None, parse_mode="Markdown", disable_notification=True, dispatcher = None):
        self.message_queue.append((type, sender_id, msg, message_id, parse_mode, disable_notification,dispatcher))
        return await self.process_message_queue()

    async def process_message_queue(self):
            async with self.send_msg_semaphore:
                while self.message_queue:
                    try:
                        type, sender_id, msg, message_id, parse_mode, disable_notification, dispatcher = self.message_queue.pop(0)
                        async with httpx.AsyncClient(timeout=120) as client:  # TimeoutValue
                            if type == 'text':
                                response = await client.post(f"https://api.telegram.org/bot{self.bot.token}/sendMessage", json={"chat_id": sender_id, "text": msg, "parse_mode": parse_mode, "disable_notification": disable_notification})
                                result = response.json()
                                if result:
                                    msg_id = result['result']['message_id']
                                    await asyncio.sleep(1.25)
                                    return int(msg_id)
                                else:
                                    logger.error(f"Error in process_message_queue: sending message: {result}")

                                    
                            elif type == 'photo':
                                if msg.startswith('http'):  # Check if msg is a URL
                                    data = {"chat_id": sender_id, "photo": msg, "disable_notification": disable_notification}
                                else:
                                    # Open the local image file in binary mode
                                    async with aiofiles.open(msg, 'rb') as img_file:
                                        img_data = await img_file.read()
                                        data = {"chat_id": sender_id, "disable_notification": disable_notification}
                                        files = {"photo": img_data}  # Send the image file as part of the request
                                response = await client.post(
                                    f"https://api.telegram.org/bot{self.bot.token}/sendPhoto",
                                    data=data,
                                    files=files if not data.get('photo') else None  # Use files parameter only if sending local image
                                )
                                result = response.json()
                                if result:
                                    msg_id = result['result']['message_id']
                                    await asyncio.sleep(1.25)
                                    return int(msg_id)
                                else:
                                    logger.error(f"Error in process_message_queue: sending message: {result}")
                                #print(f"Sent photo message with ID: {msg_id}")
                            elif type == 'edit':
                                await client.post(f"https://api.telegram.org/bot{self.bot.token}/editMessageText", json={"chat_id": sender_id, "message_id": message_id, "text": msg, "parse_mode": parse_mode})
                                await asyncio.sleep(1.25)
                                #print(f"Edited message with ID: {message_id}")
                            elif type == 'pin':
                                await asyncio.sleep(1.25)
                                await client.post(f"https://api.telegram.org/bot{self.bot.token}/pinChatMessage", json={"chat_id": sender_id, "message_id": message_id})
                                # await asyncio.sleep(1.25)
                                #print(f"Pinned message with ID: {message_id}")
                    
                    except Exception as e:
                        # Hier können Sie andere Ausnahmen behandeln
                        logger.error(f"Error in process_message_queue: while processing message: {e}")
