from database_api import *
from Year import Year
from Month import Month
import matplotlib.pyplot as plt
from itertools import islice
import locale
import pandas as pd
import threading

locale.setlocale(locale.LC_ALL, '') 



def computePerMonthPerTagExpenses(months_years,tags,last_year=2022):
    expense_dict = {}
    for tag in tags:
        if type(tag) is tuple:
            tag_label = tag[0]+" - "+tag[1]
        else:
            tag_label = tag
        expense_dict[tag_label] = {}   
        for months in months_years:
            year_no = months[0].year_no
            if year_no <= last_year:
                expense_dict[tag_label][year_no] = {}
                for month in months:
                        if type(tag) is tuple: 
                            if tag[0] in month.tagStruct.keys():
                                if tag[1] in month.tagStruct[tag[0]].keys():
                                    expense_dict[tag_label][year_no][month.month_name] = -round(month.tagStruct[tag[0]][tag[1]],2)
                                else:
                                    expense_dict[tag_label][year_no][month.month_name] = 0
                            else:
                                expense_dict[tag_label][year_no][month.month_name] = 0
                        else:
                            if tag in month.tagStruct.keys():
                                expense_dict[tag_label][year_no][month.month_name] = -round(sum([month.tagStruct[tag][sub_tag] for sub_tag in month.tagStruct[tag].keys()],2))                            
                            else:
                                expense_dict[tag_label][year_no][month.month_name] = 0
    return expense_dict

def computePerMonthExpenses(months_years,tags,last_year=2022):
    expense_dict = {}
    for months in months_years:
        year_no = months[0].year_no
        if year_no <= last_year:
            expense_dict[year_no] = {}
            for month in months:
                expense_dict[year_no][month.month_name] = -month.total_spent
    return expense_dict

def plotPerTagExpenses(expense_dict,year,n_plots=4):
    fig,axs = plt.subplots(2,2,figsize=(13,9))
    for i,(tag,expenses) in enumerate(expense_dict.items()):
        ax = axs[i//2][i%2]
        ax.yaxis.set_major_formatter('{x:n} €')
        ax.set_title(tag, fontsize = 20)
        ax.tick_params(axis='x', which='major', labelsize=12,rotation=45)
        ax.tick_params(axis='y', which='major', labelsize=12)
        for year,months in expenses.items():
            values = []
            labels = []
            for month,value in months.items():
                values.append(value)
                labels.append(month)
            avg = round(sum(values)/len(values),2)
            ax.plot(labels, values, label = str(year),lw=3)
    fig.tight_layout()
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=15)
    fig.savefig("/Users/loris/src/Python/MoneyManager/Graphs/monthlyExpensesPerTag"+str(year)+".svg", bbox_inches="tight", dpi='figure')

def main(latest_year):
	#computeBalances()
	years = []
	for i in range(2019,latest_year+1):
		years.append(Year(i))

	months_years = []
	for year in years:
	    months = []
	    for i in range(1,13):
	        month = Month(i,year.year_no)
	        if len(month.monthly_transacts) > 0:
	            months.append(month)
	    months_years.append(months)
	print("Creating every month done")
	all_tags_yearly = {}

	for y in years:
	    if y.year_no == latest_year:
	       year = y  
	for tag,subtags in year.tagStruct.items():
	    total = 0
	    for subtag, value in subtags.items():
	        total -= value
	    all_tags_yearly[tag] = round(total,2)
	sorted_tags_yearly = {k: v for k, v in sorted(all_tags_yearly.items(), key=lambda item: item[1],reverse=True)}

	tags = [tag for tag in sorted_tags_yearly]
	tags = tags[:4]
	expense_dict = computePerMonthPerTagExpenses(months_years,tags,last_year=latest_year)
	all_tags_expense_dict = computePerMonthExpenses(months_years,tags,last_year=latest_year)
	print("Creating plots..")
	plotPerTagExpenses(expense_dict,latest_year)  
	print("Monthly Per Tag Expenses Chart done!")


def executePerMonthPerTagExpenses(latest_year):
    print("Monthly Per Tag Expenses Chart Creation started")
    new_thread = threading.Thread(target=main,args=(latest_year,))
    new_thread.start()

if __name__ == '__main__':
	main(2023)