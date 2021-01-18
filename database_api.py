from database import *
from Transaction import Transaction
from datetime import datetime


def getAllTransacts():
    db_file = "db.db"
    conn = create_connection(db_file)
    with conn:
        transacts_temp = fetchAllTransacts(conn)
    transacts = []
    for action in transacts_temp:
        transacts.append(Transaction(datetime.fromtimestamp(action[1]),action[2],action[3],action[4],action[5],action[6],action[7],action[8]))
    return transacts

def getMonthlyTransacts(transacts, month,year):
    start = datetime(year,month,1)
    if month < 12:
        end = datetime(year,month+1,1)
    else:
        end = datetime(year + 1, month, 1)
    monthly_transacts = []
    for action in transacts:
        if action.date >= start and action.date < end:
            monthly_transacts.append(action)

    return monthly_transacts