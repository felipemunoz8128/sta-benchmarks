"""Extract FSC curves from RELION postprocess STAR files and M species FSC STAR files into CSV.

Usage:
    uv run scripts/extract_fsc.py ROW:KIND:PATH [ROW:KIND:PATH ...] [--out data]

KIND is "relion" (a postprocess.star written by relion_postprocess) or "m" (the FSC STAR file that
M writes next to a species map). For every input the script writes data/fsc_<ROW>.csv with the same
columns, and it writes data/fsc_summary.csv with one line per row: the resolution the program
reported (RELION only), the B-factor used for sharpening (RELION only), and the resolution at
FSC = 0.143 computed here from the table, both as the last shell at or above 0.143 and by linear
interpolation in spatial frequency between the two shells that bracket 0.143. For M, whose FSC file holds no
reported value, the reported value is the interpolated crossing to two decimals, as M prints it.

Only numbers are copied. File names and paths stored inside the STAR files are not written out.
"""

import argparse
import csv
import math
import sys
from pathlib import Path

THRESHOLD = 0.143

COLUMNS = [
    "spatial_frequency_per_A",
    "resolution_A",
    "fsc_corrected",
    "fsc_unmasked",
    "fsc_masked",
    "fsc_phase_randomised_masked",
]

RELION_MAP = {
    "fsc_corrected": "_rlnFourierShellCorrelationCorrected",
    "fsc_unmasked": "_rlnFourierShellCorrelationUnmaskedMaps",
    "fsc_masked": "_rlnFourierShellCorrelationMaskedMaps",
    "fsc_phase_randomised_masked": "_rlnCorrectedFourierShellCorrelationPhaseRandomizedMaskedMaps",
}

M_MAP = {
    "fsc_corrected": "_wrpFSCCorrected",
    "fsc_unmasked": "_wrpFSCUnmasked",
    "fsc_masked": "_wrpFSCMasked",
    "fsc_phase_randomised_masked": "_wrpFSCRandomized",
}


def read_star_blocks(path):
    """Return {block_name: {"pairs": {label: value}, "loop": (labels, rows)}} for a STAR file."""
    blocks = {}
    current = None
    labels, rows, in_loop = [], [], False
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if in_loop and rows:
                in_loop = False
            continue
        if line.startswith("data_"):
            current = line
            blocks[current] = {"pairs": {}, "loop": ([], [])}
            labels, rows, in_loop = [], [], False
            continue
        if line.startswith("loop_"):
            labels, rows, in_loop = [], [], True
            blocks[current]["loop"] = (labels, rows)
            continue
        if line.startswith("_"):
            parts = line.split()
            if in_loop and not rows:
                labels.append(parts[0])
            else:
                blocks[current]["pairs"][parts[0]] = parts[1] if len(parts) > 1 else ""
            continue
        if in_loop:
            rows.append(line.split())
    return blocks


def to_float(text):
    if text.lower() in ("infinity", "inf"):
        return math.inf
    return float(text)


def load_relion(path):
    blocks = read_star_blocks(path)
    general = blocks["data_general"]["pairs"]
    labels, rows = blocks["data_fsc"]["loop"]
    idx = {label: i for i, label in enumerate(labels)}
    table = []
    for r in rows:
        rec = {
            "spatial_frequency_per_A": float(r[idx["_rlnResolution"]]),
            "resolution_A": float(r[idx["_rlnAngstromResolution"]]),
        }
        for col, label in RELION_MAP.items():
            rec[col] = float(r[idx[label]])
        table.append(rec)
    meta = {
        "program": "relion_postprocess",
        "reported_resolution_A": general.get("_rlnFinalResolution", ""),
        "bfactor_A2": general.get("_rlnBfactorUsedForSharpening", ""),
    }
    return table, meta


def load_m(path):
    blocks = read_star_blocks(path)
    block = next(b for b in blocks.values() if b["loop"][0])
    labels, rows = block["loop"]
    idx = {label: i for i, label in enumerate(labels)}
    table = []
    for r in rows:
        res = to_float(r[idx["_wrpResolution"]])
        rec = {
            "spatial_frequency_per_A": 0.0 if math.isinf(res) else 1.0 / res,
            "resolution_A": res,
        }
        for col, label in M_MAP.items():
            rec[col] = float(r[idx[label]])
        table.append(rec)
    meta = {"program": "M (species FSC)", "reported_resolution_A": "", "bfactor_A2": ""}
    return table, meta


def crossing(table, column="fsc_corrected", threshold=THRESHOLD):
    """Last shell at or above threshold before the first drop below it, and the interpolated crossing."""
    for i in range(1, len(table)):
        if table[i][column] < threshold:
            last = table[i - 1]
            f0, f1 = last["spatial_frequency_per_A"], table[i]["spatial_frequency_per_A"]
            y0, y1 = last[column], table[i][column]
            f = f0 + (y0 - threshold) * (f1 - f0) / (y0 - y1)
            return last["resolution_A"], 1.0 / f
    return None, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("specs", nargs="+", help="ROW:KIND:PATH, KIND = relion or m")
    parser.add_argument("--out", default="data", help="output folder (default: data)")
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for spec in args.specs:
        row, kind, path = spec.split(":", 2)
        table, meta = (load_relion if kind == "relion" else load_m)(path)
        with open(out / f"fsc_{row}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(COLUMNS)
            for rec in table:
                w.writerow([("inf" if math.isinf(rec[c]) else f"{rec[c]:.6f}") for c in COLUMNS])
        shell, interp = crossing(table)
        if kind == "m":   # M prints its interpolated crossing to two decimals (2.76 for row B)
            meta["reported_resolution_A"] = f"{interp:.2f}"
        summary.append({
            "row": row,
            "program": meta["program"],
            "reported_resolution_A": meta["reported_resolution_A"],
            "bfactor_A2": meta["bfactor_A2"],
            "last_shell_at_or_above_0.143_A": f"{shell:.6f}" if shell else "",
            "interpolated_0.143_A": f"{interp:.4f}" if interp else "",
            "nyquist_A": f"{table[-1]['resolution_A']:.6f}",
        })
        print(f"{row}: {meta['program']}, reported {meta['reported_resolution_A'] or '-'}, "
              f"last shell >= 0.143 {shell:.6f} A, interpolated {interp:.4f} A", file=sys.stderr)

    with open(out / "fsc_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)


if __name__ == "__main__":
    main()
