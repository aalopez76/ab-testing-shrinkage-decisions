"""Fase F: dónde falla la contracción, y por qué.

Dos partes, y el orden importa (ver `.claude/rules/metodo.md`):

1. **Dónde falla.** En qué experimentos la contracción elige peor que no
   corregir, y qué caracteriza a esos casos. No es opcional: contraer mejora el
   conjunto y perjudica casos concretos, y omitir cuáles sería contar la mitad.

2. **Por qué.** Los diagnósticos vienen **después** de la comparación, para
   entender el resultado y no para filtrar candidatos de entrada.

Salida: reports/results/06_donde_falla.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from wcab import consola, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "06_donde_falla.json"


def donde_falla(p: pd.DataFrame, particiones: int) -> dict:
    """Perfil de los experimentos donde contraer elige peor."""
    perfiles, fracciones = [], []
    for s in range(particiones):
        el, es, ev = thinning.partir_tres(p, semilla=s)
        m = shrinkage.mascara_utilizable(es)
        el = el.loc[m].reset_index(drop=True)
        ev = ev.loc[m].reset_index(drop=True)
        c = portfolio.construir_tres(el, shrinkage.preparar(es, m), ev)
        t = c.tabla.copy()
        media, tau2 = portfolio.contraer_cartera(c)
        t["contraida"] = media
        t["alpha"] = t["v"] / (t["v"] + tau2)

        # con presupuesto del 10%, qué elige cada regla
        k = max(1, int(round(0.10 * len(t))))
        sel_cru = set(np.argsort(-t["delta_estimado"].to_numpy(), kind="stable")[:k])
        sel_con = set(np.argsort(-t["contraida"].to_numpy(), kind="stable")[:k])
        solo_cru = sorted(sel_cru - sel_con)      # los que contraer DESCARTA
        solo_con = sorted(sel_con - sel_cru)      # los que contraer AÑADE

        if not solo_cru or not solo_con:
            continue
        fracciones.append(len(solo_cru) / k)
        perfiles.append(
            {
                "descartados_delta_realizado": float(t["delta_realizado"].iloc[solo_cru].mean()),
                "anadidos_delta_realizado": float(t["delta_realizado"].iloc[solo_con].mean()),
                "descartados_alpha": float(t["alpha"].iloc[solo_cru].mean()),
                "anadidos_alpha": float(t["alpha"].iloc[solo_con].mean()),
                "descartados_impresiones": float(t["impresiones"].iloc[solo_cru].mean()),
                "anadidos_impresiones": float(t["impresiones"].iloc[solo_con].mean()),
                "descartados_brazos": float(t["brazos"].iloc[solo_cru].mean()),
                "anadidos_brazos": float(t["brazos"].iloc[solo_con].mean()),
            }
        )
    d = pd.DataFrame(perfiles)
    return {
        "presupuesto": 0.10,
        "fraccion_de_la_seleccion_que_cambia": float(np.mean(fracciones)),
        **{k: float(d[k].mean()) for k in d.columns},
    }


def precision_predice_parametro(p: pd.DataFrame) -> dict:
    """¿La precisión predice el parámetro? Controlando por periodo y tipo.

    La auditoría previa midió una correlación cruda de -0.15 entre impresiones
    y tasa, y quedó pendiente comprobar que no fuera confusión: si los
    experimentos tardíos son más grandes y además tienen tasas más bajas, el
    gradiente aparece sin dependencia estructural.

    Aquí se calcula la correlación **dentro** de cada semana y dentro de cada
    tipo de experimento, y se promedia. Si sobrevive al control, la dependencia
    que advierte Chen (*Econometrica*, 2026) es real en estos datos.
    """
    g = p.groupby("experimento_id").agg(
        n=("impresiones", "sum"), c=("clics", "sum"),
        semana=("semana", "first"),
        titular=("varia_titular", "first"), imagen=("varia_imagen", "first"),
    )
    g["tasa"] = g["c"] / g["n"]
    g["tipo"] = np.select(
        [g.titular & ~g.imagen, ~g.titular & g.imagen, g.titular & g.imagen],
        ["solo_titular", "solo_imagen", "ambos"], default="ninguno",
    )

    cruda = stats.spearmanr(g["n"], g["tasa"])

    def dentro_de(col: str) -> tuple[float, int]:
        rs, pesos = [], []
        for _, blk in g.groupby(col):
            if len(blk) < 30:
                continue
            r = stats.spearmanr(blk["n"], blk["tasa"]).statistic
            if np.isfinite(r):
                rs.append(r); pesos.append(len(blk))
        if not rs:
            return float("nan"), 0
        return float(np.average(rs, weights=pesos)), len(rs)

    r_sem, n_sem = dentro_de("semana")
    r_tipo, n_tipo = dentro_de("tipo")

    return {
        "correlacion_cruda": float(cruda.statistic),
        "p_cruda": float(cruda.pvalue),
        "correlacion_dentro_de_semana": r_sem,
        "grupos_semana": n_sem,
        "correlacion_dentro_de_tipo": r_tipo,
        "grupos_tipo": n_tipo,
        "sobrevive_al_control": bool(
            np.isfinite(r_sem) and r_sem < -0.05 and np.isfinite(r_tipo) and r_tipo < -0.05
        ),
    }


def regimen_de_la_proporcion(p: pd.DataFrame) -> dict:
    """¿Estamos donde la aproximación gaussiana de la binomial flaquea?

    Chen y Lei (dic-2025) trabajan la binomial directamente justamente para
    proporciones y muestras pequeñas. La regla de dedo habitual pide n·p ≥ 10
    para que la normal aproxime bien.
    """
    n = p["impresiones"].to_numpy(dtype=float)
    tasa = float(p["clics"].sum() / p["impresiones"].sum())
    np_ = n * tasa
    return {
        "tasa_global": tasa,
        "n_mediana": float(np.median(n)),
        "n_por_p_mediana": float(np.median(np_)),
        "fraccion_con_np_menor_10": float(np.mean(np_ < 10)),
        "fraccion_con_np_menor_5": float(np.mean(np_ < 5)),
    }


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=30)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)

    print("=" * 66)
    print("1. DÓNDE FALLA  (presupuesto 10%)")
    df = donde_falla(p, args.particiones)
    print(f"   la contracción cambia el {df['fraccion_de_la_seleccion_que_cambia']:.1%} "
          f"de la selección\n")
    print(f"   {'':24} {'descarta':>12} {'añade':>12}")
    for et, a, b in (
        ("ganancia realizada", "descartados_delta_realizado", "anadidos_delta_realizado"),
        ("alpha", "descartados_alpha", "anadidos_alpha"),
        ("impresiones", "descartados_impresiones", "anadidos_impresiones"),
        ("brazos", "descartados_brazos", "anadidos_brazos"),
    ):
        f = 100 if "realizada" in et else 1
        print(f"   {et:24} {df[a]*f:12.3f} {df[b]*f:12.3f}")

    print("\n" + "=" * 66)
    print("2. POR QUÉ  (los diagnósticos, después de la comparación)\n")

    cal = noise.calibrar(p)
    print(f"   a) calibración del ruido: {'aprobada' if cal.aprobada else 'RECHAZADA'}, "
          f"Q/gl = {cal.razon_Q_gl:.3f}")

    reg = regimen_de_la_proporcion(p)
    print(f"   b) régimen de la proporción: tasa {reg['tasa_global']:.4f}, "
          f"n·p mediana {reg['n_por_p_mediana']:.1f}")
    print(f"      brazos con n·p < 10: {reg['fraccion_con_np_menor_10']:.1%} | "
          f"< 5: {reg['fraccion_con_np_menor_5']:.1%}")

    dep = precision_predice_parametro(p)
    print(f"   c) ¿la precisión predice el parámetro?")
    print(f"      cruda          {dep['correlacion_cruda']:+.3f} (p={dep['p_cruda']:.1e})")
    print(f"      dentro de semana {dep['correlacion_dentro_de_semana']:+.3f} "
          f"({dep['grupos_semana']} semanas)")
    print(f"      dentro de tipo   {dep['correlacion_dentro_de_tipo']:+.3f} "
          f"({dep['grupos_tipo']} tipos)")
    print(f"      sobrevive al control: {'SÍ' if dep['sobrevive_al_control'] else 'no'}")

    cifras = {
        "muestra": args.muestra,
        "particiones": args.particiones,
        "donde_falla": df,
        "calibracion_ruido": cal.to_dict(),
        "regimen_proporcion": reg,
        "precision_predice_parametro": dep,
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
