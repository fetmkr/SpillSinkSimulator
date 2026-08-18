"""Substitute {{IMG:relpath|alt text}} placeholders with resized base64 data
URIs. Keeps the source HTML readable and the artifact self-contained."""
import base64, os, re, subprocess, sys, hashlib

ROOT = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imgcache")
os.makedirs(CACHE, exist_ok=True)
MAXW = 1400

def data_uri(rel):
    src = rel if rel.startswith("/") else os.path.join(ROOT, rel)
    if not os.path.exists(src):
        raise SystemExit("missing image: " + rel)
    key = hashlib.md5(rel.encode()).hexdigest()[:12]
    out = os.path.join(CACHE, key + ".jpg")
    if not os.path.exists(out):
        # resize to <=MAXW wide, flatten to jpeg q78 on white
        subprocess.run(["sips", "-s", "format", "jpeg",
                        "-s", "formatOptions", "78",
                        "--resampleWidth", str(MAXW), src, "--out", out],
                       check=True, capture_output=True)
        # sips upscales small images; redo without resample if source narrower
        w = int(subprocess.run(["sips", "-g", "pixelWidth", src],
                capture_output=True, text=True).stdout.split()[-1])
        if w <= MAXW:
            subprocess.run(["sips", "-s", "format", "jpeg",
                            "-s", "formatOptions", "82", src, "--out", out],
                           check=True, capture_output=True)
    b = open(out, "rb").read()
    return "data:image/jpeg;base64," + base64.b64encode(b).decode(), len(b)

def build(src_html, dst_html):
    s = open(src_html).read()
    total = 0
    def sub(m):
        nonlocal total
        rel, alt = m.group(1), m.group(2)
        uri, n = data_uri(rel)
        total += n
        return '<img src="%s" alt="%s">' % (uri, alt)
    s = re.sub(r"\{\{IMG:([^|}]+)\|([^}]*)\}\}", sub, s)
    left = re.findall(r"\{\{IMG:[^}]*\}\}", s)
    if left:
        raise SystemExit("unresolved placeholders: %r" % left[:3])
    open(dst_html, "w").write(s)
    print("built %s  html %.1f MB  images %.1f MB" %
          (dst_html, len(s)/1e6, total/1e6))

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
