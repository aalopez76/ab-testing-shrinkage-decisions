"""La prueba crítica del proyecto.

Si la partición está mal, **todas** las metrics quedan mal y nada en el
resultado lo delata: la inflación medida sale sesgada y los números se ven
perfectamente normales. Es el único módulo con esa propiedad.

La propiedad que hay que defender es la **independencia marginal** de las dos
mitades. Es exactamente lo que distingue *data thinning* (válido para la
binomial) de *data fission* (que para la binomial no da partes independientes),
y la confusión que casi se cuela en el planteamiento de este proyecto.

Hay un hook en `.claude/hooks/test_critico.py` que corre este archivo al editar
la partición.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import thinning

N_SIM = 30_000
P_VERDADERA = 0.013      # la rate real del archivo, ~1.3%
N_POR_BRAZO = 3_000      # la mediana real de impressions por brazo


@pytest.fixture(scope="module")
def mitades():
    """Muchas realizaciones de X ~ Binomial(n, p), cada una partida en dos."""
    rng = np.random.default_rng(20261003)
    x = rng.binomial(N_POR_BRAZO, P_VERDADERA, size=N_SIM)
    n = np.full(N_SIM, N_POR_BRAZO, dtype=np.int64)
    n_a, c_a, n_b, c_b = thinning.split_counts(n, x, 0.5, rng)
    return {"x": x, "n_a": n_a, "c_a": c_a, "n_b": n_b, "c_b": c_b}


# --------------------------------------------------------------------------
# 1. Exactitud: la partición no inventa ni pierde nada
# --------------------------------------------------------------------------

def test_las_mitades_suman_el_original(mitades):
    m = mitades
    assert np.array_equal(m["c_a"] + m["c_b"], m["x"])
    assert np.array_equal(m["n_a"] + m["n_b"], np.full(N_SIM, N_POR_BRAZO))


def test_ninguna_mitad_queda_vacia(mitades):
    assert (mitades["n_a"] >= 1).all()
    assert (mitades["n_b"] >= 1).all()


def test_los_clics_nunca_exceden_las_impresiones(mitades):
    m = mitades
    assert (m["c_a"] <= m["n_a"]).all() and (m["c_a"] >= 0).all()
    assert (m["c_b"] <= m["n_b"]).all() and (m["c_b"] >= 0).all()


# --------------------------------------------------------------------------
# 2. Insesgadez: cada mitad estima la rate verdadera
# --------------------------------------------------------------------------

def test_cada_mitad_es_insesgada(mitades):
    m = mitades
    for lado in ("a", "b"):
        rate = (m[f"c_{lado}"] / m[f"n_{lado}"]).mean()
        error = abs(rate - P_VERDADERA)
        # 4 errores estándar de la mean de N_SIM observaciones
        tope = 4 * np.sqrt(P_VERDADERA * (1 - P_VERDADERA) / (N_POR_BRAZO / 2) / N_SIM)
        assert error < tope, f"mitad {lado}: {rate:.6f} vs {P_VERDADERA}"


def test_la_varianza_de_cada_mitad_es_la_binomial_correcta(mitades):
    """Si la mitad fuera Binomial(n_a, p), su varianza debe ser n_a·p·(1-p)."""
    m = mitades
    for lado in ("a", "b"):
        esperada = (N_POR_BRAZO / 2) * P_VERDADERA * (1 - P_VERDADERA)
        observada = m[f"c_{lado}"].var(ddof=1)
        assert 0.9 < observada / esperada < 1.1, (
            f"mitad {lado}: varianza {observada:.1f} vs esperada {esperada:.1f}"
        )


# --------------------------------------------------------------------------
# 3. LA PRUEBA CRÍTICA: independencia marginal
# --------------------------------------------------------------------------

def test_las_dos_mitades_son_independientes(mitades):
    """El corazón del proyecto.

    Las tasas de las dos mitades deben ser incorreladas. Si estuvieran ligadas,
    elegir el máximo en la mitad A arrastraría mecánicamente a la mitad B y la
    inflación medida saldría sesgada, sin que nada lo delate.
    """
    m = mitades
    theta_a = m["c_a"] / m["n_a"]
    theta_b = m["c_b"] / m["n_b"]
    r = float(np.corrcoef(theta_a, theta_b)[0, 1])
    tope = 4 / np.sqrt(N_SIM)          # 4 errores estándar de una correlación nula
    assert abs(r) < tope, (
        f"correlación entre mitades = {r:+.4f}, debería ser ~0 (tope {tope:.4f}). "
        "Si es muy negativa, la partición está condicionando mal: sería el "
        "comportamiento de data fission, no de data thinning."
    )


def test_contraste_la_particion_ingenua_esta_correlacionada():
    """Documenta por qué la implementación es la que es.

    Una partición «ingenua» al estilo de *data fission* reparte la TASA en lugar
    de los conteos: θ_A = θ + Z, θ_B = θ − Z. Su correlación es

        corr(θ+Z, θ−Z) = (Var θ − Var Z) / (Var θ + Var Z)

    que solo da cero en el punto exacto Var Z = Var θ y es negativa en cuanto el
    ruido domina. Es decir: **la independencia dependería de acertar la varianza
    del ruido**, que es precisamente la cantidad que el proyecto no conoce — por
    eso se parten los conteos y no la rate.

    Aquí se usa Var Z ≈ 23 · Var θ, donde la anticorrelación es inequívoca.
    """
    rng = np.random.default_rng(1)
    theta = rng.binomial(N_POR_BRAZO, P_VERDADERA, size=20_000) / N_POR_BRAZO
    sd_theta = np.sqrt(P_VERDADERA * (1 - P_VERDADERA) / N_POR_BRAZO)
    ruido = rng.normal(0, 5 * sd_theta, size=20_000)

    r = float(np.corrcoef(theta + ruido, theta - ruido)[0, 1])
    esperado = (sd_theta**2 - (5 * sd_theta) ** 2) / (
        sd_theta**2 + (5 * sd_theta) ** 2
    )
    assert r < -0.8, f"el atajo ingenuo debería anticorrelacionar: r={r:+.3f}"
    assert abs(r - esperado) < 0.05, (
        f"la correlación observada ({r:+.3f}) debería seguir el álgebra "
        f"({esperado:+.3f})"
    )


# --------------------------------------------------------------------------
# 4. La interfaz sobre el panel
# --------------------------------------------------------------------------

def _panel_minimo(n=(3000, 3000, 5000), c=(40, 35, 70)):
    d = pd.DataFrame(
        {
            "experiment_id": ["e1", "e1", "e2"],
            "arm_id": ["a", "b", "c"],
            "impressions": n,
            "clicks": c,
            "is_aa": [False, False, False],
        }
    )
    d["theta_hat"] = d.clicks / d.impressions
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impressions
    return d


def test_partir_conserva_el_panel_y_recalcula():
    p = _panel_minimo()
    out = thinning.split(p, fraction=0.5, seed=3)
    assert thinning.check_sum(p, out)
    for mitad in (out.estimation, out.evaluation):
        assert list(mitad.columns) == list(p.columns)
        assert np.allclose(mitad["theta_hat"], mitad["clicks"] / mitad["impressions"])
        v = mitad["theta_hat"] * (1 - mitad["theta_hat"]) / mitad["impressions"]
        assert np.allclose(mitad["v"], v)
    # las columnas descriptivas se arrastran sin changes
    assert list(out.estimation["experiment_id"]) == list(p["experiment_id"])


def test_la_semilla_hace_reproducible_la_particion():
    p = _panel_minimo()
    a = thinning.split(p, seed=42).estimation["clicks"].tolist()
    b = thinning.split(p, seed=42).estimation["clicks"].tolist()
    c = thinning.split(p, seed=43).estimation["clicks"].tolist()
    assert a == b
    assert a != c


@pytest.mark.parametrize("fraction", [0.0, 1.0, -0.1, 1.5])
def test_rechaza_fracciones_invalidas(fraction):
    with pytest.raises(ValueError):
        thinning.split(_panel_minimo(), fraction=fraction)


def test_rechaza_datos_imposibles():
    with pytest.raises(ValueError):
        thinning.split_counts([100], [200], 0.5, np.random.default_rng(0))
    with pytest.raises(ValueError):
        thinning.split_counts([1], [0], 0.5, np.random.default_rng(0))
