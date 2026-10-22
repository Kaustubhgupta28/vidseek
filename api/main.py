"""FastAPI app: /api/ingest, /api/progress, /api/videos, /api/ask + static UI."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from vidseek import index, ingest
from vidseek.answer import ask_core

app = FastAPI(title="VidSeek")
STATIC = Path(__file__).parent / "static"


class Link(BaseModel):
    url: str


class Question(BaseModel):
    question: str


@app.post("/api/ingest")
def ingest_endpoint(body: Link):
    if not ingest.start(body.url):
        raise HTTPException(409, "Ek process pehle se chal raha hai.")
    return {"started": True}


@app.get("/api/progress")
def progress():
    return ingest.JOB


@app.get("/api/videos")
def videos():
    return index.list_videos_indexed()


@app.post("/api/ask")
def ask(body: Question):
    if index.count() == 0:
        raise HTTPException(400, "Pehle koi video add karo.")
    return ask_core(body.question)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")
