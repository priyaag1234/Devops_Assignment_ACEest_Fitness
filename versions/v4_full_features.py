import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date

DB_NAME = "aceest_fitness.db"

class ACEestApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACEest Fitness & Performance")
        self.root.geometry("1300x850")
        self.root.configure(bg="#1a1a1a")

        self.conn = None
        self.cur = None

        self.current_client = None

        self.init_db()
        self.setup_data()
        self.setup_ui()
        self.refresh_client_list()

    def init_db(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                height REAL,
                weight REAL,
                program TEXT,
                calories INTEGER,
                target_weight REAL,
                target_adherence INTEGER
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                week TEXT,
                adherence INTEGER
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                date TEXT,
                workout_type TEXT,
                duration_min INTEGER,
                notes TEXT
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER,
                name TEXT,
                sets INTEGER,
                reps INTEGER,
                weight REAL
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                date TEXT,
                weight REAL,
                waist REAL,
                bodyfat REAL
            )
            """
        )

        self.conn.commit()

    def setup_data(self):
        self.programs = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
        }

    def setup_ui(self):
        header = tk.Label(
            self.root,
            text="ACEest Functional Fitness System",
            bg="#d4af37",
            fg="black",
            font=("Helvetica", 24, "bold"),
            height=2,
        )
        header.pack(fill="x")

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.LabelFrame(
            main,
            text=" Client Management ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10, pady=5)

        tk.Label(left, text="Select Client", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.client_list = ttk.Combobox(left, state="readonly")
        self.client_list.pack(pady=(0, 5))
        self.client_list.bind("<<ComboboxSelected>>", self.on_client_selected)

        tk.Label(left, text="Name", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.name = tk.StringVar()
        tk.Entry(left, textvariable=self.name, bg="#333", fg="white").pack()

        tk.Label(left, text="Age", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.age = tk.IntVar()
        tk.Entry(left, textvariable=self.age, bg="#333", fg="white").pack()

        tk.Label(left, text="Height (cm)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.height = tk.DoubleVar()
        tk.Entry(left, textvariable=self.height, bg="#333", fg="white").pack()

        tk.Label(left, text="Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.weight = tk.DoubleVar()
        tk.Entry(left, textvariable=self.weight, bg="#333", fg="white").pack()

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.program = tk.StringVar()
        ttk.Combobox(
            left,
            textvariable=self.program,
            values=list(self.programs.keys()),
            state="readonly",
        ).pack()

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=5)
        ttk.Button(left, text="Load Client", command=self.load_client).pack(pady=5)

        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.summary = tk.Text(right, bg="#111", fg="white", font=("Consolas", 11))
        self.summary.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_client_list(self):
        self.cur.execute("SELECT name FROM clients ORDER BY name")
        names = [row[0] for row in self.cur.fetchall()]
        self.client_list["values"] = names

    def on_client_selected(self, event=None):
        name = self.client_list.get()
        if not name:
            return
        self.name.set(name)
        self.load_client()

    def save_client(self):
        if not self.name.get():
            messagebox.showerror("Error", "Name is required")
            return
        if not self.program.get():
            messagebox.showerror("Error", "Program is required")
            return

        name = self.name.get().strip()
        age = self.age.get() if self.age.get() > 0 else None
        height = self.height.get() if self.height.get() > 0 else None
        weight = self.weight.get() if self.weight.get() > 0 else None

        factor = self.programs[self.program.get()]["factor"]
        calories = int(weight * factor) if weight else None

        self.cur.execute(
            """
            INSERT OR REPLACE INTO clients
            (name, age, height, weight, program, calories)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, age, height, weight, self.program.get(), calories),
        )
        self.conn.commit()
        self.refresh_client_list()
        messagebox.showinfo("Saved", "Client saved")

    def load_client(self):
        name = self.name.get().strip()
        if not name:
            return
        self.cur.execute("SELECT * FROM clients WHERE name=?", (name,))
        row = self.cur.fetchone()
        if not row:
            return
        _id, name, age, height, weight, program, calories, *_ = row
        self.summary.delete("1.0", "end")
        self.summary.insert("end", f"Name: {name}\nAge: {age}\nWeight: {weight}\nProgram: {program}\nCalories: {calories}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()
