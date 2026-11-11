"""Plot run times from data/runtime_<ROW>.csv.

Usage:
    uv run scripts/plot_runtime.py     # figures/runtime_overview.{png,svg} and figures/runtime_<ROW>.{png,svg}

Run time is measured inside each job, so queue time is excluded. GPU hours are allocated GPUs times run
time (NVIDIA L40S). Steps that took seconds and were not timed, and interactive steps (tilt exclusion,
picking spheres, selecting classes), have no bar. Colours follow the stages of the processing diagrams.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

import style
from plot_pipeline import CATS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"

STAGE_FILL = {label: fill for fill, _, label in CATS.values()}
STAGES = [CATS[k][2] for k in ("pre", "tomo", "pick", "refine", "class", "cycle", "m")]
ROWS = {
    "A": "A  EMPIAR-10164, RELION 5 (5 tilt series)",
    "B": "B  EMPIAR-10491, WarpTools, RELION 5 and M (5 tilt series)",
    "C": "C  EMPIAR-10491, RELION 5 (37 tilt series)",
    "D": "D  EMPIAR-10491, WarpTools, RELION 5 and M (37 tilt series)",
}


def read(row):
    with open(DATA / f"runtime_{row}.csv") as fh:
        out = []
        for r in csv.DictReader(fh):
            r["seconds"] = int(r["seconds"]) if r["seconds"] else None
            r["gpu_seconds"] = int(r["gpu_seconds"]) if r["gpu_seconds"] else 0
            out.append(r)
    return out


def fmt(s):
    if s is None:
        return ""
    if s < 60:
        return f"{s} s"
    if s < 3600:
        return f"{s // 60} min"
    m = round(s / 60)
    return f"{m // 60} h {m % 60:02d} min"


def totals(steps):
    return sum(s["seconds"] or 0 for s in steps), sum(s["gpu_seconds"] for s in steps)


def overview():
    fig, ax = plt.subplots(figsize=(9.6, 3.3))
    ax.grid(axis="y", visible=False)
    rows = list(ROWS)
    ymax = len(rows) - 1
    xmax = 0
    for i, row in enumerate(rows):
        steps = read(row)
        y = ymax - i
        left = 0.0
        for stage in STAGES:
            h = sum(s["seconds"] or 0 for s in steps if s["stage"] == stage) / 3600
            if h > 0:
                ax.barh(y, h, left=left, height=0.58, color=STAGE_FILL[stage], edgecolor="#ffffff", linewidth=1.2)
                left += h
        tot, gpu = totals(steps)
        xmax = max(xmax, left)
        ax.text(left + 1.0, y, f"{tot / 3600:.1f} h, {gpu / 3600:.1f} GPU h", va="center", fontsize=9,
                color=style.INK)
    ax.set_yticks(range(ymax, -1, -1))
    ax.set_yticklabels([ROWS[r] for r in rows], fontsize=9)
    ax.set_xlim(0, xmax * 1.22)
    ax.set_xlabel("Run time (hours, queue time excluded)")
    ax.set_title("Run time by stage, from import to final map", pad=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=STAGE_FILL[s]) for s in STAGES]
    labels = [s.replace(" (CTF refinement, polishing, refinement)", "") for s in STAGES]
    ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.0, -0.22), ncol=4, fontsize=8.5,
              handlelength=1.2, columnspacing=1.4)
    style.save(fig, FIG / "runtime_overview")
    plt.close(fig)
    print("figures/runtime_overview.png")


def per_row(row):
    steps = read(row)
    n = len(steps)
    fig, ax = plt.subplots(figsize=(8.4, 0.27 * n + 1.5))
    ax.grid(axis="y", visible=False)
    y = list(range(n))[::-1]
    smax = max(s["seconds"] or 0 for s in steps)
    unit, div = ("hours", 3600) if smax > 3 * 3600 else ("minutes", 60)
    for yi, s in zip(y, steps):
        colour = STAGE_FILL.get(s["stage"], style.GREY)
        if s["seconds"] is None:
            ax.text(0, yi, "  " + (s["note"] or "not timed"), va="center", fontsize=7.5, color=style.INK_2,
                    style="italic")
            continue
        v = s["seconds"] / div
        ax.barh(yi, max(v, smax / div * 0.004), height=0.62, color=colour)
        g = int(s["gpus"])
        if g and not s["gpu_seconds"]:
            gl = f"up to {g} GPUs at once (not in GPU hours)"
        elif g == 0:
            gl = "CPU only"
        elif s["gpu_seconds"] and s["gpu_seconds"] < s["seconds"] * g:
            gl = f"up to {g} GPU{'s' if g > 1 else ''}"
        else:
            gl = f"{g} GPU{'s' if g > 1 else ''}"
        label = f"{fmt(s['seconds'])}, {gl}"
        if s["note"] and "interactive" in s["note"]:
            label += " (interactive part not timed)"
        ax.text(v + smax / div * 0.01, yi, label, va="center", fontsize=7.5, color=style.INK_2)
    ax.set_yticks(y)
    ax.set_yticklabels([s["step"] for s in steps], fontsize=8)
    ax.set_xlim(0, smax / div * 1.42)
    ax.set_xlabel(f"Run time ({unit}, queue time excluded)")
    tot, gpu = totals(steps)
    ax.set_title(ROWS[row][3:] + ": run time per step", pad=20, fontsize=10.5)
    ax.text(0, 1.012, f"Total {fmt(tot)} of run time, {gpu / 3600:.1f} GPU hours (NVIDIA L40S)",
            transform=ax.transAxes, fontsize=9, color=style.INK_2, va="bottom")
    present = [st for st in STAGES if any(s["stage"] == st for s in steps)]
    handles = [plt.Rectangle((0, 0), 1, 1, color=STAGE_FILL[st]) for st in present]
    ax.legend(handles, [st.replace(" (CTF refinement, polishing, refinement)", "") for st in present],
              loc="upper left", bbox_to_anchor=(0.0, -0.10 - 2.2 / (0.27 * n + 1.5) * 0.25), ncol=4, fontsize=8,
              handlelength=1.2, columnspacing=1.2)
    style.save(fig, FIG / f"runtime_{row}")
    plt.close(fig)
    print(f"{row}: figures/runtime_{row}.png ({fmt(tot)}, {gpu / 3600:.1f} GPU h)")


def main():
    style.apply()
    FIG.mkdir(exist_ok=True)
    overview()
    for row in ROWS:
        per_row(row)


if __name__ == "__main__":
    main()
