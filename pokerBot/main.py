import datetime
import os

import telebot
from telebot import TeleBot

from pokerBot.db.dbService import DbService
from pokerBot.model import JACKPOT, GAME, CHIPS, Player

API_KEY = os.getenv('API_KEY')
teleBot = telebot.TeleBot(API_KEY)


class Main(object):
    def __init__(self, bot):
        # type: (TeleBot) -> None
        self._bot = bot
        self._startTime = None
        self._start = False
        self.db_service = DbService()

    def start(self, message):
        if self._start:
            self._bot.send_message(message.chat.id, "\U0001F92A Game already started, please run /end to end game")
            return

        players = self.db_service.get_all_players()
        if len(players) == 0:
            self._bot.send_message(message.chat.id, "No players were added, please run /add-player [name]")
            return

        self._start = True
        self._bot.send_message(message.chat.id, "Welcome to the Poker Game!"
                                                "\n\U00002665 \U00002660 \U00002666 \U00002663")

        self._startTime = datetime.datetime.now().replace(microsecond=0)
        self._bot.send_message(message.chat.id, "\U00002705 Started!")
        self.send_jackpot(message)

    def infinity_polling(self):
        self._bot.infinity_polling()

    def end(self, message):
        if not self.is_game_started(message.chat.id):
            return

        self._bot.send_message(message.chat.id, "\U0001f480 Game over!")

        end_time = datetime.datetime.now().replace(microsecond=0)
        total_time = end_time - self._startTime
        self._bot.send_message(message.chat.id, f"\U000023F1 Total Game Time: {total_time}")
        self.status(message)
        self._start = False
        self._bot.send_message(message.chat.id, "Run winners command: /winners [name:chips] [name:chips] ...")

    def add_player(self, message):
        name = self.parse_player_name(message, "/add-player")
        if not name:
            return

        player = self.db_service.search_player(name)
        if not player:
            player = Player(name)
            self.db_service.insert_player(player)
            self._bot.send_message(message.chat.id,
                                   f"Player added successfully:\n{player}")
        else:
            self._bot.send_message(message.chat.id,
                                   f"\U0001F6AB Player {name} already exist, please choose another name")

    def is_game_started(self, chat_id) -> bool:
        if not self._start:
            self._bot.send_message(chat_id, "\U0001F6AB Game has not started!")
            self._bot.send_message(chat_id, "Please run: /start")
            return False

        return True

    def re_buy(self, message):
        if not self.is_game_started(message.chat.id):
            return

        player = self.parse_rebuy(message)
        if not player:
            return

        player.game_payment.amount += GAME
        self.db_service.update_player(player)
        self._bot.send_message(message.chat.id, f"{player}")

    def parse_rebuy(self, message) -> Player:
        split = message.text[1:].split(' ')
        if len(split) != 2:
            self._bot.send_message(message.chat.id, "\U0001F6AB Invalid command, please try again: /rebuy [name]")
            return None

        player_name = split[1]
        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, player_name)

        return player

    def status(self, message):
        _status = ''
        players = self.db_service.get_all_players()
        for player in players:
            _status += f"{player}\n---\n"
        _status += f"{JACKPOT}: {self.get_jackpot()} \U0001F4B5"

        self._bot.send_message(message.chat.id, _status)

    def food_order(self, message):
        if not self.is_game_started(message.chat.id):
            return

        split = message.text[1:].split(' ')
        if len(split) != 3:
            self.send_invalid_food_command(message.chat.id)
            return

        player_name = split[1]
        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, player_name)
            return

        if not split[2].isnumeric():
            self.send_invalid_food_command(message.chat.id)
            return

        total_amount = float(split[2])
        players = self.db_service.get_all_players()
        amount = total_amount / len(players)
        for i in range(len(players)):
            if players[i].name != player_name:
                players[i].food_payment.amount = round(amount, 2)
                players[i].food_payment.owes_to = player_name
                self.db_service.update_player(players[i])

        self.status(message)

    def winners(self, message):
        command_split = message.text[9:].split(' ')
        if len(command_split) < 1:
            self.send_invalid_winners_command(message.chat.id)
            return

        for winners_split in command_split:
            if ':' not in winners_split:
                self.send_invalid_winners_command(message.chat.id)
                return

            split = winners_split.split(":")
            winner = split[0]
            player = self.db_service.search_player(winner)
            if not player:
                self.send_player_does_not_exist(message.chat.id, winner)
                return

            if not split[1].isnumeric():
                self.send_invalid_winners_command(message.chat.id)
                return

            player.win_payment.amount = float(split[1]) / CHIPS * GAME
            self.db_service.update_player(player)

            # todo calculate owes to by game/food

            self._bot.send_message(message.chat.id, f"\U0001F3C6 {winner} won {player.win_payment.amount} \U0001F4B5")

        # todo from db
        jackpot = self.get_jackpot()
        total_wins = self.get_total_wins()
        if total_wins > jackpot:
            self._bot.send_message(message.chat.id,
                                   f"\U0001F6AB Invalid wins amount, "
                                   f"total wins: {total_wins}, jackpot: {jackpot}")
        else:
            if total_wins < jackpot:
                self._bot.send_message(message.chat.id,
                                       f"Jackpot left with amount: {jackpot - total_wins}, jackpot: {jackpot}"
                                       f", total wins: {total_wins}"
                                       f"\nPlease run more /winners")

    def send_jackpot(self, message):
        jackpot = self.get_jackpot()

        self._bot.send_message(message.chat.id, f"{JACKPOT}: {jackpot} \U0001F4B5")

    def get_jackpot(self) -> float:
        jackpot = 0
        for player in self.db_service.get_all_players():
            jackpot += player.game_payment.amount

        return jackpot

    def get_total_wins(self) -> float:
        total_wins = 0
        for player in self.db_service.get_all_players():
            total_wins += player.win_payment.amount

        return total_wins

    def parse_player_name(self, message, command) -> str:
        split = message.text.split(' ')
        if len(split) < 2:
            self._bot.send_message(message.chat.id, f"\U0001F6AB Invalid command, please try again: {command} [name]")
            return ''

        return split[1]

    def remove_player(self, message):
        name = self.parse_player_name(message, "/remove-player")
        if not name:
            return

        player = self.db_service.search_player(name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, name)
            return

        if self.db_service.remove_player(name):
            self._bot.send_message(message.chat.id, f"\U00002714 {name} was removed")

    def help(self, message):
        help_str = f"- /start - start a game" \
                   f"\n- /status - get players status" \
                   f"\n- /[player_name1,player_name2,...] - enter players names" \
                   f"\n- /rebuy [player_name] - add re-buy to player" \
                   f"\n- /food [player_name] - add food order by player" \
                   f"\n- /end - end game" \
                   f"\n- /winners [player_name1:chips player_name2:chips ...] - enter the winners"

        self._bot.send_message(message.chat.id, f"\U0001F4D6\n{help_str}")

    def send_invalid_food_command(self, chat_id):
        self._bot.send_message(chat_id,
                               "\U0001F6AB Invalid command, please try again: /food [name] [amount]")

    def send_invalid_winners_command(self, chat_id):
        self._bot.send_message(chat_id,
                               "\U0001F6AB Invalid command, "
                               "please try again: /winners [name:chips] [name:chips] ...")

    def send_player_does_not_exist(self, chat_id, player_name):
        self._bot.send_message(chat_id, f"\U0001F6AB {player_name} doesn't exist")


@teleBot.message_handler(commands=['start'])
def start(message):
    main.start(message)


@teleBot.message_handler(commands=['end'])
def end(message):
    main.end(message)


@teleBot.message_handler(commands=['rebuy'])
def re_buy(message):
    main.re_buy(message)


@teleBot.message_handler(commands=['status'])
def status(message):
    main.status(message)


@teleBot.message_handler(commands=['food'])
def food(message):
    main.food_order(message)


@teleBot.message_handler(commands=['winners'])
def winners(message):
    main.winners(message)


@teleBot.message_handler(commands=['add-player'])
def add_player(message):
    main.add_player(message)


@teleBot.message_handler(commands=['remove-player'])
def remove_player(message):
    main.remove_player(message)


if __name__ == '__main__':
    main = Main(teleBot)
    main.infinity_polling()
