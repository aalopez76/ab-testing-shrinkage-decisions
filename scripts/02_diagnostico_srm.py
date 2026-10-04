"""Paso 0: reproduce el fallo de aleatorización del archivo, mes a mes.

El equipo del archivo reportó en junio de 2024 que una mala configuración de la
caché de Cloudflare afectó ~22% de las pruebas. Los CSV públicos no traen la
columna que las marca, así que este script lo verifica desde cero y produce la
tabla que justifica la exclusión.

Corre SIN exclusión a propósito: es el diagnóstico que la motiva.

Salida: reports/results/02_srm.json
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from wcab import consola
from wcab import panel
from wcab.diagnostics import srm

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reports" / "results" / "02_srm.json"


def sin_exclusion(muestra: str) -> pd.DataFrame:
    """El crudo, con las columnas que el diagnóstico necesita."""
    crudo = panel._leer_crudo(muestra)
    crudo = crudo.loc[crudo["impressions"] > 0]
    return pd.DataFrame(
        {
            "experimento_id": crudo["clickability_test_id"].astype(str),
            "impresiones": crudo["impressions"].astype("int64"),
            "fecha": pd.to_datetime(crudo["created_at"], errors="coerce"),
        }
    )


def main() -> None:
    consola.preparar()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", default="exploratorio",
                    choices=["exploratorio", "confirmatorio"])
    ap.add_argument("--minimo-mes", type=int, default=30)
    args = ap.parse_args()

    datos = sin_exclusion(args.muestra)
    tabla = srm.por_experimento(datos)
    mensual = srm.por_mes(tabla, minimo=args.minimo_mes)

    print(f"{'mes':9} {'exp.':>6} {'desbalance':>11}")
    for _, r in mensual.iterrows():
        barra = "#" * int(r.fraccion_desbalance * 40)
        print(f"{r.mes:9} {int(r.experimentos):6d} {r.fraccion_desbalance:10.1%}  {barra}")

    cifras = {
        "muestra": args.muestra,
        **srm.resumen(tabla),
        "por_mes": [
            {"mes": r.mes, "experimentos": int(r.experimentos),
             "fraccion_desbalance": round(float(r.fraccion_desbalance), 4)}
            for _, r in mensual.iterrows()
        ],
    }
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    previo[args.muestra] = cifras
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(previo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
