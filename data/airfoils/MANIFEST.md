# Airfoil coordinate manifest

Airfoil coordinate files are **pinned data**, not incidental fixtures.
`fx63137.dat` is load-bearing well beyond the CAD loft: its shoelace shape
factor (0.6062, section area / max thickness at unit chord) drives
`tests/test_cad_wing.py::test_wing_planform_area_matches_spec`, the ~143 L
gross wing volume quoted in `README.md`, and the two corrections in
`research/materials_pack.md` §2.5 that supersede that pack's 160 L figure.

UIUC ships several FX 63-137 variants. Substituting one with the same 13.7%
t/c would pass every other check in this repository while silently moving the
shape factor, the wing volume, and with it the fuel-volume conclusion that is
currently escalated to the sponsor. Hence the checksums below, enforced by
`tests/test_airfoil_coords.py`:

- `test_manifest_lists_exactly_the_committed_dat_files` — no unlisted file,
  no listed file missing.
- `test_airfoil_dat_checksums_match_the_manifest` — the bytes.
- `test_manifest_thickness_matches_the_measured_file` — what the bytes mean,
  so a row cannot be updated to bless a substitution without the substitution
  showing up in the recorded t/c.
- `test_manifest_records_a_retrieval_date_for_every_file`.

**Changing any file here requires re-checking the shape factor, the wing
volume in `README.md`, and `research/materials_pack.md` §2.5 — then updating
the row.** Phase 2 adds S1223, E387 and SD7037; each needs a row.

| File | Source | Retrieved | Format | Points | t/c | sha256 |
|---|---|---|---|---|---|---|
| `fx63137.dat` | https://m-selig.ae.illinois.edu/ads/coord/fx63137.dat | 2026-08-20 | Lednicer, 49/49 header | 98 | 0.13712 | `8c3a70fa1639885a72bb1394ff6666db637efc4971d3594f1a3882c1b9f18c5d` |

Notes on the row above:

- **Source URL** is the UIUC Airfoil Coordinates Database's canonical path for
  this section. The file was committed in git `0654436`, whose message
  identifies it as "the real UIUC fx63137.dat"; the URL itself was *not*
  recorded at retrieval time and is reconstructed from that database's fixed
  naming scheme. The retrieval date is that commit's date. Both are recorded
  as the honest best account, not as a verified download log.
- **Format**: Lednicer — a title line, then a `49.0 49.0` per-surface
  point-count header (not a coordinate), then two LE→TE surface blocks.
  `argus7.cad.airfoil_coords.load_airfoil` detects this, validates the split
  against the declared counts, and reassembles into Selig order; 98 raw points
  become 97 after the shared leading-edge point is de-duplicated.
- **Derived quantities** (recomputed from these exact bytes, recorded here so
  a change is visible even where no test reads them): max camber 0.05968,
  section area at unit chord 0.08312, shape factor 0.08312 / 0.13712 =
  **0.6062**.

## Deleted: `naca0010.dat`

`data/airfoils/naca0010.dat` was committed but **never read**.
`argus7.cad.model._section_coords` routes any airfoil name beginning with
`NACA` to the `naca4()` generator, so the file was unreachable by
construction, not merely unused — two sources for one section (the tail's
`NACA0010`), one of them dead.

**It was deleted rather than wired in.** Git `0654436` shows the file was
itself *generated* by `naca4('0010')` and written out to 6 decimal places:
the maximum absolute difference between its 241 points and the live
generator's output is 5e-7, i.e. rounding. It was a cached copy of a pure
function. A NACA 4-digit section is *defined* by a closed-form equation, so
the generator is the authoritative source and a coordinate dump is a
discretisation of it — keeping both would add a drift surface for no
information, which is the defect class this whole phase exists to close. The
generator is parameterised for whatever 4-digit sections Phase 2 wants and is
covered by the thickness and symmetry tests in
`tests/test_airfoil_coords.py`.

`test_no_committed_dat_is_unreachable_by_the_loader` keeps the directory
honest. Non-NACA files are deliberately not policed by that test: Phase 2 will
land candidate sections here before any design file selects one.
