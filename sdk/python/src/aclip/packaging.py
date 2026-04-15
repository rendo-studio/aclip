from __future__ import annotations

import hashlib
import importlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .app import AclipApp
from .contracts import DistributionSpec


AppFactory = Callable[[], AclipApp]
Runner = Callable[[list[str], Path], None]


@dataclass(frozen=True)
class BinaryArtifact:
    binary_path: Path
    manifest_path: Path
    manifest: dict


def load_app_factory(target: str) -> AppFactory:
    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError("app factory must use the form 'module.path:callable_name'")
    module = importlib.import_module(module_name)
    factory = getattr(module, attr_name)
    if not callable(factory):
        raise ValueError("app factory target must be callable")
    return factory


def package_binary(
    *,
    app: AclipApp,
    binary_name: str,
    entry_script: Path,
    project_root: Path,
    source_root: Path,
    extra_paths: list[Path] | None = None,
    dist_dir: Path | None = None,
    build_dir: Path | None = None,
    runner: Runner | None = None,
    platform_value: str | None = None,
) -> BinaryArtifact:
    dist_dir = dist_dir or project_root / "dist"
    build_dir = build_dir or project_root / "build"
    dist_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    runner = runner or _default_runner
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        binary_name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(build_dir),
    ]
    for path in [source_root, *(extra_paths or [])]:
        command.extend(["--paths", str(path)])
    command.append(str(entry_script))

    runner(command, project_root)

    binary_filename = f"{binary_name}.exe" if sys.platform.startswith("win") else binary_name
    binary_path = dist_dir / binary_filename
    digest = hashlib.sha256(binary_path.read_bytes()).hexdigest()
    manifest = app.build_index_manifest(
        binary_name=binary_name,
        distribution=[
            DistributionSpec.standalone_binary(
                binary=binary_path.name,
                platform=platform_value or f"{sys.platform}-{platform.machine().lower()}",
                sha256=digest,
            )
        ],
    )
    manifest_path = dist_dir / f"{binary_name}.aclip.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

    return BinaryArtifact(
        binary_path=binary_path,
        manifest_path=manifest_path,
        manifest=manifest,
    )


def _default_runner(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)
