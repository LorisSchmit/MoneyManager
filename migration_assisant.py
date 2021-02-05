import csv
import os
import datetime
from database_api import *
from Account import CC_LUX


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


def main():
    cleaner()

if __name__ == '__main__':
    main()