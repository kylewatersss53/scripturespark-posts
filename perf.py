"""TikTok performance tracking and schedule tuning for @scripturesparkapp.

Buffer reports per-post TikTok stats (views, likes, comments, shares, reach, watch time;
not saves). The nightly task saves recently sent posts to a JSON file and runs:

    python3 perf.py ingest posts.json   # match posts to schedule slots, update analytics/performance.csv
    python3 perf.py report              # write analytics/REPORT.md (what's working, by format/topic/time)
    python3 perf.py tune                # weekly: add a tuning step to analytics/tuning.json

posts.json: a list of posts (or Buffer list_posts output) with at least
  {"id", "dueAt", "text", "metrics": [{"type": "views", "value": 123}, ...] or {"views": 123, ...}}

Tuning nudges the schedule toward what performs, with guardrails so the feed stays varied:
  * only after MIN_POSTS scored posts over at least MIN_DAYS days
  * weights are shrunk toward 1 for small samples and clamped (no format or topic disappears)
  * a tuning step only affects dates >= today + 6, so nothing already queued or rendered changes
gen.py reads analytics/tuning.json when it builds the schedule.
"""
import csv, datetime as dt, json, math, os, re, statistics, subprocess, sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(HERE, "analytics")
CSV = os.path.join(ADIR, "performance.csv")
REPORT = os.path.join(ADIR, "REPORT.md")
TUNING = os.path.join(ADIR, "tuning.json")
CT = ZoneInfo("America/Chicago")
SLOT_BY_TIME = {"07:00": 0, "12:00": 1, "16:00": 5, "19:00": 2, "21:00": 4}
MIN_POSTS, MIN_DAYS = 10, 3
LIST_TYPES = ["V", "C", "P", "KC", "KV"]
QUIZ_STYLES = ["T", "F", "W", "B"]
TYPE_NAME = {"D": "Daily word video", "V": "10 verses", "C": "10 chapters", "P": "7-day plan", "KC": "Chapter list stack",
             "KV": "Verse list stack", "S": "Verse video (9pm)", "Q": "Bible quiz"}
STYLE_NAME = {"T": "Bible Trivia", "F": "Finish the Verse", "W": "Who Said It?", "B": "Guess the Book"}
FIELDS = ["buffer_id", "key", "date", "time", "weekday", "post", "type", "style", "topics", "category", "title", "title_style",
          "views", "likes", "comments", "shares", "reach", "eng_rate", "avg_watch_sec", "metrics_updated", "ingested"]
METRIC_MAP = {"views": "views", "reactions": "likes", "comments": "comments", "shares": "shares", "reach": "reach",
              "engagementRate": "eng_rate", "averageTimeWatched": "avg_watch_sec"}


def library():
    path = os.path.join(HERE, "build", "library.json")
    if not os.path.exists(path):
        subprocess.run([sys.executable, os.path.join(HERE, "gen.py")], check=True, stdout=subprocess.DEVNULL)
    return json.load(open(path, encoding="utf-8"))


def title_style(post):
    ti = post.get("ti", "")
    if post["t"] == "Q":
        return "quiz:" + post["f"]
    if post["t"] == "D":
        return "daily"
    if " When " in ti or ti.startswith("When "):
        return "when-you"
    if ti.startswith("10 "):
        return "10-number"
    if " About " in ti or ti.startswith("What the Bible Says"):
        return "about"
    return "other"


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("’", "'")).strip()


def _nodes(data):
    """Accepts a list of posts, Buffer list_posts output ({"edges": [{"node": ...}]}), or a list of those."""
    if isinstance(data, list):
        return [n for x in data for n in _nodes(x)]
    if isinstance(data, dict):
        if "edges" in data:
            return [e.get("node", e) for e in data["edges"]]
        if "posts" in data:
            return _nodes(data["posts"])
        if "id" in data:
            return [data]
    return []


def _metrics(node):
    m = node.get("metrics") or {}
    if isinstance(m, list):
        m = {x.get("type"): x.get("value") for x in m}
    out = {}
    for k, col in METRIC_MAP.items():
        v = m.get(k, m.get(col))
        out[col] = "" if v is None else v
    return out


