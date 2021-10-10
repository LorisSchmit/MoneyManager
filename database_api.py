from database import *
from Transaction import Transaction
from datetime import datetime
from Account import accountsLookup
from pathlib import Path


def object2list(action):
    l = [int(action.date.timestamp()), action.type, action.recipient, action.reference, str(action.amount), action.currency, action.tag,action.account.name,action.pb_assign]
    return l


def getAllTransacts():
    home = str(Path.home())
    db_file = home+"/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        transacts_temp = fetchAllTransacts(conn)
    transacts = []
    for action in transacts_temp:
        transacts.append(Transaction(action[0],datetime.fromtimestamp(action[1]),action[2],action[3],action[4],action[5],action[6],action[7],accountsLookup(action[8]),action[9]))
    return transacts

def writeTransacts2DB(transacts):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    data = []
    for action in transacts:
        data.append(object2list(action))
    with conn:
        writeMany(conn,data)

def deleteAllFromTable(table):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        deleteAll(conn,table)

def importKnownTags(table):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        raw_data = read(conn, table)
    known_tags = {}
    for el in raw_data:
        known_tags[el[1]] = el[2]
    return known_tags

def writeTags(tags):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    deleteAllFromTable("tags")
    data = []
    for key in tags:
        temp = [key,tags[key]]
        data.append(temp)
    with conn:
        writeManyTags(conn,data)


def updateMany(transacts):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        for action in transacts:
            updatePBAssign(conn,action.id, action.pb_assign)


if __name__ == '__main__':
    transacts = getAllTransacts()
    for action in transacts:
        print(action.recipient)