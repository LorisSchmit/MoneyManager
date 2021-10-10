from datetime import datetime
from database_api import *
import plotly.graph_objects as go
from commonFunctions import weekNumberToDates
from createBalanceSheets import drawPDF
import threading

class Month:
    def __init__(self,month,year):
        self.month = month
        self.month_name = self.monthNumberToMonthName()
        self.year = year
        self.start_year = year
        if month<=9:
            self.start_year -= 1
        all_transacts = getAllTransacts()
        self.transacts = self.getMonthlyTransacts(all_transacts)
        self.lean_transacts = self.getLeanTransacts()
        if len(self.transacts)>0:
            self.tags = self.perTag()
            self.total = self.getTotalSpent()
            self.budget = 1000
            self.max = self.biggestTag()[1]
            self.weeks = self.perWeek()

    def getMonthlyTransacts(self,transacts):
        start = datetime(self.year, self.month, 1)
        if self.month < 12:
            end = datetime(self.year, self.month + 1, 1)
        else:
            end = datetime(self.year + 1, 1, 1)
        monthly_transacts = []
        for action in transacts:
            if action.date >= start and action.date < end:
                monthly_transacts.append(action)
        return monthly_transacts

    def getIncome(self):
        total = 0
        for action in self.transacts:
            if action.amount > 0 and action.tag != "Kapitaltransfer":
                total += action.amount
        return total

    def getTotalSpent(self):
        tot = 0
        for action in self.transacts:
            if action.tag != "Einkommen" and action.amount < 0 and action.tag != "Kapitaltransfer":
                tot += action.amount
        return round(tot, 2)

    def getLeanTransacts(self):
        lean_transacts = []
        for action in self.transacts:
            if action.tag != "Einkommen" and action.tag != "Kapitaltransfer":
                lean_transacts.append(action)
        return lean_transacts

    def monthNumberToMonthName(self):
        months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober',
                  'November', 'Dezember']
        return months[self.month-1]

    def perTag(self):
        tags_temp = {}
        tags = {}
        truth_table = []
        #for act in self.transacts:
           # print(act.tag)
        for el in self.lean_transacts:
            truth_table.append(True)
        for i in range(0, len(self.lean_transacts)):
            if truth_table[i]:
                tot = self.lean_transacts[i].amount
                tag = self.lean_transacts[i].tag
                for j in range(i + 1, len(self.lean_transacts)):
                    if self.lean_transacts[i].tag == self.lean_transacts[j].tag and truth_table[j]:
                        tot += self.lean_transacts[j].amount
                        truth_table[j] = False
                tot = -round(tot, 2)
                tags_temp[tag.rstrip()] = tot
        rest = 0
        for tag in tags_temp:
            if tags_temp[tag] >= 20:
                tags[tag.rstrip()] = tags_temp[tag]
            elif tag.find("Rückzahlung") != -1:
                tags[tag.rstrip()] = tags_temp[tag]
            elif tags_temp[tag] > 0:
                rest += float(tags_temp[tag.rstrip()])
        rest = round(rest, 2)
        tags['Rest'] = rest
        return tags

    def biggestTag(self):
        max_key = next(iter(self.tags))
        max = self.tags[max_key]
        for tag in self.tags:
            if self.tags[tag] > max:
                max_key = tag
                max = self.tags[tag]
        return (max_key, max)

    def perWeek(self):
        weeks = {}
        date = self.lean_transacts[0].date
        week_number0 = date.isocalendar()[1]
        tot = 0
        for action in self.lean_transacts:
            date = action.date
            week_number = date.isocalendar()[1]
            if week_number == week_number0:
                tot += action.amount
            else:
                week_dates = weekNumberToDates(date.year, week_number0)
                weeks[week_dates] = str(-round(tot, 2))
                tot = action.amount
            week_number0 = week_number
        week_dates = weekNumberToDates(date.year, week_number0)
        weeks[week_dates] = str(-round(tot, 2))
        return weeks

    def createGraph(self):
        if len(self.transacts) > 0:
            font_size = 19
            labels = list(self.tags.keys())
            values = list(self.tags.values())
            rot_fact = (3 / 8 - self.max / self.total) * 8 * 55
            if rot_fact < 0:
                rot_fact = 0
            if rot_fact > 360:
                rot_fact -= 360
            layout = dict(showlegend=False, font=dict(size=font_size), margin=dict(l=0, r=0, t=0, b=0))
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)], layout=layout)
            fig.update_traces(textinfo='label', hoverinfo='percent+value', rotation=rot_fact, )
            # fig.show()
            fig.write_image("Graphs/" + str(self.year) + " - " + str(self.month) + ".svg")

    def createBalanceSheet(self):
        if len(self.transacts) > 0:
            drawPDF(self)

def monthsPerYear(year):
    for i in range(1, 13):
        month = Month(i, year)
        #month.createGraph()
        month.createBalanceSheet()
    return "All Balances for "+str(year)+" created"

def createSingleMonth(month,year):
    month = Month(month, year)
    month.createGraph()
    month.createBalanceSheet()

def executeCreateSingleMonth(month,year):
    print("Balance Sheet Creation started")
    main_thread = threading.Thread(target=createSingleMonth,args=(month,year,))
    main_thread.start()


if __name__ == '__main__':
    #monthsPerYear(2020)
    createSingleMonth(9, 2021)