def match(node, L, byid):
    """Find the schedule post for a Buffer post: by slot time first, then by title on that date."""
    when = node.get("dueAt") or node.get("sentAt")
    if not when:
        return None, None
    t = dt.datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(CT)
    d, hhmm = t.date(), t.strftime("%H:%M")
    start = dt.date.fromisoformat(L["meta"]["start"])
    i = (d - start).days
    if not 0 <= i < len(L["schedule"]):
        return None, None
    first = _norm((node.get("text") or "").split("\n")[0])
    day = L["schedule"][i]
    cands = []
    if hhmm in SLOT_BY_TIME and SLOT_BY_TIME[hhmm] < len(day):
        cands.append((day[SLOT_BY_TIME[hhmm]], hhmm))
    cands += [(pid, hhmm) for pid in day]
    for pid, tm in cands:
        for t in (byid[pid].get("vh"), byid[pid].get("ti")):
            if t and first.startswith(_norm(t)):
                return byid[pid], f"{d.isoformat()}-{tm.replace(':', '')}"
    # published slots are frozen, so after a content edit the post may no longer be in that day's schedule
    if hhmm in SLOT_BY_TIME and first:
        for p in L["posts"]:
            for t in (p.get("vh"), p.get("ti")):
                if t and len(_norm(t)) > 12 and first.startswith(_norm(t)) and (p["t"] != "D" or p["date"] == d.isoformat()):
                    return p, f"{d.isoformat()}-{hhmm.replace(':', '')}"
    return None, None


def load_rows():
    if not os.path.exists(CSV):
        return {}
    with open(CSV, newline="", encoding="utf-8") as f:
        return {r["buffer_id"]: r for r in csv.DictReader(f)}


def save_rows(rows):
    os.makedirs(ADIR, exist_ok=True)
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in sorted(rows.values(), key=lambda r: (r["date"], r["time"])):
            w.writerow({k: r.get(k, "") for k in FIELDS})


def ingest(path):
    L = library()
    byid = {p["id"]: p for p in L["posts"]}
    rows = load_rows()
    added = updated = skipped = 0
    for node in _nodes(json.load(open(path, encoding="utf-8"))):
        post, key = match(node, L, byid)
        if not post:
            skipped += 1
            continue
        ks = post.get("ks") or ([post["k"]] if post.get("k") else [])
        cat = L["topics"][ks[0]]["cat"] if len(ks) == 1 and ks[0] in L["topics"] else (post.get("cat") or "")
        d, tm = key[:10], key[11:13] + ":" + key[13:]
        row = {"buffer_id": node["id"], "key": key, "date": d, "time": tm,
               "weekday": dt.date.fromisoformat(d).strftime("%a"), "post": post["id"], "type": post["t"],
               "style": post.get("f", ""), "topics": " ".join(ks), "category": cat, "title": post.get("vh") or post.get("ti", ""),
               "title_style": title_style(post), **_metrics(node), "metrics_updated": node.get("metricsUpdatedAt") or "",
               "ingested": dt.datetime.now(CT).isoformat(timespec="minutes")}
        if node["id"] in rows:
            updated += 1
        else:
            added += 1
        rows[node["id"]] = row
    save_rows(rows)
    print(f"ingest: {added} new, {updated} updated, {skipped} not from the schedule; {len(rows)} posts tracked")


# ---------------- scoring ----------------

def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def scored(rows):
    """Posts with real stats, each with a 0-1 score. Views come first (the owner's goal: the most eyeballs on the
    Scripture Spark brand): 70% views, 12% share rate, 10% comment rate, 8% like rate. Shares and comments are
    kept because they are what earns the next round of views. Percentile ranks within this account's own posts."""
    rs = [dict(r) for r in rows.values() if _f(r.get("views")) > 0]
    if not rs:
        return []
    def pct(vals):
        order = sorted(vals)
        return [(sum(1 for x in order if x < v) + 0.5 * sum(1 for x in order if x == v)) / len(order) for v in vals]
    v = [_f(r["views"]) for r in rs]
    like = [_f(r["likes"]) / max(1, _f(r["views"])) for r in rs]
    com = [_f(r["comments"]) / max(1, _f(r["views"])) for r in rs]
    sh = [_f(r["shares"]) / max(1, _f(r["views"])) for r in rs]
    for r, a, b, c, d in zip(rs, pct(v), pct(like), pct(com), pct(sh)):
        r["score"] = 0.70 * a + 0.08 * b + 0.10 * c + 0.12 * d
    return rs


def groups(rs, keyf):
    g = {}
    for r in rs:
        for k in keyf(r):
            if k:
                g.setdefault(k, []).append(r)
    return g


