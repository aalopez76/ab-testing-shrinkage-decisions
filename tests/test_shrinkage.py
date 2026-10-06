"""Shrinkage: the mask that keeps halves aligned, and the pooled variance.

Both exist to prevent a specific failure. The mask keeps two halves filterable
together; the pooled variance keeps `v` from hitting zero and from correlating
with the estimate it is supposed to weigh.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import shrinkage, thinning


def _panel(thetas, n=3000, exp="e1"):
    clicks = np.rint(np.asarray(thetas) * n).astype(int)
    d = pd.DataFrame(
        {
            "experiment_id": [exp] * len(thetas),
            "arm_id": [f"{exp}a{i}" for i in range(len(thetas))],
            "impressions": [n] * len(thetas),
            "clicks": clicks,
            "is_aa": [False] * len(thetas),
        }
    )
    d["theta_hat"] = d.clicks / d.impressions
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impressions
    return d


# --------------------------------------------------------------------------
# The pooled variance, and the two problems it solves
# --------------------------------------------------------------------------

def test_pooled_variance_avoids_zero_when_an_arm_recorded_no_clicks():
    """Per-arm variance is zero there, which breaks the 1/v weights.

    After splitting into halves this is common, not exotic: rates near 1.3% over
    roughly 1,500 impressions per half leave arms with no clicks at all.
    """
    p = _panel([0.012, 0.0])
    assert p["v"].iloc[1] == 0.0                 # the per-arm variance fails

    pooled = shrinkage.pooled_variance(p)
    assert np.isfinite(pooled.iloc[1]) and pooled.iloc[1] > 0


def test_pooled_variance_does_not_track_the_arms_own_estimate():
    """Per-arm v is a function of per-arm theta, so the two move together.

    That correlation is exactly the parameter-precision dependence the project
    diagnoses elsewhere; computing it from the experiment's pooled rate avoids
    the estimator inducing it.
    """
    p = _panel([0.004, 0.012, 0.020, 0.028])

    per_arm = p["v"].to_numpy()
    pooled = shrinkage.pooled_variance(p).to_numpy()

    assert np.corrcoef(per_arm, p["theta_hat"])[0, 1] > 0.99
    # pooled variance depends only on impressions, identical here
    assert pooled.std() == pytest.approx(0.0, abs=1e-20)


def test_experiments_with_no_clicks_at_all_are_left_as_nan():
    p = _panel([0.0, 0.0])
    assert shrinkage.pooled_variance(p).isna().all()


# --------------------------------------------------------------------------
# The mask: one filter for both halves
# --------------------------------------------------------------------------

def test_the_same_mask_keeps_two_halves_aligned():
    """Filtering each half on its own would compare different arms.

    The halves carry different click counts, so each would drop a different set
    of rows and nothing downstream would reveal the mismatch.
    """
    p = pd.concat([_panel([0.012, 0.013, 0.0005], exp=f"e{i}") for i in range(20)],
                  ignore_index=True)
    part = thinning.split(p, fraction=0.5, seed=1)

    mask = shrinkage.usable_mask(part.estimation)
    est = shrinkage.prepare(part.estimation, mask)
    ev = part.evaluation.loc[mask].reset_index(drop=True)

    assert len(est) == len(ev)
    assert list(est["arm_id"]) == list(ev["arm_id"])


def test_an_arm_without_clicks_survives_if_its_experiment_has_some():
    """The pooled variance is what makes this arm usable at all.

    Its own rate gives a variance of zero; the experiment's pooled rate gives a
    finite one. Dropping such arms would discard exactly the small, noisy cases
    the project is about.
    """
    p = _panel([0.012, 0.0])
    assert shrinkage.usable_mask(p).all()


def test_the_mask_drops_an_experiment_with_no_clicks_at_all():
    """There the pooled rate is zero too, and no variance can be formed."""
    p = _panel([0.0, 0.0])
    assert not shrinkage.usable_mask(p).any()


def test_the_mask_drops_a_single_arm_experiment():
    """One arm cannot be compared against anything."""
    p = pd.concat([_panel([0.012, 0.013], exp="e0"), _panel([0.011], exp="e1")],
                  ignore_index=True)
    mask = shrinkage.usable_mask(p)
    assert mask[:2].all()
    assert not mask[2]


def test_prepare_replaces_v_with_the_pooled_variance():
    p = _panel([0.010, 0.014])
    out = shrinkage.prepare(p)
    assert np.allclose(out["v"], shrinkage.pooled_variance(out))


# --------------------------------------------------------------------------
# The centres
# --------------------------------------------------------------------------

def test_weighted_and_simple_centres_agree_when_precision_is_equal():
    p = shrinkage.prepare(_panel([0.010, 0.013, 0.016]))
    weighted = shrinkage.shrink(p, tau2=5e-6, center="weighted")
    simple = shrinkage.shrink(p, tau2=5e-6, center="simple")
    assert np.allclose(weighted.theta_tilde, simple.theta_tilde)


def test_an_unknown_centre_is_rejected():
    p = shrinkage.prepare(_panel([0.010, 0.013]))
    with pytest.raises(ValueError, match="unknown center"):
        shrinkage.shrink(p, tau2=5e-6, center="nowhere")


def test_a_non_positive_variance_is_rejected():
    p = shrinkage.prepare(_panel([0.010, 0.013]))
    p.loc[0, "v"] = 0.0
    with pytest.raises(ValueError, match="non-positive"):
        shrinkage.shrink(p, tau2=5e-6)
