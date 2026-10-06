"""Salida de texto que no se cae por la codificación de la terminal.

Los scripts imprimen en español, con tildes y flechas. La consola de Windows
usa cp1252 por defecto y revienta con un UnicodeEncodeError ante un carácter
que no esté en esa table — así que un script perfectamente correcto deja de
correr por el terminal en el que se invoca, que es lo contrario de reproducible.

`prepare()` pone la output en UTF-8 y, si el terminal no lo admite, reemplaza
los caracteres imposibles en lugar de abortar.
"""

from __future__ import annotations

import sys


def prepare() -> None:
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is None:
            continue
        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            try:
                reconfigurar(errors="replace")
            except (ValueError, OSError):
                pass
