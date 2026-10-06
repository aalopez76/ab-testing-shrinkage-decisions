"""La rule de exclusión. Vive aquí y en ningún otro lado.

El archivo de Upworthy tiene un fallo de aleatorización documentado: una mala
configuración de la caché de Cloudflare el 25 de junio de 2013 hizo que durante
meses se mostrara una sola variante hasta que la caché expiraba. Afecta a ~22%
de las pruebas y sus responsables desaconsejan usarlas para inferencia causal.

Los CSV públicos del OSF son de 2020-2021 y **no traen la columna que las
marca**, así que la exclusión se deriva por date. Verificado de forma
independiente month a month (ver `diagnostics/srm.py`).

Regla: `.claude/rules/data.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Ventana excluida: desde el inicio de junio de 2013 hasta el fin de enero de 2014.
#: Cerrada por la izquierda, abierta por la derecha.
WINDOW_START = pd.Timestamp("2013-06-01")
WINDOW_END = pd.Timestamp("2014-02-01")


@dataclass(frozen=True)
class ExclusionResult:
    """Qué se excluyó, para poder reportarlo."""

    brazos_antes: int
    brazos_despues: int
    experimentos_antes: int
    experimentos_despues: int

    @property
    def excluded_arms(self) -> int:
        return self.brazos_antes - self.brazos_despues

    @property
    def excluded_experiments(self) -> int:
        return self.experimentos_antes - self.experimentos_despues

    @property
    def retained_fraction(self) -> float:
        if self.experimentos_antes == 0:
            return 0.0
        return self.experimentos_despues / self.experimentos_antes

    def __str__(self) -> str:
        return (
            f"exclusión {WINDOW_START.date()} a {WINDOW_END.date()}: "
            f"{self.excluded_experiments:,} de {self.experimentos_antes:,} "
            f"experiments fuera ({1 - self.retained_fraction:.1%}); "
            f"quedan {self.experimentos_despues:,} "
            f"({self.retained_fraction:.1%})"
        )


def in_failure_window(fechas: pd.Series) -> pd.Series:
    """True para las filas creadas dentro de la ventana del fallo.

    Las fechas que no se pueden interpretar devuelven True (se excluyen): ante
    la duda sobre cuándo se creó un experimento, no se usa para inferencia.
    """
    f = pd.to_datetime(fechas, errors="coerce", utc=False)
    if getattr(f.dtype, "tz", None) is not None:
        f = f.dt.tz_localize(None)
    dentro = (f >= WINDOW_START) & (f < WINDOW_END)
    return dentro | f.isna()


def apply(
    df: pd.DataFrame,
    col_fecha: str = "created_at",
    col_experimento: str = "clickability_test_id",
) -> tuple[pd.DataFrame, ExclusionResult]:
    """Quita las filas de la ventana del fallo y reporta cuánto quitó.

    Devuelve siempre el par (data, resultado) para que quien la llame no pueda
    apply la exclusión sin tener a mano la cuenta de lo que se fue.
    """
    antes_brazos = len(df)
    antes_exp = df[col_experimento].nunique()

    conservar = ~in_failure_window(df[col_fecha])
    out = df.loc[conservar].copy()

    return out, ExclusionResult(
        brazos_antes=antes_brazos,
        brazos_despues=len(out),
        experimentos_antes=antes_exp,
        experimentos_despues=out[col_experimento].nunique(),
    )
