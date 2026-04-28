from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK_ROOT = EXAMPLE_ROOT.parents[1]
for path in (PYTHON_SDK_ROOT / "src", EXAMPLE_ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import aclip
from aclip_demo_notes.app import create_app


def main() -> None:
    app = create_app()
    skills_root = EXAMPLE_ROOT / "skills"
    app.add_cli_skill(skills_root / "notes-overview")
    app.add_command_skill(("note", "create"), skills_root / "note-create-best-practice")
    artifact = aclip.export_skills(app, output_dir=EXAMPLE_ROOT / "dist" / "skills")
    print(artifact.index_path)


if __name__ == "__main__":
    main()
