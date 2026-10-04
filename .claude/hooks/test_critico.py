#!/usr/bin/env python3
"""Hook PostToolUse(Edit|Write): corre la prueba crítica al tocar la partición.

`src/wcab/thinning.py` es el único módulo donde un error pasa inadvertido y
contamina **todas** las cifras: si las dos mitades no son independientes, la
inflación medida queda mal y nada en el resultado lo delata. Esa es exactamente
la diferencia entre *data thinning* y *data fission*, y el error que casi se
cuela en el planteamiento.

Así que al editar ese módulo (o su prueba) se corre `tests/test_thinning.py`
de inmediato. No se corre la suite completa: un hook lento se desactiva, y uno
que grita por cualquier cosa se ignora.

Silencioso mientras los archivos no existan todavía.
"""

import json
import os
import re
import subprocess
import sys

VIGILADOS = re.compile(r"(thinning|particion|partición)", re.IGNORECASE)
PRUEBA = os.path.join("tests", "test_thinning.py")
PY = os.path.join(".venv", "Scripts", "python.exe")


def normaliza(ruta):
    if not ruta:
        return None
    if os.path.isdir(ruta):
        return ruta
    m = re.match(r"^/([a-zA-Z])/(.*)$", ruta)
    if m:
        cand = m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
        if os.path.isdir(cand):
            return cand
    return None


def raiz(cwd_hook):
    for inicio in (normaliza(cwd_hook), os.getcwd()):
        if not inicio:
            continue
        d = os.path.abspath(inicio)
        for _ in range(6):
            if os.path.isdir(os.path.join(d, ".claude")):
                return d
            padre = os.path.dirname(d)
            if padre == d:
                break
            d = padre
    return None


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0

    ent = datos.get("tool_input") or {}
    resp = datos.get("tool_response") or {}
    archivo = resp.get("filePath") or ent.get("file_path") or ""
    if not VIGILADOS.search(archivo):
        return 0

    base = raiz(datos.get("cwd"))
    if not base:
        return 0

    py = os.path.join(base, PY)
    prueba = os.path.join(base, PRUEBA)
    if not (os.path.exists(py) and os.path.exists(prueba)):
        return 0  # todavía no existen: nada que correr

    r = subprocess.run(
        [py, "-m", "pytest", PRUEBA, "-q", "--no-header"],
        cwd=base,
        capture_output=True,
        text=True,
        timeout=100,
    )
    if r.returncode == 0:
        print(json.dumps({"suppressOutput": True}))
        return 0

    cola = (r.stdout or r.stderr or "").strip().splitlines()[-18:]
    print(
        json.dumps(
            {
                "systemMessage": "La prueba crítica de la partición FALLÓ. "
                "Si las dos mitades no son independientes, todas las cifras del "
                "proyecto quedan mal y nada más lo delata.",
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "tests/test_thinning.py falló:\n"
                    + "\n".join(cola),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
