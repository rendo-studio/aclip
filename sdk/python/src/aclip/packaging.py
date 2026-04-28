from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .app import AclipApp
from .contracts import CliSkillHook, CommandSkillHook, DistributionSpec


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


@dataclass(frozen=True)
class ExportedSkillPackage:
    name: str
    kind: str
    source_dir: Path
    output_dir: Path
    command_path: str | None = None


@dataclass(frozen=True)
class SkillExportArtifact:
    output_dir: Path
    index_path: Path
    index: dict[str, Any]
    packages: list[ExportedSkillPackage]


@dataclass(frozen=True)
class SkillFrontmatter:
    name: str
    description: str
    metadata: dict[str, str]
    compatibility: str | None = None
    license: str | None = None
    allowed_tools: str | None = None
    extras: dict[str, str] | None = None


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
            binary_name=resolved_app.name,
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

    original_pythonpath = os.environ.get("PYTHONPATH")
    pythonpath_entries = [str(source_root), *(str(path) for path in (extra_paths or []))]
    if original_pythonpath:
        pythonpath_entries.append(original_pythonpath)
    os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    try:
        runner(command, project_root)
    finally:
        if original_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = original_pythonpath

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


def export_skills(app: AclipApp, *, output_dir: Path | str) -> SkillExportArtifact:
    resolved_output_dir = Path(output_dir).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    app_version = _require_app_version(app, "exporting skills")

    exported_packages: list[ExportedSkillPackage] = []
    seen_names: set[str] = set()

    for hook in app.cli_skills:
        exported_packages.append(
            _export_skill_package(
                app=app,
                hook=hook,
                kind="cli",
                output_dir=resolved_output_dir,
                seen_names=seen_names,
            )
        )
    for hook in app.command_skills:
        exported_packages.append(
            _export_skill_package(
                app=app,
                hook=hook,
                kind="command",
                output_dir=resolved_output_dir,
                seen_names=seen_names,
            )
        )

    index = {
        "protocol": "aclip-skill-export/0.1",
        "cli": {
            "name": app.name,
            "version": app_version,
        },
        "packages": [
            {
                "name": package.name,
                "kind": package.kind,
                "path": package.output_dir.name,
                **(
                    {"commandPath": package.command_path}
                    if package.command_path is not None
                    else {}
                ),
            }
            for package in exported_packages
        ],
    }
    index_path = resolved_output_dir / "skills.aclip.json"
    index_path.write_text(json.dumps(index, ensure_ascii=True, indent=2), encoding="utf-8")
    return SkillExportArtifact(
        output_dir=resolved_output_dir,
        index_path=index_path,
        index=index,
        packages=exported_packages,
    )


def _export_skill_package(
    *,
    app: AclipApp,
    hook: CliSkillHook | CommandSkillHook,
    kind: str,
    output_dir: Path,
    seen_names: set[str],
) -> ExportedSkillPackage:
    source_dir = Path(hook.source_dir).resolve()
    skill_markdown_path = source_dir / "SKILL.md"
    if not skill_markdown_path.exists():
        raise ValueError(f"skill package must contain SKILL.md: {source_dir}")

    frontmatter, body = _parse_skill_markdown(skill_markdown_path.read_text(encoding="utf-8"))
    _validate_skill_frontmatter(frontmatter)

    if frontmatter.name in seen_names:
        raise ValueError(f"duplicate exported skill package name: {frontmatter.name}")
    seen_names.add(frontmatter.name)

    generated_metadata = {
        "aclip-hook-kind": kind,
        "aclip-cli-name": app.name,
        "aclip-cli-version": _require_app_version(app, "exporting skills"),
    }
    command_path: str | None = None
    if _has_group(app, "auth"):
        generated_metadata["aclip-auth-group"] = "auth"
    if _has_group(app, "doctor"):
        generated_metadata["aclip-doctor-group"] = "doctor"

    if isinstance(hook, CommandSkillHook):
        command = _find_command(app, hook.command_path)
        command_path = command.command_name()
        generated_metadata.update(
            {
                "aclip-command-path": command_path,
                "aclip-command-summary": command.summary,
                "aclip-command-description": command.description,
            }
        )

    merged_metadata = dict(frontmatter.metadata)
    merged_metadata.update(hook.metadata)
    merged_metadata.update(generated_metadata)
    exported_frontmatter = SkillFrontmatter(
        name=frontmatter.name,
        description=frontmatter.description,
        metadata=merged_metadata,
        compatibility=frontmatter.compatibility,
        license=frontmatter.license,
        allowed_tools=frontmatter.allowed_tools,
        extras=dict(frontmatter.extras or {}),
    )

    destination_dir = output_dir / frontmatter.name
    if destination_dir.exists():
        shutil.rmtree(destination_dir)
    shutil.copytree(source_dir, destination_dir)
    (destination_dir / "SKILL.md").write_text(
        _render_skill_markdown(exported_frontmatter, body),
        encoding="utf-8",
    )

    return ExportedSkillPackage(
        name=frontmatter.name,
        kind=kind,
        source_dir=source_dir,
        output_dir=destination_dir,
        command_path=command_path,
    )


