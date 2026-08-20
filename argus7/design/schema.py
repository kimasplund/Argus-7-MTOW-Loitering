from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

class Wing(BaseModel):
    area_m2: float = Field(gt=0)
    aspect_ratio: float = Field(gt=0)
    taper_ratio: float = Field(gt=0, le=1)
    airfoil: str
    twist_tip_deg: float          # negative = washout
    dihedral_deg: float
    sweep_le_deg: float
    thickness_ratio: float = Field(gt=0, lt=0.5)
    incidence_deg: float
    # Vertical offset of the wing root leading edge above the fuselage
    # centreline / boom axis (z = 0). Promoted out of the bare 0.05 that was
    # typed into argus7.cad.model.build_aircraft AND, a second time, into
    # argus7.cad.to_openscad (final review, finding C1): at 0.05 m the wing
    # floated 25.8 mm clear of the booms it is supposed to carry. No default:
    # a Python-side default is exactly the geometry literal this field exists
    # to abolish.
    z_offset_m: float
    chord_root_m_assert: float | None = None   # optional cross-check, not a source of truth

class Fuselage(BaseModel):
    length_m: float = Field(gt=0)
    max_diameter_m: float = Field(gt=0)
    # (x_fraction, radius_fraction) pairs defining the outer-mould-line
    # loft stations, nose (0.0) to tail (1.0). Promoted out of
    # argus7.cad.model.build_fuselage (Task-4 review, fix round 1,
    # finding 1): the whole hull shape must not be hardcoded in Python.
    stations: list[tuple[float, float]]

class Booms(BaseModel):
    # length_m is DELETED as an input (ruling P15): its old value, 3.2,
    # came from the defective SCAD, not from any report, and cannot span
    # wing to tail. It is now derived geometry -- see
    # argus7.design.geometry.derive_booms -- not a schema field.
    diameter_m: float = Field(gt=0)
    y_station_frac: float = Field(gt=0, lt=1)
    # Longitudinal clearance the boom extends beyond the wing root LE it
    # carries at the front, and beyond the tail quarter-chord it carries
    # at the aft end. Promoted out of derive_booms's bare 0.15 (Task-4
    # review, fix round 1, finding 3).
    clearance_m: float = Field(gt=0)

class Tail(BaseModel):
    type: str
    area_h_m2: float = Field(gt=0)
    arm_m: float = Field(gt=0)
    dihedral_deg: float
    taper_ratio: float = Field(gt=0, le=1)
    airfoil: str
    # Assumed tail panel aspect ratio, used to turn the projected
    # horizontal area (area_h_m2) into a chord/span pair for the CAD
    # loft. Promoted out of build_tail's bare "AR 3" constant (Task-4
    # review, fix round 1, finding 2).
    panel_aspect_ratio: float = Field(gt=0)

class Propulsion(BaseModel):
    engine_displacement_cc: float
    power_max_kw: float
    reduction_ratio: float
    prop_diameter_m: float
    prop_rpm: float

class Masses(BaseModel):
    airframe: float; powertrain: float; avionics: float
    recovery: float; payload: float; fuel: float; mtow: float

class Mission(BaseModel):
    payload_mass_kg: float
    payload_power_w: float
    loiter_altitude_m: float

class Aero(BaseModel):
    cd0: float; oswald_e: float; cl_max: float

class Design(BaseModel):
    name: str
    variant: str
    wing: Wing
    fuselage: Fuselage | None = None
    booms: Booms | None = None
    tail: Tail | None = None
    propulsion: Propulsion | None = None
    masses: Masses | None = None
    mission: Mission | None = None
    aero: Aero | None = None
    # Maps "section.field" -> one of report-§2 / design_pack-§1 / derived /
    # assumption. Machine-checked provenance so a defective-artifact value
    # (e.g. model/argus7_model.scad) can never again be silently claimed as
    # report-sourced. See test_every_geometry_field_has_provenance.
    provenance: dict[str, str] | None = None

def load_design(path: str | Path) -> Design:
    from argus7.design.geometry import check_closure
    data = yaml.safe_load(Path(path).read_text())
    design = Design(**data)
    check_closure(design)
    return design
