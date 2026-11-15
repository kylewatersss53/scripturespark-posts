# Content changelog (what changed, why, and whether it worked)

Newest first. Each entry: date · change · why · metric to watch · judge after · verdict (kept / reverted / inconclusive).

## 2026-11-14 (owner session) · Red Letter replaces the 7am daily word video; Trivia cut
- **Data:** daily word videos flat at 366-421 views with ~4 s of 12 s watched (the weakest regular slot). Trivia quiz 66 views (worst). Winners: Finish the Verse 2,878; "When You" chapter lists 1,135 and 879; "When Panic Hits" 704.
- **Changes:** from 2026-11-16 the 07:00 slot posts **Red Letter** videos: one short saying of Jesus (69 verified sayings in `redletter/sayings.txt`), hand-lettered in red on warm paper, one word at a time, first word visible from frame one, 6.5 s, worship music. Owner gave creative freedom and liked the idea (inspired by short single-message faith posts; our own look, Jesus' actual words only). Quiz styles: Trivia cut (T 0.15) from 2026-11-17.
- **To do for the nightly reviewer:** Finish the Verse now runs most days (4 questions each); its bank has 71 questions, so add 50+ verified Finish the Verse questions soon to avoid repeats.
- **Watch:** 07:00 views and average watch (Red Letter vs the daily word's ~380 views / 4 s); 16:00 quiz views.
- **Judge after:** 2026-11-20.
- **Verdict:** pending.

## 2026-11-14 (night review) · Lean harder into "When You..." lists
- **Data (23 posts, 19 with stats):** "When You" list titles median 580 views over 6 posts (top 3 lists: Heavy 1,135 · Sick 879 · Panic 704); the weakest lists are generic/"About"/"10 Bible Verses About" (Faith 258, Unqualified 179). 10-chapter lists lead formats (median 698). Yet the next 2 weeks of the schedule were full of "About"/"for X" titles (Helping People in Need, Stewardship, Anniversaries, Loving Your Enemies, Loving Your Neighbor, Dads, Pregnancy, Body Image): the tuner compared only 12 eligible posts, so 0.5-weighted topics still got picked.
- **Change 1 (titles):** 19 more emotional topics get "When You..." titles in `WHEN` (lost a parent/child/baby/spouse, chronic pain, surgery, addiction, divorce, prodigal child, infertility, single parents, caregivers, debt, negative thoughts, body image, perfectionism, exams, mocked for faith, starting over). Verse picks unchanged; covers checked (3-line titles fit).
- **Change 2 (tuning, hand step from 2026-11-16):** new step key `topic_window: 40` (gen.py compares 40 eligible posts instead of 12, so favored topics win far more often; perf.py carries it into nightly steps); the 19 new When topics x1.5. Result: from 11-16 to 11-29 almost every list is a "When You..." title (was about half).
- **Research:** a quick search for current faith-carousel hook data found nothing new with data; the decision rests on our own numbers.
- **Watch:** list median views per day from 11-16 vs 11-10..11-15 (median ~440); share of lists over 500 and 1,000 views; whether new When topics (divorce, addiction, body image, caregivers...) match the original When topics. Staleness risk: watch for a decline in the When median as every list uses the same phrasing.
- **Judge after:** 2026-11-21.
- **Verdict:** pending.
- **Past entries:** 2026-11-13 night review (challenge headlines): inconclusive (first affected quiz is 11-16). 2026-11-13 kill/lean: inconclusive so far; early signs fine (11-13/11-14 lists Sick 879, Trauma 420; quiz still mostly F).

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
