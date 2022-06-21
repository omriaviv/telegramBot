from tinydb import TinyDB, Query

from pokerBot.model import Player


class DbService(object):
    def __init__(self):
        self.db = TinyDB('db/db.json')

    def insert_player(self, player: Player):
        self.db.insert(player.__dict__())

    def get_all_players(self):
        players = self.db.all()
        return [Player.from_dict(p) for p in players]

    def search_player(self, name: str):
        player = Query()
        return self.db.search(player.name == name)

    def update_player(self, player: Player):
        p = Query()
        self.db.update(player.__dict__(), p.name == player.name)

