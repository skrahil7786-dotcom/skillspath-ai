import os
import re
import json
import hashlib
from dotenv import load_dotenv
from database import get_db

load_dotenv()

def get_api_key():
    return os.environ.get('GEMINI_API_KEY', '').strip()

def get_cached_ai_response(cache_key):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT response_json FROM ai_cache WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()
        if row and row['response_json']:
            return json.loads(row['response_json'])
    except Exception:
        pass
    return None

def set_cached_ai_response(cache_key, prompt_type, data):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO ai_cache (cache_key, prompt_type, response_json, created_at) VALUES (?, ?, ?, datetime('now'))",
            (cache_key, prompt_type, json.dumps(data))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def clean_json_text(text):
    if not text:
        return ""
    text = text.strip()
    # Strip markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def call_gemini(prompt, system_instruction=None, retry_count=1):
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Try primary model name
        for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception:
                continue

        # If google.genai failed, try requests directly to Gemini REST endpoint
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass

    if retry_count > 0:
        # Shorter instruction retry
        short_prompt = prompt + "\nOutput strictly valid JSON with no comments or explanations."
        return call_gemini(short_prompt, system_instruction=system_instruction, retry_count=retry_count - 1)

    return None

def extract_topics_with_ai(syllabus_text, subject_name="General"):
    cache_key = hashlib.md5(f"topics:{subject_name}:{syllabus_text[:200]}".encode('utf-8')).hexdigest()
    cached = get_cached_ai_response(cache_key)
    if cached:
        return cached

    prompt = f"""You are an expert curriculum analyzer for Indian engineering exams.
Subject: {subject_name}
Text:
\"\"\"{syllabus_text[:4000]}\"\"\"

Extract 5 to 10 key technical topics from the above syllabus or notes text.
Return ONLY a valid JSON array of objects with keys:
- "topic": name of topic (string)
- "importance": integer from 1 to 5

Example output:
[
  {{"topic": "Binary Search Trees", "importance": 5}},
  {{"topic": "Dynamic Programming", "importance": 4}}
]
"""
    raw_response = call_gemini(prompt)
    if raw_response:
        try:
            cleaned = clean_json_text(raw_response)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                set_cached_ai_response(cache_key, "extract_topics", parsed)
                return parsed
        except Exception:
            pass

    return extract_topics_local(syllabus_text, subject_name)

def extract_topics_local(syllabus_text, subject_name="General"):
    """Local fallback keyword and paragraph-based logic."""
    if not syllabus_text or not syllabus_text.strip():
        return []

    lines = syllabus_text.splitlines()
    candidates = []
    
    # Common engineering keywords
    tech_keywords = [
        "algorithm", "array", "tree", "graph", "sorting", "stack", "queue", "hashing",
        "database", "sql", "normalization", "transaction", "acid", "index", "concurrency",
        "process", "thread", "memory", "deadlock", "scheduling", "paging", "file system",
        "oop", "inheritance", "polymorphism", "collection", "multithreading", "exception",
        "network", "tcp", "ip", "routing", "osi", "protocol", "socket",
        "calculus", "linear algebra", "probability", "statistics", "matrix",
        "logic", "set theory", "combinatorics", "graph theory"
    ]

    for line in lines:
        cleaned = re.sub(r'^[0-9\.\-\*\•\)\s]+', '', line).strip()
        cleaned = re.sub(r'^(Unit|Chapter|Module|Topic|Section)\s*\d*[:\-\s]*', '', cleaned, flags=re.IGNORECASE).strip()
        
        if 4 <= len(cleaned) <= 60 and not cleaned.endswith('?'):
            # Check if it looks like a heading or topic
            if any(char.isupper() for char in cleaned):
                candidates.append(cleaned)
            elif any(kw in cleaned.lower() for kw in tech_keywords):
                candidates.append(cleaned.title())

    # Fallback to paragraph extraction if lines are dense
    if not candidates:
        paragraphs = [p.strip() for p in syllabus_text.split('\n\n') if len(p.strip()) > 10]
        for p in paragraphs[:8]:
            sentences = p.split('.')
            if sentences and len(sentences[0]) < 50:
                candidates.append(sentences[0].strip())

    # De-duplicate while preserving order
    unique_topics = []
    seen = set()
    for c in candidates:
        norm = c.lower().strip()
        if norm not in seen and len(norm) > 2:
            seen.add(norm)
            unique_topics.append(c)
        if len(unique_topics) >= 8:
            break

    if not unique_topics:
        # Default topic based on subject name
        unique_topics = [f"{subject_name} Core Fundamentals", f"{subject_name} Key Applications"]

    return [{"topic": t, "importance": 4} for t in unique_topics]

