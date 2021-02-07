from createBalanceSheets import drawImage, drawBalanceTable

from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from operator import itemgetter

def createPDF(year):
    file_name = "Yearly Sheet"+str(year.year_no)+".pdf"

    graph_path_budget = "Graphs/Budget"+str(year.year_no)+".svg"
    graph_path_expenses = "Graphs/Expenses"+str(year.year_no)+".svg"

    document_title = "Balance Sheet "+str(year.year_no)
    title = "Balance Sheet "+str(year.year_no)

    total_spent = year.total_spent
    budget = year.total_budget

    pdf = canvas.Canvas(file_name)
    pdf.setTitle(document_title)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(300, 790, title)

    drawImage(graph_path_budget, pdf, -25, 510, 0.45)
    drawImage(graph_path_expenses, pdf, 245, 560, 0.45)

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(80, 430, "Budget: " + str(budget) + " €")
    pdf.drawString(320, 430, "Gesamtausgaben: " + str(total_spent) + " €")

    drawCategoryTable(pdf, year.tags)

    pdf.line(50,165,530,165)
    drawBalanceTable(pdf, budget, total_spent, year.payback, 50, 50)

    pdf.save()

def drawBigCategoryTable(tags):
    file_name = "Big Category Table 2020.pdf"
    pdf = canvas.Canvas(file_name)

    data = []
    for key in tags.keys():
        if key != "Rückzahlung":
            data.append([key,tags[key]])
    rowHeights = len(data) * [25]
    data = list(reversed(sorted(data, key=itemgetter(1))))
    for index,element in enumerate(data):
        value = str(element[1])+" €"
        data[index][1] = value
    t = Table(data, rowHeights=rowHeights)
    t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
    pdf.setFont("Helvetica", 18)
    pdf.drawString(100, 870, 'Ausgaben pro Kategorie')
    #pdf.line(350, 718, 546, 718)
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, 100, 850 - len(tags) * 25)
    pdf.save()

def drawCategoryTable(pdf,tags):
    tag_list = []
    for key in tags.keys():
        element = [key,tags[key]]
        tag_list.append(element)
    tag_list = list(reversed(sorted(tag_list, key=itemgetter(1))))
    data = []
    subdata = []
    mod0 = 0
    for index,element in enumerate(tag_list):
        mod = index//7
        if mod != mod0:
            data.append(subdata)
            subdata = []
        mod0 = mod
        subdata.append([element[0],element[1]])
    data.append(subdata)

    for index0,ar in enumerate(data):
        rowHeights = len(ar) * [25]
        for index,element in enumerate(ar):
            value = str(element[1])+" €"
            ar[index][1] = value
        t = Table(ar, rowHeights=rowHeights)
        t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('FONTSIZE', (0, 0), (-1, -1), 15),
                               ]))
        pdf.setFont("Helvetica", 18)
        pdf.drawString(50, 380, 'Ausgaben pro Kategorie')
        pdf.line(50, 378, 245, 378)
        t.wrapOn(pdf, 500, 300)
        t.drawOn(pdf, 50+170*index0, 180)