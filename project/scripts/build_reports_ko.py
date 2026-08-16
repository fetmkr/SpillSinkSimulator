"""Korean edition builder: wraps report/ko/src/*_body.html into full pages.

    python3 scripts/build_reports_ko.py

The Korean pages are TRANSLATIONS of already-published English pages.
Numbers are quoted as published there (the English builders read them
from the data files at build time); each page names its source. Figure
tokens {{IMG:relative/path.png}} inline the same PNGs the English pages
use — their internal labels stay English, noted under each figure.
"""

import os
import sys
import base64
import glob
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "report", "ko", "src")
OUTDIR = os.path.join(ROOT, "report", "ko")

STYLE = """<style>
:root{--bg:#f4f2ec;--card:#fbfaf7;--ink:#1c1b18;--ink2:#5c594f;--line:#d8d4c8;
  --acc:#b34700;--ok:#2c6e49;--mono:ui-monospace,'SF Mono',Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme=light]){
  --bg:#171613;--card:#1f1e1a;--ink:#e8e5dd;--ink2:#a39f92;--line:#37342c;
  --acc:#ff8c42;--ok:#7fc8a0}}
:root[data-theme=dark]{--bg:#171613;--card:#1f1e1a;--ink:#e8e5dd;
  --ink2:#a39f92;--line:#37342c;--acc:#ff8c42;--ok:#7fc8a0}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);
  font:16px/1.75 'Apple SD Gothic Neo','Noto Sans KR',sans-serif;
  margin:0;padding:0 18px}
main{max-width:46rem;margin:0 auto;padding:3rem 0 5rem}
h1{font-size:1.8rem;line-height:1.3;margin:.2rem 0 0}
h2{font-size:1.12rem;margin:2.6rem 0 .6rem;border-bottom:1px solid var(--line);
  padding-bottom:.35rem}
.kicker{font:700 .72rem var(--mono);letter-spacing:.18em;color:var(--acc)}
.lede{color:var(--ink2);font-size:1.02rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;
  font:.84rem var(--mono);font-variant-numeric:tabular-nums}
th{font-weight:600;text-align:left;color:var(--ink2);
  border-bottom:1px solid var(--ink2)}
td,th{padding:.45rem .6rem .45rem 0}
td{border-bottom:1px solid var(--line)}
tr.win td{color:var(--ok);font-weight:600}
.note{font-size:.85rem;color:var(--ink2)}
code{font:.85em var(--mono)}
figure{margin:1.2rem 0 0}
figure img{width:100%;border:1px solid var(--line);border-radius:6px}
figcaption{font-size:.85rem;color:var(--ink2);margin-top:.4rem}
.warn{color:var(--acc)}
</style>
"""


def inline_figs(html):
    def repl(m):
        p = os.path.join(ROOT, "report", m.group(1))
        if not os.path.exists(p):
            return ""
        b = base64.b64encode(open(p, "rb").read()).decode()
        return "data:image/png;base64," + b
    return re.sub(r"\{\{IMG:([^}]+)\}\}", repl, html)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    for src in sorted(glob.glob(os.path.join(SRC, "*_body.html"))):
        name = os.path.basename(src).replace("_body.html", "")
        body = open(src).read()
        title = re.search(r"<!--title:(.*?)-->", body)
        title = title.group(1) if title else "Spill Sink 연구 (한글판)"
        html = ("<title>%s</title>\n" % title) + STYLE + "<main>\n" \
            + inline_figs(body) + "\n</main>\n"
        out = os.path.join(OUTDIR, name + ".html")
        open(out, "w").write(html)
        print("wrote %s (%d KB)" % (out, os.path.getsize(out) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
