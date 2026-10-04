"""Fase E: la decisión entre experimentos, donde la precisión sí es heterogénea.

Compara cuatro reglas para priorizar qué experimentos desplegar, con
presupuesto limitado. Las reglas eligen con la mitad de estimación y se miden
en la de evaluación.

    azar       la referencia que hay que batir
    cruda      ordenar por la ganancia estimada — la práctica que se pone a prueba
    contraída  la media contraída entre experimentos
    cola       probabilidad posterior de ganancia positiva

Salida: reports/results/05_cartera.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wcab import consola, panel, portfolio, shrinkage, thinning
from wcab.diagnostics import noise

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "05_cartera.json"
PRESUPUESTOS = (0.05, 0.10, 0.25, 0.50, 1.00)


def una_particion(p: pd.DataFrame, semilla: int, factor_v: float):
    # Tres tercios: elegir, estimar, evaluar. Hace falta porque el máximo de un
    # experimento es un estadístico SELECCIONADO y la contracción no se le puede
    # aplicar directamente (con dos mitades, τ² se estimaba en cero).
    el, es, ev = thinning.partir_tres(p, semilla=semilla)
    m = shrinkage.mascara_utilizable(es)
    el = el.loc[m].reset_index(drop=True)
    es = shrinkage.preparar(es, m).assign()
    ev = ev.loc[m].reset_index(drop=True)
    es = es.assign(v=es["v"] * factor_v)

    c = portfolio.construir_tres(el, es, ev)
    rng = np.random.default_rng(semilla)

    media, tau2 = portfolio.contraer_cartera(c)
    reglas = {
        "azar": rng.random(len(c)),
        "cruda": portfolio.prioridad_cruda(c),
        "contraida": media,
        "cola": portfolio.prioridad_cola(c),
    }
    valores = {k: portfolio.valor_por_presupuesto(c, v, PRESUPUESTOS)
               for k, v in reglas.items()}
    valores["oraculo"] = portfolio.oraculo(c, PRESUPUESTOS)

    # ¿reordena de verdad? fracción de pares cuyo orden cambia frente a la cruda
    orden_crudo = np.argsort(-reglas["cruda"], kind="stable")
    cambios = {
        k: float(np.mean(np.argsort(-reglas[k], kind="stable") != orden_crudo))
        for k in ("contraida", "cola")
    }
    return valores, tau2, cambios, len(c)


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--particiones", type=int, default=20)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    factor = noise.calibrar(p).factor_diseno
    print(f"factor de diseño del paso 1: {factor:.3f}\n")

    acum: dict[str, dict[float, list[float]]] = {}
    taus, cambios_acum, tamanos = [], [], []
    for s in range(args.particiones):
        valores, tau2, cambios, n = una_particion(p, s, factor)
        taus.append(tau2); cambios_acum.append(cambios); tamanos.append(n)
        for regla, porb in valores.items():
            for b, v in porb.items():
                acum.setdefault(regla, {}).setdefault(b, []).append(v)

    print(f"experimentos en la cartera: {int(np.mean(tamanos)):,}")
    print(f"tau2 entre experimentos = {np.mean(taus):.3e} "
          f"(raíz {np.sqrt(np.mean(taus)):.5f})\n")

    c = pd.DataFrame(cambios_acum)
    print("¿reordena frente a la regla cruda?")
    for k in c.columns:
        print(f"  {k:12} cambia la posición de {c[k].mean():.1%} de los experimentos")

    print("\nganancia realizada media, por presupuesto "
          "(puntos porcentuales de tasa de clic)")
    cab = "  ".join(f"{int(b*100):>6}%" for b in PRESUPUESTOS)
    print(f"{'regla':12} {cab}")
    tabla = {}
    for regla in ("azar", "cruda", "contraida", "cola", "oraculo"):
        fila = [np.mean(acum[regla][b]) for b in PRESUPUESTOS]
        tabla[regla] = {str(b): {"media": float(np.mean(acum[regla][b])),
                                 "de_entre_particiones": float(np.std(acum[regla][b], ddof=1))}
                        for b in PRESUPUESTOS}
        print(f"{regla:12} " + "  ".join(f"{v*100:6.3f}" for v in fila))

    print("\ndiferencia contra la regla cruda (puntos porcentuales)")
    print(f"{'regla':12} {cab}")
    for regla in ("contraida", "cola"):
        dif = [np.mean(acum[regla][b]) - np.mean(acum["cruda"][b]) for b in PRESUPUESTOS]
        gana = [np.mean(np.array(acum[regla][b]) > np.array(acum["cruda"][b]))
                for b in PRESUPUESTOS]
        print(f"{regla:12} " + "  ".join(f"{d*100:+6.3f}" for d in dif))
        print(f"{'  gana en':12} " + "  ".join(f"{g:5.0%} " for g in gana))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = {
        "particiones": args.particiones,
        "factor_v": factor,
        "experimentos": int(np.mean(tamanos)),
        "tau2_entre_experimentos": float(np.mean(taus)),
        "reordenamiento": {k: float(c[k].mean()) for k in c.columns},
        "valor_por_presupuesto": tabla,
    }
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
