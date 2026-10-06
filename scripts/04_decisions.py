"""Steps 4 and 5: the winner's inflation, and whether correcting it helps the decision.

This is the project's first end-to-end figure, and the one that can end it early:
if no correction improves the decision, that is the result and the remaining
configurations need not be built.

Rules are compared by selecting on the estimation half and measuring on the
evaluation half, which played no part in selecting. Each split is repeated with
several seeds, and that variation is reported **separately** from sampling
uncertainty: they are two distinct sources and averaging them together would
confuse the two.

Output: reports/results/04_decisions.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import console, decision, panel, shrinkage, thinning
from wcab.diagnostics import noise
from wcab.shrinkage import dispersion

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "04_decisions.json"


def one_partition(p: pd.DataFrame, seed: int, variance_factor: float, tau2_method: str):
    """Run every rule over one split and return their results."""
    part = thinning.split(p, fraction=0.5, seed=seed)

    # A single mask for BOTH halves: were each filtered independently, different
    # arms would be compared and nothing would reveal it.
    m = shrinkage.usable_mask(part.estimation)
    est = shrinkage.prepare(part.estimation, m)
    ev = part.evaluation.loc[m].reset_index(drop=True)

    # tau2 is estimated from the estimation half ONLY: the evaluation half takes
    # part in no decision, not even through the dispersion.
    tau2 = dispersion.estimate(est, method=tau2_method, variance_factor=variance_factor)
    contr = shrinkage.shrink(est, tau2, variance_factor=variance_factor, tau2_method=tau2_method)

    rules = [
        decision.evaluate(est, ev, rule="random", seed=seed),
        decision.evaluate(est, ev, rule="raw"),
        decision.evaluate(est, ev, priority=contr.theta_tilde, rule="shrunk_global"),
    ]
    return rules, contr


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=20)
    ap.add_argument("--tau2-method", default="paule-mandel",
                    choices=list(dispersion.METHODS))
    ap.add_argument("--variance-factor", type=float, default=None,
                    help="design factor; defaults to the one from step 1")
    args = ap.parse_args()

    p = panel.load(args.sample)

    if args.variance_factor is None:
        cal = noise.calibrate(p)
        factors = {"naive": 1.0, "corrected": cal.design_factor}
        print(f"design factor from step 1: {cal.design_factor:.3f}\n")
    else:
        factors = {"given": args.variance_factor}

    output = {"sample": args.sample, "partitions": args.partitions,
              "tau2_method": args.tau2_method, "results": {}}

    for label, factor in factors.items():
        acc: dict[str, list[dict]] = {}
        shrinkages = []
        failures = []
        for s in range(args.partitions):
            rules, contr = one_partition(p, s, factor, args.tau2_method)
            shrinkages.append(contr.summary())
            for r in rules:
                acc.setdefault(r.rule, []).append(r.summary())
            by_rule = {r.rule: r for r in rules}
            failures.append(
                decision.where_it_fails(by_rule["shrunk_global"], by_rule["raw"],
                                        "shrunk", "raw")
            )

        print(f"=== v {label} (factor {factor:.3f}) ===")
        print(f"{'rule':20} {'value':>10} {'regret':>11} {'inflation':>11}")
        table = {}
        for rule, lst in acc.items():
            d = pd.DataFrame(lst)
            table[rule] = {
                k: {"mean": float(d[k].mean()), "sd_across_partitions": float(d[k].std(ddof=1))}
                for k in ("value", "regret", "inflation")
            }
            table[rule]["experiments"] = int(d["experiments"].iloc[0])
            print(f"{rule:20} {d['value'].mean():10.5f} "
                  f"{d['regret'].mean():11.5f} {d['inflation'].mean():11.5f}")

        f = pd.DataFrame(failures)
        print(f"\nshrunk worse than raw in {f['fraction_worse'].mean():.1%} of "
              f"experiments; better in {f['fraction_better'].mean():.1%}; "
              f"equal in {f['fraction_equal'].mean():.1%}")
        c = pd.DataFrame(shrinkages)
        print(f"mean tau2 = {c['tau2'].mean():.3e}  "
              f"(root {np.sqrt(c['tau2'].mean()):.5f})   "
              f"mean alpha = {c['alpha_mean'].mean():.3f}\n")

        output["results"][label] = {
            "variance_factor": factor,
            "rules": table,
            "shrinkage": {k: float(c[k].mean()) for k in
                          ("tau2", "tau", "alpha_mean", "alpha_median")},
            "where_it_fails": {k: float(f[k].mean()) for k in
                               ("fraction_worse", "fraction_better", "fraction_equal")},
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = output
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"metrics -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
