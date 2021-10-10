from database_api import *
import readline
import sys

known_tags = importKnownTags("tags")


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
        for ref in known_tags:
            if action.recipient.lower().find(ref.lower()) != -1:
                tag = known_tags[ref]
                tag_found = True
                break
        if not tag_found:
            printAction(action)
            print("Tag: ")
            tag = sys.stdin.readline()
            tag = tag.rstrip()
            default = action.recipient
            print("Default reference is: ", default)
            print("Save as: ")
            ref = str(sys.stdin.readline() or default)
            if ref != "none":
                known_tags[ref] = tag.rstrip()
        if tag != "none":
            action.tag = tag.rstrip()
            writeTags(known_tags)
        else:
            transacts.remove(action)

    return transacts
