"""Assemble the ChimeraX renders made by render_apoferritin.py into one labelled figure.

Usage:
    uv run scripts/compose_maps.py RENDER_DIR      # RENDER_DIR/{C,D}_{cage,helix}.png -> figures/maps_apoferritin.png
    uv run scripts/compose_maps.py RENDER_DIR hiv  # RENDER_DIR/A_{top,side,bundle}.png -> figures/maps_hiv.png

The renders are raster images, so no vector copy is written.
"""

import sys
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

import style

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"

LABELS = {
    "C": "RELION 5 only: 2.635852 Å (relion_postprocess)",
    "D": "WarpTools, RELION 5 and M: 2.511812 Å (relion_postprocess, same mask)",
}


def autocrop(img, pad=12):
    rgb = img[..., :3]
    mask = (rgb < 0.97).any(axis=2)
    ys, xs = np.where(mask)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, img.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, img.shape[1])
    return img[y0:y1, x0:x1]


def params(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        k, v = line.split("\t", 1)
        out[k] = v
    return out


def main(render_dir):
    style.apply()
    r = Path(render_dir)
    p = {t: params(r / f"{t}_params.txt") for t in ("C", "D")}
    fig = plt.figure(figsize=(9.0, 12.4))
    gs = fig.add_gridspec(3, 2, height_ratios=[4.5, 3.6, 3.6], hspace=0.12, wspace=0.04)
    for i, t in enumerate(("C", "D")):
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(autocrop(mpimg.imread(r / f"{t}_cage.png")))
        ax.set_axis_off()
        ax.set_title(("A  " if t == "C" else "B  ") + LABELS[t].split(":")[0]
                     + f"\n{LABELS[t].split(': ', 1)[1].replace(', same mask', '')}, contour {p[t]['cage_level_sd']} SD",
                     fontsize=9.5)
    for j, t in enumerate(("C", "D")):
        ax = fig.add_subplot(gs[1 + j, :])
        ax.imshow(mpimg.imread(r / f"{t}_helix.png"))
        ax.set_axis_off()
        ax.set_title(("C  " if t == "C" else "D  ") + LABELS[t].split(":")[0]
                     + f": helix, chain A residues 126 to 159, mesh at {p[t]['mesh_level_sd']} SD within 2.2 Å of the model",
                     fontsize=9.5)
    fig.text(0.125, 0.07,
             "EMPIAR-10491 apoferritin, all 37 tilt series. Sharpened maps masked with the same FSC mask, unsmoothed.\n"
             "Cage viewed down a 4-fold axis and coloured by radius; disconnected blobs under 8 Å hidden.\n"
             "Model: PDB 7A6A fitted as a rigid body into each map. Contour levels in SD of each whole map.",
             fontsize=8, color=style.INK_2, va="top")
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "maps_apoferritin.png", dpi=170, bbox_inches="tight", metadata={"Software": None})
    print("figures/maps_apoferritin.png")


def main_hiv(render_dir):
    style.apply()
    r = Path(render_dir)
    p = params(r / "A_params.txt")
    fig = plt.figure(figsize=(9.0, 8.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[4.3, 2.6], hspace=0.12, wspace=0.04)
    titles = {"top": f"A  Lattice around one hexamer, seen from outside the particle",
              "side": "B  Side view, front half clipped at the 6-fold axis"}
    for i, view in enumerate(("top", "side")):
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(autocrop(mpimg.imread(r / f"A_{view}.png")))
        ax.set_axis_off()
        ax.set_title(titles[view], fontsize=9.5)
    ax = fig.add_subplot(gs[1, :])
    ax.imshow(autocrop(mpimg.imread(r / "A_bundle.png"), pad=30))
    ax.set_axis_off()
    ax.set_title(f"C  The CA-SP1 junction helix of one subunit (residues 354 to 371), mesh at {p['mesh_level_sd']} SD "
                 "within 2.4 Å of the model", fontsize=9.5)
    fig.text(0.125, 0.06,
             f"EMPIAR-10164, final map of row A (3.323077 Å), sharpened and unmasked, unsmoothed. Lattice views: map cropped "
             f"to a cylinder of radius 112 Å\nand to the CA-SP1 layer, contour {p['lattice_level_sd']} SD above the mean, "
             "pieces under 25 Å hidden. Central hexamer coloured by domain within 4 Å of PDB 5L93\n"
             "(fitted as a rigid body): CA N-terminal domain blue, CA C-terminal domain orange, SP1 green; the rest of the "
             "lattice grey.", fontsize=8, color=style.INK_2, va="top")
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "maps_hiv.png", dpi=170, bbox_inches="tight", metadata={"Software": None})
    print("figures/maps_hiv.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "hiv":
        main_hiv(sys.argv[1])
    else:
        main(sys.argv[1])
