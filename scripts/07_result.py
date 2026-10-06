"""El resultado del proyecto, con el método congelado.

Produce la table que el análisis escrito cita. Corre la especificación de
`reports/results/METODO_CONGELADO.json` sin desviarse: 30 partitions en tres
tercios, variance_factor = 1.0 para δ entre experiments, y las dos métricas que
importan — el error de ESTIMACIÓN y el value de la DECISIÓN.

Sobre la sample confirmatoria se corre **una sola vez**.

Salida: reports/results/07_resultado.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from wcab import console, decision, panel, portfolio, shrinkage, thinning

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "07_resultado.json"
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
            for k in ("random", "raw", "shrunk", "cola", "oracle")}
    infl, mse_c, mse_s, rho_c, rho_s, alphas, taus = [], [], [], [], [], [], []

    for s in range(args.partitions):
        # --- nivel DENTRO del experimento: la inflación del ganador ---
        dos = thinning.split(p, fraction=0.5, seed=s)
        m2 = shrinkage.usable_mask(dos.estimation)
        e2 = shrinkage.prepare(dos.estimation, m2)
        v2 = dos.evaluation.loc[m2].reset_index(drop=True)
        infl.append(decision.evaluate(e2, v2, rule="raw").inflation)

        # --- nivel ENTRE experiments: estimación contra decisión ---
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
                  "cola": portfolio.tail_priority(c), "oracle": d_b}
        for k, pr in rules.items():
            for b, val in portfolio.value_by_budget(c, pr, BUDGETS).items():
                acc[k][b].append(val)

    md = lambda x: float(np.mean(x))
    print(f"MUESTRA: {args.sample}  ({args.partitions} partitions)\n")
    print("EL ESTIMANDO — inflación del ganador dentro del experimento")
    print(f"  {md(infl)*100:.3f} puntos porcentuales\n")
    print("LA PRUEBA DECISIVA — estimación contra decisión, entre experiments")
    print(f"  error cuadrático medio    raw {md(mse_c):.4e} -> contraída "
          f"{md(mse_s):.4e}   {100*(md(mse_s)/md(mse_c)-1):+.1f}%")
    print(f"  correlación de orden      raw {md(rho_c):+.4f}    -> contraída "
          f"{md(rho_s):+.4f}      {md(rho_s)-md(rho_c):+.4f}")
    print(f"  alpha medio {md(alphas):.3f} | tau2 {md(taus):.3e}\n")
    cab = "  ".join(f"{int(b*100):>7}%" for b in BUDGETS)
    print(f"GANANCIA REALIZADA por budget (puntos porcentuales)\n{'rule':12}{cab}")
    for k in ("random", "raw", "shrunk", "cola", "oracle"):
        print(f"{k:12}" + "  ".join(f"{md(acc[k][b])*100:7.3f}" for b in BUDGETS))
    print(f"\n{'vs raw':12}{cab}")
    for k in ("shrunk", "cola"):
        print(f"{k:12}" + "  ".join(
            f"{(md(acc[k][b])-md(acc['raw'][b]))*100:+7.3f}" for b in BUDGETS))
        print(f"{'  gana en':12}" + "  ".join(
            f"{np.mean(np.array(acc[k][b])>np.array(acc['raw'][b])):6.0%} "
            for b in BUDGETS))

    metrics = {
        "sample": args.sample, "partitions": args.partitions,
        "inflacion_del_ganador": md(infl),
        "estimation": {"mse_raw": md(mse_c), "mse_shrunk": md(mse_s),
                       "relative_change": md(mse_s) / md(mse_c) - 1,
                       "rho_raw": md(rho_c), "rho_shrunk": md(rho_s)},
        "alpha_mean": md(alphas), "tau2": md(taus),
        "gain": {k: {str(b): md(acc[k][b]) for b in BUDGETS} for k in acc},
        "beats_raw_in": {
            k: {str(b): float(np.mean(np.array(acc[k][b]) > np.array(acc["raw"][b])))
                for b in BUDGETS} for k in ("shrunk", "cola")},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
