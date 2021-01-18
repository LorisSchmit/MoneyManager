from Transaction import Transaction
from Account import *
from datetime import datetime
import csv


def CSV2Object(file,account):
    start_found = False
    transacts = []
    with open(file,mode="r",encoding="latin-1") as csv_file:
        csv_reader=csv.reader(csv_file,delimiter=";")
        transacts = []
        for index,row in enumerate(csv_reader):
            if len(row)>0:
                if row[0][0] >= '0' and row[0][0] <= '9':
                    start_index = index-1
                    start_found = True
                if start_found:
                    if account == CC_LUX:
                        comma_pos = row[2].rfind(",")
                        recipient = row[2][:comma_pos].replace(",", "")
                        reference = row[2][comma_pos + 2:].replace(",", "")
                        transacts.append(Transaction(datetime.strptime(row[0],"%d/%m/%Y"),row[1],recipient,reference,row[3],row[4],'',account))
                    elif account == GK_DE:
                        amount_str = ('-') * (row[12] == 'S') + row[11].replace(',', '.')
                        amount = float(amount_str)
                        transacts.append(Transaction(datetime.strptime(row[0], '%d.%m.%Y'), row[2], row[3],
                                               row[8].replace("\n", " "), amount, row[10], '',account))
                    elif account == PP:
                        if row[3] != "Bank Deposit to PP Account":
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

    transacts.reverse()
    return transacts

def import_transactions(file):
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
    transacts = CSV2Object(file,account)

    return transacts