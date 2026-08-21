# Structural analysis: what it found, and what is not yet trustworthy

**2026-08-21.** CalculiX and gmsh had been installed since day one and never pointed
at the airframe. This is the first structural work in the programme.

## The headline: the wing is very flexible, and the caps buckle

| Finding | Value | Status |
|---|---|---|
| **Tip deflection at limit (+3.8 g)** | **854 mm = 14.4% of semi-span** | **Cross-validated** |
| Tip deflection at ultimate (+5.7 g) | 1,283 mm = 21.6% | Cross-validated |
| Root cap stress at ultimate | 600 MPa against a 600 MPa allowable | Margin **exactly zero** |
| **Compression-cap buckling** | critical **80 MPa** against **600 MPa** applied | **Margin −87%** |
| Wing divergence speed | ~1,030 km/h | First-order |
| Wing flutter estimate | ~493 km/h | First-order |
| Boom first torsion | 14.5 Hz vs prop 1P at 34.2 Hz | 19.7 Hz separation, OK |

## 1. Deflection — cross-validated, and large

Two independent routes agree:

- My own M/EI double integration over the tapered spar: **14.4%** of semi-span at limit
- `research/materials_pack.md`'s independent estimate: **14.2%**

Agreement to 0.2 points across separately-derived methods. **854 mm of tip rise at
limit load on a 5.93 m semi-span** is a very flexible wing — sailplane territory,
not light-aircraft territory. It is not obviously disqualifying, but it interacts
with everything: control effectiveness, spanload (and therefore the AVL-measured
span efficiency the endurance rests on), and the flutter margin.

## 2. Buckling is the governing failure mode, and the margin is negative

The cap reaches its 600 MPa material allowable exactly at ultimate — zero margin by
construction, because that is how the mass model sizes it. But local buckling of the
cap between ribs is critical at **80 MPa**, so the cap would buckle at roughly an
eighth of the load the material could carry.

Report §5 says buckling governs. This confirms it, and says the current sizing does
not account for it. The fix is not more carbon: it is rib pitch, cap width-to-
thickness ratio, and skin support. **The mass model is therefore optimistic** — a
buckling-sized cap is heavier than a strength-sized one, and wing mass feeds
straight back into the endurance number.

Caveat: the cap cross-section aspect ratio here is assumed, not designed. The
magnitude of the shortfall is uncertain; its sign is not.

## 3. Aeroelastic — the good news

Divergence at ~1,030 km/h and flutter at ~493 km/h are both far above the
**207 km/h power limit**, so the aircraft is power-limited rather than
aeroelastically limited. This retires the concern raised when the speed envelope
was computed — that a high-aspect wing on slender booms might cap V_max below its
power limit. It does not.

These are first-order estimates (torsional divergence and a binary flutter
approximation), not a coupled aeroelastic solution. The margin is large enough
(2.4× on flutter) that the conclusion is robust to the method being crude.

## 4. The CalculiX model is NOT yet trustworthy

The beam FEA returns a tip deflection of 100% of semi-span against the
cross-validated 14.4%. The fault is the section definition: section properties are
converted to an equivalent rectangle, and CalculiX's local axis convention means
the strong axis is not aligned with the bending direction. One earlier bug in the
same conversion (b and h transposed, worth a factor of 10⁴ in I) was found and
fixed; this is a second, separate problem in the same place.

**Do not use the FEA numbers.** The modal results below come from the same model
and inherit the same doubt:

| Mode | Frequency |
|---|---|
| 1 | 2.14 Hz |
| 2 | 7.73 Hz |
| 3 | 8.49 Hz |
| 4 | 18.51 Hz |

What would settle it: define the section explicitly with `*BEAM SECTION,
SECTION=GENERAL` giving A, I11, I12, I22 and J directly rather than via an
equivalent rectangle, and validate against a uniform cantilever with a closed-form
solution before trusting any tapered result.

## What this changes

- **Wing mass is understated.** Buckling-sized caps are heavier than
  strength-sized ones, and the mass model uses the latter. Endurance follows mass.
- **The speed envelope stands.** Power governs, not aeroelasticity.
- **Boom torsion is clear** of prop excitation by 19.7 Hz at this design point.
  Note this supersedes the 22.7 Hz figure in `research/boom_construction_pack.md`,
  which was computed for a 3.65 m boom; v5.0's is 6.25 m.
