# VidSeek 🚀

VidSeek is an AI-powered RAG (Retrieval-Augmented Generation) application that allows users to ingest YouTube videos or entire playlists, index their transcripts, and ask complex questions about the content. It automatically points you to the **exact timestamp** in the video where the topic is discussed.

---

## ✨ Key Features

* **YouTube Playlist & Video Ingestion**: Automatically fetches and processes transcripts from YouTube URLs.
* **AI-Powered Q&A**: Uses LLMs (via Groq API) to answer queries based strictly on the video transcripts with source attribution.
* **Exact Timestamp Jumping**: Interactive source cards let you click and instantly jump the embedded YouTube player to the precise timestamp.
* **Secure Multi-Tenancy**: Built-in user authentication (Signup/Login) ensuring user data, indexed videos, and queries remain isolated per user.
* **Modern Minimalist UI**: Responsive, clean interface supporting both light and dark system themes.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, Python, SQLAlchemy, SQLite
* **Vector Store & RAG**: ChromaDB, LangChain / Custom embedding pipeline
* **AI Model**: Groq API
* **Frontend**: Vanilla HTML5, CSS3, JavaScript, YouTube IFrame API

---

## 📂 Project Structure

```text
vidseek/
│
├── api/
│   ├── main.py            # FastAPI app entry point & API routes
│   └── static/
│       └── index.html     # Frontend user interface
│
├── vidseek/
│   ├── auth.py            # JWT authentication & password hashing
│   ├── database.py        # Database connection & session setup
│   ├── index.py           # Vector indexing & retrieval logic
│   ├── ingest.py          # YouTube transcript fetching & processing
│   └── models.py          # SQLAlchemy database models
│
├── .env                   # Environment variables (API keys)
├── init_db.py             # Database initialization script
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation