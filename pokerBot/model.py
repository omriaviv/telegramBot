JACKPOT = "Jackpot"
GAME = 20
CHIPS = 1000


class Player(object):
    def __init__(self, name: str):
        self.name = name
        self.game_payment = Payment(PaymentType.GAME, GAME, JACKPOT)
        self.food_payment = Payment(PaymentType.FOOD, 0, '')
        self.win_payment = Payment(PaymentType.WIN, 0, '')

    def __str__(self):
        return f"{self.name}{self.game_payment}{self.food_payment}{self.win_payment}"


class Payment(object):
    def __init__(self, payment_type: str, amount: float, owes_to: str):
        self.payment_type = payment_type
        self.amount = amount
        self.owes_to = owes_to

    def __str__(self):
        owes_to_str = f" -> {self.owes_to}" if self.owes_to else ''
        return f"\n\t\t\t{self.payment_type}: " \
               f"{self.amount if self.payment_type == PaymentType.WIN else self.amount*-1}{owes_to_str}" \
            if self.amount > 0 else ''


class PaymentType(object):
    GAME = 'GAME'
    FOOD = 'FOOD'
    WIN = 'WIN'
