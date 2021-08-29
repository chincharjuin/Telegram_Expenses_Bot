import sqlite3

from ex_BUILTINS import (
    EXPECTED_INFORMATION,
)

def setup(dbname) -> None:
    """
    Sets up the SQL database.
    """
    statements = [
        'CREATE TABLE IF NOT EXISTS expenses (\
            owner string, \
            updateid integer, \
            dt datetime, \
            description text, \
            amount integer, \
            shop string, \
            location string, \
            purpose text, \
            payment string, \
            verified string)',
        'CREATE INDEX IF NOT EXISTS itemIndex ON expenses (description ASC)',
        'CREATE INDEX IF NOT EXISTS ownerIndex ON expenses (owner ASC)',
        'CREATE INDEX IF NOT EXISTS datetimeIndex ON expenses (datetime DESC)',
        'CREATE INDEX IF NOT EXISTS pendingIndex ON expenses (verified ASC)'
    ]

    with sqlite3.connect(dbname) as conn:
        cur = conn.cursor()
        for statement in statements:
            cur.execute(statement)
        conn.commit()

def execute(statement, values) -> None:
    with sqlite3.connect(DBNAME) as conn:
        cur = conn.cursor()
        cur.execute(statement, values)
        conn.commit()

def fetch(statement, values) -> list:
    with sqlite3.connect(DBNAME) as conn:
        cur = conn.cursor()
        cur.execute(statement, values)
        conn.commit()
        return cur.fetchall()

def add(user_data) -> None:
    """
    Adds the values from user_data to the database.
    """
    statement = 'INSERT INTO expenses VALUES (?,?,?,?,?,?,?,?,?,?)'
    values = tuple([user_data.get(name, '') for name in EXPECTED_INFORMATION])

    return execute(statement, values)
