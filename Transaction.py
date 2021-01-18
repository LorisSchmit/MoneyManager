class Transaction:
    def __init__(self, date, type, recipient, reference, amount, currency, tag, account):
        self.date = date
        self.type = type
        self.reference = reference
        self.recipient = recipient
        self.amount = amount
        self.currency = currency
        self.tag = tag
        self.account = account
