import sqlite3
con = sqlite3.connect('db.sqlite')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS Users (
                uid INTEGER,
                balance INTEGER
)''')
con.commit()


def check_user(uid):
    cur.execute(f'SELECT * FROM Users WHERE uid = {uid}')
    user = cur.fetchone()
    if user:
        return True
    return False


def add_user(uid):
    cur.execute(f'INSERT INTO Users VALUES ({uid}, 0)')
    con.commit()


def get_balance(uid):
    cur.execute(f'SELECT balance FROM Users WHERE uid = {uid}')
    balance = cur.fetchone()[0]
    return balance

def add_balance(uid, amount):
    cur.execute(f'UPDATE Users SET balance = balance + {amount} WHERE uid = {uid}')
    con.commit()

def decrease_balance(uid, amount):
    cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE uid = {uid}')
    con.commit()