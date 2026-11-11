/* Scripture slide engine: turns a post spec into slides, captions, and 1080x1440 canvas images.
   Shared by the daily app and the batch renderer, so both always look identical. */
(function (root) {
  "use strict";
  const W = 1080, H = 1440, M = 110, CW = W - 2 * M;
  // TikTok draws the caption, username and scroll bar over roughly the bottom 250px of a photo post.
  // Everything that matters ends above SAFE_B; the small "swipe" footer sits just above the overlay.
  const SAFE_B = H - 310, FOOT_Y = H - 262;

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
    spaced(ctx, text, W / 2, FOOT_Y, 3, "center");
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
    let title = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: TW, maxH: 2 * 0.98 * 124 + 1, max: 124, min: 104, lh: 0.98 });
    if (title.lines.length > 2) title = fit(ctx, s.title, { family: SERIF, weight: 500, maxW: TW, maxH: 3 * 0.98 * 106 + 1, max: 106, min: 72, lh: 0.98 });
    ctx.fillStyle = pal.ink; font(ctx, SERIF, title.size, 500);
    drawLines(ctx, title.lines, LM, topY, title.size, 0.98); ctx.restore();
    let y = topY + title.height + 36;
    const n = s.items.length, avail = SAFE_B - y;
    const row = Math.min(104, avail / n);
    const size = Math.min(72, Math.round(row * 0.82));
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
    const top = opts.handle ? 180 : 130, bottom = SAFE_B;
    const n = s.blocks.length, gap = 84, HEAD = 80;
    const avail = bottom - top - gap * (n - 1);
    const wc = s.blocks.map(b => Math.max(8, b.body.split(/\s+/).length));
    const wsum = wc.reduce((a, x) => a + x, 0);
    const maxSize = n === 1 ? (s.blocks[0].head ? 64 : 72) : (s.blocks[0].head ? 60 : 62);
    // share height by length, then use one common size so the slide reads evenly
    let size = maxSize;
    s.blocks.forEach((b, i) => {
      const fixed = 64 + (b.head ? HEAD * 1.1 + 16 : 0);
      const share = (avail - s.blocks.reduce((a, x) => a + 64 + (x.head ? HEAD * 1.1 + 16 : 0), 0)) * wc[i] / wsum;
      const f = fit(ctx, b.body, { family: SERIF, weight: 400, style: b.italic ? "italic" : "normal", maxW: CW, maxH: share, max: maxSize, min: 30, lh: 1.34 });
      size = Math.min(size, f.size);
    });
    const fits = s.blocks.map(b => {
      font(ctx, SERIF, size, 400, b.italic ? "italic" : "normal");
      const lines = wrap(ctx, b.body, CW);
      const body = { size, lines, height: lines.length * size * 1.34 };
      return { b, body, h: 64 + (b.head ? HEAD * 1.1 + 16 : 0) + body.height };
    });
    const total = fits.reduce((a, f) => a + f.h, 0) + gap * (n - 1);
    let y = top + Math.max(0, (bottom - top - total) / 2);
    fits.forEach((f, i) => {
      font(ctx, SANS, 30, 600); ctx.fillStyle = pal.acc; spaced(ctx, f.b.kicker.toUpperCase(), M, y + 28, 3);
      y += 64;
      if (f.b.head) {
        font(ctx, SERIF, HEAD, 500); ctx.fillStyle = pal.ink; ctx.textAlign = "left";
        let hd = f.b.head; while (ctx.measureText(hd).width > CW && hd.length > 4) hd = hd.slice(0, -2) + "…";
        ctx.fillText(hd, M, y + HEAD * 0.82);
        y += HEAD * 1.1 + 16;
      }
      font(ctx, SERIF, f.body.size, 400, f.b.italic ? "italic" : "normal"); ctx.fillStyle = pal.ink;
      drawLines(ctx, f.body.lines, M, y, f.body.size, 1.34);
      y += f.body.height;
      if (i < n - 1) { rule(ctx, pal, M, y + gap / 2 - 2, 120); y += gap; }
    });
  }

  function drawHook(ctx, pal, s, opts) {
    const t = fit(ctx, s.text, { family: SERIF, weight: 500, maxW: CW, maxH: 760, max: 112, min: 64, lh: 1.08 });
    const y = (150 + SAFE_B - t.height) / 2 - 30;
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
    const body = fit(ctx, s.text, { family: SERIF, weight: 400, maxW: CW, maxH: 780, max: 74, min: 40, lh: 1.32 });
    const total = body.height + 110;
    let y = (150 + SAFE_B - total) / 2;
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

  // ---------- quiz ----------
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  // words of `text`, flagging the ones inside the highlighted span (first occurrence of `hl`, or at `pos`)
  function richTokens(text, hl, pos) {
    let a = -1, b = -1;
    if (hl) { a = pos != null ? pos : text.indexOf(hl); if (a >= 0) b = a + hl.length; }
    const out = []; const re = /\S+/g; let m;
    while ((m = re.exec(text))) out.push({ t: m[0], hl: a >= 0 && m.index < b && m.index + m[0].length > a });
    return out;
  }
  function layoutRich(ctx, toks, family, size, style, maxW) {
    const lines = []; let line = [], w = 0;
    const space = (font(ctx, family, size, 400, style), ctx.measureText(" ").width);
    toks.forEach(tk => {
      font(ctx, family, size, tk.hl ? 600 : 400, style);
      const tw = ctx.measureText(tk.t).width;
      if (line.length && w + space + tw > maxW) { lines.push(line); line = []; w = 0; }
      w += (line.length ? space : 0) + tw; line.push({ ...tk, w: tw });
    });
    if (line.length) lines.push(line);
    return { lines, space };
  }
  function fitRich(ctx, text, hl, pos, o) {
    const toks = richTokens(text, hl, pos);
    for (let size = o.max; size >= o.min; size -= 2) {
      const L = layoutRich(ctx, toks, o.family, size, o.style || "normal", o.maxW);
      if (L.lines.length * size * o.lh <= o.maxH) return { ...L, size, height: L.lines.length * size * o.lh };
    }
    const L = layoutRich(ctx, toks, o.family, o.min, o.style || "normal", o.maxW);
    return { ...L, size: o.min, height: L.lines.length * o.min * o.lh };
  }
  function drawRich(ctx, R, x, y, o, ink, acc, align = "left") {
    ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    R.lines.forEach((ln, i) => {
      const lw = ln.reduce((a, tk, j) => a + tk.w + (j ? R.space : 0), 0);
      let cx = align === "center" ? x - lw / 2 : x;
      const by = y + R.size * 0.82 + i * R.size * o.lh;
      ln.forEach(tk => {
        font(ctx, o.family, R.size, tk.hl ? 600 : 400, o.style || "normal");
        ctx.fillStyle = tk.hl ? acc : ink; ctx.fillText(tk.t, cx, by); cx += tk.w + R.space;
      });
    });
  }
  function drawOptions(ctx, pal, opts4, y, rowH, gap, answer) {
    // answer: undefined on the question slide; index of the correct option on the answer slide
    const x = M - 20, w = W - 2 * (M - 20);
    opts4.forEach((txt, i) => {
      const top = y + i * (rowH + gap), right = answer === i, dim = answer != null && !right;
      ctx.save(); ctx.globalAlpha = dim ? 0.38 : 1;
      roundRect(ctx, x, top, w, rowH, rowH / 2);
      ctx.fillStyle = right ? pal.acc : "rgba(255,255,255,0.62)"; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = right ? pal.acc : hexA(pal.ink, 0.12); ctx.stroke();
      const cr = rowH * 0.31, cx = x + rowH * 0.5, cy = top + rowH / 2;
      ctx.beginPath(); ctx.arc(cx, cy, cr, 0, 7); ctx.fillStyle = right ? "#FFFFFF" : pal.acc; ctx.fill();
      font(ctx, SANS, Math.round(cr * 0.95), 600); ctx.fillStyle = right ? pal.acc : "#FFFFFF"; ctx.textAlign = "center";
      ctx.fillText("ABCD"[i], cx, cy + cr * 0.34);
      const tx = x + rowH + 6, tw = w - rowH - (right ? rowH : 36);
      let size = Math.round(rowH * 0.4);
      font(ctx, SERIF, size, 500);
      while (ctx.measureText(txt).width > tw && size > 26) { size -= 2; font(ctx, SERIF, size, 500); }
      ctx.fillStyle = right ? "#FFFFFF" : pal.ink; ctx.textAlign = "left";
      ctx.fillText(txt, tx, cy + size * 0.34);
      if (right) { // check mark
        const kx = x + w - rowH * 0.62, ky = cy;
        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = rowH * 0.075; ctx.lineCap = "round"; ctx.lineJoin = "round";
        ctx.beginPath(); ctx.moveTo(kx - rowH * 0.16, ky); ctx.lineTo(kx - rowH * 0.04, ky + rowH * 0.12); ctx.lineTo(kx + rowH * 0.18, ky - rowH * 0.13); ctx.stroke();
      }
      ctx.restore();
    });
    return y + opts4.length * (rowH + gap) - gap;
  }
  const QUIZ_ASK = { T: "", F: "Finish the verse", W: "Who said it?", B: "Which book is this from?" };
  function drawQuizCover(ctx, pal, s, opts) {
    font(ctx, SERIF, 1100, 500); ctx.fillStyle = hexA(pal.acc, 0.09); ctx.textAlign = "right"; ctx.fillText("?", W + 40, SAFE_B + 60);
    let y = 290;
    font(ctx, SANS, 40, 600); ctx.fillStyle = pal.acc; spaced(ctx, s.kicker.toUpperCase(), M, y, 6);
    y += 50;
    const t = fit(ctx, s.head, { family: SERIF, weight: 500, maxW: CW, maxH: 440, max: 140, min: 84, lh: 1.02 });
    ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500);
    ctx.save(); ctx.letterSpacing = "-2px"; drawLines(ctx, t.lines, M, y, t.size, 1.02); ctx.restore();
    y += t.height + 56; rule(ctx, pal, M, y, 120); y += 44;
    font(ctx, SERIF, 52, 400, "italic"); ctx.fillStyle = hexA(pal.ink, 0.78); ctx.textAlign = "left";
    ctx.fillText("4 questions. No looking it up.", M, y + 40);
    ctx.fillText("Comment your score at the end.", M, y + 112);
    // four empty score dots
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(M + 34 + i * 92, y + 196, 30, 0, 7); ctx.lineWidth = 5; ctx.strokeStyle = hexA(pal.acc, 0.55); ctx.stroke(); }
    footer(ctx, pal, "SWIPE TO START  →");
  }
  function quizPrompt(ctx, pal, s, top, bottom) {
    // the question / verse / quote block, vertically centered between top and bottom
    const isT = s.f === "T", italic = s.f === "W" || s.f === "B";
    const o = { family: SERIF, style: italic ? "italic" : "normal", maxW: CW, maxH: bottom - top - (s.f === "F" ? 70 : 0), lh: isT ? 1.12 : 1.3,
                max: isT ? 80 : 64, min: isT ? 50 : 36 };
    let R;
    if (isT) { R = fit(ctx, s.q, { family: SERIF, weight: 500, maxW: CW, maxH: o.maxH, max: o.max, min: o.min, lh: o.lh }); }
    else R = fitRich(ctx, s.q, s.f === "F" ? "_____" : "", null, o);
    const blockH = R.height + (s.f === "F" ? 70 : 0);
    const y = top + Math.max(0, (bottom - top - blockH) / 2);
    if (isT) { ctx.fillStyle = pal.ink; font(ctx, SERIF, R.size, 500); ctx.save(); ctx.letterSpacing = "-0.5px"; drawLines(ctx, R.lines, M, y, R.size, o.lh); ctx.restore(); }
    else drawRich(ctx, R, M, y, o, pal.ink, pal.acc);
    if (s.f === "F") { font(ctx, SANS, 30, 600); ctx.fillStyle = pal.acc; spaced(ctx, s.r.toUpperCase(), M, y + R.height + 48, 2.5); }
  }
  function drawQuizQ(ctx, pal, s, opts) {
    font(ctx, SANS, 32, 600); ctx.fillStyle = pal.acc;
    spaced(ctx, `QUESTION ${s.n} OF ${s.of}` + (QUIZ_ASK[s.f] ? "  ·  " + QUIZ_ASK[s.f].toUpperCase() : ""), M, 200, 3);
    const rowH = 104, gap = 20, oy = SAFE_B - (4 * rowH + 3 * gap);
    quizPrompt(ctx, pal, s, 236, oy - 40);
    drawOptions(ctx, pal, s.o, oy, rowH, gap);
    footer(ctx, pal, "SWIPE FOR THE ANSWER  →");
  }
  function drawQuizA(ctx, pal, s, opts) {
    font(ctx, SANS, 32, 600); ctx.fillStyle = pal.acc; spaced(ctx, `ANSWER ${s.n} OF ${s.of}`, M, 200, 3);
    const rowH = 88, gap = 16;
    const top = drawOptions(ctx, pal, s.o, 236, rowH, gap, s.a) + 56, bottom = SAFE_B;
    const o = { family: SERIF, style: "normal", maxW: CW, maxH: bottom - top - 160, lh: 1.32, max: 52, min: 30 };
    const hl = s.f === "B" ? "" : s.hl, pos = s.f === "F" ? s.hlpos : null;
    const R = fitRich(ctx, s.p, hl, pos, o);
    let y = top + Math.max(0, (bottom - top - (R.height + 150)) / 2);
    rule(ctx, pal, M, y, 70); y += 46;
    drawRich(ctx, R, M, y, o, pal.ink, pal.acc);
    font(ctx, SANS, 30, 600); ctx.fillStyle = pal.acc; spaced(ctx, (s.r + " · BSB").toUpperCase(), M, y + R.height + 52, 2.5);
    footer(ctx, pal, s.n < s.of ? "NEXT QUESTION  →" : "HOW MANY DID YOU GET?  COMMENT BELOW");
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
    if (post.t === "Q") {
      const slides = [{ kind: "quizcover", kicker: post.kick, head: post.head }];
      post.qs.forEach((qid, i) => {
        const q = lib.quiz[qid], base = { ...q, n: i + 1, of: post.qs.length };
        slides.push({ kind: "quizq", ...base }, { kind: "quiza", ...base });
      });
      slides.push(PROMO_SLIDE);
      return slides;
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
    if (post.t === "Q") {
      const ftag = { T: "#bibletrivia", F: "#finishtheverse", W: "#whosaidit", B: "#bookofthebible" }[post.f];
      return `${post.ti} 🧠\n\n4 questions, with the answer right after each one. No Googling! Comment your score out of 4 👇\n\nSend this to the friend who thinks they know the Bible best.\n\nWant to know your Bible better? Scripture Spark lets you read the Bible together with a friend or your spouse. Search “Scripture Spark” in the App Store.\n\n${[...new Set([ftag, "#biblequiz", "#bibletrivia", "#bible", "#christian", "#jesus", "#scripturespark", "#christiantiktok"])].join(" ")}`;
    }
    if (post.t === "V") body = `${cap} 🔖\n\nSave this so it's here the next time you need it. Which verse is yours? Comment the number.`;
    else if (post.t === "C") body = `${cap} 📖\n\nSave this for your next quiet time. Which chapter are you reading first?`;
    else if (post.t === "P") body = `${cap} 📖\n\nOne chapter a day for 7 days. Save this and start tomorrow. Comment “Day 1” when you begin.`;
    else if (post.t === "S") body = `${post.vh || post.ti}\n\n“${V[post.v]}”\n${post.v}\n\nSave this for the day you need it. 🔖`;
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
    const top = 400, bottom = opts.tall ? H - 200 : H - 110;
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
    // big date (about 3x the old 34px label), shrunk only if a long month would overflow
    const date = s.dateLabel.toUpperCase();
    let ds = 102;
    for (; ds > 60; ds -= 2) {
      font(ctx, SANS, ds, 600);
      const sp = ds * 0.08, wdt = [...date].reduce((a, c) => a + ctx.measureText(c).width + sp, -sp);
      if (wdt <= TW) break;
    }
    font(ctx, SANS, ds, 600); ctx.fillStyle = pal.acc; spaced(ctx, date, W / 2, 200, ds * 0.08, "center");
    font(ctx, SERIF, 46, 400, "italic"); ctx.fillStyle = hexA(pal.ink, 0.8); ctx.textAlign = "center"; ctx.fillText("God is saying to you today:", W / 2, 296);
    ctx.fillStyle = hexA(pal.acc, 0.6); ctx.fillRect(W / 2 - 40, 334, 80, 3);
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
    const pal = opts.palette != null ? PALETTES[opts.palette] : post.t === "Q" ? paletteFor(post) : paletteForSlide(post, index);
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
    else if (slide.kind === "quizcover") drawQuizCover(ctx, pal, slide, opts);
    else if (slide.kind === "quizq") drawQuizQ(ctx, pal, slide, opts);
    else if (slide.kind === "quiza") drawQuizA(ctx, pal, slide, opts);
    return c;
  }

  // ---------- verse video (9pm post): hook, then the verse revealed phrase by phrase ----------
  // 1080x1920 frames + seconds per frame; make_video.py crossfades them into a short video.
  // Text stays inside the video safe area: below TikTok's top tabs, above the caption, clear of the right-hand buttons.
  function verseChunks(toks) {
    // phrase boundaries at punctuation, 3+ words per phrase, at most 6 phrases
    let chunks = [], cur = 0;
    toks.forEach((tk, i) => {
      cur++;
      const end = /[,;:.!?…—”’)]$/.test(tk.t) && !/^(Mr|Mrs|St)\.$/.test(tk.t);
      if (end && cur >= 3) { chunks.push(cur); cur = 0; }
    });
    if (cur) { if (chunks.length && cur < 3) chunks[chunks.length - 1] += cur; else chunks.push(cur); }
    // split long phrases before a natural break word, as close to the middle as possible
    const BREAK = new Set(["and", "but", "for", "that", "who", "which", "so", "because", "when", "is", "are", "was", "will", "to", "with", "in", "as", "or", "nor", "yet", "if"]);
    for (let guard = 0; guard < 20; guard++) {
      let start = 0, idx = chunks.findIndex(k => k > 11);
      if (idx < 0) break;
      for (let i = 0; i < idx; i++) start += chunks[i];
      const k = chunks[idx], mid = k / 2;
      let best = Math.round(mid), bestD = 1e9;
      for (let j = 3; j <= k - 3; j++) {
        const w = toks[start + j].t.toLowerCase().replace(/[^a-z]/g, "");
        if (BREAK.has(w) && Math.abs(j - mid) < bestD) { best = j; bestD = Math.abs(j - mid); }
      }
      chunks.splice(idx, 1, best, k - best);
    }
    while (chunks.length > 6) {   // merge the shortest neighbouring pair
      let best = 0;
      for (let i = 1; i < chunks.length - 1; i++) if (chunks[i] + chunks[i + 1] < chunks[best] + chunks[best + 1]) best = i;
      chunks.splice(best, 2, chunks[best] + chunks[best + 1]);
    }
    return chunks;
  }
  function renderVerseVideo(post, lib, opts = {}) {
    const VW = 1080, VH = 1920, TOP = 300, BOT = 1430, X = 100, TW = VW - 2 * X - 40;
    const pal = paletteFor(post), seed = hash(post.id);
    const text = lib.verses[post.v], ref = post.v;
    const frames = [], durs = [];
    const canvas = () => {
      const c = document.createElement("canvas"); c.width = VW; c.height = VH;
      const ctx = c.getContext("2d");
      ctx.save(); ctx.scale(VW / W, VH / H); background(ctx, pal, seed); ctx.restore();
      if (opts.handle) { font(ctx, SERIF, 34, 400); ctx.fillStyle = hexA(pal.ink, 0.6); spaced(ctx, opts.handle, VW / 2, TOP - 60, 3, "center"); }
      return [c, ctx];
    };
    // 1) hook
    {
      const [c, ctx] = canvas();
      const t = fit(ctx, post.vh || post.ti, { family: SERIF, weight: 500, maxW: TW, maxH: 700, max: 112, min: 70, lh: 1.08 });
      const y = (TOP + BOT - t.height) / 2 - 40;
      ctx.fillStyle = pal.ink; font(ctx, SERIF, t.size, 500);
      ctx.save(); ctx.letterSpacing = "-1px"; drawLines(ctx, t.lines, X, y, t.size, 1.08); ctx.restore();
      rule(ctx, pal, X, y + t.height + 50, 90);
      frames.push(c.toDataURL("image/jpeg", 0.93)); durs.push(2.2);
    }
    // 2) verse, one more phrase per frame, then the reference
    const o = { family: SERIF, style: "normal", maxW: TW, maxH: BOT - TOP - 330, lh: 1.32, max: 74, min: 42 };
    const R = fitRich((() => { const [, ctx] = canvas(); return ctx; })(), text, "", null, o);
    const toks = R.lines.flat();
    const chunks = verseChunks(toks);
    const kickerH = 110, blockH = kickerH + R.height + 130;
    const y0 = TOP + Math.max(0, (BOT - TOP - blockH) / 2);
    const draw = (shown, withRef) => {
      const [c, ctx] = canvas();
      font(ctx, SERIF, 44, 400, "italic"); ctx.fillStyle = hexA(pal.ink, 0.62); ctx.textAlign = "left";
      let hook = post.vh || post.ti; while (ctx.measureText(hook).width > TW && hook.length > 8) hook = hook.slice(0, -2).trim() + "…";
      ctx.fillText(hook, X, y0 + 44);
      rule(ctx, pal, X, y0 + 78, 70);
      let n = 0;
      R.lines.forEach((ln, i) => {
        let cx = X; const by = y0 + kickerH + R.size * 0.82 + i * R.size * o.lh;
        ln.forEach(tk => {
          if (n < shown) { font(ctx, SERIF, R.size, 400); ctx.fillStyle = pal.ink; ctx.textAlign = "left"; ctx.fillText(tk.t, cx, by); }
          cx += tk.w + R.space; n++;
        });
      });
      if (withRef) { font(ctx, SANS, 34, 600); ctx.fillStyle = pal.acc; spaced(ctx, (ref + " · BSB").toUpperCase(), X, y0 + kickerH + R.height + 70, 2.5); }
      return c.toDataURL("image/jpeg", 0.93);
    };
    let shown = 0;
    chunks.forEach(k => {
      shown += k;
      frames.push(draw(shown, false));
      durs.push(Math.min(3.2, Math.max(1.1, 0.45 + 0.3 * k)));
    });
    frames.push(draw(toks.length, true)); durs.push(2.6);
    return { frames, durs };
  }

  root.ScriptureEngine = { W, H, PALETTES, loadFonts, loadPromo, setPromo, buildSlides, caption, renderSlide, renderVerseVideo, paletteFor, hash };
})(typeof window !== "undefined" ? window : globalThis);
