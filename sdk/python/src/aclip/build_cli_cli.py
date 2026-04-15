from __future__ import annotations

import argparse
from pathlib import Path

from .packaging import build_cli, load_app_factory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="aclip-build-cli")
    parser.add_argument("--app-factory", required=True, help="Import target in the form 'module.path:factory_name'.")
    parser.add_argument("--entry-script", required=True, help="CLI entry script that should be frozen into the distributable.")
    parser.add_argument("--name", default=None, help="Executable name. Defaults to the ACLIP app name.")
    parser.add_argument("--project-root", default=".", help="Project root used to resolve relative inputs.")
    parser.add_argument("--source-root", default=None, help="Import root passed through to PyInstaller. Defaults to <project-root>/src when present.")
    parser.add_argument("--extra-path", dest="extra_paths", action="append", default=[], help="Additional import roots to add during packaging. Repeat for multiple paths.")
    parser.add_argument("--dist-dir", default=None, help="Output directory for the packaged executable and manifest.")
    parser.add_argument("--build-dir", default=None, help="Temporary build directory used by PyInstaller.")
    parser.add_argument("--platform", dest="platform_value", default=None, help="Platform identifier recorded in the sidecar manifest.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    source_root = None
    if args.source_root is not None:
        source_root = Path(args.source_root)
        if not source_root.is_absolute():
            source_root = (project_root / source_root).resolve()
    extra_paths: list[Path] = []
    for extra_path in args.extra_paths:
        path = Path(extra_path)
        if not path.is_absolute():
            path = (project_root / path).resolve()
        extra_paths.append(path)
    entry_script = Path(args.entry_script)
    if not entry_script.is_absolute():
        entry_script = (project_root / args.entry_script).resolve()
    dist_dir = None if args.dist_dir is None else (project_root / args.dist_dir).resolve()
    build_dir = None if args.build_dir is None else (project_root / args.build_dir).resolve()

    factory = load_app_factory(args.app_factory)
    artifact = build_cli(
        app=factory(),
        entry_script=entry_script,
        project_root=project_root,
        source_root=source_root,
        extra_paths=extra_paths,
        executable_name=args.name,
        dist_dir=dist_dir,
        build_dir=build_dir,
        platform_value=args.platform_value,
    )
    print(artifact.binary_path)
    print(artifact.manifest_path)


if __name__ == "__main__":
    main()
