"""Descarga de los CSV públicos del OSF.

Archivo: Upworthy Research Archive (Matias, Munger, Aubin Le Quere y Ebersole,
*Scientific Data*, 2021) — https://osf.io/jd64p/

Solo se descargan el exploratory y el confirmatory. La sample de reserva del
archivo son experiments *distintos*, no más data de los mismos, así que no
sirve para validar decisiones y no se usa (ver README, paso 4).
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

OSF_FOLDER = "608ff5fd6801ab02932a448f"
API = f"https://api.osf.io/v2/nodes/jd64p/files/osfstorage/{OSF_FOLDER}/"

TARGETS = {
    "exploratory": "upworthy-exploratory.csv",
    "confirmatory": "upworthy-confirmatory.csv",
}


def download(destino: Path, tiempo_limite: int = 300) -> dict[str, Path]:
    """Descarga los CSV que faltan en `destino`. Devuelve las rutas."""
    destino.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(API, timeout=tiempo_limite) as r:
        listado = json.load(r)

    rutas: dict[str, Path] = {}
    for entrada in listado["data"]:
        nombre = entrada["attributes"]["name"]
        for clave, local in TARGETS.items():
            if clave in nombre:
                output = destino / local
                rutas[clave] = output
                if output.exists():
                    continue
                url = entrada["links"]["download"]
                with urllib.request.urlopen(url, timeout=tiempo_limite) as resp:
                    output.write_bytes(resp.read())
    faltan = set(TARGETS) - set(rutas)
    if faltan:
        raise RuntimeError(f"No se encontraron en el OSF: {sorted(faltan)}")
    return rutas
