
import hashlib
import hmac
import secrets

from db import get_db_connection


def hash_password(password):
    """Hash a password before storing it."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + "$" + password_hash.hex()


def verify_password(password, stored_hash):
    """Verify a password against its stored hash."""
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return hmac.compare_digest(
            calculated_hash.hex(),
            hash_hex
        )
    except (ValueError, TypeError):
        return False


def register_farmer(full_name, username, password, village_id):
    """Register a farmer in the database."""
    connection = get_db_connection()

    if connection is None:
        return False, "Database connection failed."

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
                (full_name, username, password_hash, role, village_id)
            VALUES (%s, %s, %s, 'farmer', %s)
            """,
            (
                full_name.strip(),
                username.strip(),
                hash_password(password),
                village_id
            )
        )

        connection.commit()
        return True, "Registration successful!"

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return False, "This username is already registered."

        return False, "Registration failed. Please check the database."

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def register_admin(full_name, username, password):
    from db import get_db_connection

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
            VALUES (%s, %s, %s, 'admin')
            """,
            (
                full_name.strip(),
                username.strip(),
                hash_password(password)
            )
        )

        connection.commit()
        return True, "Admin account created successfully."

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return False, "This username already exists."

        print("Admin registration error:", error)
        return False, "Admin account creation failed. Check the database."

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def authenticate_farmer(username, password):
    """Authenticate a registered farmer."""
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
            WHERE username = %s AND role = 'farmer'
            """,
            (username.strip(),)
        )

        farmer = cursor.fetchone()

        if farmer is None:
            return None

        user_id, full_name, db_username, stored_hash, role = farmer

        if verify_password(password, stored_hash):
            return {
                "user_id": user_id,
                "full_name": full_name,
                "username": db_username,
                "role": role
            }

        return None

    except Exception as error:
        print("Farmer login error:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def authenticate_farmer(username, password):
    """Authenticate a registered farmer."""
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
            WHERE username = %s AND role = 'farmer'
            """,
            (username.strip(),)
        )

        farmer = cursor.fetchone()

        if farmer is None:
            return None

        user_id, full_name, db_username, stored_hash, role = farmer

        if verify_password(password, stored_hash):
            return {
                "user_id": user_id,
                "full_name": full_name,
                "username": db_username,
                "role": role
            }

        return None

    except Exception as error:
        print("Farmer login error:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
