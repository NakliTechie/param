#!/usr/bin/env python3
"""Copy results.csv from ../param-fp64 (a file copy, never a dependency) and render the
benchmark table into site/index.html between <!-- bench:start --> and <!-- bench:end -->."""
import csv, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "param-fp64" / "results" / "results.csv"
DST = ROOT / "site" / "data" / "results.csv"
if SRC.exists():
    shutil.copy(SRC, DST)
rows = list(csv.DictReader(DST.open()))
order = ["ll7", "ll7f32", "linpack100", "linpack1000", "peak", "sustained"]
workloads = sorted({r["workload"] for r in rows}, key=lambda w: order.index(w) if w in order else 99)
names = {"ll7": "LL7", "ll7f32": "LL7 (fp32)", "linpack100": "LINPACK 100", "linpack1000": "LINPACK 1000", "peak": "peak", "sustained": "sustained"}
keys = []
for r in rows:
    k = (r["machine"], r["mode"], r["thermal"].split(";")[0])
    if k not in keys: keys.append(k)

def cell(r):
    v = float(r["mflops"]); s = f"{v:,.0f}" if v >= 10 else f"{v:.2f}"
    if r["precision"] != "fp64": s += f" <span class=small>({r['precision']})</span>"
    return s + {"measured": "", "published": " ᵖ", "reconstructed": " ʳ"}[r["source"]]

h = ["<table><thead><tr><th>machine</th><th>mode</th><th>thermal</th>"] + [f"<th class=n>{names.get(w, w)}</th>" for w in workloads] + ["</tr></thead><tbody>"]
for m, mode, th in keys:
    h.append(f"<tr><td>{m}</td><td>{mode}</td><td>{th}</td>")
    for w in workloads:
        hit = [r for r in rows if r["machine"] == m and r["mode"] == mode and r["thermal"].split(";")[0] == th and r["workload"] == w]
        h.append(f"<td class=n>{cell(hit[0]) if hit else '—'}</td>")
    h.append("</tr>")
meas = [r for r in rows if r["source"] == "measured"]
h.append("</tbody></table>")
h.append(f"<p class=small>MFLOPS, FP64 unless labelled. ᵖ published · ʳ reconstructed · unmarked measured. Measured cells: {meas[0]['compiler']}, flags <code>{meas[0]['flags']}</code>, median of {max(int(r['runs']) for r in meas)} runs for sustained cells; throughput = {max(int(r['cores']) for r in meas)} independent processes, MFLOPS summed.</p>" if meas else "")
p = ROOT / "site/index.html"; s = p.read_text()
s = re.sub(r"<!-- bench:start -->.*?<!-- bench:end -->", "<!-- bench:start -->\n" + "\n".join(h) + "\n<!-- bench:end -->", s, flags=re.S)
p.write_text(s); print(f"bench table: {len(rows)} rows")
