"""Phase I: what use is describing better if the same ones get selected?

The earlier phases measured two decisions of **ordering**: which variant to
deploy within an experiment, and which experiments to prioritise under a budget.
In both, shrinkage does not help. A common, strictly increasing transformation
preserves the argmax, so under the nearly homogeneous within-experiment
precision observed here shrinkage is almost ranking-invariant.

There is a third decision no earlier step measured: **do I ship this or not?** It does not compare variants against
one another; it compares an estimated improvement against an **absolute
threshold** — the minimum that justifies deploying, maintaining and carrying the
risk. And there the invariance breaks:

    ranking     is preserved by a COMMON monotone transformation, so with the
                nearly equal weights seen here shrinkage barely moves the argmax
    threshold   is NOT invariant, so shrinkage changes the value and therefore
    comparison  changes whether it crosses the line

**The policy is scored by what it delivered, not by its accuracy.** Counting how
often `estimate > u` agrees with `realized > u` is biased: the indicator of a
noisy quantity does not estimate the indicator of the truth without bias. The
value in `portfolio.threshold_adjusted_value` does, because the action is fixed
by the estimation split and the outcome comes from an independent one. Accuracy
is still reported, as a secondary figure and labelled for what it is: agreement
with a second noisy measurement.

Only `raw` and standard shrinkage are compared. BHS is a post-confirmatory
exploratory extension whose numerical sensitivity was not evaluated, so it does
not carry a primary conclusion here.

All thresholds are in the units of `delta_estimated` — proportions. Conversion
to percentage points happens only when printing.

Output: reports/results/09_ship_decision.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

from wcab import console, inference, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "09_ship_decision.json"

#: Ship thresholds as PROPORTIONS of click rate. 0.004 is 0.4 percentage points.
THRESHOLDS = (0.002, 0.004, 0.006, 0.008)


def _portfolio_for(p, seed: int) -> portfolio.Portfolio:
    selection, estimation, evaluation = thinning.split_three_way(p, seed=seed)
    mask = shrinkage.usable_mask(estimation)
    return portfolio.build_three_way(
        selection.loc[mask].reset_index(drop=True),
        shrinkage.prepare(estimation, mask),
        evaluation.loc[mask].reset_index(drop=True),
    )


def policy_statistic(sample, seed: int) -> dict[str, float]:
    """Every quantity the report needs, from ONE portfolio build per replicate.

    Returning them together is both cheaper and more correct. Cheaper because the
    portfolio build dominates the cost and is shared across rules and thresholds.
    More correct because `shrunk - raw` is a paired comparison: the two rules act
    on the same resampled experiments, so running separate bootstraps and
    subtracting would ignore their correlation and inflate the difference's
    variance.
    """
    c = _portfolio_for(sample, seed)
    raw = c.table["delta_estimated"].to_numpy()
    shrunk = portfolio.shrink_portfolio(c)[0]
    realized = c.table["delta_realized"].to_numpy()

    out: dict[str, float] = {}
    for u in THRESHOLDS:
        v_raw = portfolio.threshold_adjusted_value(c, raw, u)
        v_shrunk = portfolio.threshold_adjusted_value(c, shrunk, u)
        out[f"raw@{u}"] = v_raw["value"]
        out[f"shrunk@{u}"] = v_shrunk["value"]
        out[f"difference@{u}"] = v_shrunk["value"] - v_raw["value"]
        out[f"ship_raw@{u}"] = v_raw["ship_rate"]
        out[f"ship_shrunk@{u}"] = v_shrunk["ship_rate"]
        out[f"should_ship@{u}"] = float((realized > u).mean())
        # secondary and biased: agreement with a second noisy measurement
        truth = realized > u
        out[f"accuracy_raw@{u}"] = float(((raw > u) == truth).mean())
        out[f"accuracy_shrunk@{u}"] = float(((shrunk > u) == truth).mean())
    return out


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--replicates", type=int, default=300,
                    help="bootstrap replicates; 2000 for published inference")
    ap.add_argument("--seeds", type=int, default=3,
                    help="thinning seeds averaged within each replicate")
    args = ap.parse_args()

    p = panel.load(args.sample)

    boot = inference.cluster_bootstrap(
        p, policy_statistic,
        replicates=args.replicates, seeds_per_replicate=args.seeds, seed=0,
    )

    print(f"THE SHIP-OR-NOT DECISION  ({args.sample}, {args.replicates} cluster-"
          f"bootstrap replicates over {args.seeds} thinning seeds)")
    print("  values in percentage points of realised click rate, "
          "net of the threshold\n")
    print("  %-11s %11s %13s %24s" % (
        "threshold", "value raw", "value shrunk", "95% CI, shrunk - raw"))

    metrics = {
        "thresholds": {}, "replicates": args.replicates,
        "seeds_per_replicate": args.seeds, "sample": args.sample,
        "threshold_units": "proportion of click rate",
        "interval_method": "cluster bootstrap over experiments, percentile",
    }

    for u in THRESHOLDS:
        d = boot[f"difference@{u}"]
        lo, hi = d.percentile_interval
        print("  >%.1f pp    %11.5f %13.5f   [%+.5f, %+.5f]" % (
            u * 100,
            boot[f"raw@{u}"].point_estimate * 100,
            boot[f"shrunk@{u}"].point_estimate * 100,
            lo * 100, hi * 100))

        metrics["thresholds"][str(u)] = {
            "threshold_pp": u * 100,
            "value_raw": boot[f"raw@{u}"].to_dict(),
            "value_shrunk": boot[f"shrunk@{u}"].to_dict(),
            "difference_shrunk_minus_raw": d.to_dict(),
            "ship_rate_raw": boot[f"ship_raw@{u}"].point_estimate,
            "ship_rate_shrunk": boot[f"ship_shrunk@{u}"].point_estimate,
            "should_ship": boot[f"should_ship@{u}"].point_estimate,
            "accuracy_raw": boot[f"accuracy_raw@{u}"].point_estimate,
            "accuracy_shrunk": boot[f"accuracy_shrunk@{u}"].point_estimate,
        }

    print("\n  the ship rate explains the mechanism: two policies can reach a")
    print("  similar value while shipping very different numbers of experiments\n")
    print("  %-11s %12s %14s %12s" % (
        "threshold", "ships raw", "ships shrunk", "should ship"))
    for u in THRESHOLDS:
        m = metrics["thresholds"][str(u)]
        print("  >%.1f pp    %11.1f%% %13.1f%% %11.1f%%" % (
            u * 100, m["ship_rate_raw"] * 100, m["ship_rate_shrunk"] * 100,
            m["should_ship"] * 100))

    print("\n  secondary, and biased: accuracy measures agreement with a second")
    print("  noisy measurement, not with the truth")
    for u in THRESHOLDS:
        m = metrics["thresholds"][str(u)]
        print("    >%.1f pp    raw %.2f%%    shrunk %.2f%%" % (
            u * 100, m["accuracy_raw"] * 100, m["accuracy_shrunk"] * 100))

    disagree = [u for u in THRESHOLDS
                if not boot[f"difference@{u}"].intervals_agree]
    if disagree:
        print("\n  percentile and basic intervals differ materially at "
              f"{[f'{u*100:.1f} pp' for u in disagree]}:")
        print("  non-negligible asymmetry or displacement of the bootstrap")
        print("  distribution relative to the observed estimate.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
