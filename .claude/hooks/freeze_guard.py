#!/usr/bin/env python3
"""Hook PreToolUse(Bash): protege la muestra confirmatoria hasta congelar el método.

El archivo trae tres muestras disjuntas. El exploratorio (4 873 experimentos) es
para desarrollar; el confirmatorio (22 743) es para confirmar **una sola vez**,
con el método ya fijado. Si se mira el confirmatorio durante el desarrollo, se
pierde lo único que lo hace valioso y no hay forma de recuperarlo.

Este hook bloquea cualquier comando que toque el confirmatorio mientras no
exista `reports/results/METODO_CONGELADO.json`. Convierte el compromiso previo
del README en una puerta que el código impide cruzar por descuido.

Entrada: JSON del hook por stdin.
Salida:  JSON con permissionDecision=deny si corresponde; silencio si no.
"""

import json
import os
import re
import sys

MARCA = os.path.join("reports", "results", "METODO_CONGELADO.json")

# Señales de que el comando va a LEER el confirmatorio
CONFIRMATORIO = re.compile(
    r"upworthy-confirmatory|confirmatorio|--muestra[= ]+confirm|"
    r"muestra[\"']?\s*[:=]\s*[\"']?confirm",
    re.IGNORECASE,
)

# Comandos que solo inspeccionan el sistema de archivos: no leen datos
INOCUOS = re.compile(
    r"^\s*(ls|ll|dir|find|stat|wc|du|head\s+-c|file|git\s+(status|log|diff|show))\b",
    re.IGNORECASE,
)

# El propio script de congelación debe poder correr
CONGELAR = re.compile(r"congelar|freeze", re.IGNORECASE)


def normaliza(ruta):
    """Acepta rutas estilo Git Bash (/d/GitHub/...) y las vuelve nativas."""
    if not ruta:
        return None
    if os.path.isdir(ruta):
        return ruta
    m = re.match(r"^/([a-zA-Z])/(.*)$", ruta)      # /d/GitHub/... -> D:\GitHub\...
    if m:
        cand = m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
        if os.path.isdir(cand):
            return cand
    return None


def raiz_proyecto(cwd_hook):
    """Ubica la raíz del proyecto, o None si no la encuentra.

    Devolver None es significativo: el llamador bloquea. Un guardián que falla
    permitiendo es peor que ninguno, porque da falsa confianza.
    """
    for inicio in (normaliza(cwd_hook), os.getcwd()):
        if not inicio:
            continue
        d = os.path.abspath(inicio)
        for _ in range(6):
            if os.path.exists(os.path.join(d, "README.md")) and os.path.isdir(
                os.path.join(d, ".claude")
            ):
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

    if datos.get("tool_name") != "Bash":
        return 0

    comando = (datos.get("tool_input") or {}).get("command") or ""
    if not CONFIRMATORIO.search(comando):
        return 0
    if INOCUOS.match(comando) or CONGELAR.search(comando):
        return 0

    raiz = raiz_proyecto(datos.get("cwd"))
    if raiz and os.path.exists(os.path.join(raiz, MARCA)):
        return 0  # ya está congelado: adelante

    extra = (
        ""
        if raiz
        else "\n\n(No se pudo ubicar la raíz del proyecto, así que se bloquea por "
        "precaución: este guardián falla cerrado a propósito.)"
    )
    razon = (
        "Bloqueado: la muestra CONFIRMATORIA no se toca hasta congelar el método.\n\n"
        "El archivo tiene tres muestras disjuntas. El exploratorio (4 873 "
        "experimentos) es para desarrollar; el confirmatorio (22 743) se usa UNA "
        "sola vez, con el método ya fijado. Mirarlo antes destruye lo único que lo "
        "hace valioso, y no se puede deshacer.\n\n"
        "Para desarrollar, usa `data/raw/upworthy-exploratory.csv` o "
        "`--muestra exploratorio`.\n"
        "Cuando el método esté fijado, crea " + MARCA + " con la fecha, el commit "
        "de git, el criterio de éxito y los métodos congelados. A partir de ahí "
        "este hook deja pasar.\n\n"
        "Regla: .claude/rules/metodo.md" + extra
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
