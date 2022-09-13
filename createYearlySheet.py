from createBalanceSheets import drawImage,prepare4Saving

from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from operator import itemgetter
from pathlib import Path
from database_api import mm_dir_path
import math

def formatFloat(num):
    return "{:,.2f} €".format(num).replace(","," ").replace(".",",")

def createPDF(year,pre_year,folder,setBudget=False):
    file_name = Path(folder) / str("Yearly Sheet"+str(year.year_no)+".pdf")

    graph_path_budget = mm_dir_path / "Graphs" /str("Budget"+str(year.year_no)+".svg")
    graph_path_expenses = mm_dir_path / "Graphs" /str("Expenses"+str(year.year_no)+".svg")
    graph_path_balances = mm_dir_path / "Graphs" /str("Balances"+str(year.year_no)+".svg")

    document_title = "Balance Sheet "+str(year.year_no)
    title = "Balance Sheet "+str(year.year_no)

    total_spent = -year.total_spent
    pers_spent = -year.pers_spent
    budget = year.budget

    pdf = canvas.Canvas(str(file_name))
    pdf.setTitle(document_title)


    # Page 1

    drawImage(graph_path_expenses, pdf, 45, 75, 1)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(300, 790, title)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 50, "Gesamtausgaben (ohne Vorauszahlungen): " + formatFloat(pers_spent))

    pdf.showPage()

    #Page 2

    drawCategoryTable(pdf, year.tags,x=50,y=765)

    drawPerMonthTable(pdf, year, x=50, y=245)

    pdf.showPage()

    #Page 3
    pdf.setFont("Helvetica-Bold", 18)
    if not setBudget:
        drawImage(graph_path_budget, pdf, 45, 380, 1)
    pdf.drawString(50, 350, "Gesamtbudget: " + formatFloat(budget))


    pdf.drawString(50, 775, "Budget")
    pdf.line(50, 773, 113, 773)



    pdf.showPage()

    #Page 4
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 775, "Budget")
    drawImage(graph_path_balances, pdf, 15, 450, 0.60)

    drawBalanceTable(pdf, year, x=50, y=225)

    drawAccountBalanceTable(pdf, year, 300, 225)

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

    pdf.setFont("Helvetica", 12)

    def coord(x, y, height, unit=1):
        x, y = x * unit, height - y * unit
        return x, y

    for index0,ar in enumerate(data):
        rowHeights = len(ar) * [row_height]
        max_value = max(ar,key=lambda item:item[1])[1]
        col_width_value = 45+10*math.log10(max_value)

        max_tag = len(max(ar, key=lambda item: len(item[0]))[0])
        col_width_tag = max_tag*8
        colWidths = [col_width_tag, col_width_value]
        for index,element in enumerate(ar):
            value = formatFloat(element[1])
            ar[index][1] = value
            tag = ar[index][0]
            ar[index][0] = tag.replace("\n"," ")

        t = Table(ar, rowHeights=rowHeights,colWidths=colWidths)
        t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
        #w, h = t.wrap(width, height)
        t.wrapOn(pdf, width, height)
        t.drawOn(pdf, x+(col_width_tag+col_width_value+5)*index0, y-15-row_height*len(ar))

def drawPerMonthTable(pdf,year,x,y):
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(x, y, 'Top Ausgaben pro Monat')
    pdf.line(x, y - 2, x + 215, y - 2)
    perMonth = list(year.perMonth.items())
    perMonth_pre_year = list(year.perMonth_pre_year.items())
    data = [["",str(year.year_no),str(year.year_no-1)]]
    for ((tag,value),(pre_tag,pre_value)) in zip(perMonth,perMonth_pre_year):
        data.append([tag,value,pre_value])
    row_height = 28

    max_value = max(max(data[1:], key=lambda item: item[1])[1],max(data[1:], key=lambda item: item[2])[2])
    col_width_value = 45 + 10 * math.log10(max_value)

    max_tag = len(max(data, key=lambda item: len(item[0]))[0])
    col_width_tag = max_tag * 8
    colWidths = [col_width_tag, col_width_value, col_width_value]
    rowHeights = len(data) * [row_height]
    for index,element in enumerate(data):
        if index > 0:
            data[index][1] = (formatFloat(element[1]) if element[1] > 0 else "-  €")
            data[index][2] = (formatFloat(element[2]) if element[2] > 0 else "-  €")
    t = Table(data, rowHeights=rowHeights,colWidths=colWidths)
    t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y-15-row_height*len(data))


