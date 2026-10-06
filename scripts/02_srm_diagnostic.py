"""Step 0: reproduce the archive's randomisation failure, month by month.

The archive's team reported in June 2024 that a Cloudflare caching
misconfiguration affected roughly 22% of the tests. The public CSV files carry no
column marking them, so this script verifies it from scratch and produces the
table that justifies the exclusion.

It runs WITHOUT the exclusion on purpose: this is the diagnostic that motivates it.

Output: reports/results/02_srm.json
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from wcab import console
from wcab import panel
from wcab.diagnostics import srm

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "02_srm.json"


def without_exclusion(sample: str) -> pd.DataFrame:
    """The raw file, with the columns the diagnostic needs."""
    raw = panel._read_raw(sample)
    raw = raw.loc[raw["impressions"] > 0]
    return pd.DataFrame(
        {
            "experiment_id": raw["clickability_test_id"].astype(str),
            "impressions": raw["impressions"].astype("int64"),
            "date": pd.to_datetime(raw["created_at"], errors="coerce"),
        }
    )


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--min-per-month", type=int, default=30)
    args = ap.parse_args()

    data = without_exclusion(args.sample)
    table = srm.per_experiment(data)
    monthly = srm.by_month(table, minimum=args.min_per_month)

    print(f"{'month':9} {'exp.':>6} {'imbalance':>11}")
    for _, r in monthly.iterrows():
        bar = "#" * int(r.imbalance_fraction * 40)
        print(f"{r.month:9} {int(r.experiments):6d} {r.imbalance_fraction:10.1%}  {bar}")

    metrics = {
        "sample": args.sample,
        **srm.summary(table),
        "by_month": [
            {"month": r.month, "experiments": int(r.experiments),
             "imbalance_fraction": round(float(r.imbalance_fraction), 4)}
            for _, r in monthly.iterrows()
        ],
    }
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
