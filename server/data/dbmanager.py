# coding=utf-8
import sqlite3


class DatabaseManager:
    def __init__(self):
        # KEEP IN MIND
        # IN THIS APPLICATION USER INPUT IS TRUSTED, THAT IS WHY .format is used!

        self.db_path = "data/cred.db"

        db = self.connect()
        c = db.cursor()
        if not c.execute("select * from sqlite_master where TYPE='table'").fetchall():
            self.create_table()

            db.commit()
        db.close()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_table(self):
        db = self.connect()
        c = db.cursor()

        c.execute("CREATE TABLE KEYS (api_key TEXT PRIMARY KEY)")
        db.commit()
        db.close()

    def insert_key(self, key):
        db = self.connect()
        c = db.cursor()

        if not self.key_exists(key):
            c.execute("INSERT INTO KEYS (api_key) VALUES ('{}')".format(key))
            db.commit()
            db.close()
        else:
            db.close()
            raise UserWarning("key already exists")

    def remove_key(self, key):
        db = self.connect()
        c = db.cursor()

        c.execute("DELETE FROM KEYS WHERE api_key='{}'".format(key))
        db.commit()
        db.close()

    def key_exists(self, key):
        db = self.connect()
        c = db.cursor()

        resp = c.execute("SELECT * FROM KEYS WHERE api_key='{}'".format(key)).fetchall()

        db.commit()
        db.close()
        return resp != []
