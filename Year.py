from database_api import *
from createYearlySheet import *
from Account import accounts
from expense_plotter import *

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
import numpy as np
import plotly.express as px
import threading
from matplotlib import dates as mdates
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

class Year:
    def __init__(self,year_no,projection=True,pre_year=True,setBudget=False,budget=0,deduct_in_advances=True):
        self.year_no = year_no
        self.all_transacts = getAllTransacts()
        self.yearly_transacts = self.getYearlyTransacts()
        self.income_transacts = self.getIncomeTransacts()
        self.lean_transacts = self.getLeanTransacts(self.yearly_transacts)
        self.transfer_transacts,self.transfer_transacts_len = self.getTransferTransacts()
        self.total_sold, self.total_sold_len = self.getTotalSold()
        self.total_spent,self.total_spent_len = self.getTotalSpent(self.yearly_transacts)
        if pre_year:
            self.accounts = self.getAccounts()
            self.balances = self.getBalances()
            self.accounts_balance = self.getYearlyAccountsBalance()

        if projection and not setBudget:
            projs = importTable("budget_projection")
            self.projections = []
            for proj in projs:
                if proj["year"] == datetime.now().year:
                    self.projections.append(proj)
            self.budget,self.budget_len = self.getYearlyBudget(projection=projection)
            self.budget_tagged = self.analyzeBudget(projection=projection)
        elif not projection:
            self.budget,self.budget_len = self.getYearlyBudget(projection=projection)
            self.budget_tagged = self.analyzeBudget(projection=projection)
        else:
            self.budget,self.budget_len = budget,0
        self.setBudget = setBudget

        tags = self.perTag()
        self.tagStruct = self.getTagStructure()
        self.tags = tags
        self.max = self.biggestTag(self.tags)[1]
        self.deduct_in_advances = deduct_in_advances
        self.payback_transacts,self.payback_len,self.in_advance_payback_len = self.getPayBackTransacts(self.yearly_transacts)
        self.payback = self.getPayback()
        self.in_advances = self.paybackPerTag(self.yearly_transacts)

        self.pers_spent = round(self.total_spent + self.payback,2)
        if pre_year:
            self.adjustment_foreign_year = self.getForeignYearPaybacks()
            #self.pre_year = Year(self.year_no-1,pre_year=False)

        #self.perMonth,self.perMonth_pre_year = self.perMonth(pre_year=pre_year)
        self.file_name = "Expenses"+str(self.year_no)

    def getTotalSpent(self,transacts):
        tot = 0
        count = 0
        for id,action in transacts.items():
            if action.tag != "Einkommen" and action.amount < 0 and action.tag != "Kapitaltransfer":
                tot += action.amount
                count += 1
        return round(tot, 2),count

    def getYearlyBudget(self,projection=True):
        yearly_budget = 0
        count = 0
        if projection and self.year_no >= datetime.now().year:
            for proj in self.projections:
                yearly_budget += proj["amount"]
                count += 1
        else:
            yearly_budget = 0
            for id,action in self.yearly_transacts.items():
                if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung" and action.tag != "Kredit":
                    yearly_budget += action.amount
                    count += 1
        return round(yearly_budget,2),count

    def getPayback(self):
        total = sum([action.amount for id,action in self.payback_transacts.items()])
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
            if action.amount < 0 and action.tag != "Kapitaltransfer":
                lean_transacts[id] = action
        return lean_transacts

    def getIncomeTransacts(self):
        income_transacts = OrderedDict()
        for id,action in self.yearly_transacts.items():
            if action.amount > 0 and action.tag != "Kapitaltransfer" and action.tag != "Rückzahlung":
                income_transacts[id] = action
        return income_transacts

    def getTotalSold(self):
        total = 0
        count = 0
        for id, action in self.yearly_transacts.items():
            if action.tag == "Verkauf":
                total += action.amount
                count += 1
        return round(total, 2), count

    def getTransferTransacts(self):
        transfer_transacts = OrderedDict()
        count = 0
        for id,action in self.yearly_transacts.items():
            if action.tag == "Kapitaltransfer":
                transfer_transacts[id] = action
                count += 1
        return transfer_transacts,count

    def getPayBackTransacts(self,transacts):
        payback_transacts = OrderedDict()
        payback_count = 0
        in_advance_payback_count = 0
        for id,action in transacts.items():
            if action.tag == "Rückzahlung":
                if len(action.pb_assign) > 0:
                    if action.pb_assign[0] < 0 or not self.deduct_in_advances:
                        payback_transacts[id] = action
                        payback_count += 1
                    else:
                        in_advance_payback_count += 1

        return payback_transacts, payback_count, in_advance_payback_count

    def getForeignYearPaybacks(self):
        all_paybacks_id = []
        all_in_advances_id = []
        for id,action in self.yearly_transacts.items():
            if action.tag == "Rückzahlung":
                try:
                    if action.pb_assign[0] == 0:
                        all_paybacks_id.append(id)
                except IndexError:
                    print(action.id)
            if len(action.pb_assign) > 0:
                if action.pb_assign[0] > 0:
                    for id_a in action.pb_assign:
                        all_in_advances_id.append(id_a)

        differences = [list(set(all_paybacks_id).difference(all_in_advances_id)),list(set(all_in_advances_id).difference(all_paybacks_id))]
        adjustment_foreign_year = 0
        adjustment_foreign_year -= sum([self.all_transacts[id].amount for id in differences[0]])
        adjustment_foreign_year += sum([self.all_transacts[id].amount for id in differences[1]])

        return adjustment_foreign_year

    def assignPayback(self,transacts):
        all_transacts = getAllTransacts()
        assigns = []
        for id,action in transacts.items():
            if action.tag == "Rückzahlung":
                print(action.id,action.date,action.recipient,action.reference,action.amount,action.tag)
                pb = int(input("of which action?"))
                # pb = int(action.pb_assign)
                if pb > 0:
                    in_advance_action = all_transacts[pb]
                    if in_advance_action.pb_assign is None:
                        in_advance_action.pb_assign = []
                    elif type(in_advance_action.pb_assign) is str:
                        #if len(in_advance_action.pb_assign) == 0:
                        in_advance_action.pb_assign = []
                        #else:
                            #in_advance_action.pb_assign = ast.literal_eval(in_advance_action.pb_assign)
                    if not (action.id in in_advance_action.pb_assign):
                        in_advance_action.pb_assign.append(action.id)
                        assigns.append(in_advance_action)
                    action.pb_assign = [0]
                    assigns.append(action)
                    print("In advance", in_advance_action.id, in_advance_action.date, in_advance_action.recipient,
                          in_advance_action.reference, in_advance_action.amount, in_advance_action.tag,
                          in_advance_action.pb_assign)
                elif pb == -1:
                    break

                else:
                    action.pb_assign = [-1]
                    assigns.append(action)
                print("Payback",action.id,action.date,action.recipient,action.reference,action.amount,action.tag,action.pb_assign)
                print()
        for in_advance_action in assigns:
            in_advance_action.pb_assign = str(in_advance_action.pb_assign)
            print(object2list(in_advance_action))
        print(assigns)
        updateMany(assigns)

    def getAccounts(self):
        accounts = {}
        for id, action in self.yearly_transacts.items():
            if action.account.name not in accounts:
                accounts[action.account.name] = action.account
        return accounts

    def getBalances(self):
        new_year = datetime(self.year_no, 1, 1)

        balances = {}
        for account_name, account in self.accounts.items():
            account_transacts = []
            for id, action in self.yearly_transacts.items():
                if action.account.name == account_name:
                    account_transacts.append(action)

            transacts_list = sorted(account_transacts, key=lambda action: action.date)
            dates = [action.date for action in transacts_list]

            base_date = datetime(self.year_no,1,1)

            balance_list = []

            for (date_iter, balance_iter) in reversed(account.balances):
                if date_iter < base_date:
                    balance = balance_iter
                    balance_list = [balance]
                    break
            if len(balance_list) == 0:
                balance = 0
                balance_list = [balance]
            dates.insert(0, new_year)

            for action in transacts_list:
                balance += round(action.amount, 2)
                balance_list.append(round(balance, 2))

            balances[account_name] = (dates, balance_list)

        all_balances = []
        all_base_balances = 0
        all_balances_dates = []
        for account_name, (dates, balance_list) in balances.items():
            all_base_balances += balance_list[0]

        all_balances.append(round(all_base_balances,2))
        all_balances_dates.append(dates[0])

        ignore_accounts = []

        balance = all_base_balances
        transacts_list = sorted(self.yearly_transacts.values(), key=lambda action: action.date)
        count = 0
        for action in transacts_list:
            if action.account.name not in ignore_accounts:
                balance += action.amount
                if count < 7:
                    count += 1
                else:
                    count = 0
                    all_balances.append(round(balance, 2))
                    all_balances_dates.append(action.date)

        all_balances.append(round(balance, 2))
        all_balances_dates.append(action.date)

        balances["Alle"] = (all_balances_dates,all_balances)

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
            else:
                rest += float(tags_temp[tag.rstrip()])

        rest = round(rest, 2)
        tags['Rest'] = rest

        tags = OrderedDict(sorted(tags.items(), key=lambda x: x[1]))

        return tags


    def paybackPerTag(self,transacts):
        in_advances = {}
        for id,action in transacts.items():
            if type(action.pb_assign) is list:
                if len(action.pb_assign) > 0:
                    if action.pb_assign[0] > 0:
                        tag = action.tag
                        sub_tag = action.sub_tag
                        if not (tag in in_advances):
                            in_advances[tag] = {sub_tag: 0}
                        elif not (sub_tag in in_advances[tag]):
                            in_advances[tag][sub_tag] = 0
                        for pb_assign in action.pb_assign:
                            in_advances[tag][sub_tag] += self.all_transacts[pb_assign].amount
                            if sub_tag == "":
                                self.tagStruct[tag]["Rest"] += self.all_transacts[pb_assign].amount
                            else:
                                self.tagStruct[tag][sub_tag] += self.all_transacts[pb_assign].amount
                        #in_advances[tag] = round(in_advances[tag], 2)
        self.total_spent = 0
        for tag in self.tagStruct.values():
            for subtag in tag.values():
                self.total_spent += subtag

        self.total_spent = round(self.total_spent,2)
        return in_advances

    def recomputeTags(self):
        for tag, in_advance_amount in self.in_advances.items():
            if tag in self.tags.keys():
                self.tags[tag] -= round(in_advance_amount, 2)
                if self.tags[tag] == 0:
                    self.tags.pop(tag)
                elif self.tags[tag] < 20:
                    self.tags["Rest"] += self.tags[tag]
                    self.tags.pop(tag)
            else:
                self.tags["Rest"] -= round(in_advance_amount, 2)
                if self.tags["Rest"] == 0:
                    self.tags.pop("Rest")
        self.total_spent = -sum([amount if amount > 0 else 0 for amount in self.tags.values()])


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

    def getYearlyAccountsBalance(self):
        total_beginning = 0
        total_end = 0
        accounts_balance = {}
        ignore_accounts = ["Alle"]
        income = 0
        expense = 0
        transfer = 0
        debt = 0
        treated_count = 0
        count = 0
        for id,action in self.yearly_transacts.items():
            if action.account.name not in ignore_accounts:
                if action.amount >= 0:
                    income += action.amount
                    count += 1
                else:
                    expense -= action.amount
                if action.tag == "Kapitaltransfer" and action.amount < 0:
                    transfer += abs(action.amount)
                if action.tag == "Kredit":
                    debt += action.amount
                treated_count += 1
        print(income,count)
        accounts_balance["income"] = round(income, 2)
        accounts_balance["expense"] = round(expense, 2)
        accounts_balance["transfer"] = round(transfer, 2)
        accounts_balance["treated"] = (treated_count, len(self.yearly_transacts))
        accounts_balance["debt"] = debt
        for account_name,(dates, balance_list) in self.balances.items():
            if account_name not in ignore_accounts:
                total_beginning += balance_list[0]
                total_end += balance_list[-1]

        accounts_balance["total_beginning"] = round(total_beginning,2)
        accounts_balance["total_end"] = round(total_end,2)

        return accounts_balance

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
        fig.data[0].texttemplate = "%{label} <br> %{value:.2f} € <br> %{percentEntry}"
        file_name = "Expenses" + str(self.year_no)
        graph_path = prepare4Saving(file_name, vector)
        fig.write_image(graph_path)

    def createNestedExpensesTreemap(self,vector=True):
        print("Drawing expenses treemap for",self.file_name)
        parents = ["","all"]
        labels = [" ","Rest"]
        values = [0,0]
        ids = ["all","rest"]
        small_tags = 0
        for tag,sub_tags in self.tagStruct.items():
            total = sum([-round(value,2) for sub_tag,value in sub_tags.items()])
            if total > -0.005*self.total_spent:
                parents.append("all")
                t_id = "t_"+tag
                ids.append(t_id )
                small_amounts = 0
                small_amounts_labels = []
                for sub_tag,value in sub_tags.items():
                    if sub_tag != "Rest":
                        if -round(value,2) < - 0.0025 * self.total_spent:
                            small_amounts -= round(value,2)
                            small_amounts_labels.append(sub_tag)
                if "Rest" in sub_tags.keys():
                    values.append(round(-sub_tags["Rest"]+small_amounts,2))
                elif small_amounts > 0:
                    values.append(round(small_amounts,2))
                else:
                    values.append(0)
                if len(sub_tags)-len(small_amounts_labels) == 1:
                    labels.append(tag)
                else:
                    labels.append(tag + "&nbsp;&nbsp;"+ str(round(total / -self.total_spent * 100)) +"%<br>"+ str(round(total, 2)) + " €" )
                for sub_tag,value in sub_tags.items():
                    if sub_tag != "Rest" and sub_tag not in small_amounts_labels:
                        labels.append(sub_tag)
                        parents.append(t_id)
                        values.append(-round(value,2))
                        ids.append(t_id +"_st_"+sub_tag)
            else:
                small_tags += total
        values[1] = round(small_tags,2)
        fig = go.Figure(go.Treemap(
            ids = ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues='remainder'
        ))
        if type(self) is Year:
            width=510
            height=710
        else:
            width = 500
            height = 550
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),width=width, height=height)#,uniformtext=dict(minsize = 5, mode ='show'))

        fig.data[0].texttemplate = "%{label} <br>%{value} €<br>%{percentEntry} "
        #fig.show()
        graph_path = prepare4Saving(self.file_name, vector)
        fig.write_image(graph_path)



    def getTagStructure(self):
        strct = {}
        for id,action in self.lean_transacts.items():
            if action.tag in strct.keys():
                if action.sub_tag in strct[action.tag].keys() and action.sub_tag != "":
                    total = strct[action.tag][action.sub_tag]
                    total += action.amount
                    strct[action.tag][action.sub_tag] = total
                elif action.sub_tag != "":
                    strct[action.tag][action.sub_tag] = action.amount
                else:
                    if "Rest" in strct[action.tag].keys():
                        strct[action.tag]["Rest"] += action.amount
                    else:
                        strct[action.tag]["Rest"] = action.amount
            elif action.sub_tag != "":
                strct[action.tag] = {action.sub_tag: action.amount}
            else:
                strct[action.tag] = {"Rest": action.amount}
        return strct

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

        ignore_accounts = []
        self.balances_plot = {}

        for account_name, balances_tuples in self.balances.items():
            if account_name not in ignore_accounts:
                balance_list = balances_tuples[1]
                spectres[account_name] = (min(balance_list), max(balance_list))
                self.balances_plot[account_name] = balances_tuples
        outlier_accounts = []

        for account_name, spectre in spectres.items():
            if spectre[0] > 6000:
                outlier_accounts.append(account_name)
        #for account_name, spectre in spectres.items():
        #    if spectre[1] - spectre[0] >= 7000:
        #        outlier_accounts = []
        dpi = 500
        if len(outlier_accounts) > 0:
            f, axs = plt.subplots(2, 1, sharex=True, figsize=(10,6))
            f.subplots_adjust(hspace=0.1)  # adjust space between axes
        else:
            f = plt.figure(figsize=(10,6))
            axs = [plt.gca()]

        maxs = []
        mins = []
        maxs_out = []
        mins_out = []
        for account_name, spectre in spectres.items():
            if account_name not in outlier_accounts:
                mins.append(spectre[0])
                maxs.append(spectre[1])
            else:
                mins_out.append(spectre[0])
                maxs_out.append(spectre[1])
        y_lim = (min(mins), max(maxs) + 1000)
        if len(outlier_accounts) > 0:
            y_lim_out = (min(mins_out)-1000, max(maxs_out)+1000)
        for account_name, balances_dict in self.balances_plot.items():
            dates = [val for val in balances_dict[0] for _ in (0, 1)][1:]
            balance_list = [val for val in balances_dict[1] for _ in (0, 1)][:-1]

            new_year = dates[0]

            if len(balances_dict) > 0:
                for ax in axs:
                    p, = ax.plot(dates, balance_list, label=account_name,lw=2)
                    arrow_props = dict(arrowstyle='-', color=p.get_color(), lw=2, ls='--')
                    ax.annotate(str(balance_list[0]).replace(".", ",") + " €",color = p.get_color(), fontsize=12,
                                xy=(dates[0], balance_list[0]),
                                xytext=(dates[0] - relativedelta(days=15), balance_list[0]),
                                arrowprops=arrow_props, va="center", ha="right")
                    ax.annotate(str(balance_list[-1]).replace(".", ",") + " €",color = p.get_color(), fontsize=12,
                                xy=(dates[-1], balance_list[-1]),
                                xytext=(dates[-1] + relativedelta(days=15), balance_list[-1]),
                                arrowprops=arrow_props, va="center", ha="left")

                # zoom-in / limit the view to different portions of the data
                if len(outlier_accounts) > 0:
                    axs[0].set_ylim(y_lim_out)  # outliers only
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

    def plotComparisonBarChartForYears(self, year_to_stop=None):
        print("Drawimg Comparison Bar Chart for",self.year_no)
        first_year = list(self.all_transacts.values())[0].date.year if year_to_stop is None else year_to_stop
        years = []
        for past_year_no in range(first_year, self.year_no):
            years.append(Year(past_year_no))
        years.append(self)
        all_tags = getAllTags(years)
        expense_tag_per_year_completed = getExpensesPerTagOverTheYears(years, all_tags)
        plotComparisonBarChart(expense_tag_per_year_completed, all_tags)

    def checkTransfers(self):
        total = 0
        for id,action in self.transfer_transacts.items():
            #print(action.id,action.date,action.recipient,action.amount)
            total += round(action.amount,2)
            print("After",action.id,action.date,"total is",round(total,2))
        return round(total,2)

