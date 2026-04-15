from __future__ import annotations

import hashlib
import importlib
import inspect
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
FactoryTarget = str | AppFactory
Runner = Callable[[list[str], Path], None]


@dataclass(frozen=True)
class CliArtifact:
    binary_path: Path
    manifest_path: Path
    manifest: dict


@dataclass(frozen=True)
class AppFactoryInfo:
    target: str
    factory: AppFactory
    module_file: Path


@dataclass(frozen=True)
class AppTargetInfo:
    target: str
    app: AclipApp
    module_file: Path


def inspect_app_factory(target: str) -> AppFactoryInfo:
    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError("app factory must use the form 'module.path:callable_name'")

    module = importlib.import_module(module_name)
    factory = getattr(module, attr_name)
    if not callable(factory):
        raise ValueError("app factory target must be callable")

    module_file = getattr(module, "__file__", None)
    if module_file is None:
        raise ValueError("app factory module must resolve to a file-backed module")

    return AppFactoryInfo(
        target=target,
        factory=factory,
        module_file=Path(module_file).resolve(),
    )


def load_app_factory(target: str) -> AppFactory:
    return inspect_app_factory(target).factory


def load_app_target(target: str) -> AclipApp:
    return inspect_app_target(target).app


def build_cli(
    target: FactoryTarget | None = None,
    *,
    factory: FactoryTarget | None = None,
    app_factory: FactoryTarget | None = None,
    project_root: Path | None = None,
    source_root: Path | None = None,
    extra_paths: list[Path] | None = None,
    executable_name: str | None = None,
    dist_dir: Path | None = None,
    build_dir: Path | None = None,
    runner: Runner | None = None,
    platform_value: str | None = None,
) -> CliArtifact:
    factory_info = _resolve_factory_target(
        target=target,
        factory=factory,
        app_factory=app_factory,
    )
    resolved_app = factory_info.app
    resolved_project_root = _resolve_project_root(
        module_file=factory_info.module_file,
        project_root=project_root,
    )
    resolved_source_root = _resolve_source_root(
        module_file=factory_info.module_file,
        project_root=resolved_project_root,
        source_root=source_root,
    )
    resolved_build_dir = (build_dir or resolved_project_root / "build").resolve()
    resolved_build_dir.mkdir(parents=True, exist_ok=True)
    launcher_script = _write_launcher_script(resolved_build_dir, factory_info.target)
    resolved_extra_paths = _resolve_extra_paths(
        source_root=resolved_source_root,
        extra_paths=extra_paths,
    )

    try:
        return _build_binary_artifact(
            app=resolved_app,
            binary_name=executable_name or resolved_app.name,
            hidden_imports=[factory_info.target.partition(":")[0]],
            entry_script=launcher_script,
            project_root=resolved_project_root,
            source_root=resolved_source_root,
            extra_paths=resolved_extra_paths,
            dist_dir=dist_dir,
            build_dir=resolved_build_dir,
            runner=runner,
            platform_value=platform_value,
        )
    finally:
        launcher_script.unlink(missing_ok=True)


def _build_binary_artifact(
    *,
    app: AclipApp,
    binary_name: str,
    hidden_imports: list[str] | None = None,
    entry_script: Path,
    project_root: Path,
    source_root: Path,
    extra_paths: list[Path] | None = None,
    dist_dir: Path | None = None,
    build_dir: Path | None = None,
    runner: Runner | None = None,
    platform_value: str | None = None,
) -> CliArtifact:
    dist_dir = (dist_dir or project_root / "dist").resolve()
    build_dir = (build_dir or project_root / "build").resolve()
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
    for module_name in hidden_imports or []:
        command.extend(["--hidden-import", module_name])
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


def _resolve_factory_target(
    *,
    target: FactoryTarget | None,
    factory: FactoryTarget | None,
    app_factory: FactoryTarget | None,
) -> AppTargetInfo:
    candidates = [value for value in (target, factory, app_factory) if value is not None]
    if len(candidates) != 1:
        raise ValueError("build_cli requires exactly one factory target")

    selected = candidates[0]
    if isinstance(selected, str):
        return inspect_app_target(selected)
    return inspect_factory_callable(selected)


