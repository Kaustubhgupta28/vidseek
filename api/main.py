from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel

from vidseek.config import READ_ONLY
from vidseek.database import get_db, engine, Base
from vidseek.models import User, Video
from vidseek.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)

# Heavy imports and DB creation inside Lifespan to prevent startup freeze
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables safely on startup after port binding
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="VidSeek", lifespan=lifespan)

STATIC = Path(__file__).parent / "static"
IDLE = {"running": False, "total": 0, "done": 0, "failed": 0, "current": "", "stopped": None, "last_error": None}


class Link(BaseModel):
    url: str


class Question(BaseModel):
    question: str


class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


@app.get("/api/config")
def config():
    return {"read_only": READ_ONLY}


@app.post("/api/ingest")
def ingest_endpoint(body: Link, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if READ_ONLY:
        raise HTTPException(403, "Is demo me video add karna band hai.")
    
    from vidseek import ingest
    
    # Pass user_id to ingest so chunks are indexed specifically for this user
    if not ingest.start(body.url, user_id=current_user.id):
        raise HTTPException(409, "Ek process pehle se chal raha hai.")
    
    # Save video entry in DB linked to current user if not already present
    existing_video = db.query(Video).filter(Video.user_id == current_user.id, Video.url == body.url).first()
    if not existing_video:
        new_video = Video(user_id=current_user.id, url=body.url)
        db.add(new_video)
        db.commit()
    
    return {"started": True}


@app.get("/api/progress")
def progress():
    if READ_ONLY:
        return IDLE
    from vidseek import ingest
    return ingest.JOB


@app.get("/api/videos")
def videos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return only the videos added by the currently logged-in user
    user_videos = db.query(Video).filter(Video.user_id == current_user.id).all()
    return [{"url": v.url, "title": v.title or v.url} for v in user_videos]


@app.post("/api/ask")
def ask(body: Question, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_video_count = db.query(Video).filter(Video.user_id == current_user.id).count()
    if user_video_count == 0:
        raise HTTPException(400, "Pehle koi video add karo.")
    
    # Lazy load heavy AI modules when user actually queries
    from vidseek import index
    from vidseek.answer import ask_core
    
    # Set active user context so answer searches only this user's vectors
    index.set_active_user(current_user.id)
    return ask_core(body.question)


@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def home():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    if READ_ONLY: 
        html = html.replace("</head>", "<style>#addrow,#bar,#status,section>.row:first-of-type{display:none!important}</style></head>", 1)
        html = html.replace("Add a YouTube video or playlist, then ask your doubt.",
                            "Ask a doubt about the indexed DSA playlist and jump to the exact moment in the lecture.", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})