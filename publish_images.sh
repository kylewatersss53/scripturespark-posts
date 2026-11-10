#!/usr/bin/env bash
# Render posts from START_DATE for DAYS days and force-push them to the `images` branch.
# Image URLs: https://raw.githubusercontent.com/kylewatersss53/scripturespark-posts/images/<key>/<NN>.jpg
set -euo pipefail
cd "$(dirname "$0")"
START="${1:-$(TZ=America/Chicago date +%F)}"; DAYS="${2:-5}"
python3 gen.py >/dev/null
python3 make_site.py "$START" "$DAYS" 2>&1 | grep -v "GET\|404" || true
tmp=$(mktemp -d); cp -r site/. "$tmp"/
cd "$tmp"; git init -q -b images; git add -A
git -c user.name="Scripture Spark Bot" -c user.email="bot@scripturespark.app" commit -qm "Images from $START for $DAYS days"
git push -qf "https://github.com/kylewatersss53/scripturespark-posts" images:images
echo "pushed images $START +$DAYS days"
