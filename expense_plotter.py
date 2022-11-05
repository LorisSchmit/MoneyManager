from database_api import *
from Year import *
from Month import *
import matplotlib.pyplot as plt


def plot(years):
    fig = plt.figure(figsize=(16,9))
    for year in years:
        months = [Month(i,year.year_no) for i in range(1,13)]
        values = []
        try:
            for month in months:
                values.append(-round(month.tagStruct["Essen"]["Lebensmittel"],2))
        except AttributeError:
            print("Gotcha")
        plt.plot(values,label=year.year_no)
        plt.legend()
    plt.show()



if __name__ == '__main__':
    computeBalances()
    year_20 = Year(2020)
    year_21 = Year(2021)
    year_22 = Year(2022)
    plot([year_20,year_21,year_22])