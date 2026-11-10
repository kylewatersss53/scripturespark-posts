/* Scripture slide engine: turns a post spec into slides, captions, and 1080x1440 canvas images.
   Shared by the daily app and the batch renderer, so both always look identical. */
(function (root) {
  "use strict";
  const W = 1080, H = 1440, M = 110, CW = W - 2 * M;

  // ---------- palettes: soft skies, all light so dark serif text stays crisp ----------
  const PALETTES = [
    { name: "Lavender", top: "#ECE6FA", bot: "#BBAAE3", blobs: ["#D9CDF4", "#C6B5EC", "#F1EBFC", "#B3A0DE"], ink: "#211936", acc: "#5E479C" },
    { name: "Sky", top: "#E3EEFA", bot: "#9DBDE6", blobs: ["#C9DCF3", "#B1CBEE", "#EEF5FD", "#93B5E2"], ink: "#14233A", acc: "#2F5E96" },
    { name: "Dawn", top: "#FCEEE4", bot: "#EDB8A2", blobs: ["#F6D5C4", "#F0C4AF", "#FEF4EC", "#E8A990"], ink: "#341E16", acc: "#A04F30" },
    { name: "Sage", top: "#EEF3EA", bot: "#B5CCAC", blobs: ["#D6E4D0", "#C3D7BA", "#F5F9F2", "#A9C49F"], ink: "#1A2A1C", acc: "#44694A" },
    { name: "Rose", top: "#FAECEF", bot: "#E2B3C1", blobs: ["#F2D3DB", "#EAC1CD", "#FDF4F6", "#DCA5B5"], ink: "#33171E", acc: "#93405A" },
    { name: "Sand", top: "#F8F1E6", bot: "#DCC6A0", blobs: ["#EFE1C9", "#E6D2B1", "#FCF8F1", "#D6BD92"], ink: "#2B2215", acc: "#7F5E27" },
    { name: "Mist", top: "#EDF1F4", bot: "#B3C2D0", blobs: ["#D8E0E8", "#C5D1DC", "#F6F8FA", "#A8B9C9"], ink: "#18222D", acc: "#405A70" },
    { name: "Honey", top: "#FDF4DF", bot: "#EECB86", blobs: ["#F7E2B4", "#F3D79C", "#FEF9EC", "#EBC277"], ink: "#2E220C", acc: "#8B5E12" },
    { name: "Ocean", top: "#E3F2F2", bot: "#94C5C9", blobs: ["#C5E1E3", "#AFD4D7", "#F0F9F9", "#88BCC1"], ink: "#102A2C", acc: "#246A6F" },
    { name: "Dusk", top: "#F1EAF3", bot: "#C4AACF", blobs: ["#E2D3E8", "#D3BFDC", "#F9F4FA", "#B99CC6"], ink: "#26192C", acc: "#6A4579" },
    { name: "Peach Rose", top: "#FCE6D6", bot: "#F2B9C6", blobs: ["#F9D3C9", "#F5C2C9", "#FFF1E8", "#EFAABB"], ink: "#33191C", acc: "#A0465C" },
    { name: "Mint Sky", top: "#E2F5EC", bot: "#B9D6F0", blobs: ["#CDEBE3", "#C3DDEF", "#F2FBF7", "#A9CBEA"], ink: "#132A2C", acc: "#2D6A7A" },
    { name: "Lilac Peach", top: "#E8DDF8", bot: "#F7CDB8", blobs: ["#EED7EE", "#F3D1C6", "#F8F2FD", "#E9C1D6"], ink: "#271B30", acc: "#7A4D86" },
    { name: "Cotton Candy", top: "#F8DCEB", bot: "#C6D9F5", blobs: ["#EED7F0", "#D7D9F5", "#FCF0F7", "#BFD0F2"], ink: "#221A33", acc: "#5D4E9E" },
    { name: "Sunset", top: "#FDE3C8", bot: "#D7C2EC", blobs: ["#F8D6CF", "#E9CBE0", "#FFF3E6", "#CDB6E6"], ink: "#2B1D24", acc: "#8E4A63" },
    { name: "Seafoam", top: "#DDF3EE", bot: "#A9D8CF", blobs: ["#C5E9E1", "#B4E0D6", "#F0FAF8", "#9ACEC4"], ink: "#11292A", acc: "#24695F" },
    { name: "Butter", top: "#FEF6D8", bot: "#F6DDA6", blobs: ["#FBEEC4", "#F8E5B4", "#FFFBEE", "#F2D493"], ink: "#2C2410", acc: "#8A6416" },
    { name: "Blush Mist", top: "#F5E9EC", bot: "#D3C3D6", blobs: ["#EBDADF", "#DFD0DC", "#FBF5F6", "#CBB7CF"], ink: "#2A1C24", acc: "#7B4E66" },
  ];
  // dark "night" palettes for the daily word
  const NIGHT = [
    { name: "Midnight", top: "#0E1422", bot: "#1E2A44", glow: "#4A6BA8", ink: "#F3F1EA", acc: "#E7C98A" },
    { name: "Plum Night", top: "#170F1F", bot: "#33203F", glow: "#8A5BA6", ink: "#F5EFF6", acc: "#E9C2A2" },
    { name: "Forest Night", top: "#0C1712", bot: "#1C3328", glow: "#4E8A6A", ink: "#EFF4EE", acc: "#D9C98C" },
    { name: "Charcoal", top: "#111111", bot: "#262626", glow: "#5C5C5C", ink: "#F4F2EE", acc: "#D8C08A" },
    { name: "Wine", top: "#1A0C10", bot: "#3A1822", glow: "#9A4A5C", ink: "#F7EEEF", acc: "#EBC59B" },
  ];
  // order used for color "drift" across slides (neighbors blend nicely)
  const WHEEL = [0, 9, 4, 12, 14, 2, 11, 7, 17, 5, 3, 13, 6, 8, 15, 16, 1, 10];

  const SERIF = '"Newsreader", Georgia, "Times New Roman", serif';
  const SANS = '"Inter", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif';

  // ---------- deterministic randomness ----------
  function hash(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function rng(seed) {
    let s = seed >>> 0 || 1;
    return function () { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
  }

  // ---------- fonts ----------
  const FONT_FILES = [
    ["Newsreader", "newsreader-latin-400-normal.woff2", "400", "normal"],
    ["Newsreader", "newsreader-latin-400-italic.woff2", "400", "italic"],
    ["Newsreader", "newsreader-latin-500-normal.woff2", "500", "normal"],
    ["Newsreader", "newsreader-latin-600-normal.woff2", "600", "normal"],
    ["Inter", "inter-latin-400-normal.woff2", "400", "normal"],
    ["Inter", "inter-latin-500-normal.woff2", "500", "normal"],
    ["Inter", "inter-latin-600-normal.woff2", "600", "normal"],
  ];
  async function loadFonts(base) {
    // fetch the bytes ourselves so it works anywhere same-origin fetch works
    const jobs = FONT_FILES.map(async ([fam, file, weight, style]) => {
      try {
        const buf = await (await fetch(base + file)).arrayBuffer();
        const ff = new FontFace(fam, buf, { weight, style });
        await ff.load(); document.fonts.add(ff); return true;
      } catch (e) { return false; }
    });
    const ok = await Promise.all(jobs);
    return ok.every(Boolean);
  }

  // ---------- text helpers ----------
  function font(ctx, family, size, weight = 400, style = "normal") {
    ctx.font = `${style} ${weight} ${size}px ${family}`;
  }
  function wrap(ctx, text, maxW) {
    const words = String(text).split(/\s+/).filter(Boolean);
    const lines = [];
    let line = "";
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width <= maxW || !line) { line = test; }
      else { lines.push(line); line = w; }
    }
    if (line) lines.push(line);
    // avoid a lonely last word when possible
    if (lines.length >= 2) {
      const last = lines[lines.length - 1], prev = lines[lines.length - 2];
      if (!last.includes(" ") && prev.split(" ").length >= 3) {
        const pw = prev.split(" "); const moved = pw.pop();
        const cand = moved + " " + last;
        if (ctx.measureText(cand).width <= maxW) { lines[lines.length - 2] = pw.join(" "); lines[lines.length - 1] = cand; }
      }
    }
    return lines;
  }
  function fit(ctx, text, opt) {
    const { family, weight = 400, style = "normal", maxW, maxH, max, min, lh } = opt;
    for (let size = max; size >= min; size -= 2) {
      font(ctx, family, size, weight, style);
      const lines = wrap(ctx, text, maxW);
      if (lines.length * size * lh <= maxH) return { size, lines, height: lines.length * size * lh };
    }
    font(ctx, family, min, weight, style);
    const lines = wrap(ctx, text, maxW);
    return { size: min, lines, height: lines.length * min * lh };
  }
  function drawLines(ctx, lines, x, y, size, lh, align = "left") {
    ctx.textAlign = align;
    ctx.textBaseline = "alphabetic";
    lines.forEach((ln, i) => ctx.fillText(ln, x, y + size * 0.82 + i * size * lh));
  }
  function spaced(ctx, text, x, y, spacing, align = "left") {
    // letter-spaced small caps-style label
    const chars = [...text];
    let total = 0;
    chars.forEach(c => { total += ctx.measureText(c).width + spacing; });
    total -= spacing;
    let cx = align === "center" ? x - total / 2 : align === "right" ? x - total : x;
    ctx.textAlign = "left";
    chars.forEach(c => { ctx.fillText(c, cx, y); cx += ctx.measureText(c).width + spacing; });
    return total;
  }
  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }

  // ---------- background ----------
  let grainTile = null;
  function grain() {
    if (grainTile) return grainTile;
    const c = document.createElement("canvas"); c.width = c.height = 160;
    const g = c.getContext("2d"); const img = g.createImageData(160, 160); const r = rng(99);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = 128 + (r() - 0.5) * 255;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0); grainTile = c; return c;
  }
  function background(ctx, pal, seed) {
    const r = rng(seed);
    const lg = ctx.createLinearGradient(W * (0.2 + r() * 0.3), 0, W * (0.5 + r() * 0.3), H);
    lg.addColorStop(0, pal.top); lg.addColorStop(0.55, pal.blobs[0]); lg.addColorStop(1, pal.bot);
    ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    // soft color fields
    for (let i = 0; i < 6; i++) {
      const x = r() * W, y = r() * H, rad = 360 + r() * 520;
      const col = pal.blobs[(i + 1) % pal.blobs.length];
      const rg = ctx.createRadialGradient(x, y, 0, x, y, rad);
      rg.addColorStop(0, hexA(col, 0.7)); rg.addColorStop(1, hexA(col, 0));
      ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    }
    // clouds: bands of soft white puffs
    const bands = 2 + Math.floor(r() * 2);
    for (let c = 0; c < bands; c++) {
      const cx = r() * W, cy = H * (0.1 + r() * 0.85), n = 9 + Math.floor(r() * 8), spread = 500 + r() * 400;
      for (let i = 0; i < n; i++) {
        const x = cx + (r() - 0.5) * spread, y = cy + (r() - 0.5) * 150 - Math.abs(r() - 0.5) * 60, rad = 70 + r() * 160;
        const rg = ctx.createRadialGradient(x, y, 0, x, y, rad);
        rg.addColorStop(0, "rgba(255,255,255,0.42)"); rg.addColorStop(0.55, "rgba(255,255,255,0.2)"); rg.addColorStop(1, "rgba(255,255,255,0)");
        ctx.fillStyle = rg; ctx.beginPath(); ctx.ellipse(x, y, rad * 1.7, rad, 0, 0, Math.PI * 2); ctx.fill();
      }
    }
    // light veil behind the text column for legibility
    const veil = ctx.createLinearGradient(0, 0, W, 0);
    veil.addColorStop(0, "rgba(255,255,255,0.22)"); veil.addColorStop(0.75, "rgba(255,255,255,0.12)"); veil.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = veil; ctx.fillRect(0, 0, W, H);
    // film grain
    ctx.save(); ctx.globalAlpha = 0.05; ctx.globalCompositeOperation = "overlay";
    ctx.fillStyle = ctx.createPattern(grain(), "repeat"); ctx.fillRect(0, 0, W, H); ctx.restore();
  }

  function header(ctx, pal, opts) {
    if (!opts.handle) return;
    font(ctx, SERIF, 34, 400); ctx.fillStyle = hexA(pal.ink, 0.62);
    spaced(ctx, opts.handle, W / 2, 92, 3, "center");
  }
  function footer(ctx, pal, text) {
    font(ctx, SANS, 24, 500); ctx.fillStyle = hexA(pal.ink, 0.42);
    spaced(ctx, text, W / 2, H - 70, 3, "center");
  }
  function rule(ctx, pal, x, y, w) {
    ctx.fillStyle = hexA(pal.acc, 0.45); ctx.fillRect(x, y, w, 3);
  }

  // ---------- slide layouts ----------
  function drawList(ctx, pal, s, opts) {
    const LM = 80, TW = W - 2 * LM;
    const topY = opts.handle ? 150 : 110;
    ctx.save(); ctx.letterSpacing = "-4px";
    // prefer a big two-line title like the feed; fall back to three lines
    let title = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: TW, maxH: 2 * 0.98 * 140 + 1, max: 140, min: 118, lh: 0.98 });
    if (title.lines.length > 2) title = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: TW, maxH: 3 * 0.98 * 120 + 1, max: 120, min: 76, lh: 0.98 });
    ctx.fillStyle = pal.ink; font(ctx, SERIF, title.size, 500);
    drawLines(ctx, title.lines, LM, topY, title.size, 0.98); ctx.restore();
    let y = topY + title.height + 40;
    const n = s.items.length, avail = H - 80 - y;
    const row = Math.min(118, avail / n);
    const size = Math.min(84, Math.round(row * 0.84));
    const isDay = s.items[0] && /^Day/.test(s.items[0][0]);
    const numX = isDay ? LM + 30 : LM + 92, labX = isDay ? LM + 230 : LM + 140;
    s.items.forEach(([num, label], i) => {
      const by = y + i * row + size * 0.85;
      if (isDay) { font(ctx, SANS, Math.round(size * 0.52), 600); ctx.fillStyle = pal.acc; ctx.textAlign = "left"; spaced(ctx, num.toUpperCase(), numX, by - size * 0.12, 2.5); }
      else { font(ctx, SERIF, size, 400); ctx.fillStyle = pal.ink; ctx.textAlign = "right"; ctx.fillText(num, numX, by); }
      font(ctx, SERIF, size, 400); ctx.fillStyle = pal.ink; ctx.textAlign = "left";
      ctx.letterSpacing = "-1px";
      let lab = label; while (ctx.measureText(lab).width > W - M - labX && lab.length > 4) lab = lab.slice(0, -2) + "…";
      ctx.fillText(lab, labX, by); ctx.letterSpacing = "0px";
    });
  }

  function drawPairs(ctx, pal, s, opts) {
    // s.blocks: [{kicker, head?, body, italic?}]
    const top = opts.handle ? 190 : 130, bottom = H - 130;
    const n = s.blocks.length, gap = 100;
    const avail = bottom - top - gap * (n - 1);
    const wc = s.blocks.map(b => Math.max(8, b.body.split(/\s+/).length));
    const wsum = wc.reduce((a, x) => a + x, 0);
    const maxSize = n === 1 ? (s.blocks[0].head ? 64 : 72) : (s.blocks[0].head ? 60 : 62);
    // share height by length, then use one common size so the slide reads evenly
    let size = maxSize;
    s.blocks.forEach((b, i) => {
      const fixed = 64 + (b.head ? 92 * 1.1 + 18 : 0);
      const share = (avail - s.blocks.reduce((a, x) => a + 64 + (x.head ? 92 * 1.1 + 18 : 0), 0)) * wc[i] / wsum;
      const f = fit(ctx, b.body, { family: SERIF, weight: 400, style: b.italic ? "italic" : "normal", maxW: CW, maxH: share, max: maxSize, min: 30, lh: 1.34 });
      size = Math.min(size, f.size);
    });
    const fits = s.blocks.map(b => {
      font(ctx, SERIF, size, 400, b.italic ? "italic" : "normal");
      const lines = wrap(ctx, b.body, CW);
      const body = { size, lines, height: lines.length * size * 1.34 };
      return { b, body, h: 64 + (b.head ? 92 * 1.1 + 18 : 0) + body.height };
    });
    const total = fits.reduce((a, f) => a + f.h, 0) + gap * (n - 1);
    let y = top + Math.max(0, (bottom - top - total) / 2);
    fits.forEach((f, i) => {
      font(ctx, SANS, 30, 600); ctx.fillStyle = pal.acc; spaced(ctx, f.b.kicker.toUpperCase(), M, y + 28, 3);
      y += 64;
      if (f.b.head) {
        font(ctx, SERIF, 92, 500); ctx.fillStyle = pal.ink; ctx.textAlign = "left";
        let hd = f.b.head; while (ctx.measureText(hd).width > CW && hd.length > 4) hd = hd.slice(0, -2) + "…";
        ctx.fillText(hd, M, y + 76);
        y += 92 * 1.1 + 18;
      }
      font(ctx, SERIF, f.body.size, 400, f.b.italic ? "italic" : "normal"); ctx.fillStyle = pal.ink;
      drawLines(ctx, f.body.lines, M, y, f.body.size, 1.34);
      y += f.body.height;
      if (i < n - 1) { rule(ctx, pal, M, y + gap / 2 - 2, 120); y += gap; }
    });
  }

  function drawHook(ctx, pal, s, opts) {
    const t = fit(ctx, s.text, { family: SERIF, weight: 500, maxW: CW, maxH: 760, max: 112, min: 64, lh: 1.08 });
    const y = (H - t.height) / 2 - 40;
    ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500);
    ctx.save(); ctx.letterSpacing = "-1px"; drawLines(ctx, t.lines, M, y, t.size, 1.08); ctx.restore();
    if (s.sub) {
      font(ctx, SANS, 30, 500); ctx.fillStyle = hexA(pal.ink, 0.55);
      const sub = wrap(ctx, s.sub, CW);
      drawLines(ctx, sub, M, y + t.height + 50, 30, 1.5);
    }
    footer(ctx, pal, s.foot || "SWIPE  →");
  }

  function drawVerse(ctx, pal, s) {
    const body = fit(ctx, s.text, { family: SERIF, weight: 400, maxW: CW, maxH: 860, max: 76, min: 40, lh: 1.32 });
    const total = body.height + 110;
    let y = (H - total) / 2 - 30;
    // big opening mark
    font(ctx, SERIF, 220, 500); ctx.fillStyle = hexA(pal.acc, 0.18); ctx.textAlign = "left"; ctx.fillText("“", M - 24, y + 120);
    ctx.fillStyle = pal.ink; font(ctx, SERIF, body.size, 400); drawLines(ctx, body.lines, M, y, body.size, 1.32);
    y += body.height + 56;
    rule(ctx, pal, M, y, 70);
    font(ctx, SANS, 32, 600); ctx.fillStyle = pal.acc; spaced(ctx, s.ref.toUpperCase(), M + 96, y + 13, 2.5);
  }

  function drawCta(ctx, pal, s, opts) {
    const t = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: CW, maxH: 420, max: 124, min: 70, lh: 1.04 });
    let y = H * 0.40 - t.height / 2;
    ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500);
    ctx.save(); ctx.letterSpacing = "-1px"; drawLines(ctx, t.lines, M, y, t.size, 1.04); ctx.restore();
    y += t.height + 50;
    const sub = fit(ctx, s.sub, { family: SERIF, weight: 400, style: "italic", maxW: CW - 40, maxH: 300, max: 58, min: 38, lh: 1.3 });
    ctx.fillStyle = hexA(pal.ink, 0.78); font(ctx, SERIF, sub.size, 400, "italic"); drawLines(ctx, sub.lines, M, y, sub.size, 1.3);
    y += sub.height + 70;
    rule(ctx, pal, M, y, 120);
    if (opts.handle) { font(ctx, SANS, 34, 600); ctx.fillStyle = pal.acc; ctx.textAlign = "left"; spaced(ctx, opts.handle, M, y + 80, 1.5); }
    footer(ctx, pal, "SCRIPTURE: BEREAN STANDARD BIBLE");
  }

  function drawStackCover(ctx, pal, s, opts) {
    const t = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: CW, maxH: 560, max: 116, min: 70, lh: 1.05 });
    let y = H * 0.36 - t.height / 2;
    ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500);
    ctx.save(); ctx.letterSpacing = "-1.5px"; drawLines(ctx, t.lines, M, y, t.size, 1.05); ctx.restore();
    y += t.height + 60; rule(ctx, pal, M, y, 120); y += 50;
    font(ctx, SERIF, 52, 400, "italic"); ctx.fillStyle = hexA(pal.ink, 0.74);
    s.items.forEach((it, i) => { ctx.textAlign = "left"; ctx.fillText(it.charAt(0).toUpperCase() + it.slice(1), M, y + 48 + i * 70); });
    footer(ctx, pal, "SWIPE  →");
  }

  // ---------- content: post spec -> slides ----------
  const CTAS = [
    ["Save this for later.", "You'll want it the next time life gets heavy."],
    ["Send this to someone who needs it.", "One verse can change someone's whole day."],
    ["Which one spoke to you?", "Tell me in the comments. I read every one."],
    ["Read one tonight.", "Start small. God meets you in the pages."],
    ["Save this and come back to it.", "Screenshot your favorite one."],
    ["Share this with a friend.", "Someone in your life needs this today."],
  ];
  function cta(post, opt) {
    const c = CTAS[hash(post.id + "cta") % CTAS.length];
    return { kind: "cta", title: opt && opt.title || c[0], sub: opt && opt.sub || c[1] };
  }

  function pairs(arr, maxBlocks = 2, budget = 70, longWords = 40) {
    // group blocks onto slides by word budget so short verses share a slide and long ones get room
    const words = b => b.body.split(/\s+/).length + (b.head ? 8 : 0);
    const out = [];
    let cur = [], used = 0;
    arr.forEach(b => {
      const w = words(b);
      if (w > longWords) { if (cur.length) out.push(cur); out.push([b]); cur = []; used = 0; return; }
      if (cur.length && (cur.length >= maxBlocks || used + w > budget)) { out.push(cur); cur = []; used = 0; }
      cur.push(b); used += w;
    });
    if (cur.length) {
      // fold a lonely short tail into the previous slide when it fits
      const prev = out[out.length - 1];
      if (cur.length === 1 && prev && prev.length < maxBlocks && prev.reduce((a, x) => a + words(x), 0) + used <= budget + 10) prev.push(cur[0]);
      else out.push(cur);
    }
    return out;
  }

  const PROMO_SLIDE = { kind: "promo" };
  const APP_PLANS = { anxiety: "Overcoming Anxiety", overthinking: "Overcoming Anxiety", panic: "Overcoming Anxiety", stress: "Overcoming Anxiety",
    couples: "Relationships in Christ", marriage: "Relationships in Christ", dating: "Relationships in Christ", engaged: "Relationships in Christ",
    marriagestruggles: "Relationships in Christ", purpose: "Finding Purpose", career: "Finding Purpose", unqualified: "Finding Purpose", stuck: "Finding Purpose" };
  function even(arr, per) {
    // fewest slides of at most `per`, split evenly (10 -> 4,3,3)
    const k = Math.ceil(arr.length / per), out = [];
    let i = 0;
    for (let g = 0; g < k; g++) { const n = Math.ceil((arr.length - i) / (k - g)); out.push(arr.slice(i, i + n)); i += n; }
    return out;
  }
  function buildSlides(post, lib) {
    const T = lib.topics, V = lib.verses, C = lib.chapters;
    const num = i => `${i + 1}.`;
    if (post.t === "V") {
      const t = T[post.k]; const vs = t.v.slice(0, 10);
      const slides = [{ kind: "list", title: post.ti, items: vs.map((v, i) => [num(i), v]) }];
      pairs(vs.map((v, i) => ({ kicker: `${i + 1} · ${v}`, body: V[v] }))).forEach(g => slides.push({ kind: "pairs", blocks: g }));
      slides.push(PROMO_SLIDE);
      return slides;
    }
    if (post.t === "C") {
      const t = T[post.k]; const cs = t.c.slice(0, 10);
      const slides = [{ kind: "list", title: post.ti, items: cs.map((c, i) => [num(i), c]) }];
      even(cs.map((c, i) => ({ kicker: `Chapter ${i + 1}`, head: c, body: C[c] || "", italic: true })), 3).forEach(g => slides.push({ kind: "pairs", blocks: g }));
      slides.push(PROMO_SLIDE);
      return slides;
    }
    if (post.t === "P") {
      const t = T[post.k]; const cs = t.c.slice(0, 7);
      const slides = [{ kind: "list", title: post.ti, items: cs.map((c, i) => [`Day ${i + 1}`, c]) }];
      even(cs.map((c, i) => ({ kicker: `Day ${i + 1}`, head: c, body: C[c] || "", italic: true })), 3).forEach(g => slides.push({ kind: "pairs", blocks: g }));
      slides.push(PROMO_SLIDE);
      return slides;
    }
    if (post.t === "D") {
      const m = lib.daily[post.m];
      const [y, mo, d] = post.date.split("-").map(Number);
      const dateLabel = new Date(y, mo - 1, d).toLocaleDateString("en-US", { month: "long" }) + " " + ordinal(d);
      return [{ kind: "daily", dateLabel, opener: m.o, body: m.b, turn: m.t, verse: m.v, ref: m.r, close: m.c }, PROMO_SLIDE];
    }
    if (post.t === "S") {
      return [
        { kind: "hook", text: post.ti },
        { kind: "verse", text: V[post.v], ref: `${post.v} · BSB` },
        PROMO_SLIDE,
      ];
    }
    if (post.t === "KC" || post.t === "KV") {
      const isC = post.t === "KC";
      const slides = [];
      post.ks.forEach(k => {
        const t = T[k];
        const about = t.about;
        const list = isC ? t.c.slice(0, 10) : t.v.slice(0, 10);
        const ti = isC ? (t.tc || (t.when ? `Best Chapters to Read ${t.when}` : `Best Chapters ${about ? "About" : "for"} ${t.s}`))
                       : (t.tv || (t.when ? `Bible Verses for ${t.when}` : `Bible Verses ${about ? "About" : "for"} ${t.s}`));
        slides.push({ kind: "list", title: ti, items: list.map((x, i) => [num(i), x]) });
      });
      slides.push(PROMO_SLIDE);
      return slides;
    }
    return [];
  }

  function caption(post, lib) {
    const T = lib.topics, V = lib.verses;
    const base = ["bible", "bibleverse", "christian", "jesus", "scripturespark", "christiantiktok"];
    let topicTags = [];
    let care = false;
    const ks = post.ks || [post.k];
    ks.forEach(k => { const t = T[k]; if (t) { topicTags = topicTags.concat(t.tags || []); care = care || t.care; } });
    const tags = [...new Set([...topicTags.slice(0, 3), ...base])].slice(0, 8).map(t => "#" + t).join(" ");
    let body;
    const cap = post.cap || post.ti;
    if (post.t === "D") {
      const m = lib.daily[post.m];
      return `Today God is saying to you: ${m.o} 🤍\n\n“${m.v}” ${m.r}\n\nSave this for when you need it, and send it to someone who needs to hear it today.\n\nWant someone to read the Bible with? Search “Scripture Spark” in the App Store.\n\n#godisspeaking #dailydevotional #bibleverse #christian #jesus #scripturespark #christiantiktok`;
    }
    if (post.t === "V") body = `${cap} 🔖\n\nSave this so it's here the next time you need it. Which verse is yours? Comment the number.`;
    else if (post.t === "C") body = `${cap} 📖\n\nSave this for your next quiet time. Which chapter are you reading first?`;
    else if (post.t === "P") body = `${cap} 📖\n\nOne chapter a day for 7 days. Save this and start tomorrow. Comment “Day 1” when you begin.`;
    else if (post.t === "S") body = `${post.ti}\n\n“${V[post.v]}”\n${post.v}\n\nSave this for the day you need it. 🔖`;
    else body = `${cap} 📖\n\nSwipe through and save the one you need. Which list are you starting with?`;
    const plan = ks.map(k => APP_PLANS[k]).find(Boolean);
    if (plan) body += `\n\nTry the 14-day “${plan}” plan in the Scripture Spark app with a friend.`;
    body += `\n\nWant someone to read these with? Scripture Spark lets you read the Bible together with a friend or your spouse. Search “Scripture Spark” in the App Store.`;
    if (care) body += `\n\nIf you're struggling, you don't have to carry it alone. In the US you can call or text 988 any time.`;
    body += `\n\n${tags}`;
    return body;
  }

  // ---------- daily word ----------
  function ordinal(n) { const s = ["th", "st", "nd", "rd"], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); }
  function nightBackground(ctx, pal, seed) {
    const r = rng(seed);
    const lg = ctx.createLinearGradient(0, 0, W * 0.4, H);
    lg.addColorStop(0, pal.top); lg.addColorStop(1, pal.bot);
    ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 3; i++) {
      const x = r() * W, y = r() * H, rad = 420 + r() * 420;
      const rg = ctx.createRadialGradient(x, y, 0, x, y, rad);
      rg.addColorStop(0, hexA(pal.glow, 0.32)); rg.addColorStop(1, hexA(pal.glow, 0));
      ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    }
    // a few faint stars
    for (let i = 0; i < 60; i++) { ctx.fillStyle = `rgba(255,255,255,${0.08 + r() * 0.25})`; ctx.beginPath(); ctx.arc(r() * W, r() * H * 0.6, r() * 1.8 + 0.4, 0, 7); ctx.fill(); }
    ctx.save(); ctx.globalAlpha = 0.06; ctx.globalCompositeOperation = "overlay";
    ctx.fillStyle = ctx.createPattern(grain(), "repeat"); ctx.fillRect(0, 0, W, H); ctx.restore();
  }
  function drawDaily(ctx, pal, s, opts) {
    const LM = 100, TW = W - 2 * LM;
    // measure everything at a common scale, shrink until it fits
    const parts = [
      { t: s.opener, fam: SERIF, w: 500, st: "normal", k: 1.5, lh: 1.08, gap: 0.9, color: pal.ink },
      { t: s.body + " " + s.turn, fam: SERIF, w: 400, st: "normal", k: 0.95, lh: 1.38, gap: 0.9, color: hexA(pal.ink, 0.88) },
      { t: "“" + s.verse + "”", fam: SERIF, w: 400, st: "italic", k: 0.95, lh: 1.38, gap: 0.35, color: pal.ink },
      { t: "— " + s.ref, fam: SANS, w: 600, st: "normal", k: 0.6, lh: 1.3, gap: 1.0, color: pal.acc, spaced: true },
      { t: s.close, fam: SERIF, w: 500, st: "normal", k: 1.05, lh: 1.25, gap: 0, color: pal.ink },
    ];
    const top = 320, bottom = H - 120;
    let base = 64, laid;
    for (; base >= 28; base -= 1) {
      let y = 0; laid = [];
      for (const p of parts) {
        const size = Math.round(base * p.k);
        font(ctx, p.fam, size, p.w, p.st);
        const lines = p.spaced ? [p.t.toUpperCase()] : wrap(ctx, p.t, TW);
        laid.push({ p, size, lines, y }); y += lines.length * size * p.lh + base * p.gap * 1.6;
      }
      if (y <= bottom - top) { laid.total = y; break; }
    }
    // header
    font(ctx, SANS, 34, 600); ctx.fillStyle = pal.acc; spaced(ctx, s.dateLabel.toUpperCase(), W / 2, 150, 6, "center");
    font(ctx, SERIF, 46, 400, "italic"); ctx.fillStyle = hexA(pal.ink, 0.8); ctx.textAlign = "center"; ctx.fillText("God is saying to you today:", W / 2, 232);
    ctx.fillStyle = hexA(pal.acc, 0.6); ctx.fillRect(W / 2 - 40, 268, 80, 3);
    const y0 = top + Math.max(0, (bottom - top - laid.total) / 2) * 0.85;
    laid.forEach(({ p, size, lines, y }) => {
      font(ctx, p.fam, size, p.w, p.st); ctx.fillStyle = p.color;
      if (p.spaced) { spaced(ctx, lines[0], LM, y0 + y + size * 0.85, 3); return; }
      drawLines(ctx, lines, LM, y0 + y, size, p.lh, "left");
    });
    if (opts.handle) { font(ctx, SERIF, 30, 400); ctx.fillStyle = hexA(pal.ink, 0.5); spaced(ctx, opts.handle, W / 2, H - 60, 3, "center"); }
  }
  function drawDailyLight(ctx, pal, s, opts) {
    const nightish = { ink: pal.ink, acc: pal.acc };
    drawDaily(ctx, nightish, s, opts);
  }

  // ---------- end slide (app promo) ----------
  let PROMO = null;
  function setPromo(img) { PROMO = img; }
  function loadPromo(src) {
    return new Promise(res => { const im = new Image(); im.onload = () => { PROMO = im; res(true); }; im.onerror = () => res(false); im.src = src; });
  }
  function drawPromo(ctx, pal) {
    if (PROMO) {
      const s = Math.max(W / PROMO.width, H / PROMO.height);
      const w = PROMO.width * s, h = PROMO.height * s;
      ctx.drawImage(PROMO, (W - w) / 2, (H - h) / 2, w, h);
      return;
    }
    const t = fit(ctx, "Read Scripture with someone.", { family: SERIF, weight: 500, maxW: CW, maxH: 400, max: 120, min: 70, lh: 1.02 });
    ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500); drawLines(ctx, t.lines, W / 2, H * 0.36, t.size, 1.02, "center");
    font(ctx, SERIF, 54, 400); ctx.textAlign = "center"; ctx.fillText("“Scripture Spark” in the App Store.", W / 2, H * 0.36 + t.height + 90);
  }

  // ---------- render ----------
  function paletteFor(post) { return PALETTES[hash(post.id) % PALETTES.length]; }
  function paletteForSlide(post, index) {
    const h = hash(post.id), mode = h % 10;
    if (index === 0 || mode < 4) return PALETTES[h % PALETTES.length];            // same color all the way through
    const start = WHEEL.indexOf(h % PALETTES.length);
    if (mode < 7) return PALETTES[WHEEL[(start + index) % WHEEL.length]];           // gentle drift slide to slide
    return PALETTES[hash(post.id + ":" + index) % PALETTES.length];                 // every slide different
  }

  // opts.tall (daily word only): 1080x1920 frame for the daily video. The background is
  // stretched to fill the full height and the normal 1080x1440 layout sits TALL_Y px down,
  // clear of TikTok's top tabs and bottom caption overlay.
  const TALL_H = 1920, TALL_Y = 170;
  function renderSlide(slide, post, index, opts = {}) {
    const tall = !!opts.tall && slide.kind === "daily";
    const c = document.createElement("canvas"); c.width = W; c.height = tall ? TALL_H : H;
    const ctx = c.getContext("2d");
    const pal = opts.palette != null ? PALETTES[opts.palette] : paletteForSlide(post, index);
    if (slide.kind === "daily") {
      const h = hash(post.id), night = h % 5 < 3;
      const p = night ? NIGHT[h % NIGHT.length] : PALETTES[h % PALETTES.length];
      if (tall) { ctx.save(); ctx.scale(1, TALL_H / H); }
      night ? nightBackground(ctx, p, h) : background(ctx, p, h);
      if (tall) { ctx.restore(); ctx.translate(0, TALL_Y); }
      night ? drawDaily(ctx, p, slide, opts) : drawDailyLight(ctx, p, slide, opts);
      return c;
    }
    background(ctx, pal, hash(post.id) + index * 7919);
    if (slide.kind !== "cta" && slide.kind !== "promo") header(ctx, pal, opts);
    if (slide.kind === "list") drawList(ctx, pal, slide, opts);
    else if (slide.kind === "pairs") drawPairs(ctx, pal, slide, opts);
    else if (slide.kind === "hook") drawHook(ctx, pal, slide, opts);
    else if (slide.kind === "verse") drawVerse(ctx, pal, slide, opts);
    else if (slide.kind === "cta") drawCta(ctx, pal, slide, opts);
    else if (slide.kind === "stack") drawStackCover(ctx, pal, slide, opts);
    else if (slide.kind === "promo") drawPromo(ctx, pal);
    return c;
  }

  root.ScriptureEngine = { W, H, PALETTES, loadFonts, loadPromo, setPromo, buildSlides, caption, renderSlide, paletteFor, hash };
})(typeof window !== "undefined" ? window : globalThis);
