from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK_ROOT = EXAMPLE_ROOT.parents[1]
for path in (PYTHON_SDK_ROOT / "src", EXAMPLE_ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from aclip_demo_notes.app import create_app
from aclip import package_binary


def main() -> None:
    package_binary(
        app=create_app(),
        binary_name="aclip-demo-notes",
        entry_script=EXAMPLE_ROOT / "src" / "aclip_demo_notes" / "__main__.py",
        project_root=EXAMPLE_ROOT,
        source_root=PYTHON_SDK_ROOT / "src",
        extra_paths=[EXAMPLE_ROOT / "src"],
    )


if __name__ == "__main__":
    main()

