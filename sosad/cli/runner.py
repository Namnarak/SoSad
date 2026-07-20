"""CLI runner — python -m sosad entry point."""

from __future__ import annotations

import argparse

from sosad._meta import __version__


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sosad",
        description="SoSad Discord Framework",
    )
    parser.add_argument("--version", action="version", version=f"SoSad {__version__}")
    parser.add_argument(
        "module",
        help="Python module to run (e.g., bot:app)",
    )
    args = parser.parse_args()

    print(f"SoSad v{__version__}")
    print(f"Running: {args.module}")
    # Future: import and run the module


if __name__ == "__main__":
    main()
