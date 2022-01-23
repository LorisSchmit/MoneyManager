from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic
import threading
import sys
sys.path.append("../MoneyManager")

from Month import executeCreateSingleMonth,executeAssignPayback


class MainGUI(QMainWindow):
	def __init__(self):
		super(MainGUI, self).__init__()
		uic.loadUi("pyqt/mm_gui.ui",self)
		self.show()

		self.CreateBalanceButton.clicked.connect(lambda: executeCreateSingleMonth(int(self.monthEdit.text()),int(self.yearEdit.text())))


def main():
	app = QApplication([])
	window = MainGUI()
	app.exec()


if __name__ == '__main__':
	main()