def generate_plan_with_ai(user_data):
    """Attempt AI generation of 7-day study plan."""
    cache_key = hashlib.md5(f"plan:{user_data.get('id')}:{user_data.get('exam_date')}".encode('utf-8')).hexdigest()
    cached = get_cached_ai_response(cache_key)
    if cached:
        return cached

    prompt = f"""You are an elite study planner for Indian engineering students.
Generate a structured 7-day personalized study plan.

Student Details:
- Name: {user_data.get('name')}
- Goal: {user_data.get('primary_goal')}
- Exam Date: {user_data.get('exam_date')}
- Daily Study Hours: {user_data.get('study_hours_per_day')}
- Selected Subjects: {json.dumps(user_data.get('subjects', []))}
- Weak Areas: {json.dumps(user_data.get('weak_topics', []))}
- Preferences: {json.dumps(user_data.get('preferences', {}))}

Rules:
1. Return strictly an array of 7 items, day_number 1 to 7.
2. Divide study time: ~50% learning, 30% practice, 20% revision.
3. Day 1-5: High-priority subjects and weak topics.
4. Day 6: Mixed revision and practice.
5. Day 7: Weekly mock test or comprehensive revision.
6. Return ONLY valid JSON array with keys:
  - "day_number" (1 to 7)
  - "focus_subject"
  - "focus_topic"
  - "study_minutes" (integer)
  - "learning_task"
  - "practice_task"
  - "revision_task"
  - "recommended_resource_type"
  - "reason"
"""
    raw_response = call_gemini(prompt)
    if raw_response:
        try:
            cleaned = clean_json_text(raw_response)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) == 7:
                set_cached_ai_response(cache_key, "generate_plan", parsed)
                return parsed
        except Exception:
            pass
    return None

def generate_quiz_with_ai(subject_name, difficulty="medium", count=5):
    """Generate 5 adaptive MCQs using Gemini."""
    cache_key = hashlib.md5(f"quiz:{subject_name}:{difficulty}:{count}".encode('utf-8')).hexdigest()
    cached = get_cached_ai_response(cache_key)
    if cached:
        return cached

    prompt = f"""Generate exactly {count} multiple-choice questions for Indian engineering students.
Subject: {subject_name}
Difficulty: {difficulty}

Target exams: GATE CSE, Campus Tech Placements (TCS, Infosys, Wipro, Amazon, Google).

Return ONLY a valid JSON array of objects with keys:
- "subject_name": "{subject_name}"
- "topic": name of specific subtopic
- "concept": specific concept tested
- "question": clear question text
- "options": array of exactly 4 plausible answer strings
- "correct_index": integer index (0, 1, 2, or 3)
- "difficulty": "{difficulty}"
- "explanation": step-by-step reason why the correct option is right
- "misconception": typical blunder or faulty reasoning students make
"""
    raw_response = call_gemini(prompt)
    if raw_response:
        try:
            cleaned = clean_json_text(raw_response)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) == count:
                set_cached_ai_response(cache_key, "generate_quiz", parsed)
                return parsed
        except Exception:
            pass
    return None

def generate_next_action_with_ai(accuracy, subject_name, topic, weak_concept=None):
    """Generate next action suggestion using Gemini or fallback."""
    if get_api_key():
        prompt = f"""Student completed a quiz on {subject_name} ({topic}).
Accuracy: {accuracy}%.
Identified weak concept: {weak_concept or 'None'}.

Provide exactly ONE motivating and actionable advice sentence (under 25 words) for their next study step.
Output only the sentence.
"""
        response = call_gemini(prompt)
        if response and len(response.strip()) > 10:
            return response.strip().replace('"', '')

    # Fallback rules
    if accuracy <= 40:
        return f"Revise the fundamentals of {topic} for 30 minutes, then attempt 3 easy questions."
    elif accuracy < 80:
        target = weak_concept if weak_concept else topic
        return f"Practice 5 targeted questions on {target}. Review the explanation for each mistake."
    else:
        return f"Move to a harder topic in {subject_name} and attempt mixed practice."
