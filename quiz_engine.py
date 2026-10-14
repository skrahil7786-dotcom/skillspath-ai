import os
import json
from datetime import datetime, timedelta
from database import get_db
from ai_service import generate_quiz_with_ai, generate_next_action_with_ai

FALLBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fallback_questions.json')

SUBJECT_ALIAS_MAP = {
    "dsa": "Data Structures & Algorithms",
    "data structures": "Data Structures & Algorithms",
    "data structures & algorithms": "Data Structures & Algorithms",
    "data structures and algorithms": "Data Structures & Algorithms",
    "dbms": "DBMS",
    "database": "DBMS",
    "database management systems": "DBMS",
    "os": "Operating Systems",
    "operating systems": "Operating Systems",
    "operating system": "Operating Systems",
    "sql": "SQL",
    "java": "Java"
}

def load_fallback_questions():
    try:
        with open(FALLBACK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def normalize_subject_name(name):
    if not name:
        return "Data Structures & Algorithms"
    clean = name.strip().lower()
    return SUBJECT_ALIAS_MAP.get(clean, name.strip())

def get_or_create_quiz(user_id, subject_name, difficulty="medium"):
    normalized_subj = normalize_subject_name(subject_name)
    generated_questions = None

    # Try AI generation first
    try:
        ai_questions = generate_quiz_with_ai(normalized_subj, difficulty, count=5)
        if ai_questions and isinstance(ai_questions, list) and len(ai_questions) == 5:
            generated_questions = []
            for q in ai_questions:
                generated_questions.append({
                    "subject_name": normalized_subj,
                    "topic": q.get("topic", f"{normalized_subj} Core"),
                    "concept": q.get("concept", f"{normalized_subj} Concept"),
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "correct_index": int(q.get("correct_index", 0)),
                    "difficulty": q.get("difficulty", difficulty),
                    "explanation": q.get("explanation", "Correct according to standard syllabus."),
                    "misconception": q.get("misconception", "Common mistake occurs from incorrect assumptions."),
                    "source": "gemini"
                })
    except Exception:
        generated_questions = None

    # Fallback to local questions
    if not generated_questions:
        all_fallbacks = load_fallback_questions()
        conn = get_db()
        cursor = conn.cursor()
        
        # Check which questions user already attempted or has saved
        cursor.execute("SELECT question FROM questions WHERE user_id = ?", (user_id,))
        used_questions = set(row['question'] for row in cursor.fetchall())
        conn.close()

        # Filter by subject
        subject_pool = [q for q in all_fallbacks if q.get('subject_name', '').lower() == normalized_subj.lower()]
        if not subject_pool:
            # Fallback to general pool if subject has no dedicated fallback
            subject_pool = all_fallbacks

        # Select unused first
        unused = [q for q in subject_pool if q.get('question') not in used_questions]
        
        # Prefer matching difficulty if possible
        diff_matched = [q for q in unused if q.get('difficulty') == difficulty]
        selection = diff_matched[:5]
        if len(selection) < 5:
            for q in unused:
                if q not in selection:
                    selection.append(q)
                if len(selection) == 5:
                    break

        if len(selection) < 5:
            # If not enough unused, pull from full pool
            for q in subject_pool:
                if q not in selection:
                    selection.append(q)
                if len(selection) == 5:
                    break

        if len(selection) < 5:
            for q in all_fallbacks:
                if q not in selection:
                    selection.append(q)
                if len(selection) == 5:
                    break

        generated_questions = []
        for q in selection:
            generated_questions.append({
                "subject_name": normalized_subj,
                "topic": q.get("topic", f"{normalized_subj} Topic"),
                "concept": q.get("concept", f"{normalized_subj} Concept"),
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "correct_index": int(q.get("correct_index", 0)),
                "difficulty": q.get("difficulty", difficulty),
                "explanation": q.get("explanation", "Standard explanation."),
                "misconception": q.get("misconception", "Common misconception."),
                "source": "fallback"
            })

    # Save to database
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    client_questions = []

    for q in generated_questions:
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
            q.get('source', 'fallback'),
            now_str
        ))
        q_id = cursor.lastrowid
        # Client receives questions WITHOUT correct answers or explanations
        client_questions.append({
            "id": q_id,
            "subject_name": q['subject_name'],
            "topic": q['topic'],
            "concept": q['concept'],
            "question": q['question'],
            "options": q['options'],
            "difficulty": q['difficulty']
        })

    conn.commit()
    conn.close()

    return client_questions

