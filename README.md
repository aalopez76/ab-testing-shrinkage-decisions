# Project Background

[![CI](https://github.com/aalopez76/ab-testing-shrinkage-decisions/actions/workflows/ci.yml/badge.svg)](https://github.com/aalopez76/ab-testing-shrinkage-decisions/actions/workflows/ci.yml)

Organisations that decide through experimentation — digital commerce, media, marketplaces, healthcare, research — propose several versions of the same offering (advertisements, discounts, headlines, doses), measure which performs best, and deploy the winner. **However, the version selected for having performed best subsequently tends to deliver less than was expected.**

This is a well-documented problem known as **the winner's curse**. It arises because the selected offering owes its advantage to two things at once: partly to being genuinely the best performer, and partly to a component of luck — noise — that does not repeat on deployment. Its magnitude depends on the power of the experiment: at 80% power, the industry standard, the exaggeration is around 13%; at 20% power, it exceeds 130%.

The correction the industry proposes is **empirical Bayes shrinkage**: pulling the winner's result towards the group mean, in a proportion that grows with the imprecision of the measurement. Microsoft and Netflix use it in production, Meta published a variant in 2025 — *Bayesian Hybrid Shrinkage* — and **Spotify published its reasons for not adopting it**, warning that a poorly calibrated prior is actively worse than not correcting at all. Adopting it changes how every result is reported to the business.

**The question this project answers is whether it is worth adopting, and for what exactly.**

Three published lines of work converge on evaluating experiments by the decision they produce rather than by estimation error alone. Among the closest antecedents reviewed, I did not find a public evaluation comparing standard empirical-Bayes shrinkage by realised out-of-sample value under this decision criterion.

Findings and recommendations are organised around four decisions:

- **Which variant to deploy** — ranking candidates within a single experiment.
- **Which experiments to prioritise** — ranking under a limited budget.
- **Whether to ship at all** — comparing against an absolute threshold.
- **What figure to report to the business** — the estimate itself.

Code is in [`src/wcab/`](src/wcab/), the scripts that produce every figure cited here in [`scripts/`](scripts/), the raw results in [`reports/results/`](reports/results/), and the charts in [`reports/figures/`](reports/figures/). Exact references for every method decision are in [`papers.md`](papers.md).

*Processing is Python over flat files, so there are no SQL queries, entity-relationship diagram or interactive dashboard to show. Development was carried out with AI assistance (Claude Code); every figure cited was produced by the scripts in this repository, and every published claim was verified against its primary source.*

---

# Data Structure and Initial Checks

**Upworthy Research Archive** ([Matias et al., *Scientific Data* 8:195, 2021](https://www.nature.com/articles/s41597-021-00934-7)): real A/B tests of headlines and images from a US digital publisher. **What these data reproduce is not any particular company's figures but the procedure itself** — launch several versions, allocate users at random, measure a conversion rate and deploy the winner — which is the same loop run by a retailer testing incentives or a laboratory testing doses.

The archive is of interest because it satisfies three conditions: **genuine randomisation**, which prevents the selection effect from being confounded with assignment bias; **many variants per experiment**, since the curse lives in the maximum over candidates and with only two there is little to select from; and an **exploratory/confirmatory split included by the authors**, which allows the method to be frozen and confirmed without contamination.

| | Exploratory | Confirmatory |
|---|---|---|
| Experiments after exclusion | 3,380 | **15,787** |
| Variants | 16,629 | **77,446** |
| Impressions | 58.8 million | **273.5 million** |
| Clicks | 749,878 | **3,492,259** |
| Variants per experiment | 2 to 14 (median 5) | 2 to 20 (median 5) |
| Click-through rate | 1.28% | 1.28% |

## Check 1: randomisation

A window covering **6,956 of 22,743 experiments (30.6%)** is excluded. A caching misconfiguration on 25 June 2013 caused a single variant to be shown for months, affecting approximately 22% of the tests. **The public files carry no column identifying them**, so the window was established from scratch using a goodness-of-fit test on impressions per variant, which reproduces the failure month by month: 22.3% in June 2013, **86.4% in December**, 11.0% in January 2014, and between 0.0% and 0.9% thereafter.

The retained period runs at the anomaly rate that would be expected by chance.

## Check 2: noise model (twofold underestimation)

All shrinkage depends on the variance of each measurement, and experiments where no recorded treatment field varies between variants provide an independent benchmark. These are **inferred A/A-like experiments, identified from the treatment fields the archive publishes** — not deliberately designed A/A tests in which the true effect is known to be zero, a distinction that matters because the archive may not record every field that varied. Under the assumption that nothing else varied, observed dispersion should match the calculated one. It does not. Cochran's *Q* is **1.940** times its degrees of freedom in the exploratory sample and **1.927** in the confirmatory sample, and **replicates across both**.

What that figure establishes is **excess dispersion relative to the binomial benchmark in those experiments** — not a cleanly identified design effect, since the clustering and the unpublished-field explanations are not separable here.

![Initial checks](reports/figures/02_initial_checks.png)

## How out-of-sample evaluation is performed

Measuring how far the winner was inflated requires measuring it where it played no part in being chosen. Each variant's counts are split **hypergeometrically**, which for the family to which the binomial belongs yields marginally independent parts summing to the original observation. That result is **exact under the binomial observation model**.

It does not follow that the halves behave as independent real-world deployments. Check 2 found overdispersion relative to that very model, so if the excess comes from repeated visitors, sessions or unobserved heterogeneity, splitting aggregate counts does not reproduce the independence a fresh population would have. The partitions are therefore best read as **model-based held-out partitions**, and every out-of-sample guarantee below inherits that condition.

The split is into **three thirds** rather than two: one selects the variant, another estimates its advantage, the third evaluates. With two halves the between-experiment dispersion is estimated as zero, because the winner's advantage is an already-selected statistic and the method assumes an estimate that is not.

Uncertainty is reported as a **95% cluster-bootstrap percentile interval**, resampling whole experiments with replacement. An earlier version divided the spread across thinning seeds by the square root of their count, which measures how much the answer moves when the split moves — a quantity that shrinks towards zero as seeds are added — rather than uncertainty about the effect. Monte Carlo variability from the split is now reported separately from sampling uncertainty.

---

# Executive Summary

**The winner's curse is real and substantial:** the deployed variant promises 1.792% and delivers 1.553%, a **15.4% relative overstatement**. It is a selection effect rather than a measurement effect: choosing a variant at random yields an inflation a hundred times smaller.

**The correction does not fix what most people assume it fixes.** But the four decisions were not all specified at the same time, and that distinction is kept visible below rather than smoothed over.

## Stage 1 — pre-specified confirmatory analysis

The method was frozen at commit `69dfd977`, with its success criterion — **realised gain from the decision**, not reduction in estimation error — recorded in [`reports/results/FROZEN_METHOD.json`](reports/results/FROZEN_METHOD.json). The confirmatory sample was then run **once**, and replicated to the third decimal place on a sample 4.7 times larger that was never touched during development.

**Primary decision analyses**

| Decision | Does shrinkage help? | Figure |
|---|---|---|
| **1. Which variant to deploy** | **No, and it cannot** | 99.8% of decisions identical |
| **2. Which experiments to prioritise** | **No, and it costs** | −0.069 pp, 95% cluster-bootstrap percentile [−0.092, −0.027] |

**Pre-confirmatory secondary estimation analysis.** The improvement in estimation error was measured before the confirmatory sample was opened, but it is not the frozen criterion: **−24.0% mean squared error**, replicated across both samples.

## Stage 2 — post-confirmatory exploratory analyses

These were devised **after the confirmatory sample had already been unblinded** and evaluated on it. Nothing about them is wrong, but they are not confirmations: they **generate hypotheses requiring independent confirmation**.

| Analysis | Finding |
|---|---|
| **3. Whether to ship** | At a 0.8 pp bar the uncorrected policy delivers **negative** value, −0.0064 pp, while shrinkage delivers +0.0119 pp |
| **BHS** (Meta, 2025) | Better fit and lower held-out estimation error, −28.1% |
| **Regime boundary** | The closest published result holds inside the 6.9% of arms its filter retains, not outside |

![The four decisions](reports/figures/03_four_decisions.png)

What an experimentation lead should take away: **the correction serves to stop overstating results and to decide whether an improvement is worth deploying; it does not serve to choose better among candidates.** The distinction is not a nuance — it is a quarter of engineering effort well or poorly invested.

---

# Insights Deep Dive

## 1. Which variant to deploy: cannot be improved, and this is demonstrable

* **It is not that shrinkage fails to help; it is that it cannot.** Shrinkage is a weighted average between the observation and a common centre, so when the weight and the centre are equal across the variants of a single experiment it is a monotonically increasing function of the estimator and **preserves the ordering**.

* **And in these data the weight is effectively identical:** it varies by 0.009 across variants of the same experiment, because they receive balanced traffic by design — the ratio between the most and least exposed variant has a median of 1.040. 99.8% of decisions turn out identical.

* **This is the degenerate case the literature already describes.** Under homogeneous variance, the posterior mean, the tail probability and the tail expectation produce the same ordering. With balanced variants there was no selection problem to improve upon.

* **Practical consequence:** a team whose variants receive balanced traffic can rule out the entire project by measuring a ratio of impressions.

## 2. Which experiments to prioritise: it degrades, and the reason is identifiable

* **It genuinely reorders but selects worse.** At a 10% budget the correction changes 23.0% of the selection, and realised gain falls by **0.069 pp, 95% cluster-bootstrap percentile interval [−0.092, −0.027]**, which does not cross zero. The direction is stable across the three thinning seeds.

* **The mechanism is visible:** it discards experiments with a shrinkage weight of 0.689 and 4,000 impressions, and adds others with a weight of 0.318 and 7,151. That is, **it discards the imprecise and adds the precise**, which is exactly what theory says it does under a capacity constraint.

* **But those it discards had greater realised gain** (0.647 against 0.510 pp), because the prior-independence assumption fails: the correlation between impressions and outcome is −0.119 unadjusted, **−0.087 within each week** and **−0.113 within each experiment type**. It survives control for period and for type.

* **Practical consequence:** the sign of that correlation predicts whether the correction will help or harm before it is implemented.

![Where it fails](reports/figures/05_where_it_fails.png)

## 3. Whether to ship: here shrinkage does win, and the margin grows

* **The reason is an asymmetry the A/B testing literature does not usually separate.** Ranking is invariant to a monotone transformation, so shrinkage cannot change the argmax. **Comparison against an absolute threshold is not invariant**: shrinkage changes the value, and therefore changes whether it crosses the line.

* **The improvement grows with the stringency of the threshold**, winning across all 20 partitions from 0.4 points upwards:

| Threshold | Accuracy, uncorrected | Accuracy, shrunk | Improvement | Wins in |
|---|---|---|---|---|
| > 0.2 pp | 62.60% | 62.61% | +0.01 pp | 45% |
| > 0.4 pp | 68.69% | 70.42% | **+1.73 pp** | **100%** |
| > 0.6 pp | 76.72% | 79.62% | **+2.91 pp** | **100%** |
| > 0.8 pp | 83.83% | 86.68% | **+2.85 pp** | **100%** |

* **At a stringent threshold the uncorrected rule ships 14.2% and the truth is 14.2%:** it gets the rate right and the individuals wrong. The shrunk rule ships 3.2% and is more often correct, because most experiments genuinely do not clear a high bar and shrinkage says so.

* **This is the decision a team makes most frequently**, and it is where the correction pays.

![The ship decision](reports/figures/04_ship_decision.png)

## 4. The reported figure: improves, and the most recent variant improves further

* **The standard correction reduces estimation error by 24.0%**, replicated across both samples. This is what prevents promising the business improvements that never arrive.

* **BHS was also implemented**, the variant Meta published in 2025 with experiment-specific local shrinkage factors. This is a **Stage 2 exploratory extension**: better fit and lower held-out estimation error in this dataset, with the fitted parameter **a = 2.65** and a likelihood ratio of 961 against the standard version. **Numerical sensitivity and formal calibration of that likelihood-ratio comparison were not evaluated and remain outside scope**, so the ratio is reported as a fit statistic rather than as a test.

* **BHS estimates better: −28.1% held-out error.** But it does not change the ordering: the difference on decision 2 is +0.009 pp.

* **The reason had already been measured.** BHS corrects the **shape** of the prior through heavy tails; what fails in these data is **prior independence**. Making the prior more flexible does not make precision independent of the parameter: these are two distinct assumptions, and BHS addresses only one.

![BHS](reports/figures/06_bhs.png)

---

# Recommendations

For an experimentation team evaluating whether to adopt the correction:

* **The winning variant overstates by 15.4% in relative terms, and this is correctable.** **Adopt the correction for what is reported to the business and for deciding whether an improvement merits deployment**, since it reduces error by 24% and improves ship-decision accuracy by up to 2.9 points, winning across every partition evaluated.

* **The variants of an A/B test typically receive balanced traffic by design.** **Do not therefore justify the correction as an improvement to which variant is chosen**: measure the ratio of impressions between the most and least exposed variant, and if it is close to 1 there is an algebraic reason why it will not reorder.

* **The central assumption of the correction is that the true value does not depend on the precision with which it was measured.** **Before using it to prioritise across experiments, measure that correlation, because a negative sign means it will select worse.** Here it is −0.12 and survives control.

* **Variance is the input on which the entire method depends, and here it was underestimated twofold.** **Audit it against A/A experiments before anything else, and if the platform does not run them, start there**, because without an independent benchmark there is no way to establish whether it is correctly measured.

* **A winner's advantage is an already-selected statistic, and the method assumes an estimate that is not.** **If shrinkage is to be applied, split the counts three ways** — one selects, one estimates, one evaluates — because with two the dispersion is estimated as zero and the correction ceases to function.

---

# Assumptions and Caveats

* **The noise model does not describe these data, and the two candidate explanations are not distinguishable.** Cochran's *Q* is approximately 1.93 times its degrees of freedom across both samples. This may be because impressions are not independent, or because fields the archive does not publish were varying. Both are declared, and the measured factor is applied to the variance of each variant.

* **The design factor is applied only at the level at which it was measured.** The value of 1.94 corresponds to comparisons between variants within an experiment. For the between-experiment advantage, a factor estimated by an independent route — a covariance that does not use the variance at all — gives approximately 1.09. **A design factor does not transfer across levels**, and assuming that it does would reverse the conclusion.

* **The observed failure on prioritisation is consistent with precision−effect dependence, which is not the same as having identified it as the cause.** The correlation between impressions and outcome is negative and survives control for period and for experiment type, which is what the assumption forbids; but a negative correlation among observed quantities does not by itself establish the direction of the dependence in the underlying parameters.

* **The normal prior is misspecified by construction.** The winner's advantage is that of an already-selected variant, so its distribution is shifted (skewness +1.19) where the normal assumes zero. This is the reason BHS was implemented, and also the reason posterior-mean ranking does not attain its theoretical optimum.

* **The evaluation measures prediction on a held-out partition, not performance following an actual deployment.** The procedure is exact for the binomial, but what it tests is the ability to anticipate the held-out half of the same experiment. Deployment to a full user base introduces effects — saturation, seasonality, interference between users — that these data cannot reveal.

* **A single publisher, a single metric, 2013–2015, and aggregated data without person-level detail.** There are no segments or user characteristics. **The procedure and its thresholds transfer; the specific figures do not.** No number in this document should be used as an expectation for another platform.

* **Two methods were ruled out, each with its reason.** Direct binomial shrinkage, **by diagnostic**: n·p has a median of 40 and only 0.1% of variants falls below 10, so the Gaussian approximation is not the source of the problem here. And Chen's reference implementation, **by declared operational cost**: it is written in R and this project is in Python; its diagnostic was nonetheless run, and it is what explains the principal finding.
