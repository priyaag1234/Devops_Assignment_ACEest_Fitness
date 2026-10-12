"""
ACEest Fitness & Gym - Flask Web Application
BITS Pilani Introduction to DevOps Assignment 1

Modularized from the baseline functional fitness desktop versions into
a lightweight, zero-external-database Flask REST API and management service.
Includes Role-Based Authentication, AI Program Generation, CSV Export,
Membership Tracking, and Workout/Metrics Logging.
"""

import csv
import io
import os
import random
import sqlite3
from datetime import datetime, date
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "aceest_fitness.db")

# ------------------------------------------------------------------------------
# Baseline Domain Models & Program Specifications
# ------------------------------------------------------------------------------

FACILITY_METRICS = {
    "organization": "ACEest Functional Fitness & Gym",
    "capacity": 150,
    "unit_capacity": "Users",
    "area_sq_ft": 10000,
    "break_even_members": 250,
    "regional_nutrition_context": "Tamil Nadu Balanced Athletic Diet"
}

PROGRAMS = {
    "Fat Loss (FL)": {
        "id": 1,
        "name": "Fat Loss (FL)",
        "calorie_factor": 22,
        "desc": "3-day full-body fat loss",
        "focus": "Conditioning",
        "workout": (
            "Mon: 5x5 Back Squat + AMRAP\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: 10RFT Deadlifts/Box Jumps\n"
            "Fri: 30min Active Recovery"
        ),
        "diet": (
            "B: 3 Egg Whites + Oats Idli\n"
            "L: Grilled Chicken + Brown Rice\n"
            "D: Fish Curry + Millet Roti\n"
            "Target: ~2,000 kcal"
        ),
        "color": "#e74c3c"
    },
    "Fat Loss (FL) – 5 day": {
        "id": 2,
        "name": "Fat Loss (FL) – 5 day",
        "calorie_factor": 24,
        "desc": "5-day split, higher volume fat loss",
        "focus": "Conditioning",
        "workout": "5-day split: Push, Pull, Legs, Upper, Lower with HIIT finishers",
        "diet": "High-protein deficit plan with millet roti and lean fish",
        "color": "#e74c3c"
    },
    "Muscle Gain (MG)": {
        "id": 3,
        "name": "Muscle Gain (MG)",
        "calorie_factor": 35,
        "desc": "Push/Pull/Legs hypertrophy",
        "focus": "Hypertrophy",
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "B: 4 Eggs + PB Oats\n"
            "L: Chicken Biryani (250g Chicken)\n"
            "D: Mutton Curry + Jeera Rice\n"
            "Target: ~3,200 kcal"
        ),
        "color": "#2ecc71"
    },
    "Beginner (BG)": {
        "id": 4,
        "name": "Beginner (BG)",
        "calorie_factor": 26,
        "desc": "3-day simple beginner full-body",
        "focus": "Full Body",
        "workout": (
            "Circuit Training: Air Squats, Ring Rows, Push-ups.\n"
            "Focus: Technique Mastery & Form (90% Threshold)"
        ),
        "diet": (
            "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\n"
            "Protein: 120g/day"
        ),
        "color": "#3498db"
    }
}

# Exercise pools for AI Program Generator (from baseline ACEestFull.py)
EXERCISES_POOL = {
    "Strength": [
        "Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row"
    ],
    "Hypertrophy": [
        "Leg Press", "Incline Dumbbell Press", "Lat Pulldown", "Lateral Raise", "Bicep Curl", "Tricep Extension"
    ],
    "Conditioning": [
        "Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings"
    ],
    "Full Body": [
        "Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press"
    ]
}


# ------------------------------------------------------------------------------
# Built-in SQLite Database Initialization (Zero external server required)
# ------------------------------------------------------------------------------

