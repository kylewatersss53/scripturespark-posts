# Content changelog (what changed, why, and whether it worked)

Newest first. Each entry: date · change · why · metric to watch · judge after · verdict (kept / reverted / inconclusive).

## 2026-11-13 (night review) · Keep hand kills in force; challenge-style quiz headlines
- **Data (18 posts, 14 with stats):** Finish the Verse "Only real Bible readers get 4/4" 2,626 views (6x the ~400 median; best post by far); Who Said It? 128 (worst). Lists: "When You" titles median 597 vs 10-number/"About" 247-482. Daily word videos sliding 417 → 364 → 356 → 208 with ~4.6 s of 12 s watched. 9pm verse videos (retired) 134-325.
- **Change 1 (tuning):** the nightly `perf.py tune` recomputes weights from scratch, so tonight's auto step (from 2026-11-16) had quietly un-killed Who Said It? (0.15 → 0.62) and cut Finish the Verse (3.0 → 1.38) on one post each. Now a hand-made kill or boost stays in force while the data points the same way (stronger value wins); data only overrides it when it points the other way. Step for 2026-11-16 regenerated: F 3.0, T 1.0, B 0.8, W 0.15; lists V 0.95, C 1.5, P 0.4, KC/KV 0.3.
- **Change 2 (quiz headlines):** `QUIZ_TITLES` now lean on the identity-challenge hook ("Only real Bible readers get 4/4") for every style, with one or two plain variants left for freshness. Hypothesis: that hook, not just the format, drove the 2,626-view quiz. Affects quizzes from 2026-11-16 (earlier ones are queued/frozen).
- **Watch:** 16:00 quiz median views (before: 1,377 median over 2 posts; F 2,626, W 128); challenge vs plain headline views; W should not reappear.
- **Judge after:** 2026-11-20.
- **Verdict:** pending.
- **Past entries:** 2026-11-13 kill/lean entry: inconclusive (posts under it only started 2026-11-13, no stats yet).

## 2026-11-13 · Kill losers, lean into winners (owner: nothing over 1,000 views)
- **Data (17 posts, 3 days):** Finish the Verse quiz 774 views (best); "Chapters When Everything Feels Heavy" 684; "Verses for When Panic Hits" 597 (11 shares, 13 s watch). Generic "About Faith/Success" lists 222/392. Daily word videos 208-410 (4-6 s of 12 s watched). 9pm verse videos 134/246/320 with ~2 s average watch (worst format). Who Said It? quiz 128 (worst post).
- **Changes:** 9pm verse video retired; 9pm is now a third list. Tuning from 2026-11-13: quiz styles F x3, T x1, B x0.8, W x0.15 (killed); lists V/C x1.5, P x0.4, KC/KV x0.3; "When You..." topics x2, other topics x0.5; mind/heart categories x1.3; no Sunday/Monday pinned lists. Queued "About Pride", "OT Stories", "About Trusting God", Guess the Book and the 9pm video replaced in Buffer. Tuning now runs nightly (kill/lean, effective in 3 days) instead of weekly.
- **Watch:** median views per slot; share of posts over 500 and 1,000 views; F vs T vs B quiz views.
- **Judge after:** 2026-11-17 (nightly tune keeps adjusting before that).
- **Verdict:** pending. Also note the 2026-11-10 verse-video entry: **reverted** (lowest views and watch time).

## 2026-11-10 · 9pm verse video rebuilt as a research-driven series
- **Changes:** 21:00 verse video is now a nightly series ("TONIGHT'S VERSE · #N") with the hook on screen from the first frame, phrase-by-phrase text over a slowly drifting background, a clean fade at the end for looping, worship music (5 Pixabay tracks, 14 beds, rotated) with soft birdsong, and a "new verse every night at 9, follow" caption line. Daily word video no longer fades in from black (first frame = cover).
- **Why (research):** faceless formats have the highest median views (Revid index of 2.39M TikToks: about 1.9x on-camera); the best faceless accounts run as repeatable shows with the same opening every day; hooks are decided in the first 1–3 s and on-screen text in the first frame helps; 7–21 s with a clean loop maximises completion and rewatches; kinetic text holds attention; background music is a key driver for faith content; subtle motion beats a frozen frame (weak evidence).
- **Watch:** 21:00 median views and average watch time (vs 07:00 daily video); follows are not in Buffer, so ask the owner for TikTok Studio follower numbers.
- **Judge after:** 2026-11-24.
- **Verdict:** pending.

## 2026-11-10 · Baseline setup
- **Changes:** 5 posts a day: 07:00 daily word video (birdsong), 12:00 + 19:00 list carousels, 16:00 Bible quiz carousel, 21:00 verse video (new). Text kept clear of TikTok's caption area; smaller 10-item lists. Analytics score weighted to views (70%).
- **Why:** owner's goal is the most eyeballs on the brand. Research: completion, rewatches and shares drive For You reach; short 7–15 s videos with a hook in the first 1–2 s do best; on-screen text and the first ~50 caption characters drive TikTok search; quizzes are the strongest documented comment driver in faith TikTok.
- **Watch:** median views per format and per slot; 21:00 verse video vs 07:00 daily word video; quiz comments per 1k views.
- **Judge after:** 2026-11-24.
- **Verdict:** pending.
