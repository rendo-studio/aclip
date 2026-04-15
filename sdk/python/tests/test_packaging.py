import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import validate

from aclip_demo_notes.app import create_app
from aclip import DistributionSpec
from aclip.packaging import load_app_factory, package_binary
from aclip.schema import load_schema


def test_load_app_factory_resolves_module_factory_string():
    factory = load_app_factory("aclip_demo_notes.app:create_app")
    app = factory()

    assert app.name == "aclip-demo-notes"


def test_package_binary_invokes_runner_and_writes_manifest(tmp_path: Path):
    project_root = tmp_path
    source_root = project_root / "src"
    source_root.mkdir()
    example_root = project_root / "examples" / "demo-notes" / "src"
    example_root.mkdir(parents=True)
    entry_script = source_root / "demo_main.py"
    entry_script.write_text("print('demo')", encoding="utf-8")

    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    binary_name = "demo.exe"

    def fake_runner(command: list[str], cwd: Path) -> None:
        assert command[0].endswith("python.exe") or command[0].endswith("python")
        assert command[1:5] == ["-m", "PyInstaller", "--noconfirm", "--clean"]
        assert command.count("--paths") == 2
        assert str(source_root) in command
        assert str(example_root) in command
        assert cwd == project_root
        dist_dir.mkdir(exist_ok=True)
        (dist_dir / binary_name).write_bytes(b"demo-binary")

    artifact = package_binary(
        app=create_app(),
        binary_name="demo",
        entry_script=entry_script,
        project_root=project_root,
        source_root=source_root,
        extra_paths=[example_root],
        dist_dir=dist_dir,
        build_dir=build_dir,
        runner=fake_runner,
        platform_value="windows-x64",
    )

    assert artifact.binary_path == dist_dir / binary_name
    assert artifact.manifest_path == dist_dir / "demo.aclip.json"

    manifest = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "demo"
    assert manifest["distribution"] == [
        {
            "kind": "standalone_binary",
            "binary": "demo.exe",
            "platform": "windows-x64",
            "sha256": hashlib.sha256(b"demo-binary").hexdigest(),
        }
    ]
    validate(manifest, load_schema("manifest"))


def test_repository_layout_places_python_sdk_under_sdk_directory():
    root = Path(__file__).resolve().parents[1]

    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "aclip").exists()
    assert (root / "examples" / "demo-notes" / "src" / "aclip_demo_notes").exists()


def test_package_cli_help_is_available():
    root = Path(__file__).resolve().parents[1]
    pythonpath = str(root / "src") + ";" + str(root / "examples" / "demo-notes" / "src")
    result = subprocess.run(
        [sys.executable, "-m", "aclip.package_cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": (
                pythonpath
                if "PYTHONPATH" not in os.environ
                else pythonpath + ";" + os.environ["PYTHONPATH"]
            ),
        },
    )

    assert result.returncode == 0
    assert "--app-factory" in result.stdout


def test_distribution_spec_can_emit_npm_package_manifest():
    distribution = DistributionSpec.npm_package(
        package="@aclip/demo-notes",
        version="0.1.0",
        executable="aclip-demo-notes",
    )

    assert distribution.to_manifest() == {
        "kind": "npm_package",
        "package": "@aclip/demo-notes",
        "version": "0.1.0",
        "executable": "aclip-demo-notes",
    }

