from database import *
from Transaction import Transaction
from datetime import datetime
from Account import accountsLookup


def object2list(action):
    l = [int(action.date.timestamp()), action.type, action.recipient, action.reference, str(action.amount), action.currency, action.tag,action.account.name]
    return l


def getAllTransacts():
    db_file = "db.db"
    conn = create_connection(db_file)
    with conn:
        transacts_temp = fetchAllTransacts(conn)
    transacts = []
    for action in transacts_temp:
        transacts.append(Transaction(datetime.fromtimestamp(action[1]),action[2],action[3],action[4],action[5],action[6],action[7],accountsLookup(action[8])))
    return transacts

def writeTransacts2DB(transacts):
    db_file = "db.db"
    conn = create_connection(db_file)
    data = []
    for action in transacts:
        data.append(object2list(action))
    with conn:
        writeMany(conn,data)

def deleteAllFromTable(table):
    db_file = "db.db"
    conn = create_connection(db_file)
    with conn:
        deleteAll(conn,table)

def importKnownTags(table):
    db_file = "db.db"
    conn = create_connection(db_file)
    with conn:
        raw_data = read(conn, table)
    known_tags = {}
    for el in raw_data:
        known_tags[el[1]] = el[2]
    return known_tags

def writeTags(tags):
    db_file = "db.db"
    conn = create_connection(db_file)
    deleteAllFromTable("tags")
    data = []
    for key in tags:
        temp = [key,tags[key]]
        data.append(temp)
    with conn:
        writeManyTags(conn,data)


if __name__ == '__main__':
    transacts = getAllTransacts()
    for action in transacts:
        print(action.recipient)