def drawBalanceTable(pdf, year, x, y):
    total_spent= -year.total_spent
    total_spent_len = year.total_spent_len
    budget = year.budget
    budget_len = year.budget_len
    payback = year.payback
    payback_len = year.payback_len
    in_advance_payback_len = year.in_advance_payback_len
    pers_spent = -year.pers_spent
    transfer_transacts_len = year.transfer_transacts_len
    if not year.setBudget:
        sold,sold_len = year.total_sold,year.total_sold_len
    else:
        sold,sold_len = 0,0

    treated, treated_total = total_spent_len + budget_len + payback_len + in_advance_payback_len + transfer_transacts_len + sold_len, len(year.yearly_transacts)

    data = [['Transaktionen', str(treated)+ " von " +str(treated_total)],
            ['Gesamtausgaben', formatFloat(total_spent)],
            ['Rückzahlung', formatFloat(payback)],
            ['Netto Ausgaben*', formatFloat(pers_spent)],
            ['Grundeinkommen', formatFloat(round(budget-sold,2))],
            ['Verkauf', formatFloat(sold)]]
    balance = round(payback + budget - total_spent, 2)

    style = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
             ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('FONTSIZE', (0, 0), (-1, -1), 15),
             ]
    if balance > 0:
        balance_str = "Suffizit"
        style.append(['BACKGROUND', (0, 6), (1, 6), colors.lightgreen])
    else:
        balance_str = "Defizit"
        style.append(['BACKGROUND', (0, 6), (1, 6), colors.rgb2cmyk(255, 150, 110)])

    data.append([balance_str, formatFloat(balance)])
    row_height = 25
    rowHeights = len(data) * [row_height]
    pdf.line(x, y + row_height*(len(data)+1)+10, x + 480, y + row_height*(len(data)+1)+10)
    pdf.drawString(x, y + 6 + row_height*len(data), 'Bilanz')
    pdf.line(x, y + 4 + row_height*len(data), x + 55, y + 4 + row_height*len(data))
    t = Table(data, rowHeights=rowHeights)
    t.setStyle(TableStyle(style))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y)
    return t

def drawAccountBalanceTable(pdf, year, x, y):
    account_expense = year.accounts_balance["expense"]
    account_income = year.accounts_balance["income"]
    transfer = year.accounts_balance["transfer"]
    total_beginning = year.accounts_balance["total_beginning"]
    total_end = year.accounts_balance["total_end"]
    debt = year.accounts_balance["debt"]

    treated,treated_total = year.accounts_balance["treated"]

    data = [['Transaktionen', str(treated)+ " von " +str(treated_total)],
            ['Auf Konten eingangen', formatFloat(account_income)],
            ['Von Konten abgezogen', formatFloat(account_expense)],
            ['davon Kapitaltransfer', formatFloat(transfer)],
            ['Anpassung Rückzahlungen', formatFloat(year.adjustment_foreign_year)]]

    last_row = 7

    if debt > 0:
        data.append(['Schulden aufgenommen', formatFloat(debt)])
        last_row = 8

    data.extend([['Anfangsvermögen', formatFloat(total_beginning)], ['Endvermögen', formatFloat(total_end)]])
    balance = round(total_end-total_beginning-debt+year.adjustment_foreign_year, 2)

    style = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('FONTSIZE', (0, 0), (-1, -1), 15),
             ]
    if balance > 0:
        balance_str = "Suffizit"
        style.append(['BACKGROUND', (0, last_row), (1, last_row), colors.lightgreen])
    else:
        balance_str = "Defizit"
        style.append(['BACKGROUND', (0, last_row), (1, last_row), colors.rgb2cmyk(255, 150, 110)])

    data.append([balance_str, formatFloat(balance)])
    row_height = 25
    rowHeights = len(data) * [row_height]
    t = Table(data, rowHeights=rowHeights)
    t.setStyle(TableStyle(style))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y)
    return t

def drawAccountExpensesTable(pdf, year, x, y):
    balance_per_account = {}


    data = [['Auf Konten eingangen', formatFloat(budget)],
            ['Von Konten abgezogen', formatFloat(total_spent)],
            ['Anfangsvermögen', formatFloat(total_beginning)],
            ['Endvermögen', formatFloat(total_end)]]
    balance = round(total_end-total_beginning, 2)

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

    data.append([balance_str, formatFloat(balance)])
    row_height = 25
    rowHeights = len(data) * [row_height]
    #pdf.line(x, y + row_height*(len(data)+1)+10, x + 480, y + row_height*(len(data)+1)+10)
    #pdf.drawString(x, y + 6 + row_height*len(data), 'Konten Bilanz')
    #pdf.line(x, y + 4 + row_height*len(data), x + 120, y + 4 + row_height*len(data))
    t = Table(data, rowHeights=rowHeights)
    t.setStyle(TableStyle(style))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y)
    return t