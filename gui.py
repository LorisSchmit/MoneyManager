from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QStandardItemModel,QStandardItem,QPixmap
from PyQt6.QtCore import QDate,QSortFilterProxyModel,Qt,QPersistentModelIndex,QStringListModel,QTimer
from PyQt6 import uic
import threading
from collections import OrderedDict
import sys
import os
import subprocess
import json
import re
import xml.etree.ElementTree as ET

from pathlib import Path
from datetime import datetime

mm_dir_path = Path(__file__).parent
sys.path.append(mm_dir_path)

from Month import executeCreateSingleMonth, executeAssignPayback, Month
from Year import executeCreateSingleYear
from import_automation import activateImport,newSingleFile
from Account import Account,statementDetection, importAllAccounts,deleteAccount,exportAllAccounts,accounts
from database_api import getAllTransacts,importTable,deleteAllFromTable, writeTable
from tagger import unique_tags



class MainGUI(QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "mm_gui.ui", self)
        self.show()


        # Tab: Übersicht
        self.initTransactsTable()
        self.all_transacts = getAllTransacts()
        self.transactsTableView.setModel(self.model)

        self.transactsTableView.setColumnWidth(0, 40)
        self.transactsTableView.setColumnWidth(1, 75)
        self.transactsTableView.setColumnWidth(2, 200)
        self.transactsTableView.setColumnWidth(3, 200)
        self.transactsTableView.setColumnWidth(4, 55)
        self.transactsTableView.setColumnWidth(5, 50)
        self.transactsTableView.setSortingEnabled(True)
        self.allTransactsButton.clicked.connect(self.displayAllTransacts)
        self.refreshButton.clicked.connect(self.refreshTransacts)
        self.displayTransacts()

        # Tab: Import
        self.browseFolderButton.clicked.connect(self.selectFolder)

        self.importFolder = self.browseFolderEdit.text()
        self.importActive = False
        self.importThreadActive = False
        self.ICON_RED_LED = str(mm_dir_path/"images"/Path("led-red-on.png"))
        self.ICON_GREEN_LED = str(mm_dir_path/"images"/Path("green-led-on.png"))
        self.pixmap_red = QPixmap(self.ICON_RED_LED)
        self.pixmap_red = self.pixmap_red.scaled(18,18)
        self.pixmap_green = QPixmap(self.ICON_GREEN_LED)
        self.pixmap_green = self.pixmap_green.scaled(18, 18)
        self.ledLabel.setPixmap(self.pixmap_red)
        self.activateImportButton.clicked.connect(self.activateImportClicked)

        self.browseFileButton.clicked.connect(self.selectFile)
        self.importButton.clicked.connect(lambda: newSingleFile(str(self.browseFileEdit.text()), self))

        self.taggingTableWidget.setHorizontalHeaderLabels(['Datum', 'Sender', 'Referenz', 'Betrag'])
        self.taggingTableWidget.setColumnWidth(1, 150)
        self.taggingTableWidget.setColumnWidth(2, 300)
        self.tagReady = False
        self.saveTagReady = False
        self.notSaveTag = False
        self.taggingEnterButton.clicked.connect(self.tagEntered)
        self.taggingLineEdit.returnPressed.connect(self.taggingEnterButton.click)
        completer = QCompleter()
        self.taggingLineEdit.setCompleter(completer)
        self.completer_model = QStringListModel()
        completer.setModel(self.completer_model)
        self.completer_model.setStringList(unique_tags)
        self.saveTagButton.clicked.connect(self.saveTag)
        self.notSaveTagButton.clicked.connect(self.notSave)

        # Tab: Bilanz
        if self.balanceSheetFolderEdit.text() != "":
            self.balanceSheetFolder = self.balanceSheetFolderEdit.text()
        self.CreateBalanceButton.clicked.connect(lambda: executeCreateSingleMonth(int(self.monthEdit.text()), int(self.yearEdit.text()),self.balanceSheetFolder,gui=self))
        self.showBalanceSheetButton.clicked.connect(self.openBalanceSheet)
        self.createYearlyBalanceButton.clicked.connect(lambda: executeCreateSingleYear(int(self.yearlySheetEdit.text()),self.balanceSheetFolder,redraw_graphs=True,gui=self))
        self.showYearlyBalanceSheetButton.clicked.connect(self.openYearlyBalanceSheet)

        self.balanceSheetFolderButton.clicked.connect(self.selectBalanceSheetFolder)

        self.projRadio.toggled.connect(self.projToggled)
        self.projToggled()
            # Budget: Projections
        self.budgetProjections = importTable("budget_projection")
        self.budgetModel = QStandardItemModel(0, 3)
        self.budgetModel.setHorizontalHeaderLabels(['Name','Betrag','Kategorie'])
        self.budgetProjectionsTableView.setModel(self.budgetModel)
        self.displayBudgetProjections()
        self.addIncomeButton.clicked.connect(self.ask4Projection)
        self.deleteProjButton.clicked.connect(self.deleteBudgetProjection)

            # Budget: set fixed
        self.saveBudget.clicked.connect(self.setBudget)

        # Tab: Konten
        self.createAccountButton.clicked.connect(self.createAccount)
        self.displayAccounts()
        self.deleteAccountButton.clicked.connect(self.deleteSelectedAccount)
        self.accountsListWidget.itemSelectionChanged.connect(self.accountSelected)
        self.computeBalanceEdit.dateTimeChanged.connect(self.balanceDateChanged)
        self.updateBalancesButton.clicked.connect(self.updateBalances)
        computeBalances()


    def selectFolder(self):
        self.browseFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Select Directory"))
        text = self.browseFolderEdit.text()
        self.importFolder = text
        self.addText2LineEdit("browseFolderEdit", text)

    def selectFile(self):
        self.browseFileEdit.setText(QFileDialog.getOpenFileName()[0])

    def activateImportClicked(self):
        self.importFolder = self.browseFolderEdit.text()
        if self.importFolder == "":
            dlg = QMessageBox.information(self, "Import Ablageort", "Bitte gib einen Ablageort für die Import csv-Dateien an.",
                                          QMessageBox.StandardButton.Ok)
            return
        elif not Path(self.importFolder).is_dir():
            dlg = QMessageBox.information(self, "Import Ablageort",
                                          "Der angegebene Ablageort ist ungültig.",
                                          QMessageBox.StandardButton.Ok)
            return

        self.importActive = not self.importActive

        if not self.importThreadActive:
            activateImport(self, self.importFolder)
        if self.importActive:
            self.ledLabel.setPixmap(self.pixmap_green)
            self.importStatusLabel.setText("Import aktiv")
            self.activateImportButton.setText("Import deaktivieren")
        else:
            self.ledLabel.setPixmap(self.pixmap_red)
            self.importStatusLabel.setText("Import inaktiv")
            self.activateImportButton.setText("Import aktivieren")

    def selectBalanceSheetFolder(self):
        self.balanceSheetFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Select Directory"))
        text = self.balanceSheetFolderEdit.text()
        self.balanceSheetFolder = text
        self.addText2LineEdit("balanceSheetFolderEdit",text)

    def addText2LineEdit(self,widget_name,text):
        xml_path = mm_dir_path / "pyqt" / "mm_gui.ui"
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for widget in root.iter("widget"):
            if widget.attrib['name'] == widget_name:
                if len(widget):
                    widget[0][0].text = text
                else:
                    new_element = widget.makeelement("property", {"name":"text"})
                    sub_element = new_element.makeelement("string",{})
                    sub_element.text = text
                    new_element.append(sub_element)
                    widget.append(new_element)

        tree = ET.ElementTree(root)
        with open(xml_path, "wb") as fh:
            tree.write(fh)

    def onActivated(self):
        QTimer.singleShot(0, self.taggingLineEdit.clear)


    def tagEntered(self):
        self.tagReady = True

    def saveTag(self):
        self.saveTagReady = True

    def notSave(self):
        self.notSaveTag = True

    def initTransactsTable(self):
        currentMonth = datetime.now().month
        currentYear = datetime.now().year
        QstartDate = QDate(currentYear, 1, currentMonth)
        if currentMonth < 12:
            QendDate = QDate(currentYear, currentMonth + 1, 1)
        else:
            QendDate = QDate(currentYear + 1, 1, 1)
        self.startDateEdit.setDate(QstartDate)
        self.endDateEdit.setDate(QendDate)
        self.model = QStandardItemModel(0, 8)
        self.model.setHorizontalHeaderLabels(
            ['ID', 'Datum', 'Empfänger/Sender', 'Referenz', 'Betrag', 'Währung', 'Kategorie', 'Konto'])

        self.startDateEdit.dateChanged.connect(lambda : self.displayTransacts(True))
        self.endDateEdit.dateChanged.connect(lambda: self.displayTransacts(False))


    def displayTransacts(self,changeEndDate=True):
        startDate = self.startDateEdit.date().toPyDate()
        if changeEndDate:
            if startDate.month < 12:
                QendDate = QDate(startDate.year, startDate.month + 1, 1)
            else:
                QendDate = QDate(startDate.year + 1, 1, 1)
            self.endDateEdit.setDate(QendDate)

        endDate = self.endDateEdit.date().toPyDate()

        startDate = datetime.combine(startDate, datetime.min.time())
        endDate = datetime.combine(endDate, datetime.min.time())

        self.show_transacts = OrderedDict()
        for id, action in self.all_transacts.items():
            if int(action.date.timestamp()) >= int(startDate.timestamp()) and int(action.date.timestamp()) < int(endDate.timestamp()):
                self.show_transacts[id] = action

        self.model.setRowCount(len(self.show_transacts))
        for row, (id, action) in enumerate(self.show_transacts.items()):
            account = (action.account.name if action.account is not None else "")
            item_list = [action.id, action.date, action.recipient, action.reference,action.amount, action.currency, action.tag, account]
            for col, entry in enumerate(item_list):
                item = QStandardItem()
                if type(entry) is datetime:
                    item_value = QDate(entry.year,entry.month,entry.day)
                else:
                    item_value = entry
                item.setData(item_value, Qt.ItemDataRole.DisplayRole)
                self.model.setItem(row, col, item)


    def displayAllTransacts(self):
        self.show_transacts = self.all_transacts
        self.model.setRowCount(len(self.show_transacts))
        for row, (id, action) in enumerate(self.show_transacts.items()):
            item_list = [action.id, action.date, action.recipient, action.reference,
                         action.amount, action.currency, action.tag, action.account.name]
            for col, entry in enumerate(item_list):
                item = QStandardItem()
                if type(entry) is datetime:
                    item_value = QDate(entry.year, entry.month, entry.day)
                else:
                    item_value = entry
                item.setData(item_value, Qt.ItemDataRole.DisplayRole)
                self.model.setItem(row, col, item)

    def refreshTransacts(self):
        self.all_transacts = getAllTransacts()
        self.displayTransacts()


    def filterApplied(self,filter_proxy_model,search_str,i):
        filter_proxy_model.setSourceModel(self.model)
        filter_proxy_model.setFilterKeyColumn(i)
        filter_proxy_model.setFilterRegularExpression(search_str)
        self.transactsTableView.setModel(filter_proxy_model)


    def projToggled(self):
        if self.projRadio.isChecked():
            self.projLabel.setEnabled(True)
            self.budgetProjectionsTableView.setEnabled(True)
            self.addIncomeButton.setEnabled(True)
            self.deleteProjButton.setEnabled(True)

            self.setBudgetLabel.setEnabled(False)
            self.budgetLineEdit.setEnabled(False)
            self.saveBudget.setEnabled(False)
        else:
            self.projLabel.setEnabled(False)
            self.budgetProjectionsTableView.setEnabled(False)
            self.addIncomeButton.setEnabled(False)
            self.deleteProjButton.setEnabled(False)

            self.setBudgetLabel.setEnabled(True)
            self.budgetLineEdit.setEnabled(True)
            self.saveBudget.setEnabled(True)


    def displayBudgetProjections(self):
        #self.budgetModel.setRowCount(len(self.budgetProjections))
        row = 0
        self.budget = 0
        for proj in self.budgetProjections:
            if proj["year"] == datetime.now().year:
                item_list = [proj["name"],proj["amount"],proj["tag"]]
                self.budget += proj["amount"]
                for col, entry in enumerate(item_list):
                    item = QStandardItem()
                    item.setData(entry, Qt.ItemDataRole.DisplayRole)
                    self.budgetModel.setItem(row, col, item)
                row += 1
        self.totalBudgetLabel.setText("%.2f" % self.budget)

    def deleteBudgetProjection(self):
        if len(self.budgetProjectionsTableView.selectionModel().selectedRows()) > 0:
            for model_index in self.budgetProjectionsTableView.selectionModel().selectedRows():
                name = self.budgetProjectionsTableView.model().data(self.budgetProjectionsTableView.model().index(model_index.row(),0))
                amount = self.budgetProjectionsTableView.model().data(self.budgetProjectionsTableView.model().index(model_index.row(),1))
                tag = self.budgetProjectionsTableView.model().data(self.budgetProjectionsTableView.model().index(model_index.row(),2))
                year = datetime.now().year
                found = False
                toDelete = 0
                for ind,proj in enumerate(self.budgetProjections):
                    if proj["name"] == name and proj["amount"] == amount and proj["tag"] == tag and proj["year"] == year:
                        toDelete = ind
                        found = True
                        break

                if found:
                    self.budgetProjections.pop(toDelete)
                    deleteAllFromTable("budget_projection")
                    writeTable("budget_projection",self.budgetProjections)
                    self.budgetModel.removeRow(model_index.row())
                    self.displayBudgetProjections()



    def ask4Projection(self):
        Ask4ProjectionDialog(self)

    def setBudget(self):
        try:
            self.budget = float(self.budgetLineEdit.text())
            self.totalBudgetLabel.setText("%.2f" % self.budget)
        except TypeError:
            QMessageBox.warning(self, "Budget", "Budget ist ungültig.",
                                    QMessageBox.StandardButton.Ok)



    def openBalanceSheet(self):
        year = self.yearEdit.text()
        month = self.monthEdit.text()
        if len(month) > 0 and len(year) > 0:
            file = Path(self.balanceSheetFolder) / year / str(year+"-"+month+".pdf")
            subprocess.call(('open', file))

    def openYearlyBalanceSheet(self):
        year = self.yearlySheetEdit.text()
        if len(year) > 0:
            file = Path(self.balanceSheetFolder) / str("Yearly Sheet"+year+".pdf")
            subprocess.call(('open', file))

    def createAccount(self):
        createDialog = CreateAccountDialog()
        self.displayAccounts()

    def displayAccounts(self):
        self.accountsListWidget.clear()
        if len(accounts)>0:
            for account in accounts:
                item = QListWidgetItem(account.name)
                self.accountsListWidget.addItem(item)

    def deleteSelectedAccount(self):
        selected_index = self.accountsListWidget.currentRow()
        deleteAccount(selected_index,mm_dir_path/"accounts.json")
        self.displayAccounts()

    def accountSelected(self):
        selected_index = self.accountsListWidget.currentRow()
        try:
            account = accounts[selected_index]
        except IndexError:
            return 0
        self.accountNameLabel.setText(account.name)
        self.accountBalanceLabel.setText(str(account.balance))
        date = list(account.balances)[-1][0]
        self.accountBalanceDateLabel.setText(date.strftime("%d/%m/%Y"))
        self.computeBalanceEdit.setDate(QDate(date.year,date.month,date.day))
        self.accountBaseBalanceLabel.setText(str(account.latest_balance_base[1]))
        self.accountBaseBalanceDateLabel.setText(account.latest_balance_base[0].strftime("%d/%m/%Y"))

    def balanceDateChanged(self):
        selected_index = self.accountsListWidget.currentRow()
        try:
            account = accounts[selected_index]
        except IndexError:
            return 0
        set_date = self.computeBalanceEdit.date()
        set_date = set_date.toPyDate()
        set_date = datetime(set_date.year,set_date.month,set_date.day)
        for (date,balance) in reversed(account.balances):
            if date <= set_date:
                self.accountBalanceDateLabel.setText(date.strftime("%d/%m/%Y"))
                self.accountBalanceLabel.setText(str(balance))
                break

    def updateBalances(self):
        computeBalances()
        self.balanceDateChanged()



class CreateAccountDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "createAccountDialog.ui", self)
        self.searchButton.clicked.connect(self.search4File)

        self.headers = []
        self.rowsDeleted = []
        self.colsDeleted = []
        self.detectString = ""
        self.ignoreTypes = []
        self.statementDetectionDone = False
        today = datetime.today()
        q_today = QDate(today.year,today.month,today.day)
        self.balanceDateEdit.setDate(q_today)
        self.balanceEdit.setText("0")
        self.statementDetectionButton.clicked.connect(self.statementDetectionStarted)
        self.exampleFileEdit.textChanged.connect(self.checkFile)
        self.pushButtonOk.clicked.connect(self.accountCreated)
        self.pushButtonCancel.clicked.connect(self.reject)
        self.exec()

    def search4File(self):
        self.exampleFileEdit.setText(QFileDialog.getOpenFileName()[0])

    def statementDetectionStarted(self):
        file = self.exampleFileEdit.text()
        transacts = statementDetection(file)
        statementDetectionDialog = StatementDetectionDialog(transacts,file,self)

    def checkFile(self):
        file = Path(self.exampleFileEdit.text())
        if file.is_file() and (file.suffix == ".csv" or file.suffix == ".CSV"):
            self.statementDetectionButton.setEnabled(True)
        else:
            dlg = QMessageBox.information(self, "CSV-Datei", "Datei zur Auszugserkennung ist ungültig.",
                                          QMessageBox.StandardButton.Ok)

    def accountCreated(self):
        if self.nameLineEdit.text() == "":
            dlg = QMessageBox.information(self,"Kontoname","Bitte gib ein Name für das Konto ein.",QMessageBox.StandardButton.Ok)
            return 0
        if not self.statementDetectionDone:
            dlg = QMessageBox.information(self, "Auszugerkennung", "Bitte führe die Auszugserkennung durch.",QMessageBox.StandardButton.Ok)
            return 0
        self.account_name = self.nameLineEdit.text()
        try:
            balance = float(self.balanceEdit.text())
        except ValueError:
            dlg = QMessageBox.information(self, "Kontostand", "Bitte gib einen korrekten Wert für den Kontostand ein.",
                                              QMessageBox.StandardButton.Ok)
            return 0
        date = self.balanceDateEdit.date()
        date = date.toPyDate()
        date_str = date.strftime("%Y-%m-%d")

        file = mm_dir_path / "accounts.json"
        if not hasattr(self, 'signs'):
            self.signs = None
        accounts.append(Account(self.account_name, 0, self.rowsDeleted, self.colsDeleted, self.headers,self.detectString,self.dmy_format,self.ignoreTypes,signs=self.signs,balance_base={date_str:balance}))
        exportAllAccounts(accounts,file)

        self.close()





