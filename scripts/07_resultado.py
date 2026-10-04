"""El resultado del proyecto, con el método congelado.

Produce la tabla que el análisis escrito cita. Corre la especificación de
`reports/results/METODO_CONGELADO.json` sin desviarse: 30 particiones en tres
tercios, factor_v = 1.0 para δ entre experimentos, y las dos métricas que
importan — el error de ESTIMACIÓN y el valor de la DECISIÓN.

Sobre la muestra confirmatoria se corre **una sola vez**.

Salida: reports/results/07_resultado.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from wcab import consola, decision, panel, portfolio, shrinkage, thinning

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "07_resultado.json"
PRESUPUESTOS = (0.05, 0.10, 0.25, 0.50)


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=30)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    acum = {k: {b: [] for b in PRESUPUESTOS}
            for k in ("azar", "cruda", "contraida", "cola", "oraculo")}
    infl, mse_c, mse_s, rho_c, rho_s, alphas, taus = [], [], [], [], [], [], []

    for s in range(args.particiones):
        # --- nivel DENTRO del experimento: la inflación del ganador ---
        dos = thinning.partir(p, fraccion=0.5, semilla=s)
        m2 = shrinkage.mascara_utilizable(dos.estimacion)
        e2 = shrinkage.preparar(dos.estimacion, m2)
        v2 = dos.evaluacion.loc[m2].reset_index(drop=True)
        infl.append(decision.evaluar(e2, v2, regla="crudo").inflacion)

        # --- nivel ENTRE experimentos: estimación contra decisión ---
        el, es, ev = thinning.partir_tres(p, semilla=s)
        m = shrinkage.mascara_utilizable(es)
        el = el.loc[m].reset_index(drop=True)
        ev = ev.loc[m].reset_index(drop=True)
        c = portfolio.construir_tres(el, shrinkage.preparar(es, m), ev)
        t = c.tabla
        media, tau2 = portfolio.contraer_cartera(c)
        v = t["v"].to_numpy()
        alphas.append(float((v / (v + tau2)).mean())); taus.append(tau2)

        d_a = t["delta_estimado"].to_numpy(); d_b = t["delta_realizado"].to_numpy()
        mse_c.append(float(np.mean((d_a - d_b) ** 2)))
        mse_s.append(float(np.mean((media - d_b) ** 2)))
        rho_c.append(float(stats.spearmanr(d_a, d_b).statistic))
        rho_s.append(float(stats.spearmanr(media, d_b).statistic))

        rng = np.random.default_rng(s)
        reglas = {"azar": rng.random(len(t)), "cruda": d_a, "contraida": media,
                  "cola": portfolio.prioridad_cola(c), "oraculo": d_b}
        for k, pr in reglas.items():
            for b, val in portfolio.valor_por_presupuesto(c, pr, PRESUPUESTOS).items():
                acum[k][b].append(val)

    md = lambda x: float(np.mean(x))
    print(f"MUESTRA: {args.muestra}  ({args.particiones} particiones)\n")
    print("EL ESTIMANDO — inflación del ganador dentro del experimento")
    print(f"  {md(infl)*100:.3f} puntos porcentuales\n")
    print("LA PRUEBA DECISIVA — estimación contra decisión, entre experimentos")
    print(f"  error cuadrático medio    cruda {md(mse_c):.4e} -> contraída "
          f"{md(mse_s):.4e}   {100*(md(mse_s)/md(mse_c)-1):+.1f}%")
    print(f"  correlación de orden      cruda {md(rho_c):+.4f}    -> contraída "
          f"{md(rho_s):+.4f}      {md(rho_s)-md(rho_c):+.4f}")
    print(f"  alpha medio {md(alphas):.3f} | tau2 {md(taus):.3e}\n")
    cab = "  ".join(f"{int(b*100):>7}%" for b in PRESUPUESTOS)
    print(f"GANANCIA REALIZADA por presupuesto (puntos porcentuales)\n{'regla':12}{cab}")
    for k in ("azar", "cruda", "contraida", "cola", "oraculo"):
        print(f"{k:12}" + "  ".join(f"{md(acum[k][b])*100:7.3f}" for b in PRESUPUESTOS))
    print(f"\n{'vs cruda':12}{cab}")
    for k in ("contraida", "cola"):
        print(f"{k:12}" + "  ".join(
            f"{(md(acum[k][b])-md(acum['cruda'][b]))*100:+7.3f}" for b in PRESUPUESTOS))
        print(f"{'  gana en':12}" + "  ".join(
            f"{np.mean(np.array(acum[k][b])>np.array(acum['cruda'][b])):6.0%} "
            for b in PRESUPUESTOS))

    cifras = {
        "muestra": args.muestra, "particiones": args.particiones,
        "inflacion_del_ganador": md(infl),
        "estimacion": {"mse_cruda": md(mse_c), "mse_contraida": md(mse_s),
                       "cambio_relativo": md(mse_s) / md(mse_c) - 1,
                       "rho_cruda": md(rho_c), "rho_contraida": md(rho_s)},
        "alpha_medio": md(alphas), "tau2": md(taus),
        "ganancia": {k: {str(b): md(acum[k][b]) for b in PRESUPUESTOS} for k in acum},
        "gana_contra_cruda": {
            k: {str(b): float(np.mean(np.array(acum[k][b]) > np.array(acum["cruda"][b])))
                for b in PRESUPUESTOS} for k in ("contraida", "cola")},
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
