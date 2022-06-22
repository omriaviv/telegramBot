from constants import GAME


class Player(object):
    def __init__(self, name: str):
        self.name = name
        self.game_payment = Payment(PaymentType.GAME, GAME, '')
        self.food_payment = Payment(PaymentType.FOOD, 0, '')
        self.win_payment = Payment(PaymentType.WIN, 0, '')

    def __str__(self):
        return f"{self.name}{self.game_payment}{self.food_payment}{self.win_payment}"

    def __dict__(self):
        return {
            'name': self.name,
            'food_payment': self.food_payment.__dict__(),
            'game_payment': self.game_payment.__dict__(),
            'win_payment': self.win_payment.__dict__()
        }

    @staticmethod
    def from_dict(dict):
        player = Player(dict['name'])
        player.game_payment = Payment.from_dict(dict['game_payment'])
        player.food_payment = Payment.from_dict(dict['food_payment'])
        player.win_payment = Payment.from_dict(dict['win_payment'])
        return player


class Payment(object):
    def __init__(self, payment_type: str, amount: float, owes_to: str):
        self.payment_type = payment_type
        self.amount = amount
        self.owes_to = owes_to

    def __str__(self):
        owes_to_str = f" -> {self.owes_to}" if self.owes_to else ''
        return f"\n\t\t\t{self.payment_type}: " \
               f"{self.amount if self.payment_type == PaymentType.WIN else self.amount * -1}{owes_to_str}" \
            if self.amount > 0 else ''

    def __dict__(self):
        return {'payment_type': self.payment_type, 'amount': self.amount, 'owes_to': self.owes_to}

    @staticmethod
    def from_dict(dict):
        return Payment(dict['payment_type'], dict['amount'], dict['owes_to'])


class PaymentType(object):
    GAME = 'GAME'
    FOOD = 'FOOD'
    WIN = 'WIN'