class StatementDetectionDialog(QDialog):
    def __init__(self,transacts,file_name,account_dialog):
        super().__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "statement_detection.ui", self)
        self.account_dialog = account_dialog
        self.model = QStandardItemModel()
        self.csvView.setModel(self.model)
        self.transacts = transacts
        for row,action in enumerate(self.transacts):
            for col,entry in enumerate(action):
                item = QStandardItem(str(entry))
                self.model.setItem(row,col,item)

        self.deleteSelectedButton.clicked.connect(self.removeSelected)


        self.options = ["Bitte auswählen..","Datum", "Typ", "Empfänger/Sender", "Referenz", "Betrag", "Währung","Vorzeichen"]
        self.csvView.horizontalHeader().sectionDoubleClicked.connect(self.changeHorizontalHeader)

        detectString = file_name[file_name.rfind("/")+1:]
        detectString = detectString[:re.search(r"\d",detectString).start()]
        self.detectStringEdit.setText(detectString)
        self.account_dialog.detectString = detectString
        self.detectStringEdit.textChanged.connect(lambda: self.enableIf(self.detectStringEdit,self.saveDetectStringButton))

        self.saveDetectStringButton.clicked.connect(self.detectFileBy)

        self.ignoreTypeEdit.textChanged.connect(lambda: self.enableIf(self.ignoreTypeEdit,self.ignoreTypeSaveButton))
        self.ignoreTypeSaveButton.clicked.connect(self.addIgnore)

        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.reject)

        self.exec()


    def changeHorizontalHeader(self, index):
        oldHeader = str(self.model.headerData(index,Qt.Orientation.Horizontal))
        newHeader, ok = QInputDialog.getItem(self,'Zeilentitel %s ändern' % oldHeader,'Auswahl:', self.options, 0, False)
        if ok:
            if newHeader != "Bitte auswählen..":
                self.options.pop(self.options.index(newHeader))
                self.model.setHorizontalHeaderItem(index, QStandardItem(newHeader))
            if len(oldHeader) > 1:
                self.options.append(oldHeader)
            if newHeader == "Vorzeichen":
                self.ask4sign = Ask4Sign(self.account_dialog)


    def removeSelected(self):
        if len(self.csvView.selectionModel().selectedRows())>0:
            index_list = []
            toAppend = []
            for model_index in self.csvView.selectionModel().selectedRows():
                index = QPersistentModelIndex(model_index)
                index_list.append(index)
                index_row = index.row()

                if index_row >= self.csvView.model().rowCount()-3 and index_row >= 4:
                    toAppend.append(index_row - self.csvView.model().rowCount())
                else:
                    toAppend.append(index_row)
            if -2 in toAppend and -1 in toAppend and len(toAppend) >= 2:
                if -3 in toAppend:
                    toAppend = [-1,-1,-1]
                else:
                    toAppend = [-1,-1]
            self.account_dialog.rowsDeleted.append(toAppend)

            for index in index_list:
                self.model.removeRow(index.row())
        elif len(self.csvView.selectionModel().selectedColumns())>0:
            index_list = []
            toAppend = []
            for model_index in self.csvView.selectionModel().selectedColumns():
                index = QPersistentModelIndex(model_index)
                index_list.append(index)
                toAppend.append(index.column())
            self.account_dialog.colsDeleted.append(toAppend)

            for index in index_list:
                self.model.removeColumn(index.column())

    def detectFileBy(self):
        self.account_dialog.detectString = self.detectStringEdit.text()

    def addIgnore(self):
        ignore_type = self.ignoreTypeEdit.text()
        self.account_dialog.ignoreTypes.append(ignore_type)
        self.ignoreTypeEdit.clear()

    def enableIf(self,lineEdit,button):
        if len(lineEdit.text()) > 0:
            button.setEnabled(True)
        else:
            button.setEnabled(False)

    def accepted(self):
        self.account_dialog.headers = []
        for index in range(self.model.columnCount()):
            header = str(self.model.headerData(index, Qt.Orientation.Horizontal))
            self.account_dialog.headers.append(header)
        if self.dmyRadio.isChecked():
            self.account_dialog.dmy_format = True
        else:
            self.account_dialog.dmy_format = False
        self.account_dialog.statementDetectionDone = True


