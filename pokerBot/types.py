JACKPOT = "Jackpot"
GAME = 20
CHIPS = 1000


class Player(object):
    def __init__(self, name: str, game_amount: float):
        self.name = name
        self.game_payment = Payment(PaymentType.GAME, game_amount, JACKPOT)
        self.food_payment = Payment(PaymentType.FOOD, 0, '')


class Payment(object):
    def __init__(self, payment_type: str, amount: float, owes_to: str):
        self.payment_type = payment_type
        self.amount = amount
        self.owes_to = owes_to


class PaymentType(object):
    GAME = 'GAME'
    FOOD = 'FOOD'
