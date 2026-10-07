"""Las figuras del informe, generadas desde las metrics medidas.

Cada figura se construye leyendo `reports/results/*.json` —las mismas metrics que
cita el README— o recalculando desde el panel. **Ningún número está escrito a
mano en este archivo**: si una cifra cambia al re-correr el análisis, la figura
cambia con ella.

Salida: reports/figures/*.png
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wcab import console, decision, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "reports" / "results"
FIG = ROOT / "reports" / "figures"

# paleta: la práctica actual en gris cálido, las correcciones en azules,
# el oráculo en gris claro, y verde/rojo solo para veredictos
CRUDA, GLOBAL, BHS = "#8c7b6b", "#3b6ea5", "#1f4068"
AZAR, ORACULO = "#c9c9c9", "#e8e4dc"
AYUDA, PERJUDICA, NO_PUEDE = "#2f7d4f", "#b4422f", "#9a9a9a"

plt.rcParams.update({
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def leer(nombre: str) -> dict:
    return json.loads((RES / nombre).read_text(encoding="utf-8"))


def save(fig, nombre: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / nombre)
    plt.close(fig)
    print(f"  {nombre}")


# --------------------------------------------------------------------------
def fig_maldicion(p, partitions: int = 8) -> None:
    """Lo que promete la ganadora contra lo que entrega, y el control al random_rule."""
    prom_el, ent_el, prom_az, ent_az = [], [], [], []
    for s in range(partitions):
        dos = thinning.split(p, fraction=0.5, seed=s)
        m = shrinkage.usable_mask(dos.estimation)
        est = shrinkage.prepare(dos.estimation, m)
        ev = dos.evaluation.loc[m].reset_index(drop=True)
        for rule, pr, en in (("raw", prom_el, ent_el), ("random", prom_az, ent_az)):
            r = decision.evaluate(est, ev, rule=rule, seed=s)
            t = r.per_experiment
            pr.append(t["promised"].mean())
            en.append(t["delivered"].mean())

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), sharey=True)
    tope = max(np.mean(prom_el), np.mean(prom_az)) * 100
    for ax, (prom, ent, titulo) in zip(axes, [
        (prom_el, ent_el, "Chosen for measuring best"),
        (prom_az, ent_az, "Chosen at random (control)"),
    ]):
        a, b = np.mean(prom) * 100, np.mean(ent) * 100
        ax.bar([0, 1], [a, b], color=[CRUDA, GLOBAL], width=0.5)
        ax.set_xticks([0, 1], ["promises", "delivers"])
        ax.set_title(titulo, pad=26)
        for x, v in ((0, a), (1, b)):
            ax.text(x, v + tope * 0.015, f"{v:.3f}%", ha="center", fontsize=9)
        dif = a - b
        hay = dif > 0.01
        ax.plot([0, 1], [tope * 1.16] * 2, ls=":", lw=0.9, color="#777")
        ax.text(0.5, tope * 1.20,
                f"{dif:+.3f} pp" + (f"  ({dif/b*100:+.1f}% relative)" if hay
                                    else "  (no gap)"),
                ha="center", fontsize=9.5, weight="bold",
                color=PERJUDICA if hay else AYUDA)
        ax.set_ylim(0, tope * 1.34)
    axes[0].set_ylabel("click-through rate of the deployed variant")
    fig.suptitle("The winner's curse is a selection effect, not a measurement effect",
                 fontsize=11, weight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "01_winners_curse.png")


# --------------------------------------------------------------------------
def fig_datos(p) -> None:
    """Las dos comprobaciones iniciales: aleatorización y modelo de ruido."""
    srm = leer("02_srm.json")["confirmatory"]
    by_month = sorted(srm["by_month"], key=lambda r: r["month"])
    meses = [r["month"] for r in by_month]
    tasas = [r["imbalance_fraction"] for r in by_month]

    cal = noise.calibrate(p)
    table = noise.cochran_q(p[p["is_aa"]])
    qs = (table["Q"] / table["dof"]).to_numpy()
    qs = qs[np.isfinite(qs)]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.6))

    x = np.arange(len(meses))
    col = [PERJUDICA if t > 0.05 else GLOBAL for t in tasas]
    a1.bar(x, np.array(tasas) * 100, color=col, width=0.8)
    a1.axhline(5, ls="--", lw=1, color="#333")
    a1.text(len(meses) * 0.98, 7, "5% expected by chance", ha="right", fontsize=8.5)
    paso = max(1, len(meses) // 9)
    a1.set_xticks(x[::paso], [meses[i] for i in range(0, len(meses), paso)],
                  rotation=45, ha="right", fontsize=8)
    a1.set_ylabel("% of experiments with anomalous allocation")
    a1.set_title("1. Randomisation failed for months")

    a2.hist(np.clip(qs, 0, 6), bins=45, color=GLOBAL, alpha=0.85)
    a2.axvline(1.0, ls="--", lw=1.4, color="#333")
    a2.text(1.08, a2.get_ylim()[1] * 0.92, "1.0 = noise model\nis correct",
            fontsize=8.5)
    a2.axvline(cal.q_over_dof, lw=1.6, color=PERJUDICA)
    a2.text(cal.q_over_dof + 0.12, a2.get_ylim()[1] * 0.62,
            f"measured: {cal.q_over_dof:.2f}×", fontsize=9, color=PERJUDICA, weight="bold")
    a2.set_xlabel("Cochran's Q / degrees of freedom, per A/A experiment")
    a2.set_ylabel(f"experiments  (n={len(qs):,})")
    a2.set_title("2. The noise model underestimates twofold")

    fig.suptitle("Two data problems, resolved before any measurement",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "02_initial_checks.png")


# --------------------------------------------------------------------------
def fig_cuatro_decisiones(p, partitions: int = 8) -> None:
    """La figura central: cuatro decisiones, cuatro respuestas, cada una en sus
    propias unidades. No se normalizan a un eje común a propósito — serían
    cantidades distintas disfrazadas de comparables."""
    r = leer("07_result.json")["confirmatory"]
    u = leer("09_ship_decision.json")["thresholds"]
    g = r["gain"]

    # decisión 1: la rate que de hecho entrega la variante desplegada, con y sin
    # correct. Comparar "99.8% de decisiones idénticas" contra 100% sería
    # circular; esto está en las mismas unidades que el resto.
    ent_cru, ent_con = [], []
    for s in range(partitions):
        dos = thinning.split(p, fraction=0.5, seed=s)
        m = shrinkage.usable_mask(dos.estimation)
        est = shrinkage.prepare(dos.estimation, m)
        ev = dos.evaluation.loc[m].reset_index(drop=True)
        con = shrinkage.shrink(est, tau2=None, tau2_method="paule-mandel")
        ent_cru.append(decision.evaluate(est, ev, rule="raw", seed=s)
                       .per_experiment["delivered"].mean())
        ent_con.append(decision.evaluate(est, ev, priority=con.theta_tilde,
                                        rule="shrunk_global", seed=s)
                       .per_experiment["delivered"].mean())

    filas = [
        ("1. Which variant to deploy?", "click-through rate actually delivered",
         np.mean(ent_con) * 100, np.mean(ent_cru) * 100,
         "cannot change it: ordering is preserved", NO_PUEDE, "%", 3),
        ("2. Which experiments to prioritise?", "realised gain at a 5% budget",
         g["shrunk"]["0.05"] * 100, g["raw"]["0.05"] * 100,
         f"worse by {abs(g['shrunk']['0.05']-g['raw']['0.05'])*100:.3f} pp — "
         "interval excludes zero", PERJUDICA, " pp", 2),
        ("3. Ship or not?", "realised policy value, threshold > 0.8 pp",
         u["0.008"]["value_shrunk"]["point_estimate"] * 100,
         u["0.008"]["value_raw"]["point_estimate"] * 100,
         f"the uncorrected rule destroys value: "
         f"{u['0.008']['value_raw']['point_estimate']*100:+.4f} pp",
         AYUDA, " pp", 4),
        ("4. Which figure to report?", "mean squared error (lower is better)",
         r["estimation"]["mse_shrunk"] * 1e5, r["estimation"]["mse_raw"] * 1e5,
         f"{abs(r['estimation']['relative_change'])*100:.1f}% less error", AYUDA, " ×10⁻⁵", 2),
    ]

    fig, axes = plt.subplots(4, 1, figsize=(9.4, 7.4))
    for ax, (tit, medida, con, cru, veredicto, color, uni, dec) in zip(axes, filas):
        ax.barh([1, 0], [cru, con], color=[CRUDA, color], height=0.58)
        ax.set_yticks([1, 0], ["uncorrected", "shrunk"], fontsize=9)
        ax.set_xlim(0, max(cru, con) * 1.5)
        for y, v in ((1, cru), (0, con)):
            ax.text(v * 1.02, y, f"{v:.{dec}f}{uni}", va="center", fontsize=9.5)
        ax.set_title(f"{tit}      ", loc="left", pad=16)
        ax.text(1.0, 1.12, veredicto, transform=ax.transAxes, ha="right",
                fontsize=9.5, color=color, weight="bold")
        ax.text(0.0, 1.12, medida, transform=ax.transAxes, fontsize=8.5,
                color="#666", style="italic")
        ax.set_xticks([])
        ax.grid(visible=False)
    fig.suptitle("The same correction, four decisions, four answers",
                 fontsize=12.5, weight="bold", y=1.0)
    fig.tight_layout(h_pad=2.2)
    save(fig, "03_four_decisions.png")


# --------------------------------------------------------------------------
def fig_umbral() -> None:
    """Donde la contraccion si gana: lanzar contra un umbral absoluto.

    Se grafica el VALOR de la politica, no la exactitud. La exactitud contra
    `realized > u` compara con una segunda medicion ruidosa, no con la verdad;
    el valor realizado es lo que la regla entrega.
    """
    d = leer("09_ship_decision.json")["thresholds"]
    us = sorted(d, key=float)
    x = [float(k) * 100 for k in us]                      # a puntos porcentuales

    v_cru = [d[k]["value_raw"]["point_estimate"] * 100 for k in us]
    v_con = [d[k]["value_shrunk"]["point_estimate"] * 100 for k in us]
    ic_cru = [d[k]["value_raw"]["percentile_interval"] for k in us]
    ic_con = [d[k]["value_shrunk"]["percentile_interval"] for k in us]

    def barras(valores, intervalos):
        bajo = [v - ic[0] * 100 for v, ic in zip(valores, intervalos)]
        alto = [ic[1] * 100 - v for v, ic in zip(valores, intervalos)]
        return [bajo, alto]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    a1.axhline(0, color="#333", lw=1.1, zorder=1)
    a1.errorbar(x, v_cru, yerr=barras(v_cru, ic_cru), fmt="o-", color=CRUDA,
                lw=2, ms=6, capsize=3, label="uncorrected", zorder=3)
    a1.errorbar(x, v_con, yerr=barras(v_con, ic_con), fmt="o-", color=GLOBAL,
                lw=2, ms=6, capsize=3, label="shrunk", zorder=3)

    # El cruce por cero es el hallazgo: senalar el umbral donde ocurre.
    for xi, v in zip(x, v_cru):
        if v < 0:
            a1.annotate("destroys\nvalue", (xi, v),
                        textcoords="offset points",
                        xytext=(0, -26), ha="center", fontsize=8.5,
                        color=PERJUDICA, weight="bold")
            break

    a1.set_xlabel("ship threshold (percentage points of improvement)")
    a1.set_ylabel("realised policy value (pp)")
    a1.set_title("Above a demanding bar the uncorrected rule turns negative")
    a1.legend(frameon=False, loc="upper right")
    a1.set_xlim(min(x) - 0.06, max(x) + 0.06)

    ancho = 0.26
    xi = np.arange(len(us))
    a2.bar(xi - ancho, [d[k]["ship_rate_raw"] * 100 for k in us], ancho,
           color=CRUDA, label="ships, uncorrected")
    a2.bar(xi, [d[k]["ship_rate_shrunk"] * 100 for k in us], ancho,
           color=GLOBAL, label="ships, shrunk")
    a2.bar(xi + ancho, [d[k]["should_ship"] * 100 for k in us], ancho,
           color=ORACULO, edgecolor="#999", label="should ship")
    a2.set_xticks(xi, [f"> {float(k)*100:.1f}" for k in us])
    a2.set_xlabel("ship threshold (pp)")
    a2.set_ylabel("% of experiments shipped")
    a2.set_title("The uncorrected rule gets the rate right and the individuals wrong")
    a2.legend(frameon=False, fontsize=8.5)

    fig.suptitle("Ranking is invariant to shrinkage; threshold comparison is not",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "04_ship_decision.png")


# --------------------------------------------------------------------------
def fig_que_descarta() -> None:
    """El mecanismo del daño en la decisión 2."""
    d = leer("06_where_it_fails.json")
    d = d.get("confirmatory", d["exploratory"])
    f, pp = d["where_it_fails"], d["precision_predicts_parameter"]

    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.5))
    campos = [
        ("realised gain", "discarded_delta_realized",
         "added_delta_realized", 100, " pp"),
        ("shrinkage weight", "discarded_alpha", "added_alpha", 1, ""),
        ("impressions", "discarded_impressions", "added_impressions", 1, ""),
    ]
    for ax, (tit, ka, kb, esc, uni) in zip(axes, campos):
        va, vb = f[ka] * esc, f[kb] * esc
        ax.bar([0, 1], [va, vb], color=[PERJUDICA, GLOBAL], width=0.55)
        ax.set_xticks([0, 1], ["discards", "adds"])
        ax.set_title(tit)
        for xx, vv in ((0, va), (1, vb)):
            et = f"{vv:,.0f}" if vv > 100 else f"{vv:.3f}{uni}"
            ax.text(xx, vv * 1.02, et, ha="center", fontsize=9)
        ax.set_ylim(0, max(va, vb) * 1.22)

    ax = axes[3]
    etq = ["unadj.", "within\nweek", "within\ntype"]
    val = [pp["correlation_raw"], pp["correlation_within_week"],
           pp["correlation_within_type"]]
    ax.bar(range(3), val, color=PERJUDICA, width=0.55)
    ax.axhline(0, lw=1, color="#333")
    ax.set_xticks(range(3), etq, fontsize=8.5)
    ax.set_title("precision vs outcome")
    for i, v in enumerate(val):
        ax.text(i, v - 0.012, f"{v:+.3f}", ha="center", va="top", fontsize=9)
    ax.set_ylim(min(val) * 1.5, 0.02)

    fig.suptitle("Shrinkage discards the imprecise — and here the imprecise are "
                 "better, because prior independence fails",
                 fontsize=11, weight="bold", y=1.04)
    fig.tight_layout()
    save(fig, "05_where_it_fails.png")


# --------------------------------------------------------------------------
def fig_bhs() -> None:
    """La variante de 2025: estima mejor, no cambia el orden."""
    b = leer("10_bhs.json")["confirmatory"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    rules = ["raw", "global", "bhs"]
    etq = ["uncorrected", "standard", "BHS (2025)"]
    val = [b["mse"][k] * 1e5 for k in rules]
    a1.bar(range(3), val, color=[CRUDA, GLOBAL, BHS], width=0.58)
    a1.set_xticks(range(3), etq)
    a1.set_ylabel("mean squared error  (×10⁻⁵)")
    a1.set_title("Estimating: BHS improves on the standard version")
    for i, k in enumerate(rules):
        c = b["mse_relative_change"][k]
        a1.text(i, val[i] * 1.015, f"{val[i]:.3f}" +
                ("" if k == "raw" else f"\n{c*100:+.1f}%"),
                ha="center", fontsize=9,
                color="#333" if k == "raw" else AYUDA,
                weight="normal" if k == "raw" else "bold")
    a1.set_ylim(0, max(val) * 1.3)

    pres = sorted(b["gain"]["raw"], key=float)
    x = np.arange(len(pres))
    for k, et, c in (("raw", "uncorrected", CRUDA), ("global", "standard", GLOBAL),
                     ("bhs", "BHS (2025)", BHS)):
        a2.plot(x, [b["gain"][k][q] * 100 for q in pres], "o-",
                color=c, lw=2, ms=6, label=et)
    a2.set_xticks(x, [f"{int(float(q)*100)}%" for q in pres])
    a2.set_xlabel("budget")
    a2.set_ylabel("realised gain (pp)")
    a2.set_title("Deciding: BHS does not change the ordering")
    a2.legend(frameon=False)
    a2.text(0.98, 0.82, f"a = {b['a_mean']:.2f}\nlikelihood ratio "
            f"= {b['likelihood_ratio']:.0f}\nthe data DO require\nlocal flexibility",
            transform=a2.transAxes, ha="right", fontsize=8.5, color="#444",
            bbox=dict(boxstyle="round,pad=0.45", fc="#f4f2ee", ec="#ccc"))

    fig.suptitle("BHS corrects the shape of the prior, not prior independence",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "06_bhs.png")


# --------------------------------------------------------------------------
def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    args = ap.parse_args()

    p = panel.load(args.sample)
    print(f"figuras -> reports/figures/  ({args.sample})")
    fig_maldicion(p)
    fig_datos(p)
    fig_cuatro_decisiones(p)
    fig_umbral()
    fig_que_descarta()
    fig_bhs()


if __name__ == "__main__":
    main()
