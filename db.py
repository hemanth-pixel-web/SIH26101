import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "skillintel.db"))

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'LEARNER',
        department TEXT DEFAULT 'Official Statistics',
        designation TEXT DEFAULT 'Statistical Officer',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        description TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS user_skills (
        user_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        score REAL NOT NULL DEFAULT 0,
        target REAL NOT NULL DEFAULT 80,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, skill_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        provider TEXT NOT NULL,
        skill TEXT NOT NULL,
        level TEXT NOT NULL,
        duration TEXT NOT NULL,
        description TEXT NOT NULL,
        url TEXT DEFAULT '',
        source TEXT DEFAULT 'SKILLINTEL'
    );

    CREATE TABLE IF NOT EXISTS progress (
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        percent INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, course_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        score REAL NOT NULL,
        total INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS assessment_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        answer INTEGER NOT NULL,
        correct INTEGER NOT NULL,
        FOREIGN KEY(assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        material_id INTEGER,
        title TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        answer TEXT NOT NULL,
        explanation TEXT DEFAULT '',
        skill TEXT DEFAULT 'General',
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quiz_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected TEXT NOT NULL,
        correct INTEGER NOT NULL,
        FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
        FOREIGN KEY(question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
    );
    """)

    skills = [
        ("Data Collection & Survey Design", "Statistical Operations", "Designing sound data collection and survey instruments."),
        ("Statistical Analysis", "Statistical Methods", "Applying descriptive and inferential statistical methods."),
        ("Data Visualization", "Data Communication", "Communicating statistical insights through charts and dashboards."),
        ("Data Quality", "Statistical Operations", "Validation, consistency checks and quality assurance."),
        ("Python for Statistics", "Digital Skills", "Using Python for data processing and statistical workflows."),
        ("SQL & Data Management", "Digital Skills", "Querying, joining and managing structured datasets."),
        ("Official Statistics", "Domain Knowledge", "Understanding the production and dissemination of official statistics."),
        ("AI & Responsible Use", "Emerging Skills", "Using AI responsibly for productivity and learning.")
    ]
    for name, category, desc in skills:
        cur.execute("INSERT OR IGNORE INTO skills(name, category, description) VALUES(?,?,?)",
                    (name, category, desc))

    courses = [
        ("Foundations of Official Statistics", "iGOT Karmayogi", "Official Statistics", "Beginner", "4h 20m",
         "Core concepts, statistical standards, dissemination and official statistical systems.",
         "https://igotkarmayogi.gov.in/", "iGOT"),
        ("Survey Design & Sampling Essentials", "iGOT Karmayogi", "Data Collection & Survey Design", "Intermediate", "5h 10m",
         "Sampling frames, questionnaires, non-response and survey quality.",
         "https://igotkarmayogi.gov.in/", "iGOT"),
        ("Practical Statistical Analysis", "SKILLINTEL Academy", "Statistical Analysis", "Intermediate", "6h 40m",
         "Descriptive statistics, correlation, regression and interpretation.",
         "#", "SKILLINTEL"),
        ("Data Visualization for Decision Makers", "SKILLINTEL Academy", "Data Visualization", "Beginner", "3h 45m",
         "Build clear charts and communicate evidence effectively.",
         "#", "SKILLINTEL"),
        ("Statistical Data Quality Management", "iGOT Karmayogi", "Data Quality", "Intermediate", "4h 55m",
         "Quality dimensions, validation rules, revisions and metadata.",
         "https://igotkarmayogi.gov.in/", "iGOT"),
        ("Python for Statistical Officers", "SKILLINTEL Academy", "Python for Statistics", "Intermediate", "7h 30m",
         "Python fundamentals, pandas and practical statistical workflows.",
         "#", "SKILLINTEL"),
        ("SQL for Official Data Systems", "SKILLINTEL Academy", "SQL & Data Management", "Intermediate", "5h 25m",
         "Queries, joins, aggregation, data validation and reporting.",
         "#", "SKILLINTEL"),
        ("Responsible AI in Government", "iGOT Karmayogi", "AI & Responsible Use", "Beginner", "2h 50m",
         "Responsible, transparent and secure use of AI in public-sector work.",
         "https://igotkarmayogi.gov.in/", "iGOT")
    ]
    for c in courses:
        cur.execute("""INSERT OR IGNORE INTO courses
        (title,provider,skill,level,duration,description,url,source)
        VALUES(?,?,?,?,?,?,?,?)""", c)

    cur.execute("SELECT id FROM users WHERE email=?", ("demo@skillintel.gov.in",))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users(name,email,password_hash,role,department,designation)
                       VALUES(?,?,?,?,?,?)""",
                    ("Demo Learner", "demo@skillintel.gov.in",
                     generate_password_hash("Demo@123"), "LEARNER",
                     "National Statistical Office", "Statistical Officer"))

    cur.execute("SELECT id FROM users WHERE email=?", ("demo@skillintel.gov.in",))
    demo_id = cur.fetchone()["id"]
    skill_rows = cur.execute("SELECT id,name FROM skills ORDER BY id").fetchall()
    demo_scores = {
        "Data Collection & Survey Design": 72,
        "Statistical Analysis": 58,
        "Data Visualization": 76,
        "Data Quality": 64,
        "Python for Statistics": 45,
        "SQL & Data Management": 52,
        "Official Statistics": 82,
        "AI & Responsible Use": 68
    }
    for s in skill_rows:
        cur.execute("""INSERT OR IGNORE INTO user_skills(user_id,skill_id,score,target)
                       VALUES(?,?,?,80)""", (demo_id, s["id"], demo_scores.get(s["name"], 50)))

    conn.commit()
    conn.close()
