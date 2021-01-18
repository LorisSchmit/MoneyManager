import csv
from Transaction import Transaction
import plotly.graph_objects as go
import chart_studio
from commonFunctions import total,readCSVtoObject,perTag,defineFiles,biggestTag
from database_api import *
#!

def showTags():
    for i in range(1,10):
        month = str(i)
        transacts = getTransacts(month,"2019")
        print(month+" : "+str(total(transacts)))
        tags = perTag(transacts)
        print(tags)
        print(biggestTag(tags))

def createGraphCollection(year, transacts):
    for month in range(1,13):
        monthly_transacts = getMonthlyTransacts(transacts,int(month),year)
        if len(monthly_transacts) > 0:
            tags = perTag(monthly_transacts)
            print(tags)
            tot = -total(monthly_transacts)
            print("tot : "+str(tot))
            max = biggestTag(tags)[1]
            print("max : "+str(max))
            createGraph(tags, month,year,tot,max,19)


def embedGraph():
    with open('token.txt', mode="r") as token_file:
        username = token_file.readline()
        api_key = token_file.readline()
    chart_studio.tools.set_credentials_file(username=username, api_key=api_key)

def createGraph(data,month,year,tot,max,font_size):
    labels = list(data.keys())
    values = list(data.values())
    rot_fact = (3/8-max/tot)*8*55
    if rot_fact<0:
        rot_fact = 0
    if rot_fact > 360:
        rot_fact-360
    layout = dict(showlegend=False,font=dict(size=font_size),margin=dict(l=0, r=0, t=0, b=0))
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)],layout=layout)
    fig.update_traces(textinfo='label',hoverinfo='percent+value',rotation=rot_fact,)
    #fig.show()
    fig.write_image("Graphs/"+str(year) +" - "+str(month )+".svg")

def createGraphsYear(year):
    transacts = getAllTransacts()
    createGraphCollection(year,transacts)


def main():
    year = 2020
    createGraphsYear(int(year))

if __name__ == "__main__":
    main()