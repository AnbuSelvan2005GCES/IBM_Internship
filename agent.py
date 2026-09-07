import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from rag import KnowledgeBase
from tools import (
    get_system_information,
    check_internet,
    get_ip_address,
    run_network_diagnostics
)

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

MODEL_NAME = "gemini-2.5-flash"  # swap for whichever Gemini model you have access to

SYSTEM_INSTRUCTIONS = """You are an AI IT Helpdesk Agent.
You diagnose common technical issues and recommend troubleshooting steps.
You are given:
1. Relevant knowledge-base articles retrieved via RAG.
2. Live diagnostic data collected from the user's machine via tools.

Use both to give a clear, step-by-step diagnosis and fix.
If the knowledge base doesn't cover the issue, say so and give your best
general troubleshooting advice. Keep the response structured and practical.
"""


def _format_kb_context(docs):
    if not docs:
        return "No relevant knowledge-base articles were found."
    parts = []
    for doc in docs:
        parts.append(f"--- {doc['filename']} ---\n{doc['text']}")
    return "\n\n".join(parts)


def _gather_diagnostics(problem: str):
    """Decide which tools are relevant and run them.

    Simple heuristic: if the problem mentions network/internet/wifi/connection,
    run the network-related tools. Always include basic system info.
    """
    diagnostics = {
        "system_information": get_system_information()
    }

    network_keywords = ("internet", "network", "wifi", "wi-fi", "connection", "connect", "ping", "offline")
    if any(keyword in problem.lower() for keyword in network_keywords):
        diagnostics["internet_status"] = check_internet()
        diagnostics["ip_address"] = get_ip_address()
        diagnostics["network_diagnostics"] = run_network_diagnostics()

    return diagnostics


def _format_diagnostics(diagnostics: dict) -> str:
    lines = []
    for key, value in diagnostics.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def diagnose_problem(problem: str) -> str:
    """
    Main entry point used by app.py.
    Takes a user-described IT problem, retrieves relevant knowledge-base
    context, gathers live diagnostics, and asks Gemini to produce a
    diagnosis and recommended fix.
    """
    if not problem or not problem.strip():
        return "Please describe the technical issue you're experiencing."

    # 1. Retrieve relevant knowledge base articles (RAG)
    kb_results = kb.search(problem, k=3)
    kb_context = _format_kb_context(kb_results)

    # 2. Gather live diagnostics (Tools)
    diagnostics = _gather_diagnostics(problem)
    diagnostics_text = _format_diagnostics(diagnostics)

    # 3. Build the prompt for Gemini
    prompt = f"""User's reported problem:
{problem}

Knowledge base context:
{kb_context}

Live system diagnostics:
{diagnostics_text}

Based on the above, provide:
1. A likely diagnosis of the issue.
2. Step-by-step troubleshooting instructions.
3. When to escalate to a human IT technician, if applicable.
"""

    # 4. Call Gemini
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"system_instruction": SYSTEM_INSTRUCTIONS}
    )

    return response.text
