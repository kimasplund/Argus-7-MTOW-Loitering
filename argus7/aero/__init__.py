"""ARGUS-7 aerodynamics.

Deliberately empty of imports: the modules in this package (buildup, and the
surrogate/panel-method modules built alongside it) are independent and are
imported by name, e.g. ``from argus7.aero import buildup``. Importing them
here would make every consumer pay for torch/neuralfoil to compute a wetted
area.
"""
