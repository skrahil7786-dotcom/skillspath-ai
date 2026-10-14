import os
import io
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import pypdf

from database import init_db, get_db
from ai_service import extract_topics_with_ai, extract_topics_local
from study_planner import generate_personalized_plan
from quiz_engine import get_or_create_quiz, submit_quiz_answers, advance_revision_item

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'skillpath_ai_secure_hackathon_key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Initialize database tables on startup
init_db()

# -------------------------------------------------------------
# Web Page Routes
# -------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/onboarding')
def onboarding():
    user_id = request.args.get('user_id', '')
    return render_template('onboarding.html', user_id=user_id)

@app.route('/plan')
@app.route('/plan/<int:user_id>')
def plan_page(user_id=None):
    if not user_id:
        user_id = request.args.get('user_id', 1)
    return render_template('plan.html', user_id=user_id)

@app.route('/quiz')
@app.route('/quiz/<int:user_id>')
def quiz_page(user_id=None):
    if not user_id:
        user_id = request.args.get('user_id', 1)
    subject = request.args.get('subject', 'Data Structures & Algorithms')
    return render_template('quiz.html', user_id=user_id, subject=subject)

@app.route('/dashboard')
@app.route('/dashboard/<int:user_id>')
def dashboard_page(user_id=None):
    if not user_id:
        user_id = request.args.get('user_id')
    return render_template('dashboard.html', user_id=user_id)

@app.route('/auth/login')
def login_page():
    return render_template('auth/login.html')

@app.route('/auth/signup')
def signup_page():
    return render_template('auth/signup.html')

@app.route('/mentor')
@app.route('/mentor/<int:user_id>')
def mentor_page(user_id=None):
    if not user_id:
        user_id = request.args.get('user_id')
    return render_template('mentor.html', user_id=user_id)

@app.route('/resources')
def resources_page():
    return render_template('resources.html')

@app.route('/reminders')
@app.route('/reminders/<int:user_id>')
def reminders_page(user_id=None):
    if not user_id:
        user_id = request.args.get('user_id')
    return render_template('reminders.html', user_id=user_id)

