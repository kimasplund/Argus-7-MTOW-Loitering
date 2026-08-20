"""Validation gates for the mission simulator.

These are the gates from the design spec, not incidental unit tests. The
simulator is the piece every optimisation result will rest on, so it must be
shown correct against an analytic solution and against the published design
before anything is built on top of it.
"""
import pytest
import torch

from argus7.design.geometry import derive_wing
from argus7.design.schema import load_design
from argus7.mission.sim import (
    breguet_endurance_s,
    drag_polar,
    loiter_cl,
    simulate_loiter,
)

torch.set_default_dtype(torch.float64)


def T(v):
    return torch.tensor(float(v))


@pytest.fixture(scope="module")
def baseline():
    d = load_design("design/argus7_v1.yaml")
    g = derive_wing(d.wing)
    return dict(
        mass_total_kg=T(d.masses.mtow),
        mass_fuel_kg=T(d.masses.fuel),
        wing_area_m2=T(g.area_m2),
        aspect_ratio=T(g.aspect_ratio),
        cd0=T(d.aero.cd0),
        oswald_e=T(d.aero.oswald_e),
        cl_max=T(d.aero.cl_max),
        altitude_m=T(d.mission.loiter_altitude_m),
        bsfc_kg_per_kwh=T(0.270),
    )


def test_loiter_cl_is_stall_limited_not_min_power(baseline):
    """The report's loiter C_L of 1.21 comes from the stall margin, not min power.

    Unconstrained min-power C_L is sqrt(3*CD0*pi*AR*e) = 1.877 here, far above
    C_Lmax/1.15^2 = 1.21. Documenting which constraint binds matters, because the
    optimiser's gradient changes character when a design crosses that boundary.
    """
    cl = loiter_cl(baseline["cd0"], baseline["aspect_ratio"], baseline["oswald_e"], baseline["cl_max"])
    assert float(cl) == pytest.approx(1.21, abs=0.01)

    cl_minpower = torch.sqrt(3 * baseline["cd0"] * torch.pi * baseline["aspect_ratio"] * baseline["oswald_e"])
    assert float(cl_minpower) > 1.8, "min-power branch should be the inactive one here"


def test_gate1_step_integration_matches_closed_form_breguet(baseline):
    """SPEC GATE: the integrator must reproduce the analytic solution to <0.1%.

    Breguet assumes no electrical load and constant BSFC, so the comparison is
    made under exactly those conditions. A mismatch means the integrator is wrong,
    not that the physics differs.
    """
    stepped = simulate_loiter(**baseline, payload_power_w=T(0.0), n_steps=400)
    closed = breguet_endurance_s(**baseline)
    assert float(stepped.endurance_s) == pytest.approx(float(closed), rel=1e-3)


def test_gate2_reproduces_the_published_endurance(baseline):
    """SPEC GATE: with the 500 W payload, reproduce the report's 112.8 h.

    This is the strongest available check that the model matches the design it
    claims to represent: an independent reimplementation landing on the published
    number without tuning.
    """
    d = load_design("design/argus7_v1.yaml")
    r = simulate_loiter(**baseline, payload_power_w=T(d.mission.payload_power_w), n_steps=400)
    assert float(r.endurance_h) == pytest.approx(112.8, rel=0.05)
    assert float(r.mean_shaft_kw) == pytest.approx(3.4, rel=0.15)


def test_integration_is_converged_in_step_count(baseline):
    """200 steps must already be converged, or the optimiser inherits step noise."""
    coarse = float(simulate_loiter(**baseline, payload_power_w=T(500.0), n_steps=50).endurance_h)
    fine = float(simulate_loiter(**baseline, payload_power_w=T(500.0), n_steps=800).endurance_h)
    mid = float(simulate_loiter(**baseline, payload_power_w=T(500.0), n_steps=200).endurance_h)
    assert mid == pytest.approx(fine, rel=1e-4)
    assert coarse == pytest.approx(fine, rel=1e-2)


def test_batching_matches_scalar_evaluation(baseline):
    """A batched call must give exactly what N scalar calls would."""
    n = 32
    batched = {k: v.expand(n).clone() for k, v in baseline.items()}
    rb = simulate_loiter(**batched, payload_power_w=torch.full((n,), 500.0), n_steps=200)
    rs = simulate_loiter(**baseline, payload_power_w=T(500.0), n_steps=200)
    assert rb.endurance_h.shape == (n,)
    assert torch.allclose(rb.endurance_h, rs.endurance_h.expand(n), rtol=1e-9)


def test_gradients_are_finite_and_correctly_signed(baseline):
    """Autograd must thread the whole integration, with physically sane signs."""
    x = torch.tensor([3.9, 22.0, 0.020, 0.85], requires_grad=True)
    r = simulate_loiter(
        mass_total_kg=baseline["mass_total_kg"], mass_fuel_kg=baseline["mass_fuel_kg"],
        wing_area_m2=x[0], aspect_ratio=x[1], cd0=x[2], oswald_e=x[3],
        cl_max=baseline["cl_max"], altitude_m=baseline["altitude_m"],
        bsfc_kg_per_kwh=baseline["bsfc_kg_per_kwh"], payload_power_w=T(500.0), n_steps=200,
    )
    r.endurance_h.backward()
    g = x.grad
    assert torch.all(torch.isfinite(g))
    assert float(g[1]) > 0, "more aspect ratio must help endurance"
    assert float(g[2]) < 0, "more parasite drag must hurt endurance"
    assert float(g[3]) > 0, "better span efficiency must help endurance"


def test_gradient_matches_finite_difference(baseline):
    """Spot-check autograd against a central difference on the Oswald term.

    This is the term worth checking: span efficiency is the largest single lever
    in the drag model and is currently an unvalidated assumption.
    """
    def endurance(e_val):
        return float(simulate_loiter(**{**baseline, "oswald_e": T(e_val)},
                                     payload_power_w=T(500.0), n_steps=200).endurance_h)

    h = 1e-4
    fd = (endurance(0.85 + h) - endurance(0.85 - h)) / (2 * h)

    e = torch.tensor(0.85, requires_grad=True)
    r = simulate_loiter(**{**baseline, "oswald_e": e}, payload_power_w=T(500.0), n_steps=200)
    r.endurance_h.backward()
    assert float(e.grad) == pytest.approx(fd, rel=1e-4)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device")
def test_cuda_agrees_with_cpu(baseline):
    cpu = simulate_loiter(**baseline, payload_power_w=T(500.0), n_steps=200)
    gpu_args = {k: v.cuda() for k, v in baseline.items()}
    gpu = simulate_loiter(**gpu_args, payload_power_w=T(500.0).cuda(), n_steps=200)
    assert float(gpu.endurance_h.cpu()) == pytest.approx(float(cpu.endurance_h), rel=1e-9)


def test_drag_polar_is_the_documented_form(baseline):
    cd = drag_polar(T(1.21), baseline["cd0"], baseline["aspect_ratio"], baseline["oswald_e"])
    expected = 0.020 + 1.21**2 / (torch.pi * 22.0 * 0.85)
    assert float(cd) == pytest.approx(float(expected), rel=1e-12)
