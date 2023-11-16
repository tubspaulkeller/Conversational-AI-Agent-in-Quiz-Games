
import asyncio
import aiohttp
import datetime

from actions.timestamps.timestamphandler import TimestampHandler
from actions.gamification.countdown.countdown import Countdown
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.common.common import get_credentials, async_connect_to_db, ask_openai, ben_is_typing_2, setup_logging
from actions.session.sessionhandler import SessionHandler
from actions.common.basehandler import BaseHandler
import time
import random
import re
import logging
logger = setup_logging()


class GameModeHandler(BaseHandler):
    '''
    GameModeHandler with basic functions
    '''

    def __init__(self):
        super().__init__()
        self.group_collection = async_connect_to_db(self.db, 'Groups')
        self.session_collection = async_connect_to_db(self.db, 'Session')
        self.solution_collection = async_connect_to_db(self.db, 'Solutions')
        self.leaderboard_collection = async_connect_to_db(
            self.db, 'Leaderboard')
        self.competition_collection = async_connect_to_db(
            self.db, 'Competition')

    async def get_len_of_session_obj(self, filter):
        '''
        returns the length of the questions array of a sessio obj,
        so we know how many quests got askes
        '''
        session_obj = await self.session_collection.find_one(filter)
        return len(session_obj['questions'])

    async def check_status(self, status, name_of_slot, filter, collection):
        '''
        checks a passed status of a database entry like if a question got allready evaluated
        '''
        try:
            collection_object = await collection.find_one(filter)
            #print("COLLECTION_OBJECT", collection_object)
            if collection_object == None:
                return False
            for index, question in reversed(list(enumerate(collection_object['questions']))):
                if question['id'] == name_of_slot:
                    return question[status]
            return False
        except Exception as e:
            logger.exception(e)
            return False

    async def set_status(self, status, name_of_slot, filter, collection, boolean):
        '''
        sets a passed status to true or false
        '''
        try:

            collection_object = await collection.find_one(filter)
            if collection_object == None:
                return False
            for index, question in reversed(list(enumerate(collection_object['questions']))):
                if question['id'] == name_of_slot:
                    update_status = {
                        "$set": {
                            f"questions.{str(index)}.{str(status)}": boolean
                        }
                    }
                    await collection.update_one(filter, update_status)
                    return True
        except Exception as e:
            logger.exception(e)
            return False

    async def set_goal_and_status(self, name_of_slot, goal, status, filter, boolean):
        '''
        sets a passed status to true or false and sets the goal
        '''
        try:
            session_object = await self.session_collection.find_one(filter)
            if session_object is not None:
                for index, question in reversed(list(enumerate(session_object['questions']))):
                    if question['id'] == name_of_slot:
                        update_quest_object = {
                            "$set": {
                                f"questions.{str(index)}.{str(status)}": boolean,
                                "goal": goal
                            }
                        }
                        break
                await self.session_collection.update_one(filter, update_quest_object)
                return True
            else: 
                return False
        except Exception as e:
            logger.exception(e)
            return False

    async def number_of_team_mates(self, channel_id):
        ''' 
        count number of mates in my team
        '''
        filter = {"group_id": str(channel_id)}
        try:
            existing_group = await self.group_collection.find_one(filter)
            return len(existing_group['users']), existing_group['users']
        except Exception as e:
            logger.exception(e)
            return 0, None

    def number_of_team_mates_slot(self, tracker, slotname):
        ''' 
        count number of mates in my team using slot
        '''
        mates = tracker.get_slot(slotname)['users']
        return len(mates)

    async def _get_solution(self, name_of_slot):
        '''
        get the solution of asked question
        '''
        filter_solution = {
            "question_id": name_of_slot,
        }
        try:
            solution = await self.solution_collection.find_one(filter_solution)
            return solution
        except Exception as e:
            logger.exception(e)

    async def rate_open_question(self, answer, quest, retries=10):
        '''
        a call to open ai to evaluate open questions
        '''
        try:
            role = "Du hast herausragendes Wissen über die Vorlesung 'Einführung in die Wirtschaftsinfomratik'.\
            Bewerte die eingehende Antwort zu der Frage auf inhatliche Korrektheit: %s auf einer Skala 0 - 20 Punkten. \
            0 Punkte stellt dabei eine falsche/ nicht korrekte Antwort da, umso korrekter/besser die Antwort ist, desto mehr Punkte gibt es.\
            Gib dabei nur die Punktzahl ohne weitere Wörter direkt am Satzanfang an (Bsp: 15). Bewerte nicht zu großzügig!\
            Dann gib eine kurze motivierende Erläuterung (halber Satz) zu deiner Bewertung für \
            die eingegangene Antwort. Die Bewertung sollte ebenfalls einen kurzen Tipp für eine lösungsnahere Antwort enthalten.\
            Zuletzt gebe eine richtige kurze Lösung zusätzlich an. Ganz wichtig ist, dass dein Antwortformat wie folgt aussehen muss: Punktzahl doppelter Absatz Bewertung doppelter Absatz Lösung\
            Die zu bewertende Antwort ist:" % quest

            openai_rating = ask_openai(role, answer)
            sections = openai_rating.split("\n\n")
            points = 0
            evaluation = ""
            solution = ""

            try:
                # points for answer
                get_number_of_string = re.search(r'\b(\d+)\b', sections[0])
                points = int(get_number_of_string.group()
                             ) if get_number_of_string else 0
                # evaluation of the given answer
                evaluation = sections[1]
                # a better solution for the quest
                solution = sections[2]
            except IndexError:
                print("IN IndexError")
                logger.info("OpenAI IndexError")
                if retries > 0:
                    return await self.rate_open_question(answer, quest, retries - 1)
                else:
                    return 0, "Es konnte keine Bewertung stattfinden", "Keine Lösung"
            except Exception:
                print("IN Exception")
                logger.info("OpenAI Exception")
                if retries > 0:
                    await asyncio.sleep(2)
                    return await self.rate_open_question(answer, quest, retries - 1)
                else:
                    return 0, "Es konnte keine Bewertung stattfinden", "Keine Lösung"
            return int(points), evaluation, solution
        except Exception as e:
            logger.exception(e)

    async def calc_earned_points(self, filter, answer, name_of_slot, group_id, countdown):
        '''
        calculate the points which the user got for their answer
        '''
        try:
            earned_points = 0
            solution_points = 0
            if name_of_slot[-1] == "o":
                # Open Questions
                await ben_is_typing_2(countdown, self)

                points, evaluation, solution = await self.rate_open_question(answer=answer['answer'], quest=countdown['question']['display_question'])
                # Debug
                print("PUNKTE: %s\nEVALUATION: %s\nSOLUTION: %s\n" %
                      (points, evaluation, solution))
                logger.info("Pkt:" + str(points) + " Eval: " +
                            evaluation+" Lösg.: "+solution)
                # if points more than ten, the attribute correct is setted to true, for calc badges
                if points > 10:
                    await self.set_status("correct", name_of_slot, filter, self.session_collection, True)
                # correct answer
                if points > 0:
                    earned_points = await self.calculate_points(filter, name_of_slot, group_id, points, answer, evaluation)
                    # set answer to correct needed for other logic
                    answer['answer'] = 'correct'
                # wrong answer
                else:
                    answer['answer'] = 'wrong'
                    if evaluation:
                        await self.telegram_bot_send_message('text', group_id, evaluation)
                await self.bot.unpin_all_chat_messages(group_id)
            else:
                # Single or Multiple Choice
                solution = await self._get_solution(name_of_slot)
                solution_points = solution['points']

                # correct is pased through button
                if answer['answer'] == 'correct':
                    await self.set_status("correct", name_of_slot, filter, self.session_collection, True)
                    earned_points = await self.calculate_points(filter, name_of_slot, group_id, solution['points'], answer, None)

                solution = solution['solution']
            # if KLOK bewerte einzelne Antworten hier !
            return earned_points, solution, solution_points
        except Exception as e:
            logger.exception(e)

    async def get_needed_time_for_answering(self, answer, id):
        '''
        get the time which the user needed to answer
        '''
        try:
            timestamp_handler = TimestampHandler()
            question_timestamp, loop, quest_id, _ = await timestamp_handler.get_timestamp(id, 'answer')
            if quest_id is None:
                session_handler = SessionHandler()
                session = await session_handler.session_collection.find_one({"channel_id": id})
                if session:
                    quest_id = session['questions'][-1]['id']
            delay = int(get_credentials('DELAY'))
            if quest_id[-1] == "o":
                delay += int(get_credentials('DELAY'))
            question_timestamp += delay
            answer_timestamp = answer['timestamp']
            return answer_timestamp - question_timestamp
        except Exception as e:
            logger.exception(e)
            return 0

    async def calc_points_for_in_time_answering(self, result, time_bound, max_points, penalty, name_of_slot, filter, evaluation):
        '''
        give a penalty if a user answer got delayed otherwise set the attribute (in_time) to true, for badges
        '''
        if result <= time_bound:
            await self.set_status("in_time", name_of_slot, filter, self.session_collection, True)
            points_to_get = max_points
            if evaluation:
                await self.telegram_bot_send_message('text', filter['channel_id'], evaluation)

            print("\033[94m 1. Weniger als %s Sekunden gebraucht: %s, Punkte sind %s\033[0m" % (
                time_bound, result, points_to_get))

        elif result <= (time_bound+5):
            points_to_get = max(max_points - penalty, 0)
            print("\033[94m 2. Weniger als %s Sekunden gebraucht: %s, Punkte sind %s\033[0m" % (
                (time_bound+5), result, points_to_get))
            if evaluation:
                await self.telegram_bot_send_message('text', filter['channel_id'], evaluation + "\n\nAufgrund der verspäteten Antwort, wird eine Strafe von -%s Punkten verhängt." % penalty)
            else:
                await self.telegram_bot_send_message('text', filter['channel_id'], "Aufgrund der verspäteten Antwort, wird eine Strafe von -%s Punkten verhängt." % penalty)

        else:
            points_to_get = 0
            print("\033[94m 3. Länger als %s Sekunden gebraucht: %s, Punkte sind 0\033[0m" % (
                result, (time_bound+5)))
            if evaluation:
                await self.telegram_bot_send_message('text', filter['channel_id'], evaluation + "\n\nDies ist eine gute Lösung! Leider wurde die Antwort nicht rechtzeitig abgegeben, weshalb keine Punkte vergeben werden können.")

        return points_to_get

    async def calculate_points(self, filter, name_of_slot,  id, points, answer, evaluation):
        '''
        get points for user answer after checking if the user answered with a delay
        '''
        try:
            result = await self.get_needed_time_for_answering(answer, id)
            if name_of_slot[-1] == "o":
                points_to_get = await self.calc_points_for_in_time_answering(result, int(get_credentials("OPEN_QUEST_TIME")), points, int(get_credentials("OPEN_QUEST_PENALTY")), name_of_slot, filter, evaluation)
            else:
                points_to_get = await self.calc_points_for_in_time_answering(result, int(get_credentials("BUTTON_QUEST_TIME")), points, int(get_credentials("BUTTON_QUEST_PENALTY")), name_of_slot, filter, evaluation)
            return points_to_get
        except Exception as e:
            logger.exception(e)

    async def update_session(self, filter, name_of_slot, earned_points, group_answer, loop=None, mates_number=None):
        '''
        update the session object in DB with the current quest object which contains answer and earned points
        '''
        try:
            session_object = await self.session_collection.find_one(filter)
            session_handler = SessionHandler()
            old_total_points = session_object['total_points']
            new_total_points = old_total_points + earned_points
            curr_level = session_object['level']
            max_points = await session_handler.max_points()
            level_up = False

            level_points = [(1, max_points - 53), (2, max_points - 43),
                            (3, max_points - 22), (4, max_points)]

            if loop and loop == 'KLOK':
                mates_number = mates_number
                avg_points = new_total_points / mates_number
                levels_achieved = [level for level,
                                   points in level_points if avg_points >= points]
            else:
                levels_achieved = [
                    level for level, points in level_points if new_total_points >= points]

            if earned_points > 0 and levels_achieved:
                highest_level_achieved = max(levels_achieved)
                level = highest_level_achieved
                if level > curr_level:
                    level_up = True
                    curr_level = level

            update_quest_object = {}
            for index, question in enumerate(session_object['questions']):
                if question['id'] == name_of_slot:
                    update_quest_object = {
                        "$set": {
                            f"questions.{str(index)}.answer": group_answer,
                            f"questions.{str(index)}.points": earned_points,
                            "total_points": new_total_points,
                            "level": curr_level
                        }
                    }
                    break
            await self.session_collection.update_one(filter, update_quest_object)
            return old_total_points + earned_points, level_up
        except Exception as e:
            logger.exception(e)
            return 0, False

    def get_text_for_right_or_wrong_answer(self, is_correct, solution="", solution_text="", is_user=False):
        try:
            if is_correct:
                return random.choice(["Genau richtig! Die Antwort ist korrekt! ",
                                      "Perfekt! Die richtige Antwort wurde gefunden! ",
                                      "Ausgezeichnet! Die richtige Antwort wurde entdeckt! ",
                                      "Fantastisch! Das ist korrekt! ",
                                      "Brilliant! Die richtige Antwort wurde erkannt! ",
                                      "Hervorragend! Das ist die richtige Antwort! ",
                                      "Gut gemacht! Die richtige Antwort wurde ermittelt! ",
                                      "Fantastische Arbeit! Das ist korrekt! ",
                                      "Auf dem richtigen Weg! Die Antwort ist richtig! ",
                                      "Wunderbar! Die Lösung ist genau die richtige! ",
                                      "Bravo! Die richtige Antwort wurde erkannt! ",
                                      "Perfekte Wahl! Das ist die richtige Antwort! ",
                                      "Expertenwürdig! Die Antwort ist korrekt! ",
                                      "Exzellent! Die richtige Antwort wurde gefunden! ",
                                      "Großartig! Die richtige Antwort wurde entdeckt! ",
                                      "Genauso ist es! Die Antwort ist richtig! ",
                                      "Weiter so! Die Antwort ist korrekt! ",
                                      "Gut erkannt! Das ist die richtige Antwort! ",
                                      "Perfektion! Die richtige Antwort wurde gefunden! ",
                                      "Hervorragend! Das ist korrekt! "])
            else:
                if is_user:
                    return random.choice(["Oh, schade! Die Antwort ist leider falsch. 😔 %s %s\nBleib weiter dran 💫📚", "Das ist nicht die richtige Antwort. 😔 %s %s\nKeine Sorge, jeder macht mal Fehler! 🤷‍♂️💡 Mit jedem Versuch wirst du besser! 🚀🎯", "Leider falsch! 😔 %s %s\nFehler sind Chancen zum Lernen. 🌱", "Schade, die Antwort ist leider falsch. 😔 %s %s\nNicht schlimm! Du lernst draus und wirst stärker! 💪🌟",  "Schade die Antwort ist leider falsch. 😔 %s %s\nGib nicht auf! 🚀"]) % (solution_text, solution)
                else:
                    return random.choice(["Oh, schade! Die Antwort ist leider falsch. 😔 %s %s\nBleibt weiter dran 💫📚", "Das ist nicht die richtige Antwort. 😔 %s %s\nKeine Sorge, jeder macht mal Fehler! 🤷‍♂️💡", "Leider falsch! 😔 %s %s\nFehler sind Chancen zum Lernen. 🌱", "Schade, die Antwort ist leider falsch. 😔 %s %s\nNicht schlimm! Wir lernen draus und werden stärker! 💪🌟"]) % (solution_text, solution)
        except Exception as e:
            logger.exception(e)

    def get_text_for_evaluation_of_points(self, is_user, level_up, kind_of_points, points_to_get):
        try:
            if is_user:
                level_up_text = ""
                if level_up:
                    level_up_text = random.choice(["Außerdem bist du ein weiteres Level aufgestiegen!", "Zusätzlich hast du ein weiteres Level erreicht!", "Darüber hinaus bist du auf eine höhere Stufe aufgestiegen!",
                                                  "Außerdem hast du dich in ein neues Level vorgearbeitet!", "Des Weiteren hast du ein weiteres Level erfolgreich gemeistert!"])

                if kind_of_points == 'max':
                    return random.choice(["Glückwunsch! Du hast %s Punkte geholt. 🎉 %s", "Fantastisch! Du hast %s Punkte erzielt. 🎉 %s", "Toll gemacht! Du hast %s Punkte erreicht. 🎉 %s", "Hervorragend! Du hast %s Punkte erzielt. 🎉 %s"]) % (points_to_get, level_up_text)
                elif kind_of_points == 'middle':
                    return random.choice(["Da du etwas zu spät geantwortet hast, hast du %s Punkte erzielt. 🎉 %s", "Aufgrund deiner verspäteten Antwort hast du %s Punkte erreicht. 🎉 %s", "%s Punkte wurden dir gutgeschrieben 🎉, weil du etwas zu spät geantwortet hast. %s", "Du hast %s Punkte erzielt 🎉, da deine Antwort etwas verspätet war. %s", "Du hast %s Punkte geholt 🎉, da du etwas zu spät gewantwortet hast. %s"]) % (points_to_get, level_up_text)
                else:
                    return random.choice(["Leider hast du zu lange gebraucht ⏳, um deine Antwort abzugeben, weshalb du 0 Punkte erhältst.", "Deine Antwort kam leider zu spät ⏳, wodurch du keine Punkte erhältst.", "Da du zu viel Zeit benötigt hast ⏳, um zu antworten, bekommst du 0 Punkte.", "Aufgrund der Verzögerung ⏳ bei deiner Antwort erhältst du keine Punkte.", "Allerdings hast du zu lange gebraucht ⏳, um deine Antwort abzugeben. Du bekommst deshalb 0 Punkte."])
            else:
                level_up_text = ""
                if level_up:
                    level_up_text = random.choice(["Außerdem seid ihr ein weiteres Level aufgestiegen!", "Zusätzlich habt ihr ein weiteres Level erreicht!", "Darüber hinaus seid ihr auf eine höhere Stufe aufgestiegen!",
                                                  "Außerdem habt ihr euch in ein neues Level vorgearbeitet!", "Des Weiteren habt ihr ein weiteres Level erfolgreich gemeistert!"])

                if kind_of_points == 'max':
                    return random.choice(["Glückwunsch! Ihr habt %s Punkte geholt. 🎉 %s", "Fantastisch! Ihr habt %s Punkte erzielt. 🎉 %s", "Toll gemacht! Ihr habt %s Punkte erreicht. 🎉 %s", "Hervorragend! Ihr habt %s Punkte erzielt. 🎉 %s"]) % (points_to_get, level_up_text)
                elif kind_of_points == 'middle':
                    return random.choice(["Da ihr etwas zu spät geantwortet habt, habt ihr %s Punkte erzielt 🎉. %s", "Aufgrund eurer verspäteten Antwort habt ihr %s Punkte erreicht. 🎉 %s", "%s Punkte wurden euch gutgeschrieben 🎉, weil ihr etwas zu spät geantwortet habt. %s", "Ihr habt %s Punkte erzielt 🎉, da eure Antwort etwas verspätet war. %s", "Ihr habt %s Punkte geholt 🎉, da ihr etwas zu spät gewantwortet habt. %s"]) % (points_to_get, level_up_text)
                elif kind_of_points == 'less':
                    return random.choice(["Leider habt ihr zu lange gebraucht ⏳, um eure Antwort abzugeben, weshalb ihr 0 Punkte erhaltet.", "Eure Antwort kam leider zu spät ⏳, wodurch ihr keine Punkte erhaltet.", "Da ihr zu viel Zeit benötigt habt ⏳, um zu antworten, bekommt ihr 0 Punkte.", "Aufgrund der Verzögerung ⏳ bei eurer Antwort erhaltet ihr keine Punkte.", "Allerdings habt ihr zu lange gebraucht ⏳, um eure Antwort abzugeben. Ihr bekommt deshalb 0 Punkte."])
        except Exception as e:
            logger.exception(e)

    async def utter_points(self, solution, answer, points_to_get, level_up, recipient_id, is_user, name_of_slot, solution_points):
        '''
        give user information about his scored points
        '''
        try:
            # Offene Fragen
            if name_of_slot[-1] == "o":
                if points_to_get > 0:
                    text = self.get_text_for_evaluation_of_points(
                        is_user, level_up, 'max', points_to_get)
                elif points_to_get == 0 and answer['answer'] == 'correct':
                    text = self.get_text_for_evaluation_of_points(
                        is_user, level_up, 'less', points_to_get)
                elif points_to_get == 0 and answer['answer'] == 'wrong':
                    text = self.get_text_for_right_or_wrong_answer(
                        False, solution, is_user=is_user)
            # Single/Multiple Choice Fragen
            else:
                if points_to_get > (solution_points * 0.75):
                    text = self.get_text_for_right_or_wrong_answer(
                        True,  is_user=is_user) + self.get_text_for_evaluation_of_points(is_user, level_up, 'max', points_to_get)
                elif points_to_get > (solution_points/2):
                    text = self.get_text_for_right_or_wrong_answer(
                        True,  is_user=is_user) + self.get_text_for_evaluation_of_points(is_user, level_up, 'middle', points_to_get)
                elif points_to_get == 0 and answer['answer'] == 'correct':
                    text = self.get_text_for_right_or_wrong_answer(
                        True,  is_user=is_user) + self.get_text_for_evaluation_of_points(is_user, level_up, 'less', points_to_get)
                elif points_to_get == 0 and answer['answer'] == 'wrong':
                    text = self.get_text_for_right_or_wrong_answer(
                        False, solution, solution_text="Die Lösung lautet: ", is_user=is_user)
            await self.telegram_bot_send_message('text', recipient_id, text)

        except Exception as e:
            logger.exception(e)

    async def increase_stars(self, filter):
        '''
        update the session object in DB with the current quest object which contains answer and earned points
        '''
        try:
            session_object = await self.session_collection.find_one(filter)
            if session_object:
                curr_stars = session_object['stars']
                update_stars = {
                    "$set": {
                        "stars": curr_stars + 1
                    }
                }
                await self.session_collection.update_one(filter, update_stars)
            return
        except Exception as e:
            logger.exception(e)