class Ask4Sign(QDialog):
    def __init__(self, account_dialog, parent=None):
        super(Ask4Sign, self).__init__(parent)
        self.setWindowTitle('Vorzeichen')
        self.account_dialog = account_dialog
        outerLayout = QVBoxLayout()
        layout = QGridLayout()

        self.descriptionLabel = QLabel("Bitte geben sie an welches Zeichen, welcher Art von Transaktion entspricht")

        self.plusLabel = QLabel("Zeichen für Einnahmen:")
        self.plusSignEdit = QLineEdit()

        self.minusLabel = QLabel("Zeichen für Ausgaben:")
        self.minusSignEdit = QLineEdit()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        layout.addWidget(self.plusLabel,0,0)
        layout.addWidget(self.plusSignEdit, 0, 1)
        layout.addWidget(self.minusLabel, 1, 0)
        layout.addWidget(self.minusSignEdit, 1, 1)

        outerLayout.addWidget(self.descriptionLabel)
        outerLayout.addLayout(layout)
        outerLayout.addWidget(self.buttonBox)

        self.setLayout(outerLayout)

        self.buttonBox.accepted.connect(self.getSigns)
        self.buttonBox.rejected.connect(self.reject)

        self.exec()

    def getSigns(self):
        self.plusSign = self.plusSignEdit.text()
        self.minusSign = self.minusSignEdit.text()

        self.account_dialog.signs = {"+":self.plusSign,"-":self.minusSign}

        self.close()



