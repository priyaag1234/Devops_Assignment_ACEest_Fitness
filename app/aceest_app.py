"""
ACEest Fitness & Gym Management System — Flask REST API
Version: 3.2.4 (Assignment 2 — DevOps CI/CD Pipeline)

This is the production-ready Flask application built on the work from
Assignment 1. It exposes all features as a REST API with SQLite persistence,
role-based auth, BMI/calorie calculators, workout logging, and AI program gen.
"""

import os
import csv
import io
import random
import sqlite3
from datetime import datetime, date
from functools import wraps
from flask import Flask, jsonify, request, g, Response

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["TESTING"] = False

DB_PATH = os.environ.get("DB_PATH", "aceest_fitness.db")

APP_VERSION = "3.2.4"

# ── Program definitions ───────────────────────────────────────────────────────
PROGRAMS = {
    "Fat Loss (FL) - 3 day": {
        "factor": 22,
        "desc": "3-day full-body fat-loss circuit",
        "days": 3,
        "focus": "Conditioning",
    },
    "Fat Loss (FL) - 5 day": {
        "factor": 24,
        "desc": "5-day split, higher volume fat loss",
        "days": 5,
        "focus": "Conditioning",
    },
    "Muscle Gain (MG) - PPL": {
        "factor": 35,
        "desc": "Push/Pull/Legs hypertrophy",
        "days": 6,
        "focus": "Hypertrophy",
    },
    "Beginner (BG)": {
        "factor": 26,
        "desc": "3-day simple beginner full-body",
        "days": 3,
        "focus": "Full Body",
    },
}

EXERCISE_POOL = {
    "Conditioning": ["Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings"],
    "Hypertrophy":  ["Leg Press", "Incline DB Press", "Lat Pulldown", "Lateral Raise", "Bicep Curl", "Tricep Ext"],
    "Strength":     ["Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row"],
    "Full Body":    ["Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press"],
}

FACILITY = {
    "name":       "ACEest Functional Fitness",
    "capacity":   150,
    "area_sqft":  10000,
    "break_even": 250,
    "location":   "Tamil Nadu, India",
}


# ── Database helpers ──────────────────────────────────────────────────────────

def get_db(db_path: str = None) -> sqlite3.Connection:
    """Return a per-request (or given) DB connection."""
    if db_path:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path: str = None) -> None:
    """Create all tables and seed default admin user."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'Member'
        );

        CREATE TABLE IF NOT EXISTS clients (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT UNIQUE NOT NULL,
            age              INTEGER,
            height           REAL,
            weight           REAL,
            program          TEXT,
            calories         INTEGER,
            target_weight    REAL,
            target_adherence INTEGER,
            membership_expiry TEXT,
            created_at       TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS progress (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week        TEXT NOT NULL,
            adherence   INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workouts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name  TEXT NOT NULL,
            date         TEXT NOT NULL,
            workout_type TEXT,
            duration_min INTEGER,
            notes        TEXT
        );

        CREATE TABLE IF NOT EXISTS exercises (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            name       TEXT,
            sets       INTEGER,
            reps       INTEGER,
            weight     REAL
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date        TEXT NOT NULL,
            weight      REAL,
            waist       REAL,
            bodyfat     REAL
        );
    """)
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
        ("admin", "admin", "Admin"),
    )
    conn.commit()
    conn.close()


# ── Business logic (pure, testable) ──────────────────────────────────────────

def calculate_calories(weight_kg: float, program: str) -> int:
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    if program not in PROGRAMS:
        raise ValueError(f"Unknown program: {program}")
    return int(weight_kg * PROGRAMS[program]["factor"])


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive")
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m ** 2), 1)


def classify_bmi(bmi: float) -> dict:
    if bmi < 18.5:
        return {"category": "Underweight", "risk": "Potential nutrient deficiency, low energy."}
    elif bmi < 25.0:
        return {"category": "Normal", "risk": "Low risk if active and strong."}
    elif bmi < 30.0:
        return {"category": "Overweight", "risk": "Moderate risk; focus on adherence and progressive activity."}
    return {"category": "Obese", "risk": "Higher risk; prioritize fat loss, consistency, and supervision."}


def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, gender: str) -> int:
    """Mifflin-St Jeor BMR formula."""
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return int(bmr)


