
from db import get_db_connection

connection = get_db_connection()

if connection and connection.is_connected():
    print("AgriCare AI database connected successfully!")

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")

    print("Tables in agricare_db:")
    for table in cursor.fetchall():
        print("-", table[0])

    cursor.close()
    connection.close()
else:
    print("Connection failed. Check the error above.")
