"""Fase I: ¿de qué sirve describir mejor si se escogen los mismos?

Las fases anteriores midieron dos decisiones de **orden**: qué variante
desplegar dentro de un experimento, y qué experiments priorizar con
budget. En las dos, shrink no ayuda — y dentro del experimento no puede,
por álgebra.

Pero hay una tercera decisión que ningún paso anterior midió, y que es la que
un equipo toma con más frecuencia: **¿lanzo esto o no?** Esa decisión no compara
variantes entre sí, compara una improvement estimada contra un **umbral absoluto**
—el mínimo que justifica el costo de desplegar, mantener y arriesgar.

Y ahí la invariancia se rompe:

Porque "cual variante" y "¿la lanzo?" son DOS decisiones distintas.

    ordenar      es invariante a una transformación monótona  ⇒ shrink NO
                 puede cambiar el argmax
    compare con
    un umbral    NO es invariante  ⇒ shrink cambia el value, así que cambia
                 si cruza la línea

Misma corrección, dos decisiones, dos respuestas. Este script mide la segunda.

Salida: reports/results/09_decision_de_lanzar.json
"""
import json
from pathlib import Path

import numpy as np

from wcab import panel, portfolio, shrinkage, thinning
from wcab.console import prepare

prepare()
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "09_decision_de_lanzar.json" 

p = panel.load("confirmatory")
# thresholds de lanzamiento, en puntos porcentuales de improvement
THRESHOLDS = [0.2, 0.4, 0.6, 0.8]
res = {u: {"cru_ok": [], "con_ok": [], "cru_lanza": [], "con_lanza": [],
           "real_lanza": []} for u in THRESHOLDS}

for s in range(20):
    el, es, ev = thinning.split_three_way(p, seed=s)
    m = shrinkage.usable_mask(es)
    c = portfolio.build_three_way(el.loc[m].reset_index(drop=True),
                                 shrinkage.prepare(es, m),
                                 ev.loc[m].reset_index(drop=True))
    t = c.table
    cru = t.delta_estimated.to_numpy() * 100      # a puntos porcentuales
    con = portfolio.shrink_portfolio(c)[0] * 100
    real = t.delta_realized.to_numpy() * 100

    for u in THRESHOLDS:
        verdad = real > u
        for nom, est in (("cru", cru), ("con", con)):
            dec = est > u
            res[u][f"{nom}_ok"].append(np.mean(dec == verdad))
            res[u][f"{nom}_lanza"].append(np.mean(dec))
        res[u]["real_lanza"].append(np.mean(verdad))

print("LA DECISION DE LANZAR O NO  (20 partitions, confirmatory)\n")
print("  %-9s %9s %9s %9s %9s" % ("umbral", "lanza cru", "lanza con",
                                   "deberia", "exceso cru"))
for u in THRESHOLDS:
    lc = np.mean(res[u]["cru_lanza"]); ln = np.mean(res[u]["con_lanza"])
    lr = np.mean(res[u]["real_lanza"])
    print("  >%.1f pp   %8.1f%% %8.1f%% %8.1f%% %+8.1f pp"
          % (u, lc*100, ln*100, lr*100, (lc-lr)*100))

print("\n  %-9s %12s %12s %10s" % ("umbral", "acierto cru", "acierto con", "improvement"))
for u in THRESHOLDS:
    a = np.array(res[u]["cru_ok"]); b = np.array(res[u]["con_ok"])
    gana = np.mean(b > a)
    print("  >%.1f pp   %11.2f%% %11.2f%% %+9.2f pp   (shrink gana en %.0f%%)"
          % (u, a.mean()*100, b.mean()*100, (b.mean()-a.mean())*100, gana*100))

metrics = {"thresholds": {}, "partitions": 20, "sample": "confirmatory"}
for u in THRESHOLDS:
    a = np.array(res[u]["cru_ok"]); b = np.array(res[u]["con_ok"])
    metrics["thresholds"][str(u)] = {
        "accuracy_raw": float(a.mean()),
        "accuracy_shrunk": float(b.mean()),
        "improvement": float(b.mean() - a.mean()),
        "shrunk_wins_in": float(np.mean(b > a)),
        "ships_raw": float(np.mean(res[u]["cru_lanza"])),
        "ships_shrunk": float(np.mean(res[u]["con_lanza"])),
        "should_ship": float(np.mean(res[u]["real_lanza"])),
    }
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
print("\ncifras -> %s" % OUTPUT.relative_to(ROOT))
