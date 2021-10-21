from Month import Month
from database_api import *
import plotly.graph_objects as go
from createYearlySheet import *

income_tags = importTable("income_tags",tags=True)

class Year:
    def __init__(self,year_no,projection=True):
        self.year_no = year_no
        self.months = self.getMonths()
        all_transacts = getAllTransacts()
        self.transacts = self.getYearlyTransacts(all_transacts)
        self.income_transacts = self.getIncomeTransacts()
        self.lean_transacts = self.getLeanTransacts()
        self.total_spent = self.getTotalSpent()
        if projection and self.year_no >= datetime.now().year:
            self.projections = importTable("budget_projection")
        self.budget = self.getBudget(projection=projection)
        self.budget_tagged = self.analyzeBudget(projection=projection)
        tags = self.perTag()
        self.tags = tags[0]
        self.tags_shortened = tags[1]
        self.max = self.biggestTag(self.tags)[1]
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

    def getBudget(self,projection=True):
        total = 0
        if projection and self.year_no >= datetime.now().year:
            for proj in self.projections:
                total += proj["amount"]
        else:
            total = 0
            for action in self.transacts:
                if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
                    print(object2list(action))
                    total += action.amount
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
            if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
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


    def analyzeBudget(self,projection=True):
        if projection and self.year_no >= datetime.now().year:
            data = {}
            for proj in self.projections:
                data[proj["tag"]] = 0
            for proj in self.projections:
                data[proj["tag"]] += proj["amount"]
        else:
            data_temp = {}
            for cat in income_tags.values():
                data_temp[cat] = 0
            data_temp["Rest"] = 0
            for action in self.income_transacts:
                for ref in income_tags:
                    tag_found = False
                    if action.recipient.lower().find(ref.lower()) != -1:
                        tag = income_tags[ref]
                        tag_found = True
                        break
                if not tag_found:
                    tag = "Rest"
                data_temp[tag] += action.amount
            data = {}
            for key in data_temp.keys():
                if data_temp[key] != 0:
                    data[key] = data_temp[key]
        return data



    def setProjections(self):
        projections = importTable("budget_projection")
        print(projections)
        exited = False
        print("Startup of budget projection...")
        while not exited:
            name = input("Income name?")
            if name == "none":
                exited = True
            else:
                amount = float(input("Amount?"))
                tag = input("Tag?")
                projections.append({"name":name,"amount":amount, "tag":tag})
        print(projections)
        writeTable("budget_projection", projections)

        return 0

    def createBudgetGraph(self):
        labels = list(self.budget_tagged.keys())
        values = list(self.budget_tagged.values())
        rot_fact = (3 / 8 - self.biggestTag(self.budget_tagged)[1]/self.budget) * 8 * 55
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
    year.createBudgetGraph()
    year.createExpensesGraph()
    createPDF(year)

if __name__ == '__main__':
    year = Year(2019)
    createYearlySheet(year)
