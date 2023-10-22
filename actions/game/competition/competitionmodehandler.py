import asyncio
import random
import time
import datetime
import os
from rasa_sdk.events import ReminderScheduled, ReminderCancelled, FollowupAction, SlotSet
from actions.groups.grouphandler import GroupHandler
from actions.timestamps.timestamphandler import TimestampHandler
from actions.gamification.countdown.countdown import Countdown
from actions.gamification.countdown.countdownhandler import CountdownHandler
from actions.game.gamemodehandler import GameModeHandler
from actions.achievements.achievementshandler import AchievementHandler
from actions.image_gen.text_on_image_gen import add_table_on_leaderboard
from actions.common.common import get_credentials, async_connect_to_db, get_dp_inmemory_db, ben_is_typing, delete_folder, create_folder_if_not_exists, setup_logging
from rasa_sdk.events import UserUtteranceReverted, FollowupAction, AllSlotsReset, Restarted
import logging
logger = setup_logging()


class CompetitionModeHandler(GameModeHandler):
    '''
    Specific Handler for Modi like GroupCompeition: KLOK, KLMK
    '''

    def __init__(self):
        super().__init__()

    # KLOK
    async def handle_validation_of_group_answers_KLOK(self, name_of_slot, filter, active_loop, sender_id, group_answers, quest, num_of_my_group):
        earned_points = 0
        group_id_opponent = filter['other_group']

        for answer in group_answers:
            points, solution = await self.calc_earned_points_competition(filter, answer, name_of_slot, sender_id, active_loop, quest)
            earned_points += points

        # if there more people in the other group I earn the average of my points
        num_of_opponent, _ = await self.number_of_team_mates(get_credentials(str(sender_id)))
        if num_of_opponent > num_of_my_group:
            print("UNGERADE ZAHL")
            difference_of_people = num_of_opponent - num_of_my_group
            average_points_of_my_group = earned_points / num_of_my_group
            earned_points += (int(average_points_of_my_group)
                              * int(difference_of_people))

        _, level_up = await self.update_session(filter, name_of_slot, earned_points,  group_answers, 'KLOK', mates_number=num_of_my_group)
        return earned_points, solution, level_up

    # KLMK
    async def handle_validation_of_group_answers_KLMK(self, name_of_slot, filter, active_loop, sender_id, group_answer, quest, num_of_my_group):
        group_id_opponent = filter['other_group']
        earned_points, solution = await self.calc_earned_points_competition(filter, group_answer, name_of_slot, sender_id, active_loop, quest)
        _, level_up = await self.update_session(filter, name_of_slot, earned_points, group_answer['answer'])
        return earned_points, solution, level_up

    async def handle_validation_of_group_answer(self, name_of_slot, filter, dispatcher, active_loop, sender_id, group_answer, quest, num_of_my_group):
        if active_loop == "quiz_form_KLOK":
            earned_points, solution, level_up = await self.handle_validation_of_group_answers_KLOK(name_of_slot, filter, active_loop, sender_id, group_answer, quest, num_of_my_group)
        else:
            earned_points, solution, level_up = await self.handle_validation_of_group_answers_KLMK(name_of_slot, filter, active_loop, sender_id, group_answer, quest, num_of_my_group)
        await self.set_status("evaluated", name_of_slot, filter, self.session_collection, True)
        waiting_countdown, utter_message = await self.msg_check_evaluation_status_of_opponent(filter['other_group'], name_of_slot, sender_id, active_loop, False)
        dispatcher.utter_message(response=utter_message)
        return [SlotSet("earned_points", earned_points), SlotSet("solution", solution), SlotSet("level_up", level_up), SlotSet("waiting_countdown", waiting_countdown.to_dict()), FollowupAction('action_set_reminder_competition')]

    async def get_winner_of_round(self, name_of_slot, earned_points, solution, group_answer, level_up, sender_id, countdown, slots, filter, game_modus):
        '''
        announce winner or looser of the question round
        '''
        group_id_opponent = filter['other_group']
        await self.evaluate_answer(sender_id, group_id_opponent, name_of_slot, earned_points, solution, group_answer, level_up, game_modus)
        # get achievements
        achievements_handler = AchievementHandler()
        await achievements_handler.earn_achievement(filter, slots, sender_id)
        await ben_is_typing(countdown, self)

        return [SlotSet(name_of_slot, "answered"), SlotSet("random_person", None), SlotSet("flag", None), SlotSet("countdown", None), SlotSet("answered", None), SlotSet("waiting_countdown", None), FollowupAction("action_forget_reminders_competition")]

    async def waiting_of_opponent(self, name_of_slot, sender_id, group_id_opponent, waiting_countdown, loop, dispatcher):
        try:
            filter = {
                "channel_id": str(group_id_opponent),
                "other_group": int(sender_id)
            }
            evaluated = await self.check_status('evaluated', name_of_slot, filter, self.session_collection)
            exceeded = False
            if not evaluated and waiting_countdown['countdown'] == 0:
                await self.set_status('exceeded', name_of_slot, filter, self.session_collection, True)
                exceeded = True
                # and die andere Gruppe
                text = "Ihr wart zu langsam ⏳😔 und verliert das Spiel. 😢🎮"
                await self.telegram_bot_send_message('text', str(group_id_opponent), text)

                return evaluated, None, exceeded

            # nach 15 Sekunden warten
            if not evaluated and waiting_countdown['countdown'] == (int(get_credentials("WAITING_COUNTDOWN"))-14):
                carry_on_message = ["Die andere Gruppe ist fertig und wartet schon 🕰️",
                                    "🙋‍♂️ die andere Gruppe ist schon bereit, seht zu 🚀",
                                    "👋 die andere Gruppe wartet schon geduldig 🤔",
                                    "Die andere Gruppe 🤝 ist fertig, beeilt euch 🎯",
                                    "📢 die andere Gruppe 🤝 erwartet euch, werdet fertig 🏁"]
                text = random.choice(carry_on_message)
                await self.telegram_bot_send_message('text', str(group_id_opponent), text)

                dispatcher.utter_message(
                    response="utter_waiting_msg_after_15_sec")

            # nach der Hälfte
            if not evaluated and waiting_countdown['countdown'] == (int(get_credentials("WAITING_COUNTDOWN"))/2):
                dispatcher.utter_message(
                    response="utter_waiting_msg_after_30_sec")

            # 15 Sekunden vor schluss
            if not evaluated and waiting_countdown['countdown'] == ((int(get_credentials("WAITING_COUNTDOWN"))*0.25) - 1):
                warning_msg = ["⏰🔴 Achtung! ⏳💬 Ihr müsst eure Antwort nun abgeben! 🕒 In 15 Sekunden ist das Spiel sonst vorbei und ihr verliert es! 😱🆘",
                               "🔴 Achtung! 📝💨 Ihr müsst eure Antwort jetzt abgeben! 🕐 In 15 Sekunden ist das Spiel vorbei und ihr verliert es! 😓🆘",
                               "🚨🔴 Achtung! 🗣️🏃‍♂️ Ihr müsst eure Antwort schnell abgeben! ⏰ In 15 Sekunden ist das Spiel vorbei und ihr verliert es! 😥🆘",
                               "🔴 Achtung! Ihr müsst eure Antwort nun abgeben! In 15 Sekunden ist das Spiel sonst vorbei und ihr verliert es! 🆘"]
                text = random.choice(warning_msg)
                await self.telegram_bot_send_message('text', str(group_id_opponent), text)

                dispatcher.utter_message(response="utter_waiting_msg_less_15_sec")
            waiting_countdown['countdown'] = waiting_countdown['countdown'] - int(get_credentials("COMPETITION_REMINDER"))
            return evaluated, waiting_countdown, exceeded
        except Exception as e:
            logger.exception(e)

    async def msg_check_evaluation_status_of_opponent(self, group_id_opponent, name_of_slot, sender_id, loop, is_user):
        '''
        '''
        try:
            # if multiple user have to answer for the team
            filter = {
                "channel_id": str(group_id_opponent),
                "other_group": int(sender_id)
            }

            if is_user:
                utter_message = "utter_is_user_waiting_msg"
            else:
                utter_message = "utter_is_group_waiting_msg"
            waiting_countdown_handler = CountdownHandler()
            waiting_countdown = Countdown(sender_id, name_of_slot, loop)
            waiting_countdown.countdown = int(
                get_credentials("WAITING_COUNTDOWN"))
            #waiting_countdown.text = "warten wir auf die andere Gruppe."
            return waiting_countdown, utter_message
        except Exception as e:
            logger.exception(e)
            return None

    async def create_waiting_countdown_message(self, name_of_slot, sender_id, group_id_opponent, loop):
        waiting_countdown_handler = CountdownHandler()
        waiting_countdown = Countdown(sender_id, name_of_slot, loop)
        waiting_countdown.countdown = int(get_credentials("WAITING_COUNTDOWN"))
        waiting_countdown.text = "warten wir auf die andere Gruppe."
        return waiting_countdown

    async def calc_earned_points_competition(self, filter, answer, name_of_slot, group_id, game_modus, quest):
        '''
        calculate the points which the user got for their answer
        '''
        username = answer['username'] if 'username' in answer else None

        try:
            earned_points = 0
            if name_of_slot[-1] == "o":
                points, evaluation, solution = await self.rate_open_question(answer=answer['answer'], quest=quest)
                print("PUNKTE: ", points)
                print("EVALUATION: ", evaluation)
                print("LÖSUNG: ", solution)
                logger.info("Pkt:" + str(points) + " Eval: " +
                            evaluation+" Lösg.: "+solution)
                if points > 10:
                    await self.set_status("correct", name_of_slot, filter, self.session_collection, True)
                # correct answer
                if points > 0:
                    earned_points = await self.calculate_points_competition(filter, name_of_slot, group_id, points, answer, evaluation, game_modus)
                    answer['answer'] = 'correct'
                # wrong answer
                else:
                    answer['answer'] = 'wrong'

                    if game_modus == 'quiz_form_KLOK' and username:
                        evaluation_text = evaluation if evaluation else ""
                        wrong_answer_text = self.get_text_for_right_or_wrong_answer(
                            False)
                        wrong_answer_text = '@%s: ' % (username) + \
                            wrong_answer_text + "\n" + evaluation_text
                        await self.telegram_bot_send_message('text', group_id, wrong_answer_text)
                    else:
                        if evaluation:
                            await self.telegram_bot_send_message('text', group_id, evaluation)

            # SINGLE / MULTIPLE CHOICE
            else:
                solution = await self._get_solution(name_of_slot)

                # correct is pased through button
                if answer['answer'] == 'correct':
                    await self.set_status("correct", name_of_slot, filter, self.session_collection, True)
                    earned_points = await self.calculate_points_competition(filter, name_of_slot, group_id, solution['points'], answer, None, game_modus)

                elif answer['answer'] == 'wrong' and game_modus == 'quiz_form_KLOK' and username:
                    wrong_answer_text = self.get_text_for_right_or_wrong_answer(
                        False, solution['solution'], solution_text="Die Lösung lautet: ", is_user=True)
                    wrong_answer_text = '@%s: ' % (username) + \
                        wrong_answer_text
                    await self.telegram_bot_send_message('text', group_id, wrong_answer_text)
                elif answer['answer'] == 'wrong':
                    wrong_answer_text = self.get_text_for_right_or_wrong_answer(
                        False, solution['solution'], solution_text="Die Lösung lautet: ")
                    await self.telegram_bot_send_message('text', group_id, wrong_answer_text)

                solution = solution['solution']
            # if KLOK bewerte einzelne Antworten hier !
            return earned_points, solution
        except Exception as e:
            logger.exception(e)

    async def calculate_points_competition(self, filter, name_of_slot,  id, points, answer, evaluation, game_modus):
        '''
        Check Timestamps of group answer, if the group takes too long for answering there will be 
        a decrease in getting points
        '''
        try:
            username = answer['username'] if 'username' in answer else None
            result = await self.get_needed_time_for_answering(answer, id)
            if name_of_slot[-1] == "o":
                points_to_get = await self.calc_points_for_in_time_answering_competition(result, 60, points, 4, name_of_slot, filter, evaluation, game_modus, username)
            else:
                points_to_get = await self.calc_points_for_in_time_answering_competition(result, 15, points, 2, name_of_slot, filter, evaluation, game_modus, username)
            return points_to_get
        except Exception as e:
            logger.exception(e)

    async def calc_points_for_in_time_answering_competition(self, result, time_bound, max_points, penalty, name_of_slot, filter, evaluation, game_modus, username):
        try:
            correct_text = self.get_text_for_right_or_wrong_answer(True)
            if game_modus == 'quiz_form_KLOK' and username:
                correct_text = '@%s: ' % (username) + correct_text
            # rechtzeitig geanwotert
            if result <= time_bound:
                await self.set_status("in_time", name_of_slot, filter, self.session_collection, True)
                points_to_get = max_points
                if evaluation:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text + evaluation)

                else:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text)

                print("\033[94m 1. Weniger als %s Sekunden gebraucht: %s, Punkte sind %s\033[0m" % (
                    time_bound, result, points_to_get))

            # etwas zu spät geantwortet
            elif result <= (time_bound+5):
                points_to_get = max(max_points - penalty, 0)

                text = self.get_text_for_right_or_wrong_answer(True)
                if evaluation:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text + evaluation + "\n\nAufgrund der verspäteten Antwort, wird eine Strafe von -%s Punkten verhängt." % penalty)
                else:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text + "Aufgrund der verspäteten Antwort, wird eine Strafe von -%s Punkten verhängt." % penalty)

                print("\033[94m 2. Weniger als %s Sekunden gebraucht: %s, Punkte sind %s\033[0m" % (
                    (time_bound+5), result, points_to_get))

            # zu spät geanwortet
            else:
                points_to_get = 0
                if evaluation:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text + evaluation + "\n\nLeider wurde die Antwort nicht rechtzeitig abgegeben, weshalb keine Punkte vergeben werden können.")
                else:
                    await self.telegram_bot_send_message('text', filter['channel_id'], correct_text + "Leider wurde die Antwort nicht rechtzeitig abgegeben, weshalb keine Punkte vergeben werden können.")

                print("\033[94m 3. Länger als %s Sekunden gebraucht: %s, Punkte sind 0\033[0m" % (
                    result, (time_bound+5)))
            return points_to_get

        except Exception as e:
            logger.exception(e)

    async def evaluate_answer(self, group_id, group_id_opponent, name_of_slot, my_group_points, solution, answer, is_level_up, game_modus):
        '''
        compare the earned points per questions between the two groups and check who is the winner of this round
        '''
        filter_group_opponent = {
            "channel_id": str(group_id_opponent),
            "other_group": int(group_id),
        }
        try:
            opponent = await self.session_collection.find_one(filter_group_opponent)
            level_up_text = ""
            if is_level_up:
                level_context = ["\n😎🆙 Ihr seid ein weiteres Level aufgestiegen!",
                                 "\n🤩 Super, ihr habt euch auf ein höheres Level katapultiert!",
                                 "\n🎉 Herzlichen Glückwunsch, ihr habt ein weiteres Level erreicht! 🚀",
                                 "\n🌟 Wow, ihr habt es geschafft! Ihr seid ein Level nach oben gestiegen!",
                                 "\n🏆 Klasse Leistung! Ihr seid auf ein höheres Level aufgestiegen! 📈",
                                 "\n🔝 Top, ihr habt euch auf das nächste Level gearbeitet!",
                                 "\n🚀 Fantastisch, ihr seid ein Level aufgestiegen! Weiter so! 💪",
                                 "\n🎯 Ziel erreicht! Ihr seid nun auf einem neuen Level!",
                                 "\n🎊 Bravo, ihr habt euch auf ein neues Level vorgearbeitet! 🥳"]
                level_up_text = random.choice(level_context)

            winner_options = []
            for other in reversed(opponent['questions']):
                if other['id'] == name_of_slot:
                    filter = {
                        "channel_id": str(group_id),
                        "other_group": int(group_id_opponent),
                    }
                    # KLOK
                    if game_modus == 'quiz_form_KLOK':
                        winner_options = self.get_winner_option_KLOK(
                            my_group_points, other['points'])
                    # KLMK
                    else:
                        winner_options = self.get_winner_option_KLMK(
                            my_group_points, other['points'], answer['answer'], solution)

            winner = random.choice(winner_options) if len(
                winner_options) > 0 else "Ihr habt gewonnen!  🎉"
            await self.telegram_bot_send_message('text', group_id, winner + level_up_text)

        except Exception as e:
            logger.exception(e)

    def get_winner_option_KLOK(self, my_group_points, other_group_points):
        try:
            if my_group_points == 0 and other_group_points == 0:
                winner_options = [
                    "Beide Gruppe haben 0 Punkte geholt.",
                    "Beide Teams haben keine Punkte erzielt.",
                    "Beide Gruppen haben null Punkte erreicht."
                ]
            elif my_group_points == 0 and other_group_points > 0:
                winner_options = [
                    "Ihr habt 0 Punkte geholt. Die andere Gruppe hat %s Punkte erreicht und gewinnt diese Runde." % (
                        other_group_points),
                    "Ihr habt keine Punkte erzielt. Mit %s Punkten sichert sich die andere Gruppe den Sieg in dieser Runde." % (
                        other_group_points),
                    "Ihr habt null Punkte erreicht. In dieser Runde erzielt die andere Gruppe %s Punkte und geht als Gewinner hervor." % (
                        other_group_points)
                ]
            elif my_group_points > other_group_points:
                winner_options = [
                    "Ihr habt diese Fragerunde gewonnen. 🎉\nIhr verdient euch %s Punkte und die andere Gruppe hat %s Punkte erzielt." % (
                        my_group_points,  other_group_points),
                    "Ihr habt diese Fragerunde gewonnen! 🎉\nIhr erzielt %s Punkte, während die andere Gruppe %s Punkte erreicht hat." % (
                        my_group_points, other_group_points),
                    "Herzlichen Glückwunsch, ihr seid die Gewinner dieser Fragerunde! 🎉\nIhr verdient euch %s Punkte, während die andere Gruppe %s Punkte erzielt." % (
                        my_group_points, other_group_points)
                ]

            elif my_group_points < other_group_points:
                winner_options = [
                    "Die andere Gruppe hat mehr Punkte geholt. 😔 Ihr bekommt %s Punkte und die andere Gruppe hat %s Punkte erzielt." % (
                        my_group_points,  other_group_points),
                    "Leider hat die andere Gruppe mehr Punkte erreicht. 😔 Ihr erhaltet %s Punkte, während die andere Gruppe %s Punkte erzielt hat." % (
                        my_group_points, other_group_points),
                    "Die andere Gruppe hat mehr Punkte geholt. 😔 Ihr bekommt %s Punkte, während die andere Gruppe %s Punkte erzielt hat." % (
                        my_group_points, other_group_points)
                ]
            else:
                winner_options = [
                    "Beide Gruppen haben gleich viele (%s) Punkte für diese Frage erzielt. 🤝" % (
                        my_group_points),
                    "Beide Gruppen haben für diese Frage jeweils %s Punkte erzielt. 🤝" % my_group_points,
                    "Es gibt ein Unentschieden für diese Frage, da beide Gruppen %s Punkte erreicht haben. 🤝" % my_group_points
                ]
            return winner_options

        except Exception as e:
            logger.exception(e)
            return []

    def get_winner_option_KLMK(self, my_group_points, other_group_points, answer, solution):
        try:
            # richtig geantwortet, aber überzogen, andere Gruppe 0 Punkte geholt
            if my_group_points == 0 and answer == 'correct' and other_group_points == 0:
                winner_options = [
                    "Die andere Gruppe hat ebenfalls 0 Punkte geholt. 🤝 Nicht schlimm, wir bleiben stark!",
                    "Die andere Gruppe hat ebenfalls keine Punkte erzielt. 💪 Gemeinsam werden wir besser!",
                    "Die andere Gruppe hat ebenfalls null Punkte erreicht. 🌟 Lasst uns gemeinsam aufholen!"
                ]
            # richtig geantwortet, aber überzogen, andere Gruppe >0 Punkte geholt
            elif my_group_points == 0 and answer == 'correct' and other_group_points > 0:
                winner_options = [
                    "Die andere Gruppe hat %s Punkte erreicht und gewinnt diese Runde.\nLernen aus jeder Runde macht uns stärker. 🚀" % (
                        other_group_points),
                    "Mit %s Punkten sichert sich die andere Gruppe den Sieg in dieser Runde.\nKopf hoch! Unser Fortschritt zählt. 🌈" % (
                        other_group_points),
                    "In dieser Runde erzielt die andere Gruppe %s Punkte und geht als Gewinner hervor.\nNicht schlimm, wir geben nicht auf! 💫" % (
                        other_group_points)
                ]

            # ich habe falsch geantwortet und die andere Gruppe hat ebenfalls 0 Punkte geholt
            elif my_group_points == 0 and answer == 'wrong' and other_group_points == 0:
                winner_options = [
                    "Ihr habt die Frage leider falsch beantwortet. 😔 Die andere Gruppe hat ebenfalls 0 Punkte geholt. Weiter geht's! 😊",
                    "Schade, ihr habt die Frage leider falsch beantwortet. 😔 Die andere Gruppe hat ebenfalls keine Punkte erzielt. Weiter geht es! 💪",
                    "Leider habt ihr die Frage falsch beantwortet. 😔 Die andere Gruppe hat ebenfalls null Punkte erreicht. Wir bleiben stark! 💪"
                ]

            # ich habe falsch geantworter, die andere Gruppe richtig
            elif my_group_points == 0 and answer == 'wrong' and other_group_points > 0:
                winner_options = [
                    "Ihr habt die Frage leider falsch beantwortet. Die andere Gruppe hat sie richtig beanwortet.\nIhr bekommt 0 Punkte und die gegnerische Gruppe verdient sich %s Punkte. Bleibt weiter dran 💫" % (
                        other_group_points),
                    "Leider habt ihr die Frage falsch beantwortet, während die andere Gruppe sie richtig beantwortet hat.\nIhr erhaltet keine Punkte, während die gegnerische Gruppe sich %s Punkte verdient. Weiter geht's! 💪" % (
                        other_group_points),
                    "Eure Antwort auf die Frage war leider falsch, während die andere Gruppe sie richtig beantwortet hat.\nIhr erzielt keine Punkte, während die gegnerische Gruppe sich %s Punkte verdient. Weiter geht's! 😊" % (
                        other_group_points)
                ]

            # ich habe mehr Punkte geholt als die andere
            elif my_group_points > other_group_points:
                winner_options = [
                    "Ihr habt diese Fragerunde gewonnen. 🎉\nIhr verdient euch %s Punkte und die andere Gruppe hat %s Punkte erzielt." % (
                        my_group_points,  other_group_points),
                    "Ihr habt diese Fragerunde gewonnen! 🥇\nIhr erzielt %s Punkte, während die andere Gruppe %s Punkte erreicht hat." % (
                        my_group_points, other_group_points),
                    "Herzlichen Glückwunsch, ihr seid die Gewinner dieser Fragerunde! 🏆\nIhr verdient euch %s Punkte, während die andere Gruppe %s Punkte erzielt." % (
                        my_group_points, other_group_points)
                ]

            # ich habe weniger Punkte geholt als die andere
            elif my_group_points < other_group_points:
                winner_options = [
                    "Die andere Gruppe hat mehr Punkte geholt. 😔 Ihr bekommt %s Punkte und die andere Gruppe hat %s Punkte erzielt.\nLernen aus jeder Runde macht uns stärker. 🚀" % (
                        my_group_points,  other_group_points),
                    "Leider hat die andere Gruppe mehr Punkte erreicht. 😔 Ihr erhaltet %s Punkte, während die andere Gruppe %s Punkte erzielt hat.\nKopf hoch! Unser Fortschritt zählt. 🌈" % (
                        my_group_points, other_group_points),
                    "Die andere Gruppe hat mehr Punkte geholt. 😔 Ihr bekommt %s Punkte, während die andere Gruppe %s Punkte erzielt hat.\nNicht schlimm, wir geben nicht auf! 💫" % (
                        my_group_points, other_group_points)
                ]
            # beide Gruppen gleih viel geholt
            else:
                winner_options = [
                    "Beide Gruppen haben gleich viele (%s) Punkte für diese Frage erzielt. 🤝" % (
                        my_group_points),
                    "Beide Gruppen haben für diese Frage jeweils %s Punkte erzielt. 🤝" % my_group_points,
                    "Es gibt ein Unentschieden für diese Frage, da beide Gruppen %s Punkte erreicht haben. 🤝" % my_group_points
                ]
            return winner_options

        except Exception as e:
            logger.exception(e)
            return None

    async def get_winner(self, group_id, group_id_opponent, dispatcher):
        filter_my_group = {
            "channel_id": str(group_id),
            "other_group": int(group_id_opponent)
        }

        filter_group_opponent = {
            "channel_id": str(group_id_opponent),
            "other_group": int(group_id),
        }
        try:
            opponent = await self.session_collection.find_one(filter_group_opponent)
            points_opponent = opponent['total_points']

            my_group = await self.session_collection.find_one(filter_my_group)
            points_my_group = my_group['total_points']
            if points_my_group > points_opponent:
                # send Badge und erhöhe badge
                achievement_handler = AchievementHandler()
                achievement = "GESAMTSIEGER"
                if await achievement_handler.insert_achievement(filter_my_group, achievement):
                    badges = get_dp_inmemory_db("./badges.json")
                    dispatcher.utter_message(image=badges[achievement])
                    dispatcher.utter_message(text="Herzlichen Glückwunsch! 🎉🏆 Ihr habt mit einem beeindruckenden %s:%s Sieg gewonnen! 🎊🥇 Euer Team hat großartig gespielt und verdient den Erfolg! 👏😄" % (
                        points_my_group, points_opponent))
                    text = "mygroup"
            elif points_opponent > points_my_group:
                text = "Gegner gewonnen"
                dispatcher.utter_message(text="Leider habt ihr mit %s:%s verloren 😔💔, aber ihr habt großartig gekämpft und es war ein spannendes Spiel." % (
                    points_my_group, points_opponent))
            else:
                text = "Unternschieden"
                dispatcher.utter_message(text="Das Spiel endete unentschieden mit einem Ergebnis von %s:%s. 🤝 Es war ein hart umkämpftes Match, und beide Teams haben ihr Bestes gegeben." % (
                    points_my_group, points_opponent))
            return text

        except Exception as e:
            logger.exception(e)
            return None

    async def insert_leaderboard(self, session, loop, dispatcher, team_name, sender_id):
        try:
            # get points
            total_points = session['total_points']
            group_title = team_name

            # Aktuellen Unix-Zeitstempel erhalten
            unix_timestamp = int(time.time())
            # gen entry
            entry = {'Gruppenname': group_title, 'Punkte': total_points,
                     'Spieltag': unix_timestamp, 'Gamemode': loop}

            # insert entry
            await self.leaderboard_collection.insert_one(entry)

            await self.print_leaderboard(entry, dispatcher, loop, sender_id)

        except Exception as e:
            logger.exception(e)

    def find_group_place(self, sorted_list, group):
        for i, entry in enumerate(sorted_list, start=1):
            if entry['Gruppenname'] == group['Gruppenname'] and entry['Spieltag'] == group['Spieltag'] and entry['Gamemode'] == group['Gamemode']:
                return i
        return None

    def format_date(self, timestamp):
        datetime_obj = datetime.datetime.fromtimestamp(timestamp)
        return datetime_obj.strftime("%d-%m")

    async def print_leaderboard(self, my_group, dispatcher, gamemode, sender_id):
        try:
            leaderboard_list = await self.leaderboard_collection.find().to_list(length=None)
            filtered_list = [entry for entry in leaderboard_list if entry.get(
                'Gamemode', None) == gamemode]
            sorted_list = sorted(
                filtered_list, key=lambda x: x['Punkte'], reverse=True)

            # give best x teams
            max_number = min(
                int(get_credentials('RANK_LIST')), len(sorted_list))
            best_entries = sorted_list[:max_number]

            # Tabelle vorbereiten
            tab_data = []
            # get place of group
            if my_group not in best_entries:
                place = self.find_group_place(sorted_list, my_group)
                # get Group before
                place_before = sorted_list[place-2]
                tab_data.append([place-1, place_before['Gruppenname'],
                                place_before['Punkte'], self.format_date(place_before['Spieltag'])])

                # current group
                # dateformat "DD-MM"
                current_place = sorted_list[place-1]
                spieltag = self.format_date(current_place['Spieltag'])
                tab_data.append(
                    [place, current_place['Gruppenname'], current_place['Punkte'], spieltag])

                # group after
                if len(sorted_list) >= place + 1:
                    place_after = sorted_list[place]
                    tab_data.append([place+1, place_after['Gruppenname'],
                                    place_after['Punkte'], self.format_date(place_after['Spieltag'])])
            else:
                for i, entry in enumerate(best_entries, start=1):
                    group_title = entry['Gruppenname']
                    total_points = entry['Punkte']
                    # dateformat "DD-MM"
                    spieltag = self.format_date(entry['Spieltag'])
                    tab_data.append([i, group_title, total_points, spieltag])

            path = "actions/image_gen/output/%s/%s" % (gamemode, sender_id)
            folder_path = create_folder_if_not_exists(path)
            image_name = "ranking.png"
            image_path = os.path.join(path, image_name)
            add_table_on_leaderboard(tab_data, image_path)

            # send photo
            await self.telegram_bot_send_message('photo', sender_id, image_path)

        except Exception as e:
            logger.exception(e)
