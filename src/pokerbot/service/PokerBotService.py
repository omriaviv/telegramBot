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
            self._bot.send_message(message.chat.id, f"No players were added, please run /{ADD_PLAYER_COMMAND}")
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
        self.db_service.remove_started_timestamp(started_timestamp)
        self.status(message)
        self.winners_choose_player(message)

    def enter_player_name(self, message):
        self._bot.send_message(message.chat.id,
                               "Enter player name", reply_markup=types.ForceReply())

    def add_player(self, message):
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

        markup = self.generate_players_buttons(CallbackDataType.REBUY)
        self._bot.send_message(message.chat.id, "\nRebuy - Choose Player", reply_markup=markup)

    def generate_players_buttons(self, callback_data_type: CallbackDataType):
        markup = types.InlineKeyboardMarkup()
        players = self.db_service.get_all_players()
        for player in players:
            markup.add(types.InlineKeyboardButton(text=player.name,
                                                  callback_data=
                                                  ButtonCallbackData(callback_data_type, player.id).to_json()))

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
            self.send_player_does_not_exist(message.chat.id)
            return

        player.add_rebuy(is_add)

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

    def food(self, message):
        if not self.is_game_started(message.chat.id):
            return

        markup = self.generate_players_buttons(CallbackDataType.FOOD)
        self._bot.send_message(message.chat.id, "\nFood - Choose Player", reply_markup=markup)

    def food_enter_amount(self, message, player_id):
        player = self.db_service.get_player(player_id)

        if not player:
            self.send_player_does_not_exist(message.chat.id)
            return

        self._bot.send_message(message.chat.id,
                               f"{player.name}, please enter food amount", reply_markup=types.ForceReply())

    def food_order(self, message):
        split = message.reply_to_message.text.split(',')
        player_name = split[0]

        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id)
            return

        food_amount = message.text
        if not food_amount.isnumeric():
            self._bot.send_message(message.chat.id, f"{PROHIBITED} Amount must be numeric")
            return

        total_amount = float(food_amount)
        players = self.db_service.get_all_players()
        amount = total_amount / len(players)
        for i in range(len(players)):
            if players[i].name != player_name:
                players[i].food_payment.amount = round(amount, 2)
                players[i].food_payment.owes_to = player_name
                self.db_service.update_player(players[i])
            else:
                players[i].food_payment.amount = 0
                players[i].food_payment.owes_to = None
                self.db_service.update_player(players[i])

        self.status(message)

    def winners_choose_player(self, message):
        if self.db_service.get_started_timestamp() > 0:
            self._bot.send_message(message.chat.id, f"{PROHIBITED} Please run /{END_COMMAND} to end game")
            return

        markup = self.generate_players_buttons(CallbackDataType.WINNERS)
        self._bot.send_message(message.chat.id, "\nWinners - Choose Player", reply_markup=markup)

    def winners_enter_chips(self, message, player_id):
        player = self.db_service.get_player(player_id)

        if not player:
            self.send_player_does_not_exist(message.chat.id)
            return

        self._bot.send_message(message.chat.id,
                               f"{player.name}, please enter chips count", reply_markup=types.ForceReply())

    def winners(self, message):
        split = message.reply_to_message.text.split(',')
        player_name = split[0]
        chips = message.text

        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id)
            return

        if not chips.isnumeric():
            self._bot.send_message(message.chat.id, f"{PROHIBITED} "
                                                    f"Chips amount must be numeric")
            return

        jackpot = self.get_jackpot()
        total_chips = jackpot / REBUY_AMOUNT * CHIPS
        winners_chips = (self.get_total_wins() / REBUY_AMOUNT * CHIPS) + float(chips)
        if winners_chips > total_chips:
            self._bot.send_message(message.chat.id,
                                   f"{PROHIBITED} Invalid wins amount, "
                                   f"total wins: {int(winners_chips)}, chips: {int(total_chips)}")
            return

        player.win_payment.amount = (float(chips) / CHIPS * REBUY_AMOUNT)
        self.db_service.update_player(player)

        self.send_player_win_message(message, player)

        if winners_chips < total_chips:
            self._bot.send_message(message.chat.id,
                                   f"Jackpot left with chips: {int(total_chips)-int(winners_chips)}")
            self.winners_choose_player(message)
        else:
            self.send_final_status_message(message)

    def send_final_status_message(self, message):
        _status = ''
        players = self.db_service.get_all_players()
        for p in players:
            if p.win_payment.amount > p.game_payment.amount:
                p.win_payment.amount = p.win_payment.amount - p.game_payment.amount
                p.game_payment.amount = 0
            elif p.win_payment.amount < p.game_payment.amount:
                p.game_payment.amount = p.game_payment.amount - p.win_payment.amount
                p.win_payment.amount = 0
            else:
                p.game_payment.amount = 0
                p.win_payment.amount = 0

            _status += f"{p}\n---\n"
        self._bot.send_message(message.chat.id, _status)
        self._bot.send_message(message.chat.id, "Game ended")

    def send_player_win_message(self, message, player):
        win_amount = player.win_payment.amount
        if win_amount > player.game_payment.amount:
            win_amount = win_amount - player.game_payment.amount
        else:
            win_amount = 0
        self._bot.send_message(message.chat.id, f"{TROPHY} {player.name} won {win_amount} {MONEY}")

    def send_jackpot(self, message):
        jackpot = self.get_jackpot()
        self._bot.send_message(message.chat.id, self.format_jackpot(jackpot))

    @staticmethod
    def format_jackpot(jackpot: float):
        return f"{JACKPOT}: {jackpot} {MONEY}\nTotal Chips: {int(jackpot / REBUY_AMOUNT * CHIPS)}"

    def get_jackpot(self) -> float:
        jackpot = 0
        for player in self.db_service.get_all_players():
            jackpot += player.rebuy_count * REBUY_AMOUNT

        return jackpot

    def get_total_wins(self) -> float:
        total_wins = 0
        for player in self.db_service.get_all_players():
            total_wins += player.win_payment.amount

        return total_wins

    def remove_player(self, message):
        markup = self.generate_players_buttons(CallbackDataType.REMOVE_PLAYER)
        self._bot.send_message(message.chat.id, "\nRemove Player - Choose Player", reply_markup=markup)

    def remove_player_from_db(self, message, player_id):
        player = self.db_service.get_player(player_id)

        if not player:
            self.send_player_does_not_exist(message.chat.id)
            return

        if self.db_service.remove_player(player.name):
            self._bot.send_message(message.chat.id, f"{CHECK_MARK_BLACK} {player.name} was removed")

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

    def menu(self, message):
        self._bot.send_message(message.chat.id, f"{BOOK} Menu", reply_markup=self.generate_menu_buttons())

    def send_player_does_not_exist(self, chat_id):
        self._bot.send_message(chat_id, f"{PROHIBITED} Player doesn't exist")

    def init_players(self):
        players = self.db_service.get_all_players()
        [p.__init__(p.name) for p in players]
        [self.db_service.update_player(p) for p in players]
