import sqlite3
from pathlib import Path


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
    names = list(map(lambda x: x[0], cur.description))
    return data,names

def write(conn, row):
    sql = ''' INSERT INTO transacts(id,date,type,recipient,reference,amount,currency,tag,sub_tag,account,pb_assign)
              VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, row)
    return cur.lastrowid


def writeMany(conn, data):
    sql = ''' INSERT INTO transacts(id,date,type,recipient,reference,amount,currency,tag,sub_tag,account,pb_assign)
              VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.executemany(sql, data)
    return cur.lastrowid

def writeManyTable(conn, table, data):
    cols = ', '.join('"{}"'.format(col) for col in data[0].keys())
    vals = ', '.join(':{}'.format(col) for col in data[0].keys())
    sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(table, cols, vals)
    cur = conn.cursor()
    cur.executemany(sql, data)
    conn.commit()

def writeManyTags(conn, data):
    sql = ' INSERT INTO tags(ref,cat) VALUES(?,?) '
    cur = conn.cursor()
    cur.executemany(sql, data)
    return cur.lastrowid

def updatePBAssign(conn,id,pb_assign):
    sql = 'UPDATE transacts SET pb_assign = ? WHERE ID = ?'
    cur = conn.cursor()
    cur.execute(sql,(pb_assign,id))
    return cur.lastrowid


def deleteAll(conn,table):
    sql = "delete from "+table
    cur = conn.cursor()
    cur.execute(sql)
    sql = "delete from sqlite_sequence where name='"+table+"'"
    cur.execute(sql)
    return 0

