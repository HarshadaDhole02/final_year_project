
from auth import register_farmer, authenticate_farmer
from admin_auth import authenticate_admin
from db import (
    get_db_connection,
    save_disease_report,
    update_disease_report,
    get_available_doctors,
    create_consultation_request
)
from doctor_auth import register_doctor, authenticate_doctor
import os
import tempfile
# pyrefly: ignore [missing-import]
import streamlit as st
from PIL import Image
from predict import load_model_and_classes, predict_image

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="PashuVet",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)
def farmer_login(language):
    st.subheader("Farmer Login")

    with st.form("farmer_login_form_main"):
        username = st.text_input("Username", key="farmer_login_username")
        password = st.text_input(
            "Password",
            type="password",
            key="farmer_login_password"
        )
        submitted = st.form_submit_button("Login")

    if submitted:
        if not username.strip() or not password:
            st.warning("Please enter both username and password.")
        else:
            farmer = authenticate_farmer(username, password)

            if farmer:
                st.session_state["logged_in_farmer"] = farmer
                st.success(f"Welcome, {farmer['full_name']}!")
                st.rerun()
            else:
                st.error("Invalid farmer username or password.")


def farmer_registration(language):
    is_marathi = language == "मराठी"

    labels = {
        "title": "शेतकरी नोंदणी" if is_marathi else "Farmer Registration",
        "name": "पूर्ण नाव" if is_marathi else "Full Name",
        "username": "वापरकर्तानाव" if is_marathi else "Username",
        "password": "पासवर्ड" if is_marathi else "Password",
        "village": "गावाचे नाव" if is_marathi else "Village Name",
        "district": "जिल्हा" if is_marathi else "District",
        "state": "राज्य" if is_marathi else "State",
        "register": "नोंदणी करा" if is_marathi else "Register",
    }

    with st.expander("👨‍🌾 " + labels["title"]):
        with st.form("farmer_registration_form_main"):
            full_name = st.text_input(labels["name"])
            username = st.text_input(labels["username"])
            password = st.text_input(
                labels["password"], type="password"
            )
            village_name = st.text_input(labels["village"])
            district = st.text_input(labels["district"])
            state = st.text_input(
                labels["state"],
                value="Maharashtra"
            )

            submitted = st.form_submit_button(labels["register"])

        if submitted:
            if not all([
                full_name.strip(),
                username.strip(),
                password,
                village_name.strip(),
                district.strip(),
                state.strip()
            ]):
                st.error(
                    "कृपया सर्व माहिती भरा."
                    if is_marathi else
                    "Please fill in all fields."
                )
                return

            if len(password) < 8:
                st.error(
                    "पासवर्ड किमान ८ अक्षरांचा असावा."
                    if is_marathi else
                    "Password must be at least 8 characters."
                )
                return

            connection = get_db_connection()

            if connection is None:
                return

            cursor = None
            village_id = None

            try:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO villages
                        (village_name, district, state)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        village_id = LAST_INSERT_ID(village_id)
                    """,
                    (
                        village_name.strip(),
                        district.strip(),
                        state.strip()
                    )
                )

                village_id = cursor.lastrowid
                connection.commit()

            except Exception:
                connection.rollback()
                st.error(
                    "गावाची माहिती जतन करता आली नाही."
                    if is_marathi else
                    "Could not save village information."
                )
                return

            finally:
                if cursor is not None:
                    cursor.close()
                connection.close()

            success, message = register_farmer(
                full_name,
                username,
                password,
                village_id
            )

            if success:
                st.success(
                    "नोंदणी यशस्वी झाली!"
                    if is_marathi else
                    "Farmer registered successfully!"
                )
            elif "already registered" in message.lower():
                st.error(
                    "हे वापरकर्तानाव आधीच वापरले आहे."
                    if is_marathi else message
                )
            else:
                st.error(
                    "नोंदणी अयशस्वी झाली."
                    if is_marathi else message
                )

    
def animal_registration(language):
    is_marathi = language == "मराठी"

    title = "जनावराची नोंदणी" if is_marathi else "Animal Registration"
    animal_name_label = "जनावराचे नाव (ऐच्छिक)" if is_marathi else "Animal Name (optional)"
    animal_type_label = "जनावराचा प्रकार" if is_marathi else "Animal Type"
    breed_label = "जात" if is_marathi else "Breed"
    age_label = "वय (वर्षे)" if is_marathi else "Age (years)"
    submit_label = "जनावर नोंदवा" if is_marathi else "Register Animal"
    farmer_label = "शेतकरी निवडा" if is_marathi else "Select Farmer"

    animal_types = (
        ["गाय", "म्हैस"]
        if is_marathi
        else ["Cow", "Buffalo"]
    )

    type_mapping = {
        "गाय": "Cow",
        "म्हैस": "Buffalo"
    }

    with st.expander("🐄 " + title):

        # Fetch registered farmers
        connection = get_db_connection()

        if connection is None:
            return

        cursor = None

        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT user_id, full_name, username
                FROM users
                WHERE role = 'farmer'
                ORDER BY full_name
                """
            )
            farmers = cursor.fetchall()

        except Exception:
            st.error(
                "शेतकऱ्यांची माहिती मिळाली नाही."
                if is_marathi
                else "Could not load farmer records."
            )
            return

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

        if not farmers:
            st.info(
                "प्रथम शेतकऱ्याची नोंदणी करा."
                if is_marathi
                else "Please register a farmer first."
            )
            return

        farmer_options = {
            f"{farmer[1]} ({farmer[2]})": farmer[0]
            for farmer in farmers
        }

        with st.form("animal_registration_form"):

            selected_farmer = st.selectbox(
                farmer_label,
                list(farmer_options.keys())
            )

            animal_name = st.text_input(animal_name_label)

            animal_type = st.selectbox(
                animal_type_label,
                animal_types
            )

            breed = st.text_input(breed_label)

            age = st.number_input(
                age_label,
                min_value=0.0,
                max_value=100.0,
                value=2.0,
                step=0.5
            )

            submitted = st.form_submit_button(submit_label)

        if submitted:

            connection = get_db_connection()

            if connection is None:
                return

            cursor = None

            try:
                cursor = connection.cursor()

                db_animal_type = type_mapping.get(
                    animal_type,
                    animal_type
                )

                cursor.execute(
                    """
                    INSERT INTO animals
                    (
                        animal_name,
                        animal_type,
                        breed,
                        age_years,
                        owner_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        animal_name.strip() or None,
                        db_animal_type,
                        breed.strip() or None,
                        age,
                        farmer_options[selected_farmer]
                    )
                )

                connection.commit()

                st.success(
                    "जनावराची नोंदणी यशस्वी झाली!"
                    if is_marathi
                    else "Animal registered successfully!"
                )

            except Exception:
                connection.rollback()

                st.error(
                    "जनावराची नोंदणी अयशस्वी झाली."
                    if is_marathi
                    else "Animal registration failed. Please check the database."
                )

            finally:
                if cursor is not None:
                    cursor.close()
                connection.close()


def get_registered_animals(farmer_id):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                a.animal_id,
                a.animal_name,
                a.animal_type,
                a.breed,
                u.full_name
            FROM animals a
            JOIN users u ON a.owner_user_id = u.user_id
            WHERE a.owner_user_id = %s
              AND u.role = 'farmer'
            ORDER BY a.animal_id
        """, (farmer_id,))

        return cursor.fetchall()

    except Exception as error:
        print("Could not load registered animals:", error)
        return []

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

