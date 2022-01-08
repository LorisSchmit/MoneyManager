import csv
import os
import datetime
from PyPDF2 import PdfFileReader
import ast


from database_api import *
from Account import CC_LUX
from Month import Month
from commonFunctions import object2list
from importer import importNewFile


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
    for action in transacts:
        print(object2list(action))
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





def removeNewLine():
    #all_transacts = getAllTransacts()
    known_tags = importTable("tags", tags=True)
    known_tags_new = {}
    for ref,tag in known_tags.items():
        known_tags_new[ref.rstrip()] = tag.rstrip()
        #known_tags.pop(ref)
    print(known_tags_new)
    #deleteAllFromTable("tags")
    writeTags(known_tags_new)




def main():
    #for i in range(1,8):
     #assignPayback(,2021)
    #cleaner()
    file = "/Users/lorisschmit1/Movements/Export_Card_Mouvements.csv"
    importNewFile(file)

if __name__ == '__main__':
    main()


