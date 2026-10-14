import json
from datetime import datetime
from database import get_db
from ai_service import generate_plan_with_ai

SUBJECT_DEFAULT_TOPICS = {
    "Data Structures & Algorithms": ["Arrays & Two Pointers", "Binary Trees & BST", "Dynamic Programming", "Graph Traversals (BFS/DFS)", "Heaps & Priority Queues"],
    "DBMS": ["Relational Model & Keys", "Normalization (1NF to BCNF)", "SQL Joins & Group By", "ACID & Transactions", "Indexing with B+ Trees"],
    "Operating Systems": ["CPU Scheduling", "Process Synchronization & Semaphores", "Deadlock Avoidance & Bankers Algo", "Paging & Virtual Memory", "Page Replacement (LRU/FIFO)"],
    "Java": ["Object-Oriented Programming & Interfaces", "Collections Framework (HashMap/ArrayList)", "Exception Handling & Best Practices", "Multithreading & Concurrency", "Java 8 Streams & Lambdas"],
    "SQL": ["Basic SELECT & Filtering", "INNER, LEFT & FULL OUTER Joins", "Aggregate Functions & HAVING", "Subqueries & Common Table Expressions", "Window Functions (RANK/ROW_NUMBER)"],
    "Python": ["Core Data Structures (Lists, Dicts, Sets)", "OOP & Classes", "Decorators & Generators", "File I/O & Exception Handling", "Standard Libraries & Comprehensions"],
    "C/C++": ["Pointers & Memory Allocation", "Structures & Unions", "Templates & STL", "OOP & Inheritance in C++", "File Handling & Bitwise Ops"],
    "Computer Networks": ["OSI & TCP/IP Model Layers", "Subnetting & IP Addressing", "Routing Algorithms", "TCP vs UDP & Flow Control", "Application Protocols (HTTP, DNS)"],
    "Software Engineering": ["SDLC Models (Agile/Scrum)", "Design Patterns (Factory, Singleton)", "Software Testing Strategies", "UML Diagrams & System Architecture", "Git & Version Control"],
    "Machine Learning": ["Linear & Logistic Regression", "Decision Trees & Random Forests", "Model Evaluation & Cross-Validation", "Clustering (K-Means)", "Neural Network Fundamentals"],
    "Aptitude": ["Quantitative Aptitude (Percentages, Profit/Loss)", "Time, Speed & Distance", "Permutations & Combinations", "Data Interpretation", "Probability Basics"],
    "Reasoning": ["Logical Deductions & Syllogisms", "Coding-Decoding & Series", "Blood Relations & Direction Sense", "Puzzles & Seating Arrangements", "Critical Reasoning"]
}

def get_days_until_exam(exam_date_str):
    if not exam_date_str:
        return 90
    try:
        exam_date = datetime.strptime(exam_date_str[:10], '%Y-%m-%d')
        delta = (exam_date - datetime.now()).days
        return max(1, delta)
    except Exception:
        return 90

