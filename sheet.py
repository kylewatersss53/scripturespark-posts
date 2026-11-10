import sys, os, glob
from PIL import Image
def sheet(dirs, out, w=270):
    rows = []
    for d in dirs:
        fs = sorted(glob.glob(os.path.join(d, "*.jpg")))
        ims = [Image.open(f).resize((w, int(w * 1440 / 1080))) for f in fs]
        rows.append(ims)
    cols = max(len(r) for r in rows); hh = int(w * 1440 / 1080)
    S = Image.new("RGB", (cols * (w + 8) + 8, len(rows) * (hh + 8) + 8), (40, 40, 40))
    for ri, r in enumerate(rows):
        for ci, im in enumerate(r):
            S.paste(im, (8 + ci * (w + 8), 8 + ri * (hh + 8)))
    S.save(out, quality=88)
if __name__ == "__main__":
    sheet(sys.argv[2:], sys.argv[1])
