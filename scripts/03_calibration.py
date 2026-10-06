"""Step 1: the verdict on the noise model.

Tests v = p(1-p)/n against the dispersion observed in the A/A experiments, where
the true difference between arms is zero by construction.

Output: reports/results/03_calibration.json
"""

import argparse
import json
from pathlib import Path

from wcab import console
from wcab import panel
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "03_calibration.json"


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--tolerance", type=float, default=0.15)
    args = ap.parse_args()

    p = panel.load(args.sample)
    cal = noise.calibrate(p, tolerance=args.tolerance)
    print(cal)

    if not cal.passed:
        print(
            "\nThe noise model does NOT describe these data. Two explanations, and\n"
            "they are not distinguishable with this archive:\n"
            "  1. An arm's impressions are not independent (clustering).\n"
            "  2. Those experiments vary in fields the archive does not publish.\n"
            "Both are declared. Step 2 compares naive v against corrected v."
        )

    metrics = {
        "sample": args.sample,
        "tolerance": args.tolerance,
        **cal.to_dict(),
        "indistinguishable_explanations": [
            "impressions not independent within an arm (clustering)",
            "variation in fields the archive does not publish",
        ],
    }
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
