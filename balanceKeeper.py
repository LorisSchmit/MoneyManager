from Year import Year
from Month import Month
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from datetime import datetime
from matplotlib import dates as mdates
from dateutil.relativedelta import relativedelta


def getAccounts(transacts):
    accounts = {}
    for id,action in transacts.items():
        if action.account.name not in accounts:
            accounts[action.account.name] = action.account
    return accounts

def balancePerYear(transacts,balances):
    num_transacts = {}
    for id,action in transacts:
        balances[action.account.name] += action.amount
        num_transacts[action.account.name] += 1
        if action.tag == "Kapitaltransfer":
            if action.recipient.find("PayPal") != -1:
                balances["PayPal"] -= action.amount
            elif action.recipient.find("DECOMPTE VISA") != -1:
                balances["Visa"] -= action.amount

def balancePerMonth(months,balances,num_transacts):
    for month_no, month in months.items():
        for id, action in month.monthly_transacts.items():
            balances[action.account.name] += round(action.amount,2)
            num_transacts[action.account.name] += 1
            if action.tag == "Kapitaltransfer":
                if action.recipient.find("PayPal") != -1:
                    balances["PayPal"] -= action.amount
                elif action.recipient.find("DECOMPTE VISA") != -1:
                    balances["Visa"] -= action.amount
        print("Balance for Month", month.month_name, month.year_no, ":", round(balances["Girokonto"],2))
        print("Num transacts",num_transacts["Girokonto"])
    return balances,num_transacts

def getCapitalTransfers(transacts):
    paypal_balance = 0
    visa_balance = 0
    for id, action in transacts:
        if action.tag == "Kapitaltransfer":
            if action.recipient.find("PayPal") != -1:
                paypal_balance += action.amount
            if action.recipient.find("DECOMPTE VISA") != -1:
                visa_balance += action.amount
            #print(action.date,action.recipient,action.reference,action.amount, action.account)
        if action.account.name == "PayPal" and action.amount > 0:
            paypal_balance -= action.amount

    return paypal_balance,visa_balance

def analyzeAccount(transacts,account_name):
    total_income = 0
    total_spent = 0
    for id,action in transacts:
        if action.account.name == account_name:
            if action.amount >= 0:
                total_income += abs(action.amount)
                print("Income:",action.date,action.recipient,action.amount,action.date)
            else:
                total_spent -= action.amount
                print("Expense",action.date, action.recipient, action.amount, action.date)
        if action.recipient.find("PayPal") !=-1:
            total_income += abs(action.amount)
            print("Income:",action.date, action.recipient, action.amount, action.date)

    print("Total spent for",account_name,total_spent)
    print("Total income for",account_name,total_income)

def getBalances(year_no):
    year = Year(year_no, projection=False, pre_year=False, setBudget=False)

    transacts = year.yearly_transacts

    accounts = getAccounts(transacts)

    new_year = datetime(year_no, 1, 1)

    balances = {}
    for account_name,account in accounts.items():
        account_transacts = []
        for id,action in transacts.items():
            if action.account.name == account_name:
                account_transacts.append(action)

        transacts_list = sorted(account_transacts, key=lambda action: action.date)
        dates = [action.date for action in transacts_list]

        if new_year in account.balance_base:
            balance = account.balance_base[new_year]
            balance_list = [balance]
            dates.insert(0,new_year)
        else:
            print("No balance base available")
            continue

        for action in transacts_list:
            balance += round(action.amount,2)
            balance_list.append(round(balance,2))

        balances[account_name] = (dates,balance_list)

    return balances

def plotBalances(balances,year_no):
    new_years_eve = datetime(year_no, 12, 31, 23, 59)
    spectres = {}

    ignore_accounts = ["Visa","PayPal"]

    for ignore_account in ignore_accounts:
        balances.pop(ignore_account)

    for account_name,balances_dict in balances.items():
        balance_list = balances_dict[1]
        spectres[account_name] = (min(balance_list),max(balance_list))
    outlier_accounts = []
    for account_name_i, spectre_i in spectres.items():
        diff = 0
        for account_name_j, spectre_j in spectres.items():
            if account_name_i != account_name_j:
                diff += abs(spectre_i[0] - spectre_j[1])  #min(i) - max(j)
                diff += abs(spectre_j[0] - spectre_i[1])  #min(j) - max(i)
        print(account_name_i,diff)
        if diff/(2*(len(spectres.keys())-1)) > 10000:
            outlier_accounts.append(account_name_i)

    if len(outlier_accounts) > 0:
        f, axs = plt.subplots(len(outlier_accounts)+1, 1, sharex=True, figsize=(12, 7))
        f.subplots_adjust(hspace=0.1)  # adjust space between axes
        maxs = []
        mins = []
        for account_name, spectre in spectres.items():
            if account_name not in outlier_accounts:
                mins.append(spectre[0])
                maxs.append(spectre[1])
        y_lim = (min(mins), max(maxs) + 1000)
    else:
        f,axs = plt.figure(figsize=(12, 7))

    for account_name,balances_dict in balances.items():
        dates = balances_dict[0]
        balance_list = balances_dict[1]

        new_year = dates[0]

        if len(balances_dict)>0:
            for ax in axs:
                p, = ax.plot(dates,balance_list,label=account_name)
                arrow_props = dict(arrowstyle='-', color=p.get_color(), lw=1.5, ls='--')
                ax.annotate(str(balance_list[0]).replace(".",",")+" €",fontsize=12, xy=(dates[0], balance_list[0]), xytext=(dates[0]+relativedelta(days=15), balance_list[0]),
                             arrowprops=arrow_props, va="center",ha="left")
                ax.annotate(str(balance_list[-1]).replace(".",",")+" €",fontsize=12, xy=(dates[-1], balance_list[-1]), xytext=(dates[-1]+relativedelta(days=15), balance_list[-1]),
                             arrowprops=arrow_props, va="center",ha="left")


            # zoom-in / limit the view to different portions of the data
            if len(outlier_accounts) > 0:
                axs[0].set_ylim(spectres[outlier_accounts[0]][0]-750, spectres[outlier_accounts[0]][1]+750)  # outliers only
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
                axs[0].set_ylim(0, spectres[account_name][1] + 1000)  # most of the data
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
            sec_xaxis = ax.secondary_xaxis(-0.15)
            sec_xaxis.xaxis.set_major_locator(fmt_year)
            sec_xaxis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

            # Hide the second x-axis spines and ticks
            sec_xaxis.spines['bottom'].set_visible(False)
            sec_xaxis.tick_params(length=0, labelsize=12)

    plt.legend()
    plt.show()



def main():
    year_no = 2020
    year = Year(year_no,projection=False,pre_year=False,setBudget=False)
    months = {}

    for i in range(1, 13):
        months[i] = Month(i, year_no)

    transacts = year.yearly_transacts

    accounts = getAccounts(transacts)

    balances = {}
    num_transacts = {}

    for name,account in accounts.items():
        balances[name] = 0
        num_transacts[name] = 0

    balances["Girokonto"] = 0
    balances["Compte courant"] = 2033.93
    balances["Compte epargne"] = 16825.06

    print("Anfangssaldo:", balances)

    balances, num_transacts = balancePerMonth(months,balances,num_transacts)

    print("Endsaldo:", balances)

    print("Anzahl Umsätze",num_transacts)

    print()


if __name__ == '__main__':
    main()
    #plotBalances(2021)
    #year_no = 2021
    #balances = getBalances(year_no)
    #plotBalances(balances,year_no)