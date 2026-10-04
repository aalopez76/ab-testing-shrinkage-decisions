"""Construye el panel canónico y escribe sus cifras de escala.

Salida: data/derived/panel-<muestra>.parquet  y  reports/results/01_panel.json

Toda cifra de escala que citen los documentos sale de este JSON. Si una cifra
de un documento no está aquí, es huérfana (ver .claude/rules/evidencia.md).
"""

import argparse
import json
from pathlib import Path

from wcab import consola
from wcab import panel

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "01_panel.json"


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    args = ap.parse_args()

    tabla, res = panel.construir(args.muestra)
    destino = panel.guardar(tabla, args.muestra)

    cifras = {
        "muestra": args.muestra,
        "exclusion": {
            "ventana": "2013-06-01 a 2014-02-01",
            "brazos_antes": res.brazos_antes,
            "brazos_despues": res.brazos_despues,
            "experimentos_antes": res.experimentos_antes,
            "experimentos_despues": res.experimentos_despues,
            "fraccion_conservada": round(res.fraccion_conservada, 4),
        },
        "panel": panel.resumen(tabla),
    }

    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")

    print(res)
    print(f"panel -> {destino.relative_to(RAIZ)}")
    print(f"cifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