def doctor_portal(language):
    is_marathi = language == "मराठी"

    title = "डॉक्टर पोर्टल" if is_marathi else "Doctor Portal"
    login_tab = "लॉगिन" if is_marathi else "Login"
    register_tab = "नोंदणी" if is_marathi else "Register"
    username_label = "वापरकर्तानाव" if is_marathi else "Username"
    password_label = "पासवर्ड" if is_marathi else "Password"
    name_label = "पूर्ण नाव" if is_marathi else "Full Name"
    login_button = "लॉगिन करा" if is_marathi else "Log In"
    register_button = "डॉक्टर म्हणून नोंदणी करा" if is_marathi else "Register as Doctor"

    st.subheader("🩺 " + title)

    login_tab_ui, register_tab_ui = st.tabs([login_tab, register_tab])

    with login_tab_ui:
        with st.form("doctor_login_form"):
            username = st.text_input(username_label, key="doctor_login_username")
            password = st.text_input(
                password_label,
                type="password",
                key="doctor_login_password"
            )
            submitted = st.form_submit_button(login_button)

        if submitted:
            if not username.strip() or not password:
                st.warning(
                    "सर्व माहिती भरा." if is_marathi
                    else "Please enter your username and password."
                )
            else:
                doctor = authenticate_doctor(username, password)

                if doctor:
                    st.session_state["logged_in_doctor"] = doctor
                    st.success(
                        ("स्वागत आहे, " if is_marathi else "Welcome, ")
                        + doctor["full_name"]
                    )
                else:
                    st.error(
                        "लॉगिन अयशस्वी." if is_marathi
                        else "Invalid credentials or doctor account not found."
                    )

    with register_tab_ui:
        with st.form("doctor_register_form"):
            full_name = st.text_input(name_label, key="doctor_register_name")
            new_username = st.text_input(
                username_label, key="doctor_register_username"
            )
            new_password = st.text_input(
                password_label,
                type="password",
                key="doctor_register_password"
            )
            confirm_password = st.text_input(
                "पासवर्ड पुन्हा टाका" if is_marathi else "Confirm Password",
                type="password",
                key="doctor_register_confirm"
            )
            submitted = st.form_submit_button(register_button)

        if submitted:
            if not full_name.strip() or not new_username.strip() or not new_password:
                st.warning(
                    "सर्व माहिती भरा." if is_marathi
                    else "Please complete all fields."
                )
            elif len(new_password) < 8:
                st.warning(
                    "पासवर्डमध्ये किमान ८ अक्षरे असावीत."
                    if is_marathi
                    else "Password must be at least 8 characters."
                )
            elif new_password != confirm_password:
                st.error(
                    "पासवर्ड जुळत नाहीत." if is_marathi
                    else "Passwords do not match."
                )
            else:
                success, message = register_doctor(
                    full_name, new_username, new_password
                )

                if success:
                    st.success(message)
                    st.info(
                        "आता लॉगिन करा." if is_marathi
                        else "Registration complete. Please log in."
                    )
                else:
                    st.error(message)

    doctor = st.session_state.get("logged_in_doctor")

    if doctor:
        st.success(
            ("लॉगिन केले: " if is_marathi else "Logged in as: ")
            + doctor["full_name"]
        )

        if st.button(
            "लॉगआउट" if is_marathi else "Log Out",
            key="doctor_logout"
        ):
            del st.session_state["logged_in_doctor"]
            st.rerun()



