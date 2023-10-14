from actions.common.common import get_requested_slot, ben_is_typing
import re
import asyncio
import datetime
from actions.game.gamemodehandler import GameModeHandler
from actions.game.competition.competitionmodehandler import CompetitionModeHandler
from actions.session.sessionhandler import SessionHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.common.common import get_credentials, get_requested_slot, get_countdown_value
from actions.groups.grouphandler import GroupHandler
class TeamName:
    def __init__(self, is_group, id):
        self.id = id
        self.exceeded = False
        self.evaluated = False

        if is_group:
            self.text = "Ihr habt nun kurz Zeit, um euch zu besprechen und gemeinsam einen Teamnamen festzulegen.\nIch frage euch gleich nach eurem festgelegten Teamnamen und gebe euch dazu Rückmeldung. 🤓"         
            self.task = "👋 %s schreib mir nun euren Teamnamen und markiere es mit einem # (#Teamname). 😎 "
        else:
            self.text = "Du hast nun kurz Zeit, dir einen Spielnamen zu überlegen.\nIch frage dich gleich nach deinem festgelegten Spielnamen und gebe dir dazu Rückmeldung. 🤓"         
            self.task = "👋 %s schreib mir nun dein Spielnamen und markiere es mit einem # (#Spielname). 😎 "

    def to_dict(self):
        return {
            'id': self.id,
            'exceeded': self.exceeded,
            'evaluated': self.evaluated,
            'text': self.text,
            'task': self.task
        }
        
async def set_team_name(slot_value, tracker, dispatcher, competition_mode_handler, session_handler):
        timestamp_handler = TimestampHandler()
        game_mode_handler = GameModeHandler()
        session_handler =  SessionHandler()
        
        timestamp, loop, quest_id,_ = timestamp_handler.get_timestamp(tracker.sender_id, 'waiting')
        countdown = get_countdown_value(quest_id,loop)
        now = datetime.datetime.now().timestamp()
        requested_slot = get_requested_slot(tracker)
        
        if now >= timestamp + countdown and requested_slot == 'team_name' and "#" in slot_value:
            team_name = slot_value.strip("#")
            text = f"Cool! Euer Teamname ist: {team_name} 🚀💥"
            await competition_mode_handler.telegram_bot_send_message('text', tracker.sender_id, text)

            '''
            check if opponent group has answered
            '''
            active_loop = tracker.active_loop.get('name') 
            modus = '_'.join(active_loop.split('_')[2:])
            if modus == 'KLOK' or modus == 'KLMK':
                dispatcher.utter_message(response="utter_waiting_of_opponent")
                return{"answered": True,"team_name": team_name,"teamname_value": team_name, "requested_slot": None}
            filter = session_handler.get_session_filter(tracker)
            await competition_mode_handler.set_status('evaluated', 'team_name', filter, session_handler.session_collection, True)
            await ben_is_typing(tracker.get_slot('countdown'), game_mode_handler)
            return {'team_name': team_name,"teamname_value": team_name,"random_person": None, "flag": None,  "countdown": None}
        elif now < timestamp + countdown:
            print("Before Submitting: team_name")
            return{'team_name': None}
        else: 
            return{'team_name': slot_value}
