from flask import Flask, render_template, jsonify, request
import scraper
import os
from datetime import datetime, timezone, timedelta
import json

app = Flask(__name__)

d2l_session = None
def get_d2l_session(populate = False):
    global d2l_session
    if d2l_session is None:
        cookie_file = os.getenv("COOKIE_FILE_NAME")
        login_site = os.getenv("LOGIN_SITE")
        d2l_session = scraper.get_authenticated_session(cookie_file, login_site, populate=populate)

    return d2l_session

COMPLETED_FILE = os.getenv("COMPLETED_FILE")

def load_completed() -> set:
    if not os.path.exists(COMPLETED_FILE):
        return set()
    try:
        with open(COMPLETED_FILE) as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_completed(completed: set):
    with open(COMPLETED_FILE, "w") as f:
        json.dump(sorted(completed), f, indent=2)


MAX_DATE = datetime.max.replace(tzinfo=timezone.utc)
URGENT_WINDOW = timedelta(days=3)

def parse_date(date_str):
    if not date_str:
        return MAX_DATE
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return MAX_DATE

def format_due(dt):
    if dt == datetime.max:
        return "No due date"
    return dt.strftime("%b. %d")

def get_due_status(due_dt, now):
    if due_dt == MAX_DATE:
        return "normal"
    if due_dt < now:
        return "overdue"
    if due_dt - now <= URGENT_WINDOW:
        return "urgent"
    return "normal"


def build_course_and_task_data(session):
    courses = []
    tasks = []
    now = datetime.now(timezone.utc)
    completed = load_completed()

    for course in session.courses.values():
        assignment_count = len(course.get_quizzes()) + len(course.get_dropboxes())
        courses.append({
            "name": course.name,
            "assignment_count": assignment_count,
            "included": True
        })

        for quiz in course.get_quizzes().values():
            due_dt = parse_date(quiz.due)
            task_id = f"quiz-{quiz.id}"
            tasks.append({
                "name": quiz.name,
                "url": quiz.url,
                "course": course.name,
                "due_dt": due_dt,
                "due_date": format_due(due_dt),
                "due_iso": due_dt.isoformat(),
                "status": get_due_status(due_dt, now),
                "task_id": task_id,
                "completed": task_id in completed,
            })

        for dropbox in course.get_dropboxes().values():
            due_dt = parse_date(dropbox.due)
            task_id = f"dropbox-{dropbox.id}"
            tasks.append({
                "name": dropbox.name,
                "url": dropbox.url,
                "course": course.name,
                "due_dt": due_dt,
                "due_date": format_due(due_dt),
                "due_iso": due_dt.isoformat(),
                "status": get_due_status(due_dt, now),
                "task_id": task_id,
                "completed": task_id in completed,
            })

    tasks.sort(key=lambda t: t["due_dt"])
    courses.sort(key=lambda c: c["name"])
    return courses, tasks


@app.route('/')
def home():
    courses, tasks = [], []

    if d2l_session is not None:
        courses, tasks = build_course_and_task_data(d2l_session)

    return render_template("index.html", courses=courses, tasks=tasks)


@app.route('/scrape', methods=['POST'])
def scrape():
    session = get_d2l_session(populate=True)  # only place a session is created/authenticated

    if not session.validate_request():
        return jsonify({"error": "Session expired"}), 401

    session.populate_courses()

    return jsonify({"status": "ok", "count": len(session.courses)})


@app.route('/complete', methods=['POST'])
def toggle_complete():
    data = request.get_json(force=True)
    task_id = data.get("task_id")
    is_complete = data.get("completed", False)

    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    completed = load_completed()
    if is_complete:
        completed.add(task_id)
    else:
        completed.discard(task_id)
    save_completed(completed)

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True)