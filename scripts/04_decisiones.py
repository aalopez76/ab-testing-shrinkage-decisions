"""Pasos 4 y 5: la inflación del ganador y si corregirla mejora la decisión.

Esta es la primera cifra de punta a punta del proyecto, y la que puede
terminarlo temprano: si ninguna corrección mejora la decisión, ése es el
resultado y no hace falta construir las configuraciones restantes.

Las reglas se comparan eligiendo con la mitad de estimación y midiendo en la de
evaluación, que no participó en elegir. Cada partición se repite con varias
semillas, y esa variación se reporta **por separado** de la incertidumbre
muestral: son dos fuentes distintas y promediarlas juntas confundiría.

Salida: reports/results/04_decisiones.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import consola, decision, panel, shrinkage, thinning
from wcab.diagnostics import noise
from wcab.shrinkage import dispersion

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "04_decisiones.json"


def una_particion(p: pd.DataFrame, semilla: int, factor_v: float, metodo_tau2: str):
    """Corre todas las reglas sobre una partición y devuelve sus resultados."""
    part = thinning.partir(p, fraccion=0.5, semilla=semilla)

    # Una sola máscara para las DOS mitades: si cada una se filtrara por su
    # cuenta se compararían brazos distintos y nada lo delataría.
    m = shrinkage.mascara_utilizable(part.estimacion)
    est = shrinkage.preparar(part.estimacion, m)
    ev = part.evaluacion.loc[m].reset_index(drop=True)

    # tau2 se estima SOLO con la mitad de estimación: la de evaluación no
    # participa en ninguna decisión, ni siquiera a través de la dispersión.
    tau2 = dispersion.estimar(est, metodo=metodo_tau2, factor_v=factor_v)
    contr = shrinkage.contraer(est, tau2, factor_v=factor_v, metodo_tau2=metodo_tau2)

    reglas = [
        decision.evaluar(est, ev, regla="azar", semilla=semilla),
        decision.evaluar(est, ev, regla="crudo"),
        decision.evaluar(est, ev, prioridad=contr.theta_tilde, regla="contraido_global"),
    ]
    return reglas, contr


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=20)
    ap.add_argument("--metodo-tau2", default="paule-mandel",
                    choices=list(dispersion.METODOS))
    ap.add_argument("--factor-v", type=float, default=None,
                    help="factor de diseño; por omisión, el del paso 1")
    args = ap.parse_args()

    p = panel.cargar(args.muestra)

    if args.factor_v is None:
        cal = noise.calibrar(p)
        factores = {"ingenuo": 1.0, "corregido": cal.factor_diseno}
        print(f"factor de diseño del paso 1: {cal.factor_diseno:.3f}\n")
    else:
        factores = {"indicado": args.factor_v}

    salida = {"muestra": args.muestra, "particiones": args.particiones,
              "metodo_tau2": args.metodo_tau2, "resultados": {}}

    for etiqueta, factor in factores.items():
        acum: dict[str, list[dict]] = {}
        contracciones = []
        fallos = []
        for s in range(args.particiones):
            reglas, contr = una_particion(p, s, factor, args.metodo_tau2)
            contracciones.append(contr.resumen())
            for r in reglas:
                acum.setdefault(r.regla, []).append(r.resumen())
            porreg = {r.regla: r for r in reglas}
            fallos.append(
                decision.donde_falla(porreg["contraido_global"], porreg["crudo"],
                                     "contraído", "crudo")
            )

        print(f"=== v {etiqueta} (factor {factor:.3f}) ===")
        print(f"{'regla':20} {'valor':>10} {'arrepent.':>11} {'inflación':>11}")
        tabla = {}
        for regla, lst in acum.items():
            d = pd.DataFrame(lst)
            tabla[regla] = {
                k: {"media": float(d[k].mean()), "de_entre_particiones": float(d[k].std(ddof=1))}
                for k in ("valor", "arrepentimiento", "inflacion")
            }
            tabla[regla]["experimentos"] = int(d["experimentos"].iloc[0])
            print(f"{regla:20} {d['valor'].mean():10.5f} "
                  f"{d['arrepentimiento'].mean():11.5f} {d['inflacion'].mean():11.5f}")

        f = pd.DataFrame(fallos)
        print(f"\ncontraído peor que crudo en {f['fraccion_peor'].mean():.1%} de los "
              f"experimentos; mejor en {f['fraccion_mejor'].mean():.1%}; "
              f"igual en {f['fraccion_igual'].mean():.1%}")
        c = pd.DataFrame(contracciones)
        print(f"tau2 medio = {c['tau2'].mean():.3e}  "
              f"(raíz {np.sqrt(c['tau2'].mean()):.5f})   "
              f"alpha medio = {c['alpha_media'].mean():.3f}\n")

        salida["resultados"][etiqueta] = {
            "factor_v": factor,
            "reglas": tabla,
            "contraccion": {k: float(c[k].mean()) for k in
                            ("tau2", "raiz_tau2", "alpha_media", "alpha_mediana")},
            "donde_falla": {k: float(f[k].mean()) for k in
                            ("fraccion_peor", "fraccion_mejor", "fraccion_igual")},
        }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = salida
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"cifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
