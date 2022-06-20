import datetime

import telebot
from telebot import TeleBot

API_KEY = '5527567369:AAGH2h4kF0w0sW3eFARorWofAWPqbZfh7Go'
teleBot = telebot.TeleBot(API_KEY)
BUY = 20


class Main(object):
    def __init__(self, bot):
        # type: (TeleBot) -> None
        self._bot = bot
        self._startTime = {}
        self._players = {}
        self._start = False

    def start(self, message):
        self._start = True
        self._players = {}
        self._bot.send_message(message.chat.id, "Welcome to the Poker Game!")
        self._bot.send_message(message.chat.id, "Please enter players name (separated by ,):")

    def infinity_polling(self):
        self._bot.infinity_polling()

    def end(self, message):
        if not self.is_game_started(message.chat.id):
            return

        self._bot.send_message(message.chat.id, "Game over!")

        end_time = datetime.datetime.now().replace(microsecond=0)
        total_time = end_time - self._startTime
        self._bot.send_message(message.chat.id, "Total Game Time: " + str(total_time))
        self.status(message)
        self._start = False

    def init_players(self, message):
        if not self.is_game_started(message.chat.id):
            return

        players = message.text[1:].split(',')
        for player in players:
            self._players.update({player: BUY})

        self._bot.send_message(message.chat.id, "Started!")
        self._bot.send_message(message.chat.id, "Jackpot: " + str(len(self._players) * BUY))

        self._startTime = datetime.datetime.now().replace(microsecond=0)

    def is_game_started(self, chat_id):
        if not self._start:
            self._bot.send_message(chat_id, "Game was not started!")
            self._bot.send_message(chat_id, "Please run: /start")
            return False

        return True

    def re_buy(self, message):
        if not self.is_game_started(message.chat.id):
            return

        player = self.parse_rebuy(message)
        if not player:
            return

        self._players[player] = self._players[player] + BUY
        self._bot.send_message(message.chat.id, player + ": " + str(self._players[player]))

    def parse_rebuy(self, message):
        split = message.text[1:].split(' ')
        if len(split) != 2:
            self._bot.send_message(message.chat.id, "Invalid command, please try again: /rebuy [name]")
            return

        player = split[1]
        if player not in self._players:
            self._bot.send_message(message.chat.id, "Player " + player + " doesn't exist")
            return

        return player

    def status(self, message):
        self._bot.send_message(message.chat.id, "Re-buys:")
        for player in self._players:
            self._bot.send_message(message.chat.id, player + ": " + str(self._players[player]))

    def food_order(self, message):
        if not self.is_game_started(message.chat.id):
            return

        split = message.text[1:].split(' ')
        if len(split) != 3:
            self._bot.send_message(message.chat.id, "Invalid command, please try again: /food [name] [amount]")
            return

        player = split[1]
        if player not in self._players:
            self._bot.send_message(message.chat.id, "Player " + player + " doesn't exist")
            return

        amount = int(split[2])
        self._bot.send_message(message.chat.id, "Every player owes "
                               + player + ": " + str(amount / len(self._players)) + " for food")



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


if __name__ == '__main__':
    main = Main(teleBot)
    main.infinity_polling()
