"""Build the post library + 3-year posting schedule -> build/library.json

Post types
  V  : 10 Bible verses for a topic (list cover + verse text slides + CTA)
  C  : 10 Bible chapters for a topic (list cover + chapter summary slides + CTA)
  P  : 7-day reading plan for a topic
  S  : single verse post (hook slide + verse slide + CTA)
  KC : stack of 5 chapter lists (like the screenshot carousel)
  KV : stack of 5 verse lists
  D  : daily word ("Today God is saying to you"), slot 0
  Q  : Bible quiz (4 multiple-choice questions, swipe to reveal), slot 5 / 4pm
"""
import datetime as dt, glob, hashlib, json, os, random, re
import bible, library, quiz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
START = dt.date(2026, 11, 10)
DAYS = 3 * 365 + 1

ABOUT = set("""godslove grace salvation gods-promises faithfulness presence holyspirit love money integrity gossip words justice unity
humility pride heaven eternallife forgiveness faith identity purpose obedience holiness fasting worship gratitude contentment trust
generosity hospitality stewardship timemanagement victory kindness friendship enemies neighbor poor church serving evangelism success
patience discipline selfcontrol purity temptation rest creation prayer wisdom peace joy hope surrender growth marriage""".split())

# Sensitive topics get a gentle support line in the caption.
CARE = set("depression givingup trauma lonely panic brokenheart grief childloss miscarriage lossofparent addiction".split())

# Topics pinned to dates (not used outside their window).
SEASONAL = set("christmas advent easter goodfriday thanksgiving newyear lent mothersday fathersday backtoschool harvest winter monday sunday".split())

