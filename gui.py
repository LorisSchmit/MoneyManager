from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog, QListView, QLineEdit,QInputDialog,QComboBox,QListWidgetItem
from PyQt6 import uic
from PyQt6.QtGui import QFont, QStandardItemModel,QStandardItem
from PyQt6.QtCore import QDate,QSortFilterProxyModel,Qt,QPersistentModelIndex
import threading
from collections import OrderedDict
import sys
import os
import subprocess
import json
import re
import time

from pathlib import Path
from datetime import datetime

mm_dir_path = Path(__file__).parent
sys.path.append(mm_dir_path)

from Month import executeCreateSingleMonth, executeAssignPayback, Month
from Year import executeCreateSingleYear
from import_automation import activateImport,newSingleFile
from Account import statementDetection, importAllAccounts,deleteAccount


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
        self.transactsTableView.setModel(self.model)

        self.transactsTableView.setColumnWidth(0, 40)
        self.transactsTableView.setColumnWidth(1, 75)
        self.transactsTableView.setColumnWidth(2, 200)
        self.transactsTableView.setColumnWidth(3, 200)
        self.transactsTableView.setColumnWidth(4, 55)
        self.transactsTableView.setColumnWidth(5, 50)
        self.transactsTableView.setSortingEnabled(True)
        self.allTransactsButton.clicked.connect(self.displayAllTransacts)
        self.displayTransacts()

        # Tab: Import
        self.browseFolderButton.clicked.connect(self.selectFolder)
        self.activateImportButton.clicked.connect(lambda: activateImport(self, str(self.browseFolderEdit.text())))

        self.browseFileButton.clicked.connect(self.selectFile)
        self.importButton.clicked.connect(lambda: newSingleFile(str(self.browseFileEdit.text()), self))

        self.taggingTableWidget.setHorizontalHeaderLabels(['Datum', 'Sender', 'Referenz', 'Betrag'])
        self.tagReady = False
        self.saveTagReady = False
        self.notSaveTag = False
        self.taggingEnterButton.clicked.connect(self.tagEntered)
        self.taggingLineEdit.returnPressed.connect(self.taggingEnterButton.click)
        self.saveTagButton.clicked.connect(self.saveTag)
        self.notSaveTagButton.clicked.connect(self.notSave)

        # Tab: Monat
        self.CreateBalanceButton.clicked.connect(lambda: executeCreateSingleMonth(int(self.monthEdit.text()), int(self.yearEdit.text())))
        self.showBalanceSheetButton.clicked.connect(self.openBalanceSheet)

        # Tab: Jahr
        self.createYearlyBalanceButton.clicked.connect(lambda: executeCreateSingleYear(int(self.yearlySheetEdit.text()),redraw_graphs=True,gui=self))
        self.showYearlyBalanceSheetButton.clicked.connect(self.openYearlyBalanceSheet)

        # Tab: Konten
        self.createAccountButton.clicked.connect(self.createAccount)
        self.displayAccounts()
        self.deleteAccountButton.clicked.connect(self.deleteSelectedAccount)

    def selectFolder(self):
        self.browseFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Select Directory"))

    def selectFile(self):
        self.browseFileEdit.setText(QFileDialog.getOpenFileName()[0])

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
            QendDate = QDate(currentYear + 1, currentMonth, 1)
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
                QendDate = QDate(startDate.year, + 1, startDate.month, 1)
            self.endDateEdit.setDate(QendDate)

        endDate = self.endDateEdit.date().toPyDate()

        startDate = datetime.combine(startDate, datetime.min.time())
        endDate = datetime.combine(endDate, datetime.min.time())

        self.all_transacts = getAllTransacts()
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


    def filterApplied(self,filter_proxy_model,search_str,i):
        filter_proxy_model.setSourceModel(self.model)
        filter_proxy_model.setFilterKeyColumn(i)
        filter_proxy_model.setFilterRegularExpression(search_str)
        self.transactsTableView.setModel(filter_proxy_model)


    def openBalanceSheet(self):
        year = self.yearEdit.text()
        month = self.monthEdit.text()
        if len(month) > 0 and len(year) > 0:
            file = Path("/Users/lorisschmit1/Balance Sheets") / year / str(year+"-"+month+".pdf")
            subprocess.call(('open', file))

    def openYearlyBalanceSheet(self):
        year = self.yearlySheetEdit.text()
        if len(year) > 0:
            file = Path("/Users/lorisschmit1/Balance Sheets") / str("Yearly Sheet"+year+".pdf")
            subprocess.call(('open', file))

    def createAccount(self):
        createDialog = CreateAccountDialog()
        self.displayAccounts()

    def displayAccounts(self):
        self.accountsListWidget.clear()
        file = mm_dir_path / "accounts.json"
        self.account_data = importAllAccounts(file)
        if "accounts" in self.account_data:
            for account in self.account_data["accounts"]:
                item = QListWidgetItem(account["name"])
                self.accountsListWidget.addItem(item)

    def deleteSelectedAccount(self):
        selected_index = self.accountsListWidget.currentRow()
        deleteAccount(selected_index,self.account_data,mm_dir_path/"accounts.json")
        self.displayAccounts()



class CreateAccountDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "createAccountDialog.ui", self)
        self.searchButton.clicked.connect(self.search4File)

        self.headers = []
        self.rowsDeleted = []
        self.columnsDeleted = []
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
        data = importAllAccounts(file)

        with open(file, "w+",encoding="latin-1") as json_file:
            if not bool(data):
                data = {'accounts': [{'name': self.account_name,
                                      'balance': 0,
                                      'rowsDeleted': self.rowsDeleted,
                                      'colsDeleted': self.columnsDeleted,
                                      'headers': self.headers,
                                      'detectString':self.detect_string}]}
            else:
                data['accounts'].append({'name': self.account_name,
                                      'balance': 0,
                                      'rowsDeleted': self.rowsDeleted,
                                      'colsDeleted': self.columnsDeleted,
                                      'headers': self.headers,
                                      'detectString':self.detect_string})
            json_string = json.dumps(data)
            json_file.write(json_string)
        #time.sleep(0.2)

        self.close()





class StatementDetectionDialog(QDialog):
    def __init__(self,transacts,file_name,account_dialog):
        super().__init__()
        uic.loadUi(mm_dir_path / "pyqt" / "statement_detection.ui", self)
        self.account_dialog = account_dialog
        self.model = QStandardItemModel()
        self.csvView.setModel(self.model)
        for row,action in enumerate(transacts):
            for col,entry in enumerate(action):
                item = QStandardItem(str(entry))
                self.model.setItem(row,col,item)

        self.deleteSelectedButton.clicked.connect(self.removeSelected)


        self.options = ["Bitte auswählen..","Datum", "Typ", "Empfänger/Sender", "Referenz", "Betrag", "Währung"]
        self.csvView.horizontalHeader().sectionDoubleClicked.connect(self.changeHorizontalHeader)

        detect_string = file_name[file_name.rfind("/")+1:]
        detect_string = detect_string[:re.search(r"\d",detect_string).start()]
        self.detectStringEdit.setText(detect_string)
        self.account_dialog.detect_string = detect_string

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


    def removeSelected(self):
        if len(self.csvView.selectionModel().selectedRows())>0:
            index_list = []
            for model_index in self.csvView.selectionModel().selectedRows():
                index = QPersistentModelIndex(model_index)
                index_list.append(index)
                self.account_dialog.rowsDeleted.append(model_index.row())

            for index in index_list:
                self.model.removeRow(index.row())
        elif len(self.csvView.selectionModel().selectedColumns())>0:
            index_list = []
            for model_index in self.csvView.selectionModel().selectedColumns():
                index = QPersistentModelIndex(model_index)
                index_list.append(index)
                self.account_dialog.columnsDeleted.append(model_index.column())

            for index in index_list:
                self.model.removeColumn(index.column())

    def detectFileBy(self):
        self.account_dialog.detect_string = self.detectStringEdit.text()

    def accepted(self):
        self.account_dialog.headers = []
        for index in range(self.model.columnCount()):
            header = str(self.model.headerData(index, Qt.Orientation.Horizontal))
            self.account_dialog.headers.append(header)


def main():
    app = QApplication([])
    #app.setFont(QFont('Helvetica Neue'))
    window = MainGUI()
    app.exec()


if __name__ == '__main__':
    main()
