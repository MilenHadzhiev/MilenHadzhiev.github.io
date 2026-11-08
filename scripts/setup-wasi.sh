#!/usr/bin/env bash
# Download the WASI toolchain into the venv, fetch the CPython source and
# cross-compile CPython to WebAssembly (wasm32-wasip1).
#
# Usage: scripts/setup-wasi.sh [--quiet]
#   --quiet   send build output to build/logs instead of the terminal
set -euo pipefail

# Versions: CPython comes from .python-version, and the WASI SDK major version
# must match the one pinned in the CPython checkout (Platforms/WASI/config.toml).
WASI_SDK_VERSION=33
WASMTIME_VERSION=50.0.1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/venv"
BUILD="$ROOT/build"
CPYTHON_VERSION="$(tr -d '[:space:]' < "$ROOT/.python-version")"
CPYTHON_SRC="$BUILD/cpython"

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "error: $VENV not found; create the venv first (python -m venv venv)" >&2
    exit 1
fi

QUIET_ARGS=()
if [[ "${1:-}" == "--quiet" ]]; then
    mkdir -p "$BUILD/logs"
    QUIET_ARGS=(--quiet --logdir "$BUILD/logs")
fi

# 1. WASI SDK -> venv/wasi-sdk
if [[ ! -x "$VENV/wasi-sdk/bin/clang" ]]; then
    echo ">> Downloading WASI SDK $WASI_SDK_VERSION"
    mkdir -p "$VENV/wasi-sdk"
    curl -fsSL "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-$WASI_SDK_VERSION/wasi-sdk-$WASI_SDK_VERSION.0-x86_64-linux.tar.gz" \
        | tar xz -C "$VENV/wasi-sdk" --strip-components=1
else
    echo ">> WASI SDK already installed, skipping"
fi

# 2. wasmtime CLI -> venv/bin/wasmtime
if [[ ! -x "$VENV/bin/wasmtime" ]]; then
    echo ">> Downloading wasmtime $WASMTIME_VERSION"
    dir="wasmtime-v$WASMTIME_VERSION-x86_64-linux"
    curl -fsSL "https://github.com/bytecodealliance/wasmtime/releases/download/v$WASMTIME_VERSION/$dir.tar.xz" \
        | tar xJ -C "$VENV/bin" --strip-components=1 "$dir/wasmtime"
else
    echo ">> wasmtime already installed, skipping"
fi

# 3. CPython source at the tag matching .python-version
if [[ ! -d "$CPYTHON_SRC" ]]; then
    echo ">> Cloning CPython v$CPYTHON_VERSION"
    mkdir -p "$BUILD"
    git clone --branch "v$CPYTHON_VERSION" --depth 1 https://github.com/python/cpython "$CPYTHON_SRC"
else
    echo ">> CPython source already present, skipping clone"
fi

# 4. Build the native "build Python", then cross-compile for WASI
export WASI_SDK_PATH="$VENV/wasi-sdk"
export PATH="$VENV/bin:$PATH"

echo ">> Building CPython for WASI (this takes a while)"
cd "$CPYTHON_SRC"
"$VENV/bin/python" Platforms/WASI build "${QUIET_ARGS[@]}"

echo ">> Done. Run it with: $CPYTHON_SRC/cross-build/wasm32-wasip1/python.sh --version"
