import os
import json
from datetime import datetime, timedelta
from database import init_db, get_db
from study_planner import generate_personalized_plan

def seed():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now()
    now_str = now.isoformat()
    exam_date_str = (now + timedelta(days=90)).strftime('%Y-%m-%d')
    tomorrow_str = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_str = (now - timedelta(days=1)).isoformat()

    # Clear existing demo student if exists
    cursor.execute("SELECT id FROM users WHERE name = ?", ("Demo Student",))
    existing_user = cursor.fetchone()
    if existing_user:
        user_id = existing_user['id']
        cursor.execute("DELETE FROM user_subjects WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM study_preferences WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_challenges WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM topics WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM study_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM attempts WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM revision_queue WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM questions WHERE user_id = ?", (user_id,))
    else:
        cursor.execute('''
        INSERT INTO users (
            name, education_level, branch, year, college_name,
            primary_goal, exam_name, exam_date, preparation_stage,
            target_role, gate_attempt_year, semester, government_exam_category,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "Demo Student",
            "B.Tech",
            "CSE",
            "3",
            "National Institute of Technology",
            "GATE CSE + Campus Placement",
            "GATE CSE 2027 & Tech Placements",
            exam_date_str,
            "Completed basics",
            "Software Developer",
            "2027",
            "6th Semester",
            None,
            now_str,
            now_str
        ))
        user_id = cursor.lastrowid

    # 1. Seed Study Preferences (3 daily hours)
    cursor.execute('''
    INSERT INTO study_preferences (
        user_id, study_days_per_week, study_hours_per_day, preferred_time,
        learning_styles, language_preference, resource_preferences,
        daily_revision_enabled, weekly_mock_test_enabled, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        6,
        3.0,
        "Evening",
        json.dumps(["Coding practice", "Reading notes"]),
        "English",
        json.dumps(["Free practice platforms", "Free YouTube playlists"]),
        1,
        1,
        now_str
    ))

    # 2. Seed Subjects: DSA (Weak, High), DBMS (Average, High), Operating Systems (Average, Medium), Java (Good, Medium)
    subjects_to_seed = [
        ("Data Structures & Algorithms", "Weak", "High", "Arrays, Linked Lists", "Dynamic Programming, Graphs"),
        ("DBMS", "Average", "High", "Basic SQL, Relational Algebra", "Normalization, Concurrency Control"),
        ("Operating Systems", "Average", "Medium", "Process States, CPU Scheduling", "Process Synchronization, Semaphores"),
        ("Java", "Good", "Medium", "OOP, Classes, Interfaces", "Multithreading, Streams")
    ]
    for s_name, conf, prio, comp, diff in subjects_to_seed:
        cursor.execute('''
        INSERT INTO user_subjects (
            user_id, subject_name, confidence_level, priority,
            completed_topics, difficult_topics, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, s_name, conf, prio, comp, diff, now_str))

    # 3. Seed Challenges & 2 Weak Topics
    cursor.execute('''
    INSERT INTO user_challenges (
        user_id, challenges, weak_topics, avoid_topics, upcoming_events, created_at
    ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        json.dumps(["Unable to solve coding problems", "Forgetting concepts"]),
        json.dumps(["Dynamic Programming", "Process Synchronization"]),
        json.dumps(["Compiler Design"]),
        "Internal college mid-terms in 3 weeks",
        now_str
    ))

    # 4. Seed Topics with initial mastery
    topics_seed = [
        ("Data Structures & Algorithms", "Dynamic Programming", 5, 35, "needs_work"),
        ("Data Structures & Algorithms", "Binary Trees & BST", 4, 65, "in_progress"),
        ("DBMS", "Normalization (1NF to BCNF)", 5, 50, "in_progress"),
        ("DBMS", "Relational Model & Keys", 4, 75, "in_progress"),
        ("Operating Systems", "Process Synchronization", 5, 40, "needs_work"),
        ("Operating Systems", "Paging & Virtual Memory", 4, 60, "in_progress"),
        ("Java", "OOP Concepts & Polymorphism", 4, 85, "mastered"),
        ("SQL", "SQL Joins & Aggregations", 4, 70, "in_progress")
    ]
    for subj, top, imp, mast, stat in topics_seed:
        cursor.execute('''
        INSERT INTO topics (user_id, subject_name, topic, importance, mastery, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, subj, top, imp, mast, stat, now_str))

    # 5. Load fallback questions from JSON and seed questions
    fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fallback_questions.json')
    with open(fallback_path, 'r', encoding='utf-8') as f:
        fb_questions = json.load(f)

    seeded_question_ids = []
    for q in fb_questions:
        cursor.execute('''
        INSERT INTO questions (
            user_id, subject_name, topic, concept, question, options,
            correct_index, difficulty, explanation, misconception, source, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            q['subject_name'],
            q['topic'],
            q['concept'],
            q['question'],
            json.dumps(q['options']),
            q['correct_index'],
            q['difficulty'],
            q['explanation'],
            q['misconception'],
            'fallback',
            now_str
        ))
        seeded_question_ids.append(cursor.lastrowid)

    # 6. Seed 2 Revision Items
    # Revision item 1: Process Synchronization
    cursor.execute('''
    INSERT INTO revision_queue (user_id, question_id, concept, due_date, interval_days, completed, created_at)
    VALUES (?, ?, ?, ?, 1, 0, ?)
    ''', (
        user_id,
        seeded_question_ids[14] if len(seeded_question_ids) > 14 else 1,
        "Semaphores vs Mutexes in Process Synchronization",
        tomorrow_str,
        now_str
    ))

    # Revision item 2: Dynamic Programming
    cursor.execute('''
    INSERT INTO revision_queue (user_id, question_id, concept, due_date, interval_days, completed, created_at)
    VALUES (?, ?, ?, ?, 1, 0, ?)
    ''', (
        user_id,
        seeded_question_ids[3] if len(seeded_question_ids) > 3 else 2,
        "0/1 Knapsack Optimal Substructure & DP Table",
        tomorrow_str,
        now_str
    ))

    # 7. Seed sample attempts for streak calculation (yesterday and today)
    # Yesterday's attempt
    if seeded_question_ids:
        cursor.execute('''
        INSERT INTO attempts (user_id, question_id, selected_index, is_correct, created_at)
        VALUES (?, ?, ?, 1, ?)
        ''', (user_id, seeded_question_ids[0], 1, yesterday_str))
        
        # Today's attempt
        cursor.execute('''
        INSERT INTO attempts (user_id, question_id, selected_index, is_correct, created_at)
        VALUES (?, ?, ?, 1, ?)
        ''', (user_id, seeded_question_ids[1], 2, now_str))

    conn.commit()
    conn.close()

    # 8. Generate initial 7-day personalized study plan
    generate_personalized_plan(user_id)
    print(f"Seed data created successfully! Demo User ID: {user_id}")

if __name__ == '__main__':
    seed()
