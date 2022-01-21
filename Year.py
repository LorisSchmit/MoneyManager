from database_api import *
import plotly.graph_objects as go
from createYearlySheet import *
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
import numpy as np
import squarify
import plotly.express as px

income_tags = importTable("income_tags",tags=True)

class Year:
    def __init__(self,year_no,projection=True):
        self.year_no = year_no
        self.all_transacts = getAllTransacts()
        self.yearly_transacts = self.getYearlyTransacts()
        self.income_transacts = self.getIncomeTransacts()
        self.lean_transacts = self.getLeanTransacts(self.yearly_transacts)
        self.total_spent = self.getTotalSpent(self.yearly_transacts)
        if projection and self.year_no >= datetime.now().year:
            self.projections = importTable("budget_projection")
        self.budget = self.getYearlyBudget(projection=projection)
        self.budget_tagged = self.analyzeBudget(projection=projection)
        tags = self.perTag()
        self.tags = tags
        self.max = self.biggestTag(self.tags)[1]
        self.payback = self.getPayback()
        self.perMonth = self.perMonth()


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

    def perTag(self):
        tags_temp = {}
        tags = {}
        tags_shortened = {}

        for id,action in self.lean_transacts.items():
            tot = action.amount
            tag = action.tag
            if tag not in tags_temp.keys():
                tags_temp[tag] = 0
            tags_temp[tag] += tot

        for tag,value in tags_temp.items():
            tags_temp[tag] = -round(value, 2)

        rest = 0
        rest_shortened = 0
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
        fig.savefig("Graphs/Budget" + str(self.year_no) + ".svg", bbox_inches="tight", dpi=1000)

    def createExpensesGraph(self):
        labels = list(self.tags_shortened.keys())
        values = list(self.tags_shortened.values())
        font_size = 12
        labels = list(self.tags.keys())
        values = list(self.tags.values())
        pb_exist = False
        if "Rückzahlung" in labels:
            pb_exist = True
            #pb_exist = False
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
        fig.savefig("Graphs/Expenses" + str(self.year_no) + ".svg",bbox_inches="tight",dpi=1000)



    def createBudgetTreemap(self):
        print("Drawing budget treemap for",self.year_no)
        labels = list(self.budget_tagged.keys())
        values = list(self.budget_tagged.values())
        parents = ["" for _ in range(len(labels))]
        fig = px.treemap(names=labels,values=values,parents=parents,width=510,height=400)#,color=cs)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.data[0].texttemplate = "%{label} <br> %{value} € <br> %{percentEntry}"
        fig.write_image("Graphs/Budget" + str(self.year_no) + ".svg")


    def createExpensesTreemap(self):
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
        fig.write_image("Graphs/Expenses" + str(self.year_no) + ".svg")

    def perMonth(self,num_top_tags = 5):
        top_tags_candidates = list(reversed(self.tags.items()))
        option4top_tags = ["Essen","Bar","Sport","Fahrrad","Auto","Sprit","Transport","Wohnen","Hardware","Drogerie","Amazon","Kleider"]
        perMonth = OrderedDict()
        i = 0
        while len(perMonth.items()) < num_top_tags:
            tag,value = top_tags_candidates[i]
            if tag in option4top_tags:
                perMonth[tag] = round(value/12,2)
            i += 1

        return perMonth



def createYearlySheet(year,redraw_graphs=False):
    if redraw_graphs:
        year.createBudgetTreemap()
        year.createExpensesTreemap()
    createPDF(year)

if __name__ == '__main__':
    year = Year(2021)
    createYearlySheet(year)#,redraw_graphs=True)