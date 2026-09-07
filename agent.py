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