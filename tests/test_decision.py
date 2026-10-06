"""The decision rules, and the property that explains the phase D result."""

import numpy as np
import pandas as pd

from wcab import decision, shrinkage


def _panel(theta, n=3000, exp="e1"):
    clicks = np.rint(np.asarray(theta) * n).astype(int)
    d = pd.DataFrame(
        {
            "experiment_id": [exp] * len(theta),
            "arm_id": [f"{exp}a{i}" for i in range(len(theta))],
            "impressions": [n] * len(theta),
            "clicks": clicks,
            "is_aa": [False] * len(theta),
        }
    )
    d["theta_hat"] = d.clicks / d.impressions
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impressions
    return d


def test_uniform_shrinkage_CANNOT_change_the_maximum():
    """The mathematical property that explains the phase D result.

    If alpha is the same for every arm of an experiment, then

        theta_tilde = (1 - alpha) * theta_hat + alpha * centre

    is a monotonically increasing function of theta_hat, so it **preserves the
    ordering** and in particular preserves which arm is the maximum. Shrinkage
    corrects the ESTIMATE — the improvement reported to the business — but cannot
    change the SELECTION.

    This is the most direct demonstration that estimating better is not deciding
    better, and the reason the global/local axis is not optional: only a method
    whose target differs across arms can reorder them.
    """
    p = _panel([0.010, 0.013, 0.016, 0.012])
    # identical n across arms, plus pooled variance, implies identical alpha
    prep = shrinkage.prepare(p)
    c = shrinkage.shrink(prep, tau2=5e-6)

    assert c.alpha.std() < 1e-12, "this case deliberately constructs a uniform alpha"
    assert int(np.argmax(c.theta_tilde.to_numpy())) == int(
        np.argmax(prep["theta_hat"].to_numpy())
    )
    # and it preserves the full ordering, not merely the maximum
    assert list(np.argsort(c.theta_tilde.to_numpy())) == list(
        np.argsort(prep["theta_hat"].to_numpy())
    )


def test_unequal_alpha_can_reorder():
    """When arms differ greatly in size, alpha differs and the ordering changes.

    This is the condition the project requires for a correction to be able to
    improve the decision, and the one that is almost never met in this archive
    because arms receive similar numbers of impressions by design.
    """
    d = _panel([0.0105, 0.020])
    d.loc[1, "impressions"] = 200          # small, noisy arm
    d.loc[1, "clicks"] = 4                  # high rate on little evidence
    d["theta_hat"] = d.clicks / d.impressions
    prep = shrinkage.prepare(d)
    c = shrinkage.shrink(prep, tau2=1e-7)
    assert c.alpha.std() > 1e-6
    # the small arm shrinks much harder and can lose first place
    assert c.alpha.iloc[1] > c.alpha.iloc[0]


def test_random_selection_does_not_suffer_the_winners_curse():
    """Internal validation: without selection there is no inflation.

    The project's inflation is a SELECTION effect. Selecting at random should
    yield inflation near zero; a large value would mean the estimand is
    mismeasured.
    """
    rng = np.random.default_rng(0)
    n = 2000
    est = pd.concat([_panel(rng.normal(0.013, 0.002, 4).clip(0.001), exp=f"e{i}")
                     for i in range(300)], ignore_index=True)
    ev = est.copy()
    ev["clicks"] = rng.binomial(n, est["theta_hat"].clip(1e-6, 1 - 1e-6))
    ev["theta_hat"] = ev.clicks / ev.impressions

    r_random = decision.evaluate(est, ev, rule="random", seed=1)
    r_raw = decision.evaluate(est, ev, rule="raw")
    assert abs(r_random.inflation) < abs(r_raw.inflation)
    assert r_raw.inflation > 0


def test_where_it_fails_reports_three_fractions_summing_to_one():
    """The three fractions partition the experiments, and the profile branch runs.

    The evaluation half is drawn as a noisy realisation rather than copied, so
    the raw rule genuinely loses in some experiments. Without that, `fraction_worse`
    is zero, the branch profiling the worst cases never executes, and a defect in
    it would go unnoticed.
    """
    rng = np.random.default_rng(3)
    n = 1500
    est = pd.concat([_panel(rng.normal(0.013, 0.003, 3).clip(0.002), n=n, exp=f"e{i}")
                     for i in range(200)], ignore_index=True)
    ev = est.copy()
    ev["clicks"] = rng.binomial(n, est["theta_hat"].clip(1e-6, 1 - 1e-6))
    ev["theta_hat"] = ev.clicks / ev.impressions

    a = decision.evaluate(est, ev, rule="raw")
    b = decision.evaluate(est, ev, rule="random", seed=2)
    out = decision.where_it_fails(a, b, "raw", "random")

    s = out["fraction_worse"] + out["fraction_better"] + out["fraction_equal"]
    assert abs(s - 1.0) < 1e-9
    assert out["fraction_worse"] > 0, "the profile branch must be exercised"
    perfil = out["profile_of_the_worst"]
    assert set(perfil) == {"mean_arms", "mean_arms_rest", "mean_loss"}
    assert perfil["mean_loss"] > 0
