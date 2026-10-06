"""Pasos 4 y 5: la inflación del ganador y si corregirla improvement la decisión.

Esta es la primera cifra de punta a punta del proyecto, y la que puede
terminarlo temprano: si ninguna corrección improvement la decisión, ése es el
resultado y no hace falta build las configuraciones restantes.

Las rules se comparan eligiendo con la mitad de estimación y midiendo en la de
evaluación, que no participó en elegir. Cada partición se repite con varias
semillas, y esa variación se reporta **por separado** de la incertidumbre
muestral: son dos fuentes distintas y promediarlas juntas confundiría.

Salida: reports/results/04_decisiones.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import consola, decision, panel, shrinkage, thinning
from wcab.diagnostics import noise
from wcab.shrinkage import dispersion

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "04_decisiones.json"


def one_partition(p: pd.DataFrame, seed: int, variance_factor: float, tau2_method: str):
    """Corre todas las rules sobre una partición y devuelve sus results."""
    part = thinning.split(p, fraction=0.5, seed=seed)

    # Una sola máscara para las DOS mitades: si cada una se filtrara por su
    # cuenta se compareían arms distintos y nada lo delataría.
    m = shrinkage.usable_mask(part.estimation)
    est = shrinkage.prepare(part.estimation, m)
    ev = part.evaluation.loc[m].reset_index(drop=True)

    # tau2 se estima SOLO con la mitad de estimación: la de evaluación no
    # participa en ninguna decisión, ni siquiera a través de la dispersión.
    tau2 = dispersion.estimate(est, method=tau2_method, variance_factor=variance_factor)
    contr = shrinkage.shrink(est, tau2, variance_factor=variance_factor, tau2_method=tau2_method)

    rules = [
        decision.evaluate(est, ev, rule="random", seed=seed),
        decision.evaluate(est, ev, rule="raw"),
        decision.evaluate(est, ev, priority=contr.theta_tilde, rule="shrunk_global"),
    ]
    return rules, contr


def main() -> None:
    consola.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=20)
    ap.add_argument("--method-tau2", default="paule-mandel",
                    choices=list(dispersion.METHODS))
    ap.add_argument("--factor-v", type=float, default=None,
                    help="factor de diseño; por omisión, el del paso 1")
    args = ap.parse_args()

    p = panel.load(args.sample)

    if args.variance_factor is None:
        cal = noise.calibrate(p)
        factores = {"ingenuo": 1.0, "corregido": cal.design_factor}
        print(f"factor de diseño del paso 1: {cal.design_factor:.3f}\n")
    else:
        factores = {"indicado": args.variance_factor}

    output = {"sample": args.sample, "partitions": args.partitions,
              "tau2_method": args.tau2_method, "results": {}}

    for label, factor in factores.items():
        acc: dict[str, list[dict]] = {}
        contracciones = []
        fallos = []
        for s in range(args.partitions):
            rules, contr = one_partition(p, s, factor, args.tau2_method)
            contracciones.append(contr.summary())
            for r in rules:
                acc.setdefault(r.rule, []).append(r.summary())
            porreg = {r.rule: r for r in rules}
            fallos.append(
                decision.where_it_fails(porreg["shrunk_global"], porreg["raw"],
                                     "contraído", "raw")
            )

        print(f"=== v {label} (factor {factor:.3f}) ===")
        print(f"{'rule':20} {'value':>10} {'arrepent.':>11} {'inflación':>11}")
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

        f = pd.DataFrame(fallos)
        print(f"\ncontraído peor que crudo en {f['fraccion_peor'].mean():.1%} de los "
              f"experiments; mejor en {f['fraccion_mejor'].mean():.1%}; "
              f"igual en {f['fraccion_igual'].mean():.1%}")
        c = pd.DataFrame(contracciones)
        print(f"tau2 medio = {c['tau2'].mean():.3e}  "
              f"(raíz {np.sqrt(c['tau2'].mean()):.5f})   "
              f"alpha medio = {c['alpha_mean'].mean():.3f}\n")

        output["results"][label] = {
            "variance_factor": factor,
            "rules": table,
            "contraccion": {k: float(c[k].mean()) for k in
                            ("tau2", "tau", "alpha_mean", "alpha_median")},
            "where_it_fails": {k: float(f[k].mean()) for k in
                            ("fraccion_peor", "fraccion_mejor", "fraccion_igual")},
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = output
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"metrics -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
