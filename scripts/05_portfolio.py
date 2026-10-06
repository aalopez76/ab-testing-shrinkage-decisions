"""Phase E: the decision between experiments, where precision is heterogeneous.

Compares four rules for prioritising which experiments to deploy under a limited
budget. The rules select on the estimation half and are scored on the evaluation
half.

    random  the benchmark that must be beaten
    raw     rank by estimated gain - the practice being put to the test
    shrunk  the shrunken mean between experiments
    tail    posterior probability of a positive gain

Output: reports/results/05_portfolio.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import console, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "05_portfolio.json"
BUDGETS = (0.05, 0.10, 0.25, 0.50, 1.00)


def one_partition(p: pd.DataFrame, seed: int, variance_factor: float):
    # Three thirds: select, estimate, evaluate. Necessary because an experiment's
    # maximum is a SELECTED statistic to which shrinkage cannot be applied
    # directly (with two halves, tau squared was estimated as zero).
    el, es, ev = thinning.split_three_way(p, seed=seed)
    m = shrinkage.usable_mask(es)
    el = el.loc[m].reset_index(drop=True)
    es = shrinkage.prepare(es, m).assign()
    ev = ev.loc[m].reset_index(drop=True)
    es = es.assign(v=es["v"] * variance_factor)

    c = portfolio.build_three_way(el, es, ev)
    rng = np.random.default_rng(seed)

    mean, tau2 = portfolio.shrink_portfolio(c)
    rules = {
        "random": rng.random(len(c)),
        "raw": portfolio.raw_priority(c),
        "shrunk": mean,
        "tail": portfolio.tail_priority(c),
    }
    values = {k: portfolio.value_by_budget(c, v, BUDGETS)
               for k, v in rules.items()}
    values["oracle"] = portfolio.oracle(c, BUDGETS)

    # does it genuinely reorder? fraction of positions that change versus raw
    raw_order = np.argsort(-rules["raw"], kind="stable")
    changes = {
        k: float(np.mean(np.argsort(-rules[k], kind="stable") != raw_order))
        for k in ("shrunk", "tail")
    }
    return values, tau2, changes, len(c)


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=20)
    args = ap.parse_args()

    p = panel.load(args.sample)
    factor = noise.calibrate(p).design_factor
    print(f"design factor from step 1: {factor:.3f}\n")

    acc: dict[str, dict[float, list[float]]] = {}
    taus, change_acc, sizes = [], [], []
    for s in range(args.partitions):
        values, tau2, changes, n = one_partition(p, s, factor)
        taus.append(tau2); change_acc.append(changes); sizes.append(n)
        for rule, by_budget in values.items():
            for b, v in by_budget.items():
                acc.setdefault(rule, {}).setdefault(b, []).append(v)

    print(f"experiments in the portfolio: {int(np.mean(sizes)):,}")
    print(f"tau2 between experiments = {np.mean(taus):.3e} "
          f"(raíz {np.sqrt(np.mean(taus)):.5f})\n")

    c = pd.DataFrame(change_acc)
    print("does it reorder against the raw rule?")
    for k in c.columns:
        print(f"  {k:12} changes the position of {c[k].mean():.1%} of experiments")

    print("\nganancia realizada mean, por budget "
          "(puntos porcentuales de rate de clic)")
    cab = "  ".join(f"{int(b*100):>6}%" for b in BUDGETS)
    print(f"{'rule':12} {cab}")
    table = {}
    for rule in ("random", "raw", "shrunk", "tail", "oracle"):
        row = [np.mean(acc[rule][b]) for b in BUDGETS]
        table[rule] = {str(b): {"mean": float(np.mean(acc[rule][b])),
                                 "sd_across_partitions": float(np.std(acc[rule][b], ddof=1))}
                        for b in BUDGETS}
        print(f"{rule:12} " + "  ".join(f"{v*100:6.3f}" for v in row))

    print("\ndifference against the raw rule (percentage points)")
    print(f"{'rule':12} {cab}")
    for rule in ("shrunk", "tail"):
        dif = [np.mean(acc[rule][b]) - np.mean(acc["raw"][b]) for b in BUDGETS]
        wins = [np.mean(np.array(acc[rule][b]) > np.array(acc["raw"][b]))
                for b in BUDGETS]
        print(f"{rule:12} " + "  ".join(f"{d*100:+6.3f}" for d in dif))
        print(f"{'  wins in':12} " + "  ".join(f"{g:5.0%} " for g in wins))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = {
        "partitions": args.partitions,
        "variance_factor": factor,
        "experiments": int(np.mean(sizes)),
        "tau2_between_experiments": float(np.mean(taus)),
        "reordering": {k: float(c[k].mean()) for k in c.columns},
        "value_by_budget": table,
    }
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfigures -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
