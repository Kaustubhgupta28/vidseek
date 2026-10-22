"""FastAPI app: /api/ingest, /api/progress, /api/videos, /api/ask, /api/config + static UI.
READ_ONLY=1 (deployed demo): adding videos is disabled and heavy ingest deps are never imported."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from vidseek import index
from vidseek.answer import ask_core
from vidseek.config import READ_ONLY

if not READ_ONLY:
    from vidseek import ingest

app = FastAPI(title="VidSeek")
STATIC = Path(__file__).parent / "static"
IDLE = {"running": False, "total": 0, "done": 0, "failed": 0, "current": "", "stopped": None, "last_error": None}


class Link(BaseModel):
    url: str


class Question(BaseModel):
    question: str


@app.get("/api/config")
def config():
    return {"read_only": READ_ONLY}


@app.post("/api/ingest")
def ingest_endpoint(body: Link):
    if READ_ONLY:
        raise HTTPException(403, "Is demo me video add karna band hai.")
    if not ingest.start(body.url):
        raise HTTPException(409, "Ek process pehle se chal raha hai.")
    return {"started": True}


@app.get("/api/progress")
def progress():
    return IDLE if READ_ONLY else ingest.JOB


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
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    if READ_ONLY:  # hide the "add video" UI on the server side (no JS / cache dependence)
        html = html.replace("</head>", "<style>#addrow,#bar,#status,section>.row:first-of-type{display:none!important}</style></head>", 1)
        html = html.replace("Add a YouTube video or playlist, then ask your doubt.",
                            "Ask a doubt about the indexed DSA playlist and jump to the exact moment in the lecture.", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})