from reportlab.pdfgen import canvas
from reportlab.lib import colors
from operator import itemgetter
from pathlib import Path
from PIL import Image,EpsImagePlugin
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from pdfrw import PdfReader, PdfDict




import os

from commonFunctions import perWeek,readCSVtoObjectExpense,monthNumberToMonthName,total,perTag,defineFiles
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from database_api import *

from reportlab.platypus import Table, TableStyle

#from budget import getBudgetPerMonth,getBudget

home = str(Path.home())

def drawPDF(month_obj):
    file_name = home + "/Balance Sheets/"+str(month_obj.year_no)+"/"+str(month_obj.year_no)+"-"+str(month_obj.month)+".pdf"
    image_path = "Graphs/"+str(month_obj.year_no)+" - "+str(month_obj.month)+".png"
    document_title = str(month_obj.month)+" "+str(month_obj.year_no)
    title = month_obj.month_name + " " + str(month_obj.year_no)
    total_spent = month_obj.total_spent

    pdf = canvas.Canvas(file_name)

    myImage = Image.open(image_path)

    pdf.setPageCompression(0)
    pdf.drawInlineImage(myImage, 0, 400, width=400,height=400)


    pdf.setTitle(document_title)

    # drawImage(image_path,pdf,-10, 390,1)
    #page = PdfReader(image_path, decompress=False).pages[0]
    #xobj = pagexobj(page)
    #xobj_name = makerl(pdf, xobj)
    #pdf.translate(0, 150)
    #pdf.scale(1, 1)
    #pdf.doForm(xobj_name)

    drawCategoryTable(pdf,month_obj.tags)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(300, 780, title)

    drawWeeksTable(pdf,month_obj.weeks,int(month_obj.month),int(month_obj.year_no))

    pdf.line(50, 220, 540, 220)

    try:
        payback = -month_obj.tags["Rückzahlung"]
    except KeyError:
        payback = 0
    drawBalanceTable(pdf,month_obj.budget,-total_spent,payback,50,75)

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(50,35,"Gesamtausgaben: "+str(-total_spent)+" €")

    if not (str(month_obj.year_no) in os.listdir(home+"/Balance Sheets")):
        os.mkdir(home+"/Balance Sheets/"+str(month_obj.year_no))
    pdf.save()

def drawImage(image_path,pdf,x,y,scale):
    drawing = svg2rlg(image_path)
    drawing.scale(scale,scale)

    renderPDF.draw(drawing, pdf, x,y)

def drawWeeksTable(pdf,weeks,month,year):
    print("Drawing "+str(month)+" - "+str(year))
    data = []
    week_dates =[]
    for week in weeks.keys():
        start = week[0].strftime("%d/%m")
        end = week[1].strftime("%d/%m")
        if week[0].month == week[1].month:
            week_dates.append(start+" - "+end)
        elif (week[0].month < month and week[0].year == year) or (week[0].year < year):
            week_dates.append("    - " + end)
        elif week[1].month > month:
            week_dates.append(start + " -    ")
    data.append(week_dates)
    week_values = list(weeks.values())
    week_values_str = []
    for value in week_values:
        week_values_str.append(str(value)+" €")
    data.append(week_values_str)
    rowHeights = len(data)*[25]
    t=Table(data,rowHeights=rowHeights)
    t.setStyle(TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                           ('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                           ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]))
    pdf.setFont("Helvetica", 18)
    pdf.drawString(50, 320, 'Ausgaben pro Woche')
    pdf.line(50, 318, 225, 318)
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, 50, 250)

def drawCategoryTable(pdf,tags):
    data = []
    for key in tags.keys():
        if key.find("Rückzahlung") == -1:
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
    pdf.drawString(350, 720, 'Ausgaben pro Kategorie')
    pdf.line(350, 718, 546, 718)
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, 400, 700 - len(tags) * 25)

def drawBalanceTable(pdf,budget,spent,payback,x,y):
    data = [['Gesamtausgaben',str(spent)+" €"],
            ['Budget pro Monat', str(budget)+" €"],
            ['Rückzahlung', str(payback)+" €"]]
    balance = round(payback+budget-spent,2)

    style =[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('FONTSIZE', (0, 0), (-1, -1), 15),
                           ]
    if balance > 0 :
        balance_str = "Suffizit"
        style.append(['BACKGROUND', (0, 3), (1, 3), colors.lightgreen])
    else:
        balance_str = "Defizit"
        style.append(['BACKGROUND', (0, 3), (1, 3), colors.rgb2cmyk(255, 150, 110)])

    data.append([balance_str,str(balance)+" €"])

    rowHeights = len(data) * [25]
    pdf.drawString(x, y+110, 'Bilanz')
    pdf.line(x, y+108, x+50, y+108)
    t = Table(data,rowHeights=rowHeights)
    t.setStyle(TableStyle(style))
    t.wrapOn(pdf, 500, 300)
    t.drawOn(pdf, x, y)
    return t

def main():
    drawPDFCollection(2018)
    #drawPDF("",1,2019,2018)
if __name__ == "__main__":
    main()

