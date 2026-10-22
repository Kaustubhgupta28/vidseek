"""Segments -> time-window chunks. Hand-written so the timestamp survives (generic text
splitters concatenate text and lose it). Overlap, title prefix, junk filter."""
import re
from collections import Counter
from vidseek.config import MIN_WORDS, OVERLAP, WINDOW


def is_repetitive(text, th=0.6):
    """Whisper loop hallucination: one sentence repeated most of the chunk."""
    sents = [s.strip().lower() for s in re.split(r"[.!?\n]+", text) if s.strip()]
    if len(sents) < 3:
        return False
    return Counter(sents).most_common(1)[0][1] / len(sents) >= th


def make_chunks(snips, title):
    """-> [(start_sec, end_sec, text)]"""
    snips = [s for s in snips if s["text"].strip()]
    chunks, i = [], 0
    while i < len(snips):
        t0 = snips[i]["start"]
        j = i
        while j < len(snips) and snips[j]["start"] - t0 < WINDOW:
            j += 1
        body = " ".join(s["text"].strip() for s in snips[i:j])
        if len(body.split()) >= MIN_WORDS and not is_repetitive(body):
            # title prefix: a chunk from minute 34 rarely restates its topic
            chunks.append((int(t0), int(snips[j - 1]["end"]), f"{title}\n\n{body}"))
        if j >= len(snips):
            break
        t_back = snips[j - 1]["start"] - OVERLAP
        nxt = next((k for k in range(i, j) if snips[k]["start"] >= t_back), j)
        i = max(nxt, i + 1)
    # two windows can start in the same second (fractional starts) -> duplicate Chroma IDs; keep the first
    uniq = {}
    for c in chunks:
        uniq.setdefault(c[0], c)
    return list(uniq.values())
