"""Render the HIV-1 CA-SP1 map with ChimeraX: the lattice around one hexamer seen from outside the
virus-like particle, a cut-away side view, and a mesh close-up of one helix of the CA-SP1 six-helix bundle with a
fitted atomic model (PDB 5L93) shown as sticks.

Usage (ChimeraX 1.12; on macOS a window opens and closes by itself):
    ChimeraX --script "scripts/render_hiv.py MAP MODEL OUTDIR TAG LATTICE_SD MESH_SD [small]"

MAP is the sharpened, unmasked map from relion_postprocess (box 192, 1.35 Å/px, C6 axis along z through
the box centre, +z pointing out of the virus-like particle). MODEL is chain A of PDB 5L93 fitted into the
same frame; the script makes the other five subunits of the central hexamer by C6 symmetry. For the
lattice views the map is set to zero outside a cylinder of radius 112 Å and outside the CA-SP1 layer
(z from -52 to +58 Å about the centre). Contour levels are LATTICE_SD and MESH_SD standard deviations
above the mean of the whole map. Disconnected surface pieces under 25 Å are hidden in the lattice views.
The central hexamer is coloured by domain (CA N-terminal domain, CA C-terminal domain, SP1) where the
surface lies within 4 Å of the model; the rest of the lattice is grey.

Writes OUTDIR/TAG_top.png, OUTDIR/TAG_side.png, OUTDIR/TAG_bundle.png and OUTDIR/TAG_params.txt.
"""

import os
import sys
import traceback

import numpy as np
from chimerax.core.commands import run
from chimerax.geometry import Place
from chimerax.map import volume_from_grid_data
from chimerax.map_data import ArrayGridData

NTD, CTD, SP1, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#cfcfcf"
# Gag numbering, as in PDB 5L93
NTD_RES, CTD_RES, SP1_RES = "148-277", "278-363", "364-371"
BUNDLE = "354-371"


def camera(session, direction, at, dist, up):
    z = np.asarray(direction, float); z /= np.linalg.norm(z)
    up = np.asarray(up, float)
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    session.main_view.camera.position = Place(axes=[x, y, z], origin=np.asarray(at) + z * dist)


