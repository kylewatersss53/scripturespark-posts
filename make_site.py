"""Render the next N days of scheduled posts into site/ (served by Netlify), plus manifest.json."""
import json, os, shutil, sys, datetime as dt
import render_batch
HERE = os.path.dirname(os.path.abspath(__file__))
start_day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
days = int(sys.argv[2]) if len(sys.argv) > 2 else 5
SLOTS = [(0, "07:00"), (1, "12:00"), (2, "19:00")]
L = json.load(open(os.path.join(HERE, "build", "library.json")))
s0 = dt.date.fromisoformat(L["meta"]["start"])
site = os.path.join(HERE, "site"); shutil.rmtree(site, ignore_errors=True); os.makedirs(site)
jobs = []
for k in range(days):
    d = start_day + dt.timedelta(k); i = (d - s0).days
    for slot, hhmm in SLOTS:
        jobs.append((d, hhmm, L["schedule"][i][slot]))
tmp = os.path.join(HERE, "_render"); shutil.rmtree(tmp, ignore_errors=True)
res = {r["id"]: r for r in render_batch.render(sorted({j[2] for j in jobs}), tmp, handle="@scripturesparkapp")}
manifest = []
for d, hhmm, pid in jobs:
    r = res[pid]; key = f"{d.isoformat()}-{hhmm.replace(':', '')}"
    os.makedirs(os.path.join(site, key))
    imgs = []
    for f in r["files"][:10]:
        shutil.copy(f, os.path.join(site, key, os.path.basename(f))); imgs.append(f"{key}/{os.path.basename(f)}")
    manifest.append({"key": key, "date": d.isoformat(), "time": hhmm, "post": pid, "title": r["title"], "caption": r["caption"], "images": imgs})
json.dump(manifest, open(os.path.join(site, "manifest.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(site, "index.html"), "w").write("<!doctype html><title>Scripture Spark posts</title><p>Image host for scheduled posts.</p>")
shutil.rmtree(tmp, ignore_errors=True)
print(len(manifest), "posts ->", site)
