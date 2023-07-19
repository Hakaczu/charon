import os
import mysql.connector as database

username = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
try:
    connection = database.connect(
        user=username,
        password=password,
        host="localhost",
        database="charon"
        )
    cursor = connection.cursor()
except database.Error as e:
    print(f"Error retrieving entry from database: {e}")

def get_currencies():
    try:
        stmt = "SELECT name, code FROM currencies"
        cursor.execute(stmt)
        for (name, code) in cursor:
            print(f"Successfully retrieved {name}, {code}")
    except database.Error as e: 
        print(f"Error retrieving entry from database: {e}")

get_currencies()
connection.close()