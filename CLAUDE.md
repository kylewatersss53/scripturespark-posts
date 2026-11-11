# Scripture Spark TikTok content engine

Generates TikTok photo carousels for @scripturesparkapp (promotes the Scripture Spark iOS app, "Read Scripture with someone") and schedules them through Buffer.

## Goal
Bookmarks/saves and app awareness. Post 4x daily (America/Chicago): 07:00 "Today God is saying to you" daily word (12 s video with birdsong), 12:00 and 19:00 list carousels (photo posts, no music), 16:00 Bible quiz carousel (comment/share driver: "comment your score"). Content must not feel stale: rotating topics, title phrasings, formats and colors.

## How it works
- `data/BSB.json`: Berean Standard Bible (public domain). `bible.py` parses/validates references and cleans display text (Psalm superscriptions, quote balancing).
- `topics/*.txt`: 214 hand-curated topics. Format: `@id | Subject | category | hook`, then `V ref =keyword ; ...` (verse picks, keyword must appear in BSB text as a sanity check), `C chapter ; ...`, optional `TV`/`TC` custom titles. Run `python3 library.py` to validate (must report 0 problems).
- `chapters/*.txt`: one-line summary per chapter used on chapter slides.
- `daily/messages.txt`: 100 daily-word messages `opener | body | turn | verse ref | close`, cycled without repeats.
- `quiz/*.txt` + `quiz.py`: Bible quiz banks (trivia, finish the verse, who said it, guess the book), 330 questions. Every question names a BSB reference that proves the answer; run `python3 quiz.py` to validate (must report 0 problems). The answer slide shows that verse.
- `gen.py` → `build/library.json`: all posts (V verse lists, C chapter lists, P 7-day plans, S single verse, KC/KV multi-list stacks, D daily word, Q daily quiz) and a 3-year schedule from 2026-11-10. Each schedule day = `[D, list, list, single, list, Q]`; Buffer uses slots 0,1,5,2 (07:00, 12:00, 16:00, 19:00). Quiz styles rotate T,F,W,T,B,T,F,W,B,F,T; each style's questions cycle without repeats. Quiz carousel = cover + 4 x (question, answer) + promo = 10 slides. Holidays are pinned (Easter, Thanksgiving, Advent, Christmas, etc.). `WHEN` dict gives "When You..." titles (best performers on the account).
- `web/engine.js`: canvas slide renderer shared by everything. 1080x1440 JPEG. Palettes (light pastels + NIGHT darks for daily word), per-post color mode (same / drift / mixed), app promo end slide (`web/promo.jpg`), captions (save CTA + app line + 988 line on sensitive topics + `APP_PLANS` mentions).
- `render_batch.py`: headless Chrome (Playwright, `/usr/bin/google-chrome`) renders posts via `web/harness.html`. For `D:` posts it also writes `tall.jpg`, a full-screen 1080x1920 frame (engine `opts.tall`: background stretched to fill, normal layout offset 170px down).
- Daily-word video: `make_video.py` turns `tall.jpg` into a 12 s 1080x1920 H.264/AAC MP4 with the birdsong in `web/daily_audio.m4a`, built by `make_audio.py` from `audio/daily_birds_source.wav` (owner-supplied clip, looped with crossfades, about -19 LUFS). Same audio on every daily video; to change it, replace the wav and rerun `make_audio.py`. No app promo slide in the video; the caption carries the app line.
- `make_site.py START DAYS` → `site/` + `manifest.json` (per slot: key, date, time, post, title, caption, images; daily slots also have `video` = `<key>/video.mp4`).
- `publish_images.sh START DAYS`: force-pushes `site/` to the orphan `images` branch. Public URLs: `https://raw.githubusercontent.com/kylewatersss53/scripturespark-posts/images/<key>/<NN>.jpg`.
- `build_app.py` → `build/app/` (Post Studio web app, published as a claude.ai artifact: manual daily view, library search, save slides, copy captions).

## Buffer
- Org "My organization" `6af36ee396c2cde5badc9174`, TikTok channel `scripturesparkapp` `6af36f7962b70b94b0e7bd92`. Free plan: max 10 scheduled posts, 10 images per TikTok photo post.
- Posts are created with `schedulingType: automatic`, `mode: customScheduled`. Daily slots (manifest has `video`): one video asset by URL. Carousel slots: image assets by URL. Buffer copies images at publish time, but scheduled posts reference the raw URLs until then, so the images branch must always cover every queued slot (today + 5 days).
- A daily scheduled task (8:37pm Central) runs `publish_images.sh <today> 5` and fills free slots up to 10 (with 4 posts/day the queue covers about 2.5 days).

## Conventions
- Verify every new reference with `python3 library.py`; never quote Scripture from memory.
- After engine/style changes, render samples with `render_batch.py` and look at them (`sheet.py` makes contact sheets).
- Keep the app promo slide last in every carousel (max 10 slides total). Daily-word videos have no promo slide.
- TikTok's caption, username and scroll bar cover roughly the bottom 250px of a photo post (and the bottom ~430px of the 1920 video frame). Keep slide content above `SAFE_B` (H-310) in `web/engine.js`; footers sit at `FOOT_Y`. Check new layouts against a mock overlay before shipping.
- The nightly task clones `main`; changes only reach posts once merged to `main`.
