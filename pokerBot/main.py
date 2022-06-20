import datetime
import telebot
from telebot import TeleBot

API_KEY = '5527567369:AAGH2h4kF0w0sW3eFARorWofAWPqbZfh7Go'
teleBot = telebot.TeleBot(API_KEY)
BUY = 20
CHIPS = 1000
JACKPOT = "Jackpot"


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
        self._bot.send_message(message.chat.id, "Welcome to the Poker Game!"
                                                "\n\U00002665 \U00002660 \U00002666 \U00002663")
        self._bot.send_message(message.chat.id, "Please enter players name (separated by ,):")

        #todo: remove
        self._players.update({"p1": {"buy": BUY, "food": 0, "food-player": ''}})
        self._players.update({"p2": {"buy": BUY, "food": 0, "food-player": ''}})
        self._players.update({"p3": {"buy": BUY, "food": 0, "food-player": ''}})
        self._players.update({"p4": {"buy": BUY, "food": 0, "food-player": ''}})


    def infinity_polling(self):
        self._bot.infinity_polling()

    def end(self, message):
        if not self.is_game_started(message.chat.id):
            return

        self._bot.send_message(message.chat.id, "\U0001f480 Game over!")

        end_time = datetime.datetime.now().replace(microsecond=0)
        total_time = end_time - self._startTime
        self._bot.send_message(message.chat.id, f"Total Game Time: {total_time}")
        self.status(message)
        self._start = False
        self._bot.send_message(message.chat.id, "Run winners command: /winners [name:chips] [name:chips] ...")

    def init_players(self, message):
        if not self.is_game_started(message.chat.id):
            return

        players = message.text[1:].split(',')
        for player in players:
            self._players.update({player: {"buy": BUY, "food": 0, "food-player": ''}})

        self._bot.send_message(message.chat.id, "\U00002705 Started!")
        self.send_jackpot(message)

        self._startTime = datetime.datetime.now().replace(microsecond=0)

    def is_game_started(self, chat_id):
        if not self._start:
            self._bot.send_message(chat_id, "Game has not started!")
            self._bot.send_message(chat_id, "Please run: /start")
            return False

        return True

    def re_buy(self, message):
        if not self.is_game_started(message.chat.id):
            return

        player = self.parse_rebuy(message)
        if not player:
            return

        self._players[player]["buy"] = self._players[player]["buy"] + BUY
        buy = self._players[player]["buy"]
        self._bot.send_message(message.chat.id, f"{player}\n    buy: {buy}")

    def parse_rebuy(self, message):
        split = message.text[1:].split(' ')
        if len(split) != 2:
            self._bot.send_message(message.chat.id, "Invalid command, please try again: /rebuy [name]")
            return

        player = split[1]
        if player not in self._players:
            self._bot.send_message(message.chat.id, f"Player {player} doesn't exist")
            return

        return player

    def status(self, message):
        if not self.is_game_started(message.chat.id):
            return

        self._bot.send_message(message.chat.id, "Status:")
        _status = ''
        for player in self._players:
            food_amount = self._players[player]["food"]
            food_player = self._players[player]["food-player"]
            food_str = f"\n    food: {food_amount} -> {food_player}" if food_amount > 0 else ""
            buy = self._players[player]["buy"]
            _status += f"{player}\n    buy: {buy}{food_str}\n---\n"

        self._bot.send_message(message.chat.id, _status)

        self.send_jackpot(message)

    def food_order(self, message):
        if not self.is_game_started(message.chat.id):
            return

        split = message.text[1:].split(' ')
        if len(split) != 3:
            self._bot.send_message(message.chat.id, "Invalid command, please try again: /food [name] [amount]")
            return

        player = split[1]
        if player not in self._players:
            self._bot.send_message(message.chat.id, f"Player {player} doesn't exist")
            return

        total_amount = float(split[2])
        amount = total_amount / len(self._players)
        for p in self._players:
            if p != player:
                self._players[p]["food"] = round(amount, 2)
                self._players[p]["food-player"] = player

        self.status(message)

    def winners(self, message):
        command_split = message.text[9:].split(' ')
        if len(command_split) < 1:
            self._bot.send_message(message.chat.id,
                                   "Invalid command, please try again: /winners [name:chips] [name:chips] ...")
            return

        self.send_jackpot(message)

        for winners_split in command_split:
            if ':' not in winners_split:
                self._bot.send_message(message.chat.id,
                                       "Invalid command, please try again: /winners [name:chips] [name:chips] ...")

            split = winners_split.split(":")
            winner = split[0]
            won = float(split[1]) / CHIPS * BUY

            if winner not in self._players:
                self._bot.send_message(message.chat.id, f"{winner} doesn't exist")
                return

            player = self._players[winner]
            amount = won - player["buy"]
            self._bot.send_message(message.chat.id, f"\U0001F3C6 {winner} won {amount} \U0001F4B5")

    def send_jackpot(self, message):
        jackpot = 0
        for player in self._players:
            jackpot += self._players[player]["buy"]

        self._bot.send_message(message.chat.id, f"{JACKPOT}: {jackpot} \U0001F4B5")


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


if __name__ == '__main__':
    main = Main(teleBot)
    main.infinity_polling()
