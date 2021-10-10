class Transaction:
    def __init__(self,id, date, type, recipient, reference, amount, currency, tag, account, pb_assign):
        self.id = id
        self.date = date
        self.type = type
        self.reference = reference
        self.recipient = recipient
        self.amount = amount
        self.currency = currency
        self.tag = tag
        self.account = account
        self.pb_assign = pb_assign

