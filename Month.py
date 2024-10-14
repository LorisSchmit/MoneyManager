from commonFunctions import weekNumberToDates
from createBalanceSheets import drawPDF,prepare4Saving
import os
from Year import *
import pandas as pd




class Month(Year):
    def __init__(self,month,year,projection=True,setBudget=False,budget=0,deduct_in_advances=True):
        self.month = month
        self.month_name = self.monthNumberToMonthName()
        self.year_no = year
        self.all_transacts = getAllTransacts()
        self.monthly_transacts = self.getMonthlyTransacts(self.all_transacts)
        self.monthly_transacts_count = len(self.monthly_transacts)
        self.lean_transacts = self.getLeanTransacts(self.monthly_transacts)
        self.yearly_transacts = self.getYearlyTransacts()
        if len(self.monthly_transacts) > 0:
            self.tags = self.perTag()
            self.tagStruct = self.getTagStructure()
            self.total_spent,_ = self.getTotalSpent(self.monthly_transacts)
            if projection and self.year_no >= datetime.now().year:
                projs = importTable("budget_projection")
                self.projections = []
                for proj in projs:
                    if proj["year"] == datetime.now().year:
                        self.projections.append(proj)
            if not setBudget:
                self.budget = self.getMonthlyBudget(projection=projection)
            else:
                self.budget = round(budget/12,2)
            self.max = self.biggestTag(self.tags)[1]
            self.weeks = self.perWeek()
            self.deduct_in_advances = deduct_in_advances
            self.payback_transacts,self.payback_len,self.in_advance_payback_len = self.getPayBackTransacts(self.monthly_transacts)
            self.payback = self.getPayback()
            self.in_advances = self.paybackPerTag(self.monthly_transacts)
        self.file_name = str(self.year_no) + " - " + str(self.month)

    def getMonthlyTransacts(self,transacts):
        start = datetime(self.year_no, self.month, 1)
        if self.month < 12:
            end = datetime(self.year_no, self.month + 1, 1)
        else:
            end = datetime(self.year_no + 1, 1, 1)
        monthly_transacts = OrderedDict()
        for id,action in transacts.items():
            if action.date >= start and action.date < end:
                monthly_transacts[id] = action
        return monthly_transacts


    def getMonthlyBudget(self,projection=True):
        yearly_budget,_ = self.getYearlyBudget(projection=projection)
        monthly_budget = round(yearly_budget/12.0,2)
        return monthly_budget



    def monthNumberToMonthName(self):
        months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober',
                  'November', 'Dezember']
        return months[self.month-1]


    def perWeek(self):
        weeks = {}
        date = min(action.date for action in self.lean_transacts.values())
        week_number0 = date.isocalendar()[1]
        tot = 0
        for id,action in self.lean_transacts.items():
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

    def createGraph(self,vector=True):
        if len(self.monthly_transacts) > 0:
            font_size = 12
            labels = list(self.tags.keys())
            values = list(self.tags.values())
            pb_exist = False
            if "Rückzahlung" in labels:
                pb_exist = True
                pb_ind = labels.index("Rückzahlung")
                labels.pop(pb_ind)
                values.pop(pb_ind)
                pbs_pie_dict = self.paybackPerTag()
                pbs_values = list(pbs_pie_dict.values())
                pbs_labels = list(pbs_pie_dict.keys())

            rot_fact = (3 / 8 - self.max / self.total_spent) * 8 * 55
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

            file_name = str(self.year_no) + " - " + str(self.month)
            graph_path = prepare4Saving(file_name, vector)

            fig.savefig(graph_path,bbox_inches="tight",dpi=1000)

    def createExpensesTreemap(self,vector=True):
        print("Drawing expenses treemap for",self.month_name,"-",self.year_no)
        labels = list(self.tags.keys())
        values = list([round(value,2) for value in self.tags.values()])
        if "Rückzahlung" in labels:
            pb_ind = labels.index("Rückzahlung")
            labels.pop(pb_ind)
            values.pop(pb_ind)
        parents = ["" for _ in range(len(labels))]
        fig = px.treemap(names=labels,values=values,parents=parents,width=300,height=400)#,color=cs)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.data[0].texttemplate = "%{label} <br> %{percentEntry}"

        file_name = str(self.year_no) + " - " + str(self.month)
        graph_path = prepare4Saving(file_name, vector)

        fig.write_image(graph_path)


    def createBalanceSheet(self,folder):
        if len(self.monthly_transacts) > 0:
            drawPDF(self,folder)

def monthsPerYear(year):
    for i in range(1, 13):
        month = Month(i, year,deduct_in_advances=True)
        month.createNestedExpensesTreemap()
        home = Path.home()
        month.createBalanceSheet(home/"Documents"/"Balance Sheets")
    return "All Balances for "+str(year)+" created"

def createSingleMonth(month,year,folder,gui=None,redraw_graphs=True,deduct_in_advances=True):
    projection = False
    budget = 0
    setBudget = False
    if gui is not None:
        gui.progressBarMonthLabel.setText("Monatliche Bilanz PDF Erstellung gestartet")
        if gui.takeProjRadio.isChecked():
            projection = True
        if gui.setBudgetRadio.isChecked():
            budget = gui.budget
            setBudget = True
    month = Month(month, year,projection=projection,setBudget=setBudget,budget=budget,deduct_in_advances=deduct_in_advances)
    if redraw_graphs:
        if gui is not None:
            gui.monthlySheetCreationProgressBar.setValue(33)
            gui.progressBarMonthLabel.setText("Erstellen des Ausgaben Diagramms für "+str(month.month_name)+" "+str(month.year_no))
        month.createNestedExpensesTreemap()
        if gui is not None:
            gui.monthlySheetCreationProgressBar.setValue(66)
            gui.progressBarMonthLabel.setText("Erstellen der monatlichen Bilanz PDF für "+str(month.month_name)+" "+str(month.year_no))
    month.createBalanceSheet(folder)
    if gui is not None:
        gui.monthlySheetCreationProgressBar.setValue(100)
        gui.progressBarMonthLabel.setText("Monatliche Bilanz PDF fertig!")

def executeCreateSingleMonth(month,year,folder,gui=None):
    print("Balance Sheet Creation started")
    main_thread = threading.Thread(target=createSingleMonth,args=(month,year,folder,gui))
    main_thread.start()

def executeAssignPayback(month,year):
    print("Payback Assignment started")
    month_obj = Month(month,year)
    assign_thread = threading.Thread(target=month_obj.assignPayback,args=(month_obj.monthly_transacts,))
    assign_thread.start()



if __name__ == '__main__':
    #monthsPerYear(2021)
    home = Path.home()
    #createSingleMonth(9,2022,home/"Documents"/"Balance Sheets",redraw_graphs=True,deduct_in_advances=True)
    month = Month(1, 2023)
    #month.createNestedExpensesTreemap()
    month.assignPayback(month.monthly_transacts)
    #month.createGraph()
    #month.createBalanceSheet()
    #print(month.budget)


