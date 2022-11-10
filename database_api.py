from database import *
from Transaction import Transaction
from datetime import datetime
from Account import accountsLookup
from pathlib import Path
import ast
from collections import OrderedDict
from shutil import copyfile



mm_dir_path = Path(__file__).parent
home = Path.home()
if str(home) == "/Users/loris":
    db_file = home / "Documents" / "MoneyManager" / "db_private.db"
    db_file_backup = home / "Documents"/ "MoneyManager" / "db_private_backup.db"
else:
    db_file = mm_dir_path / "db.db"
    db_file_backup = mm_dir_path / "db_backup.db"


def object2list(action):
    l = [action.id,int(action.date.timestamp()), action.type, action.recipient, action.reference, str(action.amount), action.currency, action.tag, action.sub_tag,action.account.name,str(action.pb_assign)]
    return l

def displayTransact(action):
    l = [action.id, action.date, action.type, action.recipient, action.reference, str(action.amount),
         action.currency, action.tag, action.account.name, str(action.pb_assign)]
    return l

def getAllTransacts():
    conn = create_connection(db_file)
    with conn:
        transacts_temp = fetchAllTransacts(conn)
    transacts = OrderedDict()
    for action in transacts_temp:
        if action[10] is None:
            pb_assign = []
        elif type(action[10]) is str:
            if len(action[10]) == 0:
                pb_assign = []
            else:
                pb_assign = ast.literal_eval(action[10])
        id = action[0]
        transacts[id] = Transaction(id,datetime.fromtimestamp(action[1]),action[2],action[3],action[4],action[5],action[6],action[7],action[8],accountsLookup(action[9]),pb_assign)

        sorted_transacts = sorted(list(transacts.items()), key=lambda key_value: key_value[1].date)
        sorted_transacts = OrderedDict(sorted_transacts)

    return sorted_transacts

def writeTransacts2DB(transacts):
    conn = create_connection(db_file)
    data = []
    for id,action in transacts.items():
        data.append(object2list(action))
    with conn:
        writeMany(conn,data)

def deleteAllFromTable(table):
    copyfile(db_file, db_file_backup)
    conn = create_connection(db_file)
    with conn:
        deleteAll(conn,table)

def importTable(table,tags=False):
    conn = create_connection(db_file)
    with conn:
        raw_data,cnames = read(conn, table)
    if tags:
        data = {}
        for el in raw_data:
            data[el[1]] = (el[2],el[3])
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
    conn = create_connection(db_file)
    with conn:
        writeManyTable(conn, table, data)



def writeTags(tags):
    conn = create_connection(db_file)
    deleteAllFromTable("tags")
    data = []
    for key in tags:
        temp = [key,tags[key][0],tags[key][1]]
        data.append(temp)
    with conn:
        writeManyTags(conn,data)


def updateMany(transacts):
    conn = create_connection(db_file)
    with conn:
        for action in transacts:
            updatePBAssign(conn,action.id, action.pb_assign)


if __name__ == '__main__':
    transacts = getAllTransacts()
    for action in transacts:
        print(action.recipient)