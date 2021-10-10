from Transaction import Transaction
from Account import *
import datetime as dt
import csv
from pathlib import Path
from database_api import *
from tagger import tag

class Importer:
    def __init__(self,file):
        self.new_transacts = self.import_transactions(file)

    def CSV2Object(self,file,account):
        start_found = False
        transacts = []
        with open(file,mode="r",encoding="latin-1") as csv_file:
            if account == PP:
                csv_reader=csv.reader(csv_file,delimiter=",")
            else:
                csv_reader = csv.reader(csv_file, delimiter=";")
            transacts = []
            for index,row in enumerate(csv_reader):
                if len(row)>0:
                    if row[0][0] >= '0' and row[0][0] <= '9':
                        start_index = index-1
                        start_found = True
                    if start_found:
                        if account == CC_LUX:
                            if row[1] != "DECOMPTE VISA":
                                comma_pos = row[4].rfind(",")
                                recipient = row[4][:comma_pos].replace(",", "")
                                reference = row[4][comma_pos + 2:].replace(",", "")
                                transacts.append(Transaction(datetime.strptime(row[0],"%d/%m/%Y"),row[1],recipient,reference,float(row[2].replace(',', '.')),row[3],'',account))
                        elif account == GK_DE and not (row[3] == "" and row[8] == ""):
                            amount_str = ('-') * (row[12] == 'S') + row[11].replace(',', '.')
                            amount = float(amount_str)
                            transacts.append(Transaction(datetime.strptime(row[0], '%d.%m.%Y'), row[2], row[3],
                                                   row[8].replace("\n", " "), amount, row[10], '',account))
                        elif account == PP:
                            if row[3] != "Bank Deposit to PP Account" and row[3] != "Reversal of General Account Hold" and row[3] != "Account Hold for Open Authorization" and row[4] == "EUR":
                                if row[9] != "":
                                    amount = float(row[7])
                                else:
                                    amount = float(row[5])
                                date = datetime.strptime(row[0], "%m/%d/%Y")
                                transacts.append(Transaction(date, row[3], row[11], '', amount, row[4], '', account))
                        elif account == VISA:
                            recipient = row[6].replace(",", "")
                            reference = ''
                            amount = float(row[8].replace(",", "."))
                            date = datetime.strptime(row[5], "%d/%m/%Y")
                            self.settlement_date = datetime.strptime(row[2], "%d/%m/%Y")
                            transacts.append(Transaction(date, 'Credit Card Transaction', recipient, reference, amount, row[4], '', account))
        if account != PP:
            transacts.reverse()
        return transacts

    def import_transactions(self,file):
        if file.find("Export_Mouvements") >= 0:
            account = CC_LUX
        elif file.find("Umsaetze") >= 0:
            account = GK_DE
        elif file.find("MSR") >= 0:
            account = PP
        elif file.find("Export_Card") >= 0:
            account = VISA
        else:
            account = None
        self.account = account
        transacts = self.CSV2Object(file,account)

        return transacts

    def display_transacts(self):
        for action in self.new_transacts:
            print(action.__dict__)

    def getLastAccountEntry(self,transacts,account):
        for i,action in reversed(list(enumerate(transacts))):
            if action.account == account:
                last_element = action
                last_index = i
                break
        return last_element, last_index


    def joiner(self):
        old_transacts = list(getAllTransacts())
        lastAccountEntry = self.getLastAccountEntry(old_transacts,self.account)
        first_new_index = 0
        new_transacts = []
        if lastAccountEntry[0].date > self.new_transacts[-1].date:
            print("all transactions already imported")
            return 0
        else:
            for index, action in enumerate(self.new_transacts):
                if __eq__(action, lastAccountEntry[0], 'date', 'amount', 'account'):
                    first_new_index = index + 1
                    break
            new_transacts = list(self.new_transacts[first_new_index:])
        new_transacts = tag(new_transacts)
        joined_transacts = old_transacts
        for action in new_transacts:
            joined_transacts.append(action)
        final_transacts = []
        if self.account == PP:
            for action in joined_transacts:
                if not (action.tag == "PayPal" and action.date <= self.new_transacts[-1].date + dt.timedelta(days=1)):
                    final_transacts.append(action)
        elif self.account == VISA:
            for action in joined_transacts:
                if not (action.tag == "Visa" and action.date <= self.settlement_date):
                    final_transacts.append(action)
        else:
            final_transacts = joined_transacts

        final_transacts.sort(key=lambda x: x.date)
        self.updated_transacts = final_transacts
        deleteAllFromTable("transacts")
        writeTransacts2DB(final_transacts)


def __eq__(this,other, *attributes):

    if attributes:
        d = float('NaN')  # default that won't compare equal, even with itself
        return all(this.__dict__.get(a, d) == other.__dict__.get(a, d) for a in attributes)

    return this.__dict__ == other.__dict__

def displayTransacts(transacts):
    for action in transacts:
        print(action.__dict__)

def importNewFile(file):
    importer = Importer(file)
    importer.joiner()

if __name__ == '__main__':
    main()