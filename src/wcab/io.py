"""Download of the public CSV files from OSF.

Archive: Upworthy Research Archive (Matias, Munger, Aubin Le Quere and Ebersole,
*Scientific Data*, 2021) - https://osf.io/jd64p/

Only the exploratory and confirmatory samples are downloaded. The archive's
held-out sample contains *different* experiments rather than more data on the
same ones, so it cannot serve to validate decisions and is not used.
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


def download(target: Path, timeout: int = 300) -> dict[str, Path]:
    """Download any missing CSV files into `target`. Returns the paths."""
    target.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(API, timeout=timeout) as r:
        listing = json.load(r)

    paths: dict[str, Path] = {}
    for entrada in listado["data"]:
        nombre = entrada["attributes"]["name"]
        for clave, local in TARGETS.items():
            if clave in nombre:
                output = destino / local
                rutas[clave] = output
                if output.exists():
                    continue
                url = entrada["links"]["download"]
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    output.write_bytes(resp.read())
    faltan = set(TARGETS) - set(rutas)
    if faltan:
        raise RuntimeError(f"No se encontraron en el OSF: {sorted(faltan)}")
    return rutas
