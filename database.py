import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skillpath.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        education_level TEXT,
        branch TEXT,
        year TEXT,
        college_name TEXT,
        primary_goal TEXT,
        exam_name TEXT,
        exam_date TEXT,
        preparation_stage TEXT,
        target_role TEXT,
        gate_attempt_year TEXT,
        semester TEXT,
        government_exam_category TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject_name TEXT,
        confidence_level TEXT,
        priority TEXT,
        completed_topics TEXT,
        difficult_topics TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        study_days_per_week INTEGER,
        study_hours_per_day REAL,
        preferred_time TEXT,
        learning_styles TEXT,
        language_preference TEXT,
        resource_preferences TEXT,
        daily_revision_enabled INTEGER DEFAULT 1,
        weekly_mock_test_enabled INTEGER DEFAULT 1,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        challenges TEXT,
        weak_topics TEXT,
        avoid_topics TEXT,
        upcoming_events TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject_name TEXT,
        topic TEXT,
        importance INTEGER DEFAULT 5,
        mastery INTEGER DEFAULT 0,
        status TEXT DEFAULT 'not_started',
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        day_number INTEGER,
        focus_subject TEXT,
        focus_topic TEXT,
        study_minutes INTEGER,
        learning_task TEXT,
        practice_task TEXT,
        revision_task TEXT,
        recommended_resource_type TEXT,
        reason TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject_name TEXT,
        topic TEXT,
        concept TEXT,
        question TEXT,
        options TEXT,
        correct_index INTEGER,
        difficulty TEXT,
        explanation TEXT,
        misconception TEXT,
        source TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        selected_index INTEGER,
        is_correct INTEGER,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS revision_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        concept TEXT,
        due_date TEXT,
        interval_days INTEGER,
        completed INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    ''')

    # AI Cache table for caching successful AI prompts and responses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT UNIQUE,
        prompt_type TEXT,
        response_json TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)
