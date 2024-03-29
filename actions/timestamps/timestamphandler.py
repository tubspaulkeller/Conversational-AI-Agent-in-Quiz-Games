import datetime
from collections import OrderedDict
from actions.common.common import async_connect_to_db, get_credentials, setup_logging
from actions.session.sessionhandler import SessionHandler
import pymongo
import asyncio
logger = setup_logging()


class TimestampHandler:
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.answer_collection = async_connect_to_db(
            self.db, 'timestamps_answer')
        self.waiting_collection = async_connect_to_db(
            self.db, 'timestamps_waiting')

    def insert_new_timestamp(self, timestamp, timestamp_type):
        try:
            timestamp_doc = {
                "group_id": str(timestamp['group_id']),
                "timestamp": timestamp['timestamp'],
                "loop": timestamp['loop'],
                "quest_id": timestamp['quest_id'],
                "opponent_id": timestamp['opponent_id']
            }
            if timestamp_type == "answer":
                self.answer_collection.insert_one(timestamp_doc)
            elif timestamp_type == "waiting":
                self.waiting_collection.insert_one(timestamp_doc)
        except Exception as e:
            logger.exception(e)

    async def get_timestamp(self, group_id, timestamp_type):
        try:
            collection = self.answer_collection if timestamp_type == "answer" else self.waiting_collection
            count = await collection.count_documents({"group_id": str(group_id)})
            # Die Dokumente nach dem Zeitstempel absteigend sortieren und das erste (neueste) abrufen
            print(f"Anzahl der Dokumente: {count}")
            if count > 0:
                cursor = collection.find({"group_id": str(group_id)}).sort(
                    "timestamp", pymongo.DESCENDING)
                timestamp_info = await cursor.limit(1).next()
                timestamp = timestamp_info.get("timestamp", 0)
                loop = timestamp_info.get("loop", None)
                quest_id = timestamp_info.get("quest_id", None)
                opponent_id = timestamp_info.get("opponent_id", 0)
                return timestamp, loop, quest_id, opponent_id
            else:
                return await self.get_timestamp_infos_through_session_obj(group_id)
        except Exception as e:
            logger.exception(e)
            return await self.get_timestamp_infos_through_session_obj(group_id)


    async def get_timestamp_infos_through_session_obj(self, group_id):
        try: 
            session_handler = SessionHandler()
            session = await session_handler.session_collection.find_one({"channel_id":group_id})
            if session:
                mode = session['questions'][0]['modus']
                last_quest = session['questions'][-1]['id']
                opponent_id = session.get('other_group')  
            else:
                mode = last_quest = opponent_id = None

            loop = "quiz_form_" + mode if mode else None
            timestamp = 0
            quest_id = last_quest

            return timestamp, loop, quest_id, opponent_id

        except Exception as e:
            logger.exception(e)
            return 0, None, None, None

    async def delete_timestamps_for_group(self, group_id, timestamp_type):
        try:
            collection = self.answer_collection if timestamp_type == "answer" else self.waiting_collection
            result = await collection.delete_many({"group_id": str(group_id)})
            deleted_count = result.deleted_count
        except Exception as e:
            logger.exception(e)
