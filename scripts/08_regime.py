"""Phase H: does the conclusion depend on the regime the literature filters out?

Coey and Hung (*Empirical Bayes Selection for Value Maximization*, arXiv
2210.03905) ask this same question of this same archive. Their setup, described
in their Appendix B, imposes two conditions:

  1. they discard arms with fewer than 1,000 impressions or 100 clicks, "to
     ensure normality approximations are reasonable";
  2. they reduce each experiment to an arbitrary pair - the arm with the most
     impressions against the second-most - omitting the rest.

The second condition removes selection on outcome, so their setup does not
contain the winner's curse.

**Only the first condition is implemented here.** This script applies their
arm-quality filter, which retains 6.9% of the arms, and does not reduce each
experiment to its two largest arms. It is therefore a comparison across that
quality regime, not a replication of their construction, and nothing it reports
should be read as reproducing their result.

It measures the same quantity inside and outside that filter with an interval.
Failing to detect a difference inside it is not evidence of equivalence: the
filtered sample is small and its interval is correspondingly wide.

Output: reports/results/08_regime.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import console, inference, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "08_regime.json"

# the filter exactly as stated in their Appendix B
MIN_IMPRESSIONS, MIN_CLICKS = 1000, 100


def at_least_two_arms(p: pd.DataFrame) -> pd.DataFrame:
    g = p.groupby("experiment_id").size()
    return p[p.experiment_id.isin(g[g >= 2].index)].reset_index(drop=True)


def make_statistic(budget: float):
    """Gain difference and estimation error, from one portfolio build per replicate.

    Both quantities come back together so the comparison stays paired: the two
    rules act on the same resampled experiments, and running separate bootstraps
    would ignore their correlation and inflate the difference's variance.
    """

    def statistic(sample: pd.DataFrame, seed: int) -> dict[str, float]:
        el, es, ev = thinning.split_three_way(sample, seed=seed)
        m = shrinkage.usable_mask(es)
        c = portfolio.build_three_way(
            el.loc[m].reset_index(drop=True), shrinkage.prepare(es, m),
            ev.loc[m].reset_index(drop=True))
        mean, _ = portfolio.shrink_portfolio(c)
        d_a = c.table.delta_estimated.to_numpy()
        d_b = c.table.delta_realized.to_numpy()
        raw = portfolio.value_by_budget(c, d_a, [budget])[budget]
        shrunk = portfolio.value_by_budget(c, mean, [budget])[budget]
        return {
            "gain_raw": raw,
            "gain_shrunk": shrunk,
            "difference": shrunk - raw,
            "mse_raw": float(np.mean((d_a - d_b) ** 2)),
            "mse_shrunk": float(np.mean((mean - d_b) ** 2)),
        }

    return statistic


def measure(p: pd.DataFrame, replicates: int, seeds: int, budget: float) -> dict:
    """Cluster-bootstrap the regime comparison.

    The earlier version divided the standard deviation across thinning seeds by
    the square root of their count and called the result a 95% interval. That
    measured how much the answer moves when the split moves — a quantity that
    shrinks towards zero as seeds are added — rather than uncertainty about the
    effect. The resampling unit is now the experiment.
    """
    boot = inference.cluster_bootstrap(
        p, make_statistic(budget),
        replicates=replicates, seeds_per_replicate=seeds, seed=0,
    )
    d = boot["difference"]
    lo, hi = d.percentile_interval
    rate = float(p.clicks.sum() / p.impressions.sum())
    return {
        "experiments": int(p.experiment_id.nunique()),
        "arms": int(len(p)),
        "median_n_times_p": float(np.median(p.impressions * rate)),
        "difference": d.to_dict(),
        "mean_difference": d.point_estimate,
        "percentile_interval": [float(lo), float(hi)],
        "basic_interval": list(d.basic_interval),
        "intervals_agree": d.intervals_agree,
        "differs_from_zero": bool(lo * hi > 0),
        "mse_relative_change": float(
            boot["mse_shrunk"].point_estimate / boot["mse_raw"].point_estimate - 1
        ),
    }


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--replicates", type=int, default=300,
                    help="bootstrap replicates; 2000 for published inference")
    ap.add_argument("--seeds", type=int, default=3,
                    help="thinning seeds averaged within each replicate")
    ap.add_argument("--budget", type=float, default=0.05)
    args = ap.parse_args()

    p = panel.load(args.sample)
    passes = (p.impressions >= MIN_IMPRESSIONS) & (p.clicks >= MIN_CLICKS)
    print(f"the Coey and Hung filter (>={MIN_IMPRESSIONS} impressions and "
          f">={MIN_CLICKS} clicks) retains {passes.mean():.1%} of {len(p):,} arms\n")

    cases = {
        "filtered_regime": at_least_two_arms(p[passes].reset_index(drop=True)),
        "full_archive": p,
    }
    metrics = {}
    for name, data in cases.items():
        r = measure(data, args.replicates, args.seeds, args.budget)
        metrics[name] = r
        lo, hi = r["percentile_interval"]
        print(f"{name}  ({r['experiments']:,} experiments | "
              f"median n*p {r['median_n_times_p']:.0f})")
        print(f"  mean squared error          {r['mse_relative_change']*100:+.1f}%")
        print(f"  gain, shrunk minus raw      {r['mean_difference']*100:+.4f} pp")
        print(f"  95% cluster-bootstrap       [{lo*100:+.4f}, {hi*100:+.4f}] "
              "percentile")
        if not r["intervals_agree"]:
            b_lo, b_hi = r["basic_interval"]
            print(f"  basic interval             [{b_lo*100:+.4f}, {b_hi*100:+.4f}] "
                  "— differs materially: asymmetry or displacement")
        print(f"  does it differ from zero?   "
              f"{'YES' if r['differs_from_zero'] else 'NO'}\n")

    a, b = metrics["filtered_regime"], metrics["full_archive"]
    print("READING")
    if not a["differs_from_zero"] and b["differs_from_zero"] and b["mean_difference"] < 0:
        print("  Inside their arm-quality filter, NO CLEAR DIFFERENCE is detected")
        print("  between raw and shrunken prioritisation. That is not equivalence:")
        print("  the filtered sample is small and its interval is wide enough to")
        print("  hold effects of either sign. In the FULL ARCHIVE, which contains")
        print("  the filtered arms rather than excluding them, shrinkage degrades")
        print("  selection measurably.")

    metrics["filter"] = {"min_impressions": MIN_IMPRESSIONS, "min_clicks": MIN_CLICKS,
                         "fraction_of_arms_retained": float(passes.mean())}
    metrics["replicates"] = args.replicates
    metrics["seeds_per_replicate"] = args.seeds
    metrics["interval_method"] = "cluster bootstrap over experiments, percentile"
    metrics["budget"] = args.budget
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