def summarize(items):
    v = [_f(r["views"]) for r in items]
    tot = max(1, sum(v))
    w = [_f(r.get("avg_watch_sec")) for r in items if _f(r.get("avg_watch_sec")) > 0]
    return {"n": len(items), "median_views": statistics.median(v), "avg_watch": statistics.mean(w) if w else None,
            "like_pct": 100 * sum(_f(r["likes"]) for r in items) / tot,
            "comments_per_1k": 1000 * sum(_f(r["comments"]) for r in items) / tot,
            "shares_per_1k": 1000 * sum(_f(r["shares"]) for r in items) / tot,
            "score": statistics.mean(r["score"] for r in items)}


def table(title, g, names=None, min_n=1):
    lines = [f"### {title}", "", "| | posts | median views | likes % | comments / 1k views | shares / 1k views | avg watch (videos) | score |", "|---|---|---|---|---|---|---|---|"]
    rows = sorted(((k, summarize(v)) for k, v in g.items() if len(v) >= min_n), key=lambda x: -x[1]["score"])
    for k, s in rows:
        aw = f"{s['avg_watch']:.1f}s" if s["avg_watch"] else "–"
        lines.append(f"| {(names or {}).get(k, k)} | {s['n']} | {s['median_views']:,.0f} | {s['like_pct']:.1f} | {s['comments_per_1k']:.1f} | {s['shares_per_1k']:.1f} | {aw} | {s['score']:.2f} |")
    return "\n".join(lines) + "\n"


def report():
    rows = load_rows()
    rs = scored(rows)
    now = dt.datetime.now(CT)
    out = [f"# TikTok performance report", "", f"Updated {now:%Y-%m-%d %H:%M} Central. {len(rows)} posts tracked, {len(rs)} with stats so far.",
           "Score = 70% views, 12% share rate, 10% comment rate, 8% like rate, each ranked against this account's own posts (0 to 1). "
           "Buffer does not report saves; check TikTok Studio for those.", ""]
    if not rs:
        out.append("No stats yet. Buffer refreshes TikTok numbers about once a day.")
    else:
        days = len({r["date"] for r in rs})
        if len(rs) < MIN_POSTS or days < MIN_DAYS:
            out += [f"**Early data:** {len(rs)} posts over {days} days. Tuning starts at {MIN_POSTS} posts over {MIN_DAYS}+ days; treat differences below as noise for now.", ""]
        out.append(table("By format", groups(rs, lambda r: [r["type"]]), TYPE_NAME))
        out.append(table("By time slot", groups(rs, lambda r: [r["time"]])))
        out.append(table("Quiz styles", groups([r for r in rs if r["type"] == "Q"], lambda r: [r["style"]]), STYLE_NAME))
        out.append(table("List title styles", groups([r for r in rs if r["type"] in LIST_TYPES], lambda r: [r["title_style"]])))
        out.append(table("Topic categories", groups([r for r in rs if r["category"]], lambda r: [r["category"]])))
        out.append(table("Topics (2+ posts)", groups([r for r in rs if r["type"] in ("V", "C", "P")], lambda r: r["topics"].split()), min_n=2))
        out.append(table("Weekday", groups(rs, lambda r: [r["weekday"]])))
        dv = [r for r in rs if r["type"] == "D" and _f(r.get("avg_watch_sec")) > 0]
        if dv:
            out += [f"Daily word videos (12 s): people watch {100 * statistics.mean(_f(r['avg_watch_sec']) for r in dv) / 12:.0f}% of the video on average (over 100% means rewatches).", ""]
        best = sorted(rs, key=lambda r: -r["score"])
        fmt = lambda r: f"- {r['date']} {r['time']} · {TYPE_NAME.get(r['type'], r['type'])} · “{r['title']}” · {int(_f(r['views'])):,} views, {int(_f(r['likes']))} likes, {int(_f(r['comments']))} comments, {int(_f(r['shares']))} shares"
        out += ["### Top posts", ""] + [fmt(r) for r in best[:5]] + ["", "### Weakest posts", ""] + [fmt(r) for r in best[-5:][::-1]] + [""]
    hist = load_tuning()
    if hist:
        last = hist[-1]
        out += ["### Current tuning", "", f"Applies from {last['effective_from']} (made {last['made']} from {last['posts']} posts).", "",
                "List formats: " + ", ".join(f"{TYPE_NAME[k]} ×{v:.2f}" for k, v in last.get("list_types", {}).items()),
                "", "Quiz styles: " + ", ".join(f"{STYLE_NAME[k]} ×{v:.2f}" for k, v in last.get("quiz_styles", {}).items()), ""]
        if last.get("topics"):
            top = sorted(last["topics"].items(), key=lambda x: -x[1])
            out += ["Topics favored: " + ", ".join(f"{k} ×{v:.2f}" for k, v in top[:8] if v > 1.0),
                    "", "Topics de-emphasized: " + ", ".join(f"{k} ×{v:.2f}" for k, v in top[::-1][:8] if v < 1.0), ""]
    os.makedirs(ADIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out[:4]))
    print("wrote", REPORT)


