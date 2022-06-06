from Transaction import Transaction
from Account import *
import datetime as dt
import csv
from pathlib import Path
from database_api import *
from tagger import tag
from copy import copy
import numpy as np
import dateutil
import re

mm_dir_path = Path(__file__).parent
#sys.path.append(mm_dir_path)

class Importer:
    def __init__(self,file,account):
        self.old_transacts = getAllTransacts()
        self.new_transacts = transacts = self.CSV2Object(file,account)
        self.account = account

    def CSV2Object(self,file,account):
        start_found = False
        transacts = OrderedDict()
        transacts_list = []
        transacts_temp = []
        with open(file, mode="r", encoding="latin-1") as csv_file:
            delimiterFound = False
            while not delimiterFound:
                try:
                    dialect = csv.Sniffer().sniff(csv_file.readline(), delimiters=";,")
                    delimiterFound = True
                except:
                    pass
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file, dialect)
            max_col_num = 0
            for index,row in enumerate(csv_reader):
                if len(row)>0:
                    #if row[0][0] >= '0' and row[0][0] <= '9':
                    transacts_list.append(row)
                    if len(row)>max_col_num:
                        max_col_num = len(row)
            for row in transacts_list:
                if len(row) < max_col_num:
                    row.extend(["" for _ in range(max_col_num-len(row))])

            transacts_list = np.array(transacts_list)
            for group in account.rowsDeleted:
                for deleteRow in list(reversed(sorted(group))):
                    transacts_list = np.delete(transacts_list,deleteRow,0)


            for group in account.colsDeleted:
                for deleteCol in list(reversed(sorted(group))):
                    transacts_list = np.delete(transacts_list,deleteCol,1)

            start_index = -1
            counter = 0

            for action in transacts_list:
                values = {}
                for index,header in enumerate(account.headers):
                    value = action[index]
                    if header == "Betrag":
                        value = value.strip()
                        separators = re.sub('[0-9]', '', value)
                        for sep in separators[:-1]:
                            if sep != "-":
                                value = value.replace(sep, '')
                        if separators:
                            value = value.replace(separators[-1], '.')
                        value = float(value.replace(",","."))
                    if header == "Referenz":
                        value = value.replace("\n"," ")
                    if header == "Datum":
                        value = dateutil.parser.parse(value,dayfirst=account.dmy_format)
                    values[header] = value
                counter += 1
                id = start_index + counter

                params = {"id":id,"account":account}
                if "Datum" in values:
                    params["date"] = values["Datum"]
                if "Typ" in values:
                    params["type"] = values["Typ"]
                if "Empfänger/Sender" in values:
                    params["recipient"] = values["Empfänger/Sender"]
                if account.name in ["Compte epargne","Compte courant"] and "Referenz" in values:
                    reference_ind = values["Referenz"].rfind(",")
                    params["recipient"] = values["Referenz"][:reference_ind]
                    params["reference"] = values["Referenz"][reference_ind+1:]
                elif "Referenz" in values:
                    params["reference"] = values["Referenz"]
                if "Betrag" in values:
                    sign = 1
                    if account.signs is not None:
                        if "Vorzeichen" in values:
                            if values["Vorzeichen"] == account.signs["-"]:
                                sign = -1
                    params["amount"] = sign*values["Betrag"]
                if "Währung" in values:
                    params["currency"] = values["Währung"]
                if "Währung" in values and "Typ" in values:
                    if values["Währung"].lower() == "eur" and values["Typ"] not in account.ignoreTypes:
                        transacts_temp.append(Transaction(**params))
                else:
                    transacts_temp.append(Transaction(**params))
        transacts_temp = sorted(transacts_temp, key=lambda action: action.date)
        start_index = -1
        counter = 0
        for action in transacts_temp:
            counter += 1
            id = start_index + counter
            transacts[id] = action
        return transacts


    def display_transacts(self):
        for action in self.new_transacts:
            print(action.__dict__)

    def getLastEntry(self,transacts,account=None):
        for id,action in reversed(transacts.items()):
            if account is None or action.account == account:
                last_element = action
                last_index = id
                return last_element, last_index
        return None

    def getLastIndex(self,transacts):
        return list(transacts.items())[-1][0]


    def joiner(self,gui=None):
        lastAccountEntry = self.getLastEntry(self.old_transacts,account=self.account)
        first_new_index = 0
        new_transacts = OrderedDict()
        if lastAccountEntry is not None and len(self.new_transacts.items())>0:
            if lastAccountEntry[0].date >= list(self.new_transacts.items())[-1][1].date:
                gui.importProgressLabel.setText("Alle Transaktionen bereits importiert")
                return 0
            else:
                for index,action in self.new_transacts.items():
                    if __eq__(action, lastAccountEntry[0], 'date', 'amount', 'account'):
                        first_new_index = index + 1
                        break
                new_transacts = OrderedDict(list(self.new_transacts.items())[first_new_index:])
        else:
            new_transacts = OrderedDict(list(self.new_transacts.items()))
        lastEntryIndex = (self.getLastIndex(self.old_transacts) if lastAccountEntry is not None else 0)
        new_transacts_reindexed = OrderedDict()
        for counter,(id,action) in enumerate(new_transacts.items()):
            new_id = lastEntryIndex+1+counter
            new_action = copy(action)
            new_action.id = new_id
            new_transacts_reindexed[new_id] = new_action
        new_transacts = new_transacts_reindexed
        new_transacts = tag(new_transacts,gui)
        joined_transacts = self.old_transacts
        for id,action in new_transacts.items():
            joined_transacts[id] = action
        final_transacts = OrderedDict()
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

def importNewFile(file,account,gui=None):
    importer = Importer(file,account)
    importer.joiner(gui)
