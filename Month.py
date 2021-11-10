from datetime import datetime
from database_api import *
import plotly.graph_objects as go
from commonFunctions import weekNumberToDates
from createBalanceSheets import drawPDF
import threading
import matplotlib.pyplot as plt
import collections
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from test_pdf import PdfImage
import matplotlib.colors as mcolors
from Year import Year


class Month(Year):
    def __init__(self,month,year,projection=True):
        self.month = month
        self.month_name = self.monthNumberToMonthName()
        self.year_no = year
        #self.year = Year.Year(self.year_no)
        self.all_transacts = getAllTransacts()
        self.transacts = self.getMonthlyTransacts(self.all_transacts)
        self.lean_transacts = self.getLeanTransacts()
        self.yearly_transacts = self.getYearlyTransacts()
        if len(self.transacts)>0:
            self.tags = self.perTag()
            self.total = self.getTotalSpent()
            if projection and self.year_no >= datetime.now().year:
                self.projections = importTable("budget_projection")
            self.budget = self.getBudget(projection=projection)
            self.max = self.biggestTag()[1]
            self.weeks = self.perWeek()
            self.pbs = self.getPayBacks()
            self.pbs_tags = self.paybackPerTag()

    def getMonthlyTransacts(self,transacts):
        start = datetime(self.year_no, self.month, 1)
        if self.month < 12:
            end = datetime(self.year_no, self.month + 1, 1)
        else:
            end = datetime(self.year_no + 1, 1, 1)
        monthly_transacts = []
        for action in transacts:
            if action.date >= start and action.date < end:
                monthly_transacts.append(action)
        return monthly_transacts

    def getIncome(self):
        total = 0
        for action in self.transacts:
            if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Einkommen":
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

    def getYearlyTransacts(self):
        start = datetime(self.year_no, 1, 1)
        end = datetime(self.year_no+1, 1, 1)
        yearly_transacts = []
        for action in self.all_transacts:
            if action.date >= start and action.date < end:
                yearly_transacts.append(action)
        return yearly_transacts

    def getBudget(self,projection=True):
        yearly_budget = 0
        if projection and self.year_no >= datetime.now().year:
            for proj in self.projections:
                yearly_budget += proj["amount"]
        else:
            yearly_budget = 0
            for action in self.yearly_transacts:
                if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
                    yearly_budget += action.amount

        budget = round(yearly_budget/12.0,2)
        return budget

    def getPayBacks(self):
        pbs = []
        for action in self.transacts:
            if action.tag == "Rückzahlung":
                pbs.append(action)
        return pbs

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
        tags = collections.OrderedDict(sorted(tags.items(), key=lambda x: x[1]))
        return tags

    def biggestTag(self):
        max_key = next(iter(self.tags))
        max = self.tags[max_key]
        for tag in self.tags:
            if self.tags[tag] > max:
                max_key = tag
                max = self.tags[tag]
        return (max_key, max)

    def paybackPerTag(self):
        in_advances = {}
        for action in self.transacts:
            if type(action.pb_assign) is list:
                if len(action.pb_assign) > 0:
                    tag = action.tag
                    if not (tag in in_advances):
                        in_advances[tag] = 0
                    for pb_assign in action.pb_assign:
                        in_advances[tag] += self.all_transacts[pb_assign-1].amount

                    in_advances[tag] = round(in_advances[tag], 2)
        pbs_labels = []
        pbs_labels.extend(in_advances.keys())
        pbs_labels.append("  ")
        pbs_values = []
        pbs_values.extend(in_advances.values())
        #pbs_values.append(-self.total - in_advances["Ausflug"])
        in_advances = collections.OrderedDict(sorted(in_advances.items(), key=lambda x: x[1]))
        pbs_pie_dict = collections.OrderedDict()
        tags = self.tags.copy()
        if "Rückzahlung" in tags:
            tags.pop("Rückzahlung")
            for key,value in tags.items():
                if key in in_advances:
                    pbs_pie_dict[key] = in_advances[key]
                    pbs_pie_dict[key+" fillup"] = round(value - in_advances[key],2)
                else:
                    pbs_pie_dict[key+" fillup"] = value
        return pbs_pie_dict

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
            font_size = 12
            labels = list(self.tags.keys())
            values = list(self.tags.values())
            pb_exist = False
            if "Rückzahlung" in labels:
                #pb_exist = True
                pb_ind = labels.index("Rückzahlung")
                labels.pop(pb_ind)
                values.pop(pb_ind)
                pbs_pie_dict = self.paybackPerTag()
                pbs_values = list(pbs_pie_dict.values())
                pbs_labels = list(pbs_pie_dict.keys())

            rot_fact = (3 / 8 - self.max / self.total) * 8 * 55
            if rot_fact < 0:
                rot_fact = 0
            if rot_fact > 360:
                rot_fact -= 360
            rot_fact = 0

            #cs = plt.get_cmap('rainbow',len(values))(range(len(values)))
            interval = np.hstack([np.linspace(0, 0.6), np.linspace(0.7, 1)])
            colors = plt.cm.jet(interval)
            cs = LinearSegmentedColormap.from_list('name', colors,N=len(values))
            cs = [mcolors.rgb2hex(cs(i)) for i in range(cs.N)]

            if pb_exist:
                cs_pb = []
                i = 0
                for key,value in pbs_pie_dict.items():
                    if key.find("fillup") == -1:
                        cs_pb.append("#FFFFFF80")
                    else:
                        cs_pb.append("#FFFFFF00")
                    i+=1
                cs_pb = np.array(cs_pb)
            fig, ax = plt.subplots()
            pie = ax.pie(values, labels=labels, startangle=rot_fact, labeldistance=0.35, textprops={"color":"white", "fontsize":font_size, "rotation_mode":'anchor', "va":'center', "ha":'right'}, rotatelabels=True, colors=cs)
            for t in pie[1]:
                if t.get_position()[0] > 0:
                    t.set_ha("left")
            if pb_exist:
                pbs_pie = ax.pie(pbs_values, radius=1,startangle=rot_fact,textprops={"color":"white", "fontsize":font_size, "rotation_mode":'anchor', "va":'center', "ha":'left'},labeldistance=0.6,  colors=cs_pb,wedgeprops={"lw":0})
                legend_labels = []
                legend_patches = []
                for i in range(len(pbs_pie[0])):
                    if int(cs_pb[i][1:],16) > 0xFFFFFF00:
                        ind = labels.index(list(pbs_pie_dict.items())[i][0].replace(" fillup",""))
                        pbs_pie[0][i].set(hatch="///",edgecolor=cs[ind])
                        if len(legend_patches) == 0:
                            legend_patches.append(pbs_pie[0][i])
                            legend_labels.append("Rückzahlung")
                ax.legend(legend_patches,legend_labels,loc="lower left",framealpha=0)

            fig.savefig("Graphs/" + str(self.year_no) + " - " + str(self.month) + ".png",bbox_inches="tight",dpi=1000)


    def createBalanceSheet(self):
        if len(self.transacts) > 0:
            drawPDF(self)

def monthsPerYear(year):
    for i in range(1, 13):
        month = Month(i, year)
        month.createGraph()
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
    #monthsPerYear(2019)
    month = Month(10, 2021)
    month.createGraph()
    month.createBalanceSheet()
    print(month.budget)


