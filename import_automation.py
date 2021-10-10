from pathlib import Path
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from importer import importNewFile
import threading


def on_created(event):
    file = event.src_path
    if (file.find("Export_Mouvements") >= 0 or file.find("Umsaetze") >= 0 or file.find("MSR") >= 0 or file.find("Export_Card") >= 0)  and file.find("imported") == -1:
        print("New File detected : " + file)
        importNewFile(file)
        ind = file.rfind("/")
        dest_file = file[:ind+1] + "imported" + file[ind:]
        os.rename(file,dest_file)

def launchEventListener():
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    home = str(Path.home())
    path = home + "/Movements"
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


def activateImport():
    print("Import Activated")
    main_thread = threading.Thread(target=launchEventListener)
    main_thread.start()
    return "Balance Creation started"