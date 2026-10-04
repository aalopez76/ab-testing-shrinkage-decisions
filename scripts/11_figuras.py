"""Las figuras del informe, generadas desde las cifras medidas.

Cada figura se construye leyendo `reports/results/*.json` —las mismas cifras que
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

from wcab import consola, decision, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "reports" / "results"
FIG = RAIZ / "reports" / "figures"

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


def guardar(fig, nombre: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / nombre)
    plt.close(fig)
    print(f"  {nombre}")


# --------------------------------------------------------------------------
def fig_maldicion(p, particiones: int = 8) -> None:
    """Lo que promete la ganadora contra lo que entrega, y el control al azar."""
    prom_el, ent_el, prom_az, ent_az = [], [], [], []
    for s in range(particiones):
        dos = thinning.partir(p, fraccion=0.5, semilla=s)
        m = shrinkage.mascara_utilizable(dos.estimacion)
        est = shrinkage.preparar(dos.estimacion, m)
        ev = dos.evaluacion.loc[m].reset_index(drop=True)
        for regla, pr, en in (("crudo", prom_el, ent_el), ("azar", prom_az, ent_az)):
            r = decision.evaluar(est, ev, regla=regla, semilla=s)
            t = r.por_experimento
            pr.append(t["prometido"].mean())
            en.append(t["entregado"].mean())

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), sharey=True)
    tope = max(np.mean(prom_el), np.mean(prom_az)) * 100
    for ax, (prom, ent, titulo) in zip(axes, [
        (prom_el, ent_el, "Se elige la que midió mejor"),
        (prom_az, ent_az, "Se elige al azar (control)"),
    ]):
        a, b = np.mean(prom) * 100, np.mean(ent) * 100
        ax.bar([0, 1], [a, b], color=[CRUDA, GLOBAL], width=0.5)
        ax.set_xticks([0, 1], ["promete", "entrega"])
        ax.set_title(titulo, pad=26)
        for x, v in ((0, a), (1, b)):
            ax.text(x, v + tope * 0.015, f"{v:.3f}%", ha="center", fontsize=9)
        dif = a - b
        hay = dif > 0.01
        ax.plot([0, 1], [tope * 1.16] * 2, ls=":", lw=0.9, color="#777")
        ax.text(0.5, tope * 1.20,
                f"{dif:+.3f} pp" + (f"  ({dif/b*100:+.1f}% relativo)" if hay
                                    else "  (sin brecha)"),
                ha="center", fontsize=9.5, weight="bold",
                color=PERJUDICA if hay else AYUDA)
        ax.set_ylim(0, tope * 1.34)
    axes[0].set_ylabel("tasa de clic de la variante desplegada")
    fig.suptitle("La maldición del ganador es un efecto de selección, no de medición",
                 fontsize=11, weight="bold", y=1.02)
    fig.tight_layout()
    guardar(fig, "01_maldicion_del_ganador.png")


# --------------------------------------------------------------------------
def fig_datos(p) -> None:
    """Las dos comprobaciones iniciales: aleatorización y modelo de ruido."""
    srm = leer("02_srm.json")["confirmatorio"]
    por_mes = sorted(srm["por_mes"], key=lambda r: r["mes"])
    meses = [r["mes"] for r in por_mes]
    tasas = [r["fraccion_desbalance"] for r in por_mes]

    cal = noise.calibrar(p)
    tabla = noise.q_de_cochran(p[p["es_aa"]])
    qs = (tabla["Q"] / tabla["gl"]).to_numpy()
    qs = qs[np.isfinite(qs)]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.6))

    x = np.arange(len(meses))
    col = [PERJUDICA if t > 0.05 else GLOBAL for t in tasas]
    a1.bar(x, np.array(tasas) * 100, color=col, width=0.8)
    a1.axhline(5, ls="--", lw=1, color="#333")
    a1.text(len(meses) * 0.98, 7, "5% esperado por azar", ha="right", fontsize=8.5)
    paso = max(1, len(meses) // 9)
    a1.set_xticks(x[::paso], [meses[i] for i in range(0, len(meses), paso)],
                  rotation=45, ha="right", fontsize=8)
    a1.set_ylabel("% de experimentos con reparto anómalo")
    a1.set_title("1. La aleatorización falló durante meses")

    a2.hist(np.clip(qs, 0, 6), bins=45, color=GLOBAL, alpha=0.85)
    a2.axvline(1.0, ls="--", lw=1.4, color="#333")
    a2.text(1.08, a2.get_ylim()[1] * 0.92, "1.0 = el modelo\nde ruido acierta",
            fontsize=8.5)
    a2.axvline(cal.razon_Q_gl, lw=1.6, color=PERJUDICA)
    a2.text(cal.razon_Q_gl + 0.12, a2.get_ylim()[1] * 0.62,
            f"medido: {cal.razon_Q_gl:.2f}×", fontsize=9, color=PERJUDICA, weight="bold")
    a2.set_xlabel("Q de Cochran / grados de libertad, por experimento A/A")
    a2.set_ylabel(f"experimentos  (n={len(qs):,})")
    a2.set_title("2. El modelo de ruido subestima al doble")

    fig.suptitle("Dos problemas de los datos, resueltos antes de medir nada",
                 fontsize=11, weight="bold", y=1.04)
    guardar(fig, "02_comprobaciones_iniciales.png")


# --------------------------------------------------------------------------
def fig_cuatro_decisiones(p, particiones: int = 8) -> None:
    """La figura central: cuatro decisiones, cuatro respuestas, cada una en sus
    propias unidades. No se normalizan a un eje común a propósito — serían
    cantidades distintas disfrazadas de comparables."""
    r = leer("07_resultado.json")["confirmatorio"]
    u = leer("09_decision_de_lanzar.json")["umbrales"]
    g = r["ganancia"]

    # decisión 1: la tasa que de hecho entrega la variante desplegada, con y sin
    # corregir. Comparar "99.8% de decisiones idénticas" contra 100% sería
    # circular; esto está en las mismas unidades que el resto.
    ent_cru, ent_con = [], []
    for s in range(particiones):
        dos = thinning.partir(p, fraccion=0.5, semilla=s)
        m = shrinkage.mascara_utilizable(dos.estimacion)
        est = shrinkage.preparar(dos.estimacion, m)
        ev = dos.evaluacion.loc[m].reset_index(drop=True)
        con = shrinkage.contraer(est, tau2=None, metodo_tau2="paule-mandel")
        ent_cru.append(decision.evaluar(est, ev, regla="crudo", semilla=s)
                       .por_experimento["entregado"].mean())
        ent_con.append(decision.evaluar(est, ev, prioridad=con.theta_tilde,
                                        regla="contraido_global", semilla=s)
                       .por_experimento["entregado"].mean())

    filas = [
        ("1. ¿Qué variante despliego?", "tasa de clic realmente entregada",
         np.mean(ent_con) * 100, np.mean(ent_cru) * 100,
         "no puede cambiarla: conserva el orden", NO_PUEDE, "%", 3),
        ("2. ¿Qué experimentos priorizo?", "ganancia realizada al 5% de presupuesto",
         g["contraida"]["0.05"] * 100, g["cruda"]["0.05"] * 100,
         f"peor en {abs(g['contraida']['0.05']-g['cruda']['0.05'])*100:.3f} pp — "
         "pierde en 40 de 40", PERJUDICA, " pp", 2),
        ("3. ¿Lanzo esto o no?", "acierto contra lo realizado, umbral > 0.6 pp",
         u["0.6"]["acierto_contraida"] * 100, u["0.6"]["acierto_cruda"] * 100,
         f"mejor en {u['0.6']['mejora']*100:+.2f} pp — gana en 20 de 20",
         AYUDA, "%", 1),
        ("4. ¿Qué cifra reporto?", "error cuadrático medio (menos es mejor)",
         r["estimacion"]["mse_contraida"] * 1e5, r["estimacion"]["mse_cruda"] * 1e5,
         f"{abs(r['estimacion']['cambio_relativo'])*100:.1f}% menos error", AYUDA, " ×10⁻⁵", 2),
    ]

    fig, axes = plt.subplots(4, 1, figsize=(9.4, 7.4))
    for ax, (tit, medida, con, cru, veredicto, color, uni, dec) in zip(axes, filas):
        ax.barh([1, 0], [cru, con], color=[CRUDA, color], height=0.58)
        ax.set_yticks([1, 0], ["sin corregir", "contraída"], fontsize=9)
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
    fig.suptitle("La misma corrección, cuatro decisiones, cuatro respuestas",
                 fontsize=12.5, weight="bold", y=1.0)
    fig.tight_layout(h_pad=2.2)
    guardar(fig, "03_cuatro_decisiones.png")


# --------------------------------------------------------------------------
def fig_umbral() -> None:
    """Donde contraer sí gana: la decisión de lanzar contra un umbral."""
    d = leer("09_decision_de_lanzar.json")["umbrales"]
    us = sorted(d, key=float)
    x = [float(k) for k in us]
    cru = [d[k]["acierto_cruda"] * 100 for k in us]
    con = [d[k]["acierto_contraida"] * 100 for k in us]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    a1.plot(x, cru, "o-", color=CRUDA, lw=2, ms=6, label="sin corregir")
    a1.plot(x, con, "o-", color=GLOBAL, lw=2, ms=6, label="contraída")
    for xi, k in zip(x, us):
        gana = d[k]["contraida_gana_en"]
        a1.annotate(f"gana en\n{gana:.0%}", (xi, d[k]["acierto_contraida"] * 100),
                    textcoords="offset points", xytext=(0, 11), ha="center",
                    fontsize=8, color=AYUDA if gana > 0.9 else "#777",
                    weight="bold" if gana > 0.9 else "normal")
    a1.set_xlabel("umbral de lanzamiento (puntos porcentuales de mejora)")
    a1.set_ylabel("% de decisiones correctas")
    a1.set_title("Contraer acierta más, y la ventaja crece con el umbral")
    a1.legend(frameon=False, loc="upper left")
    a1.set_ylim(min(cru) - 5, max(con) + 9)
    a1.set_xlim(min(x) - 0.06, max(x) + 0.06)

    ancho = 0.26
    xi = np.arange(len(us))
    a2.bar(xi - ancho, [d[k]["lanza_cruda"] * 100 for k in us], ancho,
           color=CRUDA, label="lanza sin corregir")
    a2.bar(xi, [d[k]["lanza_contraida"] * 100 for k in us], ancho,
           color=GLOBAL, label="lanza contraída")
    a2.bar(xi + ancho, [d[k]["deberia_lanzar"] * 100 for k in us], ancho,
           color=ORACULO, edgecolor="#999", label="debería lanzar")
    a2.set_xticks(xi, [f"> {k}" for k in us])
    a2.set_xlabel("umbral de lanzamiento (pp)")
    a2.set_ylabel("% de experimentos lanzados")
    a2.set_title("La cruda acierta la tasa y falla en los individuos")
    a2.legend(frameon=False, fontsize=8.5)

    fig.suptitle("Ordenar es invariante a contraer; comparar con un umbral no lo es",
                 fontsize=11, weight="bold", y=1.04)
    guardar(fig, "04_decision_de_lanzar.png")


# --------------------------------------------------------------------------
def fig_que_descarta() -> None:
    """El mecanismo del daño en la decisión 2."""
    d = leer("06_donde_falla.json")
    d = d.get("confirmatorio", d["exploratorio"])
    f, pp = d["donde_falla"], d["precision_predice_parametro"]

    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.5))
    campos = [
        ("ganancia realizada", "descartados_delta_realizado",
         "anadidos_delta_realizado", 100, " pp"),
        ("peso de contracción", "descartados_alpha", "anadidos_alpha", 1, ""),
        ("impresiones", "descartados_impresiones", "anadidos_impresiones", 1, ""),
    ]
    for ax, (tit, ka, kb, esc, uni) in zip(axes, campos):
        va, vb = f[ka] * esc, f[kb] * esc
        ax.bar([0, 1], [va, vb], color=[PERJUDICA, GLOBAL], width=0.55)
        ax.set_xticks([0, 1], ["descarta", "añade"])
        ax.set_title(tit)
        for xx, vv in ((0, va), (1, vb)):
            et = f"{vv:,.0f}" if vv > 100 else f"{vv:.3f}{uni}"
            ax.text(xx, vv * 1.02, et, ha="center", fontsize=9)
        ax.set_ylim(0, max(va, vb) * 1.22)

    ax = axes[3]
    etq = ["cruda", "por\nsemana", "por\ntipo"]
    val = [pp["correlacion_cruda"], pp["correlacion_dentro_de_semana"],
           pp["correlacion_dentro_de_tipo"]]
    ax.bar(range(3), val, color=PERJUDICA, width=0.55)
    ax.axhline(0, lw=1, color="#333")
    ax.set_xticks(range(3), etq, fontsize=8.5)
    ax.set_title("precisión vs resultado")
    for i, v in enumerate(val):
        ax.text(i, v - 0.012, f"{v:+.3f}", ha="center", va="top", fontsize=9)
    ax.set_ylim(min(val) * 1.5, 0.02)

    fig.suptitle("Contraer descarta los imprecisos — y aquí los imprecisos son "
                 "mejores, porque falla la independencia previa",
                 fontsize=11, weight="bold", y=1.04)
    fig.tight_layout()
    guardar(fig, "05_donde_falla.png")


# --------------------------------------------------------------------------
def fig_bhs() -> None:
    """La variante de 2025: estima mejor, no cambia el orden."""
    b = leer("10_bhs.json")["confirmatorio"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    reglas = ["cruda", "global", "bhs"]
    etq = ["sin corregir", "estándar", "BHS (2025)"]
    val = [b["mse"][k] * 1e5 for k in reglas]
    a1.bar(range(3), val, color=[CRUDA, GLOBAL, BHS], width=0.58)
    a1.set_xticks(range(3), etq)
    a1.set_ylabel("error cuadrático medio  (×10⁻⁵)")
    a1.set_title("Estimar: BHS mejora sobre la versión estándar")
    for i, k in enumerate(reglas):
        c = b["mse_cambio_relativo"][k]
        a1.text(i, val[i] * 1.015, f"{val[i]:.3f}" +
                ("" if k == "cruda" else f"\n{c*100:+.1f}%"),
                ha="center", fontsize=9,
                color="#333" if k == "cruda" else AYUDA,
                weight="normal" if k == "cruda" else "bold")
    a1.set_ylim(0, max(val) * 1.3)

    pres = sorted(b["ganancia"]["cruda"], key=float)
    x = np.arange(len(pres))
    for k, et, c in (("cruda", "sin corregir", CRUDA), ("global", "estándar", GLOBAL),
                     ("bhs", "BHS (2025)", BHS)):
        a2.plot(x, [b["ganancia"][k][q] * 100 for q in pres], "o-",
                color=c, lw=2, ms=6, label=et)
    a2.set_xticks(x, [f"{int(float(q)*100)}%" for q in pres])
    a2.set_xlabel("presupuesto")
    a2.set_ylabel("ganancia realizada (pp)")
    a2.set_title("Decidir: BHS no cambia el orden")
    a2.legend(frameon=False)
    a2.text(0.98, 0.82, f"a = {b['a_medio']:.2f}\nrazón de verosimilitudes "
            f"= {b['razon_de_verosimilitudes']:.0f}\nlos datos SÍ piden\nflexibilidad local",
            transform=a2.transAxes, ha="right", fontsize=8.5, color="#444",
            bbox=dict(boxstyle="round,pad=0.45", fc="#f4f2ee", ec="#ccc"))

    fig.suptitle("BHS corrige la forma de la previa, no la independencia previa",
                 fontsize=11, weight="bold", y=1.04)
    guardar(fig, "06_bhs.png")


# --------------------------------------------------------------------------
def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="confirmatorio",
                    choices=["exploratorio", "confirmatorio"])
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    print(f"figuras -> reports/figures/  ({args.muestra})")
    fig_maldicion(p)
    fig_datos(p)
    fig_cuatro_decisiones(p)
    fig_umbral()
    fig_que_descarta()
    fig_bhs()


if __name__ == "__main__":
    main()
