import datetime
from datetime import datetime

from telebot import types

from constants import *
from db import DbService
from model.model import CallbackDataType, ButtonCallbackData, Player


class PokerBotService(object):
    def __init__(self, bot):
        self._bot = bot
        self.db_service = DbService()

    def start(self, message):
        if self.db_service.get_started_timestamp() > 0:
            self._bot.send_message(message.chat.id, f"{ZANY_FACE} Game already started, please run "
                                                    f"/{END_COMMAND} to end game")
            return

        players = self.db_service.get_all_players()
        if len(players) == 0:
            self._bot.send_message(message.chat.id, f"No players were added, please run /{ADD_PLAYER_COMMAND} [name]")
            return

        self.init_players()
        self.db_service.insert_started_timestamp(datetime.now().replace(microsecond=0).timestamp())
        self._bot.send_message(message.chat.id, f"Welcome to the Poker Game!\n{CARDS_EMOJI}")
        self._bot.send_message(message.chat.id, f"{CHECK_MARK_GREEN} Started!")
        self.send_jackpot(message)

    def infinity_polling(self):
        self._bot.infinity_polling()

    def end(self, message):
        started_timestamp = self.is_game_started(message.chat.id)
        if started_timestamp == 0:
            return

        self._bot.send_message(message.chat.id, f"{SKULL} Game over!")

        start_time = datetime.fromtimestamp(started_timestamp)
        end_time = datetime.now().replace(microsecond=0)
        total_time = end_time - start_time
        self._bot.send_message(message.chat.id, f"{STOPWATCH} Total Game Time: {total_time}")
        self.status(message)
        self.db_service.remove_started_timestamp(started_timestamp)
        self._bot.send_message(message.chat.id, f"Run /{WINNER_COMMAND} [name] [chips]")

    def add_player(self, message):
        self._bot.send_message(message.chat.id,
                               "Enter player name", reply_markup=types.ForceReply())

    def add_player_name(self, message):
        player = self.db_service.search_player(message.text)

        if not player:
            player = Player(message.text)
            self.db_service.insert_player(player)
            self._bot.send_message(message.chat.id,
                                   f"{CHECK_MARK_BLACK} {player} was added successfully")
        else:
            self._bot.send_message(message.chat.id,
                                   f"{PROHIBITED} Player {message.text} already exist, please choose another name",
                                   reply_markup=types.ForceReply())

    def is_game_started(self, chat_id) -> float:
        started_timestamp = self.db_service.get_started_timestamp()
        if started_timestamp == 0:
            self._bot.send_message(chat_id, f"{PROHIBITED} Game has not started!")
            self._bot.send_message(chat_id, f"Please run: /{START_COMMAND}")

        return started_timestamp

    def re_buy(self, message):
        if not self.is_game_started(message.chat.id):
            return

        markup = self.generate_players_buttons()
        self._bot.send_message(message.chat.id, "\nRebuy - Choose Player", reply_markup=markup)

    def generate_players_buttons(self):
        markup = types.InlineKeyboardMarkup()
        players = self.db_service.get_all_players()
        for player in players:
            markup.add(types.InlineKeyboardButton(text=player.name,
                                                  callback_data=
                                                  ButtonCallbackData(CallbackDataType.REBUY, player.id).to_json()))

        return markup

    def delete_re_buy(self, message):
        if not self.is_game_started(message.chat.id):
            return

        markup = types.InlineKeyboardMarkup()

        players = self.db_service.get_all_players()
        for player in players:
            markup.add(types.InlineKeyboardButton(text=player.name,
                                                  callback_data=ButtonCallbackData(
                                                      CallbackDataType.DELETE_REBUY,
                                                      player.id).to_json()))

        self._bot.send_message(message.chat.id, "\nDelete Rebuy - Choose Player", reply_markup=markup)

    def add_rebuy_to_player(self, message, player_id, is_add):
        player = self.db_service.get_player(player_id)

        if not player:
            return

        if is_add:
            player.game_payment.amount += GAME
        elif player.game_payment.amount > GAME:
            player.game_payment.amount -= GAME

        self.db_service.update_player(player)
        self._bot.send_message(message.chat.id, f"{player}")

    def status(self, message):
        _status = ''
        players = self.db_service.get_all_players()
        for player in players:
            _status += f"{player}\n---\n"
        _status += self.format_jackpot(self.get_jackpot())

        self._bot.send_message(message.chat.id, _status)
        self._bot.send_message(message.chat.id,
                               "Game in progress" if self.db_service.get_started_timestamp() > 0 else "Game ended")

    def food_order(self, message):
        if not self.is_game_started(message.chat.id):
            return

        params = self.parse_command(message, FOOD_COMMAND, ['name', 'amount'])
        if len(params) == 0:
            return

        player_name = params[0]
        food_amount = params[1]

        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, player_name)
            return

        if not food_amount.isnumeric():
            self._bot.send_message(message.chat.id, f"{PROHIBITED} "
                                                    f"Invalid command, amount is not numeric")
            return

        total_amount = float(food_amount)
        players = self.db_service.get_all_players()
        amount = total_amount / len(players)
        for i in range(len(players)):
            if players[i].name != player_name:
                players[i].food_payment.amount = round(amount, 2)
                players[i].food_payment.owes_to = player_name
                self.db_service.update_player(players[i])

        self.status(message)

    def winner(self, message):
        if self.db_service.get_started_timestamp() > 0:
            self._bot.send_message(message.chat.id, f"{PROHIBITED} Please run /{END_COMMAND} to end game")
            return

        params = self.parse_command(message, WINNER_COMMAND, ['name', 'chips'])
        if len(params) == 0:
            return

        player_name = params[0]
        chips = params[1]

        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, player_name)
            return

        if not chips.isnumeric():
            self._bot.send_message(message.chat.id, f"{PROHIBITED} "
                                                    f"Invalid command, chips is not numeric")
            return

        player.win_payment.amount = float(chips) / CHIPS * GAME

        jackpot = self.get_jackpot()
        total_chips = jackpot / GAME * CHIPS
        total_wins = (self.get_total_wins() / GAME * CHIPS) + float(chips)
        if total_wins > total_chips:
            self._bot.send_message(message.chat.id,
                                   f"{PROHIBITED} Invalid wins amount, "
                                   f"total wins: {int(total_wins)}, chips: {int(total_chips)}")
            return

        self.db_service.update_player(player)
        self._bot.send_message(message.chat.id, f"{TROPHY} {player_name} won {player.win_payment.amount} {MONEY}")

        if total_wins < total_chips:
            self._bot.send_message(message.chat.id,
                                   f"Jackpot left with chips: {int(total_chips)}"
                                   f", total wins: {total_wins}"
                                   f"\nPlease add more /{WINNER_COMMAND}")
        else:
            self.status(message)

    def send_jackpot(self, message):
        jackpot = self.get_jackpot()
        self._bot.send_message(message.chat.id, self.format_jackpot(jackpot))

    @staticmethod
    def format_jackpot(jackpot: float):
        return f"{JACKPOT}: {jackpot} {MONEY}\nTotal Chips: {int(jackpot / GAME * CHIPS)}"

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

    def parse_command(self, message, command: str, params: []) -> []:
        split = message.text.split(' ')
        if len(split) < len(params) + 1:
            self._bot.send_message(message.chat.id, f"{PROHIBITED} "
                                                    f"Invalid command, please try again: /{command} {params}")
            return []

        return split[1:]

    def remove_player(self, message):
        params = self.parse_command(message, REMOVE_PLAYER_COMMAND, ['name'])
        if len(params) == 0:
            return

        name = params[0]
        player = self.db_service.search_player(name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, name)
            return

        if self.db_service.remove_player(name):
            self._bot.send_message(message.chat.id, f"{CHECK_MARK_BLACK} {name} was removed")

    @staticmethod
    def generate_menu_buttons():
        markup = types.InlineKeyboardMarkup()

        markup.add(types.InlineKeyboardButton(text='Start',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  START_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Status',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  STATUS_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Re-buy',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  RE_BUY_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Delete Re-buy',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  DELETE_RE_BUY_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Food',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  FOOD_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='End',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  END_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Winners',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  WINNER_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Add Player',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  ADD_PLAYER_COMMAND).to_json()),
                   types.InlineKeyboardButton(text='Remove Player',
                                              callback_data=ButtonCallbackData(
                                                  CallbackDataType.COMMAND,
                                                  REMOVE_PLAYER_COMMAND).to_json()))

        return markup

    def help(self, message):
        self._bot.send_message(message.chat.id, f"{BOOK} Menu", reply_markup=self.generate_menu_buttons())

    def send_player_does_not_exist(self, chat_id, player_name):
        self._bot.send_message(chat_id, f"{PROHIBITED} {player_name} doesn't exist")

    def init_players(self):
        players = self.db_service.get_all_players()
        [p.__init__(p.name) for p in players]
        [self.db_service.update_player(p) for p in players]
