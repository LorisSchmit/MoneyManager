from database_api import *
import readline
import sys
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import QTimer
import time
import numpy as np




def rlinput(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def getUniqueTags():
    transacts = getAllTransacts()
    tags = [action[1].tag for action in transacts.items()]
    tags = np.array(tags)
    uniques = np.unique(tags)
    return uniques


def printAction(action):
    print(action.date.strftime("%d/%m/%Y")+": "+action.recipient+" "+action.reference+" Amount: "+str(action.amount))

def tag(transacts,gui=None):
    for i,(id,action) in enumerate(transacts.items()):
        tag_found = False
        for known_ref in known_tags:
            if action.recipient.lower().find(known_ref.lower()) != -1 or action.reference.lower().find(known_ref.lower()) != -1:
                tag = known_tags[known_ref][0]
                subtag = known_tags[known_ref][1]
                tag_found = True
                break
        if not tag_found:
            gui.importProgressLabel.setText(" %d von %d Transaktionen importiert" % (i, len(transacts)))
            gui.taggingTableWidget.setItem(0, 0, QTableWidgetItem(action.date.strftime("%d/%m/%Y")))
            gui.taggingTableWidget.setItem(0, 1, QTableWidgetItem(action.recipient))
            gui.taggingTableWidget.setItem(0, 2, QTableWidgetItem(action.reference))
            gui.taggingTableWidget.setItem(0, 3, QTableWidgetItem(str(action.amount)+" €"))
            while not gui.tagReady:
                time.sleep(.01)
            tag = str(gui.taggingLineEdit.text())
            subtag = str(gui.subtagLineEdit.text())
            gui.tagReady = False
            default = (action.recipient if action.recipient!= "" else action.reference)

            if len(default) > 0:
                gui.tagReferenceEdit.setEnabled(True)
                gui.saveTagButton.setEnabled(True)
                gui.notSaveTagButton.setEnabled(True)
                gui.tagReferenceEdit.setText(str(default))
                while (not gui.saveTagReady) and (not gui.notSaveTag):
                    time.sleep(.01)
                if gui.saveTagReady:
                    ref = str(gui.tagReferenceEdit.text())
                    known_tags[ref] = (tag.strip().rstrip(),subtag.strip().rstrip())
                    writeTags(known_tags)
                gui.saveTagReady = False
                gui.notSaveTag = False
                gui.tagReferenceEdit.setEnabled(False)
                gui.saveTagButton.setEnabled(False)
                gui.notSaveTagButton.setEnabled(False)
        transacts[id].tag = tag
        transacts[id].sub_tag = subtag
        gui.importProgressLabel.setText(" %d von %d Transaktionen importiert" % (i+1, len(transacts)))
        QTimer.singleShot(0, gui.taggingLineEdit.clear)
        QTimer.singleShot(0, gui.tagReferenceEdit.clear)
        QTimer.singleShot(0, gui.subtagLineEdit.clear)
        gui.taggingTableWidget.clear()


    return transacts


known_tags = importTable("tags",tags=True)
unique_tags = getUniqueTags()