def doctor_dashboard():
    doctor = st.session_state.get("logged_in_doctor")

    if not doctor:
        return

    st.subheader("📋 Doctor Dashboard")

    connection = get_db_connection()

    if connection is None:
        st.error("Could not connect to the database.")
        return

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # ==========================================
        # 1. FARMER CONSULTATION REQUESTS
        # ==========================================
        st.markdown("---")
        st.subheader("🩺 Farmer Consultation Requests")

        cursor.execute("""
            SELECT
                cr.request_id,
                cr.report_id,
                cr.farmer_id,
                cr.message,
                cr.status AS request_status,
                cr.doctor_advice,
                cr.created_at,
                u.full_name AS farmer_name,
                a.animal_name,
                a.animal_type,
                dr.predicted_disease,
                dr.severity,
                dr.image_path
            FROM consultation_requests cr
            JOIN users u
                ON cr.farmer_id = u.user_id
            JOIN disease_reports dr
                ON cr.report_id = dr.report_id
            JOIN animals a
                ON dr.animal_id = a.animal_id
            WHERE cr.doctor_id = %s
            ORDER BY cr.created_at DESC
        """, (doctor["user_id"],))

        consultation_requests = cursor.fetchall()

        if not consultation_requests:
            st.info(
                "No consultation requests assigned to you yet."
            )
        else:
            st.write(
                f"Total consultation requests: "
                f"{len(consultation_requests)}"
            )

            for request in consultation_requests:
                st.markdown("---")

                st.markdown(
                    f"### Consultation #{request['request_id']}"
                )

                st.write(
                    f"**Farmer:** {request['farmer_name']}"
                )
                st.write(
                    f"**Animal:** "
                    f"{request['animal_name'] or request['animal_type']}"
                )
                st.write(
                    f"**Disease:** {request['predicted_disease']}"
                )
                st.write(
                    f"**Severity:** {request['severity']}"
                )
                st.write(
                    f"**Farmer's Message:** "
                    f"{request['message'] or 'No message provided'}"
                )
                st.write(
                    f"**Request Status:** {request['request_status']}"
                )

                image_path = request.get("image_path")

                if image_path and os.path.isfile(image_path):
                    st.image(
                        image_path,
                        caption="Animal photo",
                        width=300
                    )

                status_options = [
                    "Pending",
                    "Accepted",
                    "Completed",
                    "Rejected"
                ]

                current_request_status = request["request_status"]

                if current_request_status not in status_options:
                    current_request_status = "Pending"

                with st.form(
                    f"consultation_form_{request['request_id']}"
                ):
                    advice = st.text_area(
                        "Your Advice to the Farmer",
                        value=request["doctor_advice"] or "",
                        key=f"advice_{request['request_id']}"
                    )

                    new_status = st.selectbox(
                        "Update Request Status",
                        status_options,
                        index=status_options.index(
                            current_request_status
                        ),
                        key=f"consult_status_{request['request_id']}"
                    )

                    if st.form_submit_button(
                        "Save Consultation Response"
                    ):
                        cursor.execute("""
                            UPDATE consultation_requests
                            SET doctor_advice = %s,
                                status = %s
                            WHERE request_id = %s
                              AND doctor_id = %s
                        """, (
                            advice,
                            new_status,
                            request["request_id"],
                            doctor["user_id"]
                        ))

                          # Also save doctor's advice in the linked disease report
                        cursor.execute("""
                            UPDATE disease_reports
                            SET doctor_notes = %s,
                                review_status = 'reviewed'
                            WHERE report_id = %s
                        """, (
                            advice,
                            request["report_id"]
                        ))


                        connection.commit()

                        st.success(
                            "Consultation response saved successfully!"
                        )
                        st.rerun()

        # ==========================================
        # 2. EXISTING DISEASE REPORTS
        # ==========================================
       
    except Exception as error:
        st.error("Could not load the Doctor Dashboard.")
        print("Doctor dashboard error:", error)

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def admin_dashboard():
    st.subheader("📊 Animal Health Monitoring Dashboard")

    connection = get_db_connection()

    if connection is None:
        st.error("Could not connect to the database.")
        return

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                COUNT(*) AS total_reports,
                SUM(
                    CASE
                        WHEN LOWER(review_status) = 'pending'
                        THEN 1 ELSE 0
                    END
                ) AS pending_reports,
                SUM(
                    CASE
                        WHEN LOWER(review_status) = 'reviewed'
                        THEN 1 ELSE 0
                    END
                ) AS reviewed_reports
            FROM disease_reports
        """)
        
        summary = cursor.fetchone()

        st.metric(
            "🐄 Total Disease Reports",
            summary["total_reports"] or 0
        )

      
        cursor.execute("""
            SELECT
                COALESCE(v.village_name, 'Unknown') AS village,
                COUNT(dr.report_id) AS total_reports
            FROM disease_reports dr
            JOIN animals a
                ON dr.animal_id = a.animal_id
            JOIN users u
                ON a.owner_user_id = u.user_id
            LEFT JOIN villages v
                ON u.village_id = v.village_id
            GROUP BY v.village_name
            ORDER BY total_reports DESC
        """)

        village_reports = cursor.fetchall()

        st.markdown("### 🏡 Village-wise Reports")

        if village_reports:
            st.dataframe(
                village_reports,
                use_container_width=True
            )
        else:
            st.info("No village reports available yet.")

        cursor.execute("""
            SELECT
                predicted_disease,
                COUNT(*) AS total
            FROM disease_reports
            GROUP BY predicted_disease
            ORDER BY total DESC
        """)

        disease_reports = cursor.fetchall()

        
        st.markdown("### 🐄 Disease Prediction Summary")

        if disease_reports:
            st.dataframe(
                disease_reports,
                use_container_width=True
            )

            # Disease Prediction Bar Chart
            import pandas as pd

            disease_df = pd.DataFrame(
                disease_reports,
                columns=["predicted_disease", "total"]
            )

            st.markdown("#### 📊 Disease-wise Report Chart")

            st.bar_chart(
                disease_df,
                x="predicted_disease",
                y="total",
                x_label="Disease",
                y_label="Number of Reports"
            )

        else:
            st.info("No disease predictions available yet.")

        
    except Exception as error:
        st.error("Could not load the admin dashboard.")
        print("Admin dashboard error:", error)

    finally:
        if cursor is not None:
            cursor.close()
    
    
    st.divider()
    st.subheader("🚨 Village Disease Outbreak Alerts")

    detect_village_outbreaks()

    connection = get_db_connection()

    if connection is not None:
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    v.village_name,
                    v.district,
                    oa.predicted_disease,
                    oa.report_count,
                    oa.window_days,
                    oa.alert_status,
                    oa.created_at
                FROM outbreak_alerts oa
                JOIN villages v
                    ON oa.village_id = v.village_id
                ORDER BY oa.created_at DESC
            """)

            alerts = cursor.fetchall()

            if alerts:
                for alert in alerts:
                    st.warning(
                        f"📍 Village: {alert[0]}, {alert[1]}\n\n"
                        f"🦠 Disease: {alert[2]}\n\n"
                        f"📊 Reports in last {alert[4]} days: {alert[3]}\n\n"
                        f"Status: {alert[5]}"
                    )
            else:
                st.info(
                    "No potential outbreak alerts found yet. "
                    "At least 3 recent reports of the same disease "
                    "in one village are needed."
                )

        except Exception as error:
            st.error(f"Could not load outbreak alerts: {error}")

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()