def generate_ai_program(program_name: str, experience: str) -> list[dict]:
    """Generate a randomised weekly workout plan."""
    focus = PROGRAMS.get(program_name, {}).get("focus", "Full Body")
    pool = EXERCISE_POOL.get(focus, EXERCISE_POOL["Full Body"])
    exp_map = {
        "beginner":     {"days": 3, "sets": (2, 3), "reps": (8, 12)},
        "intermediate": {"days": 4, "sets": (3, 4), "reps": (8, 15)},
        "advanced":     {"days": 5, "sets": (4, 5), "reps": (6, 15)},
    }
    cfg = exp_map.get(experience.lower(), exp_map["beginner"])
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][: cfg["days"]]
    plan = []
    for day in days:
        exercises = random.sample(pool, k=min(3, len(pool)))
        for ex in exercises:
            plan.append({
                "day":      day,
                "exercise": ex,
                "sets":     random.randint(*cfg["sets"]),
                "reps":     random.randint(*cfg["reps"]),
            })
    return plan


def authenticate_user(username: str, password: str, db_path: str = None) -> str | None:
    """Return role if credentials valid, else None."""
    conn = sqlite3.connect(db_path or DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_app_version() -> str:
    return APP_VERSION


# ── Auth decorator ────────────────────────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json(silent=True) or {}
        username = data.get("username") or request.args.get("username", "")
        password = data.get("password") or request.args.get("password", "")
        role = authenticate_user(username, password)
        if not role:
            return jsonify({"error": "Unauthorized"}), 401
        g.current_user = username
        g.current_role = role
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════════════════════
#  API Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return jsonify({
        "app":     "ACEest Fitness & Performance",
        "version": APP_VERSION,
        "status":  "running",
    })


@app.route("/health")
def health():
    """Health check endpoint used by Docker & Kubernetes probes."""
    return jsonify({"status": "healthy", "version": APP_VERSION}), 200


