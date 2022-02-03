import csv
import os
import json
from pathlib import Path


mm_dir_path = Path(__file__).parent

class Account:
    def __init__(self,name,balance,rowsDeleted,colsDeleted,headers,detectString="",dmy_format=True,signs=None):
        self.name  = name
        self.balance = balance
        self.rowsDeleted = rowsDeleted
        self.colsDeleted = colsDeleted
        self.headers = headers
        self.detectString = detectString
        self.dmy_format = dmy_format
        self.signs = signs
        #self.balance = self.getBalance(name)[0]
        #self.date = self.getBalance(name)[1]


    def transfer(self,amount, account):
        self.balance -= amount
        account.balance += amount


    def getDate(self):
        return self.date


def accountsLookup(account_name):
    for acc in accounts:
        if acc.name == account_name:
            account = acc
            return account
    return None


def statementDetection(file):
    transacts = []
    with open(file,mode="r",encoding="latin-1") as csv_file:
        delimiterFound = False
        while not delimiterFound:
            try:
                dialect = csv.Sniffer().sniff(csv_file.readline(), delimiters=";,")
                delimiterFound = True
            except:
                pass
        csv_file.seek(0)
        csv_reader = csv.reader(csv_file, dialect)
        for index, row in enumerate(csv_reader):
            if len(row) > 0:
                transacts.append(row)
    return transacts


def importAllAccounts(file):
    accounts = []
    if os.path.isfile(file):
        if os.stat(file).st_size > 0:
            with open(file, "r", encoding="latin-1") as json_file:
                account_data = json.load(json_file)

            if "accounts" in account_data:
                for acc in account_data["accounts"]:
                    signs = (acc["signs"] if "signs" in acc else None)
                    accounts.append(Account(acc["name"], acc["balance"],acc["rowsDeleted"], acc["colsDeleted"], acc["headers"],acc["detectString"],acc["dmy_format"],signs=signs))

    return accounts

def exportAllAccounts(accounts,file):
    data = {}
    if len(accounts)>0:
        data = {"accounts":[]}
        for acc in accounts:
            new_account = {'name': acc.name,
             'balance': acc.balance,
             'rowsDeleted': acc.rowsDeleted,
             'colsDeleted': acc.colsDeleted,
             'headers': acc.headers,
             'detectString': acc.detectString,
             'dmy_format': acc.dmy_format}
            if acc.signs is not None:
                new_account['signs'] = acc.signs
            data['accounts'].append(new_account)

        with open(file, "w+", encoding="latin-1") as json_file:
            json_string = json.dumps(data)
            json_file.write(json_string)
    return data

def deleteAccount(index,file):
    accounts.pop(index)
    exportAllAccounts(accounts,file)


accounts_file = mm_dir_path / "accounts.json"
accounts = importAllAccounts(accounts_file)
