"""Phase H: does the conclusion depend on the regime the literature filters out?

Coey and Hung (*Empirical Bayes Selection for Value Maximization*, arXiv
2210.03905) ask this same question of this same archive. Their setup, described
in their Appendix B, imposes two conditions:

  1. they discard arms with fewer than 1,000 impressions or 100 clicks, "to
     ensure normality approximations are reasonable";
  2. they reduce each experiment to an arbitrary pair - the arm with the most
     impressions against the second-most - omitting the rest.

The second condition removes selection on outcome, so their setup does not
contain the winner's curse. The first retains 6.9% of the arms.

This script measures the same quantity inside and outside their filter, with a
confidence interval, to establish whether their conclusion is general or specific
to their regime.

Output: reports/results/08_regime.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import console, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "08_regime.json"

# the filter exactly as stated in their Appendix B
MIN_IMPRESSIONS, MIN_CLICKS = 1000, 100


def at_least_two_arms(p: pd.DataFrame) -> pd.DataFrame:
    g = p.groupby("experiment_id").size()
    return p[p.experiment_id.isin(g[g >= 2].index)].reset_index(drop=True)


def measure(p: pd.DataFrame, partitions: int, budget: float) -> dict:
    dif, mse_c, mse_s = [], [], []
    for s in range(partitions):
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        c = portfolio.build_three_way(
            el.loc[m].reset_index(drop=True), shrinkage.prepare(es, m),
            ev.loc[m].reset_index(drop=True))
        mean, _ = portfolio.shrink_portfolio(c)
        d_a = c.table.delta_estimated.to_numpy()
        d_b = c.table.delta_realized.to_numpy()
        mse_c.append(float(np.mean((d_a - d_b) ** 2)))
        mse_s.append(float(np.mean((mean - d_b) ** 2)))
        cru = portfolio.value_by_budget(c, d_a, [budget])[budget]
        con = portfolio.value_by_budget(c, mean, [budget])[budget]
        dif.append(con - cru)
    d = np.array(dif)
    ee = d.std(ddof=1) / np.sqrt(len(d))
    lo, hi = d.mean() - 1.96 * ee, d.mean() + 1.96 * ee
    rate = float(p.clicks.sum() / p.impressions.sum())
    return {
        "experiments": int(p.experiment_id.nunique()),
        "arms": int(len(p)),
        "median_n_times_p": float(np.median(p.impressions * rate)),
        "mean_difference": float(d.mean()),
        "ci95": [float(lo), float(hi)],
        "shrunk_wins_in": float(np.mean(d > 0)),
        "differs_from_zero": bool(lo * hi > 0),
        "mse_relative_change": float(np.mean(mse_s) / np.mean(mse_c) - 1),
    }


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=40)
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
        r = measure(data, args.partitions, args.budget)
        metrics[name] = r
        print(f"{name}  ({r['experiments']:,} experiments | "
              f"median n*p {r['median_n_times_p']:.0f})")
        print(f"  mean squared error          {r['mse_relative_change']*100:+.1f}%")
        print(f"  gain, shrunk minus raw      {r['mean_difference']*100:+.4f} pp"
              f"  95% CI [{r['ci95'][0]*100:+.4f}, {r['ci95'][1]*100:+.4f}]")
        print(f"  shrinkage wins in           {r['shrunk_wins_in']:.0%} of partitions")
        print(f"  does it differ from zero?   "
              f"{'YES' if r['differs_from_zero'] else 'NO'}\n")

    a, b = metrics["filtered_regime"], metrics["full_archive"]
    print("READING")
    if not a["differs_from_zero"] and b["differs_from_zero"] and b["mean_difference"] < 0:
        print("  In the regime they retain, shrinkage is NEUTRAL for the decision,")
        print("  consistent with their theorem. Outside it - 93% of the archive - it")
        print("  degrades selection measurably. Their conclusion holds where tested.")

    metrics["filter"] = {"min_impressions": MIN_IMPRESSIONS, "min_clicks": MIN_CLICKS,
                         "fraction_of_arms_retained": float(passes.mean())}
    metrics["partitions"] = args.partitions
    metrics["budget"] = args.budget
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