def h(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

def pick(options, key):
    return options[h(key) % len(options)]

def prep(t):
    return "About" if t["id"] in ABOUT else "for"

# "When You..." phrasing, which is what the account's best-performing posts use.
WHEN = {
 "anxiety": "When You're Anxious", "fear": "When You're Afraid", "overthinking": "When You Can't Stop Overthinking",
 "depression": "When Everything Feels Heavy", "lonely": "When You Feel Alone", "sleep": "When You Can't Sleep",
 "stress": "When You're Stressed", "overwhelmed": "When You Feel Overwhelmed", "anger": "When You're Angry",
 "comparison": "When You Can't Stop Comparing", "selfworth": "When You Feel Like You're Not Enough",
 "givingup": "When You Feel Like Giving Up", "burnout": "When You're Burned Out", "courage": "When You Need Courage",
 "guilt": "When You Can't Let Go of Shame", "regret": "When You Regret Your Past", "panic": "When Panic Hits",
 "numb": "When God Feels Far Away", "strength": "When You Need Strength", "hope": "When You Need Hope",
 "peace": "When You Need Peace", "confidence": "When You Doubt Yourself", "patience": "When You're Running Out of Patience",
 "grief": "When You're Grieving", "brokenheart": "When Your Heart Is Broken", "breakup": "When You're Going Through a Breakup",
 "betrayal": "When Someone Betrays You", "forgiveothers": "When It's Hard to Forgive", "rejection": "When You Feel Rejected",
 "disappointment": "When Life Didn't Go as Planned", "unansweredprayer": "When God Seems Silent", "waiting": "When You're Waiting on God",
 "suffering": "When You're Suffering", "trials": "When Life Gets Hard", "healing": "When You Need Healing",
 "sickness": "When You're Sick", "temptation": "When You're Tempted", "protection": "When You Need Protection",
 "forgotten": "When You Feel Forgotten", "wilderness": "When You're in a Dry Season", "trauma": "When You're Healing From Trauma",
 "jobloss": "When You Lose Your Job", "marriagestruggles": "When Your Marriage Is Struggling", "doubt": "When You're Doubting",
 "decisions": "When You Have a Big Decision to Make", "guidance": "When You Don't Know What to Do Next",
 "unqualified": "When You Feel Unqualified", "future": "When You're Worried About the Future", "stuck": "When You Feel Stuck",
 "behind": "When You Feel Behind in Life", "unfair": "When Life Feels Unfair", "miraclesneed": "When You Need a Miracle",
 "financialstress": "When Money Is Tight", "tiredmoms": "When You're a Tired Mom", "familyconflict": "When Family Is Hard",
 "toxicpeople": "When People Are Difficult", "repentance": "When You've Drifted From God", "peoplepleasing": "When You Need Everyone to Like You",
}

def verse_title(t):
    if t["tv"]:
        return t["tv"]
    if t["id"] in WHEN:
        return pick([f"10 Best Bible Verses for {WHEN[t['id']]}", f"Bible Verses for {WHEN[t['id']]}", f"Bible Verses to Read {WHEN[t['id']]}"], "V" + t["id"])
    p, s = prep(t), t["subject"]
    if p == "About":
        return pick([f"Bible Verses About {s}", f"What the Bible Says About {s}", f"10 Bible Verses About {s}"], "V" + t["id"])
    return pick([f"Bible Verses {p} {s}", f"Save These Verses {p} {s}", f"10 Bible Verses {p} {s}", f"Scriptures {p} {s}"], "V" + t["id"])

def chapter_title(t):
    if t["tc"]:
        return t["tc"]
    if t["id"] in WHEN:
        return pick([f"Best Chapters to Read {WHEN[t['id']]}", f"Bible Chapters to Read {WHEN[t['id']]}"], "C" + t["id"])
    p, s = prep(t), t["subject"]
    if p == "About":
        return pick([f"Bible Chapters About {s}", f"Best Chapters to Read About {s}"], "C" + t["id"])
    return pick([f"Best Bible Chapters {p} {s}", f"Best Chapters to Read {p} {s}", f"Bible Chapters {p} {s}"], "C" + t["id"])

def plan_title(t):
    p = "on" if prep(t) == "About" else "for"
    return f"A 7-Day Bible Reading Plan {p} {t['subject']}"

PROPER = {"God", "God's", "Jesus", "Christ", "Christmas", "Easter", "Thanksgiving", "Advent", "Lent", "Good", "Friday",
          "Sunday", "Monday", "Mother's", "Father's", "Holy", "Spirit", "Scripture", "I", "Bible", "Day"}

def sentence_case(subject):
    return " ".join(w if w in PROPER or w.strip('"') in PROPER else w.lower() for w in subject.split())

SINGLE_OVERRIDE = {
    "memorize": "A verse every Christian should know by heart.",
    "prayers": "Pray this one over your day.",
    "shortverses": "Short enough to memorize today.",
    "jesuswords": "Words Jesus said that still hold today.",
    "advent": "Preparing your heart for Christmas starts here.",
}

CAT_TAGS = {"mind": ["mentalhealth", "christianmentalhealth"], "heart": ["hope", "comfort"], "love": ["christiancouples", "relationships"],
            "family": ["christianfamily", "christianparenting"], "faith": ["faith", "christianliving"], "life": ["christianlife", "dailydevotional"],
            "seasons": ["devotional", "christianholiday"], "study": ["biblestudy", "learnthebible"]}
TOPIC_TAGS = {
 "anxiety": ["anxiety", "anxietyrelief"], "fear": ["fear", "courage"], "overthinking": ["overthinking", "anxiety"], "depression": ["depression", "mentalhealthmatters"],
 "lonely": ["loneliness", "notalone"], "sleep": ["insomnia", "cantsleep"], "stress": ["stress", "overwhelmed"], "overwhelmed": ["overwhelmed", "stress"],
 "anger": ["anger", "selfcontrol"], "comparison": ["comparison", "jealousy"], "selfworth": ["selfworth", "youareenough"], "givingup": ["dontgiveup", "keepgoing"],
 "burnout": ["burnout", "rest"], "peace": ["peace", "calm"], "joy": ["joy", "happiness"], "hope": ["hope", "encouragement"], "strength": ["strength", "encouragement"],
 "courage": ["courage", "bebrave"], "guilt": ["shame", "forgiveness"], "regret": ["regret", "newbeginnings"], "panic": ["panicattack", "anxiety"],
 "grief": ["grief", "loss"], "lossofparent": ["grief", "missingmom"], "childloss": ["childloss", "grief"], "miscarriage": ["miscarriage", "infantloss"],
 "brokenheart": ["heartbreak", "healing"], "breakup": ["breakup", "heartbreak"], "betrayal": ["betrayal", "trustissues"], "forgiveothers": ["forgiveness", "letgo"],
 "rejection": ["rejection", "chosen"], "unansweredprayer": ["prayer", "waitingongod"], "waiting": ["waitingongod", "patience"], "healing": ["healing", "prayerforhealing"],
 "sickness": ["sick", "healing"], "chronicillness": ["chronicillness", "chronicpain"], "addiction": ["recovery", "sobriety"], "temptation": ["temptation", "purity"],
 "marriage": ["marriage", "christianmarriage"], "couples": ["couples", "christiancouples"], "dating": ["christiandating", "dating"], "singleness": ["single", "christiansingles"],
 "moms": ["momlife", "christianmom"], "tiredmoms": ["momlife", "tiredmom"], "dads": ["dadlife", "christiandad"], "teens": ["teens", "youthgroup"], "kids": ["kids", "sundayschool"],
 "students": ["studytok", "college"], "exams": ["finals", "studytok"], "work": ["work", "9to5"], "money": ["money", "finance"], "financialstress": ["money", "provision"],
 "christmas": ["christmas", "jesusisthereason"], "easter": ["easter", "heisrisen"], "thanksgiving": ["thanksgiving", "grateful"], "newyear": ["newyear", "newbeginnings"],
 "prayer": ["prayer", "howtopray"], "newbeliever": ["newbeliever", "newchristian"], "startbible": ["biblereading", "bibleforbeginners"],
}


SINGLE_HOOKS = [
    "{hook}", "{hook}", "{hook}", "{hook}", "{hook}",
    "Read this if you need it today.",
    "Save this for the day you need it.",
    "A verse to hold on to.",
]

STACK_CHAPTER_HOOKS = {
    "any": ["If you want to start reading the Bible, start here", "Bible chapters for every season of life",
            "Not sure where to read in the Bible? Start here", "Bible chapters for whatever you're going through",
            "Save this for your next Bible study", "Where to read in the Bible when life happens"],
    "mind": ["Bible chapters for when your mind won't rest", "Read these when your thoughts get loud"],
    "heart": ["Bible chapters for when life gets hard", "Save these for your hardest days"],
    "love": ["Bible chapters for every relationship in your life", "Chapters to read with the people you love"],
    "family": ["Bible chapters every family should read", "Chapters for every season of family life"],
    "faith": ["Bible chapters that will grow your faith", "Read these to fall in love with God's Word"],
    "life": ["Bible chapters for real life", "Chapters for work, money, and everything in between"],
    "study": ["Bible chapters every Christian should read", "Start your Bible study with these"],
}
STACK_VERSE_HOOKS = {
    "any": ["Bible verses for whatever you're going through", "Save this. You'll need one of these soon.",
            "Find the verse for what you're facing right now", "Bible verses for every season of life",
            "A verse for every situation", "Screenshot the one you need today"],
    "mind": ["Bible verses for your mental health", "Verses for when your mind won't slow down"],
    "heart": ["Bible verses for when life breaks your heart", "Verses for your hardest seasons"],
    "love": ["Bible verses for every relationship", "Verses for the people you love"],
    "family": ["Bible verses to pray over your family", "Verses for every season of family life"],
    "faith": ["Bible verses to grow your faith", "Verses every believer should know"],
    "life": ["Bible verses for everyday life", "Verses for work, school, and real life"],
}


def build():
    topics = library.load_topics()
    probs = library.validate(topics)
    if probs:
        raise SystemExit("Fix library problems first:\n" + "\n".join(probs))
    summaries = {}
    for f in glob.glob(os.path.join(HERE, "chapters", "*.txt")):
        for line in open(f, encoding="utf-8"):
            if "|" in line:
                k, v = [x.strip() for x in line.split("|", 1)]
                summaries[bible.label(k)] = v.replace('"', "“", 1).replace('"', "”", 1).replace('"', "“", 1).replace('"', "”", 1)

    T, verses_text = {}, {}
    for t in topics:
        vl = [bible.label(r) for r, _, _ in t["verses"]]
        cl = [bible.label(c) for c, _ in t["chapters"]]
        for lab in vl:
            verses_text[lab] = bible.display_text(lab)
        tags = TOPIC_TAGS.get(t["id"]) or CAT_TAGS.get(t["cat"], [])
        T[t["id"]] = {"s": t["subject"], "cat": t["cat"], "hook": t["hook"], "v": vl, "c": cl,
                      "care": t["id"] in CARE, "tags": tags, "about": t["id"] in ABOUT,
                      "tv": t["tv"], "tc": t["tc"], "when": WHEN.get(t["id"])}

    posts = []
    for t in topics:
        tid = t["id"]
        if len(T[tid]["v"]) >= 8:
            posts.append({"id": f"V:{tid}", "t": "V", "k": tid, "ti": verse_title(t)})
        if len(T[tid]["c"]) >= 6:
            posts.append({"id": f"C:{tid}", "t": "C", "k": tid, "ti": chapter_title(t)})
        if len(T[tid]["c"]) >= 7 and t["cat"] != "study":
            posts.append({"id": f"P:{tid}", "t": "P", "k": tid, "ti": plan_title(t)})
        plural = re.search(r"\b(these|verses|chapters|them|ones)\b", t["hook"], re.I)
        own = SINGLE_OVERRIDE.get(tid) or (t["hook"] if not plural else
              f"A Bible verse {'about' if prep(t) == 'About' else 'for'} {sentence_case(t['subject'])}.")
        for i, lab in enumerate(T[tid]["v"]):
            hook = pick(SINGLE_HOOKS, f"S{tid}{i}").format(hook=own)
            if tid in ("beatitudes", "commandments", "armor", "iam", "namesofgod", "prophecies", "fruit"):
                hook = own
            # vh: topic-specific hook used for the 9pm verse video (first second on screen + start of caption, for search)
            posts.append({"id": f"S:{tid}:{i}", "t": "S", "k": tid, "v": lab, "ti": hook, "vh": own})

    # Stacks: 5 topics each, from a category pool (or mixed), never repeating a combination.
    rng = random.Random(7)
    general = [x for x in T if x not in SEASONAL]
    by_cat = {}
    for x in general:
        by_cat.setdefault(T[x]["cat"], []).append(x)
    used = set()
    for kind, hooks_map, need in (("KC", STACK_CHAPTER_HOOKS, "c"), ("KV", STACK_VERSE_HOOKS, "v")):
        made = 0
        tries = 0
        while made < 180 and tries < 10000:
            tries += 1
            cat = rng.choice(list(hooks_map.keys()))
            pool = [x for x in (general if cat == "any" else by_cat.get(cat, [])) if len(T[x][need]) >= (6 if need == "c" else 8)]
            if need == "v":
                pool = [x for x in pool if T[x]["cat"] != "study"]
            if len(pool) < 5:
                continue
            ks = tuple(sorted(rng.sample(pool, 5)))
            if (kind, ks) in used:
                continue
            used.add((kind, ks))
            ks = list(ks)
            rng.shuffle(ks)
            posts.append({"id": f"{kind}:{made}", "t": kind, "ks": ks, "ti": rng.choice(hooks_map[cat]), "cat": cat})
            made += 1

    byid = {p["id"]: p for p in posts}
    hist = load_tuning()
    schedule = make_schedule(posts, T, hist)
    # daily "God is saying to you today" post, first slot every day; messages cycle without repeats
    daily = []
    for line in open(os.path.join(HERE, "daily", "messages.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            o, b, tn, ref, c = [x.strip() for x in line.split("|")]
            daily.append({"o": o, "b": b, "t": tn, "r": bible.label(ref), "v": bible.display_text(ref), "c": c})
    drng = random.Random(11); order = []
    while len(order) < len(schedule):
        cyc = list(range(len(daily))); drng.shuffle(cyc)
        if order and cyc[0] == order[-1]: cyc.append(cyc.pop(0))
        order += cyc
    for i, day in enumerate(schedule):
        d = (START + dt.timedelta(i)).isoformat()
        pid = f"D:{d}"
        posts.append({"id": pid, "t": "D", "date": d, "m": order[i], "ti": f"Today God is saying to you: {daily[order[i]]['o']}"})
        day.insert(0, pid)
    # daily Bible quiz, appended as the last slot (index 5) of every day
    Qs, qprobs = quiz.load()
    if qprobs:
        raise SystemExit("Fix quiz problems first (python3 quiz.py):\n" + "\n".join(qprobs))
    add_quiz(posts, schedule, Qs, hist)
    lib = {
        "meta": {"translation": "Berean Standard Bible (BSB)", "start": START.isoformat(), "days": len(schedule),
                 "built": dt.datetime.now().isoformat(timespec="minutes")},
        "topics": T, "verses": verses_text, "daily": daily, "chapters": summaries, "posts": posts, "schedule": schedule,
        "quiz": Qs,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "library.json"), "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, separators=(",", ":"))
    counts = {}
    for p in posts:
        counts[p["t"]] = counts.get(p["t"], 0) + 1
    print("posts:", len(posts), counts)
    print("schedule days:", len(schedule), "size KB:", os.path.getsize(os.path.join(OUT, "library.json")) // 1024)
    return lib


# ---------------- performance tuning (analytics/tuning.json, written by perf.py tune) ----------------

TUNING = os.path.join(HERE, "analytics", "tuning.json")

def load_tuning():
    try:
        hist = json.load(open(TUNING, encoding="utf-8")).get("history", [])
    except FileNotFoundError:
        return []
    return sorted(hist, key=lambda t: t["effective_from"])

def tuning_for(d, hist):
    """The tuning step in effect on date d (the latest one whose effective_from <= d), or None."""
    cur = None
    for t in hist:
        if t["effective_from"] <= d.isoformat():
            cur = t
    return cur

def weighted_pattern(base, weights, length):
    """Spread types over `length` slots in proportion to base count x weight (smooth weighted round-robin),
    so a favored type shows up more often but every type still appears."""
    keys = list(base)
    w = {k: base[k] * float(weights.get(k, 1.0)) for k in keys}
    total, cur, seq = sum(w.values()), {k: 0.0 for k in keys}, []
    for _ in range(length):
        for k in keys:
            cur[k] += w[k]
        best = max(keys, key=lambda k: (cur[k], -keys.index(k)))
        seq.append(best); cur[best] -= total
    return seq


# ---------------- daily quiz ----------------

# Rotation of quiz styles (trivia most often). 11-day cycle: T x4, F x3, W x2, B x2.
QUIZ_PATTERN = ["T", "F", "W", "T", "B", "T", "F", "W", "B", "F", "T"]
QUIZ_TITLES = {
    "T": [("Bible Trivia", "Can you get 4/4?"), ("Bible Trivia", "How well do you know your Bible?"),
          ("Bible Trivia", "Only true Bible readers get 4/4"), ("Bible Trivia", "Bet you can’t get all 4 right"),
          ("Bible Quiz", "No Googling. How many can you get?")],
    "F": [("Finish the Verse", "Can you get 4/4?"), ("Finish the Verse", "Can you finish all 4 without looking?"),
          ("Finish the Verse", "Only real Bible readers get 4/4")],
    "W": [("Who Said It?", "Bible edition. Can you get 4/4?"), ("Who Said It?", "Guess who said it in the Bible"),
          ("Who Said It?", "4 quotes. How many can you name?")],
    "B": [("Guess the Book", "Which book of the Bible is this from?"), ("Guess the Book", "Can you name all 4 books?"),
          ("Guess the Book", "Only real Bible readers get 4/4")],
}

def add_quiz(posts, schedule, Qs, hist=()):
    """One quiz post per day. Each style's questions cycle in shuffled order, so a question
    only repeats after its whole pool has been used; no two questions in a post share a verse."""
    rng = random.Random(23)
    pools = {f: sorted(k for k, q in Qs.items() if q["f"] == f) for f in "TFWB"}
    queues = {f: [] for f in pools}

    def take(f):
        out, skipped = [], []
        while len(out) < 4:
            if not queues[f]:
                cyc = pools[f][:]; rng.shuffle(cyc); queues[f] = cyc
            qid = queues[f].pop(0)
            if qid in out or any(Qs[qid]["r"] == Qs[o]["r"] for o in out):
                skipped.append(qid); continue
            out.append(qid)
        queues[f] = skipped + queues[f]
        return out

    for i, day in enumerate(schedule):
        d = (START + dt.timedelta(i)).isoformat()
        tn = tuning_for(START + dt.timedelta(i), hist)
        if tn and tn.get("quiz_styles"):
            base = {k: QUIZ_PATTERN.count(k) for k in dict.fromkeys(QUIZ_PATTERN)}
            f = weighted_pattern(base, tn["quiz_styles"], len(QUIZ_PATTERN))[i % len(QUIZ_PATTERN)]
        else:
            f = QUIZ_PATTERN[i % len(QUIZ_PATTERN)]
        kicker, head = pick(QUIZ_TITLES[f], "Q" + d)
        ti = f"{kicker} {head}" if kicker.endswith("?") else f"{kicker}: {head}"
        pid = f"Q:{d}"
        posts.append({"id": pid, "t": "Q", "date": d, "f": f, "qs": take(f), "ti": ti, "kick": kicker, "head": head})
        day.append(pid)


# ---------------- schedule ----------------

def easter(y):
    a = y % 19; b = y // 100; c = y % 100; d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    hh = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - hh - k) % 7
    m = (a + 11 * hh + 22 * l) // 451; month = (hh + l - 7 * m + 114) // 31; day = ((hh + l - 7 * m + 114) % 31) + 1
    return dt.date(y, month, day)

def nth_weekday(y, m, weekday, n):
    d = dt.date(y, m, 1)
    while d.weekday() != weekday:
        d += dt.timedelta(1)
    return d + dt.timedelta(weeks=n - 1)

def pinned_for_year(y):
    """date -> list of (slot, post-id-prefix) for list slot 'A' / single-verse slot 'B'."""
    pins = {}
    def add(d, slot, what):
        pins.setdefault(d, []).append((slot, what))
    e = easter(y)
    add(dt.date(y, 1, 1), "A", "V:newyear"); add(dt.date(y, 1, 1), "B", "S:newyear")
    add(dt.date(y, 1, 2), "A", "C:newyear"); add(dt.date(y, 1, 3), "A", "P:newyear"); add(dt.date(y, 1, 2), "B", "S:newyear")
    add(dt.date(y, 1, 16), "A", "V:winter"); add(dt.date(y, 1, 16), "B", "S:winter"); add(dt.date(y, 2, 6), "A", "C:winter")
    add(dt.date(y, 2, 13), "A", "C:couples"); add(dt.date(y, 2, 14), "A", "V:love"); add(dt.date(y, 2, 14), "B", "S:love")
    ash = e - dt.timedelta(46)
    add(ash, "A", "V:lent"); add(ash, "B", "S:lent"); add(ash + dt.timedelta(4), "A", "C:lent"); add(ash + dt.timedelta(11), "A", "P:lent")
    add(e - dt.timedelta(2), "A", "V:goodfriday"); add(e - dt.timedelta(2), "B", "S:goodfriday"); add(e - dt.timedelta(3), "A", "C:goodfriday")
    add(e - dt.timedelta(1), "B", "S:goodfriday")
    add(e, "A", "V:easter"); add(e, "B", "S:easter"); add(e + dt.timedelta(1), "A", "C:easter"); add(e + dt.timedelta(1), "B", "S:easter")
    add(e - dt.timedelta(7), "A", "P:easter")
    md = nth_weekday(y, 5, 6, 2)
    add(md, "A", "V:mothersday"); add(md, "B", "S:mothersday"); add(md - dt.timedelta(1), "A", "C:mothersday")
    fd = nth_weekday(y, 6, 6, 3)
    add(fd, "A", "V:fathersday"); add(fd, "B", "S:fathersday"); add(fd - dt.timedelta(1), "A", "C:fathersday")
    add(dt.date(y, 8, 9), "A", "V:backtoschool"); add(dt.date(y, 8, 9), "B", "S:backtoschool"); add(dt.date(y, 8, 12), "A", "C:backtoschool")
    add(dt.date(y, 10, 3), "A", "V:harvest"); add(dt.date(y, 10, 3), "B", "S:harvest"); add(dt.date(y, 10, 10), "A", "C:harvest")
    tg = nth_weekday(y, 11, 3, 4)
    add(tg, "A", "V:thanksgiving"); add(tg, "B", "S:thanksgiving"); add(tg - dt.timedelta(3), "A", "C:thanksgiving")
    add(tg - dt.timedelta(1), "B", "S:thanksgiving"); add(tg - dt.timedelta(6), "A", "P:thanksgiving")
    adv = dt.date(y, 11, 27)
    while adv.weekday() != 6:
        adv += dt.timedelta(1)
    add(adv, "A", "V:advent"); add(adv, "B", "S:advent"); add(adv + dt.timedelta(7), "A", "C:advent")
    add(adv + dt.timedelta(14), "B", "S:advent"); add(adv + dt.timedelta(21), "B", "S:advent")
    add(dt.date(y, 12, 19), "A", "P:christmas"); add(dt.date(y, 12, 22), "A", "C:christmas"); add(dt.date(y, 12, 24), "A", "V:christmas")
    for d in (20, 23, 24, 25):
        add(dt.date(y, 12, d), "B", "S:christmas")
    add(dt.date(y, 12, 25), "A", "V:prophecies")
    add(dt.date(y, 12, 30), "A", "V:newbeginnings")
    return pins


def make_schedule(posts, T, hist=()):
    """Each day: [list, list, single verse, list]. The app shows as many slots as the user posts per day.
    Lists (what people bookmark) are 3 of 4 slots. Topics don't repeat within ~5 days."""
    rng = random.Random(42)
    byid = {p["id"]: p for p in posts}
    tops = lambda pid: byid[pid].get("ks") or [byid[pid]["k"]]
    singles = {}
    for p in posts:
        if p["t"] == "S":
            singles.setdefault(p["k"], []).append(p["id"])
    for k in singles:
        rng.shuffle(singles[k])
    seasonal_list = {p["id"] for p in posts if p["t"] in "VCP" and p["k"] in SEASONAL}
    pools = {t: [p["id"] for p in posts if p["t"] == t and p["id"] not in seasonal_list] for t in ("V", "C", "P", "KC", "KV")}
    for t in pools:
        rng.shuffle(pools[t])
    # verse and chapter lists lead (they get the most saves); stacks and plans mixed in
    pattern = ["C", "V", "KC", "V", "C", "P", "V", "C", "KV", "C", "V", "P"]
    cur = {t: 0 for t in pools}
    pat_i = [0]
    general = [k for k in singles if k not in SEASONAL]
    single_order = []
    idx = {k: 0 for k in general}
    for _ in range(40):
        ks = general[:]; rng.shuffle(ks)
        for k in ks:
            if idx[k] < len(singles[k]):
                single_order.append(singles[k][idx[k]]); idx[k] += 1
    s_cur = [0]
    recent = []

    def take_list(avoid, pattern=pattern, tw=None):
        for step in range(len(pattern)):
            typ = pattern[(pat_i[0] + step) % len(pattern)]
            pool = pools[typ]
            found = []
            for look in range(min(25, len(pool))):
                j = (cur[typ] + look) % len(pool)
                if not set(tops(pool[j])) & avoid:
                    found.append(j)
                    if not tw or len(found) >= 6:
                        break
            if found:
                # with tuning, take the best-performing topic among the next few eligible posts
                score = lambda jj: sum(tw(k) for k in tops(pool[jj])) / len(tops(pool[jj]))
                j = max(found, key=lambda jj: (score(jj), -found.index(jj))) if tw else found[0]
                pid = pool[j]
                a = cur[typ] % len(pool)
                pool[a], pool[j] = pool[j], pool[a]
                cur[typ] += 1; pat_i[0] += 1
                return pid
        typ = pattern[pat_i[0] % len(pattern)]; pat_i[0] += 1
        pid = pools[typ][cur[typ] % len(pools[typ])]; cur[typ] += 1
        return pid

    def take_single(avoid):
        for look in range(40):
            j = (s_cur[0] + look) % len(single_order)
            pid = single_order[j]
            if byid[pid]["k"] not in avoid:
                a = s_cur[0] % len(single_order)
                single_order[a], single_order[j] = single_order[j], single_order[a]
                s_cur[0] += 1
                return pid
        pid = single_order[s_cur[0] % len(single_order)]; s_cur[0] += 1
        return pid

    pins = {}
    for y in range(START.year, START.year + 5):
        for d, lst in pinned_for_year(y).items():
            pins.setdefault(d, []).extend(lst)
    seasonal_cur = {}
    schedule = []
    for i in range(DAYS):
        d = START + dt.timedelta(i)
        pinned_a = pinned_b = None
        for slot, what in pins.get(d, []):
            if slot == "A" and pinned_a is None and what in byid:
                pinned_a = what
            if slot == "B" and pinned_b is None and what.startswith("S:") and singles.get(what[2:]):
                k = what[2:]; c = seasonal_cur.get(k, 0)
                pinned_b = singles[k][c % len(singles[k])]; seasonal_cur[k] = c + 1
        if pinned_a is None and d.weekday() == 0 and i % 28 < 7:
            pinned_a = "V:monday" if (i // 28) % 2 == 0 else "C:monday"
        if pinned_a is None and d.weekday() == 6 and i % 42 < 7:
            pinned_a = "V:sunday" if (i // 42) % 2 == 0 else "C:sunday"
        avoid = set(recent)
        tn = tuning_for(d, hist)
        pat, tw = pattern, None
        if tn:
            if tn.get("list_types"):
                base = {k: pattern.count(k) for k in dict.fromkeys(pattern)}
                pat = weighted_pattern(base, tn["list_types"], len(pattern))
            if tn.get("topics") or tn.get("categories"):
                tws, cws = tn.get("topics", {}), tn.get("categories", {})
                tw = lambda k: float(tws.get(k, 1.0)) * float(cws.get(T[k]["cat"], 1.0))
        day = []
        a = pinned_a or take_list(avoid, pat, tw); avoid |= set(tops(a)); day.append(a)
        b = take_list(avoid, pat, tw); avoid |= set(tops(b)); day.append(b)
        c = pinned_b or take_single(avoid); avoid |= {byid[c]["k"]}; day.append(c)
        e = take_list(avoid, pat, tw); day.append(e)
        recent = (recent + [t for pid in day for t in tops(pid)])[-24:]
        schedule.append(day)
    return schedule


if __name__ == "__main__":
    build()
