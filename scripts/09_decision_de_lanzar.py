"""Fase I: ¿de qué sirve describir mejor si se escogen los mismos?

Las fases anteriores midieron dos decisiones de **orden**: qué variante
desplegar dentro de un experimento, y qué experimentos priorizar con
presupuesto. En las dos, contraer no ayuda — y dentro del experimento no puede,
por álgebra.

Pero hay una tercera decisión que ningún paso anterior midió, y que es la que
un equipo toma con más frecuencia: **¿lanzo esto o no?** Esa decisión no compara
variantes entre sí, compara una mejora estimada contra un **umbral absoluto**
—el mínimo que justifica el costo de desplegar, mantener y arriesgar.

Y ahí la invariancia se rompe:

Porque "cual variante" y "¿la lanzo?" son DOS decisiones distintas.

    ordenar      es invariante a una transformación monótona  ⇒ contraer NO
                 puede cambiar el argmax
    comparar con
    un umbral    NO es invariante  ⇒ contraer cambia el valor, así que cambia
                 si cruza la línea

Misma corrección, dos decisiones, dos respuestas. Este script mide la segunda.

Salida: reports/results/09_decision_de_lanzar.json
"""
import json
from pathlib import Path

import numpy as np

from wcab import panel, portfolio, shrinkage, thinning
from wcab.consola import preparar

preparar()
RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "09_decision_de_lanzar.json" 

p = panel.cargar("confirmatorio")
# umbrales de lanzamiento, en puntos porcentuales de mejora
UMBRALES = [0.2, 0.4, 0.6, 0.8]
res = {u: {"cru_ok": [], "con_ok": [], "cru_lanza": [], "con_lanza": [],
           "real_lanza": []} for u in UMBRALES}

for s in range(20):
    el, es, ev = thinning.partir_tres(p, semilla=s)
    m = shrinkage.mascara_utilizable(es)
    c = portfolio.construir_tres(el.loc[m].reset_index(drop=True),
                                 shrinkage.preparar(es, m),
                                 ev.loc[m].reset_index(drop=True))
    t = c.tabla
    cru = t.delta_estimado.to_numpy() * 100      # a puntos porcentuales
    con = portfolio.contraer_cartera(c)[0] * 100
    real = t.delta_realizado.to_numpy() * 100

    for u in UMBRALES:
        verdad = real > u
        for nom, est in (("cru", cru), ("con", con)):
            dec = est > u
            res[u][f"{nom}_ok"].append(np.mean(dec == verdad))
            res[u][f"{nom}_lanza"].append(np.mean(dec))
        res[u]["real_lanza"].append(np.mean(verdad))

print("LA DECISION DE LANZAR O NO  (20 particiones, confirmatorio)\n")
print("  %-9s %9s %9s %9s %9s" % ("umbral", "lanza cru", "lanza con",
                                   "deberia", "exceso cru"))
for u in UMBRALES:
    lc = np.mean(res[u]["cru_lanza"]); ln = np.mean(res[u]["con_lanza"])
    lr = np.mean(res[u]["real_lanza"])
    print("  >%.1f pp   %8.1f%% %8.1f%% %8.1f%% %+8.1f pp"
          % (u, lc*100, ln*100, lr*100, (lc-lr)*100))

print("\n  %-9s %12s %12s %10s" % ("umbral", "acierto cru", "acierto con", "mejora"))
for u in UMBRALES:
    a = np.array(res[u]["cru_ok"]); b = np.array(res[u]["con_ok"])
    gana = np.mean(b > a)
    print("  >%.1f pp   %11.2f%% %11.2f%% %+9.2f pp   (contraer gana en %.0f%%)"
          % (u, a.mean()*100, b.mean()*100, (b.mean()-a.mean())*100, gana*100))

cifras = {"umbrales": {}, "particiones": 20, "muestra": "confirmatorio"}
for u in UMBRALES:
    a = np.array(res[u]["cru_ok"]); b = np.array(res[u]["con_ok"])
    cifras["umbrales"][str(u)] = {
        "acierto_cruda": float(a.mean()),
        "acierto_contraida": float(b.mean()),
        "mejora": float(b.mean() - a.mean()),
        "contraida_gana_en": float(np.mean(b > a)),
        "lanza_cruda": float(np.mean(res[u]["cru_lanza"])),
        "lanza_contraida": float(np.mean(res[u]["con_lanza"])),
        "deberia_lanzar": float(np.mean(res[u]["real_lanza"])),
    }
SALIDA.parent.mkdir(parents=True, exist_ok=True)
SALIDA.write_text(json.dumps(cifras, indent=2, ensure_ascii=False), encoding="utf-8")
print("\ncifras -> %s" % SALIDA.relative_to(RAIZ))