# ---------------- tuning ----------------

def load_tuning():
    if not os.path.exists(TUNING):
        return []
    return sorted(json.load(open(TUNING, encoding="utf-8")).get("history", []), key=lambda t: t["effective_from"])


def _weights(g, overall, k, lo, hi):
    """group mean score relative to the overall mean, shrunk toward 1 for small samples, clamped."""
    out = {}
    for key, items in g.items():
        raw = statistics.mean(r["score"] for r in items) / overall if overall else 1.0
        w = 1 + (raw - 1) * len(items) / (len(items) + k)
        out[key] = round(min(hi, max(lo, w)), 3)
    return out


def tune(today=None):
    """Nightly: kill what's losing, lean into what's winning.
    Each group's weight = its mean score vs. the overall mean, shrunk only lightly for small samples (k=2),
    clamped wide (formats/quiz styles 0.15-3.0, topics 0.3-2.5): a clear loser drops to almost never,
    a clear winner shows up up to 3x as often. Groups with no new data keep their previous weight, so a
    killed format stays killed until it is deliberately retested. Applies from today + 3 (the publish
    window is 3 days, so nothing already published or queued changes)."""
    rs = scored(load_rows())
    days = len({r["date"] for r in rs})
    if len(rs) < MIN_POSTS or days < MIN_DAYS:
        print(f"tune: not enough data yet ({len(rs)} posts over {days} days; need {MIN_POSTS} over {MIN_DAYS}). No change.")
        return
    today = today or dt.datetime.now(CT).date()
    eff = (today + dt.timedelta(3)).isoformat()
    prev = (load_tuning() or [{}])[-1]
    lists = [r for r in rs if r["type"] in LIST_TYPES]
    quizzes = [r for r in rs if r["type"] == "Q"]
    step = {"effective_from": eff, "made": today.isoformat(), "posts": len(rs), "by": "perf.py tune (nightly)"}
    for k in ("no_weekday_pins",):
        if k in prev:
            step[k] = prev[k]
    hand = next((h for h in reversed(load_tuning()) if str(h.get("by", "")).startswith("hand") and h["effective_from"] < eff), {})
    def merge(name, new):
        """Groups without new data keep their previous weight. A hand-made kill or boost stays in force
        while the data points the same way (the stronger of the two wins); the data overrides it only
        when it points the other way."""
        out = dict(prev.get(name, {}))
        for k, w in new.items():
            h = hand.get(name, {}).get(k)
            if h is not None and (h - 1) * (w - 1) > 0:
                w = min(h, w) if w < 1 else max(h, w)
            out[k] = w
        return out
    if lists:
        m = statistics.mean(r["score"] for r in lists)
        step["list_types"] = merge("list_types", {t: w for t, w in _weights(groups(lists, lambda r: [r["type"]]), m, 2, 0.15, 3.0).items() if t in LIST_TYPES})
        single = [r for r in lists if r["type"] in ("V", "C", "P")]
        step["topics"] = merge("topics", _weights(groups(single, lambda r: r["topics"].split()), m, 1, 0.3, 2.5))
        step["categories"] = merge("categories", _weights(groups([r for r in single if r["category"]], lambda r: [r["category"]]), m, 3, 0.6, 1.6))
    if quizzes:
        m = statistics.mean(r["score"] for r in quizzes)
        step["quiz_styles"] = merge("quiz_styles", {s: w for s, w in _weights(groups(quizzes, lambda r: [r["style"]]), m, 1, 0.15, 3.0).items() if s in QUIZ_STYLES})
    hist = [h for h in load_tuning() if h["effective_from"] < eff]   # steps that may already be live stay as they are
    hist.append(step)
    os.makedirs(ADIR, exist_ok=True)
    json.dump({"note": "Written by perf.py tune (nightly) and by hand (see analytics/CHANGELOG.md); read by gen.py. Each step applies from effective_from until the next one.",
               "history": hist}, open(TUNING, "w", encoding="utf-8"), indent=1)
    print(f"tune: new step from {eff} based on {len(rs)} posts: lists {step.get('list_types')}, quiz {step.get('quiz_styles')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "ingest":
        ingest(sys.argv[2])
    elif cmd == "report":
        report()
    elif cmd == "tune":
        tune(dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        raise SystemExit(__doc__)