@app.route('/api/mentor/chat', methods=['POST'])
def api_mentor_chat():
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = data.get('user_id')
        user_msg = (data.get('message') or '').strip()
        if not user_msg:
            return jsonify({"success": False, "error": "Message is required"}), 400

        # Retrieve user context if available
        context_str = "You are MentorAI, an expert engineering mentor for Indian students preparing for GATE CSE, Placements, and Semester exams."
        if user_id:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT name, primary_goal, exam_date FROM users WHERE id = ?", (user_id,))
                u_row = cursor.fetchone()
                if u_row:
                    context_str += f" The student is {u_row['name']}, targeting {u_row['primary_goal']} on {u_row['exam_date']}."
                cursor.execute("SELECT topic, mastery FROM topics WHERE user_id = ? AND mastery < 50", (user_id,))
                weak_topics = [f"{r['topic']} ({r['mastery']}% mastery)" for r in cursor.fetchall()]
                if weak_topics:
                    context_str += f" Their identified weak areas are: {', '.join(weak_topics)}."
                conn.close()
            except Exception:
                pass

        prompt = f"""{context_str}

Student Question: "{user_msg}"

Provide a concise, encouraging, and pedagogically sound response (under 120 words). If they asked about a concept, explain the core intuition with a quick rule or code example. If they asked for a plan or resource, give specific recommendations. Focus on clarity and high yield.
"""
        from ai_service import call_gemini
        ai_reply = call_gemini(prompt)

        if not ai_reply or len(ai_reply.strip()) < 10:
            # Smart contextual fallback matching engineering topics
            msg_lower = user_msg.lower()
            if "normalization" in msg_lower or "dbms" in msg_lower or "2nf" in msg_lower or "3nf" in msg_lower or "bcnf" in msg_lower:
                ai_reply = "Start with functional dependencies. Remember that 2NF eliminates partial dependencies (non-prime depending on part of candidate key), while 3NF eliminates transitive dependencies (X -> Y -> Z). For BCNF, every determinant must be a candidate key. Dedicate 20 minutes to practice decomposition questions!"
            elif "dynamic programming" in msg_lower or "dp" in msg_lower or "knapsack" in msg_lower:
                ai_reply = "In Dynamic Programming, focus first on identifying the state and recurrence relation. For 0/1 Knapsack, state is dp[i][w] = max value using first i items with weight cap w. Always solve the recursive tree with memoization before writing bottom-up tabulation."
            elif "weak" in msg_lower or "weakest" in msg_lower:
                ai_reply = "Reviewing your latest quiz data shows key stumbling blocks in Process Synchronization and Dynamic Programming. Let's schedule a 30-minute high-yield practice session on Mutex vs Semaphores today."
            elif "revision" in msg_lower or "30-minute" in msg_lower or "plan" in msg_lower:
                ai_reply = "Here is your 30-minute sprint: 10 minutes active recall of key definitions, 15 minutes solving 3 targeted questions from your revision queue, and 5 minutes noting any misconceptions. Let's start now!"
            elif "resource" in msg_lower or "recommend" in msg_lower:
                ai_reply = "For core CS topics: Check NPTEL's DBMS series by Prof. Shamik Sural, Gate Smashers on YouTube for quick OS concepts, and GeeksforGeeks practice tracks for DSA patterns."
            else:
                ai_reply = "Focus on breaking this concept down into smaller, testable sub-problems. Review the fundamentals for 15 minutes, try 2 easy examples, and then take an adaptive quiz to verify your intuition. You've got this!"

        return jsonify({
            "success": True,
            "reply": ai_reply
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# Onboarding API Endpoints
# -------------------------------------------------------------

@app.route('/api/onboarding/step1', methods=['POST'])
def onboarding_step1():
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        name = (data.get('name') or '').strip()
        education_level = data.get('education_level') or 'B.Tech'
        branch = data.get('branch') or 'CSE'
        year = str(data.get('year') or '3')
        college_name = (data.get('college_name') or '').strip()
        user_id = data.get('user_id')

        if not name:
            return jsonify({"success": False, "error": "Full name is required"}), 400

        conn = get_db()
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()

        if user_id:
            cursor.execute('''
            UPDATE users SET name=?, education_level=?, branch=?, year=?, college_name=?, updated_at=?
            WHERE id=?
            ''', (name, education_level, branch, year, college_name, now_str, user_id))
        else:
            cursor.execute('''
            INSERT INTO users (name, education_level, branch, year, college_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, education_level, branch, year, college_name, now_str, now_str))
            user_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": user_id,
            "next_step": 2
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/step2', methods=['POST'])
def onboarding_step2():
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        primary_goal = data.get('primary_goal') or 'Campus Placement'
        exam_name = data.get('exam_name') or primary_goal
        exam_date = data.get('exam_date')
        if not exam_date:
            # Default to 90 days from now if not provided
            exam_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        preparation_stage = data.get('preparation_stage') or 'Just starting'

        target_role = data.get('target_role')
        gate_attempt_year = data.get('gate_attempt_year')
        semester = data.get('semester')
        government_exam_category = data.get('government_exam_category')
        now_str = datetime.now().isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users SET
            primary_goal = ?, exam_name = ?, exam_date = ?, preparation_stage = ?,
            target_role = ?, gate_attempt_year = ?, semester = ?, government_exam_category = ?,
            updated_at = ?
        WHERE id = ?
        ''', (
            primary_goal, exam_name, exam_date, preparation_stage,
            target_role, gate_attempt_year, semester, government_exam_category,
            now_str, user_id
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": int(user_id),
            "next_step": 3
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/step3', methods=['POST'])
def onboarding_step3():
    try:
        user_id = None
        subjects = []
        syllabus_text = ""
        extracted_topics = []

        # Handle multipart/form-data or application/json
        if request.content_type and 'multipart/form-data' in request.content_type:
            user_id = request.form.get('user_id')
            subjects_raw = request.form.get('subjects')
            if subjects_raw:
                try:
                    subjects = json.loads(subjects_raw)
                except Exception:
                    subjects = []
            syllabus_text = request.form.get('syllabus_text', '')

            # Check for file upload
            if 'notes_file' in request.files:
                file = request.files['notes_file']
                if file and file.filename:
                    filename = file.filename.lower()
                    file_bytes = file.read()
                    if filename.endswith('.pdf'):
                        try:
                            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                            extracted_parts = []
                            for page in reader.pages[:15]:  # Process up to 15 pages
                                txt = page.extract_text()
                                if txt:
                                    extracted_parts.append(txt)
                            file_extracted = "\n".join(extracted_parts)
                            syllabus_text = (syllabus_text + "\n" + file_extracted).strip()
                        except Exception:
                            pass
                    elif filename.endswith('.txt'):
                        try:
                            syllabus_text = (syllabus_text + "\n" + file_bytes.decode('utf-8', errors='ignore')).strip()
                        except Exception:
                            pass
        else:
            data = request.get_json(force=True, silent=True) or {}
            user_id = data.get('user_id')
            subjects = data.get('subjects', [])
            syllabus_text = data.get('syllabus_text', '')

        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        # Extract topics if syllabus or notes provided
        if syllabus_text and syllabus_text.strip():
            primary_subject = subjects[0].get('subject_name', 'General') if subjects else 'General'
            extracted_topics = extract_topics_with_ai(syllabus_text, primary_subject)

        conn = get_db()
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()

        # Replace user_subjects
        cursor.execute("DELETE FROM user_subjects WHERE user_id = ?", (user_id,))
        for s in subjects:
            s_name = s.get('subject_name', '').strip()
            if not s_name:
                continue
            cursor.execute('''
            INSERT INTO user_subjects (
                user_id, subject_name, confidence_level, priority,
                completed_topics, difficult_topics, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                s_name,
                s.get('confidence_level', 'Average'),
                s.get('priority', 'Medium'),
                s.get('completed_topics', ''),
                s.get('difficult_topics', ''),
                now_str
            ))

        # Also register extracted topics into topics table if available
        if extracted_topics:
            for item in extracted_topics:
                t_name = item.get('topic')
                t_imp = item.get('importance', 4)
                cursor.execute(
                    "INSERT INTO topics (user_id, subject_name, topic, importance, mastery, status, created_at) VALUES (?, ?, ?, ?, 40, 'not_started', ?)",
                    (user_id, subjects[0].get('subject_name', 'General') if subjects else 'General', t_name, t_imp, now_str)
                )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": int(user_id),
            "next_step": 4,
            "extracted_topics": extracted_topics
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/step4', methods=['POST'])
def onboarding_step4():
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        study_days = int(data.get('study_days_per_week', 6) or 6)
        study_hours = float(data.get('study_hours_per_day', 3.0) or 3.0)
        preferred_time = data.get('preferred_time') or 'Flexible'
        
        learning_styles = data.get('learning_styles', [])
        if not isinstance(learning_styles, str):
            learning_styles = json.dumps(learning_styles)

        language_pref = data.get('language_preference') or 'English'
        
        resource_pref = data.get('resource_preferences', [])
        if not isinstance(resource_pref, str):
            resource_pref = json.dumps(resource_pref)

        daily_rev = 1 if str(data.get('daily_revision_enabled', '1')).lower() in ['1', 'true', 'yes'] else 0
        weekly_mock = 1 if str(data.get('weekly_mock_test_enabled', '1')).lower() in ['1', 'true', 'yes'] else 0
        now_str = datetime.now().isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_preferences WHERE user_id = ?", (user_id,))
        cursor.execute('''
        INSERT INTO study_preferences (
            user_id, study_days_per_week, study_hours_per_day, preferred_time,
            learning_styles, language_preference, resource_preferences,
            daily_revision_enabled, weekly_mock_test_enabled, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, study_days, study_hours, preferred_time,
            learning_styles, language_pref, resource_pref,
            daily_rev, weekly_mock, now_str
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": int(user_id),
            "next_step": 5
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/step5', methods=['POST'])
def onboarding_step5():
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        challenges = data.get('challenges', [])
        if not isinstance(challenges, str):
            challenges = json.dumps(challenges)

        weak_topics = data.get('weak_topics', [])
        if not isinstance(weak_topics, str):
            weak_topics = json.dumps(weak_topics)

        avoid_topics = data.get('avoid_topics', [])
        if not isinstance(avoid_topics, str):
            avoid_topics = json.dumps(avoid_topics)

        upcoming_events = (data.get('upcoming_events') or '').strip()
        now_str = datetime.now().isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_challenges WHERE user_id = ?", (user_id,))
        cursor.execute('''
        INSERT INTO user_challenges (
            user_id, challenges, weak_topics, avoid_topics, upcoming_events, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, challenges, weak_topics, avoid_topics, upcoming_events, now_str))

        # Check if daily revision or weekly mock test were sent in step 5
        if 'daily_revision' in data or 'weekly_mock_test' in data:
            daily_rev = 1 if str(data.get('daily_revision', 'yes')).lower() in ['yes', 'true', '1'] else 0
            weekly_mock = 1 if str(data.get('weekly_mock_test', 'yes')).lower() in ['yes', 'true', '1'] else 0
            cursor.execute('''
            UPDATE study_preferences
            SET daily_revision_enabled = ?, weekly_mock_test_enabled = ?
            WHERE user_id = ?
            ''', (daily_rev, weekly_mock, user_id))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "user_id": int(user_id),
            "next_step": "review"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/review/<int:user_id>', methods=['GET'])
def onboarding_review(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        user = dict(user_row)

        cursor.execute("SELECT * FROM user_subjects WHERE user_id = ?", (user_id,))
        subjects = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM study_preferences WHERE user_id = ?", (user_id,))
        pref_row = cursor.fetchone()
        preferences = dict(pref_row) if pref_row else {}

        cursor.execute("SELECT * FROM user_challenges WHERE user_id = ?", (user_id,))
        chal_row = cursor.fetchone()
        challenges = dict(chal_row) if chal_row else {}

        conn.close()

        # Parse JSON fields safely
        for key in ['learning_styles', 'resource_preferences']:
            if key in preferences and isinstance(preferences[key], str) and preferences[key].startswith('['):
                try:
                    preferences[key] = json.loads(preferences[key])
                except Exception:
                    pass

        for key in ['challenges', 'weak_topics', 'avoid_topics']:
            if key in challenges and isinstance(challenges[key], str) and challenges[key].startswith('['):
                try:
                    challenges[key] = json.loads(challenges[key])
                except Exception:
                    pass

        return jsonify({
            "success": True,
            "data": {
                "user": user,
                "subjects": subjects,
                "preferences": preferences,
                "challenges": challenges
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/onboarding/generate-plan/<int:user_id>', methods=['POST'])
def onboarding_generate_plan(user_id):
    try:
        result = generate_personalized_plan(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# Quiz API Endpoints
# -------------------------------------------------------------

@app.route('/api/quiz/<int:user_id>', methods=['POST'])
def api_quiz_generate(user_id):
    try:
        data = request.get_json(force=True, silent=True) or {}
        subject_name = data.get('subject_name') or 'Data Structures & Algorithms'
        difficulty = data.get('difficulty') or 'medium'

        questions = get_or_create_quiz(user_id, subject_name, difficulty)
        return jsonify({
            "success": True,
            "questions": questions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/quiz/<int:user_id>/submit', methods=['POST'])
def api_quiz_submit(user_id):
    try:
        data = request.get_json(force=True, silent=True) or {}
        answers = data.get('answers', [])
        result = submit_quiz_answers(user_id, answers)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# Revision API Endpoints
# -------------------------------------------------------------

@app.route('/api/revision/<int:revision_id>/complete', methods=['POST'])
def api_revision_complete(revision_id):
    try:
        result = advance_revision_item(revision_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# Dashboard API Endpoint
# -------------------------------------------------------------

@app.route('/api/dashboard/<int:user_id>', methods=['GET'])
def api_dashboard(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # User Profile
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        user = dict(user_row)

        # 1. Topic Mastery List
        cursor.execute("SELECT * FROM topics WHERE user_id = ? ORDER BY mastery ASC", (user_id,))
        topics = [dict(r) for r in cursor.fetchall()]

        # Compute average mastery
        if topics:
            avg_mastery = sum(t['mastery'] for t in topics) / len(topics)
        else:
            avg_mastery = 50.0

        # 2. Weak Topics (mastery < 50 or in user challenges)
        cursor.execute("SELECT * FROM user_challenges WHERE user_id = ?", (user_id,))
        chal_row = cursor.fetchone()
        weak_topics_set = set()
        if chal_row and chal_row['weak_topics']:
            try:
                wt_parsed = json.loads(chal_row['weak_topics'])
                if isinstance(wt_parsed, list):
                    weak_topics_set.update(wt_parsed)
                else:
                    weak_topics_set.add(str(wt_parsed))
            except Exception:
                weak_topics_set.update([w.strip() for w in chal_row['weak_topics'].split(',') if w.strip()])

        for t in topics:
            if t['mastery'] < 50:
                weak_topics_set.add(t['topic'])

        weak_topics = list(weak_topics_set)

        # 3. Revision Queue (only incomplete items sorted by due_date)
        cursor.execute('''
        SELECT * FROM revision_queue
        WHERE user_id = ? AND completed = 0
        ORDER BY due_date ASC
        ''', (user_id,))
        revision_queue = [dict(r) for r in cursor.fetchall()]

        # 4. Quiz Accuracy & Streak
        # Check attempts
        cursor.execute("SELECT * FROM attempts WHERE user_id = ? ORDER BY id DESC", (user_id,))
        all_attempts = [dict(r) for r in cursor.fetchall()]

        if all_attempts:
            # Latest quiz accuracy (last 5 attempts or recent session)
            recent_attempts = all_attempts[:5]
            recent_correct = sum(1 for a in recent_attempts if a['is_correct'])
            latest_quiz_accuracy = round((recent_correct / len(recent_attempts)) * 100, 1)
        else:
            latest_quiz_accuracy = 65.0

        # Calculate streak: consecutive calendar days with at least one quiz submission
        cursor.execute('''
        SELECT DISTINCT substr(created_at, 1, 10) as attempt_date
        FROM attempts
        WHERE user_id = ?
        ORDER BY attempt_date DESC
        ''', (user_id,))
        dates_rows = cursor.fetchall()
        attempt_dates = set(r['attempt_date'] for r in dates_rows if r['attempt_date'])

        streak = 0
        current_check = datetime.now().date()
        # If user hasn't attempted today, check starting from yesterday
        if current_check.strftime('%Y-%m-%d') not in attempt_dates:
            current_check = current_check - timedelta(days=1)

        while current_check.strftime('%Y-%m-%d') in attempt_dates:
            streak += 1
            current_check = current_check - timedelta(days=1)

        # 5. Readiness Score
        # readiness = (average_topic_mastery * 0.7) + (latest_quiz_accuracy * 0.3)
        readiness_score = round((avg_mastery * 0.7) + (latest_quiz_accuracy * 0.3), 1)

        # 6. Current 7-Day Plan
        cursor.execute("SELECT * FROM study_plans WHERE user_id = ? ORDER BY day_number ASC", (user_id,))
        study_plans = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "user": user,
                "readiness_score": readiness_score,
                "topic_mastery": topics,
                "weak_topics": weak_topics,
                "revision_queue": revision_queue,
                "quiz_accuracy": latest_quiz_accuracy,
                "streak": streak,
                "study_plan": study_plans
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Do not start a long-running server during non-interactive execution
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
