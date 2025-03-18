from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .openai_config import get_sql_query

UNAPPROVED_QUESTIONS_FILE = "query_converter/unapproved_questions.json"
QUESTIONS_FILE = "query_converter/questions.json"

# ✅ Load JSON files safely
def load_json_file(filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

# ✅ Save JSON data
def save_json_file(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# ✅ Load questions and unapproved questions
questions_db = load_json_file(QUESTIONS_FILE)
unapproved_questions = load_json_file(UNAPPROVED_QUESTIONS_FILE)

# ✅ Save a new unapproved question for admin review
def save_unapproved_question(question, sql_query):
    """Stores unapproved questions for admin review."""
    unapproved_questions = load_unapproved_questions()  # Load existing unapproved questions
    unapproved_questions[question] = sql_query  # Add new question
    save_json_file(UNAPPROVED_QUESTIONS_FILE, unapproved_questions)  # Save back to JSON

@csrf_protect
@require_POST
def generate_sql_query(request):
    try:
        data = json.loads(request.body)
        user_query = data.get("question", "").strip()

        if not user_query:
            return JsonResponse({"error": "No query provided"}, status=400)

        sql_query = get_sql_query(user_query)  # Convert question to SQL query
        
        # ✅ If a modification query was blocked, log it
        if sql_query.startswith("Error: Only SELECT queries are allowed"):
            
            return JsonResponse({"error": sql_query})

        # ✅ If question is new, save for review
        existing_questions = load_json_file(QUESTIONS_FILE)
        new_question = user_query not in existing_questions

        if new_question:
            save_unapproved_question(user_query, sql_query)

        return JsonResponse({"sql_query": sql_query, "new_question": new_question})
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)


# ✅ Review Unapproved Questions (Admin Panel)
def review_questions(request):
    """Render the page to review and approve new questions."""
    unapproved_questions = load_json_file(UNAPPROVED_QUESTIONS_FILE)
    return render(request, "review_questions.html", {"unapproved_questions": unapproved_questions})

def load_unapproved_questions():
    if os.path.exists(UNAPPROVED_QUESTIONS_FILE):
        with open(UNAPPROVED_QUESTIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# ✅ Save approved question and remove it from the unapproved list
def approve_and_save_question(question, sql_query):
    """Moves an approved question to the main questions list and removes it from unapproved."""
    
    # Load existing questions
    questions_db = load_json_file(QUESTIONS_FILE)

    # ✅ Save approved question
    questions_db[question] = sql_query
    save_json_file(QUESTIONS_FILE, questions_db)

    # ✅ Remove from unapproved list
    unapproved_questions = load_unapproved_questions()
    if question in unapproved_questions:
        del unapproved_questions[question]
        save_json_file(UNAPPROVED_QUESTIONS_FILE, unapproved_questions)

@csrf_protect
@require_POST
def approve_question(request):
    """Approves a question and moves it to the main questions.json file."""
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        sql_query = data.get("sql_query", "").strip()

        if not question or not sql_query:
            return JsonResponse({"error": "Invalid input"}, status=400)

        approve_and_save_question(question, sql_query)
        return JsonResponse({"success": True})
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

@csrf_protect
@require_POST
def delete_question(request):
    """Deletes an unapproved question."""
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()

        unapproved_questions = load_json_file(UNAPPROVED_QUESTIONS_FILE)
        if question in unapproved_questions:
            del unapproved_questions[question]
            save_json_file(UNAPPROVED_QUESTIONS_FILE, unapproved_questions)

        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)


def query_form(request):
    """Renders the query form and checks if there are unapproved questions."""
    unapproved_questions = load_unapproved_questions()
    has_unapproved = bool(unapproved_questions)  # ✅ True if unapproved questions exist

    return render(request, "query_form.html", {
        "has_unapproved_questions": has_unapproved,
        "new_question": True if has_unapproved else False  # ✅ Set a flag if a new question is present
    })
