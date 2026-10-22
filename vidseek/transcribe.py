"""Video -> timestamped segments [{text,start,end}]. Cache -> captions -> Whisper(audio)."""
import glob, json, os, shutil, tempfile
import yt_dlp
from faster_whisper import WhisperModel
from youtube_transcript_api import YouTubeTranscriptApi
from vidseek.config import TRANSCRIBE_MODE, TRANSCRIPT_DIR, WHISPER_LANG, WHISPER_MODEL

_whisper = None


def get_whisper():
    global _whisper
    if _whisper is None:
        _whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper


def download_audio(vid, outdir):
    opts = {"format": "bestaudio/best", "outtmpl": f"{outdir}/%(id)s.%(ext)s", "quiet": True, "noplaylist": True}
    if os.getenv("YT_COOKIES_FILE"):
        opts["cookiefile"] = os.getenv("YT_COOKIES_FILE")
    elif os.getenv("YT_COOKIES_BROWSER"):
        opts["cookiesfrombrowser"] = (os.getenv("YT_COOKIES_BROWSER"),)
    with yt_dlp.YoutubeDL(opts) as y:
        y.download([f"https://www.youtube.com/watch?v={vid}"])
    return glob.glob(f"{outdir}/{vid}.*")[0]


def get_captions(vid):
    api = YouTubeTranscriptApi()
    try:
        tr = api.fetch(vid, languages=["hi", "en", "en-IN", "hi-Latn"])
    except Exception:
        tr = next(iter(api.list(vid))).fetch()
    return [{"text": x.text, "start": x.start, "end": x.start + x.duration} for x in tr]


def get_whisper_transcript(vid):
    tmp = tempfile.mkdtemp()
    try:
        path = download_audio(vid, tmp)
        segs, _ = get_whisper().transcribe(path, language=WHISPER_LANG, vad_filter=True, beam_size=1)
        return [{"text": g.text.strip(), "start": g.start, "end": g.end} for g in segs]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def get_transcript(vid):
    cache = TRANSCRIPT_DIR / f"{vid}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out = None
    if TRANSCRIBE_MODE != "whisper":
        try:
            out = get_captions(vid)
            print(f"   captions mile ({len(out)} segments)", flush=True)
        except Exception as e:
            print(f"   captions nahi mile ({type(e).__name__}), Whisper chalega...", flush=True)
    if not out:
        out = get_whisper_transcript(vid)
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
