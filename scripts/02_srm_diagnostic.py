"""Paso 0: reproduce el fallo de aleatorización del archivo, month a month.

El equipo del archivo reportó en junio de 2024 que una mala configuración de la
caché de Cloudflare afectó ~22% de las pruebas. Los CSV públicos no traen la
columna que las marca, así que este script lo verifica desde cero y produce la
table que justifica la exclusión.

Corre SIN exclusión a propósito: es el diagnóstico que la motiva.

Salida: reports/results/02_srm.json
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from wcab import console
from wcab import panel
from wcab.diagnostics import srm

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "results" / "02_srm.json"


def sin_exclusion(sample: str) -> pd.DataFrame:
    """El crudo, con las columnas que el diagnóstico necesita."""
    crudo = panel._read_raw(sample)
    crudo = crudo.loc[crudo["impressions"] > 0]
    return pd.DataFrame(
        {
            "experiment_id": crudo["clickability_test_id"].astype(str),
            "impressions": crudo["impressions"].astype("int64"),
            "date": pd.to_datetime(crudo["created_at"], errors="coerce"),
        }
    )


def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="exploratory",
                    choices=["exploratory", "confirmatory"])
    ap.add_argument("--minimo-month", type=int, default=30)
    args = ap.parse_args()

    data = sin_exclusion(args.sample)
    table = srm.per_experiment(data)
    mensual = srm.by_month(table, minimo=args.minimo_mes)

    print(f"{'month':9} {'exp.':>6} {'desbalance':>11}")
    for _, r in mensual.iterrows():
        barra = "#" * int(r.imbalance_fraction * 40)
        print(f"{r.month:9} {int(r.experiments):6d} {r.imbalance_fraction:10.1%}  {barra}")

    metrics = {
        "sample": args.sample,
        **srm.summary(table),
        "by_month": [
            {"month": r.month, "experiments": int(r.experiments),
             "imbalance_fraction": round(float(r.imbalance_fraction), 4)}
            for _, r in mensual.iterrows()
        ],
    }
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    previous[args.sample] = metrics
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(previous, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ncifras -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
