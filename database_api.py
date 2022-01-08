from database import *
from Transaction import Transaction
from datetime import datetime
from Account import accountsLookup
from pathlib import Path
import ast
from collections import OrderedDict
from shutil import copyfile




def object2list(action):
    l = [action.id,int(action.date.timestamp()), action.type, action.recipient, action.reference, str(action.amount), action.currency, action.tag,action.account.name,str(action.pb_assign)]
    return l


def getAllTransacts():
    home = str(Path.home())
    db_file = home+"/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        transacts_temp = fetchAllTransacts(conn)
    transacts = OrderedDict()
    for action in transacts_temp:
        if action[9] is None:
            pb_assign = []
        elif type(action[9]) is str:
            if len(action[9]) == 0:
                pb_assign = []
            else:
                pb_assign = ast.literal_eval(action[9])
        id = action[0]
        transacts[id] = Transaction(id,datetime.fromtimestamp(action[1]),action[2],action[3],action[4],action[5],action[6],action[7],accountsLookup(action[8]),pb_assign)
    return transacts

def writeTransacts2DB(transacts):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    data = []
    for id,action in transacts.items():
        data.append(object2list(action))
    with conn:
        writeMany(conn,data)

def deleteAllFromTable(table):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    db_file_backup = home + "/Documents/db_backup.db"
    copyfile(db_file, db_file_backup)
    conn = create_connection(db_file)
    with conn:
        deleteAll(conn,table)

def importTable(table,tags=False):
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        raw_data,cnames = read(conn, table)
    if tags:
        data = {}
        for el in raw_data:
            data[el[1]] = el[2]
    else:
        data = []
        for row in raw_data:
            row_dict = {}
            for i,el in enumerate(row):
                if i > 0:
                    row_dict[cnames[i]] = el
            data.append(row_dict)
    return data

def writeTable(table,data):
    deleteAllFromTable(table)
    home = str(Path.home())
    db_file = home + "/Documents/db.db"
    conn = create_connection(db_file)
    with conn:
        writeManyTable(conn, table, data)



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