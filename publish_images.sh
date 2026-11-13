#!/usr/bin/env bash
# Render posts from START_DATE for DAYS days and force-push them to the `images` branch.
# Image URLs: https://raw.githubusercontent.com/kylewatersss53/scripturespark-posts/images/<key>/<NN>.jpg
# Slots that are already published are kept exactly as they are (see make_site.py); FRESH=1 re-renders everything.
set -euo pipefail
cd "$(dirname "$0")"
START="${1:-$(TZ=America/Chicago date +%F)}"; DAYS="${2:-3}"
REPO="https://github.com/kylewatersss53/scripturespark-posts"
python3 gen.py >/dev/null
prev=$(mktemp -d)
git clone -q --depth 1 -b images "$REPO" "$prev" 2>/dev/null || echo "no published site yet; rendering everything"
PREV_SITE="$prev" python3 make_site.py "$START" "$DAYS" 2>&1 | grep -v "GET\|404\|console:" || true
rm -rf "$prev"
tmp=$(mktemp -d); cp -r site/. "$tmp"/
cd "$tmp"; git init -q -b images; git add -A
git -c user.name="Scripture Spark Bot" -c user.email="bot@scripturespark.app" commit -qm "Images from $START for $DAYS days"
git push -qf "$REPO" images:images
echo "pushed images $START +$DAYS days"
