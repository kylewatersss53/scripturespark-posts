"""Build web/daily_audio.m4a: the calm birdsong under every daily-word video.

Source: audio/daily_birds_source.wav (bird clip supplied by the account owner,
~5 s mono). The first 0.85 s has dropouts, so we use 0.85 s to the end (~4.1 s),
loop it 4x with 0.6 s crossfades so the joins are seamless, roll off rumble,
set the level to about -19 LUFS (soft), make it stereo, trim to 12.5 s and fade
both ends. To change the sound, replace the source wav and rerun:

    python3 make_audio.py
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "audio", "daily_birds_source.wav")
OUT = os.path.join(HERE, "web", "daily_audio.m4a")
VERSE_OUT = os.path.join(HERE, "web", "verse_audio.m4a")   # longer bed for the 9pm verse videos
START, LEN, XF, COPIES = 0.85, 12.5, 0.6, 4

def build(src=SRC, out=OUT, length=LEN):
    clip = 4.1   # usable seconds of the source after START
    copies = max(COPIES, int((length + XF) // (clip - XF)) + 2)
    inputs = []
    for _ in range(copies):
        inputs += ["-ss", str(START), "-i", src]
    chain, last = [], "0:a"
    for i in range(1, copies):
        lab = f"x{i}"
        chain.append(f"[{last}][{i}:a]acrossfade=d={XF}:c1=tri:c2=tri[{lab}]")
        last = lab
    chain.append(f"[{last}]highpass=f=200:poles=2,loudnorm=I=-19:TP=-3:LRA=7,"
                 f"atrim=0:{length},afade=t=in:st=0:d=0.8,afade=t=out:st={length - 1.6}:d=1.6,"
                 f"aformat=channel_layouts=stereo[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[a]", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", out], check=True)
    return out

# ---------- worship music beds for the 9pm verse videos ----------
# Sources: royalty-free worship instrumentals from Pixabay Music (Pixabay Content License: commercial use on
# social media allowed, no attribution required; the license forbids redistributing the files as-is, so the
# originals stay out of git in audio/worship_src/ and only edited beds are committed). See audio/WORSHIP_SOURCES.md.
# Each bed: a full, steady 30 s section (no quiet intro), softly layered with the birdsong (brand sound),
# loudness-normalised to about -16 LUFS, faded at both ends.
WORSHIP_SRC = os.path.join(HERE, "audio", "worship_src")
BEDS_DIR = os.path.join(HERE, "web", "worship")
WORSHIP_SECTIONS = {   # file -> start seconds of the sections picked by loudness/steadiness analysis
    "denis-pavlov-beautiful-worship-piano.mp3": [340, 165, 295],
    "denis-pavlov-worship-piano-peaceful-prayer.mp3": [425, 320, 470],
    "leberch-worship-instrumental.mp3": [65, 110],
    "leberch-worship-music.mp3": [100, 155, 45],
    "zeldafleming-jesus-you-alone.mp3": [175, 125, 80],
}
BED_LEN = 30.0

def build_worship_beds():
    os.makedirs(BEDS_DIR, exist_ok=True)
    birds = VERSE_OUT if os.path.exists(VERSE_OUT) else build(out=VERSE_OUT, length=30.0)
    n = 0
    for fname, starts in sorted(WORSHIP_SECTIONS.items()):
        src = os.path.join(WORSHIP_SRC, fname)
        if not os.path.exists(src):
            print("missing", src, "(upload it to rebuild this bed)"); continue
        for st in starts:
            out = os.path.join(BEDS_DIR, f"{os.path.splitext(fname)[0]}-{st}.m4a")
            fc = (f"[0:a]atrim=0:{BED_LEN},asetpts=PTS-STARTPTS,highpass=f=50,aformat=channel_layouts=stereo,"
                  f"loudnorm=I=-16:TP=-2:LRA=9[m];[1:a]volume=0.22[b];[m][b]amix=inputs=2:duration=first:normalize=0,"
                  f"afade=t=in:st=0:d=0.6,afade=t=out:st={BED_LEN - 2}:d=2[a]")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(st), "-t", str(BED_LEN + 1), "-i", src, "-i", birds,
                            "-filter_complex", fc, "-map", "[a]", "-ar", "44100", "-c:a", "aac", "-b:a", "160k", out], check=True)
            n += 1
    print("wrote", n, "worship beds ->", BEDS_DIR)

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["worship"]:
        build_worship_beds(); raise SystemExit
    print("wrote", build())
    print("wrote", build(out=VERSE_OUT, length=30.0))
