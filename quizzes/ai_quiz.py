import json
import os
import re
from typing import Any, Dict, List

from django.conf import settings
import google.generativeai as genai


def _strip_markdown_fences(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    t = text.strip()
    # Remove leading ```json or ```
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    # Remove trailing ```
    t = re.sub(r"\s*```$", "", t)
    return t


def _validate_question_item(item: Any) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("Invalid question item")

    question_text = item.get("question_text")
    if not isinstance(question_text, str) or not question_text.strip():
        raise ValueError("question_text is required")

    options = item.get("options")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("Each question must have exactly 4 options")

    # Ensure options are strings
    if any(not isinstance(opt, str) or not opt.strip() for opt in options):
        raise ValueError("All options must be non-empty strings")

    correct_answer = item.get("correct_answer")
    if not isinstance(correct_answer, int) or correct_answer not in (0, 1, 2, 3):
        raise ValueError("correct_answer must be an index from 0 to 3")

    difficulty = item.get("difficulty")
    if not isinstance(difficulty, str) or not difficulty.strip():
        raise ValueError("difficulty is required")

    marks = item.get("marks", 1)
    if not isinstance(marks, int):
        marks = int(marks)

    return {
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty": difficulty,
        "marks": marks,
    }


def generate_ai_quiz(*, topic: str, number_of_questions: int, difficulty: str) -> List[Dict[str, Any]]:
    """Generate AI quiz questions via Gemini 2.5 Flash.

    Returns:
        List of question dicts in the exact format required by the API response.
    """

    # Create Gemini client using env vars already configured.
    # Existing project already loads GEMINI_API_KEY from env.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    genai.configure(api_key=api_key)
    model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(model_name)


    prompt = (
        f"Generate exactly {number_of_questions} multiple choice questions about:\n\n"
        f'"{topic}"\n\n'
        f"Difficulty level:\n{difficulty}\n\n"
        "Return ONLY valid JSON.\n"
        "Format:\n"
        "[\n"
        "{\n"
        '"question_text":"...",\n'
        '"options":["Option A","Option B","Option C","Option D"],\n'
        '"correct_answer":2,\n'
        '"difficulty":"medium",\n'
        '"marks":1\n'
        "}\n"
        "]\n\n"
        "Rules:\n"
        "* Exactly four options.\n"
        "* Only one correct answer.\n"
        "* No explanations.\n"
        "* No markdown.\n"
        "* JSON only.\n"
        "* University level.\n"
        "* Avoid repeated questions.\n"
        "* Suitable for exams.\n"
    )

    response = model.generate_content(prompt)
    text = getattr(response, "text", None) or str(response)

    text = _strip_markdown_fences(text)
    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError("Expected JSON array")

    if len(data) != number_of_questions:
        raise ValueError("Unexpected number of questions")

    questions: List[Dict[str, Any]] = []
    for item in data:
        questions.append(_validate_question_item(item))

    # Ensure the final defensive checks match the spec
    for q in questions:
        if len(q["options"]) != 4:
            raise ValueError("Each question must have exactly 4 options")
        if q["correct_answer"] not in (0, 1, 2, 3):
            raise ValueError("correct_answer must be an index from 0 to 3")

    return questions

