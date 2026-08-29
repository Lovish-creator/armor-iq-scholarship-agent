import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

# Default location: alongside this file, inside the mock_portal package.
# Override with SCHOLARSHIP_DB_PATH for a custom location (e.g. in CI or prod).
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scholarship_portal.db")
DB_PATH = os.getenv("SCHOLARSHIP_DB_PATH", DEFAULT_DB_PATH)

_initialized = False

def get_db_connection():
    global _initialized
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _initialized:
        # Ensure schema exists before any caller tries to use the connection,
        # since callers may reach this via the in-process fallback path
        # (bypassing the FastAPI startup event that normally calls init_db()).
        _ensure_schema(conn)
        _initialized = True
    return conn

def _ensure_schema(conn):
    """Create all tables if they don't already exist. Safe to call repeatedly
    and safe to call on every new connection (idempotent)."""
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
    conn.commit()


def init_db():
    """Create schema (if needed) and (re)seed synthetic demo data."""
    conn = get_db_connection()  # already ensures schema via get_db_connection()
    cursor = conn.cursor()

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

    # Seed Synthetic & Live Verified Scholarships (Buddy4Study, NSP, AICTE, Reliance, Tata, Kotak, JSW, HDFC)
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
            "SCH-GOV-AICTE-PRAGATI",
            "AICTE Pragati Scholarship Scheme for Girl Students",
            "government",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu"]),
            json.dumps(["Engineering", "Computer Science", "Technology", "Information Technology", "Pharmacy", "Architecture"]),
            800000,
            6.0,
            50000,
            "2026-10-31",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf", "tuition_fee_receipt.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-GOV-AICTE-SAKSHAM",
            "AICTE Saksham Scholarship Scheme for Specially-Abled Students",
            "government",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka"]),
            json.dumps(["Engineering", "Computer Science", "Technology", "Pharmacy", "Diploma"]),
            800000,
            5.5,
            50000,
            "2026-10-31",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "disability_certificate.pdf", "admission_letter.pdf", "tuition_fee_receipt.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-GOV-NSP-CSSS",
            "Central Sector Scheme of Scholarship for College & University Students (PM-USP)",
            "government",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Tamil Nadu", "Uttar Pradesh"]),
            json.dumps(["Engineering", "Computer Science", "Technology", "Medicine", "General Degree", "Science"]),
            450000,
            7.5,
            20000,
            "2026-10-31",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "bonafide_certificate.pdf", "fee_receipt.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-PRV-RELIANCE-UG",
            "Reliance Foundation Undergraduate Scholarship 2026-27",
            "private",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Gujarat", "Karnataka"]),
            json.dumps(["Engineering", "Computer Science", "Information Technology", "Data Science", "Medicine", "General Degree"]),
            1500000,
            6.0,
            200000,
            "2026-10-05",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf", "aadhaar_card.pdf", "bank_passbook.pdf", "bonafide_certificate.pdf"])
        ),
        (
            "SCH-PRV-TATA-PANKH",
            "Tata Capital Pankh Scholarship Programme for Undergraduate Students",
            "private",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "West Bengal", "Tamil Nadu"]),
            json.dumps(["Engineering", "Technology", "Computer Science", "Medicine", "General Degree", "Diploma"]),
            400000,
            6.0,
            100000,
            "2026-09-30",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf", "tuition_fee_receipt.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-PRV-KOTAK-KANYA",
            "Kotak Kanya Scholarship for Professional Higher Education",
            "private",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Telangana"]),
            json.dumps(["Engineering", "Computer Science", "Medicine", "Architecture", "Design", "Integrated LLB"]),
            600000,
            7.5,
            150000,
            "2026-08-31",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf", "bonafide_certificate.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-PRV-JSW-UDAAN",
            "JSW Udaan Scholarship for Higher & Technical Education",
            "private",
            json.dumps(["All India", "Punjab", "Maharashtra", "Karnataka", "Tamil Nadu", "Rajasthan", "Goa", "Odisha"]),
            json.dumps(["Engineering", "Technology", "Computer Science", "Diploma", "Polytechnic"]),
            800000,
            6.0,
            50000,
            "2026-10-31",
            json.dumps(["marksheet_12th.pdf", "marksheet_10th.pdf", "income_certificate.pdf", "admission_letter.pdf", "fee_receipt.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-PRV-HDFC-ECSS",
            "HDFC Bank Parivartan's Educational Crisis Scholarship Support (ECSS)",
            "private",
            json.dumps(["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Uttar Pradesh"]),
            json.dumps(["Engineering", "Computer Science", "General Degree", "Medicine", "Diploma"]),
            250000,
            5.5,
            75000,
            "2026-10-31",
            json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf", "tuition_fee_receipt.pdf", "aadhaar_card.pdf", "bank_passbook.pdf"])
        ),
        (
            "SCH-DEL-TECH-04",
            "Delhi State Technical Higher Education Scheme",
            "government",
            json.dumps(["Delhi"]),
            json.dumps(["Engineering", "Polytechnic", "Technology"]),
            400000,
            7.0,
            95000,
            "2026-10-31",
            json.dumps(["domicile_delhi.pdf", "income_certificate.pdf", "marksheet_12th.pdf"])
        ),
        (
            "SCH-PRV-GLOBAL-03",
            "Apex Global Foundation Private Leadership Award",
            "private",
            json.dumps(["All India"]),
            json.dumps(["Engineering", "Technology", "Computer Science"]),
            1200000,
            8.5,
            250000,
            "2026-12-31",
            json.dumps(["essay.pdf", "recommendation.pdf"])
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
