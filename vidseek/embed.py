"""Text -> vectors (multilingual e5; needs 'query: ' / 'passage: ' prefixes)."""
from sentence_transformers import SentenceTransformer
from vidseek.config import EMBED_MODEL

_model = None


def _m():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_passages(texts):
    return _m().encode(["passage: " + t for t in texts], normalize_embeddings=True).tolist()


def embed_queries(texts):
    return _m().encode(["query: " + t for t in texts], normalize_embeddings=True).tolist()
