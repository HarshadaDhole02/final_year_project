
from mysql.connector import connection_cext

import os
import mysql.connector
import streamlit as st



def get_db_connection():
    """Create a connection to the AgriCare MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("AGRICARE_DB_HOST", "localhost"),
            user=os.getenv("AGRICARE_DB_USER", "root"),
            password="harshada@1702",
            database="agricare_db",
            port=int(os.getenv("AGRICARE_DB_PORT", "3306"))
        )
        return connection

    except mysql.connector.Error as error:
        st.error(f"Database connection failed: {error}")
        return None


def save_disease_report(
    animal_id,
    predicted_disease,
    confidence,
    severity,
    image_path=None
):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO disease_reports (
                animal_id,
                predicted_disease,
                confidence,
                severity,
                image_path,
                review_status
            )
            VALUES (%s, %s, %s, %s, %s, 'pending')
            """,
            (
                animal_id,
                predicted_disease,
                float(confidence),
                severity,
                image_path
            )
        )

        connection.commit()
        return cursor.lastrowid

    except Exception as error:
        connection.rollback()
        print("Failed to save disease report:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def update_disease_report(report_id, doctor_notes, review_status):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE disease_reports
            SET doctor_notes = %s,
                review_status = %s
            WHERE report_id = %s
            """,
            (doctor_notes, review_status, report_id)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as error:
        connection.rollback()
        print("Update disease report error:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def get_available_doctors():
    """Return registered doctors for the farmer to choose from."""
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, full_name, username, village_id
            FROM users
            WHERE role = 'doctor'
            ORDER BY full_name
        """)

        return cursor.fetchall()

    except Exception as error:
        print("Fetch doctors error:", error)
        return []

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def create_consultation_request(
    report_id,
    farmer_id,
    doctor_id,
    message=""
):
    """Save a farmer's request for a selected doctor."""
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = None

    try:
        cursor = connection.cursor()

        # Verify that the selected doctor is actually a doctor.
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE user_id = %s AND role = 'doctor'
        """, (doctor_id,))

        if cursor.fetchone() is None:
            return False

        # Verify that the report belongs to this farmer's animal.
        cursor.execute("""
            SELECT dr.report_id
            FROM disease_reports dr
            JOIN animals a ON a.animal_id = dr.animal_id
            WHERE dr.report_id = %s
              AND a.owner_user_id = %s
        """, (report_id, farmer_id))

        if cursor.fetchone() is None:
            return False

        cursor.execute("""
            INSERT INTO consultation_requests
                (report_id, farmer_id, doctor_id, message)
            VALUES (%s, %s, %s, %s)
        """, (
            report_id,
            farmer_id,
            doctor_id,
            message.strip() if message else None
        ))

        connection.commit()
        return True

    except Exception as error:
        connection.rollback()
        print("Create consultation request error:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
