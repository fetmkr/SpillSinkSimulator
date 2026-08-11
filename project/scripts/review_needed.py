"""
Has anything changed since the last time the claims were reviewed?

    python3 scripts/review_needed.py          -> prints CHANGED or CLEAN
    python3 scripts/review_needed.py --mark   -> record that a review just ran

Hashes every script and every results CSV/JSON that a number can come from.
A standing reviewer that fires on a timer is noise; one that fires when the
evidence has actually moved is a check. This is what makes the difference.
"""
import os
import sys
import glob
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = os.path.join(ROOT, "results", ".reviewed")


def state():
    h = hashlib.sha256()
    files = sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py")) +
                   glob.glob(os.path.join(ROOT, "results", "*.csv")) +
                   glob.glob(os.path.join(ROOT, "results", "*.json")))
    for f in files:
        if os.path.basename(f) == ".reviewed":
            continue
        h.update(os.path.basename(f).encode())
        h.update(open(f, "rb").read())
    return h.hexdigest(), len(files)


def main():
    cur, n = state()
    if "--mark" in sys.argv:
        open(STAMP, "w").write(cur)
        print("marked reviewed at this state (%d files)" % n)
        return
    old = open(STAMP).read().strip() if os.path.exists(STAMP) else ""
    print("CHANGED" if cur != old else "CLEAN", "(%d files)" % n)


if __name__ == "__main__":
    main()
