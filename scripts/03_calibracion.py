"""Paso 1: el veredicto sobre el modelo de ruido.

Contrasta v = p(1-p)/n contra la dispersión observada en los experimentos A/A,
donde la diferencia verdadera entre brazos es cero por construcción.

Salida: reports/results/03_calibracion.json
"""

import argparse
import json
from pathlib import Path

from wcab import consola
from wcab import panel
from wcab.diagnostics import noise

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "03_calibracion.json"


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--tolerancia", type=float, default=0.15)
    args = ap.parse_args()

    p = panel.cargar(args.muestra)
    cal = noise.calibrar(p, tolerancia=args.tolerancia)
    print(cal)

    if not cal.aprobada:
        print(
            "\nEl modelo de ruido NO describe estos datos. Dos explicaciones, y\n"
            "no son distinguibles con este archivo:\n"
            "  1. Las impresiones de un brazo no son independientes (agrupamiento).\n"
            "  2. Esos experimentos varían en campos que el archivo no publica.\n"
            "Las dos se declaran. El paso 2 compara v ingenuo contra v corregido."
        )

    cifras = {
        "muestra": args.muestra,
        "tolerancia": args.tolerancia,
        **cal.to_dict(),
        "explicaciones_no_distinguibles": [
            "impresiones no independientes dentro del brazo (agrupamiento)",
            "variación en campos no publicados por el archivo",
        ],
    }
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
