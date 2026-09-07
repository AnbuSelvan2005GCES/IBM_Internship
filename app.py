from fastapi import FastAPI
from pydantic import BaseModel

from agent import diagnose_problem


app = FastAPI(
    title="AI IT Helpdesk Agent",
    description="AI-powered IT troubleshooting system using RAG and diagnostic tools",
    version="1.0.0"
)


class HelpdeskRequest(BaseModel):
    problem: str


@app.get("/")
def home():
    return {
        "message": "AI IT Helpdesk Agent is running"
    }


@app.post("/diagnose")
def diagnose(request: HelpdeskRequest):

    result = diagnose_problem(request.problem)

    return {
        "problem": request.problem,
        "diagnosis": result
    }