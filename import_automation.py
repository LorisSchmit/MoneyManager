from pathlib import Path
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from importer import importNewFile
import threading
from Account import *

mm_dir_path = Path(__file__).parent


def newFileDetectedListener(event,gui):
    file = event.src_path
    account_detected = False
    for acc in accounts:
        if file.find(acc.detectString) >= 0:
            account = acc
            account_detected = True

    if account_detected:
        gui.accountDetectedLabel.setText("Konto erkannt: " + account.name)
        print("New File detected : " + file)
        importNewFile(file,account,gui=gui)
        ind = file.rfind("/")
        dest_file = file[:ind + 1] + "imported" + file[ind:]
        os.rename(file, dest_file)
    else:
        gui.accountDetectedLabel.setText("Unbekanntes Konto")


def newSingleFile(file,gui=None):
    account_detected = False
    for acc in accounts:
        if file.find(acc.detectString) >= 0:
            account = acc
            account_detected = True

    if account_detected:
        gui.accountDetectedLabel.setText("Konto erkannt: " + account.name)
        sec_thread = threading.Thread(target=importNewFile, args=(file,account,gui))
        sec_thread.start()
    else:
        gui.accountDetectedLabel.setText("Unbekanntes Konto")
        #print("Unknown file type")



def launchEventListener(gui,path):
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = lambda event,gui_obj=gui: newFileDetectedListener(event,gui_obj)
    #home = str(Path.home())
    #path = home + "/Movements"
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


def activateImport(gui,import_path):
    print("Import Activated")
    main_thread = threading.Thread(target=launchEventListener,args=(gui,import_path,))
    main_thread.start()
    return "Balance Creation started"