"""Vector store (Chroma, local, persistent)."""
import chromadb
from vidseek.config import CHROMA_PATH

_col = None


def col():
    global _col
    if _col is None:
        _col = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection(
            "chunks", metadata={"hnsw:space": "cosine"})
    return _col


def count():
    return col().count()


def indexed_ids():
    return {m["vid"] for m in col().get(include=["metadatas"])["metadatas"]}


def list_videos_indexed():
    metas = col().get(include=["metadatas"])["metadatas"]
    return sorted({m["vid"]: m["title"] for m in metas}.items(), key=lambda x: x[1])


def add_chunks(video, chunks, embeddings):
    col().upsert(
        ids=[f"{video['id']}_{c[0]}" for c in chunks], embeddings=embeddings,
        documents=[c[2] for c in chunks],
        metadatas=[{"vid": video["id"], "title": video["title"], "start": c[0], "end": c[1]} for c in chunks])


def query(embeddings, k):
    return col().query(query_embeddings=embeddings, n_results=k,
                       include=["documents", "metadatas", "distances"])


def all_chunks():
    return col().get(include=["documents", "metadatas"])
