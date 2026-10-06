"""Phase I: what use is describing better if the same ones are selected?

The earlier phases measured two decisions of **ordering**: which variant to
deploy within an experiment, and which experiments to prioritise under a budget.
In both, shrinkage does not help — and within an experiment it cannot, by
algebra.

But there is a third decision no earlier step measured, and it is the one a team
takes most frequently: **do I ship this or not?** That decision does not compare
variants against one another; it compares an estimated improvement against an
**absolute threshold** — the minimum that justifies the cost of deploying,
maintaining and carrying the risk.

And there the invariance breaks:

    ranking     is invariant to a monotone transformation, so shrinkage CANNOT
                change the argmax
    threshold   is NOT invariant, so shrinkage changes the value and therefore
    comparison  changes whether it crosses the line

The same correction, two decisions, two answers. This script measures the second.

Output: reports/results/09_ship_decision.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

from wcab import console, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "09_ship_decision.json"

#: ship thresholds, in percentage points of improvement
THRESHOLDS = (0.2, 0.4, 0.6, 0.8)


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=20)
    args = ap.parse_args()

    p = panel.load(args.sample)
    acc = {u: {"raw_ok": [], "shrunk_ok": [], "raw_ships": [],
               "shrunk_ships": [], "truth_ships": []} for u in THRESHOLDS}

    for s in range(args.partitions):
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        c = portfolio.build_three_way(el.loc[m].reset_index(drop=True),
                                      shrinkage.prepare(es, m),
                                      ev.loc[m].reset_index(drop=True))
        t = c.table
        raw = t.delta_estimated.to_numpy() * 100        # to percentage points
        shrunk = portfolio.shrink_portfolio(c)[0] * 100
        realized = t.delta_realized.to_numpy() * 100

        for u in THRESHOLDS:
            truth = realized > u
            for name, est in (("raw", raw), ("shrunk", shrunk)):
                decided = est > u
                acc[u][f"{name}_ok"].append(np.mean(decided == truth))
                acc[u][f"{name}_ships"].append(np.mean(decided))
            acc[u]["truth_ships"].append(np.mean(truth))

    print(f"THE SHIP-OR-NOT DECISION  ({args.partitions} partitions, {args.sample})\n")
    print("  %-9s %10s %13s %10s %12s" % ("threshold", "ships raw", "ships shrunk",
                                          "should", "raw excess"))
    for u in THRESHOLDS:
        lr = np.mean(acc[u]["raw_ships"]); ls = np.mean(acc[u]["shrunk_ships"])
        lt = np.mean(acc[u]["truth_ships"])
        print("  >%.1f pp   %9.1f%% %12.1f%% %9.1f%% %+11.1f pp"
              % (u, lr * 100, ls * 100, lt * 100, (lr - lt) * 100))

    print("\n  %-9s %14s %17s %14s" % ("threshold", "accuracy raw",
                                       "accuracy shrunk", "improvement"))
    for u in THRESHOLDS:
        a = np.array(acc[u]["raw_ok"]); b = np.array(acc[u]["shrunk_ok"])
        print("  >%.1f pp   %13.2f%% %16.2f%% %+13.2f pp   (shrinkage wins in %.0f%%)"
              % (u, a.mean() * 100, b.mean() * 100,
                 (b.mean() - a.mean()) * 100, np.mean(b > a) * 100))

    metrics = {"thresholds": {}, "partitions": args.partitions, "sample": args.sample}
    for u in THRESHOLDS:
        a = np.array(acc[u]["raw_ok"]); b = np.array(acc[u]["shrunk_ok"])
        metrics["thresholds"][str(u)] = {
            "accuracy_raw": float(a.mean()),
            "accuracy_shrunk": float(b.mean()),
            "improvement": float(b.mean() - a.mean()),
            "shrunk_wins_in": float(np.mean(b > a)),
            "ships_raw": float(np.mean(acc[u]["raw_ships"])),
            "ships_shrunk": float(np.mean(acc[u]["shrunk_ships"])),
            "should_ship": float(np.mean(acc[u]["truth_ships"])),
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
