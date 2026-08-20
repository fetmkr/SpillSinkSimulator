"""Fold `sweep_x.shardN.csv` back into `sweep_x.csv`.

    python3 scripts/merge_shards.py results/sweep_topo.csv [more.csv ...]

Plain Python, no Blender -- `run_queue.sh` calls it after a sharded job's
processes have all exited. See `scripts/sweep_shard.py` for why sharding is
safe here at all.
"""

import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_shard import merge_shards                              # noqa: E402


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    for path in argv:
        merge_shards(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
