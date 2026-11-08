#!/usr/bin/env python3
"""Collect what the browser needs next to index.html.

Produces, in the project root:
  main.wasm    the WASI CPython interpreter
  stdlib.zip   the stdlib modules the app imports (stored, not deflated: this build has no zlib) (mounted as /lib/python<XY>.zip)
  app.zip      our own Python modules (mounted as /lib/app.zip)
"""
import pathlib
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'build' / 'cpython'
CROSS = SRC / 'cross-build' / 'wasm32-wasip1'

APP_MODULES = ['wasm_main.py', 'github.py', 'net.py', 'repo.py', 'release.py', 'constants.py']

STDLIB_MODULES = [
    '__future__', '_collections_abc', '_colorize', '_py_warnings', '_sitebuiltins',
    'annotationlib', 'ast', 'codecs', 'codeop', 'collections', 'contextlib', 'copyreg',
    'dataclasses', 'enum', 'functools', 'genericpath', 'html', 'importlib', 'json',
    'keyword', 'linecache', 'ntpath', 'operator', 'os', 'pathlib', 'posixpath', 're',
    'reprlib', 'runpy', 'site', 'stat', 'textwrap', 'token', 'tokenize', 'traceback',
    'types', 'typing', 'warnings', 'zipimport',
]
ENCODINGS = ['__init__', 'aliases', 'ascii', 'latin_1', 'utf_8', 'utf_8_sig']


def add_stdlib(zf: zipfile.ZipFile, lib: pathlib.Path) -> None:
    for name in STDLIB_MODULES:
        package = lib / name
        if package.is_dir():
            for path in sorted(package.rglob('*.py')):
                if '__pycache__' not in path.parts:
                    zf.write(path, path.relative_to(lib).as_posix())
        else:
            zf.write(lib / f'{name}.py', f'{name}.py')
    for name in ENCODINGS:
        zf.write(lib / 'encodings' / f'{name}.py', f'encodings/{name}.py')


def main() -> None:
    wasm = CROSS / 'python.wasm'
    if not wasm.is_file():
        sys.exit(f'{wasm} not found; run scripts/setup-wasi.sh first')

    shutil.copyfile(wasm, ROOT / 'main.wasm')

    with zipfile.ZipFile(ROOT / 'stdlib.zip', 'w', zipfile.ZIP_STORED) as zf:
        add_stdlib(zf, SRC / 'Lib')
        for data in CROSS.glob('build/lib.*/_sysconfigdata_*.py'):
            zf.write(data, data.name)

    with zipfile.ZipFile(ROOT / 'app.zip', 'w', zipfile.ZIP_STORED) as zf:
        for name in APP_MODULES:
            zf.write(ROOT / name, name)

    for name in ('main.wasm', 'stdlib.zip', 'app.zip'):
        print(f'{name}: {(ROOT / name).stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
