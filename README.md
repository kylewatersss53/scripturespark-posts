# Scripture Spark TikTok posts

Generates daily TikTok photo carousels for @scripturesparkapp and feeds them to Buffer.

- `topics/` 214 hand-picked topics (verses + chapters), every reference checked against the Berean Standard Bible (`data/BSB.json`, public domain)
- `daily/messages.txt` "Today God is saying to you" messages
- `gen.py` builds `build/library.json` (posts + 3-year schedule). Each day = [daily word, list, list, single verse, list]
- `web/engine.js` the slide renderer (also used by the Post Studio artifact)
- `make_site.py START DAYS` renders slots 7:00 / 12:00 / 19:00 into `site/` with `manifest.json` (captions + image paths)
- `publish_images.sh START DAYS` force-pushes `site/` to the `images` branch, served from raw.githubusercontent.com
