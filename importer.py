from Transaction import Transaction
from Account import *
import datetime as dt
import csv
from pathlib import Path
from database_api import *
from tagger import tag
from copy import copy

class Importer:
    def __init__(self,file):
        self.old_transacts = getAllTransacts()
        self.new_transacts = self.import_transactions(file)

    def CSV2Object(self,file,account):
        start_found = False
        transacts = OrderedDict()
        with open(file,mode="r",encoding="latin-1") as csv_file:
            if account == PP:
                csv_reader = csv.reader(csv_file,delimiter=",")
            else:
                csv_reader = reversed(list(csv.reader(csv_file, delimiter=";")))

            #start_index = self.getLastEntry(self.old_transacts)[1]
            start_index = -1
            counter = 0
            for index,row in enumerate(csv_reader):
                if len(row)>0:
                    if row[0][0] >= '0' and row[0][0] <= '9':
                        if account == CC_LUX or account == CE_LUX:
                            if row[1] != "DECOMPTE VISA":
                                comma_pos = row[4].rfind(",")
                                recipient = row[4][:comma_pos].replace(",", "")
                                reference = row[4][comma_pos + 2:].replace(",", "")
                                counter += 1
                                id = start_index + counter
                                transacts[id] = Transaction(id,datetime.strptime(row[0],"%d/%m/%Y"),row[1],recipient,reference,float(row[2].replace(',', '.')),row[3],'',account,[])
                        elif account == GK_DE and not (row[3] == "" and row[8] == ""):
                            amount_str = ('-') * (row[12] == 'S') + row[11].replace(',', '.')
                            amount = float(amount_str)
                            counter += 1
                            id = start_index + counter
                            transacts[id] = Transaction(id,datetime.strptime(row[0], '%d.%m.%Y'), row[2], row[3],
                                                   row[8].replace("\n", " "), amount, row[10], '',account,[])
                        elif account == PP:
                            if row[3] != "Bank Deposit to PP Account" and row[3] != "Reversal of General Account Hold" and row[3] != "Account Hold for Open Authorization" and row[4] == "EUR":
                                if row[9] != "":
                                    amount = float(row[7])
                                else:
                                    amount = float(row[5])
                                date = datetime.strptime(row[0], "%m/%d/%Y")
                                counter += 1
                                id = start_index + counter
                                transacts[id] = Transaction(id,date, row[3], row[11], '', amount, row[4], '', account,[])
                        elif account == VISA:
                            recipient = row[6].replace(",", "")
                            reference = ''
                            amount = float(row[8].replace(",", "."))
                            date = datetime.strptime(row[5], "%d/%m/%Y")
                            self.settlement_date = datetime.strptime(row[2], "%d/%m/%Y")
                            counter += 1
                            id = start_index + counter
                            transacts[id] = Transaction(id,date, 'Credit Card Transaction', recipient, reference, amount, row[4], '', account,[])

        #transacts = OrderedDict(reversed(list(transacts.items())))
        return transacts

    def import_transactions(self,file):
        if file.find("Export_Mouvements_Current") >= 0:
            account = CC_LUX
        elif file.find("Export_Mouvements_Savings") >= 0:
            account = CE_LUX
        elif file.find("Umsaetze") >= 0:
            account = GK_DE
        elif file.find("MSR") >= 0 or file.find("WLEC") >= 0:
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

    def getLastEntry(self,transacts,account=None):
        for id,action in reversed(transacts.items()):
            if account is None or action.account == account:
                last_element = action
                last_index = id
                break
        return last_element, last_index


    def joiner(self):
        lastAccountEntry = self.getLastEntry(self.old_transacts,account=self.account)
        first_new_index = 0
        new_transacts = OrderedDict()
        print(list(self.new_transacts.items())[-1])
        if lastAccountEntry[0].date > list(self.new_transacts.items())[-1][1].date:
            print("all transactions already imported")
            return 0
        else:
            for index,action in self.new_transacts.items():
                if __eq__(action, lastAccountEntry[0], 'date', 'amount', 'account'):
                    first_new_index = index + 1
                    break
            new_transacts = OrderedDict(list(self.new_transacts.items())[first_new_index:])
        lastEntryIndex = self.getLastEntry(self.old_transacts)[1]
        new_transacts_reindexed = OrderedDict()
        for counter,(id,action) in enumerate(new_transacts.items()):
            new_id = lastEntryIndex+1+counter
            new_action = copy(action)
            new_action.id = new_id
            new_transacts_reindexed[new_id] = new_action
        new_transacts = new_transacts_reindexed
        new_transacts = tag(new_transacts)
        joined_transacts = self.old_transacts
        for id,action in new_transacts.items():
            joined_transacts[id] = action
        final_transacts = OrderedDict()
        if self.account == PP:
            for id,action in joined_transacts.items():
                if not (action.tag == "PayPal" and action.date <= list(self.new_transacts.items())[1][-1].date + dt.timedelta(days=1)):
                    final_transacts[id] = action
        elif self.account == VISA:
            for id,action in joined_transacts.items():
                if not (action.tag == "Visa" and action.date <= self.settlement_date):
                    final_transacts[id] = action
        else:
            final_transacts = joined_transacts

        final_transacts = OrderedDict(sorted(final_transacts.items(),key=lambda x: x[1].date))
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
    file = "/Users/lorisschmit1/Movements/WLEC3J2ALW5XJ-CSR-20211201000000-20211231235959-20220101074559.CSV"
    importNewFile(file)