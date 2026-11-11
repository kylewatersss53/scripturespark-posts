"""Turn a daily-word frame into a 12 s TikTok video with calm background music.

Input is the full-screen 1080x1920 daily-word frame (render_batch.py writes it as
tall.jpg for every D: post). Output: 1080x1920, 30 fps, H.264 + AAC, 12 s, soft
fade-in, birdsong from web/daily_audio.m4a (see make_audio.py) faded at both ends.
No app promo slide; the caption carries the app line.

    python3 make_video.py OUT.mp4 tall.jpg
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(HERE, "web", "daily_audio.m4a")
TOTAL = 12.0

def make_daily_video(frame, out, music=MUSIC, total=TOTAL):
    fc = (f"[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p,trim=duration={total},setpts=PTS-STARTPTS[v];"
          f"[1:a]atrim=0:{total},afade=t=in:st=0:d=0.8,afade=t=out:st={total - 1.6}:d=1.6,asetpts=PTS-STARTPTS[a]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y",
           "-loop", "1", "-framerate", "30", "-t", str(total), "-i", frame,
           "-i", music,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-t", str(total), "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out

VERSE_MUSIC = os.path.join(HERE, "web", "verse_audio.m4a")
BEDS_DIR = os.path.join(HERE, "web", "worship")

def pick_bed(key):
    """Worship music bed for a verse video, rotated by post id (falls back to the birdsong bed)."""
    beds = sorted(f for f in os.listdir(BEDS_DIR) if f.endswith(".m4a")) if os.path.isdir(BEDS_DIR) else []
    if not beds:
        return VERSE_MUSIC
    import hashlib
    return os.path.join(BEDS_DIR, beds[int(hashlib.md5(key.encode()).hexdigest()[:8], 16) % len(beds)])

def make_verse_video(spec, out, music=None, key=""):
    """9pm verse video from engine layers: the background drifts slowly (subtle motion) while text layers
    fade in phrase by phrase on top. The hook is visible from the first frame (TikTok's default cover)."""
    music = music or pick_bed(key or out)
    total, layers = float(spec["total"]), spec["layers"]
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{total:.2f}", "-i", spec["bg"]]
    for L in layers:
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{total:.2f}", "-i", L["file"]]
    cmd += ["-i", music]
    # slow diagonal drift across the whole oversized background (about 12-35 px/s)
    fc = [f"[0:v]fps=30,crop=1080:1920:x='216*t/{total:.2f}':y='384*t/{total:.2f}',setsar=1,format=rgba[b0]"]
    last = "b0"
    for i, L in enumerate(layers, start=1):
        f = [f"[{i}:v]fps=30,format=rgba"]
        if L.get("fadeIn"):
            f.append(f"fade=t=in:st={L['start']:.2f}:d={L['fadeIn']:.2f}:alpha=1")
        if L.get("end") is not None and L.get("fadeOut"):
            f.append(f"fade=t=out:st={max(0.0, L['end'] - L['fadeOut']):.2f}:d={L['fadeOut']:.2f}:alpha=1")
        fc.append(",".join(f) + f"[l{i}]")
        en = f":enable='between(t,{L['start']:.2f},{L['end']:.2f})'" if L.get("end") is not None else (f":enable='gte(t,{L['start']:.2f})'" if L["start"] > 0 else "")
        fc.append(f"[{last}][l{i}]overlay=0:0{en}[b{i}]")
        last = f"b{i}"
    a = len(layers) + 1
    fc.append(f"[{last}]format=yuv420p,trim=duration={total:.2f}[v]")
    fc.append(f"[{a}:a]atrim=0:{total:.2f},afade=t=in:st=0:d=0.5,afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5,asetpts=PTS-STARTPTS[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-t", f"{total:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out

if __name__ == "__main__":
    print(make_daily_video(sys.argv[2], sys.argv[1]))
