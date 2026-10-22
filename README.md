# VidSeek
Video lecture Q&A with timestamp-level retrieval. Add a YouTube video/playlist, ask a doubt (English or Hinglish),
get a grounded answer plus clickable links that jump to the exact second in the exact lecture.

## Pipeline
YouTube link -> `playlist.py` (video list) -> `transcribe.py` (captions, Whisper fallback) -> `chunk.py` (45s windows, overlap,
title prefix) -> `embed.py` (multilingual-e5) -> `index.py` (Chroma) -> `answer.py` (retrieve, Groq LLM, 3 guards, citations)

## Structure
```
vidseek/   core package (config, playlist, transcribe, chunk, embed, index, ingest, answer, evaluate, gen_golden)
api/       FastAPI app + static UI (YouTube IFrame player)
eval/      golden question sets
transcripts/  cached transcripts     chroma_db/  vector store
main.py    entry point
```

## Run
`uvicorn main:app --reload` -> http://localhost:8000   (setup: see SETUP.md)

## Evaluate
`python -m vidseek.evaluate eval/golden.json` ; `python -m vidseek.gen_golden 30` ; `JUDGE=1 python -m vidseek.evaluate eval/golden_auto.json`
