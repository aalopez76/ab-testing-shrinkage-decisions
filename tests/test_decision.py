"""Las reglas de decisión, y la propiedad que explica el resultado de la fase D."""

import numpy as np
import pandas as pd

from wcab import decision, shrinkage


def _panel(theta, n=3000, exp="e1"):
    clics = np.rint(np.asarray(theta) * n).astype(int)
    d = pd.DataFrame(
        {
            "experimento_id": [exp] * len(theta),
            "brazo_id": [f"{exp}b{i}" for i in range(len(theta))],
            "impresiones": [n] * len(theta),
            "clics": clics,
            "es_aa": [False] * len(theta),
        }
    )
    d["theta_hat"] = d.clics / d.impresiones
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impresiones
    return d


def test_la_contraccion_uniforme_NO_puede_cambiar_el_maximo():
    """La propiedad matemática que explica el resultado de la fase D.

    Si α es igual para todos los brazos de un experimento, entonces

        θ̃ = (1−α)·θ̂ + α·centro

    es una función monótona creciente de θ̂, así que **conserva el orden** y en
    particular conserva cuál es el máximo. Contraer corrige la ESTIMACIÓN —la
    mejora que se le reporta al negocio— pero no puede cambiar la ELECCIÓN.

    Es la demostración más cruda de que estimar mejor no es decidir mejor, y es
    el motivo de que el eje global/local no sea opcional: solo un método cuyo
    objetivo difiera entre brazos puede reordenar.
    """
    p = _panel([0.010, 0.013, 0.016, 0.012])
    # mismo n en todos los brazos y v agrupada ⇒ α idéntico
    prep = shrinkage.preparar(p)
    c = shrinkage.contraer(prep, tau2=5e-6)

    assert c.alpha.std() < 1e-12, "este caso construye α uniforme a propósito"
    assert int(np.argmax(c.theta_tilde.to_numpy())) == int(
        np.argmax(prep["theta_hat"].to_numpy())
    )
    # y conserva el orden completo, no solo el máximo
    assert list(np.argsort(c.theta_tilde.to_numpy())) == list(
        np.argsort(prep["theta_hat"].to_numpy())
    )


def test_con_alpha_desigual_si_puede_reordenar():
    """Si los brazos tienen tamaños muy distintos, α difiere y el orden cambia.

    Es la condición que el proyecto necesita para que una corrección pueda
    mejorar la decisión, y la que casi no se cumple en este archivo porque los
    brazos reciben impresiones parecidas por diseño.
    """
    d = _panel([0.0105, 0.020])
    d.loc[1, "impresiones"] = 200          # brazo chico y ruidoso
    d.loc[1, "clics"] = 4                  # tasa alta pero con poca evidencia
    d["theta_hat"] = d.clics / d.impresiones
    prep = shrinkage.preparar(d)
    c = shrinkage.contraer(prep, tau2=1e-7)
    assert c.alpha.std() > 1e-6
    # el brazo chico se contrae mucho más y puede perder el primer lugar
    assert c.alpha.iloc[1] > c.alpha.iloc[0]


def test_el_azar_no_sufre_la_maldicion_del_ganador():
    """Validación interna: si no se selecciona, no hay inflación.

    La inflación del proyecto es un efecto de SELECCIÓN. Elegir al azar debe
    dar inflación ~0; si diera algo grande, el estimando estaría mal medido.
    """
    rng = np.random.default_rng(0)
    n = 2000
    est = pd.concat([_panel(rng.normal(0.013, 0.002, 4).clip(0.001), exp=f"e{i}")
                     for i in range(300)], ignore_index=True)
    ev = est.copy()
    ev["clics"] = rng.binomial(n, est["theta_hat"].clip(1e-6, 1 - 1e-6))
    ev["theta_hat"] = ev.clics / ev.impresiones

    r_azar = decision.evaluar(est, ev, regla="azar", semilla=1)
    r_crudo = decision.evaluar(est, ev, regla="crudo")
    assert abs(r_azar.inflacion) < abs(r_crudo.inflacion)
    assert r_crudo.inflacion > 0


def test_donde_falla_reporta_las_tres_fracciones():
    est = pd.concat([_panel([0.010, 0.014], exp=f"e{i}") for i in range(50)],
                    ignore_index=True)
    ev = est.copy()
    a = decision.evaluar(est, ev, regla="crudo")
    b = decision.evaluar(est, ev, regla="azar", semilla=2)
    out = decision.donde_falla(a, b, "crudo", "azar")
    s = out["fraccion_peor"] + out["fraccion_mejor"] + out["fraccion_igual"]
    assert abs(s - 1.0) < 1e-9
