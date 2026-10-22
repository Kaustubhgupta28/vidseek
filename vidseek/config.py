"""All settings in one place. Secrets/overrides come from .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CHROMA_PATH = str(ROOT / "chroma_db")
TRANSCRIPT_DIR = ROOT / "transcripts"
TRANSCRIPT_DIR.mkdir(exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "openai/gpt-oss-120b"
EMBED_MODEL = "intfloat/multilingual-e5-small"

# chunking
WINDOW, OVERLAP, MIN_WORDS = 45, 10, 15
# transcription: auto = captions first, Whisper fallback | whisper = audio only
TRANSCRIBE_MODE = os.getenv("TRANSCRIBE_MODE", "auto")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_LANG = os.getenv("WHISPER_LANG", "") or None
MAX_PER_ADD = int(os.getenv("MAX_PER_ADD", "1000"))
# retrieval / answer
TOP_K = 5
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.15"))
READ_ONLY = os.getenv("READ_ONLY", "0") == "1"  # deploy demo: no adding videos
REFUSAL = "Ye topic is video/playlist mein cover nahi hua."
