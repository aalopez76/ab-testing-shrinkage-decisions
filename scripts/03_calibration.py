"""Paso 1: el veredicto sobre el modelo de ruido.

Contrasta v = p(1-p)/n contra la dispersión observada en los experiments A/A,
donde la diferencia verdadera entre arms es cero por construcción.

Salida: reports/results/03_calibracion.json
"""

import argparse
import json
from pathlib import Path

from wcab import console
from wcab import panel
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "03_calibracion.json"


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--tolerance", type=float, default=0.15)
    args = ap.parse_args()

    p = panel.load(args.sample)
    cal = noise.calibrate(p, tolerance=args.tolerance)
    print(cal)

    if not cal.passed:
        print(
            "\nEl modelo de ruido NO describe estos data. Dos explicaciones, y\n"
            "no son distinguibles con este archivo:\n"
            "  1. Las impressions de un brazo no son independientes (agrupamiento).\n"
            "  2. Esos experiments varían en campos que el archivo no publica.\n"
            "Las dos se declaran. El paso 2 compara v ingenuo contra v corregido."
        )

    metrics = {
        "sample": args.sample,
        "tolerance": args.tolerance,
        **cal.to_dict(),
        "explicaciones_no_distinguibles": [
            "impressions no independientes dentro del brazo (agrupamiento)",
            "variación en campos no publicados por el archivo",
        ],
    }
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
