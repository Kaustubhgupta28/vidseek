"""Golden-set retrieval eval.
Run:  python -m vidseek.evaluate [eval/golden.json]      (JUDGE=1 -> also LLM-judge relevance)"""
import json, os, re, sys, time
from vidseek.answer import ask_core, get_llm, retrieve
from vidseek.config import LLM_MODEL, MAX_DISTANCE, ROOT

K = 5
JUDGE = os.getenv("JUDGE") == "1"


def run(path):
    gold = [g for g in json.load(open(path, encoding="utf-8")) if not str(g.get("q", "")).startswith("_")]
    ret, ref, rr, vid_hit, judged = [], [], [], 0, []
    for g in gold:
        if g.get("expect_refusal"):
            res = ask_core(g["q"], K)
            time.sleep(1.5)
            ok = not res["grounded"]
            ref.append(ok)
            print(f"[refusal {'OK ' if ok else 'MISS'}] top_dist={res['top_distance']}  {g['q']}")
            continue
        hits = retrieve(g["q"], K)
        time.sleep(1.5)
        ids = set(g.get("expect_video_ids") or [g["expect_video_id"]])
        around = g.get("expect_around_sec")
        tol = int(g.get("tolerance_sec", 120))
        rank = None
        for i, (_, m, _) in enumerate(hits, 1):
            if m["vid"] in ids and (around is None or (m["start"] <= around + tol and m["end"] >= around - tol)):
                rank = i
                break
        vid_hit += any(m["vid"] in ids for _, m, _ in hits)
        ret.append(rank is not None)
        rr.append(1 / rank if rank else 0.0)
        if JUDGE:
            ctx = "\n\n".join(f"[{i+1}] {d.split(chr(10)*2, 1)[-1][:700]}" for i, (d, _, _) in enumerate(hits))
            out = get_llm().chat.completions.create(model=LLM_MODEL, temperature=0, messages=[
                {"role": "system", "content": "You judge retrieval quality. Given a question and numbered lecture excerpts, reply "
                 "with ONLY the number of the first excerpt that clearly contains the answer, or 0 if none does."},
                {"role": "user", "content": f"QUESTION: {g['q']}\n\n{ctx}"}])
            mm = re.search(r"\d+", out.choices[0].message.content or "0")
            n = int(mm.group()) if mm else 0
            judged.append(n if 1 <= n <= len(hits) else None)
            print(f"      judge: sahi chunk rank = {judged[-1]}")
            time.sleep(1.5)
        print(f"[retrieval {'OK ' if rank else 'MISS'}] rank={rank} top_dist={round(hits[0][2], 4)}  {g['q']}")
        if not rank:
            for _, m, d in hits[:3]:
                print(f"      mila: {m['title'][:60]} @ {m['start']}s  (id={m['vid']}, dist={round(d, 3)})")
    print("\n===== RESULTS =====")
    if ret:
        print(f"Recall@{K}      : {sum(ret)/len(ret):.2f}")
        print(f"MRR           : {sum(rr)/len(rr):.2f}")
        print(f"Video hit rate: {vid_hit/len(ret):.2f}")
    if judged:
        print(f"Answerable@{K} (judge): {sum(j is not None for j in judged)/len(judged):.2f}")
        print(f"MRR (judge)           : {sum(1/j for j in judged if j)/len(judged):.2f}")
    if ref:
        print(f"Refusal rate  : {sum(ref)/len(ref):.2f}")
    print(f"MAX_DISTANCE  : {MAX_DISTANCE}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "eval" / "golden.json"))
