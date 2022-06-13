from database_api import *
from createYearlySheet import *
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
import numpy as np
import plotly.express as px
import threading
from matplotlib import dates as mdates
from dateutil.relativedelta import relativedelta

income_tags = importTable("income_tags",tags=True)

class Year:
    def __init__(self,year_no,projection=True,pre_year=True,setBudget=False,budget=0):
        self.year_no = year_no
        self.all_transacts = getAllTransacts()
        self.yearly_transacts = self.getYearlyTransacts()
        self.income_transacts = self.getIncomeTransacts()
        self.lean_transacts = self.getLeanTransacts(self.yearly_transacts)
        self.total_spent = self.getTotalSpent(self.yearly_transacts)
        if pre_year:
            self.balances = self.getBalances()

        if projection and not setBudget:
            projs = importTable("budget_projection")
            self.projections = []
            for proj in projs:
                if proj["year"] == datetime.now().year:
                    self.projections.append(proj)
            self.budget = self.getYearlyBudget(projection=projection)
            self.budget_tagged = self.analyzeBudget(projection=projection)
        elif not projection:
            self.budget = self.getYearlyBudget(projection=projection)
            self.budget_tagged = self.analyzeBudget(projection=projection)
        else:
            self.budget = budget
        self.setBudget = setBudget

        tags = self.perTag()
        self.tags = tags
        self.max = self.biggestTag(self.tags)[1]
        self.payback = self.getPayback()
        self.pers_spent = round(self.total_spent + self.payback,2)
        if pre_year:
            self.pre_year = Year(self.year_no-1,pre_year=False)
        self.perMonth,self.perMonth_pre_year = self.perMonth(pre_year=pre_year)



    def getTotalSpent(self,transacts):
        tot = 0
        for id,action in transacts.items():
            if action.tag != "Einkommen" and action.amount < 0 and action.tag != "Kapitaltransfer":
                tot += action.amount
        return round(tot, 2)

    def getYearlyBudget(self,projection=True):
        yearly_budget = 0
        if projection and self.year_no >= datetime.now().year:
            for proj in self.projections:
                yearly_budget += proj["amount"]
        else:
            yearly_budget = 0
            for id,action in self.yearly_transacts.items():
                if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
                    yearly_budget += action.amount
        return round(yearly_budget,2)

    def getPayback(self):
        total = 0
        for id,action in self.yearly_transacts.items():
            if action.tag == "Rückzahlung":
                total += action.amount
        return round(total,2)

    def getYearlyTransacts(self):
        start = datetime(self.year_no, 1, 1)
        end = datetime(self.year_no+1, 1, 1)
        yearly_transacts = OrderedDict()
        for id,action in self.all_transacts.items():
            if action.date >= start and action.date < end:
                yearly_transacts[id] = action
        return yearly_transacts

    def getLeanTransacts(self,transacts):
        lean_transacts = OrderedDict()
        for id,action in transacts.items():
            if action.tag != "Einkommen" and action.tag != "Kapitaltransfer":
                lean_transacts[id] = action
        return lean_transacts

    def getIncomeTransacts(self):
        income_transacts = OrderedDict()
        for id,action in self.yearly_transacts.items():
            if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
                income_transacts[id] = action
        return income_transacts

    def getAccounts(self):
        accounts = {}
        for id, action in self.yearly_transacts.items():
            if action.account.name not in accounts:
                accounts[action.account.name] = action.account
        return accounts

    def getBalances(self):
        accounts = self.getAccounts()

        new_year = datetime(self.year_no, 1, 1)

        balances = {}
        for account_name, account in accounts.items():
            account_transacts = []
            for id, action in self.yearly_transacts.items():
                if action.account.name == account_name:
                    account_transacts.append(action)

            transacts_list = sorted(account_transacts, key=lambda action: action.date)
            dates = [action.date for action in transacts_list]

            base_date = datetime(self.year_no,12,31)

            for date in account.balance_base.keys():
                if date.year == self.year_no:
                    if date < base_date:
                        base_date = date

            if base_date < datetime(self.year_no,12,31):
                balance = account.balance_base[base_date]
                balance_list = [balance]
                dates.insert(0, base_date)
            else:
                print("No balance base available")
                balance = 0
                balance_list = [balance]
                dates.insert(0, new_year)

            for action in transacts_list:
                balance += round(action.amount, 2)
                balance_list.append(round(balance, 2))

            balances[account_name] = (dates, balance_list)

        return balances

    def perTag(self):
        tags_temp = {}
        tags = {}

        for id,action in self.lean_transacts.items():
            tot = action.amount
            tag = action.tag
            if tag not in tags_temp.keys():
                tags_temp[tag] = 0
            tags_temp[tag] += tot

        for tag,value in tags_temp.items():
            tags_temp[tag] = -round(value, 2)

        rest = 0

        for tag,value in tags_temp.items():
            if tags_temp[tag] >= 20:
                tags[tag.rstrip()] = tags_temp[tag]
            elif tag == "Rückzahlung":
                tags[tag.rstrip()] = tags_temp[tag]
            elif tags_temp[tag] > 0:
                rest += float(tags_temp[tag.rstrip()])

        rest = round(rest, 2)
        tags['Rest'] = rest
        tags_temp = {}
        for tag,value in tags.items():
            if value >= 1:
                tags_temp[tag] = value
        tags = OrderedDict(sorted(tags_temp.items(), key=lambda x: x[1]))

        return tags

    def paybackPerTag(self):
        in_advances = {}
        for id,action in self.yearly_transacts.items():
            if type(action.pb_assign) is list:
                if len(action.pb_assign) > 0:
                    if action.pb_assign[0] != -1:
                        tag = action.tag
                        if not (tag in in_advances):
                            in_advances[tag] = 0
                        for pb_assign in action.pb_assign:
                            in_advances[tag] += self.all_transacts[pb_assign].amount

                        in_advances[tag] = round(in_advances[tag], 2)
        pbs_labels = []
        pbs_labels.extend(in_advances.keys())
        pbs_labels.append("  ")
        pbs_values = []
        pbs_values.extend(in_advances.values())
        in_advances = OrderedDict(sorted(in_advances.items(), key=lambda x: x[1]))
        pbs_pie_dict = OrderedDict()
        tags = self.tags.copy()
        if "Rückzahlung" in tags:
            tags.pop("Rückzahlung")
            for key,value in tags.items():
                if key in in_advances:
                    if value >= in_advances[key]:
                        pbs_pie_dict[key] = in_advances[key]
                        pbs_pie_dict[key+" fillup"] = round(value - in_advances[key], 2)
                    else:
                        pbs_pie_dict[key] = value
                        pbs_pie_dict[key+" fillup"] = 0
                else:
                    pbs_pie_dict[key+" fillup"] = value
        return pbs_pie_dict

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
            data = {}

            for id, action in self.income_transacts.items():
                tot = action.amount
                tag = action.tag
                if tag not in data_temp.keys():
                    data_temp[tag] = 0
                data_temp[tag] += tot

            for tag, value in data_temp.items():
                data[tag] = round(value, 2)
        return data



    def setProjections(self):
        projections = importTable("budget_projection")
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
        writeTable("budget_projection", projections)

        return 0

    def createBudgetGraph(self,vector=True):
        font_size = 12
        labels = list(self.budget_tagged.keys())
        values = list(self.budget_tagged.values())
        rot_fact = (3 / 8 - self.biggestTag(self.budget_tagged)[1]/self.budget) * 8 * 55
        if rot_fact < 0:
            rot_fact = 0
        if rot_fact > 360:
            rot_fact = -360
        interval = np.hstack([np.linspace(0, 0.6), np.linspace(0.7, 1)])
        colors = plt.cm.jet(interval)
        cs = LinearSegmentedColormap.from_list('name', colors, N=len(values))
        cs = [mcolors.rgb2hex(cs(i)) for i in range(cs.N)]

        fig, ax = plt.subplots()
        pie = ax.pie(values, labels=labels, startangle=rot_fact, labeldistance=0.35,
                     textprops={"color": "white", "fontsize": font_size, "rotation_mode": 'anchor', "va": 'center',
                                "ha": 'right'}, rotatelabels=True, colors=cs)
        file_name = "Budget"+str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        fig.savefig(graph_path, bbox_inches="tight", dpi=1000)

    def createExpensesGraph(self,vector=True):
        labels = list(self.tags_shortened.keys())
        values = list(self.tags_shortened.values())
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

        interval = np.hstack([np.linspace(0, 0.6), np.linspace(0.7, 1)])
        colors = plt.cm.jet(interval)
        cs = LinearSegmentedColormap.from_list('name', colors, N=len(values))
        cs = [mcolors.rgb2hex(cs(i)) for i in range(cs.N)]

        if pb_exist:
            cs_pb = []
            i = 0
            for key, value in pbs_pie_dict.items():
                if key.find("fillup") == -1:
                    cs_pb.append("#FFFFFF80")
                else:
                    cs_pb.append("#FFFFFF00")
                i += 1
            cs_pb = np.array(cs_pb)
        fig, ax = plt.subplots()
        pie = ax.pie(values, labels=labels, startangle=rot_fact, labeldistance=0.35,
                     textprops={"color": "white", "fontsize": font_size, "rotation_mode": 'anchor', "va": 'center',
                                "ha": 'right'}, rotatelabels=True, colors=cs)
        for t in pie[1]:
            if t.get_position()[0] > 0:
                t.set_ha("left")
        if pb_exist:
            pbs_pie = ax.pie(pbs_values, radius=1, startangle=rot_fact,
                             textprops={"color": "white", "fontsize": font_size, "rotation_mode": 'anchor',
                                        "va": 'center', "ha": 'left'}, labeldistance=0.6, colors=cs_pb,
                             wedgeprops={"lw": 0})
            legend_labels = []
            legend_patches = []
            for i in range(len(pbs_pie[0])):
                if int(cs_pb[i][1:], 16) > 0xFFFFFF00:
                    ind = labels.index(list(pbs_pie_dict.items())[i][0].replace(" fillup", ""))
                    pbs_pie[0][i].set(hatch="///", edgecolor=cs[ind])
                    if len(legend_patches) == 0:
                        legend_patches.append(pbs_pie[0][i])
                        legend_labels.append("Rückzahlung")
            ax.legend(legend_patches, legend_labels, loc="lower left", framealpha=0)

        file_name = "Expenses" + str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        fig.savefig(graph_path, bbox_inches="tight", dpi=1000)



    def createBudgetTreemap(self,vector=True):
        print("Drawing budget treemap for",self.year_no)
        labels = list(self.budget_tagged.keys())
        values = list(self.budget_tagged.values())
        parents = ["" for _ in range(len(labels))]
        fig = px.treemap(names=labels,values=values,parents=parents,width=510,height=400)#,color=cs)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.data[0].texttemplate = "%{label} <br> %{value} € <br> %{percentEntry}"
        file_name = "Budget" + str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        fig.write_image(graph_path)


    def createExpensesTreemap(self,vector=True):
        print("Drawing expenses treemap for",self.year_no)
        labels = list(self.tags.keys())
        values = list(self.tags.values())
        if "Rückzahlung" in labels:
            pb_ind = labels.index("Rückzahlung")
            labels.pop(pb_ind)
            values.pop(pb_ind)
        parents = ["" for _ in range(len(labels))]
        fig = px.treemap(names=labels,values=values,parents=parents,width=510,height=710)#,color=cs)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.data[0].texttemplate = "%{label} <br> %{value} € <br> %{percentEntry}"
        file_name = "Expenses" + str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        fig.write_image(graph_path)

    def perMonth(self,num_top_tags = 8,pre_year=True):
        top_tags_candidates = list(reversed(self.tags.items()))
        option4top_tags = ["Essen","Bar","Sport","Fahrrad","Auto","Sprit","Transport","Wohnen","Hardware","Drogerie","Amazon","Kleider"]
        perMonth = OrderedDict()
        perMonth["Gesamt"] = round(-self.pers_spent/12,2)
        i = 0
        while len(perMonth.items()) < num_top_tags and i < len(top_tags_candidates):
            tag,value = top_tags_candidates[i]
            if tag in option4top_tags:
                perMonth[tag] = round(value/12,2)
            i += 1

        perMonth_pre_year = OrderedDict()
        if pre_year:
            perMonth_pre_year["Gesamt"] = round(-self.pre_year.pers_spent / 12, 2)
            for tag,value in list(perMonth.items()):
                if tag in self.pre_year.tags:
                    perMonth_pre_year[tag] = round(self.pre_year.tags[tag]/12,2)
                elif tag != "Gesamt":
                    perMonth_pre_year[tag] = 0
        return perMonth,perMonth_pre_year


    def createBalancePlot(self,vector=True):
        new_years_eve = datetime(self.year_no, 12, 31, 23, 59)
        spectres = {}

        ignore_accounts = ["Visa", "PayPal"]
        self.balances_plot = {}

        for account_name, balances_tuples in self.balances.items():
            if account_name not in ignore_accounts:
                balance_list = balances_tuples[1]
                spectres[account_name] = (min(balance_list), max(balance_list))
                self.balances_plot[account_name] = balances_tuples
        outlier_accounts = []
        for account_name_i, spectre_i in spectres.items():
            diff = 0
            for account_name_j, spectre_j in spectres.items():
                if account_name_i != account_name_j:
                    diff += abs(spectre_i[0] - spectre_j[1])  # min(i) - max(j)
                    diff += abs(spectre_j[0] - spectre_i[1])  # min(j) - max(i)
            if diff / (2 * (len(spectres.keys()) - 1)) > 10000:
                outlier_accounts.append(account_name_i)
        dpi = 500
        if len(outlier_accounts) > 0:
            f, axs = plt.subplots(len(outlier_accounts) + 1, 1, sharex=True, figsize=(10,6))
            f.subplots_adjust(hspace=0.1)  # adjust space between axes
        else:
            f = plt.figure(figsize=(10,6))
            axs = [plt.gca()]

        maxs = []
        mins = []
        for account_name, spectre in spectres.items():
            if account_name not in outlier_accounts:
                mins.append(spectre[0])
                maxs.append(spectre[1])
        y_lim = (min(mins), max(maxs) + 1000)

        for account_name, balances_dict in self.balances_plot.items():
            dates = balances_dict[0]
            balance_list = balances_dict[1]

            new_year = dates[0]

            if len(balances_dict) > 0:
                for ax in axs:
                    p, = ax.plot(dates, balance_list, label=account_name)
                    arrow_props = dict(arrowstyle='-', color=p.get_color(), lw=1.5, ls='--')
                    ax.annotate(str(balance_list[0]).replace(".", ",") + " €", fontsize=12,
                                xy=(dates[0], balance_list[0]),
                                xytext=(dates[0] + relativedelta(days=15), balance_list[0]),
                                arrowprops=arrow_props, va="center", ha="left")
                    ax.annotate(str(balance_list[-1]).replace(".", ",") + " €", fontsize=12,
                                xy=(dates[-1], balance_list[-1]),
                                xytext=(dates[-1] + relativedelta(days=15), balance_list[-1]),
                                arrowprops=arrow_props, va="center", ha="left")

                # zoom-in / limit the view to different portions of the data
                if len(outlier_accounts) > 0:
                    axs[0].set_ylim(spectres[outlier_accounts[0]][0] - 750,
                                    spectres[outlier_accounts[0]][1] + 750)  # outliers only
                    axs[1].set_ylim(y_lim)  # most of the data
                    axs[1].set_xlim([new_year, new_years_eve])

                    # hide the spines between ax and ax2
                    axs[0].spines.bottom.set_visible(False)
                    axs[1].spines.top.set_visible(False)
                    axs[0].xaxis.tick_top()
                    axs[0].tick_params(labeltop=False)  # don't put tick labels at the top
                    axs[1].xaxis.tick_bottom()

                    # Now, let's turn towards the cut-out slanted lines.
                    # We create line objects in axes coordinates, in which (0,0), (0,1),
                    # (1,0), and (1,1) are the four corners of the axes.
                    # The slanted lines themselves are markers at those locations, such that the
                    # lines keep their angle and position, independent of the axes size or scale
                    # Finally, we need to disable clipping.

                    d = .5  # proportion of vertical to horizontal extent of the slanted line
                    kwargs = dict(marker=[(-1, -d), (1, d)], markersize=12,
                                  linestyle="none", color='k', mec='k', mew=1, clip_on=False)
                    axs[0].plot([0, 1], [0, 0], transform=axs[0].transAxes, **kwargs)
                    axs[1].plot([0, 1], [1, 1], transform=axs[1].transAxes, **kwargs)
                else:
                    axs[0].set_ylim(y_lim)  # most of the data
                    axs[0].set_xlim([new_year, new_years_eve])
                # Minor ticks every month.
                fmt_month = mdates.MonthLocator()
                # Minor ticks every year.
                fmt_year = mdates.YearLocator()
                if len(outlier_accounts) > 0:
                    ax = axs[1]
                else:
                    ax = axs[0]
                ax.xaxis.set_minor_locator(fmt_month)
                # '%b' to get the names of the month
                ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
                ax.xaxis.set_major_locator(fmt_year)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
                # fontsize for month labels
                ax.xaxis.set_tick_params(labelsize=10, which='both')
                # create a second x-axis beneath the first x-axis to show the year in YYYY format
                sec_xaxis = ax.secondary_xaxis(-0.075*len(axs))
                sec_xaxis.xaxis.set_major_locator(fmt_year)
                sec_xaxis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

                # Hide the second x-axis spines and ticks
                sec_xaxis.spines['bottom'].set_visible(False)
                sec_xaxis.tick_params(length=0, labelsize=12)

        axs[0].legend(loc="upper left")
        file_name = "Balances" + str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        f.savefig(graph_path, bbox_inches="tight", dpi=dpi)



