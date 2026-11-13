# Daily content review (playbook for the nightly reviewer)

Goal: **the most eyeballs on the Scripture Spark brand.** Views first; shares and comments next (they earn the next round of views); saves when the owner shares them. Every night, look at what caught and what didn't, kill what isn't working, lean into what is, and record what you changed so the next nights can tell whether it worked. Act fast: the owner wants decisions daily, not weekly.

Read `CLAUDE.md` first. It describes the pipeline, the validators and the rules that always apply.

## 1. Look back
- `git pull`, then `python3 perf.py report` and read `analytics/REPORT.md`. Also skim `analytics/performance.csv` for the posts behind the numbers.
- Read `analytics/CHANGELOG.md`. For each change made 1–3 weeks ago, compare the metric it was meant to move (same slot or format, before vs after). Write the verdict under that entry: **kept** (it helped), **reverted** (it hurt; undo it), or **inconclusive** (not enough posts yet; keep watching).
- Don't trust single posts. New accounts get erratic distribution. Compare medians, need 3+ posts per group, and compare posts of similar age (stats keep growing for days).

## 2. Look out
- Research what is getting views right now: Christian/faith TikTok formats, Bible content, hooks, carousel and short-video trends, TikTok search keywords people use for Bible topics. Use web search; prefer sources with data; note dates.
- Look for ideas that fit the brand ("Read Scripture with someone"; warm, hopeful, Scripture-first) and our limits: automated photo carousels and short videos through Buffer, no trending sounds, original designs only, BSB text only.

## 3. Improve (up to 3 changes a night; one clear hypothesis each)
You may change these without asking:
- Titles, hooks and phrasings: `WHEN` titles, topic hooks, `TV`/`TC` titles, quiz headlines (`QUIZ_TITLES`), verse-video hooks (`vh`), list cover wording.
- Captions: first line keywords (TikTok search reads the first ~50 characters and on-screen text), CTA wording, hashtag sets (keep it to about 5–8).
- New topics, verse picks, chapter summaries, daily messages, quiz questions. Every reference must pass `python3 library.py` / `python3 quiz.py` with 0 problems. Never quote Scripture from memory.
- Slide and video design within the safe areas (`SAFE_B`, video safe area). Render samples and check them against a mock TikTok overlay before shipping.
- Mix weights are tuned automatically every night (`perf.py tune`). You may also add a hand-made step to `analytics/tuning.json` (effective tomorrow or later) when the data is clear, e.g. a post far above the rest (2x+ the median) or a format/topic/quiz style clearly below (under half the median on 2+ posts). Log why in the changelog.
- Queued posts: you MAY replace a queued Buffer post (delete it, then re-create the slot from the new manifest after publishing with `FRESH_KEYS=<that slot key>`) when its format, quiz style or topic type has been cut by the data. Never leave the queue below what it was; never post with shareNow.

Ask the owner first (write it up as a proposal in your summary; don't do it):
- Posting times, number of posts per day, new post formats, which format a time slot uses, the audio, anything about Buffer settings or the scheduled tasks.

Always:
- Keep the app promo slide last in carousels (max 10 slides). Keep the brand voice. No fabricated statistics or claims on slides or captions.
- Published slots are frozen (`make_site.py`), so edits only affect slots that haven't been published yet. Don't force a re-render (`FRESH=1`) unless the owner asks.

## 4. Ship
- Run `python3 library.py`, `python3 quiz.py`, `python3 gen.py`, and render samples of anything you touched (`render_batch.py`, `sheet.py`); look at them.
- Commit to `main` with a clear message (`git pull --rebase origin main` first; the nightly task also pushes analytics there).
- Add an entry to `analytics/CHANGELOG.md`: date, what changed, why (evidence), the metric to watch, and when to judge it (usually 3-7 days).

## 5. Report
Reply with: views trend (last 24 h and last 7 days vs before), what's working and what isn't (top formats, slots, topics, quiz styles), verdicts on past changes, the changes you made this week, and any proposals that need the owner's OK. Keep it short and plain.
