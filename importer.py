from Transaction import Transaction
from Account import *
from datetime import datetime
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
                            if row[3] != "Bank Deposit to PP Account" and row[3] != "Reversal of General Account Hold" and row[3] != "Account Hold for Open Authorization":
                                if row[9] != "":
                                    amount = float(row[7])
                                else:
                                    amount = float(row[5])
                                date = datetime.strptime(row[0], "%m/%d/%Y")
                                transacts.append(Transaction(date, row[3], row[11], '', amount, row[4], '', account))
                        elif account == VISA:
                            recipient = row[1].replace(",", "")
                            reference = ''
                            amount = float(row[3].replace(",", "."))
                            date = datetime.strptime(row[0], "%d/%m/%Y")
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
        joined_transacts.sort(key=lambda x: x.date)
        self.updated_transacts = joined_transacts
        deleteAllFromTable("transacts")
        writeTransacts2DB(joined_transacts)


def __eq__(this,other, *attributes):

    if attributes:
        d = float('NaN')  # default that won't compare equal, even with itself
        return all(this.__dict__.get(a, d) == other.__dict__.get(a, d) for a in attributes)

    return this.__dict__ == other.__dict__

def displayTransacts(transacts):
    for action in transacts:
        print(action.__dict__)

def main():
    home = str(Path.home())
    file = home+"/Movements/Umsaetze_DE22660908000007898649_2021.01.26.csv"
    file2 = home+"/Movements/Export_Mouvements_Current acc. Green Code 18-30 Study copy.csv"
    file3 = home+"/Movements/MSR-202012.CSV"
    importer = Importer(file)
    importer.joiner()

if __name__ == '__main__':
    main()