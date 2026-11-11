"""Render posts to JPEG files with headless Chrome, using the exact same engine as the app."""
import base64, http.server, json, os, sys, threading, datetime as dt, functools
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")

def serve():
    import shutil
    shutil.copy(os.path.join(HERE, "build", "library.json"), os.path.join(WEB, "library.json"))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=WEB)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def render(post_ids, outdir, handle=None, extra=None):
    """extra: optional {post_id: {opts}} merged into the render options for that post (e.g. verse video episode number)."""
    httpd = serve()
    port = httpd.server_address[1]
    results = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        page = b.new_page()
        page.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
        page.goto(f"http://127.0.0.1:{port}/harness.html")
        page.evaluate("window.ready")
        for pid in post_ids:
            r = page.evaluate("([id, o]) => window.renderPost(id, o)", [pid, {"handle": handle} if handle else {}])
            safe = pid.replace(":", "-")
            d = os.path.join(outdir, safe) if len(post_ids) > 1 else outdir
            os.makedirs(d, exist_ok=True)
            files = []
            for i, data in enumerate(r["imgs"], 1):
                fn = os.path.join(d, f"{i:02d}.jpg")
                with open(fn, "wb") as f:
                    f.write(base64.b64decode(data.split(",", 1)[1]))
                files.append(fn)
            if pid.startswith("D:"):   # full-screen frame for the daily video
                t = page.evaluate("([id, o]) => window.renderTall(id, o)", [pid, {"handle": handle} if handle else {}])
                fn = os.path.join(d, "tall.jpg")
                with open(fn, "wb") as f:
                    f.write(base64.b64decode(t.split(",", 1)[1]))
                r["tall"] = fn
            if pid.startswith("S:"):   # layers for the 9pm verse video (see engine renderVerseVideo)
                vo = dict({"handle": handle} if handle else {}, **((extra or {}).get(pid, {})))
                vv = page.evaluate("([id, o]) => window.renderVerseVideo(id, o)", [pid, vo])
                bg = os.path.join(d, "vv_bg.jpg")
                with open(bg, "wb") as f:
                    f.write(base64.b64decode(vv["bg"].split(",", 1)[1]))
                layers = []
                for i, L in enumerate(vv["layers"]):
                    fn = os.path.join(d, f"vv_{i:02d}.png")
                    with open(fn, "wb") as f:
                        f.write(base64.b64decode(L.pop("img").split(",", 1)[1]))
                    layers.append(dict(L, file=fn))
                r["verse_video"] = {"bg": bg, "layers": layers, "total": vv["total"]}
            r.pop("imgs"); r["files"] = files; r["dir"] = d
            results.append(r)
        b.close()
    httpd.shutdown()
    return results

if __name__ == "__main__":
    out = sys.argv[1]
    ids = sys.argv[2:]
    for r in render(ids, out):
        print(r["id"], len(r["files"]), "slides ->", r["dir"])