@app.route("/api/facility")
def facility():
    return jsonify(FACILITY)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    role = authenticate_user(username, password)
    if not role:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": "Login successful", "username": username, "role": role})


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "Member").strip()
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password, role) VALUES (?,?,?)",
            (username, password, role),
        )
        db.commit()
        return jsonify({"message": f"User '{username}' registered", "role": role}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409


# ── Programs ──────────────────────────────────────────────────────────────────

@app.route("/api/programs")
def list_programs():
    return jsonify(list(PROGRAMS.keys()))


@app.route("/api/programs/<path:key>")
def get_program(key):
    prog = PROGRAMS.get(key)
    if not prog:
        return jsonify({"error": "Program not found"}), 404
    return jsonify({"name": key, **prog})


@app.route("/api/programs/generate", methods=["POST"])
def generate_program():
    data = request.get_json(silent=True) or {}
    program    = data.get("program", "Beginner (BG)")
    experience = data.get("experience", "beginner")
    if program not in PROGRAMS:
        return jsonify({"error": "Unknown program"}), 400
    if experience.lower() not in ("beginner", "intermediate", "advanced"):
        return jsonify({"error": "experience must be beginner/intermediate/advanced"}), 400
    plan = generate_ai_program(program, experience)
    return jsonify({"program": program, "experience": experience, "plan": plan})


# ── Clients ───────────────────────────────────────────────────────────────────

@app.route("/api/clients", methods=["GET"])
def list_clients():
    db = get_db()
    rows = db.execute("SELECT name FROM clients ORDER BY name").fetchall()
    return jsonify([r["name"] for r in rows])


@app.route("/api/clients", methods=["POST"])
def create_client():
    data   = request.get_json(silent=True) or {}
    name   = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    program  = data.get("program", "")
    weight   = float(data.get("weight", 0) or 0)
    calories = calculate_calories(weight, program) if weight > 0 and program in PROGRAMS else None

    db = get_db()
    try:
        db.execute("""
            INSERT OR REPLACE INTO clients
              (name, age, height, weight, program, calories,
               target_weight, target_adherence, membership_expiry)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            name,
            data.get("age"),
            data.get("height"),
            weight or None,
            program or None,
            calories,
            data.get("target_weight"),
            data.get("target_adherence"),
            data.get("membership_expiry"),
        ))
        db.commit()
        return jsonify({"message": f"Client '{name}' saved", "calories": calories}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/clients/<name>", methods=["GET"])
def get_client(name):
    db  = get_db()
    row = db.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/api/clients/<name>/membership", methods=["GET"])
def get_membership(name):
    db  = get_db()
    row = db.execute(
        "SELECT name, membership_expiry FROM clients WHERE name=?", (name,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    expiry = row["membership_expiry"]
    status = "Active"
    if expiry:
        try:
            if date.fromisoformat(expiry) < date.today():
                status = "Expired"
        except ValueError:
            status = "Unknown"
    return jsonify({"client": name, "membership_expiry": expiry, "status": status})


@app.route("/api/clients/<name>/report", methods=["GET"])
def client_report(name):
    db  = get_db()
    client = db.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        return jsonify({"error": "Client not found"}), 404
    prog_rows = db.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    avg = round(sum(r["adherence"] for r in prog_rows) / len(prog_rows), 1) if prog_rows else 0
    return jsonify({
        "client":          dict(client),
        "weeks_logged":    len(prog_rows),
        "avg_adherence":   avg,
    })


# ── Export ────────────────────────────────────────────────────────────────────

@app.route("/api/export/clients.csv", methods=["GET"])
def export_clients_csv():
    db   = get_db()
    rows = db.execute("SELECT * FROM clients ORDER BY name").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "age", "height", "weight",
                     "program", "calories", "target_weight",
                     "target_adherence", "membership_expiry"])
    for row in rows:
        writer.writerow(list(row))
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"},
    )


# ── Progress ──────────────────────────────────────────────────────────────────

@app.route("/api/progress", methods=["POST"])
def log_progress():
    data = request.get_json(silent=True) or {}
    client_name = data.get("client_name", "").strip()
    adherence   = data.get("adherence")
    if not client_name or adherence is None:
        return jsonify({"error": "client_name and adherence required"}), 400
    week = datetime.now().strftime("Week %U - %Y")
    db = get_db()
    db.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)",
        (client_name, week, int(adherence)),
    )
    db.commit()
    return jsonify({"message": "Progress logged", "week": week, "adherence": adherence}), 201


@app.route("/api/progress/<name>", methods=["GET"])
def get_progress(name):
    db   = get_db()
    rows = db.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    data = [dict(r) for r in rows]
    avg  = round(sum(r["adherence"] for r in data) / len(data), 1) if data else 0
    return jsonify({"client": name, "records": data, "avg_adherence": avg})


# ── Workouts ──────────────────────────────────────────────────────────────────

@app.route("/api/workouts", methods=["POST"])
def log_workout():
    data = request.get_json(silent=True) or {}
    client_name  = data.get("client_name", "").strip()
    workout_date = data.get("date", date.today().isoformat())
    workout_type = data.get("workout_type", "")
    if not client_name or not workout_type:
        return jsonify({"error": "client_name and workout_type required"}), 400
    db = get_db()
    db.execute("""
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?,?,?,?,?)
    """, (client_name, workout_date, workout_type,
          data.get("duration_min", 60), data.get("notes", "")))
    db.commit()
    return jsonify({"message": "Workout logged"}), 201


# ── Metrics ───────────────────────────────────────────────────────────────────

@app.route("/api/metrics", methods=["POST"])
def log_metrics():
    data = request.get_json(silent=True) or {}
    client_name = data.get("client_name", "").strip()
    metric_date = data.get("date", date.today().isoformat())
    if not client_name:
        return jsonify({"error": "client_name required"}), 400
    db = get_db()
    db.execute("""
        INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
        VALUES (?,?,?,?,?)
    """, (client_name, metric_date,
          data.get("weight"), data.get("waist"), data.get("bodyfat")))
    db.commit()
    return jsonify({"message": "Metrics logged"}), 201


# ── Calculators ───────────────────────────────────────────────────────────────

@app.route("/api/calculator/calories", methods=["POST"])
def calc_calories():
    data = request.get_json(silent=True) or {}
    try:
        weight  = float(data.get("weight", 0))
        program = data.get("program", "")
        cals = calculate_calories(weight, program)
        return jsonify({"weight": weight, "program": program, "calories": cals})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/calculator/bmi", methods=["POST"])
def calc_bmi():
    data = request.get_json(silent=True) or {}
    try:
        weight = float(data.get("weight", 0))
        height = float(data.get("height", 0))
        bmi    = calculate_bmi(weight, height)
        info   = classify_bmi(bmi)
        return jsonify({"weight": weight, "height": height, "bmi": bmi, **info})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