def build_deterministic_plan(user, preferences, subjects, challenges):
    hours_per_day = float(preferences.get('study_hours_per_day', 3.0) or 3.0)
    total_minutes = int(round(hours_per_day * 60))
    learning_min = int(round(total_minutes * 0.50))
    practice_min = int(round(total_minutes * 0.30))
    revision_min = total_minutes - learning_min - practice_min

    goal = (user.get('primary_goal') or '').lower()
    prep_stage = (user.get('preparation_stage') or '').lower()
    exam_date_str = user.get('exam_date')
    days_to_exam = get_days_until_exam(exam_date_str)
    is_rush = days_to_exam <= 30 or 'final 30' in prep_stage or 'revision' in prep_stage
    is_beginner = 'starting' in prep_stage

    priority_map = {'high': 3, 'medium': 2, 'low': 1}
    confidence_map = {'weak': 4, 'average': 3, 'good': 2, 'strong': 1}

    scored_subjects = []
    for s in subjects:
        s_name = s.get('subject_name', 'General')
        p_val = priority_map.get(str(s.get('priority', '')).lower(), 2)
        c_val = confidence_map.get(str(s.get('confidence_level', '')).lower(), 3)
        score = p_val + c_val
        scored_subjects.append({
            'subject_name': s_name,
            'confidence': s.get('confidence_level', 'Average'),
            'priority': s.get('priority', 'Medium'),
            'score': score,
            'difficult_topics': s.get('difficult_topics', '')
        })

    # Sort descending by score
    scored_subjects.sort(key=lambda x: x['score'], reverse=True)

    if not scored_subjects:
        scored_subjects = [{'subject_name': 'Data Structures & Algorithms', 'confidence': 'Weak', 'priority': 'High', 'score': 7, 'difficult_topics': ''}]

    # Top 3 to 5 subjects
    selected_subjects = scored_subjects[:min(max(3, len(scored_subjects)), 5)]

    # Parse weak topics from challenges
    weak_topics_raw = challenges.get('weak_topics', '')
    weak_topics_list = []
    if weak_topics_raw:
        if isinstance(weak_topics_raw, list):
            weak_topics_list = weak_topics_raw
        else:
            try:
                weak_topics_list = json.loads(weak_topics_raw)
            except Exception:
                weak_topics_list = [w.strip() for w in weak_topics_raw.split(',') if w.strip()]

    # Resource recommendation string
    res_pref = preferences.get('resource_preferences', '')
    if isinstance(res_pref, str) and res_pref.startswith('['):
        try:
            res_pref = ', '.join(json.loads(res_pref))
        except Exception:
            pass
    if not res_pref:
        res_pref = "Free YouTube playlists & curated practice problems"

    plan = []

    # Days 1 to 5
    for day in range(1, 6):
        subj_idx = (day - 1) % len(selected_subjects)
        curr_subj = selected_subjects[subj_idx]
        s_name = curr_subj['subject_name']

        # Determine topic
        topic = None
        if weak_topics_list and day <= len(weak_topics_list):
            topic = weak_topics_list[day - 1]
        elif curr_subj['difficult_topics']:
            diff_split = [d.strip() for d in curr_subj['difficult_topics'].split(',') if d.strip()]
            if diff_split:
                topic = diff_split[(day - 1) % len(diff_split)]

        if not topic:
            default_pool = SUBJECT_DEFAULT_TOPICS.get(s_name, [f"{s_name} Core Concepts", f"{s_name} Key Implementations", f"{s_name} Advanced Problem Solving"])
            topic = default_pool[(day - 1) % len(default_pool)]

        # Custom tasks based on goal & stage
        if is_rush:
            learn_task = f"High-yield formula & concept revision for {topic} ({learning_min} mins)"
            practice_task = f"Solve 10-15 Previous Year Exam Questions on {topic} ({practice_min} mins)"
            rev_task = f"Rapid formula sheet notes and mistake review ({revision_min} mins)"
            reason = f"Within 30-day exam window: maximizing marks via targeted high-frequency exam questions."
        elif is_beginner:
            learn_task = f"Deep fundamental concept study of {topic} via video/text ({learning_min} mins)"
            practice_task = f"Step-by-step beginner-to-intermediate problem drill ({practice_min} mins)"
            rev_task = f"Flashcard recall and self-summary writing ({revision_min} mins)"
            reason = f"Building unshakeable foundation in {s_name} prioritizing clarity before speed."
        elif 'placement' in goal:
            learn_task = f"Concept recap and pattern recognition in {topic} ({learning_min} mins)"
            practice_task = f"Solve LeetCode/Interview standard coding & logic questions ({practice_min} mins)"
            rev_task = f"Dry-run code on paper and review edge cases ({revision_min} mins)"
            reason = f"Directly mapped to top Indian tech placement interview screening rounds."
        elif 'gate' in goal:
            learn_task = f"Theoretical rigor, proofs & standard theorems for {topic} ({learning_min} mins)"
            practice_task = f"Solve 8-12 GATE standard numerical questions ({practice_min} mins)"
            rev_task = f"Short notes compilation & tricky counter-examples ({revision_min} mins)"
            reason = f"High-weightage GATE CSE topic tailored for precision and conceptual clarity."
        else:
            learn_task = f"Comprehensive chapter walkthrough for {topic} ({learning_min} mins)"
            practice_task = f"Guided practice exercise and problem set ({practice_min} mins)"
            rev_task = f"Active recall summary of key definitions and properties ({revision_min} mins)"
            reason = f"Balanced preparation to improve mastery from {curr_subj['confidence']} level."

        plan.append({
            "day_number": day,
            "focus_subject": s_name,
            "focus_topic": topic,
            "study_minutes": total_minutes,
            "learning_task": learn_task,
            "practice_task": practice_task,
            "revision_task": rev_task,
            "recommended_resource_type": res_pref,
            "reason": reason
        })

    # Day 6: Mixed Revision and Practice
    top_two = ", ".join([s['subject_name'] for s in selected_subjects[:2]])
    plan.append({
        "day_number": 6,
        "focus_subject": f"Mixed Revision ({top_two})",
        "focus_topic": "Cross-Topic Synthesis & Weak-Spot Consolidation",
        "study_minutes": total_minutes,
        "learning_task": f"Review cumulative mistakes log and formula sheets from Days 1–5 ({learning_min} mins)",
        "practice_task": f"Mixed timed quiz containing 15-20 problems across {top_two} ({practice_min} mins)",
        "revision_task": f"Detailed review of incorrect questions and misconceptions ({revision_min} mins)",
        "recommended_resource_type": "SkillPath Adaptive Quizzes & Saved Mistake Log",
        "reason": "Prevents compartmentalization by interleaving multiple core subjects under time pressure."
    })

    # Day 7: Weekly Mock Test or Full Revision
    test_type = "Full Exam Simulation Mock Test" if is_rush or preferences.get('weekly_mock_test_enabled', 1) else "Comprehensive Weekly Review"
    plan.append({
        "day_number": 7,
        "focus_subject": "All Focus Subjects",
        "focus_topic": f"{test_type} & Strategy Analysis",
        "study_minutes": total_minutes,
        "learning_task": f"Pre-test mental checklist and high-frequency formula scan ({learning_min} mins)",
        "practice_task": f"Take timed weekly adaptive mock test simulating actual exam environment ({practice_min} mins)",
        "revision_task": f"Post-test autopsy: log misconceptions into revision queue ({revision_min} mins)",
        "recommended_resource_type": "SkillPath Mock Exam Engine & Performance Dashboard",
        "reason": "Evaluates 7-day retention, measures speed, and calibrates difficulty for week 2."
    })

    return plan

