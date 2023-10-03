import json
from dotenv import load_dotenv
import os
import shutil
from pymongo import MongoClient 
from motor.motor_asyncio import AsyncIOMotorClient
import json
import random
import openai
load_dotenv()
import logging
logger = logging.getLogger(__name__)

def get_dp_inmemory_db(json_file):
    """ load the inmemory db from json file """
    with open(json_file, "r") as jsonFile:
        return json.load(jsonFile)

def async_connect_to_db(database, collection):
    """
    Returns the collections(with the name collection) in the cluster(database)
    """
    try:
        cluster = AsyncIOMotorClient(get_credentials('MONGO_DB_LOCAL'),connectTimeoutMS=120000, serverSelectionTimeoutMS=120000)
        db = cluster[database]
        collections = db[collection]
        return collections
    except Exception as e: 
        logger.exception("\033[91Exception: %s\033[0m" %e)  


def print_current_tracker_state(tracker):
    '''
    Debug purpose: get the current state of the tracker 
    '''
    current_state = tracker.current_state() 
    # Iterate over the keys of the dictionary
    for state in current_state:
        print(state, current_state[state])


def get_groupuser_id_and_answer(tracker):
    '''
    Get Answer and UserID of the gorupmember who is answering the question through custom connector
    '''
    try:
        for event in reversed(tracker.events):
                    if event['event'] == 'user':
                        #print("EVENT",event )
                        if 'groupuser_id' in event['metadata']:
                            groupuser_id = event['metadata']['groupuser_id']
                            groupuser_name = event['metadata']['groupuser_name']

                            if len(event['parse_data']['entities']) > 0:
                                answer = event['parse_data']['entities'][0]['value']
                            else:
                                answer = event['text']
                            return groupuser_id,groupuser_name,answer
                        else: 
                            return None, None, None
    except Exception as e: 
        logger.exception("\033[91Exception: %s\033[0m" %e) 

def get_random_person(group):
    return random.choice(group['users'])

def get_requested_slot(tracker):
    '''
    get current requested slot of form
    '''
    current_state = tracker.current_state() 
    for state in reversed(current_state):
        if state == "slots":
            return current_state[state]['requested_slot']

def get_credentials(keyname):
    '''
    get value from env file
    '''
    try:
        return (
            os.environ[keyname]
            if os.environ[keyname] is not None
            else os.getenv(keyname)
        )
    except:
        return os.getenv(keyname)


def ask_openai(role, question):
    openai.api_key = get_credentials("OPEN_AI")
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "assistant", "content": "%s %s"%(role,question)}
    ],
    temperature=1,
    max_tokens=256,
    n =1
    )
    return completion.choices[0].message.content
    
def get_json_msg(recipient_id, text):
    return {
            "chat_id": recipient_id, 
            "text": text,
            "parse_mode": "MarkdownV2",
        }


async def ben_is_typing(countdown, game_mode_handler):
    await game_mode_handler.telegram_bot_send_message('edit', countdown['sender_id'],"Ben tippt ...", message_id=countdown['message_id'] )
    await game_mode_handler.telegram_bot_send_message('pin', countdown['sender_id'], " ", message_id=countdown['message_id'])

async def ben_is_typing_2(countdown, game_mode_handler):
    await game_mode_handler.telegram_bot_send_message('edit', countdown['sender_id'],"Ben tippt ....", message_id=countdown['message_id'] )
    await game_mode_handler.telegram_bot_send_message('pin', countdown['sender_id'], " ", message_id=countdown['message_id'])


def get_countdown_value(quest_id, loop):
    mode = '_'.join(loop.split('_')[2:]) if loop else None
    values = get_dp_inmemory_db("./countdown_values.json")
    return values[mode][quest_id]


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
    except OSError as e:
        print(f"Fehler beim rekursiven Löschen des Ordners: {e}")