def get_db_connection():
    """Create and return a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables adhering to baseline schema versions 1-6."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        # Role-based users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        """)
        # Insert default admin user if not exists
        cur.execute("""
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES ('admin', 'admin', 'Admin')
        """)

        # Clients table with full specifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                height REAL,
                weight REAL,
                program TEXT,
                calories INTEGER,
                target_weight REAL,
                target_adherence INTEGER,
                membership_status TEXT DEFAULT 'Active',
                membership_end TEXT,
                notes TEXT
            )
        """)

        # Adherence progress tracking
        cur.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                week TEXT,
                adherence INTEGER
            )
        """)

        # Workouts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                date TEXT,
                workout_type TEXT,
                duration_min INTEGER,
                notes TEXT
            )
        """)

        # Exercises per workout
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER,
                name TEXT,
                sets INTEGER,
                reps INTEGER,
                weight REAL
            )
        """)

        # Body metrics
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                date TEXT,
                weight REAL,
                waist REAL,
                bodyfat REAL
            )
        """)
        conn.commit()


# Initialize database
init_db()


# ------------------------------------------------------------------------------
# Core Endpoints & Documentation
# ------------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    """Welcome and API documentation endpoint."""
    return jsonify({
        "status": "online",
        "message": "Welcome to ACEest Fitness & Gym Management API",
        "version": "1.0.0",
        "institution": "BITS Pilani - DevOps Assignment 1",
        "facility_metrics": FACILITY_METRICS,
        "endpoints": {
            "GET /": "Service overview & documentation",
            "GET /health": "Health-check probe",
            "GET /api/facility": "Facility metrics (Capacity, Area, Break-even)",
            "POST /api/auth/login": "User login (admin/admin)",
            "POST /api/auth/register": "User registration",
            "GET /api/programs": "List all fitness & nutrition programs",
            "GET /api/programs/<key>": "Get details of a specific program",
            "POST /api/programs/generate": "AI Workout Routine Generator",
            "GET /api/clients": "List registered gym clients",
            "POST /api/clients": "Register or update client (auto-calculates calories)",
            "GET /api/clients/<name>": "Get client profile and summary",
            "GET /api/clients/<name>/membership": "Check membership status & expiry",
            "GET /api/clients/<name>/report": "Generate client text/JSON report",
            "POST /api/progress": "Log weekly client adherence",
            "GET /api/progress/<name>": "Get adherence history for client",
            "POST /api/workouts": "Log workout session with exercises",
            "GET /api/workouts/<name>": "Get workout history for client",
            "POST /api/metrics": "Log body metrics (weight, waist, bodyfat)",
            "GET /api/metrics/<name>": "Get metrics history for client",
            "GET /api/export/clients.csv": "Export client catalog to CSV",
            "POST /api/calculator/calories": "Calculate target calories based on program",
            "POST /api/calculator/bmi": "Calculate Body Mass Index (BMI)"
        }
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Application health check endpoint for monitoring & container probes."""
    return jsonify({
        "status": "healthy",
        "service": "ACEest Fitness & Gym API",
        "version": "1.0.0"
    }), 200


@app.route("/api/facility", methods=["GET"])
def facility():
    """Retrieve gym facility metrics from baseline specs."""
    return jsonify({
        "success": True,
        "data": FACILITY_METRICS
    }), 200


# ------------------------------------------------------------------------------
# Authentication Endpoints
# ------------------------------------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Verify user credentials (baseline default: admin / admin)."""
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    username = str(data["username"]).strip()
    password = str(data["password"]).strip()

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT role FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()

    if row:
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {"username": username, "role": row["role"]}
        }), 200

    return jsonify({"success": False, "error": "Invalid username or password"}), 401


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    """Register a new user account."""
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    username = str(data["username"]).strip()
    password = str(data["password"]).strip()
    role = str(data.get("role", "Coach")).strip()

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": f"Username '{username}' already exists"}), 400

    return jsonify({
        "success": True,
        "message": f"User '{username}' registered with role '{role}'"
    }), 201


# ------------------------------------------------------------------------------
# Programs Catalog & AI Routine Generator
# ------------------------------------------------------------------------------

@app.route("/api/programs", methods=["GET"])
def get_programs():
    """List all available fitness programs."""
    return jsonify({
        "success": True,
        "count": len(PROGRAMS),
        "data": list(PROGRAMS.values())
    }), 200


@app.route("/api/programs/<program_key>", methods=["GET"])
def get_program(program_key):
    """Retrieve details for a specific fitness program by key or ID."""
    if program_key in PROGRAMS:
        return jsonify({"success": True, "data": PROGRAMS[program_key]}), 200

    for prog in PROGRAMS.values():
        if str(prog["id"]) == program_key or prog["name"].lower() == program_key.lower():
            return jsonify({"success": True, "data": prog}), 200

    return jsonify({
        "success": False,
        "error": f"Program '{program_key}' not found"
    }), 404