def main(argv):
    mp, model, out, tag = argv[:4]
    lattice_sd, mesh_sd = float(argv[4]), float(argv[5])
    small = len(argv) > 6 and argv[6] == "small"
    os.makedirs(out, exist_ok=True)
    s = session  # noqa: F821  (defined by ChimeraX)
    size = "width 700 height 700 supersample 2" if small else "width 1400 height 1400 supersample 3"

    run(s, "windowsize 700 700")
    run(s, "set bgColor white")
    run(s, "lighting soft")
    run(s, "graphics silhouettes true width 1.5")

    v = run(s, f"open {mp}")[0]
    d = v.data
    a = v.full_matrix()
    mean, sd = float(a.mean()), float(a.std())
    lattice_level, mesh_level = mean + lattice_sd * sd, mean + mesh_sd * sd
    n = np.array(d.size)
    step = np.array(d.step)
    centre = np.array(d.origin) + (n - 1) / 2.0 * step
    cs = ",".join(f"{c:.3f}" for c in centre)

    # Lattice crop: cylinder r <= 112 Å, CA-SP1 layer -52 <= z <= 58 Å (array order is z, y, x).
    zz, yy, xx = np.mgrid[0:n[2], 0:n[1], 0:n[0]].astype(np.float32)
    X = xx * step[0] + d.origin[0] - centre[0]
    Y = yy * step[1] + d.origin[1] - centre[1]
    Z = zz * step[2] + d.origin[2] - centre[2]
    keep = (np.hypot(X, Y) <= 112.0) & (Z >= -52.0) & (Z <= 58.0)
    lat = volume_from_grid_data(ArrayGridData((a * keep).astype(np.float32), origin=d.origin, step=d.step,
                                              name="lattice"), s)
    L = "#" + lat.id_string
    v.display = False
    run(s, f"volume {L} level {lattice_level} style surface step 1 color {GREY}")
    run(s, "wait 1")
    run(s, f"surface dust {L} size 25")

    # Central hexamer: chain A of the fitted 5L93 and five C6 copies.
    m = run(s, f"open {model}")[0]
    others = sorted(set(m.residues.chain_ids) - {"A"})
    if others:
        run(s, f"delete #{m.id_string}/{','.join(others)}")
    before = {x.id_string for x in s.models}
    run(s, f"sym #{m.id_string} C6 center {cs} axis 0,0,1 coordinateSystem #{v.id_string} copies true")
    hexm = [x for x in s.models if x.id_string not in before and "." not in x.id_string][0]
    run(s, f"close #{m.id_string}")
    H = "#" + hexm.id_string
    run(s, f"hide {H} atoms; cartoon hide {H}")
    run(s, f"color {H}:{NTD_RES} {NTD}; color {H}:{CTD_RES} {CTD}; color {H}:{SP1_RES} {SP1}")
    run(s, f"color zone {L} near {H} distance 4 farColor {GREY}")

    # View 1: from outside the virus-like particle, down the C6 axis.
    camera(s, [0, 0, 1], centre, 470.0, up=[0, 1, 0])
    run(s, f"save {out}/{tag}_top.png {size}")

    # View 2: side view with the front half clipped at the C6 axis (NTD layer on top, SP1 at the bottom).
    camera(s, [0, -1, 0], centre, 400.0, up=[0, 0, 1])
    run(s, f"clip near 0 position {cs}")
    run(s, f"save {out}/{tag}_side.png {size}")
    run(s, "clip off")

    # View 3: one subunit's CA-SP1 helix (residues 354-371) as sticks in mesh density, viewed side-on
    # from outside the bundle; slab of +-10 Å so the other five helices do not overlap it.
    lat.display = False
    first = hexm.child_models()[0]
    spec = f"#{first.id_string}:{BUNDLE}"
    run(s, f"show {spec} atoms; style {spec} stick; color {spec} byelement; color {spec} & C #e8b04a")
    run(s, "graphics silhouettes false")
    v.display = True
    run(s, f"volume #{v.id_string} level {mesh_level} style mesh meshLighting false")
    run(s, f"color #{v.id_string} #3c6fb6")
    run(s, f"volume zone #{v.id_string} nearAtoms {spec} range 2.4")
    res = first.residues[(first.residues.numbers >= 354) & (first.residues.numbers <= 371)]
    ca = res.atoms[res.atoms.names == "CA"].scene_coords
    hc = res.atoms.scene_coords.mean(axis=0)
    hx = ca[-1] - ca[0]; hx /= np.linalg.norm(hx)
    radial = hc - centre; radial[2] = 0.0
    zc = radial - hx * (radial @ hx); zc /= np.linalg.norm(zc)
    yc = np.cross(zc, hx)
    run(s, "windowsize 1000 400")
    run(s, "wait 1")
    dist = 1.7 * np.linalg.norm(ca[-1] - ca[0]) / 2 / np.tan(np.radians(15))
    s.main_view.camera.position = Place(axes=[hx, yc, zc], origin=hc + zc * dist)
    run(s, f"clip near -10 far 10 position {','.join(f'{c:.2f}' for c in hc)}")
    wide = "width 1000 height 400 supersample 2" if small else "width 2000 height 800 supersample 3"
    run(s, f"save {out}/{tag}_bundle.png {wide}")

    with open(f"{out}/{tag}_params.txt", "w") as fh:
        fh.write(f"map_mean\t{mean:.6g}\nmap_sd\t{sd:.6g}\n"
                 f"lattice_level_sd\t{lattice_sd:g}\nlattice_level\t{lattice_level:.6g}\n"
                 f"mesh_level_sd\t{mesh_sd:g}\nmesh_level\t{mesh_level:.6g}\n"
                 f"crop\tcylinder r 112 A, z -52 to +58 A\ndust_A\t25\nzone_A\t2.4\n"
                 f"helix\tresidues {BUNDLE} of one subunit (Gag numbering, PDB 5L93)\nslab_A\t20\n")
    print(f"{tag}: lattice {lattice_level:.6g}, mesh {mesh_level:.6g}")


try:
    main(sys.argv[1:])
except Exception:
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    traceback.print_exc()
    os._exit(1)
run(session, "exit")  # noqa: F821
