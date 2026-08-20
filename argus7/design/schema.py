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
    chord_root_m_assert: float | None = None   # optional cross-check, not a source of truth

class Fuselage(BaseModel):
    length_m: float = Field(gt=0)
    max_diameter_m: float = Field(gt=0)

class Booms(BaseModel):
    length_m: float = Field(gt=0)
    diameter_m: float = Field(gt=0)
    y_station_frac: float = Field(gt=0, lt=1)

class Tail(BaseModel):
    type: str
    area_h_m2: float = Field(gt=0)
    arm_m: float = Field(gt=0)
    dihedral_deg: float
    taper_ratio: float = Field(gt=0, le=1)
    airfoil: str

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