@app.route("/api/programs/generate", methods=["POST"])
def generate_ai_program():
    """
    AI-Style Workout Routine Generator (from baseline ACEestFull.py).
    Generates customized weekly exercise schedule based on experience level and focus.
    """
    data = request.get_json(silent=True) or {}
    exp_level = str(data.get("experience_level", "intermediate")).strip().lower()
    focus = str(data.get("focus", "")).strip()

    if exp_level not in ["beginner", "intermediate", "advanced"]:
        return jsonify({
            "success": False,
            "error": "experience_level must be 'beginner', 'intermediate', or 'advanced'"
        }), 400

    if not focus or focus not in EXERCISES_POOL:
        focus = "Full Body"

    if exp_level == "beginner":
        sets_range = (2, 3)
        reps_range = (8, 12)
        days_count = 3
    elif exp_level == "intermediate":
        sets_range = (3, 4)
        reps_range = (8, 15)
        days_count = 4
    else:
        sets_range = (4, 5)
        reps_range = (6, 15)
        days_count = 5

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][:days_count]
    schedule = []

    for day in day_names:
        num_ex = 3 if days_count < 4 else 4
        chosen_exercises = random.sample(EXERCISES_POOL[focus], k=num_ex)
        day_routine = {
            "day": day,
            "exercises": [
                {
                    "name": ex,
                    "sets": random.randint(*sets_range),
                    "reps": random.randint(*reps_range)
                } for ex in chosen_exercises
            ]
        }
        schedule.append(day_routine)

    return jsonify({
        "success": True,
        "experience_level": exp_level,
        "focus": focus,
        "days_per_week": days_count,
        "schedule": schedule
    }), 200


# ------------------------------------------------------------------------------
# Client Management Endpoints
# ------------------------------------------------------------------------------

@app.route("/api/clients", methods=["GET"])
def get_clients():
    """List all registered clients."""
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        clients = [dict(row) for row in rows]
    return jsonify({
        "success": True,
        "count": len(clients),
        "data": clients
    }), 200


@app.route("/api/clients", methods=["POST"])
def save_client():
    """
    Save or update client data.
    Automatically calculates calories using the program's calorie_factor.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Valid JSON body required"}), 400

    name = str(data.get("name", "")).strip()
    program = str(data.get("program", "")).strip()

    if not name:
        return jsonify({"success": False, "error": "Client name is required"}), 400

    if not program or program not in PROGRAMS:
        return jsonify({
            "success": False,
            "error": f"Invalid program. Choose from: {list(PROGRAMS.keys())}"
        }), 400

    try:
        age = int(data["age"]) if "age" in data and data["age"] is not None else None
        height = float(data["height"]) if "height" in data and data["height"] is not None else None
        weight = float(data["weight"]) if "weight" in data and data["weight"] is not None else None
        target_weight = (
            float(data["target_weight"]) if "target_weight" in data and data["target_weight"] is not None else None
        )
        target_adherence = (
            int(data["target_adherence"]) if "target_adherence" in data and data["target_adherence"] is not None else None
        )
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Age, height, and weight values must be numeric"}), 400

    membership_status = str(data.get("membership_status", "Active"))
    membership_end = str(data.get("membership_end", "2026-12-31"))
    notes = str(data.get("notes", ""))

    # Baseline calorie formula: weight * factor
    factor = PROGRAMS[program]["calorie_factor"]
    calories = int(weight * factor) if weight and weight > 0 else None

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO clients
            (name, age, height, weight, program, calories, target_weight, target_adherence,
             membership_status, membership_end, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, age, height, weight, program, calories, target_weight, target_adherence,
              membership_status, membership_end, notes))
        conn.commit()

        row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
        client_record = dict(row)

    return jsonify({
        "success": True,
        "message": f"Client '{name}' saved successfully",
        "data": client_record
    }), 201


@app.route("/api/clients/<name>", methods=["GET"])
def get_client(name):
    """Retrieve full client profile, progress summary, and latest metrics."""
    with get_db_connection() as conn:
        client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
        if not client:
            return jsonify({"success": False, "error": f"Client '{name}' not found"}), 404

        client_data = dict(client)

        prog_row = conn.execute(
            "SELECT COUNT(*), AVG(adherence) FROM progress WHERE client_name=?", (name,)
        ).fetchone()
        weeks_logged = prog_row[0] if prog_row else 0
        avg_adherence = round(prog_row[1], 1) if prog_row and prog_row[1] is not None else 0

        metric_row = conn.execute(
            "SELECT * FROM metrics WHERE client_name=? ORDER BY date DESC LIMIT 1", (name,)
        ).fetchone()
        latest_metrics = dict(metric_row) if metric_row else None

    return jsonify({
        "success": True,
        "data": {
            "client": client_data,
            "weeks_logged": weeks_logged,
            "avg_adherence": avg_adherence,
            "latest_metrics": latest_metrics
        }
    }), 200


@app.route("/api/clients/<name>/membership", methods=["GET"])
def check_membership(name):
    """Check membership billing and expiration status."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT membership_status, membership_end FROM clients WHERE name=?", (name,)
        ).fetchone()
        if not row:
            return jsonify({"success": False, "error": f"Client '{name}' not found"}), 404

    return jsonify({
        "success": True,
        "client_name": name,
        "membership_status": row["membership_status"],
        "renewal_date": row["membership_end"]
    }), 200


