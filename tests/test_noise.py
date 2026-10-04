"""La calibración decide si `v` sirve, así que se prueba contra verdad conocida."""

import numpy as np
import pandas as pd

from wcab.diagnostics import noise


def _panel(n_exp, k, n_por_brazo, p, factor_exceso=1.0, semilla=0):
    """Genera un panel A/A sintético.

    `factor_exceso` > 1 infla la varianza real sin cambiar la media, simulando
    impresiones agrupadas: así se puede comprobar que la calibración lo detecta.
    """
    rng = np.random.default_rng(semilla)
    filas = []
    for e in range(n_exp):
        for b in range(k):
            if factor_exceso == 1.0:
                clics = rng.binomial(n_por_brazo, p)
            else:
                # beta-binomial: misma media, varianza inflada por el factor
                rho = (factor_exceso - 1.0) / (n_por_brazo - 1.0)
                a = p * (1 - rho) / rho
                bb = (1 - p) * (1 - rho) / rho
                clics = rng.binomial(n_por_brazo, rng.beta(a, bb))
            filas.append((f"e{e}", f"e{e}b{b}", n_por_brazo, clics))
    d = pd.DataFrame(filas, columns=["experimento_id", "brazo_id", "impresiones", "clics"])
    d["theta_hat"] = d.clics / d.impresiones
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impresiones
    d["es_aa"] = True
    return d


def test_aprueba_cuando_el_ruido_es_binomial_puro():
    """Sin exceso, Q/gl debe quedar cerca de 1 y la calibración aprobar."""
    cal = noise.calibrar(_panel(400, 4, 3000, 0.013))
    assert 0.85 < cal.razon_Q_gl < 1.15, cal
    assert cal.aprobada
    assert cal.fraccion_p_005 < 0.12


def test_detecta_un_exceso_de_dispersion_conocido():
    """Con la varianza inflada ×2, la calibración debe rechazar y medirlo."""
    cal = noise.calibrar(_panel(400, 4, 3000, 0.013, factor_exceso=2.0, semilla=7))
    assert not cal.aprobada
    assert 1.6 < cal.razon_Q_gl < 2.5, cal
    assert cal.factor_diseno == cal.razon_Q_gl


def test_corregir_escala_la_varianza():
    v = pd.Series([1e-6, 4e-6])
    out = noise.corregir(v, 1.9)
    assert np.allclose(out, [1.9e-6, 7.6e-6])


def test_corregir_rechaza_factores_invalidos():
    import pytest
    with pytest.raises(ValueError):
        noise.corregir(pd.Series([1e-6]), 0.0)
