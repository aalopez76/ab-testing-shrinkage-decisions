"""El panel es la única puerta a los datos, así que se comprueba su contrato."""

import pandas as pd
import pytest

from wcab import panel


@pytest.fixture(scope="module")
def p():
    return panel.cargar("exploratorio")


def test_tiene_las_columnas_del_contrato(p):
    assert list(p.columns) == panel.COLUMNAS


def test_la_exclusion_viene_aplicada(p):
    """Ningún brazo del panel puede caer en la ventana del fallo."""
    f = pd.to_datetime(p["fecha"])
    dentro = (f >= pd.Timestamp("2013-06-01")) & (f < pd.Timestamp("2014-02-01"))
    assert not dentro.any()
    assert p["fecha"].notna().all()


def test_sin_brazos_vacios(p):
    assert (p["impresiones"] > 0).all()
    assert (p["clics"] >= 0).all()
    assert (p["clics"] <= p["impresiones"]).all()


def test_theta_y_v_son_coherentes(p):
    esperado = p["clics"] / p["impresiones"]
    assert (p["theta_hat"] - esperado).abs().max() < 1e-12
    v = p["theta_hat"] * (1 - p["theta_hat"]) / p["impresiones"]
    assert (p["v"] - v).abs().max() < 1e-15
    assert (p["v"] >= 0).all()


def test_los_aa_no_varian_en_ningun_campo(p):
    """Un experimento marcado A/A no puede tener variación registrada."""
    aa = p.loc[p["es_aa"]]
    assert not aa["varia_titular"].any()
    assert not aa["varia_imagen"].any()


def test_hay_aa_suficientes_para_calibrar(p):
    """Si no hay A/A, el paso 1 del plan no se puede correr.

    El umbral es 100 experimentos: con 2 a 14 brazos cada uno, da cientos de
    grados de libertad para la Q de Cochran, que es de sobra. No se pone más
    alto para no clavar en el test una expectativa mía en lugar de un requisito.
    """
    assert p.loc[p["es_aa"], "experimento_id"].nunique() >= 100


def test_el_resumen_trae_las_cifras_que_citan_los_documentos(p):
    r = panel.resumen(p)
    for clave in (
        "brazos", "experimentos", "impresiones", "tasa_global",
        "brazos_por_experimento_max", "impresiones_por_brazo_mediana",
        "semanas", "experimentos_aa",
    ):
        assert clave in r
    assert 2 <= r["brazos_por_experimento_min"]
    assert 0 < r["tasa_global"] < 1
