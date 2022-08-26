import os
import telebot

from constants import *
from model.model import ButtonCallbackData, CallbackDataType
from service import PokerBotService

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


@teleBot.message_handler(commands=[ADD_PLAYER_COMMAND, ADD_PLAYER_COMMAND2])
def add_player(message):
    main.poker_bot_service.add_player(message)


@teleBot.message_handler(commands=[REMOVE_PLAYER_COMMAND, REMOVE_PLAYER_COMMAND2])
def remove_player(message):
    main.poker_bot_service.remove_player(message)


@teleBot.message_handler(commands=[HELP_COMMAND])
def help_command(message):
    main.poker_bot_service.help(message)


def is_reply_add_player(message):
    if message.reply_to_message.text == 'Enter player name' \
            or 'please choose another name' in message.reply_to_message.text:
        main.poker_bot_service.add_player_name(message)


@teleBot.message_handler(func=is_reply_add_player)


@teleBot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    callback_data = ButtonCallbackData.from_json(call.data)
    if callback_data.type == CallbackDataType.COMMAND:
        command = callback_data.value
        if command == START_COMMAND:
            main.poker_bot_service.start(call.message)
        elif command == STATUS_COMMAND:
            main.poker_bot_service.status(call.message)
        elif command == RE_BUY_COMMAND:
            main.poker_bot_service.re_buy(call.message)
        elif command == DELETE_RE_BUY_COMMAND:
            main.poker_bot_service.delete_re_buy(call.message)
        elif command == FOOD_COMMAND:
            main.poker_bot_service.food_order(call.message)
        elif command == END_COMMAND:
            main.poker_bot_service.end(call.message)
        elif command == WINNER_COMMAND:
            main.poker_bot_service.winner(call.message)
        elif command == ADD_PLAYER_COMMAND:
            main.poker_bot_service.add_player(call.message)
        elif command == REMOVE_PLAYER_COMMAND:
            main.poker_bot_service.remove_player(call.message)
    elif callback_data.type == CallbackDataType.REBUY:
        main.poker_bot_service.add_rebuy_to_player(call.message, callback_data.value, True)
    elif callback_data.type == CallbackDataType.DELETE_REBUY:
        main.poker_bot_service.add_rebuy_to_player(call.message, callback_data.value, False)


if __name__ == '__main__':
    main = Main()
    main.start()
