# param — the line and the shelf

Artifact 3 of the PARAM strand: an essay with one chart. Every performance threshold in US computer export controls since 1992, converted to FP64 and set against what one person could buy. India appears on the chart twice, 38 years apart.

Live: https://param.naklitechie.com

## Layout

- `site/` — the deployed static site. `index.html` is the piece; `data/` holds the chart data (`thresholds.json`, `shelf.json`) and a copy of the benchmark results (`results.csv`) from [param-fp64](https://github.com/NakliTechie/param-fp64).
- `scripts/build_chart.py` — renders the SVG chart from `site/data/*.json` into `index.html` between markers. Dev-time only.
- `scripts/build_bench.py` — copies `../param-fp64/results/results.csv` (a file copy, never a dependency) and renders the numbers table into `index.html`.
- `wrangler.jsonc` — Cloudflare Worker, static assets only, no build step; custom domain `param.naklitechie.com`.

## Sourcing rule

Threshold values come from the regulations and Federal Register notices themselves. The FP64 conversion for each row is stated in `thresholds.json`. Contested claims about PARAM 8000 are quoted as claims and never enter a table. Every consumer-shelf point carries its source class.

## Regenerate

```
python3 scripts/build_chart.py && python3 scripts/build_bench.py
```
