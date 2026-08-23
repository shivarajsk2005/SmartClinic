from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "smartclinic-secret-key"

login_manager = LoginManager(app)
login_manager.login_view = "login"

DB = os.path.join(app.root_path, "database.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if user:
        return User(user["id"], user["name"], user["email"], user["role"])
    return None


def add_column_if_missing(conn, table, column, definition):
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'patient'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available_time TEXT NOT NULL,
            hospital_name TEXT,
            city TEXT,
            user_id INTEGER,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Booked'
        )
    """)
    add_column_if_missing(conn, "doctors", "user_id", "INTEGER")
    add_column_if_missing(conn, "doctors", "is_active", "INTEGER NOT NULL DEFAULT 1")
    add_column_if_missing(conn, "doctors", "hospital_name", "TEXT")
    add_column_if_missing(conn, "doctors", "city", "TEXT")
    add_column_if_missing(conn, "appointments", "cancellation_reason", "TEXT")
    conn.commit()
    conn.close()


def seed_doctors():
    conn = get_db()
    doctors = [
        ("Dr. Anil Kumar", "General Physician", "09:00-13:00", "Govt Hospital Majestic", "Bengaluru", "anil@smartclinic.com", "anil123"),
        ("Dr. Priya Sharma", "Dermatologist", "14:00-18:00", "Victoria Hospital", "Bengaluru", "priya@smartclinic.com", "priya123"),
        ("Dr. Rahul Verma", "Cardiologist", "10:00-14:00", "Manipal Hospital", "Bengaluru", "rahul@smartclinic.com", "rahul123"),
        ("Dr. Sneha Rao", "Pediatrician", "15:00-19:00", "Sakra World Hospital", "Bengaluru", "sneha@smartclinic.com", "sneha123"),
        ("Dr. Arjun Mehta", "Orthopedic Surgeon", "09:00-13:00", "Apollo Hospitals", "Hyderabad", "arjun@smartclinic.com", "arjun123"),
        ("Dr. Kavya Nair", "Gynecologist", "10:00-14:00", "Aster CMI Hospital", "Bengaluru", "kavya@smartclinic.com", "kavya123"),
        ("Dr. Vikram Singh", "Neurologist", "14:00-18:00", "Fortis Hospital", "Mumbai", "vikram@smartclinic.com", "vikram123"),
        ("Dr. Meera Iyer", "ENT Specialist", "09:00-13:00", "Narayana Health City", "Bengaluru", "meera@smartclinic.com", "meera123"),
        ("Dr. Rohan Das", "Psychiatrist", "15:00-19:00", "Max Super Speciality Hospital", "Delhi", "rohan@smartclinic.com", "rohan123"),
        ("Dr. Aisha Khan", "Ophthalmologist", "11:00-15:00", "Kokilaben Hospital", "Mumbai", "aisha@smartclinic.com", "aisha123"),
        ("Dr. Neha Kapoor", "Internal Medicine", "13:00-17:00", "Govt Hospital Majestic", "Bengaluru", "neha@smartclinic.com", "neha123"),
        ("Dr. Suresh Bhat", "Orthopedic Specialist", "09:00-13:00", "Victoria Hospital", "Bengaluru", "suresh@smartclinic.com", "suresh123"),
        ("Dr. Pooja Reddy", "Endocrinologist", "14:00-18:00", "Manipal Hospital", "Bengaluru", "pooja@smartclinic.com", "pooja123"),
        ("Dr. Naveen Joshi", "Radiologist", "10:00-14:00", "Sakra World Hospital", "Bengaluru", "naveen@smartclinic.com", "naveen123"),
        ("Dr. Isha Patel", "General Surgeon", "13:00-17:00", "Apollo Hospitals", "Hyderabad", "isha@smartclinic.com", "isha123"),
        ("Dr. Aditya Menon", "Urologist", "09:00-13:00", "Aster CMI Hospital", "Bengaluru", "aditya@smartclinic.com", "aditya123"),
        ("Dr. Farhan Ali", "Pulmonologist", "10:00-14:00", "Fortis Hospital", "Mumbai", "farhan@smartclinic.com", "farhan123"),
        ("Dr. Lakshmi Rao", "Oncologist", "14:00-18:00", "Narayana Health City", "Bengaluru", "lakshmi@smartclinic.com", "lakshmi123"),
        ("Dr. Manish Gupta", "Nephrologist", "09:00-13:00", "Max Super Speciality Hospital", "Delhi", "manish@smartclinic.com", "manish123"),
        ("Dr. Zoya Sheikh", "Dentist", "15:00-19:00", "Kokilaben Hospital", "Mumbai", "zoya@smartclinic.com", "zoya123"),
    ]
    for name, spec, hours, hospital_name, city, email, password in doctors:
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            user_id = user["id"]
            conn.execute("UPDATE users SET name=?, role='doctor' WHERE id=?", (name, user_id))
        else:
            cur = conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), "doctor")
            )
            user_id = cur.lastrowid

        doc = conn.execute("SELECT id FROM doctors WHERE name=?", (name,)).fetchone()
        if doc:
            conn.execute(
                "UPDATE doctors SET specialization=?, available_time=?, user_id=? WHERE id=?",
                (spec, hours, user_id, doc["id"])
            )
            conn.execute(
                "UPDATE doctors SET hospital_name=?, city=? WHERE id=?",
                (hospital_name, city, doc["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO doctors
                   (name,specialization,available_time,hospital_name,city,user_id)
                   VALUES(?,?,?,?,?,?)""",
                (name, spec, hours, hospital_name, city, user_id)
            )
    conn.commit()
    conn.close()


