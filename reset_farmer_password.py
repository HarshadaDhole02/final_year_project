
from auth import hash_password
from db import get_db_connection

username = "Ram@12"
new_password = input("Enter your new farmer password: ")

if not new_password:
    print("Password cannot be empty.")
else:
    connection = get_db_connection()

    if connection is None:
        print("Database connection failed.")
    else:
        cursor = None

        try:
            cursor = connection.cursor()
            new_hash = hash_password(new_password)

            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE username = %s AND role = 'farmer'
                """,
                (new_hash, username)
            )

            if cursor.rowcount == 1:
                connection.commit()
                print("Password reset successfully for", username)
            else:
                connection.rollback()
                print("Farmer account not found. Password was not changed.")

        except Exception as error:
            connection.rollback()
            print("Password reset failed:", error)

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()
