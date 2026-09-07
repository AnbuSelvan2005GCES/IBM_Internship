from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import diagnose_problem
from database import init_db, log_diagnosis, get_recent_diagnoses

app = FastAPI(
    title="AI IT Helpdesk Agent",
    description="AI-powered IT troubleshooting system using RAG and diagnostic tools",
    version="1.0.0"
)

# Allow the frontend (running on a different origin/port) to call this API.
# Tighten allow_origins to your actual frontend URL before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class HelpdeskRequest(BaseModel):
    problem: str


@app.get("/")
def home():
    return {
        "message": "AI IT Helpdesk Agent is running"
    }


@app.post("/diagnose")
def diagnose(request: HelpdeskRequest):
    try:
        result = diagnose_problem(request.problem)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate a diagnosis: {e}"
        )

    try:
        log_diagnosis(request.problem, result)
    except Exception:
        # Logging failures shouldn't break the response to the user.
        pass

    return {
        "problem": request.problem,
        "diagnosis": result
    }


@app.get("/history")
def history(limit: int = 20):
    return {"diagnoses": get_recent_diagnoses(limit)}