def parse_slots(time_range):
    start_s, end_s = time_range.split("-")
    start = datetime.strptime(start_s, "%H:%M")
    end = datetime.strptime(end_s, "%H:%M")
    slots = []
    while start < end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=30)
    return slots


@app.context_processor
def inject_helpers():
    return {"today": date.today().isoformat()}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all fields.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return render_template("register.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), "patient")
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email is already registered.", "error")
            return render_template("register.html")
        conn.close()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and user["role"] != "patient":
            flash("This is the client login. Doctors should use the doctor login.", "error")
        elif user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["name"], user["email"], user["role"]))
            return redirect(url_for("dashboard"))
        elif not user or not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/doctor-login", methods=["GET", "POST"])
def doctor_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and user["role"] != "doctor":
            flash("This is the doctor login. Clients should use the client login.", "error")
        elif user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["name"], user["email"], user["role"]))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid doctor email or password.", "error")

    return render_template("doctor_login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "patient":
        return render_template("patient_dashboard.html")
    if current_user.role == "doctor":
        return redirect(url_for("doctor_dashboard"))
    return redirect(url_for("admin_dashboard"))


@app.route("/book-appointment", methods=["GET", "POST"])
@login_required
def book_appointment():
    if current_user.role != "patient":
        flash("Only patients can book appointments.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()

    active = conn.execute(
        "SELECT id FROM appointments WHERE patient_id=? AND status='Booked'",
        (current_user.id,)
    ).fetchone()
    if active:
        conn.close()
        flash("You already have a booked appointment. Edit or cancel it before booking another.", "error")
        return redirect(url_for("my_appointments"))

    hospitals = conn.execute("""
        SELECT hospital_name, city
        FROM doctors
        WHERE hospital_name IS NOT NULL
        GROUP BY hospital_name, city
        ORDER BY hospital_name
    """).fetchall()
    doctors = conn.execute("""
        SELECT id,name,specialization,available_time,is_active,hospital_name,city
        FROM doctors ORDER BY name
    """).fetchall()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id")
        hospital_name = request.form.get("hospital_name", "").strip()
        appt_date = request.form.get("appointment_date")
        appt_time = request.form.get("appointment_time")

        if not hospital_name or not doctor_id or not appt_date or not appt_time:
            conn.close()
            flash("Please select hospital, doctor, date and time.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        if appt_date < date.today().isoformat():
            conn.close()
            flash("Please choose today or a future date.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        doctor = conn.execute(
            "SELECT * FROM doctors WHERE id=? AND hospital_name=?", (doctor_id, hospital_name)
        ).fetchone()
        if not doctor:
            conn.close()
            flash("Doctor not found.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        if not doctor["is_active"]:
            conn.close()
            flash("This doctor is currently inactive and cannot accept appointments.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        valid_slots = parse_slots(doctor["available_time"])
        if appt_time not in valid_slots:
            conn.close()
            flash("Selected time is outside the doctor's availability.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        taken = conn.execute("""
            SELECT id FROM appointments
            WHERE doctor_id=? AND appointment_date=? AND appointment_time=? AND status='Booked'
        """, (doctor_id, appt_date, appt_time)).fetchone()

        if taken:
            conn.close()
            flash("That time slot is already booked.", "error")
            return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)

        conn.execute("""
            INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,status)
            VALUES(?,?,?,?, 'Booked')
        """, (current_user.id, doctor_id, appt_date, appt_time))
        conn.commit()
        conn.close()
        flash("Appointment booked successfully.", "success")
        return redirect(url_for("my_appointments"))

    conn.close()
    return render_template("book_appointment.html", doctors=doctors, hospitals=hospitals)


@app.route("/my-appointments")
@login_required
def my_appointments():
    if current_user.role != "patient":
        return redirect(url_for("dashboard"))
    conn = get_db()
    appointments = conn.execute("""
         SELECT a.id,a.appointment_date,a.appointment_time,a.status,a.cancellation_reason,
             d.name AS doctor_name,d.specialization,d.available_time,d.is_active
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.id
        WHERE a.patient_id=?
        ORDER BY a.appointment_date,a.appointment_time
    """, (current_user.id,)).fetchall()
    conn.close()
    return render_template("my_appointments.html", appointments=appointments)


@app.route("/edit-appointment/<int:appointment_id>", methods=["GET", "POST"])
@login_required
def edit_appointment(appointment_id):
    if current_user.role != "patient":
        return redirect(url_for("dashboard"))

    conn = get_db()
    appointment = conn.execute("""
        SELECT * FROM appointments
        WHERE id=? AND patient_id=? AND status='Booked'
    """, (appointment_id, current_user.id)).fetchone()

    if not appointment:
        conn.close()
        flash("Appointment not found or it is no longer editable.", "error")
        return redirect(url_for("my_appointments"))

    doctors = conn.execute(
        "SELECT id,name,specialization,available_time,is_active FROM doctors ORDER BY name"
    ).fetchall()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id")
        appt_date = request.form.get("appointment_date")
        appt_time = request.form.get("appointment_time")

        doctor = conn.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()

        if not doctor or not doctor["is_active"] or appt_time not in parse_slots(doctor["available_time"]):
            conn.close()
            flash("Invalid or inactive doctor, or unavailable time.", "error")
            return render_template("edit_appointment.html", appointment=appointment, doctors=doctors)

        taken = conn.execute("""
            SELECT id FROM appointments
            WHERE doctor_id=? AND appointment_date=? AND appointment_time=?
              AND status='Booked' AND id!=?
        """, (doctor_id, appt_date, appt_time, appointment_id)).fetchone()

        if taken:
            conn.close()
            flash("That time slot is already booked.", "error")
            return render_template("edit_appointment.html", appointment=appointment, doctors=doctors)

        conn.execute("""
            UPDATE appointments
            SET doctor_id=?,appointment_date=?,appointment_time=?
            WHERE id=? AND patient_id=?
        """, (doctor_id, appt_date, appt_time, appointment_id, current_user.id))
        conn.commit()
        conn.close()
        flash("Appointment updated successfully.", "success")
        return redirect(url_for("my_appointments"))

    conn.close()
    return render_template("edit_appointment.html", appointment=appointment, doctors=doctors)


@app.route("/cancel-appointment/<int:appointment_id>", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    if current_user.role != "patient":
        return redirect(url_for("dashboard"))
    conn = get_db()
    conn.execute("""
        UPDATE appointments SET status='Cancelled'
        WHERE id=? AND patient_id=? AND status='Booked'
    """, (appointment_id, current_user.id))
    conn.commit()
    conn.close()
    flash("Appointment cancelled.", "success")
    return redirect(url_for("my_appointments"))


@app.route("/doctor-dashboard")
@login_required
def doctor_dashboard():
    if current_user.role != "doctor":
        return redirect(url_for("dashboard"))

    conn = get_db()
    doctor = conn.execute(
        "SELECT * FROM doctors WHERE user_id=?", (current_user.id,)
    ).fetchone()

    if not doctor:
        conn.close()
        flash("Doctor profile not found.", "error")
        return redirect(url_for("logout"))

    appointments = conn.execute("""
        SELECT a.id,a.appointment_date,a.appointment_time,a.status,
               u.name AS patient_name,u.email AS patient_email
        FROM appointments a
        JOIN users u ON a.patient_id=u.id
        WHERE a.doctor_id=?
        ORDER BY a.appointment_date,a.appointment_time
    """, (doctor["id"],)).fetchall()
    conn.close()
    return render_template("doctor_dashboard.html", doctor=doctor, appointments=appointments)


@app.route("/doctor-status", methods=["POST"])
@login_required
def doctor_status():
    if current_user.role != "doctor":
        return redirect(url_for("dashboard"))

    is_active = request.form.get("is_active") == "1"
    conn = get_db()
    doctor = conn.execute(
        "SELECT id FROM doctors WHERE user_id=?", (current_user.id,)
    ).fetchone()
    if not doctor:
        conn.close()
        flash("Doctor profile not found.", "error")
        return redirect(url_for("doctor_dashboard"))

    if not is_active:
        booked = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM appointments
            WHERE doctor_id=? AND status='Booked' AND appointment_date=?
            """,
            (doctor["id"], date.today().isoformat()),
        ).fetchone()
        if booked["count"]:
            conn.close()
            flash(
                "You have an appointment today. Complete or cancel today's appointment before becoming inactive.",
                "error",
            )
            return redirect(url_for("doctor_dashboard"))

    conn.execute(
        "UPDATE doctors SET is_active=? WHERE user_id=?",
        (int(is_active), current_user.id)
    )
    conn.commit()
    conn.close()
    flash("Doctor status updated.", "success")
    return redirect(url_for("doctor_dashboard"))


@app.route("/doctor-appointment/<int:appointment_id>/<action>", methods=["POST"])
@login_required
def doctor_appointment_action(appointment_id, action):
    if current_user.role != "doctor":
        return redirect(url_for("dashboard"))

    allowed = {"Completed", "Cancelled"}
    if action not in allowed:
        flash("Invalid action.", "error")
        return redirect(url_for("doctor_dashboard"))

    conn = get_db()
    doctor = conn.execute("SELECT id FROM doctors WHERE user_id=?", (current_user.id,)).fetchone()
    if doctor:
        conn.execute("""
            UPDATE appointments SET status=?
            WHERE id=? AND doctor_id=? AND status='Booked'
        """, (action, appointment_id, doctor["id"]))
        conn.commit()
    conn.close()
    flash(f"Appointment marked as {action}.", "success")
    return redirect(url_for("doctor_dashboard"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (current_user.id,)).fetchone()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("password", "").strip()

        if not name or not email:
            conn.close()
            flash("Name and email are required.", "error")
            return render_template("profile.html", user=user)

        duplicate = conn.execute(
            "SELECT id FROM users WHERE email=? AND id!=?", (email, current_user.id)
        ).fetchone()
        if duplicate:
            conn.close()
            flash("That email is already in use.", "error")
            return render_template("profile.html", user=user)

        if new_password:
            if len(new_password) < 6:
                conn.close()
                flash("New password must contain at least 6 characters.", "error")
                return render_template("profile.html", user=user)
            conn.execute(
                "UPDATE users SET name=?,email=?,password=? WHERE id=?",
                (name, email, generate_password_hash(new_password), current_user.id)
            )
        else:
            conn.execute(
                "UPDATE users SET name=?,email=? WHERE id=?",
                (name, email, current_user.id)
            )

        conn.commit()
        conn.close()
        flash("Account details updated. Please login again if you changed your email/password.", "success")
        logout_user()
        return redirect(url_for("login"))

    conn.close()
    return render_template("profile.html", user=user)


@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))
    conn = get_db()
    users = conn.execute("SELECT id,name,email,role FROM users ORDER BY id DESC").fetchall()
    appointments = conn.execute("""
        SELECT a.id,a.appointment_date,a.appointment_time,a.status,
               u.name AS patient,d.name AS doctor
        FROM appointments a
        JOIN users u ON a.patient_id=u.id
        JOIN doctors d ON a.doctor_id=d.id
        ORDER BY a.appointment_date,a.appointment_time
    """).fetchall()
    conn.close()
    return render_template("admin_dashboard.html", users=users, appointments=appointments)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    seed_doctors()
    app.run(debug=True)
