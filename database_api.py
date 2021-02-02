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

def write2DB(transacts):
    db_file = "db.db"
    conn = create_connection(db_file)
    data = []
    for action in transacts:
        data.append(object2list(action))
        print(object2list(action))
    with conn:
        writeMany(conn,data)

def deleteAllFromTable():
    db_file = "db.db"
    conn = create_connection(db_file)
    with conn:
        deleteAll(conn)
