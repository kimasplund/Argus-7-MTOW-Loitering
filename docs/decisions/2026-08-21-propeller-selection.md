# Propeller selection — the propulsion set now closes

**2026-08-21.** BEMT sweep over ~400 configurations, both operating points required
simultaneously.

## Selected

**1.00 m diameter, 2 blades, 1900 rpm, pitch/diameter 1.05.**

| | Value |
|---|---|
| Loiter efficiency | **0.852** |
| Climb power absorbed | 99.0% of the 8.15 kW rating |
| Tip Mach | 0.30 |
| Boom clearance | 76 mm |
| **Reduction ratio** | **3.95:1** for a 7500 rpm engine |

The 1.04 m disc is marginally better (η 0.858) but leaves only 56 mm to the booms.
0.6% of efficiency is worth 36% more clearance on a pusher whose blades pass a
structural member.

## The published set could not close; this one does

v1.0 specified a 0.813 m prop at 2100 rpm against a 17 kW engine, requiring
**C_P = 0.911** against a practical ceiling near 0.25. It could absorb about
4.7 kW of 17. The design was not flyable as written.

**The propeller was never the real defect.** It was being asked to absorb an engine
sized for climb. Right-sizing the engine to 8.15 kW more than halved the absorption
requirement, and an ordinary 1.0 m two-blade prop then takes it comfortably. The
unflyable propulsion set was a *symptom* of the oversized engine.

Of 100 configurations in the first sweep, **34 satisfied both operating points**.
For the published design the count was zero.

## Variable pitch is not needed — a genuine save

The loiter-optimal pitch turns out to be **the same p/D the fixed-pitch optimum
already uses**, so a constant-speed unit buys **+0.00%** at loiter. It would add
mass, cost, and a failure mode on a 122-hour unattended mission for no endurance.

This holds because the fixed-pitch design was selected under a *simultaneous*
climb-absorption constraint, so it is already sitting where a variable unit would
put it. Caveat: this evaluates loiter efficiency and climb absorption, not climb
*rate* optimisation; the fixed prop absorbs 99% at climb, so climb is satisfied.

## Loiter is a gentle condition

62.8 N of thrust and 1.70 kW of useful power at 97.4 km/h. That is why a large slow
disc wins and why tip Mach never becomes a constraint (0.30 against a 0.75 limit).

## Corrections to the published design

- **Reduction ratio 2.3:1 → 3.95:1.** A small 4-stroke peaking near 7500 rpm cannot
  drive a 1900 rpm prop through 2.3:1.
- **Prop efficiency 0.84 assumed → 0.852 achieved**, worth **+2.5 h**. The mission
  simulator was mildly pessimistic here.
- The design schema now carries blade count, pitch ratio and loiter efficiency.
  v1.0 recorded only diameter and rpm, which is insufficient to determine whether a
  propeller can absorb its engine — and that is exactly the check that failed.

## Not yet done

- Blade planform and twist are a constant-pitch idealisation; a real blade wants
  chord and twist distributions optimised for the loiter point.
- Boom-wake and pusher-installation effects on inflow are not modelled.
- No structural or acoustic check on the blade.
