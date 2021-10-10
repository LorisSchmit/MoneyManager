from Month import Month
from database_api import *
import plotly.graph_objects as go
from createYearlySheet import *

income_tags = importKnownTags("income_tags")

class Year:
    def __init__(self,year_no):
        self.year_no = year_no
        self.months = self.getMonths()
        all_transacts = getAllTransacts()
        self.transacts = self.getYearlyTransacts(all_transacts)
        self.income_transacts = self.getIncomeTransacts()
        self.lean_transacts = self.getLeanTransacts()
        self.total_spent = self.getTotalSpent()
        self.total_budget = self.getBudget()
        tags = self.perTag()
        self.tags = tags[0]
        self.tags_shortened = tags[1]
        self.max = self.biggestTag(self.tags)[1]
        self.budget_tagged = self.analyzeBudget()
        self.payback = self.getPayback()

    def getMonths(self):
        months = []
        for month_no in range(1,13):
            month = Month(month_no, self.year_no)
            months.append(month)
        return months

    def getTotalSpent(self):
        total = 0
        for month in self.months:
            total += month.getTotalSpent()
        return -round(total,2)

    def getBudget(self):
        total = 0
        for month in self.months:
            total += month.getIncome()
        additional_income = 0
        total += additional_income
        return round(total,2)

    def getPayback(self):
        total = 0
        for action in self.transacts:
            if action.tag == "Rückzahlung":
                total += action.amount
        return round(total,2)

    def getYearlyTransacts(self,transacts):
        start = datetime(self.year_no, 1, 1)
        end = datetime(self.year_no+1, 1, 1)
        yearly_transacts = []
        for action in transacts:
            if action.date >= start and action.date < end:
                yearly_transacts.append(action)
        return yearly_transacts

    def getLeanTransacts(self):
        lean_transacts = []
        for action in self.transacts:
            if action.tag != "Einkommen" and action.tag != "Kapitaltransfer":
                lean_transacts.append(action)
        return lean_transacts

    def getIncomeTransacts(self):
        income_transacts = []
        for action in self.transacts:
            if action.tag == "Einkommen":
                income_transacts.append(action)
        return income_transacts

    def perTag(self):
        tags_temp = {}
        tags = {}
        tags_shortened = {}
        truth_table = []
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
                tags_temp[tag] = tot
        rest = 0
        rest_shortened = 0
        for tag in tags_temp:
            if tags_temp[tag] >= 20:
                tags[tag] = tags_temp[tag]
            elif tag == "Rückzahlung":
                tags[tag] = tags_temp[tag]
            elif tags_temp[tag] > 0:
                rest += float(tags_temp[tag])

            if tags_temp[tag] >= 200:
                tags_shortened[tag] = tags_temp[tag]
            elif tag == "Rückzahlung":
                tags_shortened[tag] = tags_temp[tag]
            elif tags_temp[tag] > 0:
                rest_shortened += float(tags_temp[tag])
        rest = round(rest, 2)
        tags['Rest'] = rest
        tags_shortened['Rest'] = rest_shortened
        return tags,tags_shortened

    def biggestTag(self,tags):
        max_key = next(iter(tags))
        max = tags[max_key]
        for tag in tags:
            if tags[tag] > max:
                max_key = tag
                max = tags[tag]
        return (max_key, max)


    def analyzeBudget(self):
        data = {}
        for cat in income_tags.values():
            data[cat] = 0
        data["Rest"] = 0
        for action in self.income_transacts:
            for ref in income_tags:
                tag_found = False
                if action.recipient.lower().find(ref.lower()) != -1:
                    tag = income_tags[ref]
                    tag_found = True
                    break
            if not tag_found:
                tag = "Rest"
            data[tag] += action.amount
        data_copy = {}
        for key in data.keys():
            if data[key] != 0:
                data_copy[key] = data[key]
        return data_copy

    def createBudgetGraph(self):
        labels = list(self.budget_tagged.keys())
        values = list(self.budget_tagged.values())
        rot_fact = (3 / 8 - self.biggestTag(self.budget_tagged)[1]/self.total_budget) * 8 * 55
        if rot_fact < 0:
            rot_fact = 0
        if rot_fact > 360:
            rot_fact = -360
        layout = dict(showlegend=False, font=dict(size=19), margin=dict(l=0, r=0, t=0, b=0))
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)], layout=layout)
        fig.update_traces(textinfo='label', hoverinfo='percent+value', rotation=rot_fact, )
        # fig.show()
        fig.write_image("Graphs/Budget" + str(self.year_no) + ".svg")

    def createExpensesGraph(self):
        labels = list(self.tags_shortened.keys())
        values = list(self.tags_shortened.values())
        rot_fact = -30#(3 / 8 - self.max/self.total_spent) * 8 * 55
        #if rot_fact < 0:
        #    rot_fact = 0
        #if rot_fact > 360:
        #    rot_fact = -360
        layout = dict(showlegend=False, font=dict(size=19), margin=dict(l=0, r=0, t=0, b=0,pad=0))
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)], layout=layout)
        fig.update_traces(textinfo='label', hoverinfo='percent+value', rotation=rot_fact, )
        #fig.show()
        fig.write_image("Graphs/Expenses" + str(self.year_no) + ".svg")

def createYearlySheet(year):
    #year.createBudgetGraph()
    year.createExpensesGraph()
    createPDF(year)

if __name__ == '__main__':
    year = Year(2020)
    createYearlySheet(year)
