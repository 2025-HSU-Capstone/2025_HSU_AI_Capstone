import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="smartfridge"
    )
    print("MySQL connection success")
except Exception as e:
    print("MySQL connection failed:", e)
