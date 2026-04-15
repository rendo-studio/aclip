from __future__ import annotations

import hashlib
import importlib
import json
import platform
import subprocess
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .app import AclipApp
from .contracts import DistributionSpec


AppFactory = Callable[[], AclipApp]
Runner = Callable[[list[str], Path], None]


@dataclass(frozen=True)
class CliArtifact:
    binary_path: Path
    manifest_path: Path
    manifest: dict


# Backward-compatible alias. Prefer CliArtifact in new code.
BinaryArtifact = CliArtifact


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
) -> CliArtifact:
    warnings.warn(
        "package_binary() is deprecated; use build_cli() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _build_binary_artifact(
        app=app,
        binary_name=binary_name,
        entry_script=entry_script,
        project_root=project_root,
        source_root=source_root,
        extra_paths=extra_paths,
        dist_dir=dist_dir,
        build_dir=build_dir,
        runner=runner,
        platform_value=platform_value,
    )


def _build_binary_artifact(
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
) -> CliArtifact:
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

    return CliArtifact(
        binary_path=binary_path,
        manifest_path=manifest_path,
        manifest=manifest,
    )


def build_cli(
    *,
    app: AclipApp,
    entry_script: Path,
    project_root: Path,
    source_root: Path | None = None,
    extra_paths: list[Path] | None = None,
    executable_name: str | None = None,
    dist_dir: Path | None = None,
    build_dir: Path | None = None,
    runner: Runner | None = None,
    platform_value: str | None = None,
) -> CliArtifact:
    project_root = project_root.resolve()
    entry_script = entry_script.resolve()
    resolved_source_root = _resolve_source_root(
        project_root=project_root,
        entry_script=entry_script,
        source_root=source_root,
    )
    resolved_extra_paths = [
        path.resolve() for path in (extra_paths or [])
    ]
    return _build_binary_artifact(
        app=app,
        binary_name=executable_name or app.name,
        entry_script=entry_script,
        project_root=project_root,
        source_root=resolved_source_root,
        extra_paths=resolved_extra_paths,
        dist_dir=dist_dir,
        build_dir=build_dir,
        runner=runner,
        platform_value=platform_value,
    )


def _default_runner(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _resolve_source_root(*, project_root: Path, entry_script: Path, source_root: Path | None) -> Path:
    if source_root is not None:
        return source_root.resolve()

    conventional_src = (project_root / "src").resolve()
    if conventional_src.exists():
        return conventional_src

    return entry_script.parent.resolve()
