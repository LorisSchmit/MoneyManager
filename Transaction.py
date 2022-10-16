class Transaction:
    def __init__(self,id, date, type="", recipient="", reference="", amount=0, currency="", tag="",sub_tag="", account=None, pb_assign=[]):
        self.id = id
        self.date = date
        self.type = type
        self.reference = reference
        self.recipient = recipient
        self.amount = amount
        self.currency = currency
        self.tag = tag
        self.sub_tag = sub_tag
        self.account = account
        self.pb_assign = pb_assign