def createYearlySheet(year_no,folder,redraw_graphs=True,gui=None):
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
    year = Year(year_no,projection=projection,setBudget=setBudget,budget=budget,deduct_in_advances=True)
    if gui is not None:
        gui.yearlySheetCreationProgressBar.setValue(20)
        #gui.progressBarLabel.setText("Erstellen des Budget Diagramms für "+str(year_no))
    if redraw_graphs:
        if not setBudget:
            year.createBudgetTreemap()
        year.plotComparisonBarChartForYears(year_to_stop=2019)
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(40)
            #gui.progressBarLabel.setText("Erstellen des Ausgaben Diagramms für " +str(year_no))
        year.createNestedExpensesTreemap()
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(60)
            #gui.progressBarLabel.setText("Erstellen der jährlichen Bilanz PDF für " +str(year_no))
        year.createBalancePlot()
        if gui is not None:
            gui.yearlySheetCreationProgressBar.setValue(80)
    createPDF(year,folder,setBudget=setBudget)
    if gui is not None:
        gui.yearlySheetCreationProgressBar.setValue(100)
        #gui.progressBarLabel.setText("Jährliche Bilanz PDF fertig!")

def executeCreateSingleYear(year,folder,redraw_graphs=True,gui=None):
    print("Yearly Balance Sheet Creation started")
    new_thread = threading.Thread(target=createYearlySheet,args=(year,folder,redraw_graphs,gui,))
    new_thread.start()

def computeBalances():
    all_transacts = getAllTransacts()
    for account in accounts:
        account.getAccountTransacts(all_transacts)
        account.getBalances()

if __name__ == '__main__':
    home = Path.home()
    computeBalances()
    #createYearlySheet(2022,home/"Documents"/"Balance Sheets",redraw_graphs=True)
    #computeBalances()
    year_no = 2022
    year = Year(year_no)
    #print(json.dumps(year.tagStruct, sort_keys = True, indent = 4))
    #year.createNestedExpensesTreemap()
    #year.getForeignYearPaybacks()
    #year.assignPayback(year.yearly_transacts)
    #print(year.checkTransfers())