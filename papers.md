# References

The works reviewed during the development of this project, with their exact reference and what each one contributed. Works that **support a method decision** are listed separately from those consulted to frame the problem or ruled out with a stated reason.

---

## 1. The data

**Matias, J. N., Munger, K., Aubin Le Quéré, M. and Ebersole, C.** (2021). *The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media*. **Scientific Data** 8, 195.
DOI: [10.1038/s41597-021-00934-7](https://doi.org/10.1038/s41597-021-00934-7) · Data: [osf.io/jd64p](https://osf.io/jd64p/)

> The archive this project uses. It supplies the genuine randomisation, the A/A-like experiments and the exploratory/confirmatory split that allows the method to be frozen.

**Matias, J. N., Munger, K., Aubin Le Quéré, M. and Ebersole, C.** (2024). *Author Correction: The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media*. **Scientific Data** 11.
DOI: [10.1038/s41597-024-03600-w](https://doi.org/10.1038/s41597-024-03600-w)

> The correction documenting the Cloudflare caching failure. It identifies **25 June 2013 to 10 January 2014** as the likely affected period, about 7,004 tests or 22%, and advises against using them for causal inference. It also added a `problem` flag to the updated main archive; **the legacy exploratory and confirmatory split files this project reads predate that flag**, so the affected window was reconstructed here from scratch.

---

## 2. The origin of the method

**Stein, C.** (1956). *Inadmissibility of the usual estimator for the mean of a multivariate normal distribution*. In **Proceedings of the Third Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 197–206. University of California Press.

> The proof that the maximum-likelihood estimator is inadmissible in three or more dimensions. The result from which the entire family derives.

**James, W. and Stein, C.** (1961). *Estimation with quadratic loss*. In **Proceedings of the Fourth Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 361–379. University of California Press.

> The explicit estimator. Stein had announced inadmissibility in 1956 with a non-constructive proof; the closed form appears here.

**Robbins, H.** (1956). *An empirical Bayes approach to statistics*. In **Proceedings of the Third Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 157–163. University of California Press.

> The source of the name "empirical Bayes": estimating the prior from the data rather than postulating it.

**Efron, B. and Morris, C.** (1975). *Data analysis using Stein's estimator and its generalizations*. **Journal of the American Statistical Association** 70(350), 311–319.
DOI: [10.1080/01621459.1975.10479864](https://doi.org/10.1080/01621459.1975.10479864)

> The work that turned it into an applicable tool and carried it beyond mathematical statistics.

---

## 3. The estimators this project implements

**Cochran, W. G.** (1954). *The combination of estimates from different experiments*. **Biometrics** 10(1), 101–129.
DOI: [10.2307/3001666](https://doi.org/10.2307/3001666)

> The *Q* statistic this project uses to audit the noise model against A/A-like experiments. **Result: Q/df = 1.940 in the exploratory sample and 1.927 in the confirmatory sample; the binomial model underestimates noise by close to a factor of two.**

**DerSimonian, R. and Laird, N.** (1986). *Meta-analysis in clinical trials*. **Controlled Clinical Trials** 7(3), 177–188.
DOI: [10.1016/0197-2456(86)90046-2](https://doi.org/10.1016/0197-2456(86)90046-2)

> Closed-form moment estimator of between-study dispersion. Implemented in `src/wcab/shrinkage/dispersion.py`.

**Paule, R. C. and Mandel, J.** (1982). *Consensus values and weighting factors*. **Journal of Research of the National Bureau of Standards** 87(5), 377–385.
DOI: [10.6028/jres.087.022](https://doi.org/10.6028/jres.087.022)

> Iterative estimator of dispersion, by bisection on *Q*. This is the project's default.

**Neufeld, A., Dharamshi, A., Gao, L. L. and Witten, D.** (2024). *Data thinning for convolution-closed distributions*. **Journal of Machine Learning Research** 25(57), 1–35.
[jmlr.org/papers/v25/23-0446.html](https://jmlr.org/papers/v25/23-0446.html)

> **The component that makes the evaluation possible.** It allows a variant's counts to be split into **marginally independent** halves that sum to the original observation — hypergeometrically for the binomial, and exactly rather than approximately. Without it there is no way to measure out of sample without additional data.
>
> It also supplies the reason the split fraction is reported rather than assumed. The paper treats that fraction as a tuning parameter governing how much information goes to the task being performed as against the task of evaluating it, with a best value that depends on the model. `scripts/12_split_sensitivity.py` reports the published estimates against that choice.
>
> **Not to be confused with *data fission*** (Leiner, Duan, Tibshirani and Ramdas), which for the binomial does not yield independent parts.

**Mudd, R., Friedberg, R., Gorbachev, I., Nassif, H. and Zaidi, A.** (2025). *Breaking the Winner's Curse with Bayesian Hybrid Shrinkage*. Meta Platforms. Presented at the **Conference on Digital Experimentation @ MIT (CODE@MIT'25)**.
arXiv: [2511.06318](https://arxiv.org/abs/2511.06318)

> The BHS variant implemented in `src/wcab/shrinkage/bhs.py`, presented at CODE@MIT 2025. A later and more developed preprint appeared in March 2026 ([arXiv:2603.12867](https://arxiv.org/abs/2603.12867), *Breaking the Winner's Curse with Bayesian Hybrid Shrinkage*, with an expanded author list); this project implements the earlier version and was not revalidated against it. It adds **local** shrinkage factors per experiment through an inverse-gamma prior on the scale, which is equivalent to a Student-t prior.
>
> The paper names its own base case: with λᵢ = 1 for all i it reduces to what the authors call *"Bayesian Global Shrinkage"*, which is standard shrinkage.
>
> **It is a conference submission, not a documented production system.**

---

## 4. The decision framework

**Schultzberg, M. and Frånberg, M.** (2026). *Bayesian Inference Procedures for A/B Testing: An Overview*. Experimentation Platform team, Confidence, Spotify.
arXiv: [2608.12949](https://arxiv.org/abs/2608.12949) (13 August 2026)

> **The framework on which this project rests.** It organises Bayesian configurations into three tiers according to the strength of their error control, and establishes that empirical Bayes is the only route to the third.
>
> Two statements this project uses directly. From the conclusion: *"error rates, estimation accuracy, and regret are all different risks, and the appropriate method follows from the risks an experimentation program needs to control, not the other way around."*
>
> And from the abstract: *"winner-selected corpora, pooled programs, and heterogeneous metrics can each prevent calibration **regardless of corpus size**."* Their point concerns the historical corpus the prior is fitted on — one kept only because those experiments won — and more data from the same biased source does not fix it. **This project avoids that by fitting on the complete archive rather than a winners-only subset.** Its three-way thinning answers a different question: preventing the same observed counts from serving at once for winner selection, effect estimation and evaluation.

**Gu, J. and Koenker, R.** (2023). *Invidious Comparisons: Ranking and Selection as Compound Decisions*. **Econometrica** 91(1), 1–41.
DOI: [10.3982/ECTA19304](https://doi.org/10.3982/ECTA19304)

> That the loss function determines which ordering is optimal. Two results this project uses:
>
> - Under **homogeneous variance**, the posterior mean, the tail probability and the tail expectation **produce the same ordering**. Decision 1 lies close to this homogeneous-variance case, which is what explains its observed 99.8% ranking invariance rather than an exact one.
> - Under a capacity constraint, the posterior mean **favours units with smaller variance** while the tail probability **prefers those with larger variance**. This explains why the tail rule loses when the criterion is realised gain.

**Chen, J.** (2026). *Empirical Bayes When Estimation Precision Predicts Parameters*. **Econometrica** 94(2).
arXiv: [2212.14444](https://arxiv.org/abs/2212.14444)

> That the prior-independence assumption can fail, and that when it does **screening on shrunken estimates can be worse than on unshrunken ones**. This is the diagnostic that explains the project's principal finding.
>
> **Measured here:** the association between precision and outcome is −0.119 unadjusted, −0.087 within each week and −0.113 within each experiment type — computed within week and, separately, within type, not in a joint model, and between total impressions and the aggregate rate rather than against the parameter being shrunk.
>
> The reference implementation, `close`, is written in R; this project is in Python. **Declared operational cost, not an omission**: the diagnostic itself was run.

**Coey, D. and Hung, K.** (2022, rev. 2025). *Empirical Bayes Selection for Value Maximization*. Meta Platforms.
arXiv: [2210.03905](https://arxiv.org/abs/2210.03905) · Code: [github.com/facebookresearch/eb-selection](https://github.com/facebookresearch/eb-selection)

> **The closest antecedent: same question, same archive.** The authors prove regret bounds, and their thesis is that *"selection of the best units is fundamentally easier than estimation of their values"* — which is, in theory, the result this project measures on real data.
>
> Their setup imposes two conditions, described in their Appendix B: they filter out article-package pairs with fewer than 1,000 impressions or 100 clicks *"to ensure normality approximations are reasonable"*, which retains **6.9%** of the variants; and they reduce each experiment to an **arbitrary pair** (the arm with the most impressions against the second-most), so that **their setup does not contain the winner's curse**. They also evaluate against a simulated truth drawn from a fitted prior.

---

## 5. The problem in other fields

**Capen, E. C., Clapp, R. V. and Campbell, W. M.** (1971). *Competitive bidding in high-risk situations*. **Journal of Petroleum Technology** 23(6), 641–653.
DOI: [10.2118/2993-PA](https://doi.org/10.2118/2993-PA)

> The origin of the term. Three Atlantic Richfield engineers documented that winning bidders in offshore lease auctions obtained unexpectedly low returns "year after year".

**Forde, A., Hemani, G. and Ferguson, J.** (2023). *Review and further developments in statistical corrections for Winner's Curse in genetic association studies*. **PLoS Genetics** 19(9), e1010546.
DOI: [10.1371/journal.pgen.1010546](https://doi.org/10.1371/journal.pgen.1010546)

> **The distinction that justifies separating the problem into four decisions.** The authors separate **ranking bias**, which arises from ordering a million variants, from **selection bias**, which arises from applying a significance threshold — attributing the distinction to Dudbridge and Newcombe. These are two different mechanisms, and nothing guarantees that a single correction addresses both.
>
> This is the field that has worked the correction hardest; the authors also publish the R package `winnerscurse`.

**Gelman, A. and Carlin, J.** (2014). *Beyond power calculations: assessing Type S (sign) and Type M (magnitude) errors*. **Perspectives on Psychological Science** 9(6), 641–651.
DOI: [10.1177/1745691614551642](https://doi.org/10.1177/1745691614551642)

> The exaggeration ratio, which is what makes the severity of the problem **depend on the power of the experiment itself**. Their normal-design example gives an expected exaggeration factor of **1.12 at 80% power**, about 12%. The paper gives no figure for lower power, stating that "when power gets much below 0.5, the exaggeration ratio becomes high"; this repository quotes only what the paper itself reports.

---

## 6. Industry practice

**Deng, A.** (2015). *Objective Bayesian Two Sample Hypothesis Testing for Online Controlled Experiments*. In **Proceedings of the 24th International Conference on World Wide Web (WWW '15 Companion)**, pp. 923–928.
DOI: [10.1145/2740908.2742563](https://doi.org/10.1145/2740908.2742563)

> Priors estimated from the historical record of experiments at Bing. Deng reports the method being **applied successfully at Bing, with thousands of past experiments used to set the priors**, which is what the README states. It does not by itself establish a continuing production deployment, and this project does not claim one.

**Dimmery, D., Bakshy, E. and Sekhon, J.** (2019). *Shrinkage Estimators in Online Experiments*. In **Proceedings of the 25th ACM SIGKDD Conference (KDD '19)**.
arXiv: [1904.12918](https://arxiv.org/abs/1904.12918)

> Shrinkage in online experiments with many arms, over 17 internal Facebook experiments. The direct antecedent of Meta's later work.

**Abadie, A., Agarwal, A., Imbens, G., Jia, S., McQueen, J., Stepaniants, S. and Torres, S.** (2023, rev. 2026). *Estimating the Value of Evidence-Based Decision Making*.
arXiv: [2306.13681](https://arxiv.org/abs/2306.13681)

> Parametric and non-parametric empirical Bayes evaluating **decision quality** rather than estimation error alone. Their conclusion: *"commonly used decision rules based on statistical significance can leave substantial value unrealized and, in some cases, generate negative expected value."*

**Sudijono, T., Ejdemyr, S., Lal, A. and Tingley, M.** (2024). *Optimizing Returns from Experimentation Programs*. Netflix.
arXiv: [2412.05508](https://arxiv.org/abs/2412.05508)

> Optimisation at the **programme** level: which experiments to run and when to ship. **Ruled out by scope**, not by quality: it does not address what to select within a portfolio already in hand, which is this project's decision 2.

**Schultzberg, M. et al.** (2026). *Why Spotify Is Not Using Bayesian A/B Testing*. Spotify Engineering (September 2026).
[engineering.atspotify.com](https://engineering.atspotify.com/2026/9/why-spotify-is-not-using-bayesian-a-b-testing)

> The operational counterweight, and what makes this project's procedure necessary. The authors acknowledge that *"any Bayes with a zero-centered informative prior reduces the winner's-curse bias, and a well-calibrated empirical prior can often counter it completely"*, but warn that *"a misspecified prior made things precision and detection worse… actively worse than baseline group sequential testing."*
>
> **They do not contradict Meta on whether the method works**: they disagree on whether an organisation can keep the corpus calibrated.

**Kohavi, R. and Thomke, S.** (2017). *The Surprising Power of Online Experiments*. **Harvard Business Review**, September–October 2017.

> The correct source for the figure that only 10–20% of experiments produce positive results at Google and Bing. It does **not** come from the KDD 2015 keynote, whose 10–20% refers to traffic allocation.

---

## 7. Consulted and ruled out, with reasons

**Chen, Y. and Lei, L.** (2025). *Compound Estimation for Binomials*.
arXiv: [2512.25042](https://arxiv.org/abs/2512.25042) (31 December 2025)

> Treats the binomial directly rather than approximating it by a normal, which matters for small proportions and small samples.
>
> **Ruled out by diagnostic, not by assumption:** in these data n·p has a median of 40 and only 0.1% of variants falls below 10, so the Gaussian approximation is not the source of the problem. The check is in `scripts/06_where_it_fails.py`.

**Leiner, J., Duan, B., Tibshirani, R. and Ramdas, A.** *Data fission: splitting a single data point*. **JASA**.
arXiv: [2112.11079](https://arxiv.org/abs/2112.11079)

> Reviewed and **ruled out on correctness grounds**: for the binomial it does not produce independent parts, which is precisely what this project requires. *Data thinning* is used instead. The test documenting the difference is in `tests/test_thinning.py`.

---

## A note on the use of these references

Every figure this project attributes to published work was verified against the original text rather than against summaries or second-hand citations. In two cases that verification corrected claims already written into the project's documents: the true source of the 10–20% success figure, and the fact that Coey and Hung use **this same archive**, which required withdrawing a novelty claim that did not hold.

References predating 1990 are cited in their original edition; arXiv entries indicate the revised version where one exists.
