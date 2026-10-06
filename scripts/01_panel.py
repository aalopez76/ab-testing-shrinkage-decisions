"""Build the canonical panel and write out its scale figures.

Output: data/derived/panel-<sample>.parquet and reports/results/01_panel.json

Every scale figure the documents cite comes from this JSON. A figure that appears
in a document but not here is orphaned.
"""

import argparse
import json
from pathlib import Path

from wcab import console
from wcab import panel

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "01_panel.json"


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    args = ap.parse_args()

    table, res = panel.build(args.sample)
    target = panel.save(table, args.sample)

    metrics = {
        "sample": args.sample,
        "exclusion": {
            "window": "2013-06-01 to 2014-02-01",
            "arms_before": res.arms_before,
            "arms_after": res.arms_after,
            "experiments_before": res.experiments_before,
            "experiments_after": res.experiments_after,
            "retained_fraction": round(res.retained_fraction, 4),
        },
        "panel": panel.summary(table),
    }

    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")

    print(res)
    print(f"panel -> {target.relative_to(ROOT)}")
    print(f"metrics -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