def admin_portal():
    st.subheader("🔐 Admin Portal")

    with st.form("admin_login_form"):
        username = st.text_input("Admin Username", key="admin_username")
        password = st.text_input(
            "Admin Password",
            type="password",
            key="admin_password"
        )

        submitted = st.form_submit_button("Admin Login")

    if submitted:
        if not username.strip() or not password:
            st.warning("Please enter your username and password.")
        else:
            admin = authenticate_admin(username, password)

            if admin:
                st.session_state["logged_in_admin"] = admin
                st.success(f"Welcome, {admin['full_name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials or admin account not found.")

    admin = st.session_state.get("logged_in_admin")

    if admin:
        st.success(f"Logged in as Admin: {admin['full_name']}")

        if st.button("Admin Logout", key="admin_logout"):
            del st.session_state["logged_in_admin"]
            st.rerun()

    
def detect_village_outbreaks():
    connection = get_db_connection()

    if connection is None:
        print("Outbreak detection: database connection failed.")
        return

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                u.village_id,
                dr.predicted_disease,
                COUNT(*) AS report_count
            FROM disease_reports dr
            JOIN animals a
                ON dr.animal_id = a.animal_id
            JOIN users u
                ON a.owner_user_id = u.user_id
            WHERE u.role = 'farmer'
              AND u.village_id IS NOT NULL
              AND dr.created_at >= NOW() - INTERVAL 7 DAY
            GROUP BY
                u.village_id,
                dr.predicted_disease
            HAVING COUNT(*) >= 3
        """)

        results = cursor.fetchall()
        print("Outbreak detection matches:", results)

        for village_id, disease, report_count in results:
            cursor.execute("""
                SELECT alert_id
                FROM outbreak_alerts
                WHERE village_id = %s
                  AND predicted_disease = %s
                  AND alert_status IN (
                      'potential', 'under_review', 'verified'
                  )
                LIMIT 1
            """, (village_id, disease))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE outbreak_alerts
                    SET report_count = %s,
                        window_days = 7
                    WHERE alert_id = %s
                """, (report_count, existing[0]))
            else:
                cursor.execute("""
                    INSERT INTO outbreak_alerts (
                        village_id,
                        predicted_disease,
                        report_count,
                        window_days,
                        alert_status
                    )
                    VALUES (%s, %s, %s, 7, 'potential')
                """, (village_id, disease, report_count))

        connection.commit()
        print("Outbreak detection completed.")

    except Exception as error:
        connection.rollback()
        print("Outbreak detection error:", repr(error))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()



