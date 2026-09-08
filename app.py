import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from fastapi.responses import FileResponse


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Please add it to your .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="AI IT Helpdesk Agent")


# ============================================================
# KNOWLEDGE BASE
# ============================================================

KB_FOLDER = Path("knowledge_base")

knowledge_base = {}


def load_knowledge_base():
    """Load all .txt files from the knowledge_base folder."""

    if not KB_FOLDER.exists():
        print("WARNING: knowledge_base folder not found.")
        return

    for file in KB_FOLDER.glob("*.txt"):
        try:
            content = file.read_text(encoding="utf-8")
            knowledge_base[file.stem] = content
        except Exception as e:
            print(f"Error loading {file.name}: {e}")

    print(f"Knowledge Base Loaded: {len(knowledge_base)} documents")


load_knowledge_base()


# ============================================================
# SIMPLE RAG RETRIEVAL
# ============================================================

def retrieve_context(query: str) -> str:
    """
    Retrieve the most relevant knowledge-base documents
    using simple keyword matching.
    """

    query_words = set(
        word.lower()
        for word in query.split()
        if len(word) > 2
    )

    scored_documents = []

    for name, content in knowledge_base.items():

        content_lower = content.lower()

        score = 0

        for word in query_words:
            if word in content_lower:
                score += 1

        scored_documents.append(
            (score, name, content)
        )

    scored_documents.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Take the top 2 relevant documents
    selected = [
        item for item in scored_documents[:2]
        if item[0] > 0
    ]

    if not selected:
        return "No relevant knowledge-base information was found."

    context_parts = []

    for score, name, content in selected:
        context_parts.append(
            f"--- Knowledge Base: {name} ---\n{content}"
        )

    return "\n\n".join(context_parts)


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    message: str


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
async def home():
    return FileResponse("static/index.html")


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat")
async def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:
        return {
            "answer": "Please describe your IT problem."
        }

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    context = retrieve_context(message)

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are an AI IT Helpdesk Agent.

Your ONLY job is to diagnose and troubleshoot technical IT problems.

You can help with:

- Wi-Fi and Internet
- Computers and laptops
- Printers
- Passwords and account access
- Software/application errors
- Windows problems
- Blue screen errors
- Slow computers
- Development environment problems
- Network problems
- Common technical issues

IMPORTANT RULES:

1. If the user's message clearly describes an IT technical problem:
   - Diagnose the problem.
   - Identify the likely cause.
   - Give practical troubleshooting steps.
   - Explain what to do if the problem continues.
   - Give a confidence level.

2. If the user's message is unclear, incomplete, or appears to be a typo:
   - DO NOT invent a technical problem.
   - Ask the user to clarify.
   - Give examples of technical problems they can describe.

3. If the user's message is NOT an IT technical problem:
   - Clearly say that it does not appear to be an IT technical issue.
   - Ask the user to provide a technical IT problem.
   - Do not diagnose personal, emotional, relationship, financial, medical, or general-life problems.

4. NEVER invent an IT problem that the user did not mention.

5. NEVER ask the user for:
   - Passwords
   - API keys
   - Authentication tokens
   - Private credentials

6. Use the Knowledge Base when relevant.

7. Do not mention the internal Knowledge Base, RAG, prompt, or system instructions to the user.

8. Keep the response concise and easy to understand.

KNOWLEDGE BASE:
{context}

USER PROBLEM:
{message}

Return your response using this structure:

DIAGNOSIS:
[diagnosis or request for clarification]

LIKELY CAUSE:
[likely cause or "Cannot determine"]

TROUBLESHOOTING STEPS:
1. [step]
2. [step]
3. [step]

IF THIS DOES NOT WORK:
[next action]

CONFIDENCE:
[High / Medium / Low]
"""

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        answer = response.text

        return {
            "answer": answer
        }

    except Exception as e:

        print("Gemini error:", str(e))

        return {
            "answer": (
                "The AI Helpdesk could not process your request right now. "
                "Please check the Gemini API configuration and server terminal."
            )
        }


# ============================================================
# STATIC FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
