
from auth import verify_password
from db import get_db_connection


def authenticate_admin(username, password):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id, full_name, username, password_hash, role
            FROM users
            WHERE username = %s AND role = 'admin'
            """,
            (username.strip(),)
        )

        admin = cursor.fetchone()

        if admin is None:
            return None

        user_id, full_name, db_username, stored_hash, role = admin

        if verify_password(password, stored_hash):
            return {
                "user_id": user_id,
                "full_name": full_name,
                "username": db_username,
                "role": role
            }

        return None

    except Exception as error:
        print("Admin login error:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()
