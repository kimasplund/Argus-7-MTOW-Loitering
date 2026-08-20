# PLAN — "ARGUS-7" Persistent Disaster-Zone Comms/Survey UAV

## Mission (locked with user)
- Payload: ~50 kg multi-role bay (comms relay + EO/IR cameras/sensors)
- Mission: local ops near disaster zone, loiter 5–7 days continuous
- Recovery: parachute + airbag (reusable airframe)
- Environment: ~0–4,500 m altitude band, loiter speed regime
- Heritage: continue from crashed Gemini session (200 kg MTOW class, heavy-fuel 4-stroke, high-AR wing) — re-derived, not trusted blindly

## Stage 1 — Grounding research (parallel explore subagents)
- R1: Propulsion — mass-produced liquid-cooled 4-stroke EFI engines 125–250cc (Honda eSP+, Yamaha Blue Core, UAV heavy-fuel options): real specs, BSFC, alternator output, mass. Needed because loiter power ~2–3 kW continuous + 300–500W avionics/payload electrical.
- R2: Payload & benchmarks — disaster-response comms UAVs (Flying COW, HAPS relays), EO/IR gimbal masses, RF power budgets, antenna configs; parachute recovery systems for 100–200 kg class UAVs.
- R3: Verification benchmarks — published data on comparable platforms (Aerosonde, Penguin, Sentry, Zephyr-class) to sanity-check L/D, fuel burn, empty-weight fraction.

## Stage 2 — Parametric design & simulation (main agent, Python)
- Wing sizing for loiter (min-power speed, not max-range speed), drag polar, AR trade vs structure
- Weight budget closing to MTOW; fuel sized for 7-day loiter + reserve
- Engine/reduction/prop matching; electrical power budget (payload 24/7)
- Stability: tail volumes, CG travel, static margin
- Structures: spar sizing at limit/ultimate loads, gust loads at loiter speed
- Thermal: radiator sizing incl. payload bay heat; oil system for 168 h run
- Recovery: parachute sizing, descent rate, airbag/crush load
- Comms coverage: link budget, footprint vs altitude
- 3D model: parametric OpenSCAD/STL of airframe + plots

## Stage 3 — Independent verification (verifier subagent)
- Re-derive key numbers independently; flag errors >5%; check unit consistency
- (skill-gauntlet N/A: that skill evaluates skill/prompt revisions, not engineering; its rigor principles — independent blind cross-checks — are applied via the verifier instead)

## Stage 4 — Premortem (user skill: premortem-evolved)
- Full 5-stage premortem on the build-and-deploy plan per /app/.user/skills/premortem-evolved/SKILL.md + references/failure-class-checklist.md

## Stage 5 — Report (report-writing skill → .md → docx skill → .docx)
- Integrated engineering design report + premortem annex; deliver .md and .docx
