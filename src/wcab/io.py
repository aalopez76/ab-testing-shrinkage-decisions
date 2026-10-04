"""Descarga de los CSV públicos del OSF.

Archivo: Upworthy Research Archive (Matias, Munger, Aubin Le Quere y Ebersole,
*Scientific Data*, 2021) — https://osf.io/jd64p/

Solo se descargan el exploratorio y el confirmatorio. La muestra de reserva del
archivo son experimentos *distintos*, no más datos de los mismos, así que no
sirve para validar decisiones y no se usa (ver README, paso 4).
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

CARPETA_OSF = "608ff5fd6801ab02932a448f"
API = f"https://api.osf.io/v2/nodes/jd64p/files/osfstorage/{CARPETA_OSF}/"

DESTINOS = {
    "exploratory": "upworthy-exploratory.csv",
    "confirmatory": "upworthy-confirmatory.csv",
}


def descargar(destino: Path, tiempo_limite: int = 300) -> dict[str, Path]:
    """Descarga los CSV que faltan en `destino`. Devuelve las rutas."""
    destino.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(API, timeout=tiempo_limite) as r:
        listado = json.load(r)

    rutas: dict[str, Path] = {}
    for entrada in listado["data"]:
        nombre = entrada["attributes"]["name"]
        for clave, local in DESTINOS.items():
            if clave in nombre:
                salida = destino / local
                rutas[clave] = salida
                if salida.exists():
                    continue
                url = entrada["links"]["download"]
                with urllib.request.urlopen(url, timeout=tiempo_limite) as resp:
                    salida.write_bytes(resp.read())
    faltan = set(DESTINOS) - set(rutas)
    if faltan:
        raise RuntimeError(f"No se encontraron en el OSF: {sorted(faltan)}")
    return rutas
