"""Fase E: la decisión entre experiments, donde la precisión sí es heterogénea.

Compara cuatro rules para priorizar qué experiments desplegar, con
budget limitado. Las rules eligen con la mitad de estimación y se miden
en la de evaluación.

    random_rule       la referencia que hay que batir
    raw      ordenar por la gain estimada — la práctica que se pone a prueba
    contraída  la mean contraída entre experiments
    cola       probabilidad posterior de gain positiva

Salida: reports/results/05_cartera.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import console, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "05_cartera.json"
BUDGETS = (0.05, 0.10, 0.25, 0.50, 1.00)


def one_partition(p: pd.DataFrame, seed: int, variance_factor: float):
    # Tres tercios: elegir, estimate, evaluate. Hace falta porque el máximo de un
    # experimento es un estadístico SELECCIONADO y la contracción no se le puede
    # apply directamente (con dos mitades, τ² se estimaba en cero).
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
        "cola": portfolio.tail_priority(c),
    }
    values = {k: portfolio.value_by_budget(c, v, BUDGETS)
               for k, v in rules.items()}
    values["oracle"] = portfolio.oracle(c, BUDGETS)

    # ¿reordena de verdad? fracción de pares cuyo orden cambia frente a la raw
    orden_crudo = np.argsort(-rules["raw"], kind="stable")
    changes = {
        k: float(np.mean(np.argsort(-rules[k], kind="stable") != orden_crudo))
        for k in ("shrunk", "cola")
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
    print(f"factor de diseño del paso 1: {factor:.3f}\n")

    acc: dict[str, dict[float, list[float]]] = {}
    taus, cambios_acum, sizes = [], [], []
    for s in range(args.partitions):
        values, tau2, changes, n = one_partition(p, s, factor)
        taus.append(tau2); cambios_acum.append(changes); sizes.append(n)
        for rule, porb in values.items():
            for b, v in porb.items():
                acc.setdefault(rule, {}).setdefault(b, []).append(v)

    print(f"experiments en la cartera: {int(np.mean(sizes)):,}")
    print(f"tau2 entre experiments = {np.mean(taus):.3e} "
          f"(raíz {np.sqrt(np.mean(taus)):.5f})\n")

    c = pd.DataFrame(cambios_acum)
    print("¿reordena frente a la rule raw?")
    for k in c.columns:
        print(f"  {k:12} cambia la posición de {c[k].mean():.1%} de los experiments")

    print("\nganancia realizada mean, por budget "
          "(puntos porcentuales de rate de clic)")
    cab = "  ".join(f"{int(b*100):>6}%" for b in BUDGETS)
    print(f"{'rule':12} {cab}")
    table = {}
    for rule in ("random", "raw", "shrunk", "cola", "oracle"):
        fila = [np.mean(acc[rule][b]) for b in BUDGETS]
        table[rule] = {str(b): {"mean": float(np.mean(acc[rule][b])),
                                 "sd_across_partitions": float(np.std(acc[rule][b], ddof=1))}
                        for b in BUDGETS}
        print(f"{rule:12} " + "  ".join(f"{v*100:6.3f}" for v in fila))

    print("\ndiferencia contra la rule raw (puntos porcentuales)")
    print(f"{'rule':12} {cab}")
    for rule in ("shrunk", "cola"):
        dif = [np.mean(acc[rule][b]) - np.mean(acc["raw"][b]) for b in BUDGETS]
        gana = [np.mean(np.array(acc[rule][b]) > np.array(acc["raw"][b]))
                for b in BUDGETS]
        print(f"{rule:12} " + "  ".join(f"{d*100:+6.3f}" for d in dif))
        print(f"{'  gana en':12} " + "  ".join(f"{g:5.0%} " for g in gana))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = {
        "partitions": args.partitions,
        "variance_factor": factor,
        "experiments": int(np.mean(sizes)),
        "tau2_entre_experimentos": float(np.mean(taus)),
        "reordering": {k: float(c[k].mean()) for k in c.columns},
        "value_by_budget": table,
    }
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
