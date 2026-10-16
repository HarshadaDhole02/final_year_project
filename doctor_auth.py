
from auth import hash_password, verify_password
from db import get_db_connection


def register_doctor(full_name, username, password):
    connection = get_db_connection()

    if connection is None:
        return False, "Database connection failed."

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
                (full_name, username, password_hash, role)
            VALUES (%s, %s, %s, 'doctor')
            """,
            (
                full_name.strip(),
                username.strip(),
                hash_password(password)
            )
        )

        connection.commit()
        return True, "Doctor registered successfully!"

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return False, "This username is already registered."

        print("Doctor registration error:", error)
        return False, "Registration failed. Please check the database."

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def authenticate_doctor(username, password):
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
            WHERE username = %s AND role = 'doctor'
            """,
            (username.strip(),)
        )

        doctor = cursor.fetchone()

        if doctor is None:
            return None

        user_id, full_name, db_username, stored_hash, role = doctor

        if verify_password(password, stored_hash):
            return {
                "user_id": user_id,
                "full_name": full_name,
                "username": db_username,
                "role": role
            }

        return None

    except Exception as error:
        print("Doctor login error:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
