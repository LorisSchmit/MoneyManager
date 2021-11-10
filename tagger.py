from database_api import *
import readline
import sys

known_tags = importTable("tags",tags=True)


def rlinput(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def printAction(action):
    print(action.date.strftime("%d/%m/%Y")+": "+action.recipient+" "+action.reference+" Amount: "+str(action.amount))

def tag(transacts):
    for action in transacts:
        tag_found = False
        for known_ref in known_tags:
            if action.recipient.lower().find(known_ref.lower()) != -1:
                tag = known_tags[known_ref]
                tag_found = True
                break
        if not tag_found:
            printAction(action)
            print("Tag: ")
            tag = sys.stdin.readline()
            tag = tag.strip().rstrip()
            default = action.recipient
            print("Default reference is: ", default)
            print("Save as: ")
            ref = str(sys.stdin.readline().rstrip() or default)
            if ref != "none":
                known_tags[ref] = tag.strip().rstrip()
        if tag != "none":
            action.tag = tag.strip().rstrip()
            writeTags(known_tags)
        else:
            transacts.remove(action)

    return transacts