@app.route("/api/clients/<name>/report", methods=["GET"])
def client_report(name):
    """Generate structured client report."""
    with get_db_connection() as conn:
        client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
        if not client:
            return jsonify({"success": False, "error": f"Client '{name}' not found"}), 404

        client_dict = dict(client)

    return jsonify({
        "success": True,
        "report_title": f"ACEest Client Report - {name}",
        "generated_at": datetime.now().isoformat(),
        "client": client_dict
    }), 200


# ------------------------------------------------------------------------------
# Progress, Workouts & Metrics
# ------------------------------------------------------------------------------

@app.route("/api/progress", methods=["POST"])
def save_progress():
    """Log weekly client adherence."""
    data = request.get_json(silent=True)
    if not data or "client_name" not in data or "adherence" not in data:
        return jsonify({"success": False, "error": "client_name and adherence are required"}), 400

    client_name = str(data["client_name"]).strip()
    try:
        adherence = int(data["adherence"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Adherence must be an integer (0-100)"}), 400

    if adherence < 0 or adherence > 100:
        return jsonify({"success": False, "error": "Adherence must be between 0 and 100"}), 400

    week = data.get("week") or datetime.now().strftime("Week %U - %Y")

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO progress (client_name, week, adherence)
            VALUES (?, ?, ?)
        """, (client_name, week, adherence))
        conn.commit()

    return jsonify({
        "success": True,
        "message": f"Weekly progress logged for '{client_name}'",
        "data": {"client_name": client_name, "week": week, "adherence": adherence}
    }), 201


@app.route("/api/progress/<name>", methods=["GET"])
def get_progress(name):
    """Retrieve adherence history for client."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM progress WHERE client_name=? ORDER BY id", (name,)
        ).fetchall()
        data = [dict(r) for r in rows]

    return jsonify({
        "success": True,
        "count": len(data),
        "data": data
    }), 200


@app.route("/api/workouts", methods=["POST"])
def log_workout():
    """Log a workout session and optional exercises."""
    data = request.get_json(silent=True)
    if not data or "client_name" not in data or "workout_type" not in data:
        return jsonify({"success": False, "error": "client_name and workout_type are required"}), 400

    client_name = str(data["client_name"]).strip()
    workout_type = str(data["workout_type"]).strip()
    workout_date = data.get("date") or date.today().isoformat()
    duration_min = int(data.get("duration_min", 60))
    notes = data.get("notes", "")

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (client_name, workout_date, workout_type, duration_min, notes))
        workout_id = cur.lastrowid

        exercises = data.get("exercises", [])
        for ex in exercises:
            if "name" in ex:
                cur.execute("""
                    INSERT INTO exercises (workout_id, name, sets, reps, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    workout_id,
                    ex.get("name"),
                    int(ex.get("sets", 3)),
                    int(ex.get("reps", 10)),
                    float(ex.get("weight", 0.0))
                ))
        conn.commit()

    return jsonify({
        "success": True,
        "message": "Workout session logged",
        "data": {"workout_id": workout_id, "client_name": client_name}
    }), 201


@app.route("/api/workouts/<name>", methods=["GET"])
def get_workouts(name):
    """Retrieve workout history for a client."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC, id DESC", (name,)
        ).fetchall()
        workouts = [dict(r) for r in rows]

    return jsonify({
        "success": True,
        "count": len(workouts),
        "data": workouts
    }), 200


@app.route("/api/metrics", methods=["POST"])
def log_metrics():
    """Log body metrics (weight, waist, bodyfat)."""
    data = request.get_json(silent=True)
    if not data or "client_name" not in data or "weight" not in data:
        return jsonify({"success": False, "error": "client_name and weight are required"}), 400

    client_name = str(data["client_name"]).strip()
    metric_date = data.get("date") or date.today().isoformat()
    weight = float(data["weight"])
    waist = float(data.get("waist", 0.0))
    bodyfat = float(data.get("bodyfat", 0.0))

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
            VALUES (?, ?, ?, ?, ?)
        """, (client_name, metric_date, weight, waist, bodyfat))
        conn.commit()

    return jsonify({
        "success": True,
        "message": "Body metrics logged",
        "data": {"client_name": client_name, "date": metric_date, "weight": weight}
    }), 201


@app.route("/api/metrics/<name>", methods=["GET"])
def get_metrics(name):
    """Retrieve body metrics history for a client."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM metrics WHERE client_name=? ORDER BY date DESC", (name,)
        ).fetchall()
        metrics = [dict(r) for r in rows]

    return jsonify({
        "success": True,
        "count": len(metrics),
        "data": metrics
    }), 200


