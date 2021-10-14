import csv
import os
import datetime
from PyPDF2 import PdfFileReader
import ast


from database_api import *
from Account import CC_LUX
from Month import Month
from commonFunctions import object2list


def migrate(year):
    root = "/Users/lorisschmit1/PycharmProjects/BudgetManager"
    folder = root+"/"+str(year)
    transacts = []
    for i in range(1,13):
        file = folder +"/"+str(i)+".csv"
        if os.path.isfile(file):
            with open(file, mode="r", encoding="latin-1") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=";")
                for index, row in enumerate(csv_reader):
                    time_str = row[0]
                    row[0] = str(int(datetime.datetime.strptime(time_str, "%d/%m/%Y").timestamp()))
                    transacts.append(row)

    return transacts


def write2db(transacts):
    conn = create_connection("db.db")
    with conn:
        writeMany(conn, transacts)


def fixer():
    transacts = getAllTransacts()
    for action in transacts:
        if action.tag.find("Elektro") != -1:
            action.tag = "Hardware"
    deleteAllFromTable("transacts")
    writeTransacts2DB(transacts)

def cleaner():
    transacts = getAllTransacts()
    transacts.sort(key=lambda x: x.date)
    deleteAllFromTable("transacts")
    writeTransacts2DB(transacts)

def extractText():
    pdf_document = "/Users/lorisschmit1/Desktop/7898649_2020_Nr.006_Kontoauszug_vom_30.06.2020_20210211092749.pdf"
    with open(pdf_document, "rb") as filehandle:
        pdf = PdfFileReader(filehandle)
        info = pdf.getDocumentInfo()
        pages = pdf.getNumPages()

        #print(info)
        #print("number of pages: %i" % pages)

        page1 = pdf.getPage(0)
        #print(page1)
        text_extract = page1.extractText()
        lines = text_extract.split('                                        ')

        lines = lines[1:]
        transacts = []
        for line in lines:
            line = line.split('             ')
            temp = []
            for el in line:
                if el != '':
                    temp.append(el[1:])
            transacts.append(temp)
        for action in transacts:
            print(action)


def assignPayback(month,year):
    all_transacts = getAllTransacts()
    month = Month(month, year)
    assigns = []
    for action in month.transacts:
        if action.tag == "Rückzahlung":
            print(object2list(action))
            pb = int(input("of which action?"))
            in_advance_action = all_transacts[pb-1]
            if in_advance_action.pb_assign is None:
                in_advance_action.pb_assign = []
            elif type(in_advance_action.pb_assign) is str:
                if len(in_advance_action.pb_assign) == 0:
                    in_advance_action.pb_assign = []
                else:
                    in_advance_action.pb_assign = ast.literal_eval(in_advance_action.pb_assign)

            if not (action.id in in_advance_action.pb_assign):
                in_advance_action.pb_assign.append(action.id)
                assigns.append(in_advance_action)

    for in_advance_action in assigns:
        in_advance_action.pb_assign = str(in_advance_action.pb_assign)
        print(object2list(in_advance_action))
    print(assigns)
    updateMany(assigns)


def removeNewLine():
    all_transacts = getAllTransacts()
    for action in all_transacts:
        action.tag = action.tag.rstrip()
    deleteAllFromTable("transacts")
    writeTransacts2DB(all_transacts)


def main():
    #for i in range(1,8):
    assignPayback(1,2020)

if __name__ == '__main__':
    main()


