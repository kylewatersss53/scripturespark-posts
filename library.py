"""Parse topic files, validate every reference against the BSB text."""
import glob, os, re, sys
import bible

HERE = os.path.dirname(os.path.abspath(__file__))


def load_topics(pattern=None):
    files = sorted(glob.glob(pattern or os.path.join(HERE, "topics", "*.txt")))
    topics, cur = [], None
    for f in files:
        for ln, line in enumerate(open(f, encoding="utf-8"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            where = f"{os.path.basename(f)}:{ln}"
            if line.startswith("@"):
                parts = [p.strip() for p in line[1:].split("|")]
                if len(parts) != 4:
                    raise SystemExit(f"{where}: header needs 4 fields: {line}")
                cur = {"id": parts[0], "subject": parts[1], "cat": parts[2], "hook": parts[3],
                       "verses": [], "chapters": [], "where": where, "tv": None, "tc": None}
                topics.append(cur)
            elif line.startswith("V "):
                for item in line[2:].split(";"):
                    item = item.strip()
                    if not item:
                        continue
                    ref, _, kw = item.partition("=")
                    cur["verses"].append((ref.strip(), kw.strip() or None, where))
            elif line.startswith("TV "):
                cur["tv"] = line[3:].strip()
            elif line.startswith("TC "):
                cur["tc"] = line[3:].strip()
            elif line.startswith("C "):
                for item in line[2:].split(";"):
                    if item.strip():
                        cur["chapters"].append((item.strip(), where))
            else:
                raise SystemExit(f"{where}: unknown line: {line}")
    return topics


def validate(topics, verbose=True):
    problems = []
    ids = set()
    for t in topics:
        if t["id"] in ids:
            problems.append(f"{t['where']}: duplicate id {t['id']}")
        ids.add(t["id"])
        seen = set()
        for ref, kw, where in t["verses"]:
            try:
                lab = bible.label(ref)
                if bible.is_chapter(ref):
                    problems.append(f"{where} [{t['id']}] verse entry is a whole chapter: {ref}")
                    continue
                txt = bible.text(ref)
            except bible.RefError as e:
                problems.append(f"{where} [{t['id']}] {e}")
                continue
            if lab in seen:
                problems.append(f"{where} [{t['id']}] duplicate verse {lab}")
            seen.add(lab)
            if kw and kw.lower() not in txt.lower():
                problems.append(f"{where} [{t['id']}] KEYWORD '{kw}' not in {lab}: {txt[:160]}")
            if len(txt.split()) > 75:
                problems.append(f"{where} [{t['id']}] LONG ({len(txt.split())}w) {lab}")
        cs = set()
        for ch, where in t["chapters"]:
            try:
                lab = bible.label(ch)
                if not bible.is_chapter(ch):
                    problems.append(f"{where} [{t['id']}] chapter entry has verses: {ch}")
            except bible.RefError as e:
                problems.append(f"{where} [{t['id']}] {e}")
                continue
            if lab in cs:
                problems.append(f"{where} [{t['id']}] duplicate chapter {lab}")
            cs.add(lab)
        if t["verses"] and len(t["verses"]) < 8:
            problems.append(f"{t['where']} [{t['id']}] only {len(t['verses'])} verses")
        if not t["verses"] and len(t["chapters"]) < 6:
            problems.append(f"{t['where']} [{t['id']}] chapter-only topic needs 6+ chapters")
        if t["chapters"] and len(t["chapters"]) < 6:
            problems.append(f"{t['where']} [{t['id']}] only {len(t['chapters'])} chapters")
    return problems


if __name__ == "__main__":
    topics = load_topics(sys.argv[1] if len(sys.argv) > 1 else None)
    probs = validate(topics)
    nv = sum(len(t["verses"]) for t in topics)
    nc = sum(len(t["chapters"]) for t in topics)
    print(f"{len(topics)} topics, {nv} verse picks, {nc} chapter picks, {len(probs)} problems")
    for p in probs:
        print(" -", p)
