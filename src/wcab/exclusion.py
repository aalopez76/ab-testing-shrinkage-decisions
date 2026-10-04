"""La regla de exclusión. Vive aquí y en ningún otro lado.

El archivo de Upworthy tiene un fallo de aleatorización documentado: una mala
configuración de la caché de Cloudflare el 25 de junio de 2013 hizo que durante
meses se mostrara una sola variante hasta que la caché expiraba. Afecta a ~22%
de las pruebas y sus responsables desaconsejan usarlas para inferencia causal.

Los CSV públicos del OSF son de 2020-2021 y **no traen la columna que las
marca**, así que la exclusión se deriva por fecha. Verificado de forma
independiente mes a mes (ver `diagnostics/srm.py`).

Regla: `.claude/rules/datos.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Ventana excluida: desde el inicio de junio de 2013 hasta el fin de enero de 2014.
#: Cerrada por la izquierda, abierta por la derecha.
VENTANA_INICIO = pd.Timestamp("2013-06-01")
VENTANA_FIN = pd.Timestamp("2014-02-01")


@dataclass(frozen=True)
class ResultadoExclusion:
    """Qué se excluyó, para poder reportarlo."""

    brazos_antes: int
    brazos_despues: int
    experimentos_antes: int
    experimentos_despues: int

    @property
    def brazos_excluidos(self) -> int:
        return self.brazos_antes - self.brazos_despues

    @property
    def experimentos_excluidos(self) -> int:
        return self.experimentos_antes - self.experimentos_despues

    @property
    def fraccion_conservada(self) -> float:
        if self.experimentos_antes == 0:
            return 0.0
        return self.experimentos_despues / self.experimentos_antes

    def __str__(self) -> str:
        return (
            f"exclusión {VENTANA_INICIO.date()} a {VENTANA_FIN.date()}: "
            f"{self.experimentos_excluidos:,} de {self.experimentos_antes:,} "
            f"experimentos fuera ({1 - self.fraccion_conservada:.1%}); "
            f"quedan {self.experimentos_despues:,} "
            f"({self.fraccion_conservada:.1%})"
        )


def en_ventana_del_fallo(fechas: pd.Series) -> pd.Series:
    """True para las filas creadas dentro de la ventana del fallo.

    Las fechas que no se pueden interpretar devuelven True (se excluyen): ante
    la duda sobre cuándo se creó un experimento, no se usa para inferencia.
    """
    f = pd.to_datetime(fechas, errors="coerce", utc=False)
    if getattr(f.dtype, "tz", None) is not None:
        f = f.dt.tz_localize(None)
    dentro = (f >= VENTANA_INICIO) & (f < VENTANA_FIN)
    return dentro | f.isna()


def aplicar(
    df: pd.DataFrame,
    col_fecha: str = "created_at",
    col_experimento: str = "clickability_test_id",
) -> tuple[pd.DataFrame, ResultadoExclusion]:
    """Quita las filas de la ventana del fallo y reporta cuánto quitó.

    Devuelve siempre el par (datos, resultado) para que quien la llame no pueda
    aplicar la exclusión sin tener a mano la cuenta de lo que se fue.
    """
    antes_brazos = len(df)
    antes_exp = df[col_experimento].nunique()

    conservar = ~en_ventana_del_fallo(df[col_fecha])
    out = df.loc[conservar].copy()

    return out, ResultadoExclusion(
        brazos_antes=antes_brazos,
        brazos_despues=len(out),
        experimentos_antes=antes_exp,
        experimentos_despues=out[col_experimento].nunique(),
    )
