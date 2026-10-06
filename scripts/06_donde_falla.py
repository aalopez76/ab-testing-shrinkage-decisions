"""Fase F: dónde falla la contracción, y por qué.

Dos partes, y el orden importa (ver `.claude/rules/method.md`):

1. **Dónde falla.** En qué experiments la contracción elige peor que no
   correct, y qué caracteriza a esos casos. No es opcional: shrink improvement el
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

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "06_donde_falla.json"


def where_it_fails(p: pd.DataFrame, partitions: int) -> dict:
    """Perfil de los experiments donde shrink elige peor."""
    profiles, fractions = [], []
    for s in range(partitions):
        el, es, ev = thinning.split_three_way(p, seed=s)
        m = shrinkage.usable_mask(es)
        el = el.loc[m].reset_index(drop=True)
        ev = ev.loc[m].reset_index(drop=True)
        c = portfolio.build_three_way(el, shrinkage.prepare(es, m), ev)
        t = c.table.copy()
        mean, tau2 = portfolio.shrink_portfolio(c)
        t["shrunk"] = mean
        t["alpha"] = t["v"] / (t["v"] + tau2)

        # con budget del 10%, qué elige cada rule
        k = max(1, int(round(0.10 * len(t))))
        sel_cru = set(np.argsort(-t["delta_estimated"].to_numpy(), kind="stable")[:k])
        sel_con = set(np.argsort(-t["shrunk"].to_numpy(), kind="stable")[:k])
        solo_cru = sorted(sel_cru - sel_con)      # los que shrink DESCARTA
        solo_con = sorted(sel_con - sel_cru)      # los que shrink AÑADE

        if not solo_cru or not solo_con:
            continue
        fractions.append(len(solo_cru) / k)
        profiles.append(
            {
                "descartados_delta_realizado": float(t["delta_realized"].iloc[solo_cru].mean()),
                "anadidos_delta_realizado": float(t["delta_realized"].iloc[solo_con].mean()),
                "discarded_alpha": float(t["alpha"].iloc[solo_cru].mean()),
                "added_alpha": float(t["alpha"].iloc[solo_con].mean()),
                "descartados_impresiones": float(t["impressions"].iloc[solo_cru].mean()),
                "anadidos_impresiones": float(t["impressions"].iloc[solo_con].mean()),
                "descartados_brazos": float(t["arms"].iloc[solo_cru].mean()),
                "anadidos_brazos": float(t["arms"].iloc[solo_con].mean()),
            }
        )
    d = pd.DataFrame(profiles)
    return {
        "budget": 0.10,
        "fraccion_de_la_seleccion_que_cambia": float(np.mean(fractions)),
        **{k: float(d[k].mean()) for k in d.columns},
    }


def precision_predicts_parameter(p: pd.DataFrame) -> dict:
    """¿La precisión predice el parámetro? Controlando por periodo y kind.

    La auditoría previa midió una correlación raw de -0.15 entre impressions
    y rate, y quedó pendiente comprobar que no fuera confusión: si los
    experiments tardíos son más grandes y además tienen tasas más bajas, el
    gradiente aparece sin dependencia estructural.

    Aquí se calcula la correlación **dentro** de cada week y dentro de cada
    kind de experimento, y se promedia. Si sobrevive al control, la dependencia
    que advierte Chen (*Econometrica*, 2026) es real en estos data.
    """
    g = p.groupby("experiment_id").agg(
        n=("impressions", "sum"), c=("clicks", "sum"),
        week=("week", "first"),
        titular=("varies_headline", "first"), imagen=("varies_image", "first"),
    )
    g["rate"] = g["c"] / g["n"]
    g["kind"] = np.select(
        [g.titular & ~g.imagen, ~g.titular & g.imagen, g.titular & g.imagen],
        ["solo_titular", "solo_imagen", "ambos"], default="ninguno",
    )

    raw = stats.spearmanr(g["n"], g["rate"])

    def within(col: str) -> tuple[float, int]:
        rs, pesos = [], []
        for _, blk in g.groupby(col):
            if len(blk) < 30:
                continue
            r = stats.spearmanr(blk["n"], blk["rate"]).statistic
            if np.isfinite(r):
                rs.append(r); pesos.append(len(blk))
        if not rs:
            return float("nan"), 0
        return float(np.average(rs, weights=pesos)), len(rs)

    r_sem, n_sem = within("week")
    r_tipo, n_tipo = within("kind")

    return {
        "correlation_raw": float(raw.statistic),
        "p_raw": float(raw.pvalue),
        "correlacion_dentro_de_semana": r_sem,
        "grupos_semana": n_sem,
        "correlation_within_type": r_tipo,
        "groups_type": n_tipo,
        "survives_control": bool(
            np.isfinite(r_sem) and r_sem < -0.05 and np.isfinite(r_tipo) and r_tipo < -0.05
        ),
    }


def proportion_regime(p: pd.DataFrame) -> dict:
    """¿Estamos donde la aproximación gaussiana de la binomial flaquea?

    Chen y Lei (dic-2025) trabajan la binomial directamente justamente para
    proporciones y muestras pequeñas. La rule de dedo habitual pide n·p ≥ 10
    para que la normal aproxime bien.
    """
    n = p["impressions"].to_numpy(dtype=float)
    rate = float(p["clicks"].sum() / p["impressions"].sum())
    np_ = n * rate
    return {
        "global_rate": rate,
        "median_n": float(np.median(n)),
        "median_n_times_p": float(np.median(np_)),
        "fraccion_con_np_menor_10": float(np.mean(np_ < 10)),
        "fraccion_con_np_menor_5": float(np.mean(np_ < 5)),
    }


def main() -> None:
    consola.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--partitions", type=int, default=30)
    args = ap.parse_args()

    p = panel.load(args.sample)

    print("=" * 66)
    print("1. DÓNDE FALLA  (budget 10%)")
    df = where_it_fails(p, args.partitions)
    print(f"   la contracción cambia el {df['fraccion_de_la_seleccion_que_cambia']:.1%} "
          f"de la selección\n")
    print(f"   {'':24} {'descarta':>12} {'añade':>12}")
    for et, a, b in (
        ("gain realizada", "descartados_delta_realizado", "anadidos_delta_realizado"),
        ("alpha", "discarded_alpha", "added_alpha"),
        ("impressions", "descartados_impresiones", "anadidos_impresiones"),
        ("arms", "descartados_brazos", "anadidos_brazos"),
    ):
        f = 100 if "realizada" in et else 1
        print(f"   {et:24} {df[a]*f:12.3f} {df[b]*f:12.3f}")

    print("\n" + "=" * 66)
    print("2. POR QUÉ  (los diagnósticos, después de la comparación)\n")

    cal = noise.calibrate(p)
    print(f"   a) calibración del ruido: {'passed' if cal.passed else 'RECHAZADA'}, "
          f"Q/dof = {cal.q_over_dof:.3f}")

    reg = proportion_regime(p)
    print(f"   b) régimen de la proporción: rate {reg['global_rate']:.4f}, "
          f"n·p mediana {reg['median_n_times_p']:.1f}")
    print(f"      arms con n·p < 10: {reg['fraccion_con_np_menor_10']:.1%} | "
          f"< 5: {reg['fraccion_con_np_menor_5']:.1%}")

    dep = precision_predicts_parameter(p)
    print(f"   c) ¿la precisión predice el parámetro?")
    print(f"      raw          {dep['correlation_raw']:+.3f} (p={dep['p_raw']:.1e})")
    print(f"      dentro de week {dep['correlacion_dentro_de_semana']:+.3f} "
          f"({dep['grupos_semana']} semanas)")
    print(f"      dentro de kind   {dep['correlation_within_type']:+.3f} "
          f"({dep['groups_type']} tipos)")
    print(f"      sobrevive al control: {'SÍ' if dep['survives_control'] else 'no'}")

    metrics = {
        "sample": args.sample,
        "partitions": args.partitions,
        "where_it_fails": df,
        "noise_calibration": cal.to_dict(),
        "proportion_regime": reg,
        "precision_predicts_parameter": dep,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
