from __future__ import annotations

import argparse
from pathlib import Path

from .packaging import load_app_factory, package_binary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="aclip-package")
    parser.add_argument("--app-factory", required=True)
    parser.add_argument("--entry-script", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source-root", default="src")
    parser.add_argument("--extra-path", dest="extra_paths", action="append", default=[])
    parser.add_argument("--dist-dir", default=None)
    parser.add_argument("--build-dir", default=None)
    parser.add_argument("--platform", dest="platform_value", default=None)
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
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
        entry_script = (project_root / entry_script).resolve()
    dist_dir = None if args.dist_dir is None else (project_root / args.dist_dir).resolve()
    build_dir = None if args.build_dir is None else (project_root / args.build_dir).resolve()

    factory = load_app_factory(args.app_factory)
    artifact = package_binary(
        app=factory(),
        binary_name=args.name,
        entry_script=entry_script,
        project_root=project_root,
        source_root=source_root,
        extra_paths=extra_paths,
        dist_dir=dist_dir,
        build_dir=build_dir,
        platform_value=args.platform_value,
    )
    print(artifact.binary_path)
    print(artifact.manifest_path)


if __name__ == "__main__":
    main()