def createYearlySheet(year_no,folder,redraw_graphs=False,gui=None):
    projection = False
    budget = 0
    setBudget = False
    if gui is not None:
        #gui.progressBarLabel.setText("Jährliche Bilanz PDF Erstellung gestartet")
        if gui.takeProjRadio.isChecked() and year_no >= datetime.now().year:
            projection = True
        if gui.setBudgetRadio.isChecked():
            budget = gui.budget
            setBudget = True
    year = Year(year_no,projection=projection,setBudget=setBudget,budget=budget)
    if gui is not None:
        gui.yearlySheetCreationProgressBar.setValue(20)
        #gui.progressBarLabel.setText("Erstellen des Budget Diagramms für "+str(year_no))
    if redraw_graphs:
        if not setBudget:
            year.createBudgetTreemap()
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(40)
            #gui.progressBarLabel.setText("Erstellen des Ausgaben Diagramms für " +str(year_no))
        year.createExpensesTreemap()
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(60)
            #gui.progressBarLabel.setText("Erstellen der jährlichen Bilanz PDF für " +str(year_no))
        year.createBalancePlot()
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(80)
    createPDF(year,year.pre_year,folder,setBudget=setBudget)
    if gui is not None:
        gui.yearlySheetCreationProgressBar.setValue(100)
        #gui.progressBarLabel.setText("Jährliche Bilanz PDF fertig!")

def executeCreateSingleYear(year,folder,redraw_graphs=False,gui=None):
    print("Yearly Balance Sheet Creation started")
    new_thread = threading.Thread(target=createYearlySheet,args=(year,folder,redraw_graphs,gui,))
    new_thread.start()

if __name__ == '__main__':
    createYearlySheet(2019)#,redraw_graphs=True)