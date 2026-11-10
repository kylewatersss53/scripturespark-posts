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
START, LEN, XF, COPIES = 0.85, 12.5, 0.6, 4

def build(src=SRC, out=OUT):
    inputs = []
    for _ in range(COPIES):
        inputs += ["-ss", str(START), "-i", src]
    chain, last = [], "0:a"
    for i in range(1, COPIES):
        lab = f"x{i}"
        chain.append(f"[{last}][{i}:a]acrossfade=d={XF}:c1=tri:c2=tri[{lab}]")
        last = lab
    chain.append(f"[{last}]highpass=f=200:poles=2,loudnorm=I=-19:TP=-3:LRA=7,"
                 f"atrim=0:{LEN},afade=t=in:st=0:d=0.8,afade=t=out:st={LEN - 1.6}:d=1.6,"
                 f"aformat=channel_layouts=stereo[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[a]", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", out], check=True)
    return out

if __name__ == "__main__":
    print("wrote", build())
