"""Shared matplotlib style for every figure in this repository."""

import matplotlib as mpl

# Validated categorical slots (light surface), then neutral inks.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
GREY = "#8a8984"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3de"
SURFACE = "#ffffff"


def apply():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "regular",
        "axes.titlelocation": "left",
        "axes.labelsize": 10,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": INK_2,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "text.color": INK,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "svg.fonttype": "none",
        "svg.hashsalt": "sta-benchmarks",
    })


def save(fig, stem):
    """Save PNG (for the README) and SVG side by side, without timestamps in the metadata."""
    fig.savefig(f"{stem}.png", dpi=200, bbox_inches="tight", metadata={"Software": None})
    fig.savefig(f"{stem}.svg", bbox_inches="tight", metadata={"Date": None, "Creator": None})
