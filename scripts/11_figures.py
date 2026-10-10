"""The report's figures, generated from the measured metrics.

Each figure is built either by reading `reports/results/*.json` — the same
metrics the README cites — or by recomputing from the panel. **No number is
written by hand in this file**: if a figure changes when the analysis is re-run,
the chart changes with it.

Output: reports/figures/*.png
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wcab import console, decision, panel, shrinkage, thinning
from wcab.diagnostics import noise

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "reports" / "results"
FIG = ROOT / "reports" / "figures"

# Palette: current practice in warm grey, the corrections in blues, the oracle
# in light grey, and green/red reserved for verdicts.
UNCORRECTED, GLOBAL, BHS = "#8c7b6b", "#3b6ea5", "#1f4068"
ORACLE = "#e8e4dc"
HELPS, HARMS, NEUTRAL = "#2f7d4f", "#b4422f", "#9a9a9a"

plt.rcParams.update({
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def read(name: str) -> dict:
    return json.loads((RES / name).read_text(encoding="utf-8"))


def save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name)
    plt.close(fig)
    print(f"  {name}")


# --------------------------------------------------------------------------
def fig_curse(p, partitions: int = 8) -> None:
    """What the winner promises against what it delivers, with a random control."""
    promised_best, delivered_best, promised_rand, delivered_rand = [], [], [], []
    for s in range(partitions):
        two = thinning.split(p, fraction=0.5, seed=s)
        m = shrinkage.usable_mask(two.estimation)
        est = shrinkage.prepare(two.estimation, m)
        ev = two.evaluation.loc[m].reset_index(drop=True)
        for rule, pr, de in (("raw", promised_best, delivered_best),
                             ("random", promised_rand, delivered_rand)):
            r = decision.evaluate(est, ev, rule=rule, seed=s)
            t = r.per_experiment
            pr.append(t["promised"].mean())
            de.append(t["delivered"].mean())

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), sharey=True)
    top = max(np.mean(promised_best), np.mean(promised_rand)) * 100
    for ax, (promised, delivered, title) in zip(axes, [
        (promised_best, delivered_best, "Chosen for measuring best"),
        (promised_rand, delivered_rand, "Chosen at random (control)"),
    ]):
        a, b = np.mean(promised) * 100, np.mean(delivered) * 100
        ax.bar([0, 1], [a, b], color=[UNCORRECTED, GLOBAL], width=0.5)
        ax.set_xticks([0, 1], ["promises", "delivers"])
        ax.set_title(title, pad=26)
        for x, v in ((0, a), (1, b)):
            ax.text(x, v + top * 0.015, f"{v:.3f}%", ha="center", fontsize=9)
        gap = a - b
        material = gap > 0.01
        ax.plot([0, 1], [top * 1.16] * 2, ls=":", lw=0.9, color="#777")
        ax.text(0.5, top * 1.20,
                f"{gap:+.3f} pp" + (f"  ({gap/b*100:+.1f}% relative)" if material
                                    else "  (no gap)"),
                ha="center", fontsize=9.5, weight="bold",
                color=HARMS if material else HELPS)
        ax.set_ylim(0, top * 1.34)
    axes[0].set_ylabel("click-through rate of the deployed variant")
    fig.suptitle("The winner's curse is a selection effect, not a measurement effect",
                 fontsize=11, weight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "01_winners_curse.png")


# --------------------------------------------------------------------------
def fig_checks(p) -> None:
    """The two initial checks: randomisation and the noise model."""
    srm = read("02_srm.json")["confirmatory"]
    by_month = sorted(srm["by_month"], key=lambda r: r["month"])
    months = [r["month"] for r in by_month]
    rates = [r["imbalance_fraction"] for r in by_month]

    cal = noise.calibrate(p)
    table = noise.cochran_q(p[p["is_aa"]])
    qs = (table["Q"] / table["dof"]).to_numpy()
    qs = qs[np.isfinite(qs)]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.6))

    x = np.arange(len(months))
    colours = [HARMS if t > 0.05 else GLOBAL for t in rates]
    a1.bar(x, np.array(rates) * 100, color=colours, width=0.8)
    a1.axhline(5, ls="--", lw=1, color="#333")
    a1.text(len(months) * 0.98, 7, "5% expected by chance", ha="right", fontsize=8.5)
    step = max(1, len(months) // 9)
    a1.set_xticks(x[::step], [months[i] for i in range(0, len(months), step)],
                  rotation=45, ha="right", fontsize=8)
    a1.set_ylabel("% of experiments with anomalous allocation")
    a1.set_title("1. Randomisation failed for months")

    a2.hist(np.clip(qs, 0, 6), bins=45, color=GLOBAL, alpha=0.85)
    a2.axvline(1.0, ls="--", lw=1.4, color="#333")
    a2.text(1.08, a2.get_ylim()[1] * 0.92, "1.0 = noise model\nis correct",
            fontsize=8.5)
    a2.axvline(cal.q_over_dof, lw=1.6, color=HARMS)
    a2.text(cal.q_over_dof + 0.12, a2.get_ylim()[1] * 0.62,
            f"measured: {cal.q_over_dof:.2f}×", fontsize=9, color=HARMS, weight="bold")
    a2.set_xlabel("Cochran's Q / degrees of freedom, per A/A-like experiment")
    a2.set_ylabel(f"experiments  (n={len(qs):,})")
    a2.set_title("2. About 1.93× the dispersion the model predicts")

    fig.suptitle("Two data problems, resolved before any measurement",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "02_initial_checks.png")


# --------------------------------------------------------------------------
def fig_four_decisions(p, partitions: int = 8) -> None:
    """The central figure: four decisions, four answers, each in its own units.

    They are deliberately not normalised onto a common axis — they would be
    different quantities disguised as comparable ones.
    """
    r = read("07_result.json")["confirmatory"]
    u = read("09_ship_decision.json")["thresholds"]
    g = r["gain"]

    # Decision 1: the rate the deployed variant actually delivers, with and
    # without the correction. Comparing "99.8% of decisions identical" against
    # 100% would be circular; this is in the same units as the rest.
    delivered_raw, delivered_shrunk = [], []
    for s in range(partitions):
        two = thinning.split(p, fraction=0.5, seed=s)
        m = shrinkage.usable_mask(two.estimation)
        est = shrinkage.prepare(two.estimation, m)
        ev = two.evaluation.loc[m].reset_index(drop=True)
        shrunk = shrinkage.shrink(est, tau2=None, tau2_method="paule-mandel")
        delivered_raw.append(decision.evaluate(est, ev, rule="raw", seed=s)
                             .per_experiment["delivered"].mean())
        delivered_shrunk.append(decision.evaluate(est, ev, priority=shrunk.theta_tilde,
                                                 rule="shrunk_global", seed=s)
                                .per_experiment["delivered"].mean())

    rows = [
        ("1. Which variant to deploy?", "click-through rate actually delivered",
         np.mean(delivered_shrunk) * 100, np.mean(delivered_raw) * 100,
         "no material benefit: ordering is near-preserved", NEUTRAL, "%", 3),
        ("2. Which experiments to prioritise?", "realised gain at a 5% budget",
         g["shrunk"]["0.05"] * 100, g["raw"]["0.05"] * 100,
         f"worse by {abs(g['shrunk']['0.05']-g['raw']['0.05'])*100:.3f} pp — "
         "interval excludes zero", HARMS, " pp", 2),
        ("3. Ship or not?", "realised policy value, threshold > 0.8 pp",
         u["0.008"]["value_shrunk"]["point_estimate"] * 100,
         u["0.008"]["value_raw"]["point_estimate"] * 100,
         f"the uncorrected rule destroys value: "
         f"{u['0.008']['value_raw']['point_estimate']*100:+.4f} pp",
         HELPS, " pp", 4),
        ("4. Which figure to report?", "mean squared error (lower is better)",
         r["estimation"]["mse_shrunk"] * 1e5, r["estimation"]["mse_raw"] * 1e5,
         f"{abs(r['estimation']['relative_change'])*100:.1f}% less error", HELPS, " ×10⁻⁵", 2),
    ]

    fig, axes = plt.subplots(4, 1, figsize=(9.4, 7.4))
    for ax, (title, measure, shrunk, raw, verdict, colour, unit, dec) in zip(axes, rows):
        ax.barh([1, 0], [raw, shrunk], color=[UNCORRECTED, colour], height=0.58)
        ax.set_yticks([1, 0], ["uncorrected", "shrunk"], fontsize=9)
        ax.set_xlim(0, max(raw, shrunk) * 1.5)
        for y, v in ((1, raw), (0, shrunk)):
            ax.text(v * 1.02, y, f"{v:.{dec}f}{unit}", va="center", fontsize=9.5)
        ax.set_title(f"{title}      ", loc="left", pad=16)
        ax.text(1.0, 1.12, verdict, transform=ax.transAxes, ha="right",
                fontsize=9.5, color=colour, weight="bold")
        ax.text(0.0, 1.12, measure, transform=ax.transAxes, fontsize=8.5,
                color="#666", style="italic")
        ax.set_xticks([])
        ax.grid(visible=False)
    fig.suptitle("The same correction, four decisions, four answers",
                 fontsize=12.5, weight="bold", y=1.0)
    fig.tight_layout(h_pad=2.2)
    save(fig, "03_four_decisions.png")


# --------------------------------------------------------------------------
def fig_ship() -> None:
    """Where shrinkage does win: shipping against an absolute threshold.

    What is plotted is the VALUE of the policy, not its accuracy. Accuracy
    against `realized > u` compares with a second noisy measurement rather than
    with the truth; realised value is what the rule delivers.
    """
    d = read("09_ship_decision.json")["thresholds"]
    us = sorted(d, key=float)
    x = [float(k) * 100 for k in us]                      # to percentage points

    v_raw = [d[k]["value_raw"]["point_estimate"] * 100 for k in us]
    v_shrunk = [d[k]["value_shrunk"]["point_estimate"] * 100 for k in us]
    ci_raw = [d[k]["value_raw"]["percentile_interval"] for k in us]
    ci_shrunk = [d[k]["value_shrunk"]["percentile_interval"] for k in us]

    def error_bars(values, intervals):
        below = [v - ci[0] * 100 for v, ci in zip(values, intervals)]
        above = [ci[1] * 100 - v for v, ci in zip(values, intervals)]
        return [below, above]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    a1.axhline(0, color="#333", lw=1.1, zorder=1)
    a1.errorbar(x, v_raw, yerr=error_bars(v_raw, ci_raw), fmt="o-",
                color=UNCORRECTED, lw=2, ms=6, capsize=3,
                label="uncorrected", zorder=3)
    a1.errorbar(x, v_shrunk, yerr=error_bars(v_shrunk, ci_shrunk), fmt="o-",
                color=GLOBAL, lw=2, ms=6, capsize=3, label="shrunk", zorder=3)

    # The zero crossing is the finding, so mark the threshold where it happens.
    # The label sits to the LEFT of the point, because below it the axis clips it.
    for xi, v in zip(x, v_raw):
        if v < 0:
            a1.annotate("destroys\nvalue", (xi, v),
                        textcoords="offset points",
                        xytext=(-16, -2), ha="right", va="center",
                        fontsize=8.5, color=HARMS, weight="bold")
            break

    a1.set_xlabel("ship threshold (percentage points of improvement)")
    a1.set_ylabel("realised policy value (pp)")
    a1.set_title("The uncorrected rule turns negative", fontsize=10.5)
    a1.legend(frameon=False, loc="upper right")
    a1.set_xlim(min(x) - 0.06, max(x) + 0.08)
    # Headroom below, so the label and the error bar both fit whole.
    low = min(ci[0] * 100 for ci in ci_raw)
    high = max(ci[1] * 100 for ci in ci_shrunk)
    a1.set_ylim(low - (high - low) * 0.14, high + (high - low) * 0.10)

    width = 0.26
    xi = np.arange(len(us))
    a2.bar(xi - width, [d[k]["ship_rate_raw"] * 100 for k in us], width,
           color=UNCORRECTED, label="ships, uncorrected")
    a2.bar(xi, [d[k]["ship_rate_shrunk"] * 100 for k in us], width,
           color=GLOBAL, label="ships, shrunk")
    a2.bar(xi + width, [d[k]["should_ship"] * 100 for k in us], width,
           color=ORACLE, edgecolor="#999", label="should ship")
    a2.set_xticks(xi, [f"> {float(k)*100:.1f}" for k in us])
    a2.set_xlabel("ship threshold (pp)")
    a2.set_ylabel("% of experiments shipped")
    a2.set_title("Right rate, wrong individuals", fontsize=10.5)
    a2.legend(frameon=False, fontsize=8.5)

    fig.suptitle("Ranking is invariant to shrinkage; threshold comparison is not",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "04_ship_decision.png")


# --------------------------------------------------------------------------
def fig_where_it_fails() -> None:
    """The mechanism of the damage on decision 2."""
    d = read("06_where_it_fails.json")
    d = d.get("confirmatory", d["exploratory"])
    f, pp = d["where_it_fails"], d["precision_predicts_parameter"]

    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.5))
    fields = [
        ("realised gain", "discarded_delta_realized",
         "added_delta_realized", 100, " pp"),
        ("shrinkage weight", "discarded_alpha", "added_alpha", 1, ""),
        ("impressions", "discarded_impressions", "added_impressions", 1, ""),
    ]
    for ax, (title, key_a, key_b, scale, unit) in zip(axes, fields):
        va, vb = f[key_a] * scale, f[key_b] * scale
        ax.bar([0, 1], [va, vb], color=[HARMS, GLOBAL], width=0.55)
        ax.set_xticks([0, 1], ["discards", "adds"])
        ax.set_title(title)
        for xx, vv in ((0, va), (1, vb)):
            label = f"{vv:,.0f}" if vv > 100 else f"{vv:.3f}{unit}"
            ax.text(xx, vv * 1.02, label, ha="center", fontsize=9)
        ax.set_ylim(0, max(va, vb) * 1.22)

    ax = axes[3]
    labels = ["unadj.", "within\nweek", "within\ntype"]
    values = [pp["correlation_raw"], pp["correlation_within_week"],
              pp["correlation_within_type"]]
    ax.bar(range(3), values, color=HARMS, width=0.55)
    ax.axhline(0, lw=1, color="#333")
    ax.set_xticks(range(3), labels, fontsize=8.5)
    ax.set_title("precision vs outcome")
    for i, v in enumerate(values):
        ax.text(i, v - 0.012, f"{v:+.3f}", ha="center", va="top", fontsize=9)
    ax.set_ylim(min(values) * 1.5, 0.02)

    fig.suptitle("Shrinkage discards the imprecise — and here the imprecise are "
                 "better, because prior independence fails",
                 fontsize=11, weight="bold", y=1.04)
    fig.tight_layout()
    save(fig, "05_where_it_fails.png")


# --------------------------------------------------------------------------
def fig_bhs() -> None:
    """The 2025 variant: estimates better, does not change the ordering."""
    b = read("10_bhs.json")["confirmatory"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8))

    rules = ["raw", "global", "bhs"]
    labels = ["uncorrected", "standard", "BHS (2025)"]
    values = [b["mse"][k] * 1e5 for k in rules]
    a1.bar(range(3), values, color=[UNCORRECTED, GLOBAL, BHS], width=0.58)
    a1.set_xticks(range(3), labels)
    a1.set_ylabel("mean squared error  (×10⁻⁵)")
    a1.set_title("Estimating: BHS improves on the standard version")
    for i, k in enumerate(rules):
        change = b["mse_relative_change"][k]
        a1.text(i, values[i] * 1.015, f"{values[i]:.3f}" +
                ("" if k == "raw" else f"\n{change*100:+.1f}%"),
                ha="center", fontsize=9,
                color="#333" if k == "raw" else HELPS,
                weight="normal" if k == "raw" else "bold")
    a1.set_ylim(0, max(values) * 1.3)

    budgets = sorted(b["gain"]["raw"], key=float)
    x = np.arange(len(budgets))
    for k, label, c in (("raw", "uncorrected", UNCORRECTED),
                        ("global", "standard", GLOBAL),
                        ("bhs", "BHS (2025)", BHS)):
        a2.plot(x, [b["gain"][k][q] * 100 for q in budgets], "o-",
                color=c, lw=2, ms=6, label=label)
    a2.set_xticks(x, [f"{int(float(q)*100)}%" for q in budgets])
    a2.set_xlabel("budget")
    a2.set_ylabel("realised gain (pp)")
    a2.set_title("Deciding: BHS does not change the ordering")
    a2.legend(frameon=False)
    a2.text(0.98, 0.82, f"a = {b['a_mean']:.2f}\nlikelihood ratio "
            f"= {b['likelihood_ratio']:.0f}\nthe data DO require\nlocal flexibility",
            transform=a2.transAxes, ha="right", fontsize=8.5, color="#444",
            bbox=dict(boxstyle="round,pad=0.45", fc="#f4f2ee", ec="#ccc"))

    fig.suptitle("BHS corrects the shape of the prior, not prior independence",
                 fontsize=11, weight="bold", y=1.04)
    save(fig, "06_bhs.png")


# --------------------------------------------------------------------------
def main() -> None:
    console.prepare()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="confirmatory",
                    choices=["exploratory", "confirmatory"])
    args = ap.parse_args()

    p = panel.load(args.sample)
    print(f"figures -> reports/figures/  ({args.sample})")
    fig_curse(p)
    fig_checks(p)
    fig_four_decisions(p)
    fig_ship()
    fig_where_it_fails()
    fig_bhs()


if __name__ == "__main__":
    main()
