from tinydb import TinyDB, Query

from pokerBot.model import *


class DbService(object):
    def __init__(self):
        self.db = TinyDB('db/db.json')
        self.query = Query()

    def insert_player(self, player: Player) -> int:
        return self.db.insert(player.__dict__())

    def get_all_players(self) -> []:
        players = self.db.search(self.query.game_payment.exists())
        return [Player.from_dict(p) for p in players]

    def search_player(self, name: str) -> Player:
        players = self.db.search(self.query.name == name)
        return Player.from_dict(players[0]) if len(players) > 0 else None

    def update_player(self, player: Player) -> bool:
        ids = self.db.update(player.__dict__(), self.query.name == player.name)
        return True if len(ids) > 0 else False

    def remove_player(self, player_name: str) -> bool:
        ids = self.db.remove(self.query.name == player_name)
        return True if len(ids) > 0 else False

    def insert_started_timestamp(self, timestamp: float) -> int:
        return self.db.insert({'started_timestamp': timestamp})

    def remove_started_timestamp(self, timestamp: float) -> int:
        ids = self.db.remove(self.query.started_timestamp == timestamp)
        return True if len(ids) > 0 else False

    def get_started_timestamp(self) -> float:
        timestamps = self.db.search(self.query.started_timestamp.exists())
        return timestamps[0]['started_timestamp'] if len(timestamps) > 0 else 0

