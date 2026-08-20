#!/usr/bin/env bash
# ARGUS-7 toolchain bootstrap. Each component is failure-isolated:
# one broken solver must not abort the rest of the stack.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$ROOT/logs/setup.log"; mkdir -p "$ROOT/logs" "$ROOT/vendor"
exec > >(tee -a "$LOG") 2>&1
step(){ echo; echo "===== [$(date +%H:%M:%S)] $* ====="; }
ok(){   echo "  [OK]   $*"; }
fail(){ echo "  [FAIL] $*"; }

step "APT system packages"
sudo -n apt-get update -qq
sudo -n apt-get install -y -qq \
  build-essential gfortran cmake ninja-build pkg-config \
  openscad xfoil gmsh calculix-ccx \
  libopenblas-dev liblapack-dev libx11-dev libxext-dev libplot-dev \
  libglu1-mesa-dev libgl1-mesa-dev xvfb unzip wget \
  && ok "apt packages" || fail "apt packages"

step "Python venv (3.14 primary)"
cd "$ROOT"
uv venv .venv --python 3.14 && ok "venv created" || fail "venv"
export VIRTUAL_ENV="$ROOT/.venv"

step "Python: core scientific + GPU"
uv pip install -q numpy scipy matplotlib pandas pyyaml pydantic pytest rich tqdm \
  && ok "core sci" || fail "core sci"
uv pip install -q torch --index-url https://download.pytorch.org/whl/cu128 \
  && ok "torch cu128" || fail "torch cu128"

step "Python: aero + optimisation"
for pkg in neuralfoil aerosandbox cma pymoo scikit-learn trimesh gmsh; do
  uv pip install -q "$pkg" && ok "$pkg" || fail "$pkg"
done

step "Python: CAD (build123d / OCP)"
if uv pip install -q build123d; then ok "build123d on py3.14"
else
  fail "build123d on py3.14 - falling back to dedicated 3.12 venv"
  uv venv .venv-cad --python 3.12 \
    && VIRTUAL_ENV="$ROOT/.venv-cad" uv pip install -q build123d cadquery numpy pyyaml \
    && ok "build123d in .venv-cad (py3.12)" || fail "build123d fallback"
  export VIRTUAL_ENV="$ROOT/.venv"
fi

step "AVL 3.36 (source build, MIT/Drela)"
cd "$ROOT/vendor"
if [ ! -x "$ROOT/vendor/bin/avl" ]; then
  wget -q https://web.mit.edu/drela/Public/web/avl/avl3.36.tgz -O avl.tgz \
    && tar xzf avl.tgz && cd Avl \
    && make -C plotlib gfortran \
    && make -C eispack -f Makefile.gfortran \
    && make -C bin -f Makefile.gfortran \
    && mkdir -p "$ROOT/vendor/bin" && cp bin/avl "$ROOT/vendor/bin/" \
    && ok "avl built" || fail "avl build (will retry interactively)"
else ok "avl already present"; fi

step "SU2 (prebuilt linux64 binaries)"
cd "$ROOT/vendor"
if [ ! -x "$ROOT/vendor/bin/SU2_CFD" ]; then
  SU2_URL="https://github.com/su2code/SU2/releases/download/v8.1.0/SU2-v8.1.0-linux64-mpi.zip"
  wget -q "$SU2_URL" -O su2.zip && unzip -qo su2.zip -d su2 \
    && mkdir -p "$ROOT/vendor/bin" \
    && find su2 -name 'SU2_*' -type f -exec cp {} "$ROOT/vendor/bin/" \; \
    && chmod +x "$ROOT/vendor/bin/"SU2_* \
    && ok "SU2 installed" || fail "SU2 download (check release URL)"
else ok "SU2 already present"; fi

step "VERIFY"
export PATH="$ROOT/vendor/bin:$PATH"
for t in openscad xfoil gmsh ccx avl SU2_CFD; do
  printf '  %-10s ' "$t"; command -v $t >/dev/null && echo "$(command -v $t)" || echo "MISSING"
done
"$ROOT/.venv/bin/python" -c "
import importlib
for m in ['numpy','scipy','torch','neuralfoil','aerosandbox','cma','pymoo','trimesh','gmsh','build123d']:
    try:
        importlib.import_module(m); print(f'  {m:14s} OK')
    except Exception as e: print(f'  {m:14s} MISSING ({type(e).__name__})')
import torch; print('  CUDA available:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')
" 2>&1
echo; echo "===== SETUP COMPLETE $(date +%H:%M:%S) ====="
