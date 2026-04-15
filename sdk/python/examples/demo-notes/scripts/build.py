from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK_ROOT = EXAMPLE_ROOT.parents[1]
for path in (PYTHON_SDK_ROOT / "src", EXAMPLE_ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from aclip import build_cli


def main() -> None:
    build_cli(app_factory="aclip_demo_notes.app:create_app")


if __name__ == "__main__":
    main()
