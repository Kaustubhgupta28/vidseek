"""Background ingest job with live progress (polled by the UI)."""
import threading, time
from vidseek import index
from vidseek.chunk import make_chunks
from vidseek.config import MAX_PER_ADD
from vidseek.embed import embed_passages
from vidseek.playlist import list_videos
from vidseek.transcribe import get_transcript

JOB = {"running": False, "total": 0, "done": 0, "failed": 0, "current": "", "stopped": None, "last_error": None}


def index_video(v):
    chunks = make_chunks(get_transcript(v["id"]), v["title"])
    if not chunks:
        raise ValueError("no usable transcript")
    index.add_chunks(v, chunks, embed_passages([c[2] for c in chunks]))


def run_ingest(url):
    try:
        vids = list_videos(url)
        have = index.indexed_ids()
        JOB.update(total=len(vids), done=sum(v["id"] in have for v in vids))
        for v in [v for v in vids if v["id"] not in have][:MAX_PER_ADD]:
            JOB["current"] = v["title"]
            t0 = time.time()
            print(f"[{JOB['done']}/{JOB['total']}] {v['title']}", flush=True)
            try:
                index_video(v)
                JOB["done"] += 1
                print(f"   done in {time.time()-t0:.0f}s", flush=True)
            except Exception as e:
                name = type(e).__name__
                JOB["failed"] += 1
                JOB["last_error"] = f"{v['title']}: {name}: {str(e)[:80]}"
                if "Blocked" in name or "429" in str(e) or "Sign in" in str(e):
                    JOB["stopped"] = "YouTube ne block kiya hai. Thodi der baad ya hotspot/VPN se try karo."
                    break
    except Exception as e:
        JOB["stopped"] = f"{type(e).__name__}: {str(e)[:100]}"
    finally:
        JOB.update(running=False, current="")


def start(url):
    """-> False if a job is already running."""
    if JOB["running"]:
        return False
    JOB.update(running=True, total=0, done=0, failed=0, stopped=None, last_error=None,
               current="Playlist ki list nikal raha hai...")
    threading.Thread(target=run_ingest, args=(url,), daemon=True).start()
    return True