def inspect_factory_callable(factory: AppFactory) -> AppTargetInfo:
    if not callable(factory):
        raise ValueError("factory target must be callable")

    factory_name = getattr(factory, "__name__", "")
    factory_qualname = getattr(factory, "__qualname__", "")
    module_name = getattr(factory, "__module__", "")
    if not module_name or not factory_name:
        raise ValueError("factory target must expose __module__ and __name__")
    if factory_name == "<lambda>" or "<locals>" in factory_qualname:
        raise ValueError("factory target must be a top-level named callable")
    if not inspect.isfunction(factory):
        raise ValueError("factory target must be a top-level function")

    module = importlib.import_module(module_name)
    exported = getattr(module, factory_name, None)
    if exported is not factory:
        raise ValueError("factory target must be directly exported from its module")

    module_file = getattr(module, "__file__", None)
    if module_file is None:
        raise ValueError("factory target module must resolve to a file-backed module")

    return AppTargetInfo(
        target=f"{module_name}:{factory_name}",
        app=factory(),
        module_file=Path(module_file).resolve(),
    )


def inspect_app_target(target: str) -> AppTargetInfo:
    module_name, _, attr_name = target.partition(":")
    if not module_name or not attr_name:
        raise ValueError("app target must use the form 'module.path:attribute_name'")

    module = importlib.import_module(module_name)
    exported = getattr(module, attr_name)
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        raise ValueError("app target module must resolve to a file-backed module")

    if callable(exported):
        app = exported()
    else:
        app = exported

    if not isinstance(app, AclipApp):
        raise ValueError("app target must resolve to an AclipApp instance or no-arg factory")

    return AppTargetInfo(
        target=target,
        app=app,
        module_file=Path(module_file).resolve(),
    )


def _default_runner(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _resolve_project_root(*, module_file: Path, project_root: Path | None) -> Path:
    if project_root is not None:
        return project_root.resolve()

    current = module_file.parent
    for ancestor in [current, *current.parents]:
        if ancestor.name == "src":
            return ancestor.parent.resolve()
        if (ancestor / "pyproject.toml").exists():
            return ancestor.resolve()

    return current.resolve()


def _resolve_source_root(*, module_file: Path, project_root: Path, source_root: Path | None) -> Path:
    if source_root is not None:
        return source_root.resolve()

    conventional_src = (project_root / "src").resolve()
    if conventional_src.exists():
        return conventional_src

    for ancestor in [module_file.parent, *module_file.parents]:
        if ancestor.name == "src":
            return ancestor.resolve()

    return project_root


def _resolve_extra_paths(*, source_root: Path, extra_paths: list[Path] | None) -> list[Path]:
    resolved_paths: list[Path] = []
    seen: set[Path] = set()

    for path in (extra_paths or []):
        resolved = path.resolve()
        if resolved not in seen and resolved != source_root:
            seen.add(resolved)
            resolved_paths.append(resolved)

    sdk_source_root = _current_sdk_source_root()
    if (
        sdk_source_root is not None
        and sdk_source_root not in seen
        and sdk_source_root != source_root
    ):
        resolved_paths.append(sdk_source_root)

    return resolved_paths


def _current_sdk_source_root() -> Path | None:
    current_source_root = Path(__file__).resolve().parents[1]
    if current_source_root.name != "src":
        return None
    if "site-packages" in current_source_root.parts or "dist-packages" in current_source_root.parts:
        return None
    if not (current_source_root / "aclip").exists():
        return None
    return current_source_root


def _write_launcher_script(build_dir: Path, app_factory: str) -> Path:
    module_name, _, attr_name = app_factory.partition(":")
    launcher_path = build_dir / "_aclip_build_launcher.py"
    launcher_path.write_text(
        "\n".join(
            [
                "from aclip import cli_main",
                f"from {module_name} import {attr_name} as __aclip_target",
                "",
                "cli_main(__aclip_target)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return launcher_path


build = build_cli
