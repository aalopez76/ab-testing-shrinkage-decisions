"""Step 0: fetch the archive's public CSV files.

Run this once on a fresh checkout, before anything else. Everything downstream
reads the canonical panel, which `01_panel.py` builds from these files.

The data are the Upworthy Research Archive (Matias et al., *Scientific Data*,
2021), distributed under CC BY 4.0 and not redistributed by this repository.

Output: data/raw/upworthy-{exploratory,confirmatory}.csv
"""

import argparse
from pathlib import Path

from wcab import console, io, panel

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timeout", type=int, default=300,
                    help="seconds allowed per request")
    args = ap.parse_args()

    print(f"downloading into {panel.RAW.relative_to(ROOT)} ...")
    paths = io.download(panel.RAW, timeout=args.timeout)

    for key in sorted(paths):
        path = paths[key]
        size = path.stat().st_size / 1e6
        print(f"  {key:13} {path.name:32} {size:8.1f} MB")

    print("\nnext: python scripts/01_panel.py --sample exploratory")


if __name__ == "__main__":
    main()
