import datetime
from datetime import datetime

from pokerBot.db.dbService import DbService
from pokerBot.model import *


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
        self._bot.send_message(message.chat.id, f"Run winners command: "
                                                f"/{WINNERS_COMMAND} [name:chips] [name:chips] ...")

    def add_player(self, message):
        params = self.parse_command(message, ADD_PLAYER_COMMAND, ['name'])
        if len(params) == 0:
            return

        name = params[0]

        player = self.db_service.search_player(name)
        if not player:
            player = Player(name)
            self.db_service.insert_player(player)
            self._bot.send_message(message.chat.id,
                                   f"{CHECK_MARK_BLACK} {player} was added successfully")
        else:
            self._bot.send_message(message.chat.id,
                                   f"{PROHIBITED} Player {name} already exist, please choose another name")

    def is_game_started(self, chat_id) -> float:
        started_timestamp = self.db_service.get_started_timestamp()
        if started_timestamp == 0:
            self._bot.send_message(chat_id, f"{PROHIBITED} Game has not started!")
            self._bot.send_message(chat_id, f"Please run: /{START_COMMAND}")

        return started_timestamp

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
        params = self.parse_command(message, RE_BUY_COMMAND, ['name'])
        if len(params) == 0:
            return

        player_name = params[0]
        player = self.db_service.search_player(player_name)
        if not player:
            self.send_player_does_not_exist(message.chat.id, player_name)

        return player

    def status(self, message):
        _status = ''
        players = self.db_service.get_all_players()
        for player in players:
            _status += f"{player}\n---\n"
        _status += self.format_jackpot(self.get_jackpot())

        self._bot.send_message(message.chat.id, _status)

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

            self._bot.send_message(message.chat.id, f"{TROPHY} {winner} won {player.win_payment.amount} {MONEY}")

        jackpot = self.get_jackpot()
        total_wins = self.get_total_wins()
        if total_wins > jackpot:
            self._bot.send_message(message.chat.id,
                                   f"{PROHIBITED} Invalid wins amount, "
                                   f"total wins: {total_wins}, jackpot: {jackpot}")
        else:
            if total_wins < jackpot:
                self._bot.send_message(message.chat.id,
                                       f"Jackpot left with amount: {jackpot - total_wins}, jackpot: {jackpot}"
                                       f", total wins: {total_wins}"
                                       f"\nPlease add more /{WINNERS_COMMAND}")

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

    def help(self, message):
        help_str = f"- /{START_COMMAND} - start a game" \
                   f"\n- /{STATUS_COMMAND} - get players status" \
                   f"\n- /{RE_BUY_COMMAND} [player_name] - add re-buy to player" \
                   f"\n- /{FOOD_COMMAND} [player_name] - add food order by player" \
                   f"\n- /{END_COMMAND} - end game" \
                   f"\n- /{WINNERS_COMMAND} [player_name1:chips player_name2:chips ...] - enter the winners" \
                   f"\n- /{ADD_PLAYER_COMMAND} [player_name]" \
                   f"\n- /{REMOVE_PLAYER_COMMAND} [player_name]"

        self._bot.send_message(message.chat.id, f"{BOOK}\n{help_str}")

    def send_invalid_winners_command(self, chat_id):
        self._bot.send_message(chat_id,
                               f"{PROHIBITED} Invalid command, "
                               f"please try again: /{WINNERS_COMMAND} [name:chips] [name:chips] ...")

    def send_player_does_not_exist(self, chat_id, player_name):
        self._bot.send_message(chat_id, f"{PROHIBITED} {player_name} doesn't exist")

    def init_players(self):
        players = self.db_service.get_all_players()
        [p.__init__(p.name) for p in players]
        [self.db_service.update_player(p) for p in players]
