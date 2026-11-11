"""Plot the FSC curves in data/fsc_<ROW>.csv.

Usage:
    uv run scripts/plot_fsc.py            # writes figures/fsc_<ROW>.{png,svg} and figures/fsc_apoferritin_relion_vs_m.{png,svg}

The x axis is linear in spatial frequency (1/Å); tick labels give the resolution in Å. The dotted
horizontal line is FSC = 0.143. The solid vertical line marks the resolution reported for this map;
the dashed vertical line, where present, marks the value the corresponding tutorial reports. The
tutorials do not publish their FSC curves, so no tutorial curve is drawn.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

import style

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"

ROWS = {
    "A": {
        "title": "EMPIAR-10164, HIV-1 CA-SP1 (RELION 5, tutorial workflow)",
        "program": "relion_postprocess",
        "reported": "3.32",  # replaced by the value in fsc_summary.csv when present
        "tutorial": (3.3, "RELION 5 tutorial, 3.3 Å"),
        "ticks": [20, 10, 6, 4.5, 3.5, 3, 2.7],
    },
    "B": {
        "title": "EMPIAR-10491, apoferritin (WarpTools, RELION 5 and M, tutorial subset)",
        "program": "M",
        "reported": "2.76",  # printed by M; the interpolated crossing of its corrected FSC
        "tutorial": (2.9, "WarpTools tutorial, 2.9 Å"),
        "ticks": [20, 10, 6, 4, 3, 2.5, 2, 1.7],
    },
    "C": {
        "title": "EMPIAR-10491, apoferritin (RELION 5, all 37 tilt series)",
        "program": "relion_postprocess",
        "ticks": [20, 10, 6, 4, 3, 2.5, 2, 1.7],
    },
    "D": {
        "title": "EMPIAR-10491, apoferritin (WarpTools, RELION 5 and M, all 37 tilt series)",
        "program": "relion_postprocess",
        "ticks": [20, 10, 6, 4, 3, 2.5, 2, 1.7],
    },
}

CURVES = [
    ("fsc_corrected", "corrected (reported)", style.BLUE, "-", 2.0),
    ("fsc_masked", "masked", style.ORANGE, (0, (5, 2)), 1.4),
    ("fsc_unmasked", "unmasked", style.AQUA, (0, (1.5, 1.5)), 1.4),
    ("fsc_phase_randomised_masked", "phase-randomised, masked", style.GREY, (0, (6, 2, 1.5, 2)), 1.2),
]


def read_csv(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    cols = {k: [float(r[k]) for r in rows] for k in rows[0]}
    return cols


def summary():
    path = DATA / "fsc_summary.csv"
    with open(path) as fh:
        return {r["row"]: r for r in csv.DictReader(fh)}


def resolution_axis(ax, ticks, fmax):
    ax.set_xlim(0, fmax)
    ax.set_xticks([1 / t for t in ticks])
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_xlabel("Resolution (Å), axis linear in spatial frequency (1/Å)")
    top = ax.secondary_xaxis("top")
    top.set_xlabel("Spatial frequency (1/Å)", color=style.INK_2)
    top.tick_params(colors=style.INK_2, labelsize=8)
    top.spines["top"].set_visible(False)


def common(ax):
    ax.set_ylim(-0.08, 1.04)
    ax.set_ylabel("Fourier shell correlation")
    ax.axhline(0.143, color=style.INK_2, lw=0.9, ls=(0, (1, 2)))
    ax.text(0.004, 0.143 + 0.02, "0.143", color=style.INK_2, fontsize=8)
    ax.axhline(0, color=style.INK_2, lw=0.6)


def plot_row(row, cfg, summ):
    path = DATA / f"fsc_{row}.csv"
    if not path.exists():
        print(f"{row}: {path.name} missing, skipped")
        return
    d = read_csv(path)
    f = d["spatial_frequency_per_A"]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    common(ax)
    for col, label, color, ls, lw in CURVES:
        ax.plot(f, d[col], color=color, ls=ls, lw=lw, label=label)

    reported = summ.get(row, {}).get("reported_resolution_A") or cfg.get("reported")
    reported = float(reported)
    ax.axvline(1 / reported, color=style.BLUE, lw=1.0)
    shown = summ.get(row, {}).get("reported_resolution_A") or cfg.get("reported")
    ax.annotate(f"{shown} Å",
                xy=(1 / reported, 0.93), xytext=(4, 0), textcoords="offset points",
                color=style.INK, fontsize=9)
    if "tutorial" in cfg:
        tval, tlabel = cfg["tutorial"]
        ax.axvline(1 / tval, color=style.INK_2, lw=1.0, ls=(0, (4, 3)))
        ax.annotate(tlabel, xy=(1 / tval, 0.80), xytext=(-4, 0), textcoords="offset points",
                    ha="right", color=style.INK_2, fontsize=9)

    resolution_axis(ax, cfg["ticks"], max(f))
    ax.set_title(cfg["title"])
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.17), ncol=2,
              title=f"FSC curves ({cfg['program']})", title_fontsize=9, alignment="left")
    style.save(fig, FIG / f"fsc_{row}")
    plt.close(fig)
    print(f"{row}: figures/fsc_{row}.png")


def plot_comparison(summ):
    c, d = read_csv(DATA / "fsc_C.csv"), read_csv(DATA / "fsc_D.csv")
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    common(ax)
    # Reported values are shown exactly as relion_postprocess wrote them.
    sc, sd = summ["C"]["reported_resolution_A"], summ["D"]["reported_resolution_A"]
    rc, rd = float(sc), float(sd)
    ax.plot(c["spatial_frequency_per_A"], c["fsc_corrected"], color=style.BLUE,
            label=f"RELION 5 only: {sc} Å")
    ax.plot(d["spatial_frequency_per_A"], d["fsc_corrected"], color=style.ORANGE, ls=(0, (5, 2)),
            label=f"WarpTools, RELION 5 and M: {sd} Å")
    for val, color in ((rc, style.BLUE), (rd, style.ORANGE)):
        ax.axvline(1 / val, color=color, lw=1.0)
    resolution_axis(ax, [20, 10, 6, 4, 3, 2.5, 2, 1.7], max(c["spatial_frequency_per_A"]))
    ax.set_title("EMPIAR-10491, all 37 tilt series: same mask, same post-processing")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.17), ncol=1,
              title="Corrected FSC (relion_postprocess)", title_fontsize=9, alignment="left")
    style.save(fig, FIG / "fsc_apoferritin_relion_vs_m")
    plt.close(fig)
    print("C vs D: figures/fsc_apoferritin_relion_vs_m.png")


def plot_programs_b(summ):
    """Row B: the same half maps, FSC by M and by relion_postprocess with two different masks."""
    m, r, rm = (read_csv(DATA / f"fsc_{k}.csv") for k in ("B", "Brelion", "BrelionMmask"))
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    common(ax)
    ax.plot(r["spatial_frequency_per_A"], r["fsc_corrected"], color=style.BLUE,
            label=f"relion_postprocess, mask of rows C and D: {summ['Brelion']['reported_resolution_A']} Å")
    ax.plot(m["spatial_frequency_per_A"], m["fsc_corrected"], color=style.ORANGE, ls=(0, (5, 2)),
            label="M, its own mask: 2.76 Å")
    ax.plot(rm["spatial_frequency_per_A"], rm["fsc_corrected"], color=style.AQUA, lw=1.4, ls=(0, (6, 2, 1.5, 2)),
            label=f"relion_postprocess, M's mask file: {summ['BrelionMmask']['reported_resolution_A']} Å")
    ax.plot(r["spatial_frequency_per_A"], r["fsc_unmasked"], color=style.GREY, lw=1.1, ls=(0, (1.5, 1.5)),
            label="unmasked, relion_postprocess (M's agrees to within 0.03)")
    resolution_axis(ax, [20, 10, 6, 4, 3, 2.5, 2, 1.7], max(r["spatial_frequency_per_A"]))
    ax.set_title("Row B: the same half maps, corrected FSC by program and mask")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.17), ncol=1, fontsize=8.5,
              title="Corrected FSC", title_fontsize=9, alignment="left")
    style.save(fig, FIG / "fsc_B_programs")
    plt.close(fig)
    print("B: figures/fsc_B_programs.png")


def main():
    style.apply()
    FIG.mkdir(exist_ok=True)
    summ = summary()
    for row, cfg in ROWS.items():
        plot_row(row, cfg, summ)
    if (DATA / "fsc_C.csv").exists() and (DATA / "fsc_D.csv").exists():
        plot_comparison(summ)
    if (DATA / "fsc_Brelion.csv").exists():
        plot_programs_b(summ)


if __name__ == "__main__":
    main()