def _require_app_version(app: AclipApp, context: str) -> str:
    version = getattr(app, "version", None)
    if version is None or not str(version).strip():
        raise ValueError(f"version is required when {context}")
    return str(version)


def _parse_skill_markdown(text: str) -> tuple[SkillFrontmatter, str]:
    match = re.match(r"\A---\r?\n(?P<frontmatter>.*?)\r?\n---\r?\n?(?P<body>.*)\Z", text, re.S)
    if not match:
        raise ValueError("SKILL.md must begin with YAML frontmatter")

    raw_frontmatter = match.group("frontmatter").splitlines()
    parsed: dict[str, str] = {}
    metadata: dict[str, str] = {}
    extras: dict[str, str] = {}
    index = 0
    while index < len(raw_frontmatter):
        line = raw_frontmatter[index]
        if not line.strip():
            index += 1
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if key == "metadata":
            index += 1
            while index < len(raw_frontmatter) and raw_frontmatter[index].startswith("  "):
                metadata_line = raw_frontmatter[index].strip()
                if ":" not in metadata_line:
                    raise ValueError(f"invalid metadata line: {metadata_line}")
                metadata_key, metadata_value = metadata_line.split(":", 1)
                metadata[metadata_key.strip()] = _parse_frontmatter_scalar(metadata_value.strip())
                index += 1
            continue
        parsed[key] = _parse_frontmatter_scalar(value)
        index += 1

    for key, value in parsed.items():
        if key not in {"name", "description", "compatibility", "license", "allowed-tools"}:
            extras[key] = value

    return (
        SkillFrontmatter(
            name=parsed.get("name", ""),
            description=parsed.get("description", ""),
            metadata=metadata,
            compatibility=parsed.get("compatibility"),
            license=parsed.get("license"),
            allowed_tools=parsed.get("allowed-tools"),
            extras=extras,
        ),
        match.group("body"),
    )


def _render_skill_markdown(frontmatter: SkillFrontmatter, body: str) -> str:
    lines = ["---"]
    lines.append(f"name: {_render_frontmatter_scalar(frontmatter.name)}")
    lines.append(f"description: {_render_frontmatter_scalar(frontmatter.description)}")
    if frontmatter.license is not None:
        lines.append(f"license: {_render_frontmatter_scalar(frontmatter.license)}")
    if frontmatter.compatibility is not None:
        lines.append(f"compatibility: {_render_frontmatter_scalar(frontmatter.compatibility)}")
    if frontmatter.allowed_tools is not None:
        lines.append(f"allowed-tools: {_render_frontmatter_scalar(frontmatter.allowed_tools)}")
    for key, value in sorted((frontmatter.extras or {}).items()):
        lines.append(f"{key}: {_render_frontmatter_scalar(value)}")
    if frontmatter.metadata:
        lines.append("metadata:")
        for key, value in sorted(frontmatter.metadata.items()):
            lines.append(f"  {key}: {_render_frontmatter_scalar(value)}")
    lines.append("---")
    lines.append("")
    lines.append(body.lstrip("\r\n"))
    return "\n".join(lines)


def _validate_skill_frontmatter(frontmatter: SkillFrontmatter) -> None:
    if not frontmatter.name:
        raise ValueError("skill package frontmatter must define name")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", frontmatter.name):
        raise ValueError("skill package name must use lowercase kebab-case")
    if not frontmatter.description:
        raise ValueError("skill package frontmatter must define description")


def _parse_frontmatter_scalar(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def _render_frontmatter_scalar(value: str) -> str:
    if not value:
        return '""'
    if re.fullmatch(r"[A-Za-z0-9._/@ -]+", value) and ":" not in value:
        return value
    return json.dumps(value, ensure_ascii=True)


def _has_group(app: AclipApp, group_name: str) -> bool:
    return any(command_group.path == (group_name,) for command_group in app.command_groups)


def _find_command(app: AclipApp, command_path: tuple[str, ...]):
    for command in app.commands:
        if command.path == command_path:
            return command
    raise ValueError(f"unknown command path for skill export: {' '.join(command_path)}")


build = build_cli
