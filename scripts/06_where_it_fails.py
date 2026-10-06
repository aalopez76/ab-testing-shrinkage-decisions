"""Phase F: where shrinkage fails, and why.

Two parts, and the order matters:

1. **Where it fails.** In which experiments shrinkage selects worse than not
   correcting, and what characterises those cases. This is not optional:
   shrinkage improves the aggregate while harming specific cases, and omitting
   which ones would be telling half the story.

2. **Why.** The diagnostics come **after** the comparison, to understand the
   result rather than to filter candidates in advance.

Output: reports/results/06_where_it_fails.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from wcab import console, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "06_where_it_fails.json"


def where_it_fails(p: pd.DataFrame, partitions: int) -> dict:
    """Profile of the experiments where shrinkage selects worse."""
    profiles, fractions = [], []
    for s in range(partitions):
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        el = el.loc[m].reset_index(drop=True)
        ev = ev.loc[m].reset_index(drop=True)
        c = portfolio.build_three_way(el, shrinkage.prepare(es, m), ev)
        t = c.table.copy()
        mean, tau2 = portfolio.shrink_portfolio(c)
        t["shrunk"] = mean
        t["alpha"] = t["v"] / (t["v"] + tau2)

        # at a 10% budget, what each rule selects
        k = max(1, int(round(0.10 * len(t))))
        sel_raw = set(np.argsort(-t["delta_estimated"].to_numpy(), kind="stable")[:k])
        sel_shr = set(np.argsort(-t["shrunk"].to_numpy(), kind="stable")[:k])
        only_raw = sorted(sel_raw - sel_shr)      # those shrinkage DISCARDS
        only_shr = sorted(sel_shr - sel_raw)      # those shrinkage ADDS

        if not only_raw or not only_shr:
            continue
        fractions.append(len(only_raw) / k)
        profiles.append(
            {
                "discarded_delta_realized": float(t["delta_realized"].iloc[only_raw].mean()),
                "added_delta_realized": float(t["delta_realized"].iloc[only_shr].mean()),
                "discarded_alpha": float(t["alpha"].iloc[only_raw].mean()),
                "added_alpha": float(t["alpha"].iloc[only_shr].mean()),
                "discarded_impressions": float(t["impressions"].iloc[only_raw].mean()),
                "added_impressions": float(t["impressions"].iloc[only_shr].mean()),
                "discarded_arms": float(t["arms"].iloc[only_raw].mean()),
                "added_arms": float(t["arms"].iloc[only_shr].mean()),
            }
        )
    d = pd.DataFrame(profiles)
    return {
        "budget": 0.10,
        "fraction_of_selection_changed": float(np.mean(fractions)),
        **{k: float(d[k].mean()) for k in d.columns},
    }


def precision_predicts_parameter(p: pd.DataFrame) -> dict:
    """Does precision predict the parameter? Controlling for period and type.

    An unadjusted correlation between impressions and rate could be confounding:
    if later experiments are larger and also carry lower rates, the gradient
    appears without any structural dependence.

    Here the correlation is computed **within** each week and within each
    experiment type, then averaged. If it survives the control, the dependence
    Chen (*Econometrica*, 2026) warns about is real in these data.
    """
    g = p.groupby("experiment_id").agg(
        n=("impressions", "sum"), c=("clicks", "sum"),
        week=("week", "first"),
        headline=("varies_headline", "first"), image=("varies_image", "first"),
    )
    g["rate"] = g["c"] / g["n"]
    g["kind"] = np.select(
        [g.headline & ~g.image, ~g.headline & g.image, g.headline & g.image],
        ["headline_only", "image_only", "both"], default="none",
    )

    raw = stats.spearmanr(g["n"], g["rate"])

    def within(col: str) -> tuple[float, int]:
        rs, weights = [], []
        for _, blk in g.groupby(col):
            if len(blk) < 30:
                continue
            r = stats.spearmanr(blk["n"], blk["rate"]).statistic
            if np.isfinite(r):
                rs.append(r); weights.append(len(blk))
        if not rs:
            return float("nan"), 0
        return float(np.average(rs, weights=weights)), len(rs)

    r_week, n_week = within("week")
    r_type, n_type = within("kind")

    return {
        "correlation_raw": float(raw.statistic),
        "p_raw": float(raw.pvalue),
        "correlation_within_week": r_week,
        "groups_week": n_week,
        "correlation_within_type": r_type,
        "groups_type": n_type,
        "survives_control": bool(
            np.isfinite(r_week) and r_week < -0.05 and np.isfinite(r_type) and r_type < -0.05
        ),
    }


def proportion_regime(p: pd.DataFrame) -> dict:
    """Are we where the Gaussian approximation to the binomial weakens?

    Chen and Lei (Dec 2025) work the binomial directly precisely for small
    proportions and small samples. The usual rule of thumb asks for n*p >= 10 for
    the normal to approximate well.
    """
    n = p["impressions"].to_numpy(dtype=float)
    rate = float(p["clicks"].sum() / p["impressions"].sum())
    np_ = n * rate
    return {
        "global_rate": rate,
        "median_n": float(np.median(n)),
        "median_n_times_p": float(np.median(np_)),
        "fraction_with_np_below_10": float(np.mean(np_ < 10)),
        "fraction_with_np_below_5": float(np.mean(np_ < 5)),
    }


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=30)
    args = ap.parse_args()

    p = panel.load(args.sample)

    print("=" * 66)
    print("1. WHERE IT FAILS  (10% budget)")
    df = where_it_fails(p, args.partitions)
    print(f"   shrinkage changes {df['fraction_of_selection_changed']:.1%} "
          f"of the selection\n")
    print(f"   {'':24} {'discards':>12} {'adds':>12}")
    for et, a, b in (
        ("realised gain", "discarded_delta_realized", "added_delta_realized"),
        ("alpha", "discarded_alpha", "added_alpha"),
        ("impressions", "discarded_impressions", "added_impressions"),
        ("arms", "discarded_arms", "added_arms"),
    ):
        f = 100 if "gain" in et else 1
        print(f"   {et:24} {df[a]*f:12.3f} {df[b]*f:12.3f}")

    print("\n" + "=" * 66)
    print("2. WHY  (the diagnostics, after the comparison)\n")

    cal = noise.calibrate(p)
    print(f"   a) noise calibration: {'passed' if cal.passed else 'REJECTED'}, "
          f"Q/dof = {cal.q_over_dof:.3f}")

    reg = proportion_regime(p)
    print(f"   b) proportion regime: rate {reg['global_rate']:.4f}, "
          f"median n*p {reg['median_n_times_p']:.1f}")
    print(f"      arms with n*p < 10: {reg['fraction_with_np_below_10']:.1%} | "
          f"< 5: {reg['fraction_with_np_below_5']:.1%}")

    dep = precision_predicts_parameter(p)
    print(f"   c) does precision predict the parameter?")
    print(f"      unadjusted     {dep['correlation_raw']:+.3f} (p={dep['p_raw']:.1e})")
    print(f"      within week    {dep['correlation_within_week']:+.3f} "
          f"({dep['groups_week']} weeks)")
    print(f"      within type    {dep['correlation_within_type']:+.3f} "
          f"({dep['groups_type']} types)")
    print(f"      survives control: {'YES' if dep['survives_control'] else 'no'}")

    metrics = {
        "sample": args.sample,
        "partitions": args.partitions,
        "where_it_fails": df,
        "noise_calibration": cal.to_dict(),
        "proportion_regime": reg,
        "precision_predicts_parameter": dep,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
