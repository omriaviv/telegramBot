import os
import telebot

from pokerBot.pokerBotService import PokerBotService
from pokerBot.db.dbService import *

API_KEY = os.getenv('API_KEY')
teleBot = telebot.TeleBot(API_KEY)


class Main(object):
    def __init__(self):
        self.poker_bot_service = PokerBotService(teleBot)

    def start(self):
        self.poker_bot_service.infinity_polling()


@teleBot.message_handler(commands=[START_COMMAND])
def start(message):
    main.poker_bot_service.start(message)


@teleBot.message_handler(commands=[END_COMMAND])
def end(message):
    main.poker_bot_service.end(message)


@teleBot.message_handler(commands=[RE_BUY_COMMAND])
def re_buy(message):
    main.poker_bot_service.re_buy(message)


@teleBot.message_handler(commands=[STATUS_COMMAND])
def status(message):
    main.poker_bot_service.status(message)


@teleBot.message_handler(commands=[FOOD_COMMAND])
def food(message):
    main.poker_bot_service.food_order(message)


@teleBot.message_handler(commands=[WINNER_COMMAND])
def winner(message):
    main.poker_bot_service.winner(message)


@teleBot.message_handler(commands=[ADD_PLAYER_COMMAND])
def add_player(message):
    main.poker_bot_service.add_player(message)


@teleBot.message_handler(commands=[REMOVE_PLAYER_COMMAND])
def remove_player(message):
    main.poker_bot_service.remove_player(message)


@teleBot.message_handler(commands=[HELP_COMMAND])
def help_command(message):
    main.poker_bot_service.help(message)


if __name__ == '__main__':
    main = Main()
    main.start()
