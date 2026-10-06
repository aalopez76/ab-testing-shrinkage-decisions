"""Fase J: BHS, la variante de Meta de 2025, contra la version estandar.

Ajusta el modelo jerarquico de `wcab.shrinkage.bhs` sobre la ventaja entre
experiments y compara las tres rules en estimation y en decision.

El parametro `a` es el diagnostico central: con `a` grande BHS reproduce la
contraccion estandar, asi que ajustarlo es preguntarle a los data cuanta
flexibilidad local necesitan.

Salida: reports/results/10_bhs.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

from wcab import consola, panel, portfolio, shrinkage, thinning
from wcab.shrinkage import bhs

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "10_bhs.json"
BUDGETS = (0.05, 0.10, 0.25)


def main() -> None:
    consola.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=12)
    args = ap.parse_args()

    p = panel.load(args.sample)
    rules = ("raw", "global", "bhs", "cola", "oracle")
    ac = {k: {b: [] for b in BUDGETS} for k in rules}
    aes, lrs, mse = [], [], {"raw": [], "global": [], "bhs": []}

    for s in range(args.partitions):
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        c = portfolio.build_three_way(el.loc[m].reset_index(drop=True),
                                     shrinkage.prepare(es, m),
                                     ev.loc[m].reset_index(drop=True))
        t = c.table
        d_a = t.delta_estimated.to_numpy()
        d_b = t.delta_realized.to_numpy()
        s2 = t.v.to_numpy()

        glob, _ = portfolio.shrink_portfolio(c)
        aj = bhs.fit(d_a, s2)
        post = bhs.posterior_mean(d_a, s2, aj)
        aes.append(aj.a)
        lrs.append(aj.beats_global)
        for k, v in (("raw", d_a), ("global", glob), ("bhs", post)):
            mse[k].append(float(np.mean((v - d_b) ** 2)))

        rng = np.random.default_rng(s)
        for k, pr in (("raw", d_a), ("global", glob), ("bhs", post),
                      ("cola", portfolio.tail_priority(c)), ("oracle", d_b)):
            for b, v in portfolio.value_by_budget(c, pr, BUDGETS).items():
                ac[k][b].append(v)

    md = lambda x: float(np.mean(x))
    print("AJUSTE  (%d partitions, %s)" % (args.partitions, args.sample))
    print("  a = %.2f  [%.2f, %.2f]" % (md(aes), min(aes), max(aes)))
    print("  razon de verosimilitudes contra la global = %.0f" % md(lrs))
    print("  los data %s flexibilidad local\n"
          % ("PIDEN" if md(lrs) > 3.84 else "NO piden"))
    print("ERROR CUADRATICO MEDIO")
    for k in ("raw", "global", "bhs"):
        print("  %-7s %.4e  %+.1f%%"
              % (k, md(mse[k]), 100 * (md(mse[k]) / md(mse["raw"]) - 1)))
    print("\nGANANCIA REALIZADA (pp)")
    print("  %-9s" % "rule" + "".join("%9s" % f"{int(b*100)}%" for b in BUDGETS))
    for k in rules:
        print("  %-9s" % k + "".join("%9.3f" % (md(ac[k][b]) * 100) for b in BUDGETS))

    metrics = {
        "sample": args.sample,
        "partitions": args.partitions,
        "a_mean": md(aes), "a_min": float(min(aes)), "a_max": float(max(aes)),
        "likelihood_ratio": md(lrs),
        "requires_local_flexibility": bool(md(lrs) > 3.84),
        "mse": {k: md(v) for k, v in mse.items()},
        "mse_relative_change": {k: md(mse[k]) / md(mse["raw"]) - 1 for k in mse},
        "gain": {k: {str(b): md(ac[k][b]) for b in BUDGETS} for k in rules},
        "bhs_beats_global_in": {
            str(b): float(np.mean(np.array(ac["bhs"][b]) > np.array(ac["global"][b])))
            for b in BUDGETS},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\ncifras -> %s" % OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
