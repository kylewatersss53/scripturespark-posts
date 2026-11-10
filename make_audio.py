"""Build web/daily_audio.m4a: the birdsong under every daily-word video.

Source: "Dawnchorus-uk.ogg", a public-domain recording of a dawn chorus in
Shipton Gorge, England, on Wikimedia Commons
(https://commons.wikimedia.org/wiki/File:Dawnchorus-uk.ogg). Public domain, so no
attribution is required. We take 12.5 s starting at 12:42 (clear, melodic songs,
little wind or traffic), notch out a faint ~511 Hz-spaced buzz, reduce hiss,
roll off rumble, set the level to about -19 LUFS (soft, sits under TikTok's UI
sounds) and fade both ends.

Only needed to regenerate the file (needs network access to upload.wikimedia.org);
the result is committed, so the nightly job never downloads anything.

    python3 make_audio.py
"""
import os, subprocess, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "web", "daily_audio.m4a")
SRC = "https://upload.wikimedia.org/wikipedia/commons/transcoded/d/de/Dawnchorus-uk.ogg/Dawnchorus-uk.ogg.mp3"
START, LEN = 762, 12.5

FILTERS = ",".join([
    "highpass=f=300:poles=2", "lowpass=f=11000",
    # faint electrical / insect buzz in the recording
    "equalizer=f=511:t=q:w=8:g=-18", "equalizer=f=1179:t=q:w=8:g=-15",
    "equalizer=f=1690:t=q:w=10:g=-22", "equalizer=f=2202:t=q:w=10:g=-15",
    "afftdn=nr=12:nf=-50",
    "loudnorm=I=-19:TP=-3:LRA=7",
    "afade=t=in:st=0:d=1.0", f"afade=t=out:st={LEN - 1.6}:d=1.6",
])

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "src.mp3")
        urllib.request.urlretrieve(SRC, src)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(START), "-t", str(LEN), "-i", src,
                        "-af", FILTERS, "-ar", "44100", "-c:a", "aac", "-b:a", "192k", OUT], check=True)
    print("wrote", OUT)
