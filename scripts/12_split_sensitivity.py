"""How much the published numbers depend on how the counts were split.

Every figure in this project is measured on held-out parts of the same counts,
and the proportions of that split are a choice. In data thinning the fraction
governs a real tradeoff rather than a detail: it decides how much information
goes to the task being performed as against the task of evaluating it, and its
optimal value depends on the problem at hand (Neufeld et al., JMLR 2024,
which states exactly that and gives no general recommended range). The
tradeoff is well established; what was not measured is how THESE estimates on
THIS archive respond to it, which is what this script reports.

Two different splits are at work and they are varied separately:

  - The winner's inflation uses a BINARY split: one half selects the winning
    arm, the other scores what it delivered. Its parameter is one fraction.
  - The between-experiment quantities use a THREE-WAY split: one part selects,
    one estimates the advantage, one evaluates. Its parameter is three shares.

The published results use 0.5 and equal thirds. Those rows are reproduced here
so the comparison is against the same code path, not against a recollection.

Stage 2: this is a post-confirmatory robustness check, not a pre-specified
analysis. It is read as evidence about the published numbers' sensitivity, not
as a new finding.

Output: reports/results/12_split_sensitivity.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

from wcab import console, decision, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "12_split_sensitivity.json"

# The binary fractions for the inflation estimate. 0.5 is what is published.
FRACTIONS = (0.3, 0.4, 0.5, 0.6, 0.7)

# Shares for (select, estimate, evaluate). Equal thirds is what is published.
SHARES = {
    "equal thirds (published)": (1 / 3, 1 / 3, 1 / 3),
    "more to evaluation": (0.25, 0.25, 0.50),
    "more to selection": (0.50, 0.25, 0.25),
    "more to estimation": (0.25, 0.50, 0.25),
}


def inflation_at(p, fraction: float, partitions: int) -> list[float]:
    """The winner's inflation, over repeated binary splits at `fraction`."""
    out = []
    for s in range(partitions):
        two = thinning.split(p, fraction=fraction, seed=s)
        mask = shrinkage.usable_mask(two.estimation)
        estimated = shrinkage.prepare(two.estimation, mask)
        realised = two.evaluation.loc[mask].reset_index(drop=True)
        out.append(decision.evaluate(estimated, realised, rule="raw").inflation)
    return out


def between_at(p, shares: tuple[float, float, float], partitions: int) -> dict:
    """Estimation error and realised gain, over repeated three-way splits."""
    mse_raw, mse_shrunk, gain_raw, gain_shrunk = [], [], [], []
    for s in range(partitions):
        select, estimate, evaluate = thinning.split_three_way(
            p, seed=s, shares=shares
        )
        mask = shrinkage.usable_mask(estimate)
        select = select.loc[mask].reset_index(drop=True)
        evaluate = evaluate.loc[mask].reset_index(drop=True)
        c = portfolio.build_three_way(
            select, shrinkage.prepare(estimate, mask), evaluate
        )
        table = c.table
        mean, _ = portfolio.shrink_portfolio(c)

        d_est = table["delta_estimated"].to_numpy()
        d_real = table["delta_realized"].to_numpy()
        mse_raw.append(float(np.mean((d_est - d_real) ** 2)))
        mse_shrunk.append(float(np.mean((mean - d_real) ** 2)))
        gain_raw.append(portfolio.value_by_budget(c, d_est, (0.05,))[0.05])
        gain_shrunk.append(portfolio.value_by_budget(c, mean, (0.05,))[0.05])

    raw, shrunk = float(np.mean(mse_raw)), float(np.mean(mse_shrunk))
    return {
        "mse_raw": raw,
        "mse_shrunk": shrunk,
        "mse_relative_change": (shrunk - raw) / raw,
        "gain_raw": float(np.mean(gain_raw)),
        "gain_shrunk": float(np.mean(gain_shrunk)),
        "gain_difference": float(np.mean(gain_shrunk) - np.mean(gain_raw)),
    }


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=10)
    args = ap.parse_args()

    p = panel.load(args.sample)
    result = {"sample": args.sample, "partitions": args.partitions}

    print("WINNER'S INFLATION, by binary split fraction")
    print(f"  {'fraction':>10}{'inflation (pp)':>18}{'vs published':>16}")
    by_fraction = {}
    for f in FRACTIONS:
        values = inflation_at(p, f, args.partitions)
        by_fraction[f"{f}"] = {
            "mean": float(np.mean(values)),
            "sd_across_partitions": float(np.std(values, ddof=1)),
        }
    base = by_fraction["0.5"]["mean"]
    for f in FRACTIONS:
        m = by_fraction[f"{f}"]["mean"]
        by_fraction[f"{f}"]["relative_to_published"] = (m - base) / base
        mark = "  <- published" if f == 0.5 else ""
        print(f"  {f:>10.2f}{m * 100:>18.4f}{(m - base) / base:>15.1%}{mark}")
    result["inflation_by_fraction"] = by_fraction

    print("\nBETWEEN-EXPERIMENT ESTIMATES, by three-way shares")
    print(f"  {'shares':>26}{'MSE change':>14}{'gain diff (pp)':>18}")
    by_shares = {}
    for label, shares in SHARES.items():
        m = between_at(p, shares, args.partitions)
        m["shares"] = list(shares)
        by_shares[label] = m
        print(f"  {label:>26}{m['mse_relative_change']:>13.1%}"
              f"{m['gain_difference'] * 100:>18.4f}")
    result["between_by_shares"] = by_shares

    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
