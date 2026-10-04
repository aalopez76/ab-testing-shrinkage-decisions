"""Fase H: ¿la conclusión depende del régimen que la literatura filtra?

Coey y Hung (*Empirical Bayes Selection for Value Maximization*, arXiv
2210.03905) hacen esta misma pregunta sobre este mismo archivo. Su montaje,
descrito en su apéndice B, impone dos condiciones:

  1. descartan los brazos con menos de 1 000 impresiones o 100 clics, «para
     asegurar que las aproximaciones de normalidad sean razonables»;
  2. reducen cada experimento a una pareja arbitraria —el brazo con más
     impresiones contra el de segundas más— omitiendo los demás.

La segunda condición quita la selección por resultado, así que su montaje no
contiene la maldición del ganador. La primera conserva el 6.9% de los brazos.

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

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "08_regimen.json"

# el filtro textual de su apéndice B
MIN_IMPRESIONES, MIN_CLICS = 1000, 100


def al_menos_dos_brazos(p: pd.DataFrame) -> pd.DataFrame:
    g = p.groupby("experimento_id").size()
    return p[p.experimento_id.isin(g[g >= 2].index)].reset_index(drop=True)


def medir(p: pd.DataFrame, particiones: int, presupuesto: float) -> dict:
    dif, mse_c, mse_s = [], [], []
    for s in range(particiones):
        el, es, ev = thinning.partir_tres(p, semilla=s)
        m = shrinkage.mascara_utilizable(es)
        c = portfolio.construir_tres(
            el.loc[m].reset_index(drop=True), shrinkage.preparar(es, m),
            ev.loc[m].reset_index(drop=True))
        media, _ = portfolio.contraer_cartera(c)
        d_a = c.tabla.delta_estimado.to_numpy()
        d_b = c.tabla.delta_realizado.to_numpy()
        mse_c.append(float(np.mean((d_a - d_b) ** 2)))
        mse_s.append(float(np.mean((media - d_b) ** 2)))
        cru = portfolio.valor_por_presupuesto(c, d_a, [presupuesto])[presupuesto]
        con = portfolio.valor_por_presupuesto(c, media, [presupuesto])[presupuesto]
        dif.append(con - cru)
    d = np.array(dif)
    ee = d.std(ddof=1) / np.sqrt(len(d))
    lo, hi = d.mean() - 1.96 * ee, d.mean() + 1.96 * ee
    tasa = float(p.clics.sum() / p.impresiones.sum())
    return {
        "experimentos": int(p.experimento_id.nunique()),
        "brazos": int(len(p)),
        "n_por_p_mediana": float(np.median(p.impresiones * tasa)),
        "diferencia_media": float(d.mean()),
        "ic95": [float(lo), float(hi)],
        "contraer_gana_en": float(np.mean(d > 0)),
        "se_distingue_de_cero": bool(lo * hi > 0),
        "mse_cambio_relativo": float(np.mean(mse_s) / np.mean(mse_c) - 1),
    }


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="confirmatorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=40)
    ap.add_argument("--presupuesto", type=float, default=0.05)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    pasa = (p.impresiones >= MIN_IMPRESIONES) & (p.clics >= MIN_CLICS)
    print(f"el filtro de Coey y Hung (>={MIN_IMPRESIONES} impresiones y "
          f">={MIN_CLICS} clics) conserva el {pasa.mean():.1%} de {len(p):,} brazos\n")

    casos = {
        "regimen_filtrado": al_menos_dos_brazos(p[pasa].reset_index(drop=True)),
        "archivo_completo": p,
    }
    cifras = {}
    for nombre, datos in casos.items():
        r = medir(datos, args.particiones, args.presupuesto)
        cifras[nombre] = r
        print(f"{nombre}  ({r['experimentos']:,} experimentos | "
              f"n·p mediana {r['n_por_p_mediana']:.0f})")
        print(f"  error cuadrático medio      {r['mse_cambio_relativo']*100:+.1f}%")
        print(f"  ganancia, contraída − cruda {r['diferencia_media']*100:+.4f} pp"
              f"  IC95 [{r['ic95'][0]*100:+.4f}, {r['ic95'][1]*100:+.4f}]")
        print(f"  contraer gana en            {r['contraer_gana_en']:.0%} de las particiones")
        print(f"  ¿se distingue de cero?      "
              f"{'SÍ' if r['se_distingue_de_cero'] else 'NO'}\n")

    a, b = cifras["regimen_filtrado"], cifras["archivo_completo"]
    print("LECTURA")
    if not a["se_distingue_de_cero"] and b["se_distingue_de_cero"] and b["diferencia_media"] < 0:
        print("  En el régimen que ellos conservan, contraer es NEUTRO para la decisión,")
        print("  consistente con su teorema. Fuera de él —el 93% del archivo— degrada la")
        print("  selección de forma medible. Su conclusión vale donde la probaron.")

    cifras["filtro"] = {"min_impresiones": MIN_IMPRESIONES, "min_clics": MIN_CLICS,
                        "fraccion_de_brazos_que_pasa": float(pasa.mean())}
    cifras["particiones"] = args.particiones
    cifras["presupuesto"] = args.presupuesto
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
