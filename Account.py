import csv
import os
import json

class Account:
    def __init__(self,name):
        self.balances_lookup = {'Compte courant': 0, 'Girokonto': 1, 'Compte epargne': 2,
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
CE_LUX = Account('Compte epargne')

def accountsLookup(account_name):
    accounts_lookup = {'Compte courant': CC_LUX, 'Girokonto': GK_DE, 'PayPal': PP, 'Geldbeutel': GB, 'Visa': VISA, 'Compte epargne': CE_LUX}
    try:
        account = accounts_lookup[account_name]
    except KeyError:
        account = None
    return account


def statementDetection(file):
    transacts = []
    with open(file,mode="r",encoding="latin-1") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        for index, row in enumerate(csv_reader):
            if len(row) > 0:
                if row[0][0] >= '0' and row[0][0] <= '9':
                    transacts.append(row)
    print(transacts)
    return transacts


def importAllAccounts(file):
    if os.path.isfile(file):
        if os.stat(file).st_size > 0:
            with open(file, "r", encoding="latin-1") as json_file:
                data = json.load(json_file)
        else:
            data = {}
    else:
        data = {}
    return data

def deleteAccount(index,data,file):
    data["accounts"].pop(index)
    with open(file, "w+", encoding="latin-1") as json_file:
        json_string = json.dumps(data)
        json_file.write(json_string)
