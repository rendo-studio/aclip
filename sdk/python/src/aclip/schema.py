from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_SCHEMA_DIR = Path(__file__).resolve().parents[4] / "schema"
PACKAGE_SCHEMA_DIR = PACKAGE_ROOT / "_schema"


def load_schema(name: str) -> dict[str, Any]:
    filename = f"{name}.schema.json"
    for schema_dir in (REPO_SCHEMA_DIR, PACKAGE_SCHEMA_DIR):
        path = schema_dir / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"ACLIP schema not found: {filename}")
