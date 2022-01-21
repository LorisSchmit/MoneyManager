from createBalanceSheets import drawImage

from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from operator import itemgetter
from pathlib import Path

def createPDF(year):
    print("Drawing yearly sheet for",year.year_no)
    home = str(Path.home())
    file_name = home+"/Balance Sheets/Yearly Sheet"+str(year.year_no)+".pdf"

    graph_path_budget = "Graphs/Budget"+str(year.year_no)+".svg"
    graph_path_expenses = "Graphs/Expenses"+str(year.year_no)+".svg"

    document_title = "Balance Sheet "+str(year.year_no)
    title = "Balance Sheet "+str(year.year_no)

    total_spent = -year.total_spent
    budget = year.budget

    pdf = canvas.Canvas(file_name)
    pdf.setTitle(document_title)


    # Page 1

    drawImage(graph_path_expenses, pdf, 45, 75, 1)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(300, 790, title)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 50, "Gesamtausgaben: " + str(total_spent) + " €")

    pdf.showPage()

    #Page 2

    drawCategoryTable(pdf, year.tags,x=50,y=775)

    drawPerMonthTable(pdf, year.perMonth, x=50, y=280)

    pdf.showPage()

    #Page 3
    pdf.setFont("Helvetica-Bold", 18)
    drawImage(graph_path_budget, pdf, 45, 380, 1)
    pdf.drawString(50, 350, "Gesamtbudget: " + str(budget) + " €")


    pdf.drawString(50, 775, "Budget")
    pdf.line(50, 773, 113, 773)

    drawBalanceTable(pdf,year, x=50, y=50)


    pdf.save()


def drawCategoryTable(pdf,tags,x,y,width=500,height=700):
    tag_list = []
    for key in tags.keys():
        if tags[key] > 0:
            element = [key,tags[key]]
            tag_list.append(element)
    tag_list = list(reversed(sorted(tag_list, key=itemgetter(1))))
    data = []
    subdata = []
    col_num = 3
    col_len = len(tag_list)//col_num
    col_len = (col_len+1 if len(tag_list)/col_num - col_len > 0 else col_len)
    for index,element in enumerate(tag_list):
        if index%col_len == 0 and index != 0:
            data.append(subdata)
            subdata = []
        subdata.append([element[0],element[1]])
    data.append(subdata)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(x, y, 'Ausgaben pro Kategorie')
    pdf.line(x, y-2, x+210, y-2)
    row_height = 28
    col_width_tag = 90
    col_width_value = 70
    pdf.setFont("Helvetica", 12)

    def coord(x, y, height, unit=1):
        x, y = x * unit, height - y * unit
        return x, y

    for index0,ar in enumerate(data):
        rowHeights = len(ar) * [row_height]
        colWidths = [col_width_tag,col_width_value]
        for index,element in enumerate(ar):
            value = str(element[1])+" €"
            ar[index][1] = value
            tag = ar[index][0]
            ar[index][0] = tag.replace("\n"," ")

        t = Table(ar, rowHeights=rowHeights,colWidths=colWidths)
        t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
        #w, h = t.wrap(width, height)
        t.wrapOn(pdf, width, height)
        t.drawOn(pdf, x+175*index0, y-20-row_height*len(ar))

def drawBalanceTable(pdf, year, x, y):
    pdf.line(x, y+160, x+480, y+160)
    spent = -year.total_spent
    budget = year.budget
    payback = year.payback
    if "Verkauf" in year.budget_tagged:
        sold = year.budget_tagged["Verkauf"]
    else:
        sold = 0

    data = [['Gesamtausgaben', str(spent) + " €"],
            ['Grundeinkommen', str(round(budget-sold,2)) + " €"],
            ['Verkauf', str(sold) + " €"],
            ['Rückzahlung', str(payback) + " €"]]
    balance = round(payback + budget - spent, 2)

    style = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('FONTSIZE', (0, 0), (-1, -1), 15),
             ]
    if balance > 0:
        balance_str = "Suffizit"
        style.append(['BACKGROUND', (0, 4), (1, 4), colors.lightgreen])
    else:
        balance_str = "Defizit"
        style.append(['BACKGROUND', (0, 4), (1, 4), colors.rgb2cmyk(255, 150, 110)])

    data.append([balance_str, str(balance) + " €"])

    rowHeights = len(data) * [25]
    pdf.drawString(x, y + 131, 'Bilanz')
    pdf.line(x, y + 127, x + 55, y + 127)
    t = Table(data, rowHeights=rowHeights)
    t.setStyle(TableStyle(style))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y)
    return t

def drawPerMonthTable(pdf,perMonth,x,y):
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(x, y, 'Top Ausgaben pro Monat')
    pdf.line(x, y - 4, x + 210, y - 4)
    tag_list = list(perMonth.items())
    data = []
    for index, element in tag_list:
        data.append([index,element])
    row_height = 28
    col_width_tag = 90
    col_width_value = 70
    rowHeights = len(data) * [row_height]
    colWidths = [col_width_tag,col_width_value]
    for index,element in enumerate(data):
        value = str(element[1])+" €"
        data[index][1] = value
        #tag = data[index][0]
        #data[index][0] = tag.replace("\n"," ")

    t = Table(data, rowHeights=rowHeights,colWidths=colWidths)
    t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y-20-row_height*len(data))
