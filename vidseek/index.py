"""Vector store (Chroma, local, persistent)."""
import chromadb
from vidseek.config import CHROMA_PATH

_col = None
_active_user_id = None


def set_active_user(user_id: int):
    global _active_user_id
    _active_user_id = user_id


def col():
    global _col
    if _col is None:
        _col = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection(
            "chunks", metadata={"hnsw:space": "cosine"})
    return _col


def count(user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    if uid is not None:
        res = col().get(where={"user_id": uid}, include=[])
        return len(res["ids"])
    return col().count()


def indexed_ids(user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    where = {"user_id": uid} if uid is not None else None
    metas = col().get(where=where, include=["metadatas"])["metadatas"]
    return {m["vid"] for m in metas}


def list_videos_indexed(user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    where = {"user_id": uid} if uid is not None else None
    metas = col().get(where=where, include=["metadatas"])["metadatas"]
    return sorted({m["vid"]: m["title"] for m in metas}.items(), key=lambda x: x[1])


def add_chunks(video, chunks, embeddings, user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    if uid is None:
        raise ValueError("user_id is required for adding chunks")
    col().upsert(
        ids=[f"{uid}_{video['id']}_{c[0]}" for c in chunks], embeddings=embeddings,
        documents=[c[2] for c in chunks],
        metadatas=[{"user_id": uid, "vid": video["id"], "title": video["title"], "start": c[0], "end": c[1]} for c in chunks])


def query(embeddings, k, user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    where = {"user_id": uid} if uid is not None else None
    return col().query(query_embeddings=embeddings, n_results=k,
                       where=where,
                       include=["documents", "metadatas", "distances"])


def all_chunks(user_id=None):
    uid = user_id if user_id is not None else _active_user_id
    where = {"user_id": uid} if uid is not None else None
    return col().get(where=where, include=["documents", "metadatas"])