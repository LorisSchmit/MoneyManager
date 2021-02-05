import sqlite3

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn

def fetchAllTransacts(conn):
    sql = 'SELECT * FROM transacts'
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

def read(conn, table):
    sql = 'SELECT * FROM '+table
    cur = conn.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    return data

def write(conn, row):
    sql = ''' INSERT INTO transacts(date,type,recipient,reference,amount,currency,tag,account)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, row)
    return cur.lastrowid


def writeMany(conn, data):
    sql = ''' INSERT INTO transacts(date,type,recipient,reference,amount,currency,tag,account)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.executemany(sql, data)
    return cur.lastrowid

def writeManyTags(conn, data):
    sql = ' INSERT INTO tags(ref,cat) VALUES(?,?) '
    cur = conn.cursor()
    cur.executemany(sql, data)
    return cur.lastrowid

def main():
    db_file = "/Users/lorisschmit1/PycharmProjects/BudgetManager/Expenses.db"
    conn = create_connection(db_file)
    with conn:
        row = ('1/2/2020','test_type','test_recipient','test_reference',40.2,'EUR','test_tag','Girokonto')
        write(conn,row)
        select(conn)


def deleteAll(conn,table):
    sql = "delete from "+table
    cur = conn.cursor()
    cur.execute(sql)
    sql = "delete from sqlite_sequence where name='"+table+"'"
    cur.execute(sql)
    return 0
