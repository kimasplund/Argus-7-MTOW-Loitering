"""Regenerate every CAD artifact from design/argus7_v1.yaml."""
from pathlib import Path
from argus7.design.schema import load_design
from argus7.cad.export import export_model, check_watertight
from argus7.cad.to_openscad import emit_openscad
from argus7.cad.render import render_views


def main(design_path="design/argus7_v1.yaml"):
    design = load_design(design_path)
    paths = export_model(design, Path("model"))
    scad = emit_openscad(design, Path("model/argus7_model.scad"))
    print(f"STEP {paths['step']}\nSTL  {paths['stl']}\nSCAD {scad}")
    print(f"watertight: {check_watertight(paths['stl'])}")
    for p in render_views(scad, Path("figures/cad")):
        print(f"render {p}")


if __name__ == "__main__":
    main()