def show_animal_health_history(farmer_id):
    st.divider()
    st.subheader("📋 Animal Health History")

    connection = get_db_connection()

    if connection is None:
        st.error("Could not connect to the database.")
        return

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                a.animal_id,
                a.animal_name,
                a.animal_type,
                a.breed
            FROM animals a
            WHERE a.owner_user_id = %s
            ORDER BY a.animal_id DESC
        """, (farmer_id,))

        animals = cursor.fetchall()

        if not animals:
            st.info("Register an animal first to view its health history.")
            return

        animal_options = {
            f"{a['animal_name'] or a['animal_type']} "
            f"({a['animal_type']}) - ID {a['animal_id']}":
            a["animal_id"]
            for a in animals
        }

        selected_animal = st.selectbox(
            "Select an animal to view its history",
            options=list(animal_options.keys()),
            key="health_history_animal"
        )

        selected_animal_id = animal_options[selected_animal]

        cursor.execute("""
            SELECT
                report_id,
                predicted_disease,
                confidence,
                severity,
                review_status,
                doctor_notes,
                created_at
            FROM disease_reports
            WHERE animal_id = %s
            ORDER BY created_at DESC
        """, (selected_animal_id,))

        reports = cursor.fetchall()

        if reports:
            st.markdown("#### 🩺 Previous Disease Reports")

            for report in reports:
                with st.expander(
                    f"📅 {report['created_at']} — "
                    f"{report['predicted_disease']}"
                ):
                    st.write(
                        f"**Report ID:** {report['report_id']}"
                    )
                    st.write(
                        f"**Disease prediction:** "
                        f"{report['predicted_disease']}"
                    )
                    st.write(
                        f"**Confidence:** "
                        f"{report['confidence']}%"
                        if report["confidence"] is not None
                        else "**Confidence:** Not available"
                    )
                    st.write(
                        f"**Severity:** "
                        f"{report['severity'] or 'Not recorded'}"
                    )
                    st.write(
                        f"**Review status:** "
                        f"{report['review_status'] or 'Not available'}"
                    )
                    st.write(
                        f"**Doctor notes:** "
                        f"{report['doctor_notes'] or 'No notes added'}"
                    )
        else:
            st.info(
                "No disease reports have been saved for this animal yet."
            )

    except Exception as error:
        st.error("Could not load animal health history.")
        print("Animal health history error:", repr(error))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

            

# --- TRANSLATIONS ---
translations = {
    "English": {
        "title": "🐾 PashuVet",
        "subtitle": "Smart Animal Health Diagnostics",
        "how_to_use": "How to use PashuVet",
        "step1_title": "1. Upload Photo",
        "step1_desc": "Take a clear picture of the animal's affected area and upload it.",
        "step2_title": "2. AI Analysis",
        "step2_desc": "Our advanced AI instantly scans the image for potential diseases.",
        "step3_title": "3. Get Results",
        "step3_desc": "Receive a diagnosis, confidence score, and severity level.",
        "upload_label": "Drag and drop or click to upload an image",
        "analyzing": "🧠 AI is analyzing the image...",
        "confidence": "AI Confidence",
        "severity": "Severity Level",
        "severity_low": "Low",
        "severity_medium": "Medium",
        "severity_high": "High",
        "tip_healthy": "Animal looks healthy! Keep up the good care.",
        "tip_vet": "Please consult a veterinarian immediately for proper treatment.",
        "error": "Failed to process the image. Please try another one.",
        "model_not_found": "⚠️ **System Offline!** AI Model is missing. Please run `python train.py` first.",
        "diseases": {
            "healthy": "Healthy",
            "cowdramatophilisis": "Dermatophilosis",
            "cowpedicilo": "Pediculosis",
            "cowringworm": "Ringworm",
            "foot-and-mouth": "Foot-and-Mouth Disease",
            "lumpycows": "Lumpy Skin Disease",
            "mastitis": "Mastitis"
        }
    },
    "मराठी": {
        "title": "🐾 पशुVet",
        "subtitle": "स्मार्ट प्राणी आरोग्य निदान",
        "how_to_use": "पशुVet कसे वापरावे",
        "step1_title": "१. फोटो अपलोड करा",
        "step1_desc": "प्राण्याच्या प्रभावित भागाचा स्पष्ट फोटो घ्या आणि तो अपलोड करा.",
        "step2_title": "२. एआय (AI) विश्लेषण",
        "step2_desc": "आमचे प्रगत तंत्रज्ञान रोगांसाठी त्वरित प्रतिमेचे विश्लेषण करते.",
        "step3_title": "३. परिणाम मिळवा",
        "step3_desc": "निदान, विश्वास पातळी आणि रोगाची तीव्रता मिळवा.",
        "upload_label": "इमेज अपलोड करण्यासाठी येथे क्लिक करा",
        "analyzing": "🧠 एआय प्रतिमेचे विश्लेषण करत आहे...",
        "confidence": "विश्वास पातळी",
        "severity": "तीव्रता पातळी",
        "severity_low": "कमी",
        "severity_medium": "मध्यम",
        "severity_high": "जास्त",
        "tip_healthy": "प्राणी निरोगी दिसत आहे! चांगली काळजी घेत राहा.",
        "tip_vet": "योग्य उपचारांसाठी कृपया त्वरित पशुवैद्यकांचा सल्ला घ्या.",
        "error": "प्रतिमेवर प्रक्रिया करण्यात अयशस्वी. कृपया दुसरी प्रतिमा वापरून पहा.",
        "model_not_found": "⚠️ **मॉडेल सापडले नाही!** कृपया अनुप्रयोग वापरण्यापूर्वी मॉडेल तयार करण्यासाठी `python train.py` चालवा.",
        "diseases": {
            "healthy": "निरोगी",
            "cowdramatophilisis": "डर्मेटोफायलोसिस",
            "cowpedicilo": "उवा / गोचीड",
            "cowringworm": "नायटा",
            "foot-and-mouth": "लाळखुरकत",
            "lumpycows": "लम्पी त्वचा रोग",
            "mastitis": "स्तनदाह"
        }
    }
}

# --- SIDEBAR: LANGUAGE SELECTION ---
st.sidebar.markdown("""
<div style="padding: 20px 0; text-align: center;">
    <h2 style="color: #3b82f6; margin-bottom: 0;">🌐</h2>
    <h3 style="color: #475569; font-size: 1.1rem; font-weight: 600; margin-top: 5px;">Select Language</h3>
