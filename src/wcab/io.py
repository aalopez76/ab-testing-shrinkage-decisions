"""Download of the public CSV files from OSF.

Archive: Upworthy Research Archive (Matias, Munger, Aubin Le Quere and Ebersole,
*Scientific Data*, 2021) - https://osf.io/jd64p/, licensed CC BY 4.0.

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
    """Download any missing CSV files into `target`. Returns their paths.

    Files already present are left untouched, so this is safe to re-run.

    If the OSF listing does not offer both samples it raises rather than
    returning a partial result: a caller handed only one of the two would build
    a panel from an incomplete archive without noticing.
    """
    target.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(API, timeout=timeout) as response:
        listing = json.load(response)

    paths: dict[str, Path] = {}
    for entry in listing["data"]:
        name = entry["attributes"]["name"]
        for key, local in TARGETS.items():
            if key in name:
                output = target / local
                paths[key] = output
                if output.exists():
                    continue
                url = entry["links"]["download"]
                with urllib.request.urlopen(url, timeout=timeout) as payload:
                    output.write_bytes(payload.read())

    missing = set(TARGETS) - set(paths)
    if missing:
        raise RuntimeError(f"not found on OSF: {sorted(missing)}")
    return paths
