"""Pre-render N days of scheduled posts into dated folders with captions, then zip."""
import json, os, re, shutil, sys, datetime as dt, zipfile
import render_batch

HERE = os.path.dirname(os.path.abspath(__file__))
days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
out = sys.argv[2]
L = json.load(open(os.path.join(HERE, "build", "library.json")))
start = dt.date.fromisoformat(L["meta"]["start"])
by = {p["id"]: p for p in L["posts"]}
tmp = os.path.join(out, "_tmp"); shutil.rmtree(tmp, ignore_errors=True)
ids = [L["schedule"][i][k] for i in range(days) for k in (0, 1, 2)]
res = {r["id"]: r for r in render_batch.render(ids, tmp, handle="@scripturesparkapp")}
root = os.path.join(out, "Scripture Posts")
shutil.rmtree(root, ignore_errors=True)
index = []
for i in range(days):
    d = start + dt.timedelta(i)
    dname = f"{d.isoformat()} {d.strftime('%a')}"
    for slot, pid in zip(("1", "2", "3"), [L["schedule"][i][k] for k in (0, 1, 2)]):
        r = res[pid]
        slug = re.sub(r"[^A-Za-z0-9]+", " ", r["title"]).strip()[:48]
        pdir = os.path.join(root, dname, f"Post {slot} - {slug}")
        os.makedirs(pdir, exist_ok=True)
        for f in r["files"]:
            shutil.copy(f, os.path.join(pdir, os.path.basename(f)))
        title = r["title"] if len(r["title"]) <= 90 else r["title"][:89] + "…"
        open(os.path.join(pdir, "caption.txt"), "w", encoding="utf-8").write(f"TITLE\n{title}\n\nCAPTION\n{r['caption']}\n")
        index.append(f"{dname}  Post {slot}: {r['title']}  ({len(r['files'])} slides)")
open(os.path.join(root, "SCHEDULE.txt"), "w", encoding="utf-8").write("\n".join(index) + "\n")
shutil.rmtree(tmp, ignore_errors=True)
zp = os.path.join(out, f"Scripture Posts {start.isoformat()} to {(start + dt.timedelta(days - 1)).isoformat()}.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            full = os.path.join(dp, f); z.write(full, os.path.relpath(full, out))
print(zp, os.path.getsize(zp) // (1024 * 1024), "MB")
print("\n".join(index))
