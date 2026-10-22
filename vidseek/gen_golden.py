"""Auto-generate a golden set from indexed chunks.
Run: python -m vidseek.gen_golden 30   -> eval/golden_auto.json (+ refusal questions from eval/golden.json)"""
import json, random, sys, time
from vidseek import index
from vidseek.answer import _chat
from vidseek.config import ROOT

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
random.seed(7)
data = index.all_chunks()
items = [(d, m) for d, m in zip(data["documents"], data["metadatas"]) if len(d.split()) > 60]
random.shuffle(items)

out = []
for d, m in items:
    if len(out) >= N:
        break
    lang = "Roman Hinglish (Hindi written in English letters)" if len(out) % 2 == 0 else "English"
    try:
        q = _chat(f"You write search questions. Given a lecture transcript excerpt, write ONE short, self-contained question a "
                  f"student would ask whose answer is explained in this excerpt. Write it in {lang}. Do not copy sentences from "
                  f"the excerpt. If the excerpt is filler or has no clear concept, reply exactly SKIP. Output only the question.",
                  d.split("\n\n", 1)[-1][:1500], 0.7)
    except Exception as e:
        print("LLM error:", str(e)[:80]); time.sleep(5); continue
    if not q or q.upper().startswith("SKIP") or len(q) > 200:
        continue
    out.append({"q": q, "expect_video_id": m["vid"], "expect_around_sec": m["start"] + 20, "tolerance_sec": 45})
    print(len(out), q)
    time.sleep(1.5)

try:
    out += [g for g in json.load(open(ROOT / "eval" / "golden.json", encoding="utf-8")) if g.get("expect_refusal")]
except Exception:
    pass
json.dump(out, open(ROOT / "eval" / "golden_auto.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nSaved eval/golden_auto.json ({len(out)} entries)")
