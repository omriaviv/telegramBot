import datetime
import os

import telebot
from telebot import TeleBot

from pokerBot.types import JACKPOT, GAME, CHIPS, Player

API_KEY = os.getenv('API_KEY')
teleBot = telebot.TeleBot(API_KEY)


class Main(object):
    def __init__(self, bot):
        # type: (TeleBot) -> None
        self._bot = bot
        self._startTime = None
        self._players = []
        self._start = False

    def start(self, message):
        if self._start:
            self._bot.send_message(message.chat.id, "\U0001F92A Game already started, please run /end to end game")
            return

        self._start = True
        self._players = []
        self._bot.send_message(message.chat.id, "Welcome to the Poker Game!"
                                                "\n\U00002665 \U00002660 \U00002666 \U00002663")
        self._bot.send_message(message.chat.id, "Please enter players name (separated by ,):")

        self._startTime = datetime.datetime.now().replace(microsecond=0)

        # todo: remove
        self._players.append(Player("p1"))
        self._players.append(Player("p2"))
        self._players.append(Player("p3"))
        self._players.append(Player("p4"))

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

    def init_players(self, message):
        if not self.is_game_started(message.chat.id):
            return

        if len(self._players) > 0:
            self._bot.send_message(message.chat.id,
                                   "\U0001F6AB Players already added, please run /end and /start - to start new game")
            return

        names = message.text[1:].split(',')
        for name in names:
            self._players.append(Player(name))

        self._bot.send_message(message.chat.id, "\U00002705 Started!")
        self.send_jackpot(message)

    def is_game_started(self, chat_id):
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
        i = self._players.index(player)
        self._players[i] = player
        self._bot.send_message(message.chat.id, f"{player}")

    def parse_rebuy(self, message):
        split = message.text[1:].split(' ')
        if len(split) != 2:
            self._bot.send_message(message.chat.id, "\U0001F6AB Invalid command, please try again: /rebuy [name]")
            return

        player_name = split[1]
        players = [p for p in self._players if p.name == player_name]
        if len(players) < 1:
            self.send_player_does_not_exist(message.chat.id, player_name)
            return

        return players[0]

    def status(self, message):
        if not self.is_game_started(message.chat.id):
            return

        self._bot.send_message(message.chat.id, "Status:")
        _status = ''
        for player in self._players:
            _status += f"{player}\n---\n"

        self._bot.send_message(message.chat.id, _status)
        self.send_jackpot(message)

    def food_order(self, message):
        if not self.is_game_started(message.chat.id):
            return

        split = message.text[1:].split(' ')
        if len(split) != 3:
            self.send_invalid_food_command(message.chat.id)
            return

        player_name = split[1]
        players = [p for p in self._players if p.name == player_name]
        if len(players) < 1:
            self.send_player_does_not_exist(message.chat.id, player_name)
            return

        if not split[2].isnumeric():
            self.send_invalid_food_command(message.chat.id)
            return

        total_amount = float(split[2])
        amount = total_amount / len(self._players)
        for i in range(len(self._players)):
            if self._players[i].name != player_name:
                self._players[i].food_payment.amount = round(amount, 2)
                self._players[i].food_payment.owes_to = player_name

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
            players = [p for p in self._players if p.name == winner]
            if len(players) < 1:
                self.send_player_does_not_exist(message.chat.id, winner)
                return

            if not split[1].isnumeric():
                self.send_invalid_winners_command(message.chat.id)
                return

            won = float(split[1]) / CHIPS * GAME
            player = players[0]
            amount = won - player.game_payment.amount
            # todo validate jackpot amount with total chips
            # todo calculate owes to by game/food

            self._bot.send_message(message.chat.id, f"\U0001F3C6 {winner} won {amount if amount > 0 else 0} \U0001F4B5")

    def send_jackpot(self, message):
        jackpot = 0
        for player in self._players:
            jackpot += player.game_payment.amount

        self._bot.send_message(message.chat.id, f"{JACKPOT}: {jackpot} \U0001F4B5")

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


@teleBot.message_handler(func=lambda message: ',' in message.text)
def handle_message(message):
    main.init_players(message)


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


@teleBot.message_handler(commands=['help'])
def help(message):
    main.help(message)


if __name__ == '__main__':
    main = Main(teleBot)
    main.infinity_polling()
