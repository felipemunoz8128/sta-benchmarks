"""Render an apoferritin map with ChimeraX: the whole cage down a 4-fold axis, and a mesh close-up of one
helix with a fitted atomic model (PDB 7A6A) shown as sticks.

Usage (ChimeraX 1.12; on macOS a window opens and closes by itself):
    ChimeraX --script "scripts/render_apoferritin.py MAP MODEL OUTDIR TAG CAGE_SD MESH_SD [small]"

MAP is a sharpened map masked with the FSC mask (box 256, 0.834 Å/px, O symmetry with a 4-fold along
z), shown without smoothing. MODEL is 7A6A already fitted into MAP. Contour levels follow one rule for
every map: CAGE_SD and MESH_SD standard deviations above the mean of the whole box. This is a fair
common rule here because the maps compared share the same box and the same mask, while their absolute
scales differ (M writes maps on a different intensity scale from RELION). The script writes
OUTDIR/TAG_cage.png, OUTDIR/TAG_helix.png and OUTDIR/TAG_params.txt (levels in sigma and absolute).
"""

import os
import sys
import traceback

import numpy as np
from chimerax.core.commands import run
from chimerax.geometry import Place

HELIX = "/A:126-159"   # a long helix of chain A (7A6A numbering) that lies on the cage surface


def look(session, direction, at, dist, up_hint=(0.0, 1.0, 0.0)):
    z = np.asarray(direction, float); z /= np.linalg.norm(z)
    hint = np.asarray(up_hint, float)
    if abs(z @ hint) > 0.9:
        hint = np.array([1.0, 0.0, 0.0])
    x = np.cross(hint, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    session.main_view.camera.position = Place(axes=[x, y, z], origin=np.asarray(at) + z * dist)


def main(argv):
    mp, model, out, tag = argv[:4]
    cage_sd, mesh_sd = float(argv[4]), float(argv[5])
    small = len(argv) > 6 and argv[6] == "small"
    os.makedirs(out, exist_ok=True)
    s = session  # noqa: F821  (defined by ChimeraX)
    v = run(s, f"open {mp}")[0]
    m = run(s, f"open {model}")[0]
    M = "#" + m.id_string
    size = "width 600 height 600 supersample 2" if small else "width 1400 height 1400 supersample 3"

    run(s, "windowsize 700 700")
    run(s, "set bgColor white")
    run(s, "lighting soft")
    run(s, f"hide {M} atoms; cartoon hide {M}")
    stats = v.full_matrix()
    mean, sd = float(stats.mean()), float(stats.std())
    cage_level, mesh_level = mean + cage_sd * sd, mean + mesh_sd * sd
    run(s, f"volume #1 level {cage_level} style surface color #c8c8c8")
    run(s, "wait 1")
    run(s, "surface dust #1 size 8")  # hide disconnected blobs smaller than 8 Å (cage view only)

    origin = np.array(v.data.origin)
    step = np.array(v.data.step)
    centre = origin + step * (np.array(v.data.size) - 1) / 2.0
    cs = ",".join(f"{c:.3f}" for c in centre)

    # Whole cage, coloured by radius, viewed down z (a 4-fold axis).
    run(s, "graphics silhouettes true width 1.5")
    run(s, f"color radial #1 center {cs} coordinateSystem #1 "
           "palette 38,#3b5b92:48,#6f9fd8:56,#d9d2bf:64,#e59a52:72,#b5452b")
    look(s, [0, 0, 1], centre, 420.0)
    run(s, f"save {out}/{tag}_cage.png {size}")

    # Helix close-up: mesh within 2.2 Å of the helix, viewed from outside the cage, side-on.
    run(s, "windowsize 1000 400")
    run(s, "wait 1")
    helix_size = "width 1000 height 400 supersample 2" if small else "width 2000 height 800 supersample 3"
    sel = m.residues[(m.residues.chain_ids == "A") & (m.residues.numbers >= 126) & (m.residues.numbers <= 159)]
    ca = sel.atoms[sel.atoms.names == "CA"].scene_coords
    cen = sel.atoms.scene_coords.mean(axis=0)
    x = ca[-1] - ca[0]; x /= np.linalg.norm(x)
    z = cen - centre; z -= x * (z @ x); z /= np.linalg.norm(z)
    y = np.cross(z, x)
    dist = 1.05 * np.linalg.norm(ca[-1] - ca[0]) / 2 / np.tan(np.radians(15))
    s.main_view.camera.position = Place(axes=[x, y, z], origin=cen + z * dist)
    spec = f"{M}{HELIX}"
    run(s, f"show {spec} atoms; style {spec} stick; color {spec} byelement; color {spec} & C #e8b04a")
    run(s, "graphics silhouettes false")
    run(s, f"volume #1 level {mesh_level} style mesh meshLighting false")
    run(s, "color #1 #3c6fb6")
    run(s, f"volume zone #1 nearAtoms {spec} range 2.2")
    run(s, f"clip near -12 far 12 position {','.join(f'{c:.2f}' for c in cen)}")
    run(s, f"save {out}/{tag}_helix.png {helix_size}")

    with open(f"{out}/{tag}_params.txt", "w") as fh:
        fh.write(f"map_mean\t{mean:.6g}\nmap_sd\t{sd:.6g}\n"
                 f"cage_level_sd\t{cage_sd:g}\ncage_level\t{cage_level:.6g}\n"
                 f"mesh_level_sd\t{mesh_sd:g}\nmesh_level\t{mesh_level:.6g}\n"
                 f"helix\tchain A residues 126-159 (7A6A)\nzone_A\t2.2\n")
    print(f"{tag}: cage {cage_level:.6g}, mesh {mesh_level:.6g}")


try:
    main(sys.argv[1:])
except Exception:
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    traceback.print_exc()
    os._exit(1)
run(session, "exit")  # noqa: F821
