"""Fase J: BHS, la variante de Meta de 2025, contra la version estandar.

Ajusta el modelo jerarquico de `wcab.shrinkage.bhs` sobre la ventaja entre
experimentos y compara las tres reglas en estimacion y en decision.

El parametro `a` es el diagnostico central: con `a` grande BHS reproduce la
contraccion estandar, asi que ajustarlo es preguntarle a los datos cuanta
flexibilidad local necesitan.

Salida: reports/results/10_bhs.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

from wcab import consola, panel, portfolio, shrinkage, thinning
from wcab.shrinkage import bhs

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "10_bhs.json"
PRESUPUESTOS = (0.05, 0.10, 0.25)


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="confirmatorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=12)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    reglas = ("cruda", "global", "bhs", "cola", "oraculo")
    ac = {k: {b: [] for b in PRESUPUESTOS} for k in reglas}
    aes, lrs, mse = [], [], {"cruda": [], "global": [], "bhs": []}

    for s in range(args.particiones):
        el, es, ev = thinning.partir_tres(p, semilla=s)
        m = shrinkage.mascara_utilizable(es)
        c = portfolio.construir_tres(el.loc[m].reset_index(drop=True),
                                     shrinkage.preparar(es, m),
                                     ev.loc[m].reset_index(drop=True))
        t = c.tabla
        d_a = t.delta_estimado.to_numpy()
        d_b = t.delta_realizado.to_numpy()
        s2 = t.v.to_numpy()

        glob, _ = portfolio.contraer_cartera(c)
        aj = bhs.ajustar(d_a, s2)
        post = bhs.media_posterior(d_a, s2, aj)
        aes.append(aj.a)
        lrs.append(aj.gana_a_la_global)
        for k, v in (("cruda", d_a), ("global", glob), ("bhs", post)):
            mse[k].append(float(np.mean((v - d_b) ** 2)))

        rng = np.random.default_rng(s)
        for k, pr in (("cruda", d_a), ("global", glob), ("bhs", post),
                      ("cola", portfolio.prioridad_cola(c)), ("oraculo", d_b)):
            for b, v in portfolio.valor_por_presupuesto(c, pr, PRESUPUESTOS).items():
                ac[k][b].append(v)

    md = lambda x: float(np.mean(x))
    print("AJUSTE  (%d particiones, %s)" % (args.particiones, args.muestra))
    print("  a = %.2f  [%.2f, %.2f]" % (md(aes), min(aes), max(aes)))
    print("  razon de verosimilitudes contra la global = %.0f" % md(lrs))
    print("  los datos %s flexibilidad local\n"
          % ("PIDEN" if md(lrs) > 3.84 else "NO piden"))
    print("ERROR CUADRATICO MEDIO")
    for k in ("cruda", "global", "bhs"):
        print("  %-7s %.4e  %+.1f%%"
              % (k, md(mse[k]), 100 * (md(mse[k]) / md(mse["cruda"]) - 1)))
    print("\nGANANCIA REALIZADA (pp)")
    print("  %-9s" % "regla" + "".join("%9s" % f"{int(b*100)}%" for b in PRESUPUESTOS))
    for k in reglas:
        print("  %-9s" % k + "".join("%9.3f" % (md(ac[k][b]) * 100) for b in PRESUPUESTOS))

    cifras = {
        "muestra": args.muestra,
        "particiones": args.particiones,
        "a_medio": md(aes), "a_min": float(min(aes)), "a_max": float(max(aes)),
        "razon_de_verosimilitudes": md(lrs),
        "piden_flexibilidad_local": bool(md(lrs) > 3.84),
        "mse": {k: md(v) for k, v in mse.items()},
        "mse_cambio_relativo": {k: md(mse[k]) / md(mse["cruda"]) - 1 for k in mse},
        "ganancia": {k: {str(b): md(ac[k][b]) for b in PRESUPUESTOS} for k in reglas},
        "bhs_gana_a_global_en": {
            str(b): float(np.mean(np.array(ac["bhs"][b]) > np.array(ac["global"][b])))
            for b in PRESUPUESTOS},
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\ncifras -> %s" % SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
