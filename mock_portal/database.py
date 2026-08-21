import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_PATH = "D:\\armor-iq-scholarship-agent\\scholarship_portal.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            education TEXT NOT NULL,
            state TEXT NOT NULL,
            annual_income INTEGER NOT NULL,
            category TEXT NOT NULL,
            cgpa REAL NOT NULL,
            documents_json TEXT NOT NULL
        )
    """)

    # Scholarships table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            scholarship_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scholarship_type TEXT NOT NULL, -- 'government' or 'private'
            eligible_states_json TEXT NOT NULL,
            eligible_fields_json TEXT NOT NULL,
            income_limit INTEGER NOT NULL,
            min_cgpa REAL NOT NULL,
            amount INTEGER NOT NULL,
            deadline TEXT NOT NULL,
            required_documents_json TEXT NOT NULL
        )
    """)

    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            scholarship_id TEXT NOT NULL,
            status TEXT NOT NULL, -- 'DRAFT', 'ELIGIBILITY_CHECKED', 'PREPARED', 'SUBMITTED', 'BLOCKED'
            intent_token TEXT,
            applied_at TEXT,
            rejection_reason TEXT
        )
    """)

    # Tool Execution & ArmorIQ Audit Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            tool TEXT NOT NULL,
            target_scholarship_id TEXT,
            intent_token TEXT,
            armoriq_decision TEXT NOT NULL, -- 'ALLOW', 'BLOCK', 'HOLD'
            executed INTEGER NOT NULL, -- 1 for executed, 0 for blocked/aborted
            detail TEXT
        )
    """)

    # Seed Synthetic Student
    cursor.execute("DELETE FROM students")
    cursor.execute("""
        INSERT INTO students (student_id, name, education, state, annual_income, category, cgpa, documents_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "student-demo-001",
        "Demo Student (Gurpreet Singh)",
        "B.Tech Computer Science",
        "Punjab",
        450000,
        "General",
        8.5,
        json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "domicile_punjab.pdf", "bonafide_certificate.pdf"])
    ))

    # Seed Synthetic Scholarships
    cursor.execute("DELETE FROM scholarships")
    scholarships = [
        (
            "SCH-GOV-PB-01",
            "Punjab Post-Matric Engineering State Scholarship",
            "government",
            json.dumps(["Punjab"]),
            json.dumps(["Engineering", "Computer Science", "IT"]),
            800000,
            6.5,
            75000,
            "2026-11-30",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "domicile_punjab.pdf"])
        ),
        (
            "SCH-GOV-MH-02",
            "Maharashtra Merit Higher Technical Grant",
            "government",
            json.dumps(["Maharashtra"]),
            json.dumps(["Engineering", "Technology"]),
            600000,
            7.0,
            60000,
            "2026-10-15",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "domicile_maharashtra.pdf"])
        ),
        (
            "SCH-PRV-GLOBAL-03",
            "Global Tech Foundation Excellence Award",
            "private",
            json.dumps(["All India"]),
            json.dumps(["Engineering", "Computer Science", "Data Science"]),
            1200000,
            8.0,
            120000,
            "2026-12-31",
            json.dumps(["marksheet_12th.pdf", "bonafide_certificate.pdf"])
        ),
        (
            "SCH-GOV-MED-04",
            "Punjab Medical & Healthcare Fellowship",
            "government",
            json.dumps(["Punjab"]),
            json.dumps(["Medicine", "Pharmacy", "Nursing"]),
            500000,
            7.5,
            90000,
            "2026-09-30",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "domicile_punjab.pdf"])
        )
    ]

    cursor.executemany("""
        INSERT INTO scholarships 
        (scholarship_id, name, scholarship_type, eligible_states_json, eligible_fields_json, income_limit, min_cgpa, amount, deadline, required_documents_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, scholarships)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized with synthetic data.")
