"""Compose the calm background track used under every daily-word video.

Original, synthesized audio (no samples, no licensing). Soft warm pad + gentle
bell-like arpeggio in D major, Dmaj9 -> Bm11 -> Gmaj9 -> A(add9), with a light
hall reverb and fades so it starts and ends softly.

    python3 make_music.py            # writes web/calm_music.m4a (12.5 s)

To use a different track instead, drop any audio file at web/calm_music.m4a.
"""
import os, subprocess, sys, tempfile, wave
import numpy as np

SR = 44100
LEN = 12.5            # seconds of finished audio (video is 12 s; a little spare)
CHORD = 3.0           # seconds per chord
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "web", "calm_music.m4a")

def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)

# MIDI notes. Pad voicings (low, warm) and arpeggio notes (upper register).
CHORDS = [
    ([50, 57, 61, 64, 66], [69, 73, 76, 78]),   # Dmaj9   D A C# E F#
    ([47, 54, 57, 62, 64], [66, 69, 71, 74]),   # Bm11    B F# A D E
    ([43, 50, 54, 57, 61], [66, 69, 71, 74]),   # Gmaj9   G D F# A C#  (A in arp)
    ([45, 52, 57, 59, 61], [64, 69, 71, 73]),   # A(add9) A E A B C#
]

rng = np.random.default_rng(7)
n = int((LEN + 3.5) * SR)            # extra for the reverb tail, trimmed later
t = np.arange(n) / SR
mix = np.zeros(n)

def env_pad(start, dur, attack=1.4, release=1.8):
    e = np.zeros(n)
    s, end = int(start * SR), int(min(n, (start + dur + release) * SR))
    tt = t[s:end] - start
    a = np.clip(tt / attack, 0, 1) ** 1.5
    r = np.clip(1 - (tt - dur) / release, 0, 1) ** 2
    e[s:end] = a * np.where(tt > dur, r, 1.0)
    return e

# --- pad: each note = 3 slightly detuned sines + a touch of 2nd harmonic ---
for ci, (pad, _) in enumerate(CHORDS):
    start = ci * CHORD - (0.6 if ci else 0)
    e = env_pad(max(start, 0), CHORD + 0.6)
    for note in pad:
        f = hz(note)
        v = np.zeros(n)
        for cents in (-5, 0, 5):
            ff = f * 2 ** (cents / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            v += np.sin(2 * np.pi * ff * t + ph) + 0.12 * np.sin(4 * np.pi * ff * t + ph)
        amp = 0.022 if note < 52 else 0.03
        mix += v * e * amp
# slow "breathing" swell on the pad
mix *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 6.0 - np.pi / 2)

# --- soft bell / felt-piano arpeggio ---
def pluck(at, midi, vel):
    s = int(at * SR)
    dur = int(2.8 * SR)
    tt = np.arange(min(dur, n - s)) / SR
    f = hz(midi)
    tone = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 3)
            + 0.12 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 6))
    env = (1 - np.exp(-tt * 180)) * np.exp(-tt * 1.6)
    mix[s:s + len(tt)] += tone * env * vel

pattern = [0, 1, 2, 3, 2, 1]            # gentle up-and-back arpeggio
step = 0.5
for ci, (_, arp) in enumerate(CHORDS):
    for k in range(int(CHORD / step)):
        at = ci * CHORD + k * step + 0.25
        if at > LEN - 1.2:
            break
        vel = 0.11 if k % 2 == 0 else 0.08
        pluck(at, arp[pattern[k % len(pattern)]], vel)

# --- one-pole low-pass to soften the top end ---
def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    # vectorised enough for a few seconds of audio via lfilter-like loop in chunks
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y
mix = lowpass(mix, 4200)
mix = mix - lowpass(mix, 110)       # high-pass: keep it light on phone speakers

# --- hall reverb: convolve with decaying stereo noise ---
def reverb(x, seconds=3.2, decay=1.1, seed=0):
    r = np.random.default_rng(seed)
    m = int(seconds * SR)
    tt = np.arange(m) / SR
    ir = r.standard_normal(m) * np.exp(-tt / decay * 3)
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + m)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y
wet_l, wet_r = reverb(mix, seed=1), reverb(mix, seed=2)
L = 0.62 * mix + 0.55 * wet_l
R = 0.62 * mix + 0.55 * wet_r

# --- trim, fade, normalise ---
k = int(LEN * SR)
L, R = L[:k], R[:k]
fade_in, fade_out = int(1.2 * SR), int(2.2 * SR)
ramp = np.ones(k)
ramp[:fade_in] = np.linspace(0, 1, fade_in) ** 2
ramp[-fade_out:] = np.linspace(1, 0, fade_out) ** 1.5
L *= ramp; R *= ramp
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.7, R / peak * 0.7      # about -3 dBFS peak

pcm = (np.stack([L, R], axis=1) * 32767).astype("<i2")
with tempfile.TemporaryDirectory() as d:
    wav = os.path.join(d, "calm.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "192k", OUT], check=True)
print("wrote", OUT, f"{LEN}s")
