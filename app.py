from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import answer_question
from database import init_db, log_qa, get_recent_qa
from memory import ConversationMemory
from tools import list_notice_categories

app = FastAPI(
    title="AI Student Support Assistant",
    description="Answers college-related questions from regulations, "
                 "syllabus, FAQs, and notices using RAG, Tools, and Memory.",
    version="1.0.0"
)

# Allow a frontend running on a different origin/port to call this API.
# Tighten allow_origins to your actual frontend URL before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = ConversationMemory()


@app.on_event("startup")
def on_startup():
    init_db()


class AskRequest(BaseModel):
    session_id: str
    question: str


@app.get("/")
def home():
    return {"message": "AI Student Support Assistant is running"}


@app.post("/ask")
def ask(request: AskRequest):
    if not request.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required.")

    try:
        answer = answer_question(request.session_id, request.question)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate an answer: {e}"
        )

    try:
        log_qa(request.session_id, request.question, answer)
    except Exception:
        # Logging failures shouldn't break the response to the student.
        pass

    return {
        "session_id": request.session_id,
        "question": request.question,
        "answer": answer
    }


@app.get("/history/{session_id}")
def session_history(session_id: str):
    return {"session_id": session_id, "history": memory.get_recent_history(session_id)}


@app.delete("/history/{session_id}")
def clear_history(session_id: str):
    memory.clear(session_id)
    return {"message": f"Conversation memory cleared for session '{session_id}'."}


@app.get("/qa-log")
def qa_log(limit: int = 20):
    return {"log": get_recent_qa(limit)}


@app.get("/categories")
def categories():
    return {"categories": list_notice_categories()}