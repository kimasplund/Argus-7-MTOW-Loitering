# ARGUS-7 — Persistent Disaster-Zone Communications & Survey UAV

Paper design study for a long-endurance fixed-wing UAV that loiters over a disaster
zone carrying a 50 kg multi-role bay (LTE/5G relay + EO/IR gimbal + mesh/satcom
backhaul), recovered by parachute and airbag for reuse.

**Status:** v1.0 paper design, independently verified. No hardware, no build.

## Headline numbers (v1.0, verified)

| Metric | Value |
|---|---|
| MTOW | 250 kg |
| Payload | 50 kg / ~500 W continuous |
| Loiter endurance (4,000 m, payload on) | 4.7 days (112.8 h) |
| Self-deploy 2,000 km → loiter | 4.0 days on station |
| Wing | S 3.9 m², AR 22, span 9.26 m |
| Propulsion | 250 cc-class liquid-cooled 4-stroke EFI, belt reduction, 32″ pusher prop |
| Recovery | 85 m² round canopy, 6 m/s descent, airbag/crush keel |

The 5–7 day mission target is reachable only with diesel-class BSFC, a clean build
(C_D0 ≤ 0.018) and payload duty-cycling — see the executive summary caveat in the
report before quoting any of the above.

## Where things are

| Path | What it is |
|---|---|
| [docs/argus7_design_report.md](docs/argus7_design_report.md) | **Start here.** Full design report v1.0 + Annex A premortem + assumptions register |
| [docs/argus7_design_report.docx](docs/argus7_design_report.docx) | Same report, Word format with footnotes |
| [docs/plan.md](docs/plan.md) | Original 5-stage work plan (research → design → verify → premortem → report) |
| [docs/report_outline.md](docs/report_outline.md) | Section-by-section outline used to assemble the report |
| [research/design_pack.md](research/design_pack.md) | Verified data pack — every number recomputed from first principles, with sources |
| [model/argus7_model.scad](model/argus7_model.scad) | Parametric OpenSCAD airframe model |
| [figures/](figures/) | `argus7_3view.png`, `argus7_performance.png` (current design) |
| [figures/design-pack/](figures/design-pack/) | `fig1`–`fig9` supporting the data pack |
| [archive/](archive/) | Original delivery zip, kept for provenance |

## Two design points in this repo

These are **not** the same aircraft, and the numbers do not interchange:

- **Data pack** ([research/design_pack.md](research/design_pack.md)) — the earlier
  200 kg MTOW / AR 20 / 40 kg payload ultra-long-range point. Figures `fig1`–`fig9`
  and the outline in [docs/report_outline.md](docs/report_outline.md) belong to it.
- **Report** ([docs/argus7_design_report.md](docs/argus7_design_report.md)) — the
  current 250 kg MTOW / AR 22 / 50 kg payload persistent-loiter point that supersedes it.

Section 10 of the report ("What Was Corrected From the Crashed Gemini Session")
records what changed and why.

## Viewing the model

```bash
openscad model/argus7_model.scad          # interactive
openscad -o argus7.stl model/argus7_model.scad   # export mesh
```

Geometry is parameter-driven at the top of the file (`span`, `c_root`, `c_tip`,
`S_h`, `S_v`, boom and fuselage dimensions).

## Known gaps

- SCAD header geometry (`c_root` 0.674 / `c_tip` 0.303 / MAC 0.421 m) does not match
  the report's §2 table (0.581 / 0.261 / 0.441 m). The report table is authoritative;
  the model needs re-syncing.
- No source code for the analysis — the Python that produced the verified numbers and
  figures did not survive the originating session. Results are reproducible only from
  the method descriptions in the data pack.
- Regulatory treatment (§9) is EU headline level only.