def submit_quiz_answers(user_id, answers):
    """
    answers is expected to be a list of dicts: [{"question_id": 1, "selected_index": 2}, ...]
    """
    if not answers:
        return {
            "success": False,
            "error": "No answers provided"
        }

    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    total = len(answers)
    correct_count = 0
    results = []
    primary_subject = "General"
    primary_topic = "Core Fundamentals"
    weak_concept = None
    updated_mastery = []

    for ans in answers:
        q_id = ans.get('question_id')
        sel_idx = ans.get('selected_index')

        cursor.execute("SELECT * FROM questions WHERE id = ?", (q_id,))
        q_row = cursor.fetchone()
        if not q_row:
            continue

        q_dict = dict(q_row)
        primary_subject = q_dict.get('subject_name', primary_subject)
        primary_topic = q_dict.get('topic', primary_topic)

        correct_idx = q_dict.get('correct_index')
        is_correct = 1 if sel_idx is not None and int(sel_idx) == int(correct_idx) else 0
        if is_correct:
            correct_count += 1
        else:
            if not weak_concept:
                weak_concept = q_dict.get('concept')

        # Record attempt
        cursor.execute('''
        INSERT INTO attempts (user_id, question_id, selected_index, is_correct, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, q_id, sel_idx, is_correct, now_str))

        # Update topic mastery
        topic_name = q_dict.get('topic')
        subj_name = q_dict.get('subject_name')
        cursor.execute("SELECT * FROM topics WHERE user_id = ? AND topic = ?", (user_id, topic_name))
        t_row = cursor.fetchone()

        if t_row:
            old_mastery = t_row['mastery']
            delta = 10 if is_correct else -5
            new_mastery = max(0, min(100, old_mastery + delta))
            new_status = 'mastered' if new_mastery >= 80 else ('in_progress' if new_mastery >= 40 else 'needs_work')
            cursor.execute('''
            UPDATE topics SET mastery = ?, status = ? WHERE id = ?
            ''', (new_mastery, new_status, t_row['id']))
            updated_mastery.append({
                "topic": topic_name,
                "subject_name": subj_name,
                "mastery": new_mastery,
                "change": delta
            })
        else:
            init_mastery = 60 if is_correct else 35
            cursor.execute('''
            INSERT INTO topics (user_id, subject_name, topic, importance, mastery, status, created_at)
            VALUES (?, ?, ?, 4, ?, ?, ?)
            ''', (user_id, subj_name, topic_name, init_mastery, 'in_progress', now_str))
            updated_mastery.append({
                "topic": topic_name,
                "subject_name": subj_name,
                "mastery": init_mastery,
                "change": 10 if is_correct else -5
            })

        # If incorrect, add to revision_queue
        if not is_correct:
            concept_name = q_dict.get('concept', f"{subj_name}: {topic_name}")
            # Check if active revision item exists
            cursor.execute(
                "SELECT id FROM revision_queue WHERE user_id = ? AND concept = ? AND completed = 0",
                (user_id, concept_name)
            )
            existing_rev = cursor.fetchone()
            if not existing_rev:
                cursor.execute('''
                INSERT INTO revision_queue (user_id, question_id, concept, due_date, interval_days, completed, created_at)
                VALUES (?, ?, ?, ?, 1, 0, ?)
                ''', (user_id, q_id, concept_name, tomorrow_str, now_str))

        # Parse options
        opts = []
        try:
            opts = json.loads(q_dict.get('options', '[]'))
        except Exception:
            pass

        results.append({
            "question_id": q_id,
            "question": q_dict.get('question'),
            "options": opts,
            "selected_index": sel_idx,
            "correct_index": correct_idx,
            "is_correct": bool(is_correct),
            "explanation": q_dict.get('explanation', ''),
            "misconception": q_dict.get('misconception', ''),
            "concept": q_dict.get('concept', ''),
            "topic": topic_name
        })

    accuracy = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    # Determine next difficulty
    if accuracy >= 80:
        next_difficulty = "hard"
    elif accuracy >= 50:
        next_difficulty = "medium"
    else:
        next_difficulty = "easy"

    # Next action suggestion
    next_action = generate_next_action_with_ai(accuracy, primary_subject, primary_topic, weak_concept)

    conn.commit()
    conn.close()

    return {
        "success": True,
        "score": correct_count,
        "total": total,
        "accuracy": accuracy,
        "next_difficulty": next_difficulty,
        "next_action": next_action,
        "results": results,
        "updated_mastery": updated_mastery
    }

def advance_revision_item(revision_id):
    """
    Updates interval_days in revision_queue:
    1 -> 3
    3 -> 7
    7 -> mark completed
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM revision_queue WHERE id = ?", (revision_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Revision item not found"}

    curr_interval = row['interval_days']
    if curr_interval == 1:
        new_interval = 3
        is_completed = 0
        new_due = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    elif curr_interval == 3:
        new_interval = 7
        is_completed = 0
        new_due = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        new_interval = curr_interval
        is_completed = 1
        new_due = row['due_date']

    cursor.execute('''
    UPDATE revision_queue
    SET interval_days = ?, completed = ?, due_date = ?
    WHERE id = ?
    ''', (new_interval, is_completed, new_due, revision_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "completed": bool(is_completed),
        "new_interval": new_interval,
        "new_due_date": new_due
    }
