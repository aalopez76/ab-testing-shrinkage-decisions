"""BHS: que reproduzca su propio caso base, y que sepa decir «no hago falta».

La tercera prueba es la que importa. Si el ajuste pidiera flexibilidad local
siempre, el resultado sobre datos reales no significaría nada: habría que
comprobar primero que el método discrimina.
"""

import numpy as np
import pytest

from wcab.shrinkage import bhs


@pytest.fixture
def datos():
    rng = np.random.default_rng(0)
    n = 3000
    s2 = rng.gamma(4, 1e-6, n)
    return rng, n, s2


def test_a_grande_reproduce_la_contraccion_global(datos):
    """El artículo llama a λᵢ=1 «Bayesian Global Shrinkage». Debe salir de BHS."""
    rng, n, s2 = datos
    m0, tau = 0.0, 2e-5
    theta = rng.normal(m0, np.sqrt(tau), n) + rng.normal(0, np.sqrt(s2))

    ajuste = bhs.AjusteBHS(m0=m0, tau=tau, a=5_000.0, log_verosimilitud=0.0,
                           log_verosimilitud_global=0.0, experimentos=n)
    por_bhs = bhs.media_posterior(theta, s2, ajuste)

    alpha = s2 / (s2 + tau)
    global_ = (1.0 - alpha) * theta + alpha * m0

    # escala de theta ~ sqrt(2e-5) ≈ 4.5e-3; una tolerancia de 1e-5 es 0.2%
    assert np.max(np.abs(por_bhs - global_)) < 1e-5
    assert np.max(np.abs(bhs.alpha_efectivo(theta, s2, ajuste) - alpha)) < 1e-3


def test_recupera_los_grados_de_libertad_de_una_previa_t(datos):
    """Con una previa t de 3 gl construida a mano, â debe caer cerca de 3."""
    rng, n, s2 = datos
    m0, tau, gl = 0.0, 2e-5, 3.0
    theta = m0 + np.sqrt(tau) * rng.standard_t(gl, n) + rng.normal(0, np.sqrt(s2))

    r = bhs.ajustar(theta, s2)
    assert 2.0 < r.a < 6.0
    assert r.pide_flexibilidad_local


def test_con_previa_normal_NO_pide_flexibilidad_local(datos):
    """La prueba decisiva: el método tiene que saber decir que no hace falta."""
    rng, n, s2 = datos
    m0, tau = 0.0, 2e-5
    theta = rng.normal(m0, np.sqrt(tau), n) + rng.normal(0, np.sqrt(s2))

    r = bhs.ajustar(theta, s2)
    assert not r.pide_flexibilidad_local, (
        f"con previa normal pidió flexibilidad local: a={r.a:.1f}, "
        f"razón de verosimilitudes={r.gana_a_la_global:.1f}"
    )


def test_el_peso_efectivo_queda_en_el_intervalo_valido(datos):
    rng, n, s2 = datos
    theta = rng.normal(0.0, 4e-3, n)
    ajuste = bhs.AjusteBHS(m0=0.0, tau=2e-5, a=3.0, log_verosimilitud=0.0,
                           log_verosimilitud_global=0.0, experimentos=n)
    alpha = bhs.alpha_efectivo(theta, s2, ajuste)
    assert np.all(alpha > 0.0) and np.all(alpha < 1.0)


def test_contrae_menos_a_los_datos_lejanos_del_centro(datos):
    """La robustez de BHS: colas pesadas ⇒ menos contracción lejos del centro."""
    _, _, _ = datos
    s2 = np.full(5, 1e-5)
    theta = np.array([0.0, 2e-3, 5e-3, 1e-2, 5e-2])
    ajuste = bhs.AjusteBHS(m0=0.0, tau=1e-5, a=2.5, log_verosimilitud=0.0,
                           log_verosimilitud_global=0.0, experimentos=5)
    alpha = bhs.alpha_efectivo(theta, s2, ajuste)
    assert np.all(np.diff(alpha) < 0), f"el peso no decrece con la distancia: {alpha}"
