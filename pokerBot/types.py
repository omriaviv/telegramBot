JACKPOT = "Jackpot"
GAME = 20
CHIPS = 1000


class Player(object):
    def __init__(self, name: str):
        self.name = name
        self.game_payment = Payment(PaymentType.GAME, GAME, JACKPOT)
        self.food_payment = Payment(PaymentType.FOOD, 0, '')

    def __str__(self):
        food_payment_str = f"\n\t\t\t{self.food_payment}" if self.food_payment.amount > 0 else ''
        return f"{self.name}\n\t\t\t{self.game_payment}{food_payment_str}"


class Payment(object):
    def __init__(self, payment_type: str, amount: float, owes_to: str):
        self.payment_type = payment_type
        self.amount = amount
        self.owes_to = owes_to

    def __str__(self):
        return f"{self.payment_type}: {self.amount} -> {self.owes_to}"


class PaymentType(object):
    GAME = 'GAME'
    FOOD = 'FOOD'
