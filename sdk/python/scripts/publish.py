from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import tomllib
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PACKAGE_ROOT / "dist"
PYPROJECT_PATH = PACKAGE_ROOT / "pyproject.toml"
CANONICAL_NAME = "rendo-aclip"
ALIAS_NAME = "aclip"


def run(command: list[str], *, cwd: Path = PACKAGE_ROOT, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def load_project_metadata() -> dict:
    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def project_version() -> str:
    return str(load_project_metadata()["project"]["version"])


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def build_canonical() -> None:
    run([sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(DIST_DIR)])


def alias_readme(version: str) -> str:
    return textwrap.dedent(
        f"""\
        # aclip

        `aclip` is the official short-name Python package for ACLIP.

        It is published in lockstep with `rendo-aclip` and installs the same SDK release.

        Use `aclip` if you want the shortest install command.
        Use `rendo-aclip` if you want the canonical dependency name in project manifests.

        ## Install

        Short-name install:

        ```bash
        pip install aclip
        ```

        Canonical install:

        ```bash
        pip install rendo-aclip
        ```

        Either way, the import path is:

        ```python
        from aclip import AclipApp
        ```

        ## What ACLIP gives you

        - natural CLI invocation
        - progressive Markdown help
        - structured result and error envelopes
        - sidecar manifests for distribution metadata
        - packaging helpers for shipping binary CLIs

        ## First Working CLI

        ```python
        from __future__ import annotations

        import sys

        from aclip import AclipApp


        app = AclipApp(
            name="notes",
            version="{version}",
            summary="A minimal notes CLI.",
            description="Create and list notes from a small local CLI.",
        )

        note = app.group(
            "note",
            summary="Manage notes",
            description="Create and inspect notes.",
        )


        @note.command(
            "create",
            summary="Create a note",
            examples=["notes note create --title hello --body world"],
        )
        def create(title: str, body: str) -> dict:
            \"\"\"Create a note.

            Args:
                title: Title for the note.
                body: Body text for the note.
            \"\"\"
            return {{"note": {{"title": title, "body": body}}}}


        if __name__ == "__main__":
            raise SystemExit(app.run(sys.argv[1:]))
        ```

        Typical usage:

        ```bash
        notes --help
        notes note --help
        notes note create --help
        notes note create --title hello --body world
        ```

        Installing `aclip` installs `rendo-aclip=={version}`.
        """
    )


def alias_pyproject(version: str) -> str:
    return textwrap.dedent(
        f"""\
        [build-system]
        requires = ["setuptools>=69", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{ALIAS_NAME}"
        version = "{version}"
        description = "Synchronized alias package for rendo-aclip"
        readme = "README.md"
        requires-python = ">=3.12"
        license = "MIT"
        authors = [{{ name = "Rendo Studio" }}]
        keywords = ["aclip", "alias", "rendo", "sdk"]
        classifiers = [
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.12",
          "Topic :: Software Development :: Libraries",
        ]
        dependencies = [
          "{CANONICAL_NAME}=={version}",
        ]
        """
    )


def build_alias() -> None:
    version = project_version()
    with tempfile.TemporaryDirectory(prefix="aclip-publish-") as temp_dir:
        temp_root = Path(temp_dir)
        (temp_root / "README.md").write_text(alias_readme(version), encoding="utf-8")
        (temp_root / "pyproject.toml").write_text(alias_pyproject(version), encoding="utf-8")
        run([sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(DIST_DIR)], cwd=temp_root)


def build_all() -> None:
    clean_dist()
    build_canonical()
    build_alias()


def dist_files() -> list[str]:
    files = sorted(str(path) for path in DIST_DIR.iterdir() if path.is_file())
    if not files:
        raise SystemExit("No distribution files were built.")
    return files


def check() -> None:
    build_all()
    run([sys.executable, "-m", "twine", "check", *dist_files()])


def publish() -> None:
    token = os.environ.get("PYPI_TOKEN")
    if not token:
        raise SystemExit("PYPI_TOKEN is required. PyPI no longer supports username/password uploads.")
    check()
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    run(
        [sys.executable, "-m", "twine", "upload", "--non-interactive", "--skip-existing", *dist_files()],
        env=env,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and publish the ACLIP Python SDK.")
    parser.add_argument("command", choices=("check", "publish"))
    args = parser.parse_args()

    if args.command == "check":
        check()
        return
    if args.command == "publish":
        publish()
        return


if __name__ == "__main__":
    main()