</div>
""", unsafe_allow_html=True)
lang = st.sidebar.selectbox("Language", ["English", "मराठी"], label_visibility="collapsed")
t = translations[lang]

st.sidebar.markdown("""
<div style="margin-top: 40px; padding: 15px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
    <div style="font-size: 1.5rem; margin-bottom: 10px;">🛡️</div>
    <div style="font-size: 0.9rem; color: #64748b; font-weight: 500;">
        Fast, accurate, and completely private AI diagnostics for your livestock.
    </div>
</div>
""", unsafe_allow_html=True)

# --- CUSTOM CSS (Ultra-Premium Animated Theme) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Animated Gradient Background */
    .stApp {
        background: linear-gradient(-45deg, #f0fdf4, #e0f2fe, #f8fafc, #eff6ff);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Outfit', sans-serif;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 24px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
        margin-bottom: 30px;
        transition: transform 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.06);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1px;
        font-size: 3.5rem;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        text-shadow: 0px 4px 15px rgba(59, 130, 246, 0.1);
    }
    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.3rem;
        font-weight: 400;
        margin-top: 5px;
        margin-bottom: 2rem;
    }
    
    /* Upload Box Styling with Hover Animations */
    .stFileUploader > div > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px dashed #94a3b8 !important;
        border-radius: 20px !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        padding: 40px !important;
        cursor: pointer;
    }
    .stFileUploader > div > div:hover {
        border-color: #3b82f6 !important;
        transform: scale(1.02);
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.15) !important;
        background: #ffffff !important;
    }
    
    /* Results Section Entrance Animation */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .result-box {
        animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        background: white;
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
        border: 1px solid #f1f5f9;
        position: relative;
        overflow: hidden;
    }
    .result-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 6px;
        background: linear-gradient(90deg, #3b82f6, #10b981);
    }

    .disease-name {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .confidence-text {
        font-size: 1rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 15px;
    }

    .progress-bar-container {
        width: 100%;
        background-color: #f1f5f9;
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        margin-bottom: 25px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }

    .progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Severity & Tip Boxes */
    .severity-box {
        padding: 15px;
        border-radius: 12px;
        font-weight: 800;
        text-align: center;
        color: white;
        margin-bottom: 15px;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .severity-low { background: linear-gradient(135deg, #10b981, #059669); }
    .severity-medium { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .severity-high { background: linear-gradient(135deg, #ef4444, #dc2626); }

    .tip-box {
        padding: 16px;
        border-radius: 12px;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    .tip-healthy { background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .tip-warning { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
    .tip-critical { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    
    /* Uploaded image */
    [data-testid="stImage"] {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        border: 4px solid white;
        animation: slideUp 0.5s ease-out forwards;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- APP UI ---
# --- APP UI ---

# --- APP UI ---
portal = st.sidebar.radio(
    "Select Portal",
    ["🐄 Farmer Portal", "🩺 Doctor Portal", "🔐 Admin Portal"],
    key="portal_navigation"
)

_, main_col, _ = st.columns([1, 8, 1])

with main_col:
    st.markdown(f"<h1>{t['title']}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='subtitle'>{t['subtitle']}</div>",
        unsafe_allow_html=True
    )
    st.divider()

    # ==========================================
    # FARMER PORTAL
    # ==========================================
    if portal == "🐄 Farmer Portal":
        farmer = st.session_state.get("logged_in_farmer")

        # Show login and registration only when logged out
        if farmer is None:
            st.subheader("🐄 Farmer Portal")

            login_tab, register_tab = st.tabs(
                ["Farmer Login", "Farmer Registration"]
            )

            with login_tab:
                farmer_login(lang)

            with register_tab:
                farmer_registration(lang)

            st.info("Please log in to access the Farmer Portal.")

        else:
            st.success(f"Welcome, {farmer['full_name']}!")

            if st.button("Logout", key="farmer_logout"):
                st.session_state.pop("logged_in_farmer", None)
                st.rerun()

            # Animal registration
            animal_registration(lang)
            show_animal_health_history(farmer["user_id"])


            # Instructions
            st.markdown(
                f"""
                <div class="glass-card">
                    <h3 style="text-align:center;color:#3b82f6;">
                        {t['how_to_use']}
                    </h3>
                    <p>📸 {t['step1_title']} — {t['step1_desc']}</p>
                    <p>🧠 {t['step2_title']} — {t['step2_desc']}</p>
                    <p>✨ {t['step3_title']} — {t['step3_desc']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Load existing EfficientNetB0 model
            @st.cache_resource
            def load_app_model():
                try:
                    model, classes = load_model_and_classes("models")
                    return model, classes
                except Exception as error:
                    print("Model loading error:", error)
                    return None, None

            model, class_names = load_app_model()

            if model is None:
                st.error(t["model_not_found"])
            else:
                st.markdown(
                    f"<div style='text-align:center;color:#3b82f6;"
                    f"font-weight:700;margin-bottom:10px;'>"
                    f"{t['upload_label']}</div>",
                    unsafe_allow_html=True
                )

                uploaded_file = st.file_uploader(
                    "Upload animal image",
                    type=["jpg", "jpeg", "png"],
                    label_visibility="collapsed",
                    key="farmer_animal_image"
                )

                if uploaded_file is not None:
                    img_col, res_col = st.columns([1, 1.2], gap="large")

                    with img_col:
                        image = Image.open(uploaded_file)
                        st.image(image, use_container_width=True)

                    with res_col:
                        predicted_class = None
                        confidence = 0.0
                        tmp_path = None

                        try:
                            with st.spinner(t["analyzing"]):
                                with tempfile.NamedTemporaryFile(
                                    delete=False,
                                    suffix=".jpg"
                                ) as tmp_file:
                                    image.convert("RGB").save(tmp_file.name)
                                    tmp_path = tmp_file.name

                                predicted_class, confidence = predict_image(
                                    tmp_path, model, class_names
                                )
                        except Exception as error:
                            print("Prediction error:", error)
                            st.error(t["error"])
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.remove(tmp_path)

                        if predicted_class:
                            eng_class = predicted_class.lower()

                            if "healthy" in eng_class:
                                severity = t["severity_low"]
                                severity_class = "severity-low"
                                tip_msg = t["tip_healthy"]
                                tip_class = "tip-healthy"
                                tip_icon = "🎉"

                            elif any(
                                name in eng_class
                                for name in [
                                    "ringworm",
                                    "dramatophilisis",
                                    "pedicilo"
                                ]
                            ):
                                severity = t["severity_medium"]
                                severity_class = "severity-medium"
                                tip_msg = t["tip_vet"]
                                tip_class = "tip-warning"
                                tip_icon = "⚠️"

                            else:
                                severity = t["severity_high"]
                                severity_class = "severity-high"
                                tip_msg = t["tip_vet"]
                                tip_class = "tip-critical"
                                tip_icon = "🚨"

                            display_name = t["diseases"].get(
                                eng_class,
                                predicted_class.replace("_", " ").title()
                            )

                            st.markdown(
                                f"""
                                <div class="result-box">
                                    <div class="disease-name">
                                        🩺 {display_name}
                                    </div>
                                    <div class="confidence-text">
                                        {t['confidence']}: {confidence:.2f}%
                                    </div>
                                    <div class="progress-bar-container">
                                        <div class="progress-bar-fill"
                                             style="width:{confidence}%;"></div>
                                    </div>
                                    <div class="severity-box {severity_class}">
                                        {t['severity']}: {severity}
                                    </div>
                                    <div class="tip-box {tip_class}">
                                        <div>{tip_icon}</div>
                                        <div>{tip_msg}</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Save disease report
                            # Note: owner filtering will be added separately.
                            
                            animals = get_registered_animals(
    farmer["user_id"]
)
                            
                            if animals:
                                animal_options = {
                                    (
                                        f"{animal[1] or animal[2]} - "
                                        f"{animal[2]} - Owner: {animal[4]}"
                                    ): animal[0]
                                    for animal in animals
                                }

                                selected_animal = st.selectbox(
                                    "Select your registered animal",
                                    options=list(animal_options.keys()),
                                    key="report_animal_select"
                                )

                                if st.button(
                                    "💾 Save Disease Report",
                                    key="save_disease_report_farmer"
                                ):
                                    os.makedirs("uploads", exist_ok=True)

                                    image_rgb = Image.open(
                                        uploaded_file
                                    ).convert("RGB")

                                    photo_filename = (
                                        f"animal_{__import__('uuid').uuid4().hex}.jpg"
                                    )
                                    photo_path = os.path.join(
                                        "uploads",
                                        photo_filename
                                    )
                                    image_rgb.save(
                                        photo_path,
                                        format="JPEG"
                                    )

                                    selected_animal_id = animal_options[
                                        selected_animal
                                    ]

                                    report_id = save_disease_report(
                                        animal_id=selected_animal_id,
                                        predicted_disease=display_name,
                                        confidence=confidence,
                                        severity=severity,
                                        image_path=photo_path
                                    )

                                    if report_id:
                                        st.session_state["latest_report_id"] = (
                                            report_id
                                        )
                                        st.session_state[
                                            "latest_report_animal_id"
                                        ] = selected_animal_id

                                        st.success(
                                            f"Disease report saved successfully! "
                                            f"Report ID: {report_id}"
                                        )
                                    else:
                                        st.error(
                                            "Could not save the report. "
                                            "Please check the database connection."
                                        )

                            else:
                                st.warning(
                                    "You have no registered animals. "
                                    "Please register an animal before saving "
                                    "a disease report."
                                )

                            

    # ==========================================
    # FARMER CONSULTATION SECTION
    # ==========================================
    if portal == "🐄 Farmer Portal":
        latest_report_id = st.session_state.get("latest_report_id")

        if st.session_state.get("logged_in_farmer") and latest_report_id:
            st.divider()
            st.subheader("🩺 Contact a Doctor")

            doctors = get_available_doctors()

            if doctors:
                doctor_options = {
                    f"{d[1]} ({d[2]})": d[0]
                    for d in doctors
                }

                selected_doctor = st.selectbox(
                    "Select a doctor",
                    options=list(doctor_options.keys()),
                    key=f"doctor_select_{latest_report_id}"
                )
                

                message = st.text_area(
                    "Describe the animal's problem",
                    key=f"consult_message_{latest_report_id}"
                )

                if st.button(
                    "Send Consultation Request",
                    key=f"send_request_{latest_report_id}"
                ):
                    farmer = st.session_state["logged_in_farmer"]

                    success = create_consultation_request(
                        report_id=latest_report_id,
                        farmer_id=farmer["user_id"],
                        doctor_id=doctor_options[selected_doctor],
                        message=message
                    )

                    if success:
                        st.success("Consultation request sent!")
                    else:
                        st.error(
                            "Could not send request. Please check the report, "
                            "farmer and doctor details."
                        )
            else:
                st.info("No doctors are registered yet.")
    # ==========================================
    # DOCTOR PORTAL
    # ==========================================
    elif portal == "🩺 Doctor Portal":
        doctor_portal(lang)
        doctor_dashboard()

    # ==========================================
    # ADMIN PORTAL
    # ==========================================
    elif portal == "🔐 Admin Portal":
        admin_portal()

        if st.session_state.get("logged_in_admin"):
            admin_dashboard()



   