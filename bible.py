"""Bible text lookup + reference parsing/validation (Berean Standard Bible, public domain)."""
import json, re, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "data", "BSB.json")

ROMAN = {"I ": "1 ", "II ": "2 ", "III ": "3 "}

def _norm_book(name):
    for r, a in sorted(ROMAN.items(), key=lambda x: -len(x[0])):
        if name.startswith(r):
            name = a + name[len(r):]
            break
    if name == "Revelation of John":
        name = "Revelation"
    return name

_d = json.load(open(_SRC))
BOOKS = {}       # canonical name -> {chapter: {verse: text}}
ORDER = []
for b in _d["books"]:
    nm = _norm_book(b["name"])
    ORDER.append(nm)
    BOOKS[nm] = {c["chapter"]: {v["verse"]: v["text"].strip() for v in c["verses"]} for c in b["chapters"]}

ALIASES = {"psalm": "Psalms", "psalms": "Psalms", "song of songs": "Song of Solomon",
           "song of solomon": "Song of Solomon", "revelation": "Revelation"}
for nm in ORDER:
    ALIASES[nm.lower()] = nm

DISPLAY = {"Psalms": "Psalm", "Song of Solomon": "Song of Solomon"}

REF_RE = re.compile(r"^\s*((?:[123]\s)?[A-Za-z][A-Za-z ]*?)\s+(\d+)(?::(\d+)(?:\s*[-–]\s*(?:(\d+):)?(\d+))?)?\s*$")

class RefError(ValueError):
    pass

def parse(ref):
    m = REF_RE.match(ref)
    if not m:
        raise RefError(f"Unparseable reference: {ref!r}")
    book_raw, ch, v1, ch2, v2 = m.groups()
    book = ALIASES.get(book_raw.strip().lower())
    if not book:
        raise RefError(f"Unknown book in {ref!r}")
    ch = int(ch)
    if ch not in BOOKS[book]:
        raise RefError(f"{book} has no chapter {ch} ({ref!r})")
    if v1 is None:
        return book, ch, None, None, None
    v1 = int(v1)
    ch2 = int(ch2) if ch2 else ch
    v2 = int(v2) if v2 else v1
    if v1 not in BOOKS[book][ch]:
        raise RefError(f"{book} {ch} has no verse {v1} ({ref!r})")
    if ch2 not in BOOKS[book] or v2 not in BOOKS[book][ch2]:
        raise RefError(f"End verse missing in {ref!r}")
    if (ch2, v2) < (ch, v1):
        raise RefError(f"Backwards range {ref!r}")
    return book, ch, v1, ch2, v2

def label(ref):
    """Canonical display label, e.g. 'Psalm 23:1-4'."""
    book, ch, v1, ch2, v2 = parse(ref)
    b = DISPLAY.get(book, book)
    if v1 is None:
        return f"{b} {ch}"
    if (ch2, v2) == (ch, v1):
        return f"{b} {ch}:{v1}"
    if ch2 == ch:
        return f"{b} {ch}:{v1}-{v2}"
    return f"{b} {ch}:{v1}-{ch2}:{v2}"

def text(ref):
    book, ch, v1, ch2, v2 = parse(ref)
    if v1 is None:
        raise RefError("Whole-chapter reference has no single text")
    out = []
    c, v = ch, v1
    while True:
        out.append(BOOKS[book][c][v])
        if (c, v) == (ch2, v2):
            break
        if v + 1 in BOOKS[book][c]:
            v += 1
        else:
            c, v = c + 1, 1
    return " ".join(out)

def is_chapter(ref):
    return parse(ref)[2] is None

if __name__ == "__main__":
    for r in ["John 3:16", "Philippians 4:6-7", "Psalm 23", "1 Peter 5:7", "Isaiah 41:10", "Song of Songs 2", "Matthew 11:28-30", "Romans 8:38-39"]:
        print(label(r), "=>", text(r) if not is_chapter(r) else f"[chapter, {len(BOOKS[parse(r)[0]][parse(r)[1]])} verses]")

# ---------- display cleanup ----------
_TITLE_START = ("For the choirmaster", "For the ", "A Psalm", "A psalm", "A song", "A Song", "A Maskil", "A Miktam", "A prayer",
                "A Prayer", "A Shiggaion", "Of David", "Of Solomon", "Of Asaph", "Of the sons", "Of Moses", "To the tune",
                "According to", "With stringed", "With flutes", "For remembrance", "For the dedication", "A Psalm.", "Of Heman", "Of Ethan",
                "When ", "He said", "To be sung", "Set to", "On the", "Concerning", "A love song", "To bring remembrance", "A song of ascents", "A Psalm of praise", "For teaching", "Upon ")
_TITLE_WORDS = ("choirmaster", "Maskil", "Miktam", "Shiggaion", "Korah", "Psalm of", "song of ascents", "Jeduthun", "Gittith", "Alamoth",
                "Sheminith", "stringed instruments", "to the tune")

_SENT = re.compile(r'(?<=[.:])\s+(?=[A-Z“‘])')

def strip_superscription(t):
    parts = _SENT.split(t)
    out = list(parts)
    while len(out) > 1:
        s = out[0]
        if s.startswith(_TITLE_START) or any(w in s for w in _TITLE_WORDS):
            out.pop(0)
            continue
        break
    return " ".join(out)

def _is_apos(chars, i, depth):
    prev = chars[i-1] if i > 0 else " "
    nxt = chars[i+1] if i + 1 < len(chars) else " "
    if prev.isalpha() and nxt.isalpha():
        return True
    if prev in "sS" and depth == 0 and not nxt.isalpha():
        return True
    return False

def _balance_quotes(t):
    """Verses cut out of longer speeches have unmatched quotes; add the missing openers/closers."""
    chars = list(t)
    dd = ds = 0; lead_d = lead_s = 0
    for i, c in enumerate(chars):
        if c == "“": dd += 1
        elif c == "”":
            if dd: dd -= 1
            else: lead_d += 1
        elif c == "‘": ds += 1
        elif c == "’":
            if _is_apos(chars, i, ds):
                continue
            if ds: ds -= 1
            else: lead_s += 1
    t = "“" * lead_d + "‘" * lead_s + t + "’" * ds + "”" * dd
    # a verse that is entirely one quotation reads better without the outer marks on a slide
    if t.startswith("“") and t.endswith("”") and t.count("“") == 1 and t.count("”") == 1:
        t = t[1:-1]
    return t

def clean(t, ref_book=None, first_verse=None):
    if ref_book == "Psalms" and first_verse == 1:
        t = strip_superscription(t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*\bSelah\b\.?", "", t).strip()
    if t and t[0].islower():
        t = "…" + t
    if t and t[-1] in ",;:—–-":
        t = t.rstrip(",;:—–- ") + "…"
    elif t and t[-1] not in ".!?…’”)":
        t = t + "…"
    return _balance_quotes(t)

def display_text(ref):
    book, ch, v1, ch2, v2 = parse(ref)
    return clean(text(ref), book, v1)
