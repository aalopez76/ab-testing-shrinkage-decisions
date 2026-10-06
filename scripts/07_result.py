"""The project's result, with the method frozen.

Produces the table the written analysis cites. It runs the specification in
`reports/results/FROZEN_METHOD.json` without deviation: 30 three-way splits, a
variance factor of 1.0 for the between-experiment delta, and the two metrics that
matter - ESTIMATION error and DECISION value.

On the confirmatory sample it is run **once**.

Output: reports/results/07_result.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from wcab import console, decision, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "07_result.json"
BUDGETS = (0.05, 0.10, 0.25, 0.50)


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=30)
    args = ap.parse_args()

    p = panel.load(args.sample)
    acc = {k: {b: [] for b in BUDGETS}
            for k in ("random", "raw", "shrunk", "tail", "oracle")}
    infl, mse_c, mse_s, rho_c, rho_s, alphas, taus = [], [], [], [], [], [], []

    for s in range(args.partitions):
        # --- WITHIN-experiment level: the winner's inflation ---
        two = thinning.split(p, fraction=0.5, seed=s)
        m2 = shrinkage.usable_mask(two.estimation)
        e2 = shrinkage.prepare(two.estimation, m2)
        v2 = two.evaluation.loc[m2].reset_index(drop=True)
        infl.append(decision.evaluate(e2, v2, rule="raw").inflation)

        # --- BETWEEN-experiments level: estimation against decision ---
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        el = el.loc[m].reset_index(drop=True)
        ev = ev.loc[m].reset_index(drop=True)
        c = portfolio.build_three_way(el, shrinkage.prepare(es, m), ev)
        t = c.table
        mean, tau2 = portfolio.shrink_portfolio(c)
        v = t["v"].to_numpy()
        alphas.append(float((v / (v + tau2)).mean())); taus.append(tau2)

        d_a = t["delta_estimated"].to_numpy(); d_b = t["delta_realized"].to_numpy()
        mse_c.append(float(np.mean((d_a - d_b) ** 2)))
        mse_s.append(float(np.mean((mean - d_b) ** 2)))
        rho_c.append(float(stats.spearmanr(d_a, d_b).statistic))
        rho_s.append(float(stats.spearmanr(mean, d_b).statistic))

        rng = np.random.default_rng(s)
        rules = {"random": rng.random(len(t)), "raw": d_a, "shrunk": mean,
                  "tail": portfolio.tail_priority(c), "oracle": d_b}
        for k, pr in rules.items():
            for b, val in portfolio.value_by_budget(c, pr, BUDGETS).items():
                acc[k][b].append(val)

    md = lambda x: float(np.mean(x))
    print(f"SAMPLE: {args.sample}  ({args.partitions} partitions)\n")
    print("THE ESTIMAND - the winner's inflation within an experiment")
    print(f"  {md(infl)*100:.3f} puntos porcentuales\n")
    print("THE DECISIVE TEST - estimation against decision, between experiments")
    print(f"  mean squared error      raw {md(mse_c):.4e} -> shrunk "
          f"{md(mse_s):.4e}   {100*(md(mse_s)/md(mse_c)-1):+.1f}%")
    print(f"  rank correlation        raw {md(rho_c):+.4f}    -> shrunk "
          f"{md(rho_s):+.4f}      {md(rho_s)-md(rho_c):+.4f}")
    print(f"  alpha medio {md(alphas):.3f} | tau2 {md(taus):.3e}\n")
    cab = "  ".join(f"{int(b*100):>7}%" for b in BUDGETS)
    print(f"GANANCIA REALIZADA por budget (puntos porcentuales)\n{'rule':12}{cab}")
    for k in ("random", "raw", "shrunk", "tail", "oracle"):
        print(f"{k:12}" + "  ".join(f"{md(acc[k][b])*100:7.3f}" for b in BUDGETS))
    print(f"\n{'vs raw':12}{cab}")
    for k in ("shrunk", "tail"):
        print(f"{k:12}" + "  ".join(
            f"{(md(acc[k][b])-md(acc['raw'][b]))*100:+7.3f}" for b in BUDGETS))
        print(f"{'  gana en':12}" + "  ".join(
            f"{np.mean(np.array(acc[k][b])>np.array(acc['raw'][b])):6.0%} "
            for b in BUDGETS))

    metrics = {
        "sample": args.sample, "partitions": args.partitions,
        "winner_inflation": md(infl),
        "estimation": {"mse_raw": md(mse_c), "mse_shrunk": md(mse_s),
                       "relative_change": md(mse_s) / md(mse_c) - 1,
                       "rho_raw": md(rho_c), "rho_shrunk": md(rho_s)},
        "alpha_mean": md(alphas), "tau2": md(taus),
        "gain": {k: {str(b): md(acc[k][b]) for b in BUDGETS} for k in acc},
        "beats_raw_in": {
            k: {str(b): float(np.mean(np.array(acc[k][b]) > np.array(acc["raw"][b])))
                for b in BUDGETS} for k in ("shrunk", "tail")},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
