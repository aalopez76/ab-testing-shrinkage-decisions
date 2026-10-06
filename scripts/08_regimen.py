"""Fase H: ¿la conclusión depende del régimen que la literatura filtra?

Coey y Hung (*Empirical Bayes Selection for Value Maximization*, arXiv
2210.03905) hacen esta misma pregunta sobre este mismo archivo. Su montaje,
descrito en su apéndice B, impone dos condiciones:

  1. descartan los arms con menos de 1 000 impressions o 100 clicks, «para
     asegurar que las aproximaciones de normalidad sean razonables»;
  2. reducen cada experimento a una pareja arbitraria —el brazo con más
     impressions contra el de segundas más— omitiendo los demás.

La segunda condición quita la selección por resultado, así que su montaje no
contiene la maldición del ganador. La primera conserva el 6.9% de los arms.

Este script mide lo mismo dentro y fuera de su filtro, con intervalo de
confianza, para saber si su conclusión es general o propia de su régimen.

Salida: reports/results/08_regimen.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import consola, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "08_regimen.json"

# el filtro textual de su apéndice B
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
        "contraer_gana_en": float(np.mean(d > 0)),
        "differs_from_zero": bool(lo * hi > 0),
        "mse_relative_change": float(np.mean(mse_s) / np.mean(mse_c) - 1),
    }


def main() -> None:
    consola.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=40)
    ap.add_argument("--budget", type=float, default=0.05)
    args = ap.parse_args()

    p = panel.load(args.sample)
    pasa = (p.impressions >= MIN_IMPRESSIONS) & (p.clicks >= MIN_CLICKS)
    print(f"el filtro de Coey y Hung (>={MIN_IMPRESSIONS} impressions y "
          f">={MIN_CLICKS} clicks) conserva el {pasa.mean():.1%} de {len(p):,} arms\n")

    casos = {
        "filtered_regime": at_least_two_arms(p[pasa].reset_index(drop=True)),
        "full_archive": p,
    }
    metrics = {}
    for nombre, data in casos.items():
        r = measure(data, args.partitions, args.budget)
        metrics[nombre] = r
        print(f"{nombre}  ({r['experiments']:,} experiments | "
              f"n·p mediana {r['median_n_times_p']:.0f})")
        print(f"  error cuadrático medio      {r['mse_relative_change']*100:+.1f}%")
        print(f"  gain, contraída − raw {r['mean_difference']*100:+.4f} pp"
              f"  IC95 [{r['ci95'][0]*100:+.4f}, {r['ci95'][1]*100:+.4f}]")
        print(f"  shrink gana en            {r['contraer_gana_en']:.0%} de las partitions")
        print(f"  ¿se distingue de cero?      "
              f"{'SÍ' if r['differs_from_zero'] else 'NO'}\n")

    a, b = metrics["filtered_regime"], metrics["full_archive"]
    print("LECTURA")
    if not a["differs_from_zero"] and b["differs_from_zero"] and b["mean_difference"] < 0:
        print("  En el régimen que ellos conservan, shrink es NEUTRO para la decisión,")
        print("  consistente con su teorema. Fuera de él —el 93% del archivo— degrada la")
        print("  selección de forma medible. Su conclusión vale donde la probaron.")

    metrics["filtro"] = {"min_impressions": MIN_IMPRESSIONS, "min_clicks": MIN_CLICKS,
                        "fraccion_de_brazos_que_pasa": float(pasa.mean())}
    metrics["partitions"] = args.partitions
    metrics["budget"] = args.budget
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
