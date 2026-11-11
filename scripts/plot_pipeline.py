"""Draw the processing steps of each workflow as a line of job groups ("metro map").

Usage:
    uv run scripts/plot_pipeline.py      # writes figures/pipeline_{A,C,BD}.{png,svg}

For the two RELION projects (rows A and C) the job groups are checked against data/jobs_<ROW>.csv,
which lists every job of the RELION project with its type, status and parent jobs (taken from the
project's pipeline file): every job must belong to exactly one group, and every group on the main line
except the first must have a parent job in an earlier group (the only exception is the apoferritin
picks, made with pytom-match-pick outside RELION and imported). Jobs that did not lead to the final map
are drawn as branches below the line. The number above a group is the resolution after that stage
(from post-processing where the stage ends with it, otherwise from refinement) or a particle count;
the grey number above it is the tutorial's value for the same stage, where the tutorial states one.
WarpTools and M have no pipeline file, so their steps (rows B and D) are listed here directly.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.textpath import TextPath

import style

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"

# Category: (fill, text colour, legend label)
CATS = {
    "pre": ("#c9c8c1", style.INK, "Preprocessing"),
    "tomo": ("#8fd6bb", style.INK, "Alignment and tomograms"),
    "pick": ("#a9cbf4", style.INK, "Picking"),
    "refine": (style.BLUE, "#ffffff", "Refinement"),
    "class": ("#6250d6", "#ffffff", "Classification or selection"),
    "cycle": ("#f2b632", style.INK, "Refinement cycle (CTF refinement, polishing, refinement)"),
    "m": (style.ORANGE, style.INK, "M refinement"),
    "diag": ("#e8a1bd", style.INK, "Checks and side studies"),
    "model": ("#008300", "#ffffff", "Model building"),
}

FONT = FontProperties(family=["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], weight="bold")
PILL_FS, SMALL_FS = 8.6, 7.4
PILL_H, GAP, MAX_W, LINE_W = 0.30, 0.20, 9.4, 3.2
ABOVE, BELOW, BRANCH_STEP = 0.62, 0.42, 0.62   # space above a row (labels), below it (job numbers), per branch level


def text_w(s, size):
    return TextPath((0, 0), s, size=size, prop=FONT).get_extents().width / 72.0


def pill_w(label):
    return text_w(label, PILL_FS) + 0.26


def jobs_label(jobs):
    jobs = sorted(jobs)
    runs, start = [], jobs[0]
    for a, b in zip(jobs, jobs[1:] + [None]):
        if b != a + 1:
            runs.append(f"{start}" if start == a else f"{start}–{a}")
            if b is not None:
                start = b
    return "jobs " + ", ".join(runs) if len(jobs) > 1 else f"job {jobs[0]}"


def g(label, cat, jobs=None, res=None, ref=None, final=False, faded=False, external=False, brk=False,
      side="right"):
    """external: input came from outside the RELION project (no parent job to check).
    brk: start a new row with this group. side: for a branch, whether it hangs right or left of its parent."""
    return dict(label=label, cat=cat, jobs=list(jobs) if jobs else [], res=res, ref=ref, final=final,
                faded=faded, external=external, brk=brk, side=side)


R = range
HIV = dict(
    title="EMPIAR-10164, HIV-1 CA-SP1: RELION 5 tutorial workflow (row A)",
    main=[
        g("Import", "pre", [2]),
        g("Motion, CTF, tilts", "pre", R(3, 6)),
        g("Alignment, tomograms", "tomo", R(6, 8)),
        g("Denoising", "tomo", [9, 10]),
        g("Sphere picking", "pick", [11]),
        g("Bin 6", "refine", R(12, 15), res="16.5447 Å"),
        g("Bin 2", "refine", R(15, 19), res="5.48571 Å"),
        g("3D classification", "class", [19, 20], res="9,659 kept", ref="9,442"),
        g("Bin 1", "refine", R(21, 29), res="4.393221 Å", ref="4 Å", brk=True),
        g("Cycle 1", "cycle", R(29, 39), res="3.600000 Å", ref="3.6 Å"),
        g("Cycle 2", "cycle", R(39, 49), res="3.456000 Å"),
        g("Cycle 3", "cycle", R(49, 59), res="3.456000 Å"),
        g("Cycle 4", "cycle", R(59, 69), res="3.323077 Å"),
        g("Cycle 5", "cycle", R(69, 79), res="3.323077 Å", ref="3.3 Å"),
        g("Final map", "refine", R(81, 84), res="3.323077 Å", final=True),
    ],
    branches=[  # (index of the parent group on the main line, group)
        (0, g("Import, superseded", "pre", [1], faded=True)),
        (2, g("Denoising, stopped", "tomo", [8], faded=True)),
        (13, g("Per-subunit classification", "diag", [79, 80], side="left")),
        (14, g("ModelAngelo", "model", [84])),
    ],
)

APO = dict(
    title="EMPIAR-10491, apoferritin: RELION 5 on all 37 tilt series (row C)",
    main=[
        g("Import", "pre", [2]),
        g("Motion, CTF, tilts", "pre", R(3, 6)),
        g("Alignment, tomograms", "tomo", R(6, 8)),
        g("Template-matching picks", "pick", [8], external=True),  # pytom-match-pick, imported
        g("Bin 4", "refine", R(9, 12), res="6.88723 Å"),
        g("Bin 2", "refine", [12, 13, 14, 16, 17], res="3.500066 Å"),
        g("3D classification", "class", [15, 22], res="25,369 kept"),
        g("Bin 1", "refine", R(23, 27), res="3.234909 Å", brk=True),
        g("Cycle 1", "cycle", R(30, 42), res="2.885189 Å"),
        g("Cycle 2", "cycle", R(42, 52), res="2.737231 Å"),
        g("Cycle 3", "cycle", R(52, 62), res="2.668800 Å"),
        g("Cycle 4", "cycle", R(62, 72), res="2.635852 Å"),
        g("Cycle 5", "cycle", R(72, 82), res="2.635852 Å", final=True),
    ],
    branches=[
        (0, g("Import, failed", "pre", [1], faded=True)),
        (5, g("Defocus-hand check", "diag", R(18, 22))),
        (7, g("Timing test", "diag", R(27, 30))),
    ],
)


def warp_pre():
    return [g("Motion, CTF", "pre"), g("Tilt selection", "pre"), g("Alignment", "tomo"),
            g("Defocus hand, CTF", "tomo"), g("Tomograms", "tomo"), g("Template matching", "pick"),
            g("Export", "pick")]


M_TUT = ["6.4 Å", "3.6 Å", "3.1 Å", "3.0 Å", "3.0 Å", "–", "3.0 Å", "2.9 Å"]
M_B = ["4.36", "3.23", "2.97", "2.92", "2.83", "2.84", "2.79", "2.76"]
M_D = ["4.07", "3.73", "2.94", "2.82", "2.61", "2.59", "2.56", "2.47"]
WARP = dict(
    title="EMPIAR-10491, apoferritin: WarpTools, RELION 5 and M (rows B and D)",
    lines=[
        dict(subtitle="WarpTools preprocessing: the same steps for both rows, run separately on each data set",
             main=warp_pre(), cont_end=True),
        dict(subtitle="Row B: the tutorial's 5 tilt series at 0.7894 Å/px; resolutions from M's FSC",
             main=[g("Initial model", "refine"), g("Refine3D", "refine", res="8.25806 Å", ref="8.17 Å")]
             + [g(f"M{i}", "m", res=f"{r} Å", ref=t, final=(i == 7)) for i, (r, t) in enumerate(zip(M_B, M_TUT))],
             cont_start=True),
        dict(subtitle="Row D: all 37 tilt series at 0.834 Å/px; M's FSC, then relion_postprocess with the mask of row C",
             main=[g("Refine3D", "refine", res="6.88723 Å"), g("Remove duplicates", "class", res="25,838 kept")]
             + [g(f"M{i}", "m", res=f"{r} Å") for i, r in enumerate(M_D)]
             + [g("Post-processing", "refine", res="2.511812 Å", final=True)],
             cont_start=True),
    ],
)


def check(spec, csv_path):
    with open(csv_path) as fh:
        rows = {int(r["job"]): r for r in csv.DictReader(fh)}
    owner = {}
    groups = list(spec["main"]) + [b for _, b in spec["branches"]]
    for i, grp in enumerate(groups):
        for j in grp["jobs"]:
            assert j in rows, f"job {j} not in {csv_path.name}"
            assert j not in owner, f"job {j} in two groups"
            owner[j] = i
    missing = sorted(set(rows) - set(owner))
    assert not missing, f"jobs not in any group: {missing}"
    for i, grp in enumerate(spec["main"][1:], start=1):
        if grp["external"]:
            continue
        parents = {int(p) for j in grp["jobs"] for p in rows[j]["parent_jobs"].split(";") if p}
        assert any(owner.get(p, 99) < i for p in parents), f"group {grp['label']} has no parent in an earlier group"
    print(f"{csv_path.name}: {len(rows)} jobs, all in exactly one group")


def pill(ax, x, y, grp):
    fill, ink, _ = CATS[grp["cat"]]
    w = pill_w(grp["label"])
    lw, ec = (2.2, style.INK) if grp["final"] else (0, "none")
    a = 0.45 if grp["faded"] else 1.0
    ax.add_patch(FancyBboxPatch((x, y - PILL_H / 2), w, PILL_H, boxstyle=f"round,pad=0,rounding_size={PILL_H / 2}",
                                fc=fill, ec=ec, lw=lw, alpha=a, zorder=3))
    ax.text(x + w / 2, y - 0.005, grp["label"], ha="center", va="center", fontsize=PILL_FS,
            fontproperties=FONT, color=ink, alpha=0.65 if grp["faded"] else 1.0, zorder=4)
    if grp["res"]:
        ax.text(x + w / 2, y + PILL_H / 2 + 0.05, grp["res"], ha="center", va="bottom",
                fontsize=SMALL_FS + 0.4, color=style.INK, fontweight="bold")
    if grp["ref"]:
        ax.text(x + w / 2, y + PILL_H / 2 + 0.22, grp["ref"], ha="center", va="bottom",
                fontsize=SMALL_FS, color=style.GREY)
    if grp["jobs"]:
        ax.text(x + w / 2, y - PILL_H / 2 - 0.04, jobs_label(grp["jobs"]), ha="center", va="top",
                fontsize=SMALL_FS - 0.6, color=style.INK_2)
    return w


def bezier(ax, p0, p1, lw):
    (x0, y0), (x1, y1) = p0, p1
    verts = [(x0, y0), (x0, y1), (x0 + 0.25 * (x1 - x0), y1), (x1, y1)]
    ax.add_patch(PathPatch(MPath(verts, [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4]),
                           fc="none", ec=style.INK, lw=lw, zorder=1, capstyle="round"))


def rows_of(main):
    rows, cur, x = [], [], 0.0
    for i, grp in enumerate(main):
        w = pill_w(grp["label"])
        if cur and (grp["brk"] or x + w > MAX_W):
            rows.append(cur); cur, x = [], 0.0
        cur.append((i, x, w)); x += w + GAP
    rows.append(cur)
    return rows


def draw_line(ax, main, branches, ytop, cont_start=False, cont_end=False):
    """Draw one line starting with its row labels at ytop; return the y below everything drawn."""
    by_parent = {}
    for parent, grp in branches:
        by_parent.setdefault(parent, []).append(grp)
    y = ytop
    all_rows = rows_of(main)
    for r, row in enumerate(all_rows):
        grps = [main[i] for i, _, _ in row]
        y -= ABOVE if any(gr["ref"] for gr in grps) else (0.45 if any(gr["res"] for gr in grps) else 0.28)
        ax.plot([row[0][1] + 0.1, row[-1][1] + row[-1][2] - 0.1], [y, y], color=style.INK, lw=LINE_W,
                zorder=1, solid_capstyle="round")
        if r > 0 or cont_start:   # continuation from the previous row
            ax.plot([-0.22, row[0][1] + 0.1], [y, y], color=style.INK, lw=LINE_W, zorder=1)
            ax.add_patch(Circle((-0.22, y), 0.06, fc="#ffffff", ec=style.INK, lw=1.8, zorder=2))
        levels = []   # occupied x-intervals per branch level in this row
        for i, x, w in row:
            pill(ax, x, y, main[i])
            for grp in by_parent.get(i, []):
                bw = pill_w(grp["label"])
                bx = x + w - 0.05 if grp["side"] == "right" else x + 0.05 - bw
                lvl = 0
                while lvl < len(levels) and any(bx < e + 0.15 and bx + bw > s - 0.15 for s, e in levels[lvl]):
                    lvl += 1
                if lvl == len(levels):
                    levels.append([])
                levels[lvl].append((bx, bx + bw))
                byy = y - BELOW - 0.18 - lvl * BRANCH_STEP
                if grp["side"] == "right":
                    bezier(ax, (x + w - PILL_H / 2, y - PILL_H / 2), (bx + 0.1, byy), 1.3)
                else:
                    bezier(ax, (x + PILL_H / 2, y - PILL_H / 2), (bx + bw - 0.1, byy), 1.3)
                pill(ax, bx, byy, grp)
        last = row[-1]
        if r < len(all_rows) - 1 or cont_end:   # continues on the next row
            xe = last[1] + last[2]
            ax.plot([xe - 0.1, xe + 0.22], [y, y], color=style.INK, lw=LINE_W, zorder=1)
            ax.add_patch(Circle((xe + 0.22, y), 0.06, fc="#ffffff", ec=style.INK, lw=1.8, zorder=2))
        y -= BELOW + len(levels) * BRANCH_STEP
    return y


def legend(ax, cats, y):
    x = 0.0
    items = [(CATS[c][0], CATS[c][2], False) for c in cats] + [("#ffffff", "Final map", True)]
    for fill, label, ring in items:
        tw = text_w(label, SMALL_FS + 0.4) * 0.92
        if x + 0.4 + tw > MAX_W:
            x, y = 0.0, y - 0.28
        ax.add_patch(FancyBboxPatch((x, y - 0.08), 0.32, 0.16, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=fill, ec=style.INK if ring else "none", lw=1.8 if ring else 0))
        ax.text(x + 0.40, y, label, va="center", fontsize=SMALL_FS + 0.4, color=style.INK_2)
        x += 0.40 + tw + 0.35
    return y


def figure(name, title, lines, note):
    fig = plt.figure(figsize=(MAX_W + 0.7, 1))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.text(0, 0, title, fontsize=10.5, color=style.INK, va="top")
    y, cats = -0.32, []
    for subtitle, main, branches, opts in lines:
        if subtitle:
            ax.text(0, y - 0.05, subtitle, fontsize=SMALL_FS + 0.9, color=style.INK_2, va="top")
            y -= 0.25
        y = draw_line(ax, main, branches, y, **opts) - 0.12
        for grp in main + [b for _, b in branches]:
            if grp["cat"] not in cats:
                cats.append(grp["cat"])
    y = legend(ax, [c for c in CATS if c in cats], y - 0.12)
    ax.text(0, y - 0.22, note, fontsize=SMALL_FS, color=style.INK_2, va="top")
    top, bottom = 0.15, y - 0.45
    ax.set_xlim(-0.35, MAX_W + 0.35)
    ax.set_ylim(bottom, top)
    fig.set_size_inches(MAX_W + 0.7, top - bottom)
    style.save(fig, FIG / f"pipeline_{name}")
    plt.close(fig)
    print(f"figures/pipeline_{name}.png")


def main():
    style.apply()
    FIG.mkdir(exist_ok=True)
    check(HIV, DATA / "jobs_A.csv")
    check(APO, DATA / "jobs_C.csv")
    note = ("Black: this work.{grey} Job numbers are those of the RELION project (data/jobs_{row}.csv). "
            "Resolutions: relion_postprocess after each stage, except Refine3D (unmasked) for {bins}.")
    figure("A", HIV["title"], [(None, HIV["main"], HIV["branches"], {})],
           note.format(grey=" Grey: the tutorial's value at the same stage.", row="A", bins="bins 6 and 2"))
    figure("C", APO["title"], [(None, APO["main"], APO["branches"], {})], note.format(grey="", row="C", bins="bin 4"))
    figure("BD", WARP["title"], [(ln["subtitle"], ln["main"], [],
                                  {k: ln[k] for k in ("cont_start", "cont_end") if k in ln})
                                 for ln in WARP["lines"]],
           "Black: this work. Grey: the WarpTools tutorial's value at the same step (no value is given for M5).")


if __name__ == "__main__":
    main()