# ------------------------------------------------------------------------------
# CSV Export Endpoint (Zero external dependencies)
# ------------------------------------------------------------------------------

@app.route("/api/export/clients.csv", methods=["GET"])
def export_clients_csv():
    """Export clients catalog as CSV (from baseline v6)."""
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Name", "Age", "Height", "Weight", "Program", "Calories",
        "Target Weight", "Target Adherence", "Membership Status", "Membership End", "Notes"
    ])

    for r in rows:
        writer.writerow([
            r["id"], r["name"], r["age"], r["height"], r["weight"],
            r["program"], r["calories"], r["target_weight"], r["target_adherence"],
            r["membership_status"], r["membership_end"], r["notes"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=aceest_clients.csv"}
    )


# ------------------------------------------------------------------------------
# Fitness & Health Calculators
# ------------------------------------------------------------------------------

@app.route("/api/calculator/calories", methods=["POST"])
def calculate_calories():
    """Calculate caloric target based on program factor or Mifflin-St Jeor equation."""
    data = request.get_json(silent=True)
    if not data or "weight_kg" not in data:
        return jsonify({"success": False, "error": "weight_kg is required"}), 400

    try:
        weight = float(data["weight_kg"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "weight_kg must be numeric"}), 400

    if weight <= 0:
        return jsonify({"success": False, "error": "weight_kg must be positive"}), 400

    if "program" in data and data["program"] in PROGRAMS:
        factor = PROGRAMS[data["program"]]["calorie_factor"]
        program_calories = int(weight * factor)
        return jsonify({
            "success": True,
            "method": "program_factor",
            "program": data["program"],
            "factor": factor,
            "target_calories": program_calories
        }), 200

    if "height_cm" in data and "age" in data and "gender" in data and "activity_level" in data:
        height = float(data["height_cm"])
        age = int(data["age"])
        gender = str(data["gender"]).strip().lower()
        activity = str(data["activity_level"]).strip().lower()

        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        if activity not in activity_multipliers:
            return jsonify({"success": False, "error": "Invalid activity level"}), 400

        bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if gender == "male" else -161)
        maintenance = round(bmr * activity_multipliers[activity], 2)
        return jsonify({
            "success": True,
            "method": "mifflin_st_jeor",
            "bmr": round(bmr, 2),
            "maintenance_calories": maintenance,
            "weight_loss_calories": round(maintenance - 500, 2),
            "weight_gain_calories": round(maintenance + 500, 2)
        }), 200

    return jsonify({
        "success": False,
        "error": "Provide either 'program' or ('height_cm', 'age', 'gender', 'activity_level')"
    }), 400


@app.route("/api/calculator/bmi", methods=["POST"])
def calculate_bmi():
    """Calculate Body Mass Index (BMI) and health category with baseline risk notes."""
    data = request.get_json(silent=True)
    if not data or "weight_kg" not in data or "height_cm" not in data:
        return jsonify({"success": False, "error": "weight_kg and height_cm are required"}), 400

    try:
        weight = float(data["weight_kg"])
        height_cm = float(data["height_cm"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "weight and height must be numeric"}), 400

    if weight <= 0 or height_cm <= 0:
        return jsonify({"success": False, "error": "weight and height must be positive numbers"}), 400

    height_m = height_cm / 100.0
    bmi = round(weight / (height_m ** 2), 2)

    if bmi < 18.5:
        category = "Underweight"
        risk = "Potential nutrient deficiency, low energy."
    elif bmi < 25.0:
        category = "Normal"
        risk = "Low risk if active and strong."
    elif bmi < 30.0:
        category = "Overweight"
        risk = "Moderate risk; focus on adherence and progressive activity."
    else:
        category = "Obese"
        risk = "Higher risk; prioritize fat loss, consistency, and supervision."

    return jsonify({
        "success": True,
        "bmi": bmi,
        "category": category,
        "risk_note": risk
    }), 200


# ------------------------------------------------------------------------------
# Error Handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    return jsonify({
        "success": False,
        "error": "The requested resource was not found on this server."
    }), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 internal server errors with JSON response."""
    return jsonify({
        "success": False,
        "error": "An internal server error occurred."
    }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
