"""
tools.py
Deterministic helper functions the agent can call alongside RAG retrieval.
These handle things a language model shouldn't be trusted to compute or
guess on its own — like today's date, how many days remain until a
deadline, or an exact keyword match in the FAQ file.
"""

import os
import re
from datetime import datetime


KB_FOLDER = "knowledge_base"


def get_current_date() -> str:
    """Return today's date as YYYY-MM-DD. Useful for deadline comparisons."""
    return datetime.now().strftime("%Y-%m-%d")


def check_deadline(deadline_date: str) -> dict:
    """
    Given a deadline in YYYY-MM-DD format, return how many days remain
    (negative if it has already passed).
    """
    try:
        deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
        today = datetime.now()
        days_remaining = (deadline - today).days
        return {
            "deadline_date": deadline_date,
            "days_remaining": days_remaining,
            "status": "passed" if days_remaining < 0 else "upcoming"
        }
    except ValueError:
        return {"error": f"'{deadline_date}' is not a valid YYYY-MM-DD date."}


def list_notice_categories(folder: str = KB_FOLDER) -> list:
    """List the knowledge base files currently available (e.g. regulations.txt,
    syllabus.txt, faqs.txt, notices.txt)."""
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.endswith(".txt"))


def search_faq_exact(keyword: str, folder: str = KB_FOLDER) -> list:
    """
    Exact/substring keyword search over faqs.txt specifically.
    Complements semantic RAG search with a literal match — useful when a
    student asks about a specific term (e.g. 'bonafide', 'scholarship')
    and wants the precise Q&A entry rather than the closest semantic match.
    """
    path = os.path.join(folder, "faqs.txt")
    if not os.path.isfile(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # FAQ entries are separated by blank lines, each starting with "Q:"
    entries = [e.strip() for e in text.split("\n\n") if e.strip().startswith("Q:")]
    keyword_lower = keyword.lower()
    return [e for e in entries if keyword_lower in e.lower()]


def extract_upcoming_deadlines(folder: str = KB_FOLDER) -> list:
    """
    Scan notices.txt for dates mentioned in the format YYYY-MM-DD and
    return the ones that are still upcoming, alongside the notice title
    they belong to.
    """
    path = os.path.join(folder, "notices.txt")
    if not os.path.isfile(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    today = datetime.now()
    upcoming = []

    entries = [e.strip() for e in text.split("\n\n") if e.strip()]
    for entry in entries:
        title_match = re.search(r"TITLE:\s*(.+)", entry)
        title = title_match.group(1).strip() if title_match else "Untitled notice"

        for date_str in re.findall(r"\d{4}-\d{2}-\d{2}", entry):
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if date_obj >= today:
                upcoming.append({
                    "title": title,
                    "date": date_str,
                    "days_remaining": (date_obj - today).days
                })

    # De-duplicate and sort by soonest first
    seen = set()
    unique_upcoming = []
    for item in upcoming:
        key = (item["title"], item["date"])
        if key not in seen:
            seen.add(key)
            unique_upcoming.append(item)

    return sorted(unique_upcoming, key=lambda x: x["days_remaining"])