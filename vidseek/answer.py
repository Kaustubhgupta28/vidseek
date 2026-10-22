"""Retrieve -> grounded answer + citations. Three guards: distance cutoff (no LLM call),
LLM refusal, citation renumbering. Also query expansion (English + Devanagari)."""
import os, re
from groq import Groq
from vidseek import index
from vidseek.config import GROQ_API_KEY, LLM_MODEL, MAX_DISTANCE, REFUSAL, TOP_K
from vidseek.embed import embed_queries

_llm = None

SYSTEM = (
    "Answer ONLY from the excerpts below. If they don't cover it, say exactly: "
    f'"{REFUSAL}". Cite inline like [1], [2] using the excerpt numbers. '
    "LANGUAGE RULE: English question -> English answer. Hindi/Hinglish question -> Roman Hinglish "
    "(Hindi words in English letters, technical terms in English). NEVER write Devanagari script, "
    "even though the excerpts are in Devanagari. "
    "4-6 sentences max. "
    "Never invent a timestamp or video title."
)


def get_llm():
    global _llm
    if _llm is None:
        _llm = Groq(api_key=GROQ_API_KEY)
    return _llm


def _chat(system, user, temperature=0.2):
    r = get_llm().chat.completions.create(
        model=LLM_MODEL, temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return (r.choices[0].message.content or "").strip()


def expand_query(q):
    """Roman Hinglish question -> English + Devanagari (transcripts are in Devanagari)."""
    try:
        return _chat("Rewrite the search query for an index of Hindi/English DSA lecture transcripts. "
                     "Output ONE line: the query in clear English, then ' | ', then the same query in Hindi Devanagari script "
                     "(technical terms like 'Big O' or 'linked list' also in Devanagari). No explanation.", q, 0).replace("\n", " ")
    except Exception:
        return q


def retrieve(question, k=TOP_K, expand=None):
    """-> [(text, meta, distance)] best first. No distance cutoff here."""
    if expand is None:
        expand = os.getenv("EXPAND", "1") == "1"
    qs = [question] + ([expand_query(question)] if expand else [])
    r = index.query(embed_queries(qs), k)
    best = {}
    for i in range(len(qs)):
        for cid, doc, meta, dist in zip(r["ids"][i], r["documents"][i], r["metadatas"][i], r["distances"][i]):
            if cid not in best or dist < best[cid][2]:
                best[cid] = (doc, meta, dist)
    return sorted(best.values(), key=lambda h: h[2])[:k]


def ask_core(question, k=TOP_K):
    hits = retrieve(question, k)
    top = round(hits[0][2], 4) if hits else None
    kept = [h for h in hits if h[2] <= MAX_DISTANCE]
    if not kept:  # guard 1: don't call the LLM at all
        return {"answer": REFUSAL, "sources": [], "grounded": False, "top_distance": top}

    srcs = [{"text": d.split("\n\n", 1)[-1], "vid": m["vid"], "title": m["title"], "start": m["start"],
             "distance": round(dist, 4), "link": f"https://youtu.be/{m['vid']}?t={m['start']}"} for d, m, dist in kept]
    ctx = "\n\n".join(f"[{i+1}] ({s['title']} @ {s['start']}s) {s['text']}" for i, s in enumerate(srcs))
    text = _chat(SYSTEM, f"EXCERPTS\n{ctx}\n\nQUESTION: {question}\n\n"
                 "(English question -> English answer. Hindi/Hinglish question -> Roman Hinglish in English letters. "
                 "NEVER use Devanagari script.)")
    if re.search(r"[\u0900-\u097F]", text):  # Devanagari slipped in -> rewrite in Roman Hinglish
        text = _chat("Rewrite the user's text in Roman Hinglish (Hindi words written in English letters, e.g. 'slow pointer ek "
                     "step aage badhta hai'). Keep technical terms in English and keep citation markers like [1], [2] exactly. "
                     "Do NOT use Devanagari. Output only the rewritten text.", text, 0) or text
    if REFUSAL.lower() in text.lower():  # guard 2: LLM refused itself
        return {"answer": REFUSAL, "sources": [], "grounded": False, "top_distance": top}

    order = []  # guard 3: keep only used citations, renumber 1..N
    for m in re.finditer(r"\[(\d+)\]", text):
        n = int(m.group(1))
        if 1 <= n <= len(srcs) and n not in order:
            order.append(n)
    remap = {old: new for new, old in enumerate(order, 1)}
    text = re.sub(r"\[(\d+)\]", lambda m: f"[{remap[int(m.group(1))]}]" if int(m.group(1)) in remap else "", text)
    return {"answer": text, "sources": [srcs[n - 1] for n in order], "grounded": bool(order), "top_distance": top}
