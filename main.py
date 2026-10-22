"""Entry point.  uvicorn main:app --reload   (or: python main.py)"""
from api.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
