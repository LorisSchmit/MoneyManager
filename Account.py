class Account:
    def __init__(self,name):
        self.balances_lookup = {'Compte courant': 0, 'Girokonto': 1, 'Compte épargne': 2,
                                'PayPal': 3, 'Geldbeutel': 4, 'Visa': 5}
        self.name  = name
        #self.balance = self.getBalance(name)[0]
        #self.date = self.getBalance(name)[1]


    def transfer(self,amount, account):
        self.balance -= amount
        account.balance += amount

    def update(self):
        self.date = datetime.now()
        index = self.balances_lookup[self.name]
        balances[index][0] = round(self.balance,2)
        balances[index][1] = self.date
        saveBalances()

    def getDate(self):
        return self.date


CC_LUX = Account('Compte courant')
GK_DE = Account('Girokonto')
PP = Account('PayPal')
GB = Account('Geldbeutel')
VISA = Account('Visa')

def accountsLookup(account_name):
    accounts_lookup = {'Compte courant': CC_LUX, 'Girokonto': GK_DE, 'PayPal': PP, 'Geldbeutel': GB, 'Visa': VISA}
    try:
        account = accounts_lookup[account_name]
    except KeyError:
        account = None
    return account