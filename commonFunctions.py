import csv
from Transaction import Transaction
import datetime
import os

from Account import CC_LUX,GK_DE,PP,VISA,GB

def listdir_nohidden(path):
    files = []
    for f in os.listdir(path):
        if not f.startswith('.'):
            try:
                files.append(int(f[:-4]))
            except ValueError:
                pass
    return files

def defineFiles(start_year,suffix):
    files = []
    for i in range(1,13):
        if i>=10:
            #if str(i)+".csv" in os.listdir(str(start_year)):
            files.append(str(start_year)+"/"+str(i)+suffix)
        else:
            #if str(i) + ".csv" in os.listdir(str(start_year+1)):
            files.append(str(start_year+1)+"/"+str(i)+suffix)
    files.sort()
    return files

def checkIfInYear(date,year):
    if (date.year == year and date.month > 9) or (date.year == year+1 and date.month <= 9):
        return True
    else:
        return False

def displayTransacts(transacts):
    for action in transacts:
        print(object2list(action))

def object2list(action):
    l = [action.date.strftime("%d/%m/%Y"), action.type, action.recipient, action.reference, str(action.amount), action.currency, action.tag,action.account.name]
    return l

def list2object(row):
    o = Transaction(datetime.datetime.strptime(row[0],"%d/%m/%Y"),row[1],row[2],row[3],float(row[4]),row[5],row[6],accountName2account(row[7]))
    return o

def accountName2account(name):
    accounts = {'Compte courant' : CC_LUX,'Girokonto' : GK_DE, 'PayPal':PP, 'Visa': VISA, 'Geldbeutel': GB}
    return accounts[name]

def getExpensesData(year):
    files = defineFiles(year, "")
    expenses_data = []
    for file in files:
        expenses_data.extend(readCSVtoObjectExpense(file))
    return expenses_data

def getTotalExpenses(year):
    expenses_data = getExpensesData(year)
    tot = total(expenses_data)
    return tot

def biggestTag(tags):
    max_key = next(iter(tags))
    max = tags[max_key]
    for tag in tags:
        if tags[tag] > max:
            max_key = tag
            max = tags[tag]
    return (max_key,max)

def total(transacts):
    tot = 0
    for action in transacts:
        if action.tag != "Einkommen" and action.amount < 0:
            tot += action.amount
    return round(tot,2)

def readCSVtoList(file):
    with open(file,mode="r") as csv_file:
        csv_reader=csv.reader(csv_file,delimiter=";")
        transacts = []
        for row in csv_reader:
            transacts.append(row)
    return transacts

def readCSVtoObject(file):
    file_name = file+ ".csv"
    transacts = []
    with open(file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        for row in csv_reader:
            date = datetime.datetime.strptime(row[0], "%d/%m/%Y")
            transacts.append(Transaction(date,row[1],row[2],row[3],float(row[4]),row[5],row[6],accountName2account(row[7])))
    return transacts


def readCSVtoObjectExpense(file):
    file_name = file+ ".csv"
    transacts = []
    with open(file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        for row in csv_reader:
            if row[6] != "Einkommen":
                date = datetime.datetime.strptime(row[0], "%d/%m/%Y")
                transacts.append(Transaction(date, row[1], row[2], row[3], float(row[4]), row[5], row[6], accountName2account(row[7])))
    return transacts

def importByFiles(files):
    transacts = []
    for file in files:
        with open(file, mode="r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            for row in csv_reader:
                transacts.append(Transaction(row[0], row[1], row[2], row[3], float(row[4]), row[5], row[6], accountName2account(row[7])))
    return transacts

def perWeek(transacts):
    weeks = {}
    date = transacts[0].date
    week_number0 = date.isocalendar()[1]
    tot = 0
    for action in transacts:
        date = action.date
        week_number = date.isocalendar()[1]
        if week_number == week_number0:
            tot += action.amount
        else:
            week_dates = weekNumberToDates(date.year,week_number0)
            weeks[week_dates] = str(-round(tot,2))
            tot = action.amount
        week_number0 = week_number
    week_dates = weekNumberToDates(date.year, week_number0)
    weeks[week_dates] = str(-round(tot,2))
    return weeks

def weekNumberToDates(year,week_number):
    if year == 2018:
        week = week_number
    else:
        week = week_number-1
    start_str = str(year)+"-W"+str(week)
    start = datetime.datetime.strptime(start_str + '-1', "%Y-W%W-%w")
    end_str = str(year) + "-W" + str(week+1)
    end = datetime.datetime.strptime(end_str + '-1', "%Y-W%W-%w")-datetime.timedelta(days=1)
    return (start,end)


def monthNumberToMonthName(month_number):
    months = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
    return months[month_number]

def perTag(transacts):
    tags_temp = {}
    tags = {}
    truth_table = []
    tot = 0
    tag = ""
    for el in transacts:
        truth_table.append(True)
    for i in range(0,len(transacts)):
        if truth_table[i]:
            tot = transacts[i].amount
            tag = transacts[i].tag
            for j in range(i+1,len(transacts)):
                if transacts[i].tag == transacts[j].tag and truth_table[j]:
                    tot += transacts[j].amount
                    truth_table[j] = False
            tot = -round(tot, 2)
            tags_temp[tag] = tot

    rest = 0
    for tag in tags_temp:
        if tags_temp[tag] >= 20:
            tags[tag] = tags_temp[tag]
        elif tag == "Rückzahlung":
            tags[tag] = tags_temp[tag]
        elif tags_temp[tag] > 0:
            rest += float(tags_temp[tag])
    rest = round(rest, 2)
    tags['Rest'] = rest
    return tags

def main():
    date = datetime.datetime.strptime("08/08/2020","%d/%m/%Y")
    print(checkIfInYear(date,2019))
if __name__ == '__main__':
    main()