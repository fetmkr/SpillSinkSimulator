"""Run one sweep as N concurrent Blender processes, then merge the pieces.

    NSHARD=2 SHARD=0 Blender --background ... --python scripts/sweep_topo.py &
    NSHARD=2 SHARD=1 Blender --background ... --python scripts/sweep_topo.py &
    wait
    python3 scripts/merge_shards.py results/sweep_topo.csv

WHY. A sweep alternates between two resources and uses one at a time. Building
a design is single-threaded Python -- 2.6 s for the 1.1 M-vertex cone -- and
during it the GPU is idle; rendering is Metal -- ~2 s -- and during that the
CPU is idle. Measured on four cone measurements: 55 s run one after another,
42 s run two at a time, because each process builds while the other renders.
Four at a time measured 43 s, no better than two, so two is the setting.

WHY IT IS SAFE, which is the only reason this is worth doing at all. The
sweeps were already resumable: each reads the (tag, diffuse_frac) pairs its CSV
already holds and skips them, so a killed run costs at most the design in
flight. That property is what makes them shardable -- a shard is just a run
that skips more. Nothing about the measurement changes.

Two rules keep it honest:

1. WITH `NSHARD` UNSET EVERY FUNCTION HERE IS A NO-OP. `shard_csv` returns the
   path it was given, `take` returns True, and `done_tags` reads the one file.
   An unsharded run is byte-identical to what it was before this module
   existed, which is what makes it acceptable to touch nine sweep scripts.

2. THE CANONICAL CSV KEEPS ITS NAME. Shards write `sweep_x.shard1.csv`
   alongside `sweep_x.csv` and are merged back into it at the end, so the
   nineteen analysis, report and gate scripts that read `results/sweep_x.csv`
   never learn that sharding exists.

`done_tags` reads the base file AND every sibling shard, so a resumed run does
not re-measure a row another shard has already written.

Partitioning is `crc32(tag) % NSHARD`, not a loop counter: it needs no index
threaded through each sweep's loops, it is stable across runs (so a resume puts
the same design on the same shard), and it survives a design list growing in
the middle. It does NOT balance the shards perfectly -- with the design counts
here the split is close enough that the imbalance is smaller than the spread
between one design and the next.
"""

from __future__ import annotations

import csv
import glob
import os
import zlib


def _env():
    """(shard, nshard), or (0, 1) when unsharded. Invalid settings are fatal.

    A typo in NSHARD must not silently produce a run that measures a third of
    the designs and looks complete.
    """
    n = os.environ.get("NSHARD")
    if not n:
        return 0, 1
    try:
        nshard = int(n)
        shard = int(os.environ.get("SHARD", "0"))
    except ValueError:
        raise SystemExit("NSHARD/SHARD must be integers, got NSHARD=%r SHARD=%r"
                         % (n, os.environ.get("SHARD")))
    if nshard < 1 or not (0 <= shard < nshard):
        raise SystemExit("bad shard: SHARD=%d of NSHARD=%d" % (shard, nshard))
    return shard, nshard


def base_csv(path):
    """The canonical path, given either it or one of its shards.

    The sweeps set `OUTCSV = shard_csv(...)` once and then pass OUTCSV to
    everything, so `done_tags` and `merge_shards` are routinely handed
    `sweep_x.shard1.csv` and must still find `sweep_x.csv` beside it. Without
    this, shard 1 would resume against its own rows only and re-measure
    everything the base file already held.
    """
    stem, ext = os.path.splitext(path)
    head, _, tail = stem.rpartition(".")
    if head and tail.startswith("shard") and tail[5:].isdigit():
        return head + ext
    return path


def shard_paths(path):
    """Every file holding rows for `path`: the base, then any shard files."""
    base = base_csv(path)
    stem, ext = os.path.splitext(base)
    return [base] + sorted(glob.glob("%s.shard*%s" % (stem, ext)))


def shard_csv(path):
    """Where THIS process writes. The base path when unsharded."""
    shard, nshard = _env()
    if nshard == 1:
        return path
    stem, ext = os.path.splitext(path)
    return "%s.shard%d%s" % (stem, shard, ext)


def take(tag):
    """Does this design belong to this shard?"""
    _, nshard = _env()
    if nshard == 1:
        return True
    shard, _ = _env()
    return zlib.crc32(str(tag).encode()) % nshard == shard


def done_tags(path):
    """The (tag, diffuse_frac) pairs already measured, across every shard.

    Reading the siblings is what makes a resume correct: shard 0 must not
    re-measure a design shard 1 wrote before it was killed.
    """
    seen = set()
    for p in shard_paths(path):
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            for r in csv.DictReader(fh):
                if r.get("tag") is not None:
                    seen.add((r["tag"], r.get("diffuse_frac")))
    return seen


def merge_shards(path, verbose=True):
    """Fold the shard files into the canonical CSV and delete them.

    Refuses to merge shards whose header differs from the base, for the same
    reason `sweep_floor.open_append` refuses to append under a mismatched
    header: a DictReader shifts every row by one and nothing raises.

    Returns (rows_in_base_after, rows_added).
    """
    path = base_csv(path)
    shards = shard_paths(path)[1:]
    if not shards:
        if verbose:
            print("[MERGE] no shards beside %s" % os.path.basename(path))
        return _count(path), 0

    header, rows = None, []
    if os.path.exists(path):
        header, rows = _read(path)

    added = 0
    for sp in shards:
        h, rs = _read(sp)
        if h is None:
            continue
        if header is None:
            header = h
        elif h != header:
            raise SystemExit(
                "%s has header\n  %s\nbut %s has\n  %s\nMerging would shift "
                "every row. Nothing was written." %
                (os.path.basename(sp), ",".join(h),
                 os.path.basename(path), ",".join(header)))
        rows.extend(rs)
        added += len(rs)

    # dedup on the same key the sweeps resume on, keeping first occurrence so
    # the base file's rows win over a shard that re-measured one
    out, seen = [], set()
    for r in rows:
        k = (r.get("tag"), r.get("diffuse_frac"), r.get("theta"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)

    tmp = path + ".merging"
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in out:
            w.writerow(r)
    os.replace(tmp, path)                 # atomic: never a half-written CSV
    for sp in shards:
        os.remove(sp)

    if verbose:
        print("[MERGE] %s: %d rows (+%d from %d shard(s), %d duplicate(s) "
              "dropped)" % (os.path.basename(path), len(out), added,
                            len(shards), len(rows) - len(out)))
    return len(out), added


def _read(path):
    with open(path) as fh:
        r = csv.DictReader(fh)
        rows = list(r)
        return (r.fieldnames, rows)


def _count(path):
    if not os.path.exists(path):
        return 0
    with open(path) as fh:
        return sum(1 for _ in csv.DictReader(fh))
