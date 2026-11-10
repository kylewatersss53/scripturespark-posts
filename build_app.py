import os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(HERE, "build", "app")
os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
tpl = open(os.path.join(HERE, "web", "app_template.html"), encoding="utf-8").read()
eng = open(os.path.join(HERE, "web", "engine.js"), encoding="utf-8").read()
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*ENGINE*/", eng))
shutil.copy(os.path.join(HERE, "build", "library.json"), os.path.join(out, "library.json"))
shutil.copy(os.path.join(HERE, "web", "promo.jpg"), os.path.join(out, "promo.jpg"))
for f in os.listdir(os.path.join(HERE, "web", "fonts")):
    shutil.copy(os.path.join(HERE, "web", "fonts", f), os.path.join(out, "fonts", f))
print("built", out, os.path.getsize(os.path.join(out, "index.html")) // 1024, "KB")
