"""Load and validate the Bible quiz banks in quiz/*.txt against the BSB text.

Formats (one question per line, '#' comments):
  trivia.txt  question | correct | wrong | wrong | wrong | reference | check & check
  finish.txt  reference | missing word | wrong | wrong | wrong
  who.txt     reference | exact quote | speaker | wrong | wrong | wrong | name [@ context reference]
  book.txt    reference

Every answer is shown with its BSB verse as proof on the answer slide, so each
question must be provable from the text of its reference:
  T: every check phrase appears in the reference text
  F: the missing word appears exactly once (whole word) in the verse
  W: the quote appears in the verse, and the speaker's name appears in it or in the context reference
  B: the book's name does not appear in the verse (no giveaways)

    python3 quiz.py            # validate, print counts (must report 0 problems)
"""
import hashlib, os, re
import bible

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, "quiz")
BLANK = "_____"

# Books grouped by kind; "Guess the Book" wrong answers come from the same group first.
GROUPS = [
    ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
    ["Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "Nehemiah", "Esther"],
    ["Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon"],
    ["Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Malachi"],
    ["Matthew", "Mark", "Luke", "John", "Acts"],
    ["Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Timothy", "Titus"],
    ["Hebrews", "James", "1 Peter", "2 Peter", "1 John", "Revelation"],
]
OT_GROUPS, NT_GROUPS = GROUPS[:4], GROUPS[4:]


def _h(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def _lines(name):
    path = os.path.join(QDIR, name)
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if line and not line.startswith("#"):
            yield f"{name}:{ln}", [p.strip() for p in line.split("|")]


def _order(qid, correct, wrong):
    """Deterministic shuffle of the four options; returns (options, index of correct)."""
    opts = [correct] + list(wrong)
    keyed = sorted(range(4), key=lambda i: _h(f"{qid}:{i}"))
    shuffled = [opts[i] for i in keyed]
    return shuffled, shuffled.index(correct)


def _book_of(ref):
    return bible.parse(ref)[0]


def _distractors(book, key):
    gi = next(i for i, g in enumerate(GROUPS) if book in g)
    same = [b for b in GROUPS[gi] if b != book]
    testament = OT_GROUPS if gi < 4 else NT_GROUPS
    other = [b for g in testament for b in g if g is not GROUPS[gi]]
    same.sort(key=lambda b: _h(key + b)); other.sort(key=lambda b: _h(key + "o" + b))
    return same[:2] + other[:1] if len(same) >= 2 else same + other[: 3 - len(same)]


def load():
    """Returns (questions dict qid -> question, problems list)."""
    Q, problems = {}, []
    seen = set()

    def add(qid, where, rec):
        if qid in Q:
            problems.append(f"{where}: duplicate question id {qid}")
        Q[qid] = rec

    for where, p in _lines("trivia.txt"):
        if len(p) != 7:
            problems.append(f"{where}: needs 7 fields, has {len(p)}"); continue
        q, correct, w1, w2, w3, ref, checks = p
        try:
            lab, txt = bible.label(ref), bible.text(ref)
        except bible.RefError as e:
            problems.append(f"{where}: {e}"); continue
        for c in [c.strip() for c in checks.split("&") if c.strip()]:
            if c.lower() not in txt.lower():
                problems.append(f"{where}: check phrase {c!r} not in {lab}: {txt}")
        if len({correct.lower(), w1.lower(), w2.lower(), w3.lower()}) < 4:
            problems.append(f"{where}: options are not all different")
        key = q.lower()
        if key in seen:
            problems.append(f"{where}: duplicate question")
        seen.add(key)
        qid = "T" + format(_h(q), "x")
        opts, a = _order(qid, correct, [w1, w2, w3])
        hl = checks.split("&")[0].strip()
        add(qid, where, {"f": "T", "q": q, "o": opts, "a": a, "r": lab, "p": bible.display_text(ref), "hl": hl})

    for where, p in _lines("finish.txt"):
        if len(p) != 5:
            problems.append(f"{where}: needs 5 fields, has {len(p)}"); continue
        ref, word, w1, w2, w3 = p
        try:
            lab, disp = bible.label(ref), bible.display_text(ref)
        except bible.RefError as e:
            problems.append(f"{where}: {e}"); continue
        hits = list(re.finditer(r"(?<![\w’'])" + re.escape(word) + r"(?![\w’'])", disp))
        if len(hits) != 1:
            problems.append(f"{where}: {word!r} appears {len(hits)} times in {lab}: {disp}"); continue
        if len(disp.split()) > 48:
            problems.append(f"{where}: {lab} is too long for a slide ({len(disp.split())} words)")
        if word.lower() in {w1.lower(), w2.lower(), w3.lower()}:
            problems.append(f"{where}: a wrong answer equals the right one")
        m = hits[0]
        qtext = disp[: m.start()] + BLANK + disp[m.end():]
        qid = "F" + format(_h(lab + word), "x")
        opts, a = _order(qid, word, [w1, w2, w3])
        add(qid, where, {"f": "F", "q": qtext, "o": opts, "a": a, "r": lab, "p": disp, "hl": word, "hlpos": m.start()})

    for where, p in _lines("who.txt"):
        if len(p) != 7:
            problems.append(f"{where}: needs 7 fields, has {len(p)}"); continue
        ref, quote, who, w1, w2, w3, check = p
        try:
            lab, txt, disp = bible.label(ref), bible.text(ref), bible.display_text(ref)
        except bible.RefError as e:
            problems.append(f"{where}: {e}"); continue
        if quote not in disp:
            problems.append(f"{where}: quote {quote!r} not in {lab}: {disp}")
        name, _, ctx = check.partition("@")
        name, ctx = name.strip(), ctx.strip()
        try:
            hay = txt + " " + (bible.text(ctx) if ctx else "")
        except bible.RefError as e:
            problems.append(f"{where}: context {e}"); continue
        if name.lower() not in hay.lower():
            problems.append(f"{where}: name {name!r} not in {lab}{' or ' + ctx if ctx else ''}")
        qid = "W" + format(_h(lab + quote), "x")
        opts, a = _order(qid, who, [w1, w2, w3])
        add(qid, where, {"f": "W", "q": "“" + quote.rstrip() + "”", "o": opts, "a": a, "r": lab, "p": disp, "hl": quote})

    for where, p in _lines("book.txt"):
        ref = p[0]
        try:
            lab, disp, book = bible.label(ref), bible.display_text(ref), _book_of(ref)
        except bible.RefError as e:
            problems.append(f"{where}: {e}"); continue
        names = {book, bible.DISPLAY.get(book, book), re.sub(r"^\d ", "", book)}
        if any(re.search(r"\b" + re.escape(n) + r"\b", disp) for n in names):
            problems.append(f"{where}: the verse gives away the book ({book}): {disp}")
        if len(disp.split()) > 48:
            problems.append(f"{where}: {lab} is too long for a slide")
        wrong = p[1:4] if len(p) >= 4 else _distractors(book, lab)
        qid = "B" + format(_h(lab), "x")
        opts, a = _order(qid, book, wrong)
        add(qid, where, {"f": "B", "q": disp, "o": opts, "a": a, "r": lab, "p": disp, "hl": ""})

    return Q, problems


if __name__ == "__main__":
    Q, probs = load()
    for x in probs:
        print("PROBLEM", x)
    counts = {}
    for q in Q.values():
        counts[q["f"]] = counts.get(q["f"], 0) + 1
    pos = [0, 0, 0, 0]
    for q in Q.values():
        pos[q["a"]] += 1
    print(f"{len(Q)} questions {counts}; correct answer positions A-D: {pos}; {len(probs)} problems")
