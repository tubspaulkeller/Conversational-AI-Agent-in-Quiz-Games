from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted, SlotSet, EventType

def debug(tracker=None):
    """ debug function for printing the current state of the tracker """
    output = '>>> Action: '
    output = '=' * min(100, len(output)) + '\n' + output
    if tracker:
        try:
            msg = tracker.latest_message
            slots = tracker.slots
            filled_slots = {}
            output += '\n- Text:       ' + str(msg['text'])
            output += '\n- Intent:     ' + str(msg['intent']['name'])
            output += '\n- Confidence: ' + str(msg['intent']['confidence'])
            output += '\n- Entities:   ' + ', '.join(msg['entities'])
            output += '\n- Slots:      '
            for slot_key, slot_value in slots.items():
                if slot_value is not None:
                    filled_slots[slot_key] = slot_value
            if len(filled_slots) > 0:
                for slot_key, slot_value in filled_slots.items():
                    output += str(slot_key) + ': ' + str(slot_value) + ', '
                output = output[:-2]
        except Exception as e:
            print(f'\n> announce: [ERROR] {e}')
    print(output)
