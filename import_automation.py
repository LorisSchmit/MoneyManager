from pathlib import Path
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from importer import importNewFile
import threading
from Account import *
from datetime import datetime
import shutil


mm_dir_path = Path(__file__).parent


def newFileDetectedListener(event,gui):
    if gui.importActive:
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
            dest_file = Path(file[:ind + 1]) / "imported" / Path(file[ind+1:])
            dir = Path(file[:ind + 1]) / "imported"
            if not dir.is_dir():
                os.mkdir(dir)
            if dest_file.exists():
                now = datetime.now()
                dest_file = dest_file.parent / (dest_file.stem + now.strftime("%d-%m-%Y")+".csv")
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
        ind = file.rfind("/")
        if gui is not None:
            import_path = Path(gui.importFolder)
        else:
            import_path = Path(file[:ind + 1])

        dest_file = import_path / "imported" / Path(file[ind + 1:])
        dir = import_path / "imported"
        if not dir.is_dir():
            os.mkdir(dir)
        if dest_file.exists():
            now = datetime.now()
            dest_file = dest_file.parent / (dest_file.stem + "_"+now.strftime("%d-%m-%Y_%H:%M:%S") + ".csv")
        shutil.copy2(file, dest_file)
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
    gui.importThreadActive = True
    return "Balance Creation started"