"""
agent.py
The AI Student Support Assistant's core logic. For every question it:
  1. Pulls relevant chunks from the knowledge base (RAG).
  2. Runs relevant deterministic tools (current date, deadlines, exact FAQ
     match, upcoming-notices scan) based on simple keyword heuristics.
  3. Pulls recent conversation history for this session (Memory).
  4. Sends all of the above to Gemini as context and returns the answer.
  5. Records the new exchange back into memory for future turns.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from rag import KnowledgeBase
from tools import (
    get_current_date,
    check_deadline,
    list_notice_categories,
    search_faq_exact,
    extract_upcoming_deadlines
)
from memory import ConversationMemory

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Please add your Gemini API key to the .env file."
    )

client = genai.Client(api_key=api_key)
kb = KnowledgeBase()
memory = ConversationMemory(max_turns=6)

MODEL_NAME = "gemini-2.5-flash"  # swap for whichever Gemini model you have access to

SYSTEM_INSTRUCTIONS = """You are an AI Student Support Assistant for a college.
You answer student questions about regulations, syllabus, FAQs, and notices.

You are given:
1. Relevant knowledge-base excerpts retrieved via RAG (regulations, syllabus,
   FAQs, notices).
2. Live tool output (today's date, deadline calculations, exact FAQ matches,
   upcoming notice deadlines) where relevant.
3. Recent conversation history with this student in this session (memory) —
   use it to stay consistent and avoid re-asking things they already told you.

Answer clearly and concisely, citing which document/category the
information came from when possible (e.g. "According to the attendance
regulations..."). If the knowledge base and tools don't cover the question,
say so honestly rather than guessing — do not invent policies, dates, or
numbers. Keep answers practical and student-friendly.
"""


def _format_kb_context(chunks) -> str:
    if not chunks:
        return "No relevant knowledge-base content was found."
    parts = []
    for chunk in chunks:
        parts.append(f"--- {chunk['filename']} (section {chunk['chunk_id']}) ---\n{chunk['text']}")
    return "\n\n".join(parts)


def _gather_tool_context(question: str) -> str:
    """Run relevant tools based on simple keyword heuristics and format
    their output as text for the prompt."""
    q_lower = question.lower()
    lines = [f"Today's date: {get_current_date()}"]

    deadline_keywords = ("deadline", "last date", "due date", "when is", "upcoming")
    if any(k in q_lower for k in deadline_keywords):
        upcoming = extract_upcoming_deadlines()
        if upcoming:
            lines.append("Upcoming deadlines found in notices:")
            for item in upcoming[:5]:
                lines.append(
                    f"  - {item['title']}: {item['date']} "
                    f"({item['days_remaining']} days remaining)"
                )
        else:
            lines.append("No upcoming deadlines found in the notices file.")

    faq_keywords = ("faq", "how do i", "how can i", "who do i contact", "process for")
    if any(k in q_lower for k in faq_keywords):
        # Try a few likely keywords pulled from the question itself
        candidate_terms = [w for w in q_lower.split() if len(w) > 4]
        matches = []
        for term in candidate_terms:
            matches.extend(search_faq_exact(term))
        if matches:
            unique_matches = list(dict.fromkeys(matches))  # de-dupe, preserve order
            lines.append("Exact FAQ matches found:")
            for m in unique_matches[:3]:
                lines.append(f"  {m}")

    if "categories" in q_lower or "what topics" in q_lower or "what can you help" in q_lower:
        categories = list_notice_categories()
        lines.append(f"Available knowledge base categories: {', '.join(categories)}")

    return "\n".join(lines)


def answer_question(session_id: str, question: str) -> str:
    """
    Main entry point used by app.py.
    Takes a session_id (so Memory can track this student's conversation)
    and a question, and returns the assistant's answer.
    """
    if not question or not question.strip():
        return "Please ask a question about regulations, syllabus, FAQs, or notices."

    # 1. RAG — retrieve relevant knowledge base chunks
    kb_results = kb.search(question, k=4)
    kb_context = _format_kb_context(kb_results)

    # 2. Tools — run relevant deterministic helpers
    tool_context = _gather_tool_context(question)

    # 3. Memory — pull recent conversation history for this session
    history_context = memory.format_history_for_prompt(session_id)

    # 4. Build the prompt
    prompt = f"""Recent conversation history with this student:
{history_context}

Student's new question:
{question}

Knowledge base context:
{kb_context}

Tool output:
{tool_context}

Answer the student's question using the above context.
"""

    # 5. Call Gemini
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"system_instruction": SYSTEM_INSTRUCTIONS}
    )
    answer = response.text

    # 6. Update memory with this exchange
    memory.remember_user_message(session_id, question)
    memory.remember_assistant_message(session_id, answer)

    return answer