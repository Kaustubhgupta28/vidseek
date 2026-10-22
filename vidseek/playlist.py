"""Playlist/video link -> [{id, title}]"""
import yt_dlp


def list_videos(url):
    opts = {"quiet": True, "extract_flat": "in_playlist", "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=False)
    items = info.get("entries") or [info]
    return [{"id": v["id"], "title": v.get("title") or v["id"]} for v in items if v]
