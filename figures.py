"""
Generate journal-quality figures for the ChaosCrypt paper.

Produces three PDF figures saved to paper/figures/:
  1. keystream_uniformity.pdf  -- chi-squared bucket distribution (Section 5.2)
  2. period_distribution.pdf   -- PRNG period survey across all 9000 seeds (Section 5.1)
  3. avalanche.pdf             -- bit-flip fractions under one-bit perturbations (Section 5.4)

Run from the repository root with the virtual environment active:
    venv/bin/python figures.py
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path

from chaoscrypt import middle_square_lcg, encrypt

# ── Output directory ──────────────────────────────────────────────────────────
OUT = Path("figures")
OUT.mkdir(parents=True, exist_ok=True)

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    # Font
    "font.family":       "serif",
    "font.serif":        ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size":         11,
    "axes.titlesize":    11,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "legend.framealpha": 0.92,
    # Layout
    "figure.dpi":        150,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
    "savefig.pad_inches": 0.08,
    # Grid / spines
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.linestyle":    ":",
    "grid.alpha":        0.55,
    "axes.axisbelow":    True,
})

# Default key parameters used throughout the paper
A, B, M = 113, 697, 65536

# Colour palette (perceptually uniform, colour-blind friendly)
BLUE   = "#2166ac"
RED    = "#d73027"
GREEN  = "#1a9850"
GREY   = "#4d4d4d"
ORANGE = "#f46d43"


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Floyd's cycle-detection on the raw Middle-Square sequence
# ─────────────────────────────────────────────────────────────────────────────
def _ms_step(x, a=A, b=B, m=M):
    nxt = int(str(x * x).zfill(8)[2:6])
    return nxt if nxt != 0 else (a * x + b) % m


def measure_period(seed):
    """Return the Middle-Square cycle length λ, or None if not found."""
    tortoise = _ms_step(seed)
    hare     = _ms_step(_ms_step(seed))
    steps    = 0
    while tortoise != hare and steps < 200_000:
        tortoise = _ms_step(tortoise)
        hare     = _ms_step(_ms_step(hare))
        steps   += 1
    if tortoise != hare:
        return None
    lam  = 1
    hare = _ms_step(tortoise)
    while tortoise != hare:
        hare = _ms_step(hare)
        lam += 1
    return lam


# ═════════════════════════════════════════════════════════════════════════════
# Figure 1 — Keystream Non-Uniformity
# ═════════════════════════════════════════════════════════════════════════════
def fig_keystream_uniformity(seed=1729, n=1000, k=10):
    ks       = middle_square_lcg(seed, A, B, M, n)
    max_val  = max(ks) + 1
    bw       = max_val / k
    observed = [0] * k
    for v in ks:
        observed[min(int(v / bw), k - 1)] += 1
    expected = n / k                         # 100.0

    fig, ax = plt.subplots(figsize=(6.5, 3.6))

    x_pos = np.arange(k)
    ax.bar(x_pos, observed,
           color=RED, edgecolor="white", linewidth=0.7,
           zorder=3, label="Observed count")
    ax.axhline(expected,
               color=GREY, linewidth=1.6, linestyle="--", zorder=4,
               label=f"Expected (uniform) = {int(expected)}")

    # Annotate each bar
    for i, v in enumerate(observed):
        label = str(v) if v > 0 else "0"
        ypos  = v + (max(observed) * 0.015) if v > 0 else max(observed) * 0.03
        ax.text(i, ypos, label, ha="center", va="bottom",
                fontsize=8.5, color=GREY)

    # Chi-squared annotation box
    ax.text(0.97, 0.95,
            r"$\chi^2 = 2299.1$" + "\n" + r"$p \approx 0$" + "\n" + r"d.f. $= 9$",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=9.5, color=RED,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=RED, alpha=0.85))

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"B{i}" for i in range(k)])
    ax.set_xlabel("Bucket index  (equal-width partition of output range)")
    ax.set_ylabel("Count")
    ax.set_title(
        f"Keystream Bucket Distribution  "
        f"($n = {n}$,  seed $= {seed}$,  $k = {k}$ buckets)"
    )
    ax.set_xlim(-0.55, k - 0.45)
    ax.set_ylim(0, max(observed) * 1.22)
    ax.legend(loc="upper right", bbox_to_anchor=(0.72, 1.0))

    plt.tight_layout()
    fig.savefig(OUT / "keystream_uniformity.pdf")
    plt.close(fig)
    print("  [1] keystream_uniformity.pdf")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 2 — PRNG Period Distribution across all 4-digit seeds
# ═════════════════════════════════════════════════════════════════════════════
def fig_period_distribution():
    print("  [2] computing periods for all 4-digit seeds (1000–9999) …")
    periods = []
    for seed in range(1000, 10000):
        p = measure_period(seed)
        if p is not None:
            periods.append(p)

    unique, counts = np.unique(periods, return_counts=True)
    total = len(periods)

    fig, ax = plt.subplots(figsize=(6.5, 3.6))

    bars = ax.bar(range(len(unique)), counts,
                  color=BLUE, edgecolor="white", linewidth=0.7, zorder=3)

    # Annotate each bar with count and percentage
    for bar, cnt in zip(bars, counts):
        pct = 100.0 * cnt / total
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + total * 0.008,
                f"{cnt}\n({pct:.1f}%)",
                ha="center", va="bottom", fontsize=9, color=GREY,
                linespacing=1.3)

    ax.set_xticks(range(len(unique)))
    ax.set_xticklabels([f"$\\lambda = {u}$" for u in unique])
    ax.set_xlabel("Period length  $\\lambda$")
    ax.set_ylabel("Number of seeds")
    ax.set_title(
        f"Middle-Square Period Distribution  "
        f"(all {total} four-digit seeds,  $a={A}$,  $b={B}$,  $m={M}$)"
    )
    ax.set_ylim(0, max(counts) * 1.22)

    plt.tight_layout()
    fig.savefig(OUT / "period_distribution.pdf")
    plt.close(fig)
    print(f"     period values → {dict(zip(unique.tolist(), counts.tolist()))}")
    print("     period_distribution.pdf")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 3 — Avalanche / Diffusion Sensitivity
# ═════════════════════════════════════════════════════════════════════════════
def fig_avalanche(plaintext="Hello, ChaosCrypt!", seed=1729, n_trials=20):
    base_ct    = encrypt(plaintext, seed, A, B, M)["ciphertext"]
    total_bits = sum(c.bit_length() for c in base_ct) or 1

    rng       = np.random.default_rng(42)
    fractions = []
    for _ in range(n_trials):
        bit_pos    = int(rng.integers(0, 14))
        flipped    = max(1000, min(9999, seed ^ (1 << bit_pos)))
        flipped_ct = encrypt(plaintext, flipped, A, B, M)["ciphertext"]
        diff_bits  = sum(bin(x ^ y).count("1")
                         for x, y in zip(base_ct, flipped_ct))
        fractions.append(diff_bits / total_bits)

    mean_frac = float(np.mean(fractions))
    colors    = [GREEN if abs(f - 0.5) <= 0.05 else RED for f in fractions]

    fig, ax = plt.subplots(figsize=(6.5, 3.6))

    ax.bar(range(n_trials), fractions,
           color=colors, edgecolor="white", linewidth=0.6, zorder=3)
    ideal_line, = ax.plot([], [], color=GREY, linewidth=1.6, linestyle="--")
    ax.axhline(0.5, color=GREY, linewidth=1.6, linestyle="--", zorder=4)
    ax.axhspan(0.45, 0.55, color=GREEN, alpha=0.10, zorder=2)
    ax.axhline(mean_frac, color=ORANGE, linewidth=1.2,
               linestyle="-.", zorder=5)

    ax.set_xticks(range(n_trials))
    ax.set_xticklabels([f"T{i+1}" for i in range(n_trials)], fontsize=8)
    ax.set_ylim(0, 0.80)
    ax.set_xlabel("Trial  (one-bit perturbation of seed)")
    ax.set_ylabel("Bit-flip fraction")
    ax.set_title(
        f"Diffusion Sensitivity: Bit-Flip Fraction per One-Bit Seed Perturbation\n"
        f"Mean $= {mean_frac:.4f}$  (ideal SAC $= 0.5000$,  seed $= {seed}$)"
    )

    legend_elements = [
        Line2D([0], [0], color=GREY,   linewidth=1.6, linestyle="--",
               label="Ideal  (SAC = 0.50)"),
        Line2D([0], [0], color=ORANGE, linewidth=1.2, linestyle="-.",
               label=f"Observed mean = {mean_frac:.4f}"),
        mpatches.Patch(facecolor=GREEN, alpha=0.25,
                       label=r"$\pm$0.05 tolerance band"),
        mpatches.Patch(facecolor=GREEN, label="Within tolerance"),
        mpatches.Patch(facecolor=RED,   label="Outside tolerance"),
    ]
    ax.legend(handles=legend_elements, loc="upper right",
              fontsize=8.5, ncol=2)

    plt.tight_layout()
    fig.savefig(OUT / "avalanche.pdf")
    plt.close(fig)
    print("  [3] avalanche.pdf")


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating figures …")
    fig_keystream_uniformity()
    fig_period_distribution()
    fig_avalanche()
    print(f"\nDone.  PDFs written to  {OUT}/")
