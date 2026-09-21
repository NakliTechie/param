#!/usr/bin/env python3
"""Render the export-control chart as inline SVG and splice it into site/index.html
between <!-- chart:start --> and <!-- chart:end -->. Data: site/data/*.json.
Dev-time only; the deployed site is static."""
import json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TH = json.load(open(ROOT / "site/data/thresholds.json"))["rows"]
SH = json.load(open(ROOT / "site/data/shelf.json"))["rows"]

W, H = 880, 520
ML, MR, MT, MB = 64, 24, 28, 44
X0, X1 = 1986.5, 2026.9
Y0, Y1 = -1, 9  # log10 MFLOPS: 0.1 MFLOPS .. 1e9 MFLOPS (1 PFLOPS)


def x(year): return ML + (year - X0) / (X1 - X0) * (W - ML - MR)
def y(mflops): return MT + (Y1 - math.log10(mflops)) / (Y1 - Y0) * (H - MT - MB)
def yr(date): y_, m, d = (int(v) for v in date.split("-")); return y_ + (m - 1) / 12 + (d - 1) / 365


def fmt(v):
    for unit, div in (("PFLOPS", 1e9), ("TFLOPS", 1e6), ("GFLOPS", 1e3), ("MFLOPS", 1)):
        if v >= div: return f"{v/div:g} {unit}"
    return f"{v:g} MFLOPS"


out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="chart-title chart-desc" font-family="inherit">',
       '<title id="chart-title">FP64 performance: US export-control thresholds applied to India, and what a person could buy, 1987–2026</title>',
       '<desc id="chart-desc">Log-scale chart. A stepped line shows the control threshold in force each year, converted to FP64 MFLOPS. A second line shows the fastest FP64 box on the consumer shelf. The consumer line crosses the control line in the early 2000s and stays above it until the 2022 chip rules, which are drawn dashed because their metric is not FP64.</desc>']

# y gridlines: one per decade, hairline
for e in range(Y0, Y1 + 1):
    v = 10 ** e
    yy = y(v)
    out.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{W-MR}" y2="{yy:.1f}" class="grid"/>')
    out.append(f'<text x="{ML-8}" y="{yy+4:.1f}" text-anchor="end" class="tick">{fmt(v)}</text>')
# x ticks
for yr_ in range(1990, 2027, 5):
    out.append(f'<text x="{x(yr_):.1f}" y="{H-MB+18}" text-anchor="middle" class="tick">{yr_}</text>')
    out.append(f'<line x1="{x(yr_):.1f}" y1="{H-MB}" x2="{x(yr_):.1f}" y2="{H-MB+4}" class="axis"/>')
out.append(f'<line x1="{ML}" y1="{H-MB}" x2="{W-MR}" y2="{H-MB}" class="axis"/>')

# threshold step line (India-applicable: CTP then APP)
steps = [r for r in TH if r["kind"] == "threshold"]
pts = []
for i, r in enumerate(steps):
    xs = x(yr(r["date"])); ys = y(r["fp64_mflops"])
    if pts: pts.append((xs, pts[-1][1]))
    pts.append((xs, ys))
pts.append((x(X1), pts[-1][1]))
out.append('<polyline class="threshold" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + '"/>')

# 3A090 chip line, dashed, incommensurable
chip = [r for r in TH if r["kind"] == "threshold-other"]
c0 = chip[0]
out.append(f'<polyline class="chip" points="{x(yr(c0["date"])):.1f},{y(c0["fp64_mflops"]):.1f} {x(X1):.1f},{y(c0["fp64_mflops"]):.1f}"/>')
out.append(f'<text x="{x(2022.6):.1f}" y="{y(c0["fp64_mflops"])-8:.1f}" class="label chip-label">3A090 chips: TPP 4,800 ≈ 75 TFLOPS if FP64 were the fastest precision</text>')

# consumer shelf
sp = [(x(r["year"]), y(r["fp64_mflops"])) for r in SH]
out.append('<polyline class="shelf" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in sp) + '"/>')
for r, (a, b) in zip(SH, sp):
    out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.2" class="shelf-pt"><title>{r["year"]} {r["box"]}: {fmt(r["fp64_mflops"])} FP64 ({r["kind"]})</title></circle>')

# annotations
ev87 = [r for r in TH if r["date"].startswith("1987")][0]
out.append(f'<circle cx="{x(1987.77):.1f}" cy="{y(420):.1f}" r="4.5" class="event"/>')
out.append(f'<text x="{x(1988.2):.1f}" y="{y(420)-10:.1f}" class="label">1987: Cray X-MP/24 refused to India (≈420 MFLOPS); X-MP/14 permitted with safeguards</text>')
out.append(f'<circle cx="{x(yr("2025-01-13")):.1f}" cy="{y(75e6):.1f}" r="4.5" class="event"/>')
out.append(f'<text x="{x(2024.9):.1f}" y="{y(75e6)+22:.1f}" text-anchor="end" class="label">2025: India capped under the AI Diffusion rule (Jan–May)</text>')
# series labels
out.append(f'<text x="{x(2008.3):.1f}" y="{y(steps[-9]["fp64_mflops"])+30:.1f}" class="label threshold-label">control threshold in force for India, FP64-equivalent</text>')
out.append(f'<text x="{x(2000.4):.1f}" y="{y(1200)+34:.1f}" class="label shelf-label">fastest FP64 box on the consumer shelf</text>')
out.append(f'<text x="{x(1987):.1f}" y="{y(1.5e6):.1f}" class="label shelf-label">1987: Compaq 386/20 at 0.16 MFLOPS</text>')
out.append('</svg>')
svg = "\n".join(out)

html_path = ROOT / "site/index.html"
h = html_path.read_text()
new = re.sub(r"<!-- chart:start -->.*?<!-- chart:end -->", "<!-- chart:start -->\n" + svg + "\n<!-- chart:end -->", h, flags=re.S)
html_path.write_text(new)
print(f"chart: {len(steps)} threshold steps, {len(SH)} shelf points, spliced into {html_path}")
