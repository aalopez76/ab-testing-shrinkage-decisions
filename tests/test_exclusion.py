"""La exclusión es la rule más fácil de violar en silencio, así que se prueba.

Si deja pasar un experimento de la ventana del fallo, se analiza como aleatorio
algo que no lo fue, y nada en el resultado lo delata.
"""

import pandas as pd
import pytest

from wcab import exclusion


def _datos(fechas, experiments=None):
    n = len(fechas)
    return pd.DataFrame(
        {
            "created_at": fechas,
            "clickability_test_id": experiments or list(range(n)),
            "impressions": [100] * n,
        }
    )


def test_quita_la_ventana_completa():
    """Los bordes importan: junio-1 entra, febrero-1 ya no."""
    df = _datos(
        [
            "2013-05-31 23:00:00",   # fuera, se conserva
            "2013-06-01 00:00:00",   # primer día excluido
            "2013-09-15 12:00:00",   # center de la ventana
            "2014-01-31 23:59:00",   # último instante excluido
            "2014-02-01 00:00:00",   # ya fuera, se conserva
        ]
    )
    out, res = exclusion.apply(df)
    assert list(out["clickability_test_id"]) == [0, 4]
    assert res.excluded_experiments == 3
    assert res.experimentos_antes == 5


def test_conserva_todo_cuando_nada_cae_en_la_ventana():
    df = _datos(["2014-06-01", "2015-01-01", "2013-02-01"])
    out, res = exclusion.apply(df)
    assert len(out) == 3
    assert res.excluded_experiments == 0
    assert res.retained_fraction == 1.0


def test_fecha_invalida_se_excluye():
    """Ante la duda sobre cuándo se creó, no se usa para inferencia."""
    df = _datos(["2015-01-01", "no es una date", None])
    out, res = exclusion.apply(df)
    assert len(out) == 1
    assert res.excluded_experiments == 2


def test_cuenta_experimentos_no_brazos():
    """Varios arms del mismo experimento cuentan como un experimento."""
    df = _datos(
        ["2013-09-01"] * 3 + ["2015-01-01"] * 2,
        experiments=["A", "A", "A", "B", "B"],
    )
    out, res = exclusion.apply(df)
    assert res.experimentos_antes == 2
    assert res.experimentos_despues == 1
    assert res.brazos_antes == 5
    assert res.brazos_despues == 2


def test_el_resultado_viene_siempre():
    """No se puede apply la exclusión sin recibir la cuenta de lo que se fue."""
    df = _datos(["2013-09-01", "2015-01-01"])
    output = exclusion.apply(df)
    assert isinstance(output, tuple) and len(output) == 2
    _, res = output
    assert "exclusión" in str(res)


@pytest.mark.parametrize("tz", [None, "UTC"])
def test_tolera_zona_horaria(tz):
    f = pd.to_datetime(pd.Series(["2013-09-01", "2015-01-01"]), utc=tz == "UTC")
    df = pd.DataFrame(
        {"created_at": f, "clickability_test_id": [1, 2], "impressions": [10, 10]}
    )
    out, _ = exclusion.apply(df)
    assert list(out["clickability_test_id"]) == [2]
