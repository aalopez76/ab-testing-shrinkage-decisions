"""Text output that does not break on the terminal's encoding.

The scripts print arrows and other non-ASCII characters. The Windows console
defaults to cp1252 and raises a UnicodeEncodeError on any character outside that
table, so a perfectly correct script stops running because of the terminal it was
invoked from, which is the opposite of reproducible.

`prepare()` switches the output to UTF-8 and, where the terminal does not support
it, replaces the impossible characters rather than aborting.
"""

from __future__ import annotations

import sys


def prepare() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            try:
                reconfigure(errors="replace")
            except (ValueError, OSError):
                pass