def generate_personalized_plan(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise ValueError(f"User {user_id} not found")
    user = dict(user_row)

    cursor.execute("SELECT * FROM study_preferences WHERE user_id = ?", (user_id,))
    pref_row = cursor.fetchone()
    preferences = dict(pref_row) if pref_row else {}

    cursor.execute("SELECT * FROM user_subjects WHERE user_id = ?", (user_id,))
    subject_rows = cursor.fetchall()
    subjects = [dict(r) for r in subject_rows]

    cursor.execute("SELECT * FROM user_challenges WHERE user_id = ?", (user_id,))
    chal_row = cursor.fetchone()
    challenges = dict(chal_row) if chal_row else {}

    # Check for study time warning
    warning = None
    study_hours = float(preferences.get('study_hours_per_day', 3.0) or 3.0)
    if len(subjects) > 5 or (len(subjects) > 3 and study_hours < 2.5):
        warning = "Your selected subjects exceed your available time. SkillPath has prioritized the most important subjects."

    # Try AI generation first
    plan = None
    try:
        user_ai_data = {
            "id": user_id,
            "name": user.get('name'),
            "primary_goal": user.get('primary_goal'),
            "exam_date": user.get('exam_date'),
            "study_hours_per_day": study_hours,
            "subjects": subjects,
            "weak_topics": challenges.get('weak_topics', []),
            "preferences": preferences
        }
        plan = generate_plan_with_ai(user_ai_data)
    except Exception:
        plan = None

    if not plan or len(plan) != 7:
        plan = build_deterministic_plan(user, preferences, subjects, challenges)

    # Clear previous plan for this user
    cursor.execute("DELETE FROM study_plans WHERE user_id = ?", (user_id,))

    # Insert plan into study_plans table
    now_str = datetime.now().isoformat()
    for day_item in plan:
        cursor.execute('''
        INSERT INTO study_plans (
            user_id, day_number, focus_subject, focus_topic, study_minutes,
            learning_task, practice_task, revision_task, recommended_resource_type,
            reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            int(day_item.get('day_number', 1)),
            str(day_item.get('focus_subject', 'General')),
            str(day_item.get('focus_topic', 'Fundamentals')),
            int(day_item.get('study_minutes', int(study_hours * 60))),
            str(day_item.get('learning_task', '')),
            str(day_item.get('practice_task', '')),
            str(day_item.get('revision_task', '')),
            str(day_item.get('recommended_resource_type', 'Free resources')),
            str(day_item.get('reason', '')),
            now_str
        ))

    # Also make sure the topics table has entries for the user's subjects so mastery tracking works
    for s in subjects:
        s_name = s.get('subject_name')
        if not s_name:
            continue
        default_topics = SUBJECT_DEFAULT_TOPICS.get(s_name, [f"{s_name} Core Concepts"])
        for t_name in default_topics:
            cursor.execute("SELECT id FROM topics WHERE user_id = ? AND topic = ?", (user_id, t_name))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO topics (user_id, subject_name, topic, importance, mastery, status, created_at) VALUES (?, ?, ?, ?, ?, 'not_started', ?)",
                    (user_id, s_name, t_name, 4, 40 if s.get('confidence_level') == 'Weak' else 60, now_str)
                )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "plan": plan,
        "warning": warning
    }
