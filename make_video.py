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
    fc = (f"[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p,trim=duration={total},setpts=PTS-STARTPTS,"
          f"fade=t=in:st=0:d=0.5[v];"
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

if __name__ == "__main__":
    print(make_daily_video(sys.argv[2], sys.argv[1]))
