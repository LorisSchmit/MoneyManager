from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QStandardItemModel,QStandardItem
from PyQt6.QtCore import QDate,QSortFilterProxyModel,Qt,QPersistentModelIndex
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


from database_api import getAllTransacts



class MainGUI(QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "mm_gui.ui", self)
        self.show()


        # Tab: Übersicht
        self.initTransactsTable()
        """
        self.filter_proxy_model = []
        filterLayout_children = [self.filterLineEdit1, self.filterLineEdit2, self.filterLineEdit3, self.filterLineEdit4, self.filterLineEdit5, self.filterLineEdit6, self.filterLineEdit7, self.filterLineEdit8]
        for i,widget in enumerate(filterLayout_children):
            if isinstance(widget, QLineEdit):
                self.filter_proxy_model.append(QSortFilterProxyModel(filterCaseSensitivity=Qt.CaseSensitivity.CaseInsensitive))

                widget.textChanged.connect(lambda: self.filterApplied(self.filter_proxy_model[i],str(widget.text()),i))
        """
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
        #self.displayTransacts()

        # Tab: Import
        self.browseFolderButton.clicked.connect(self.selectFolder)
        if self.browseFolderEdit.text() != "":
            self.importFolder = self.browseFolderEdit.text()
        self.activateImportButton.clicked.connect(lambda: activateImport(self, self.importFolder))

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

        # Tab: Konten
        self.createAccountButton.clicked.connect(self.createAccount)
        self.displayAccounts()
        self.deleteAccountButton.clicked.connect(self.deleteSelectedAccount)

    def selectFolder(self):
        self.browseFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Select Directory"))
        text = self.browseFolderEdit.text()
        self.importFolder = text
        self.addText2LineEdit("browseFolderEdit", text)

    def selectFile(self):
        self.browseFileEdit.setText(QFileDialog.getOpenFileName()[0])

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
            item_list = [action.id, action.date, action.recipient, action.reference,
                    action.amount, action.currency, action.tag, action.account.name]
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



class CreateAccountDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "createAccountDialog.ui", self)
        self.searchButton.clicked.connect(self.search4File)

        self.headers = []
        self.rowsDeleted = []
        self.colsDeleted = []
        self.detectString = ""
        self.statementDetectionButton.clicked.connect(self.statementDetectionStarted)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.reject)
        self.exec()

    def search4File(self):
        self.exampleFileEdit.setText(QFileDialog.getOpenFileName()[0])

    def statementDetectionStarted(self):
        file = self.exampleFileEdit.text()
        transacts = statementDetection(file)
        statementDetectionDialog = StatementDetectionDialog(transacts,file,self)

    def accepted(self):
        self.account_name = self.nameLineEdit.text()
        file = mm_dir_path / "accounts.json"
        if not hasattr(self, 'signs'):
            self.signs = None
        accounts.append(Account(self.account_name, 0, self.rowsDeleted, self.colsDeleted, self.headers,self.detectString,self.dmy_format,signs=self.signs))
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

        self.saveDetectStringButton.clicked.connect(self.detectFileBy)

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

                if index_row >= len(self.transacts)-3 and index_row >= 4:
                    toAppend.append(index_row - len(self.transacts))
                else:
                    toAppend.append(index_row)
            if -2 in toAppend and -1 in toAppend and len(toAppend) == 2:
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

    def accepted(self):
        self.account_dialog.headers = []
        for index in range(self.model.columnCount()):
            header = str(self.model.headerData(index, Qt.Orientation.Horizontal))
            self.account_dialog.headers.append(header)
        if self.dmyRadio.isChecked():
            self.account_dialog.dmy_format = True
        else:
            self.account_dialog.dmy_format = False


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

def main():
    app = QApplication([])
    #app.setFont(QFont('Helvetica Neue'))
    window = MainGUI()
    app.exec()


if __name__ == '__main__':
    main()
