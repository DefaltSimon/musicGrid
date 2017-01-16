# coding=utf-8
import hashlib
import sqlite3
import random

from data.dbmanager import DatabaseManager

KEY_LENGTH = 128


def main():
    print("Generating random key...")

    # Key length with hexlify is double the os.urandom
    rand_bits = str(random.getrandbits(KEY_LENGTH)).encode("utf-8")
    key = hashlib.sha512(rand_bits).hexdigest()

    print("Your key:{}".format(key))

    add = input("Add this key to the database (data/cert.db)? y/n")

    if str(add).lower() == "y":
        db = DatabaseManager()

        try:
            db.insert_key(key)
            print("Key added.")
        except UserWarning:
            print("Key already exists in the database. Now you should feel like you hit the jackpot.\n"
                  "(Seriously though, restart the script to get a new key.)")


if __name__ == '__main__':
    main()
