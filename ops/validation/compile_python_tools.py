from __future__ import annotations

import argparse
import compileall
import shutil
from pathlib import Path


def _clean_pycache(target: Path) -> None:
    for cache_dir in target.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
    for pyc in target.rglob("*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass


def compile_python_tools(paths: list[Path]) -> int:
    success = True
    for path in paths:
        resolved = path.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        _clean_pycache(resolved)
        success = compileall.compile_dir(str(resolved), force=True, quiet=1) and success
    return 0 if success else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean stale Python caches and compile ATLAS tool directories.")
    parser.add_argument("--path", action="append", required=True, type=Path)
    args = parser.parse_args(argv)
    return compile_python_tools(list(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
