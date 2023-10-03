from actions.game.gamemodehandler import GameModeHandler
import os 
import asyncio
import json
import logging
logger = logging.getLogger(__name__)
from actions.common.common import get_dp_inmemory_db, get_credentials, get_requested_slot, async_connect_to_db
'''
Farbenprint

print("\033[91mDieser Text ist rot\033[0m")
print("\033[93mDieser Text ist gelb\033[0m")
print("\033[94mDieser Text ist blau\033[0m")

Rot: \033[91m
Gelb: \033[93m
Blau: \033[94m
'''
class AchievementHandler():
    '''
    AchievementHandler to handle earned achievements during game
    '''
    def __init__(self):
        self.db = get_credentials("DB_NAME")
        self.session_collection = async_connect_to_db(self.db, 'Session')
        self.solution_collection = async_connect_to_db(self.db, 'Solutions')


    async def get_len_of_session_obj(self, filter):
        '''
        returns the length of the questions array of a sessio obj,
        so we know how many quests got askes
        '''
        session_obj = await self.session_collection.find_one(filter)
        return len(session_obj['questions'])

    async def get_number_of_fulfilled_status(self, filter, slots, status):
        '''
        Get the number of fulfilled status e.g. correct
        '''
        game_mode_handler = GameModeHandler()
        try: 
            counter = 0 
            # get number of how many quest are asked
            asked_quests = await self.get_len_of_session_obj(filter)
            for index, slot in enumerate(slots):
                if index <= (asked_quests - 1):
                    if await game_mode_handler.check_status(status, slot, filter, self.session_collection):
                        counter += 1
            return counter
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return 0
        
    async def insert_achievement(self,filter, earned_achievement):
        try: 
            session_obj = await self.session_collection.find_one(filter)

            if session_obj['achievements'] == None:
                new_achievements_list = []
                new_achievements_list.append(earned_achievement)
             #   print("\033[94m  Achievementlist 1  \033[0m",new_achievements_list)
                update_achievements = {"$set": {'achievements': new_achievements_list}}
                await self.session_collection.update_one(filter, update_achievements)
                return True
            elif not earned_achievement in session_obj['achievements']:

                achievements_list = session_obj['achievements']
                achievements_list.append(earned_achievement)
              #  print("\033[94m  Achievementlist 2  \033[0m",achievements_list)
                update_achievements = {"$set": {'achievements': achievements_list}}
                await self.session_collection.update_one(filter, update_achievements)
                return True
            else:
                #print("\033[91m  ACHIEVMENT EXISTIERT  \033[0m ")
                return False
        except Exception as e: 
            
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return False

    async def get_total_points_of_group(self, filter):
        try:
            session_obj = await self.session_collection.find_one(filter)
            if session_obj:
                return session_obj['total_points']
            else: 
                return 0
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return 0
    
    async def get_level(self, filter):
        try:
            session_obj = await self.session_collection.find_one(filter)
            if session_obj:
                return session_obj['level']
            else: 
                return 0
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return 0

    async def max_points(self):
        try:
            max_points = 0 
            cursor = self.solution_collection.find()
            solutions = await cursor.to_list(length=None) 
            for solution in solutions:
                max_points += solution['points']
            return max_points
        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)
            return 0

    async def earn_achievement(self, filter, slots, sender_id):
        try:
            # get keys of quests which start with "frage_"
            slots = [key for key in slots if key.startswith('frage_')]   

            # Points 
            points_of_group = await self.get_total_points_of_group(filter)
            max_points_of_game = await self.max_points()

            # TODO  Sicherstellen dass kein SPAM an Batches kommt
            achievements = {
                # group got first quest correct
                "KORREKTE_ANTWORT": ("correct", 1),
                # collaboration ->  teamwork
                "TEAMWORK": ("collaboration", int(get_credentials('COLLABORATION_TRESHHOLD'))),
                # in_time -> schnelles antworten
                "SCHNELLES_ANTWORTEN": ("in_time", 8),
                # Punkte Treshhold -> 60% -> quiz master
                "QUIZ_MASTER": (None, int(max_points_of_game*0.6)),
                # alle correct -> naturtalent
                "NATURTALENT": ("correct", len(slots)), 
                # Fragearten
                "SINGLE_CHOICE": ("correct", 2),
                "MULTIPLE_CHOICE":("correct", 2),
                "OFFENE_FRAGE":("correct", 2)
            }
            game_mode_handler = GameModeHandler()
            for achievement, (status, threshold) in achievements.items():
                if status:
                    if achievement == 'SINGLE_CHOICE':
                        slots_with_s = [slot for slot in slots if '_s' in slot]
                        count = await self.get_number_of_fulfilled_status(filter, slots_with_s, status)
                    elif achievement == 'MULTIPLE_CHOICE':
                        slots_with_m = [slot for slot in slots if '_m' in slot]
                        count = await self.get_number_of_fulfilled_status(filter, slots_with_m, status)
                    elif achievement == 'OFFENE_FRAGE':
                        slots_with_o = [slot for slot in slots if '_o' in slot]
                        count = await self.get_number_of_fulfilled_status(filter, slots_with_o, status) 
                    else:
                        count = await self.get_number_of_fulfilled_status(filter, slots, status)
                    if count >= threshold:
                        if await self.insert_achievement(filter, achievement):
                            badges = get_dp_inmemory_db("./badges.json")
                            await game_mode_handler.telegram_bot_send_message('photo', sender_id, badges[achievement])
                elif points_of_group >= threshold:
                    if await self.insert_achievement(filter, achievement):
                        badges = get_dp_inmemory_db("./badges.json")
                        await game_mode_handler.telegram_bot_send_message('photo', sender_id, badges[achievement])

        except Exception as e: 
            logger.exception("\033[91Exception: %s\033[0m" %e)

