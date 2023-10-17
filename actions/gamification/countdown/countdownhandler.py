import asyncio
import pymongo
import os
from actions.common.common import async_connect_to_db, get_credentials, get_json_msg, get_random_person, get_countdown_value, delete_folder, create_folder_if_not_exists, setup_logging
from rasa_sdk.events import ReminderScheduled, ReminderCancelled, FollowupAction, SlotSet
from telegram import Bot, Message, Chat
from actions.common.basehandler import BaseHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.timestamps.timestamp import Timestamp
import random
from actions.image_gen.text_on_image_gen import add_text_to_image, draw_progress_bar
import logging
logger = setup_logging()
class CountdownHandler(BaseHandler):

    def __init__(self):
        super().__init__()
        self.countdown_collection = async_connect_to_db(self.db, 'Countdown')
        self.collab_collection = async_connect_to_db(self.db, 'Collaboration')


    def get_coundown_value(self):
        return self.countdown


    async def send_waiting_countdown_message(self, countdown):
        try:
             # send countdown 
            countdown_msg_id = await self.telegram_bot_send_message('text', countdown.sender_id, "⏳ %s Sek.\n\n%s" % (countdown.countdown, countdown.text))
            return countdown_msg_id
        except Exception as e:
            logger.exception(e)  
            return None

    async def send_countdown_mesage(self, countdown, display_question, loop, session_object, quest_id, sender_id, mates_number=None):

        try:
            path = "actions/image_gen/output/%s/%s"%(loop,sender_id)
            folder_path = create_folder_if_not_exists(path)
            image_name = "%s.png"%countdown.quest_id
            image_path = os.path.join(path,image_name)
            
            # define background image, depends on question type
            if quest_id[-1] == 's':
                background_image= "actions/image_gen/input/single_choice.png" 
            elif quest_id[-1] == 'm':
                background_image = 'actions/image_gen/input/multi_choice.png'
            else:
                background_image = 'actions/image_gen/input/open_quest.png'
            # create photo 
            await add_text_to_image(display_question,background_image, image_path, session_object, quest_id, loop, mates_number)

            # send photo
            await self.telegram_bot_send_message('photo', countdown.sender_id, image_path)

            # send countdown 
            countdown_msg_id = await self.telegram_bot_send_message('text', countdown.sender_id, "⏳ %s Sek.\n\n" % (countdown.countdown))

            delete_folder(path)
            return countdown_msg_id
        except Exception as e:
            logger.exception(e)
            return None

    async def pin_countdown_message(self, countdown):
        await self.telegram_bot_send_message('pin', countdown.sender_id, " ", message_id=countdown.message_id)


    async def insert_new_countdown(self, countdown):
        await self.countdown_collection.insert_one(countdown)

    async def update_countdown_text(self, countdown,dispatcher, follow_reminder, active_loop, group):
        '''
        countdown for non questions
        '''
        countdown_old_val, message_id, countdown_intervall = countdown['countdown'], countdown['message_id'], countdown['intervall'] 
        try:
            # countdown is still acitve
            if countdown_old_val > countdown_intervall:
                countdown_old_val -= countdown_intervall
                countdown['countdown'] = countdown_old_val
                countdown_text = countdown['text'] 
                await self.telegram_bot_send_message('edit', countdown['sender_id'],"⏳ %s Sek.\n\n%s" % (countdown_old_val,countdown_text), message_id=message_id)

                return [SlotSet("countdown", countdown), FollowupAction(follow_reminder)]
            else: 
                # countdown finished
                await self.bot.unpin_all_chat_messages(countdown['sender_id'])
                if active_loop == "quiz_form_OKK": 
                    random_user_username = ""
                else:
                    random_user = get_random_person(group)
                    random_user_username = random_user['username']
                if len(countdown['buttons']) == 0: 
                    dispatcher.utter_message(text=countdown['question']%random_user_username)
                else:
                    dispatcher.utter_message(text=countdown['question']%random_user_username, buttons = countdown['buttons'])
                return [FollowupAction("action_forget_reminders")]
        except Exception as e:
            logger.exception(e) 

    
    async def update_countdown_question(self, countdown, dispatcher, follow_reminder, multiple_response_quest, competition_mode_handler, active_loop, group, sender_id, filter, opponent_id):
        '''
        countdown for questions
        '''
        countdown_old_val, message_id, countdown_intervall = countdown['countdown'], countdown['message_id'], countdown['intervall']
        try:
            # check if countdown still active
            if countdown_old_val > countdown_intervall:
                countdown_old_val -= countdown_intervall
                countdown['countdown'] = countdown_old_val
                if active_loop == 'quiz_form_KLMK' or active_loop == 'quiz_form_KL':
                    await self.boost_collaboration(countdown, dispatcher, follow_reminder, multiple_response_quest, competition_mode_handler, countdown_old_val, active_loop, sender_id, group, filter)
                # change countdownnumber in message 
                await self.telegram_bot_send_message('edit', countdown['sender_id'],"⏳ %s Sek.\n\n" % (countdown_old_val), message_id=message_id)
                await self.telegram_bot_send_message('pin', countdown['sender_id'], " ", message_id=message_id)
                return [SlotSet("countdown", countdown), FollowupAction(follow_reminder)]
            # countdown not active anymore
            else: 
                ''' create question with buttons so the user can answer the question after countdown stopped'''
                btns = []
                if countdown['quest_id'][-1] == 's':
                    btns = multiple_response_quest.create_btns_for_single_choice(countdown['question'])
                elif countdown['quest_id'][-1] == 'm':
                    btns = multiple_response_quest.create_btns_for_multiple_choice(countdown['question'])
                
                set_random_user = None
                beep_text ="🚨 Beep! Beep!! TIME'S UP!!!"
                
                ''' depending on modi: text for the question which get answered by user,
                    in two modi there is a direct speech to a person who has to answer the quest,
                    therefore a random person get selected'''

                if active_loop == 'quiz_form_KLMK' or active_loop == 'quiz_form_KL':
                    '''
                    delete collab dict 
                    '''
                    collab_filter = {
                    "group_id": int(sender_id)     
                    }
                    await self.collab_collection.delete_one(collab_filter)  
                    random_user = get_random_person(group)
                    set_random_user = SlotSet('random_person', random_user['user_id'])
                    if countdown['quest_id'][-1] == 'o':
                        quest_for_answering = beep_text + "\n\n✨%s✨ gebe bitte nun die Antwort in ein bis zwei Sätzen für euch ab. 🧠💭\n markiere es mit einem #-Zeichen (#Antwort)" %random_user['username']
                    else: 
                        quest_for_answering =beep_text + "\n\n✨%s✨ gebe bitte nun die Antwort für euch ab."%random_user['username'] +multiple_response_quest.create_text_for_question(countdown['question'], "")                          
                else:
                    if countdown['quest_id'][-1] == 'o':
                        quest_for_answering = beep_text + "\n\nGib bitte nun deine Antwort in ein bis zwei Sätzen ab. 🧠💭\n markiere es mit einem #-Zeichen (#Antwort)" 
                    else: 
                        quest_for_answering = beep_text + "\n\nGib bitte nun deine Antwort ab. 🧠💭{}".format(multiple_response_quest.create_text_for_question(countdown['question'], ""))

                '''countdown has finished, user get the chance to answer'''
                
                ''' insert a timestamp into answer json '''
                timestamp_handler = TimestampHandler()
                new_timestamp = Timestamp(countdown['sender_id'], countdown['quest_id'], active_loop,opponent_id).to_dict()
                timestamp_handler.insert_new_timestamp(new_timestamp, 'answer')

                dispatcher.utter_message(text=quest_for_answering, buttons=btns)
                if set_random_user is None:
                    return [FollowupAction("action_forget_reminders")]
                else:
                    return [set_random_user,  FollowupAction("action_forget_reminders")]
        except Exception as e:
            logger.exception(e) 


    async def boost_collaboration(self,countdown, dispatcher, follow_reminder, multiple_response_quest, competition_mode_handler, countdown_old_val, active_loop, sender_id, group, filter):
        '''
        boost collaboration between user, if no conservation is after half time 
        1. check if anyone has said something
        2. check if groupmems == 2, speak to one person directly to share his opinion 
        3. if groupmems >2, one person has to ask after the meaning of an other user
        '''
        try:
            # a group exitsts if there were allready a discussion for a question 
            existing_group = await self.collab_collection.find_one({"group_id": int(sender_id)})
            print("existing_group", existing_group)
            if existing_group: 
                person_with_lowest_counter = min(existing_group['users'], key=lambda x: x['counter'])
                # if the person who had said least but had more than three interaction in a discussion for one quesion, the team gets a badge for good communication
                if person_with_lowest_counter and person_with_lowest_counter['counter'] > 3: #TODO check treshhold
                    # lots of communication in group
                    await competition_mode_handler.set_status("collaboration", countdown['quest_id'], filter, competition_mode_handler.session_collection , True)
                    
            if not existing_group and countdown_old_val == (get_countdown_value(multiple_response_quest.quest_id,active_loop) - 20) :
                text = "Versucht gemeinsam zu diskutieren und eine Lösung zu erarbeiten\. 🤓\nGerne könnt ihr mich mit *'@Ben'* ansprechen und mich nach einem Tipp fragen\. 🙂"
                dispatcher.utter_message(json_message=get_json_msg(sender_id, text))

            # a user_group exists if they have allready talked in the group about a question, this is tracked in the table 'Kollaboration'
            if existing_group and countdown_old_val == get_countdown_value(multiple_response_quest.quest_id,active_loop) / 2:
                # if user_group has just two members, bot speaks to a person directly who has said at least and motivates for more conversation to the group
                if len(existing_group['users']) == 2:
                    person_with_lowest_counter = min(existing_group['users'], key=lambda x: x['counter'])
                    if person_with_lowest_counter['counter'] < 2: 
                        text = "*%s* was denkst du zu dieser Frage? Teile gerne deine Meinung\. 🤓 " % person_with_lowest_counter['username']
                        await asyncio.sleep(1.25)
                        dispatcher.utter_message(json_message=get_json_msg(sender_id, text))
                # if user_group has more than two members, bot says to one person that he should ask about the opinion of another user
                elif len(existing_group['users']) > 2:
                    # get two users with the lowest counter value, there are the person who said least
                    lowest_counters = sorted(existing_group['users'], key=lambda x: x['counter'])[:2] 
                    if lowest_counters[0]['counter'] < 2: 
                        text = "*%s* frage *%s* nach seiner Meinung zu diesem Thema\. 🤓" %(lowest_counters[1]['username'], lowest_counters[0]['username'])
                        await asyncio.sleep(1.25)
                        dispatcher.utter_message(json_message=get_json_msg(sender_id, text))
            
            # if nobody has said something in a discussion for a question, bot will chose a random perosn
            elif not existing_group and countdown_old_val == get_countdown_value(multiple_response_quest.quest_id,active_loop)/2:
                if len(group['users']) > 1:
                    random_users = random.sample(group['users'], 2)
                    text = "*%s* frage *%s* nach seiner Meinung zu diesem Thema\. 🤓" %(random_users[0]['username'], random_users[1]['username'])
                    await asyncio.sleep(1.25)
                    dispatcher.utter_message(json_message=get_json_msg(sender_id, text))
            

        except Exception as e:
            logger.exception(e) 