class Ask4ProjectionDialog(QDialog):
    def __init__(self,gui, parent=None):
        super(Ask4ProjectionDialog, self).__init__(parent)
        self.setWindowTitle('Vorausichtliches Einkommen')

        self.gui = gui

        outerLayout = QVBoxLayout()
        layout = QGridLayout()

        self.descriptionLabel = QLabel("Bitte gib das vorausichtliche Einkommen an")

        self.nameLabel = QLabel("Name:")
        self.nameEdit = QLineEdit()

        self.amountLabel = QLabel("Betrag:")
        self.amountEdit = QLineEdit()

        self.tagLabel = QLabel("Kategorie:")
        self.tagEdit = QLineEdit()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        layout.addWidget(self.nameLabel,0,0)
        layout.addWidget(self.nameEdit, 0, 1)
        layout.addWidget(self.amountLabel, 1, 0)
        layout.addWidget(self.amountEdit, 1, 1)
        layout.addWidget(self.tagLabel, 2, 0)
        layout.addWidget(self.tagEdit, 2, 1)

        outerLayout.addWidget(self.descriptionLabel)
        outerLayout.addLayout(layout)
        outerLayout.addWidget(self.buttonBox)

        self.setLayout(outerLayout)

        self.buttonBox.accepted.connect(self.getProj)
        self.buttonBox.rejected.connect(self.reject)

        self.exec()

    def getProj(self):
        name = self.nameEdit.text()
        amount = float(self.amountEdit.text())
        tag = self.tagEdit.text()
        year = datetime.now().year

        self.gui.budgetProjections.append({"name":name,"amount":amount,"tag":tag,"year":year})
        deleteAllFromTable("budget_projection")
        writeTable("budget_projection",self.gui.budgetProjections)
        self.gui.displayBudgetProjections()
        self.close()

def computeBalances():
    all_transacts = getAllTransacts()
    for account in accounts:
        account.getAccountTransacts(all_transacts)
        account.getBalances()

def main():
    app = QApplication([])
    #app.setFont(QFont('Helvetica Neue'))
    window = MainGUI()
    app.exec()


if __name__ == '__main__':
    main()
