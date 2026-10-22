# Setup (Windows)
1. `python -m venv venv` then `venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, put your Groq key (console.groq.com). Never commit `.env`.
4. `uvicorn main:app --reload`, open http://localhost:8000, paste a YouTube link, press Add, wait for the progress bar, ask.
