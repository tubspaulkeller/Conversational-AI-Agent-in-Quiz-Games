import json
import datetime
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class TimestampHandler:
    def __init__(self):
        self.timestamps_answer = OrderedDict()
        self.timestamps_waiting = OrderedDict()
        self.file_path_answer = "./timestamps_answering.json"
        self.file_path_waiting = "./timestamps_waiting.json"
        self.load_timestamps_from_file("answer")
        self.load_timestamps_from_file("waiting")
            
    def insert_new_timestamp(self, timestamp, timestamp_type): 
        try:
            if timestamp_type == "answer":
                self.timestamps_answer[str(timestamp['group_id'])] = {
                    "timestamp": timestamp['timestamp'],
                    "loop": timestamp['loop'],
                    "quest_id": timestamp['quest_id'],
                    "opponent_id": timestamp['opponent_id']
                }
            elif timestamp_type == "waiting":
                self.timestamps_waiting[str(timestamp['group_id'])] = {
                    "timestamp": timestamp['timestamp'],
                    "loop": timestamp['loop'],
                    "quest_id": timestamp['quest_id'],
                    "opponent_id": timestamp['opponent_id']
                }
            self.save_timestamps_to_file(timestamp_type)
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)  
    
    def get_timestamp(self, group_id, timestamp_type):
        try:
            if timestamp_type == "answer":
                timestamps = self.timestamps_answer
            elif timestamp_type == "waiting":
                timestamps = self.timestamps_waiting

            if str(group_id) in timestamps:
                timestamp_info = timestamps[str(group_id)]
                timestamp = timestamp_info["timestamp"]
                loop = timestamp_info["loop"]
                quest_id = timestamp_info["quest_id"]
                opponent_id = timestamp_info["opponent_id"]
            else:
                timestamp = 0
                loop = None 
                quest_id = None
                opponent_id = 0
            
            return timestamp, loop, quest_id, opponent_id
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e) 
    
    def delete_timestamps_for_group(self, group_id, timestamp_type):
        try:
            if timestamp_type == "answer":
                timestamps = self.timestamps_answer
            elif timestamp_type == "waiting":
                timestamps = self.timestamps_waiting

            if str(group_id) in timestamps:
                del timestamps[str(group_id)]
                self.save_timestamps_to_file(timestamp_type)
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e) 
    
    def save_timestamps_to_file(self, timestamp_type):
        try:
            if timestamp_type == "answer":
                file_path = self.file_path_answer
                timestamps = self.timestamps_answer
            elif timestamp_type == "waiting":
                file_path = self.file_path_waiting
                timestamps = self.timestamps_waiting
            
            with open(file_path, "w") as file:
                json.dump(list(timestamps.items()), file)
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)
    
    def load_timestamps_from_file(self, timestamp_type):
        try:
            if timestamp_type == "answer":
                file_path = self.file_path_answer
            elif timestamp_type == "waiting":
                file_path = self.file_path_waiting

            with open(file_path, "r") as file:
                items = json.load(file)
                if timestamp_type == "answer":
                    self.timestamps_answer = OrderedDict(items)
                elif timestamp_type == "waiting":
                    self.timestamps_waiting = OrderedDict(items)
        except FileNotFoundError as e:
            # If the file doesn't exist, create an empty OrderedDict
            if timestamp_type == "answer":
                self.timestamps_answer = OrderedDict()
            elif timestamp_type == "waiting":
                self.timestamps_waiting = OrderedDict()
            logger.exception("\033[91Exception: %s\033[0m" %e)
