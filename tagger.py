from database_api import *
import readline
import sys
from PyQt6.QtWidgets import QTableWidgetItem
import time

known_tags = importTable("tags",tags=True)


def rlinput(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def printAction(action):
    print(action.date.strftime("%d/%m/%Y")+": "+action.recipient+" "+action.reference+" Amount: "+str(action.amount))

def tag(transacts,gui=None):
    for i,(id,action) in enumerate(transacts.items()):
        tag_found = False
        for known_ref in known_tags:
            if action.recipient.lower().find(known_ref.lower()) != -1:
                tag = known_tags[known_ref]
                tag_found = True
                break
        if not tag_found:
            gui.taggingTableWidget.setItem(0, 0, QTableWidgetItem(action.date.strftime("%d/%m/%Y")))
            gui.taggingTableWidget.setItem(0, 1, QTableWidgetItem(action.recipient))
            gui.taggingTableWidget.setItem(0, 2, QTableWidgetItem(action.reference))
            gui.taggingTableWidget.setItem(0, 3, QTableWidgetItem(str(action.amount)+" €"))
            while not gui.tagReady:
                time.sleep(.01)
            tag = str(gui.taggingLineEdit.text())
            gui.tagReady = False
            default = action.recipient
            gui.tagReferenceEdit.setText(str(default))
            while (not gui.saveTagReady) and (not gui.notSaveTag):
                time.sleep(.01)
            if gui.saveTagReady:
                ref = str(gui.tagReferenceEdit.text())
                known_tags[ref] = tag.strip().rstrip()
            gui.saveTagReady = False
            gui.notSave = False
        gui.importProgressLabel.setText(" %d von %d Transaktionen importiert" % (i+1, len(transacts)))
        gui.taggingLineEdit.setText("")
        gui.tagReferenceEdit.setText("")
        if tag != "none":
            action.tag = tag.strip().rstrip()
            #writeTags(known_tags)
        else:
            transacts.remove(action)

    return transacts
