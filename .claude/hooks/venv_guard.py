#!/usr/bin/env python3
"""Hook PreToolUse(Bash): bloquea invocar Python o pip fuera del venv del proyecto.

La regla permanente del proyecto es usar ./.venv/Scripts/python.exe y nunca el
Python global. Esta máquina tiene un Python global en el PATH, así que un
`python script.py` escrito por descuido se ejecutaría con el intérprete
equivocado y con otras dependencias. El hook lo impide antes de que corra.

Entrada: JSON del hook por stdin.
Salida:  JSON con permissionDecision=deny si detecta una invocación global.
         Silencio (y salida 0) en cualquier otro caso.
"""

import json
import re
import sys

# Invocación de python/pip en posición de comando: al inicio, o tras ; && || | ( &
INVOCACION = re.compile(
    r"(?:^|[;&|(]|&&|\|\|)\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"(python3?|pip3?|py)(?:\.exe)?\b",
    re.IGNORECASE,
)

# Señales de que SÍ se está usando el venv del proyecto
VENV = re.compile(r"\.venv[\\/]|uv\s+run|poetry\s+run", re.IGNORECASE)

# Excepción de arranque: crear el propio venv exige el Python global una vez.
# Sin esto el hook impediría construir el entorno que el hook exige usar.
BOOTSTRAP = re.compile(r"-m\s+venv\b|--version\b|-m\s+ensurepip\b", re.IGNORECASE)


def segmentos(comando: str):
    """Parte el comando en segmentos separados por operadores de shell."""
    return [s for s in re.split(r"&&|\|\||[;|]", comando) if s.strip()]


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0  # ante la duda, no estorbar

    if datos.get("tool_name") != "Bash":
        return 0

    comando = (datos.get("tool_input") or {}).get("command") or ""

    culpables = [
        s.strip()
        for s in segmentos(comando)
        if INVOCACION.search(s) and not VENV.search(s) and not BOOTSTRAP.search(s)
    ]
    if not culpables:
        return 0

    razon = (
        "Bloqueado: este proyecto usa exclusivamente ./.venv/Scripts/python.exe "
        "(hay un Python global en el PATH y usarlo daría otro intérprete y otras "
        "dependencias).\n"
        "Segmento detectado: " + culpables[0] + "\n"
        "Reescribe el comando usando ./.venv/Scripts/python.exe (o `uv run`). "
        "Si el venv aún no existe, créalo primero."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": razon,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
