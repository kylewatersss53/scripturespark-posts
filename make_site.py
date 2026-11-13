"""Render the next N days of scheduled posts into site/ (published to the `images` branch), plus manifest.json.

Published slots are frozen: if PREV_SITE points at the currently published site (publish_images.sh clones the
`images` branch there), any slot key already in its manifest is copied as-is (same images, video, title,
caption) instead of re-rendered. Posts already queued in Buffer therefore never change underneath their
captions, even when topics, titles, quiz questions or the schedule are edited. Set FRESH=1 to re-render
everything, or FRESH_KEYS=key,key to re-render specific slots (only for slots not yet queued in Buffer).
"""
import json, os, shutil, sys, datetime as dt
import render_batch
from make_video import make_daily_video, make_verse_video
HERE = os.path.dirname(os.path.abspath(__file__))
start_day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
days = int(sys.argv[2]) if len(sys.argv) > 2 else 5
VERSE_LAUNCH = dt.date(2026, 11, 10)
SLOTS = [(0, "07:00"), (1, "12:00"), (5, "16:00"), (2, "19:00"), (4, "21:00")]   # (schedule index, Central time); 5 = quiz, 4 = third list (9pm verse video retired 2026-11-13: lowest views and ~2 s watch time)
L = json.load(open(os.path.join(HERE, "build", "library.json")))
s0 = dt.date.fromisoformat(L["meta"]["start"])
site = os.path.join(HERE, "site"); shutil.rmtree(site, ignore_errors=True); os.makedirs(site)

prev_dir = os.environ.get("PREV_SITE", "")
prev = {}
fresh_keys = set(k.strip() for k in os.environ.get("FRESH_KEYS", "").split(",") if k.strip())
if prev_dir and not os.environ.get("FRESH") and os.path.exists(os.path.join(prev_dir, "manifest.json")):
    for e in json.load(open(os.path.join(prev_dir, "manifest.json"), encoding="utf-8")):
        if e["key"] in fresh_keys:
            continue
        files = e["images"] + ([e["video"]] if e.get("video") else [])
        if all(os.path.exists(os.path.join(prev_dir, f)) for f in files):
            prev[e["key"]] = e

jobs = []
for k in range(days):
    d = start_day + dt.timedelta(k); i = (d - s0).days
    for slot, hhmm in SLOTS:
        jobs.append((d, hhmm, L["schedule"][i][slot], f"{d.isoformat()}-{hhmm.replace(':', '')}"))
jobs.sort(key=lambda j: (j[0], j[1]))
todo = sorted({pid for d, hhmm, pid, key in jobs if key not in prev})
tmp = os.path.join(HERE, "_render"); shutil.rmtree(tmp, ignore_errors=True)
# verse videos are a nightly series: episode number = days since launch + 1
extra = {pid: {"ep": (d - VERSE_LAUNCH).days + 1} for d, hhmm, pid, key in jobs if pid.startswith("S:") and key not in prev}
res = {r["id"]: r for r in render_batch.render(todo, tmp, handle="@scripturesparkapp", extra=extra)} if todo else {}
manifest, kept = [], 0
for d, hhmm, pid, key in jobs:
    if key in prev:   # already published: keep it exactly as it is
        shutil.copytree(os.path.join(prev_dir, key), os.path.join(site, key))
        manifest.append(prev[key]); kept += 1
        continue
    r = res[pid]
    os.makedirs(os.path.join(site, key))
    imgs = []
    for f in r["files"][:10]:
        shutil.copy(f, os.path.join(site, key, os.path.basename(f))); imgs.append(f"{key}/{os.path.basename(f)}")
    entry = {"key": key, "date": d.isoformat(), "time": hhmm, "post": pid, "title": r["title"], "caption": r["caption"], "images": imgs}
    if r.get("tall"):   # daily word -> 12 s full-screen video with birdsong (post this instead of the images)
        make_daily_video(r["tall"], os.path.join(site, key, "video.mp4"))
        entry["video"] = f"{key}/video.mp4"
    if r.get("verse_video"):   # 9pm single verse -> short verse video (hook, then the verse phrase by phrase, worship music)
        make_verse_video(r["verse_video"], os.path.join(site, key, "video.mp4"), key=pid)
        entry["video"] = f"{key}/video.mp4"
    manifest.append(entry)
json.dump(manifest, open(os.path.join(site, "manifest.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(site, "index.html"), "w").write("<!doctype html><title>Scripture Spark posts</title><p>Image host for scheduled posts.</p>")
shutil.rmtree(tmp, ignore_errors=True)
print(len(manifest), "posts ->", site, f"({kept} already published and kept, {len(manifest) - kept} rendered)")
