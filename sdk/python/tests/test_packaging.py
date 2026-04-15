import hashlib
import json
import sys
import tomllib
from pathlib import Path

from jsonschema import validate

from aclip_demo_notes.app import create_app
from aclip import AclipApp, DistributionSpec, build, cli_main
from aclip.packaging import build_cli, inspect_app_factory, load_app_factory, load_app_target
from aclip.schema import load_schema


def test_load_app_factory_resolves_module_factory_string():
    factory = load_app_factory("aclip_demo_notes.app:create_app")
    app = factory()

    assert app.name == "aclip-demo-notes"


def test_build_cli_accepts_factory_callable_and_includes_hidden_import(tmp_path: Path):
    project_root = tmp_path
    source_root = project_root / "src"
    source_root.mkdir()
    extra_root = project_root / "shared"
    extra_root.mkdir()
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    binary_name = "aclip-demo-notes.exe"
    launcher_script: Path | None = None

    def fake_runner(command: list[str], cwd: Path) -> None:
        nonlocal launcher_script
        assert command[0].endswith("python.exe") or command[0].endswith("python")
        assert command[1:5] == ["-m", "PyInstaller", "--noconfirm", "--clean"]
        python_sdk_root = Path(__file__).resolve().parents[1] / "src"
        assert command.count("--paths") == 3
        hidden_import_index = command.index("--hidden-import")
        assert command[hidden_import_index + 1] == "aclip_demo_notes.app"
        assert str(source_root) in command
        assert str(extra_root) in command
        assert str(python_sdk_root) in command
        assert cwd == project_root
        launcher_script = Path(command[-1])
        assert launcher_script.exists()
        launcher_text = launcher_script.read_text(encoding="utf-8")
        assert "from aclip_demo_notes.app import create_app as __aclip_target" in launcher_text
        assert "cli_main(__aclip_target)" in launcher_text
        dist_dir.mkdir(exist_ok=True)
        (dist_dir / binary_name).write_bytes(b"demo-binary")

    artifact = build_cli(
        create_app,
        project_root=project_root,
        source_root=source_root,
        extra_paths=[extra_root],
        dist_dir=dist_dir,
        build_dir=build_dir,
        runner=fake_runner,
        platform_value="windows-x64",
    )

    assert artifact.binary_path == dist_dir / binary_name
    assert artifact.manifest_path == dist_dir / "aclip-demo-notes.aclip.json"

    manifest = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "aclip-demo-notes"
    assert manifest["distribution"] == [
        {
            "kind": "standalone_binary",
            "binary": "aclip-demo-notes.exe",
            "platform": "windows-x64",
            "sha256": hashlib.sha256(b"demo-binary").hexdigest(),
        }
    ]
    validate(manifest, load_schema("manifest"))
    assert launcher_script is not None
    assert not launcher_script.exists()


def test_build_cli_auto_includes_local_sdk_source_root_for_repo_layout(tmp_path: Path):
    captured: dict[str, object] = {}

    def fake_runner(command: list[str], cwd: Path) -> None:
        captured["command"] = command
        captured["cwd"] = cwd
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir(exist_ok=True)
        (dist_dir / "aclip-demo-notes.exe").write_bytes(b"demo-binary")

    artifact = build_cli(
        app_factory="aclip_demo_notes.app:create_app",
        dist_dir=tmp_path / "dist",
        build_dir=tmp_path / "build",
        runner=fake_runner,
    )

    command = captured["command"]
    assert isinstance(command, list)
    python_sdk_root = Path(__file__).resolve().parents[1] / "src"
    example_source_root = Path(__file__).resolve().parents[1] / "examples" / "demo-notes" / "src"
    assert command.count("--paths") == 2
    assert str(example_source_root) in command
    assert str(python_sdk_root) in command
    assert artifact.binary_path.name == "aclip-demo-notes.exe"


def test_build_cli_accepts_app_import_target_string(tmp_path: Path):
    def fake_runner(command: list[str], cwd: Path) -> None:
        (tmp_path / "dist").mkdir(exist_ok=True)
        (tmp_path / "dist" / "aclip-demo-notes.exe").write_bytes(b"demo-binary")

    artifact = build_cli(
        "aclip_demo_notes.app:app",
        dist_dir=tmp_path / "dist",
        build_dir=tmp_path / "build",
        runner=fake_runner,
    )

    assert artifact.binary_path.name == "aclip-demo-notes.exe"


def test_inspect_app_factory_exposes_module_file():
    info = inspect_app_factory("aclip_demo_notes.app:create_app")

    assert info.target == "aclip_demo_notes.app:create_app"
    assert info.module_file.name == "app.py"


def test_repository_layout_places_python_sdk_under_sdk_directory():
    root = Path(__file__).resolve().parents[1]

    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "aclip").exists()
    assert (root / "examples" / "demo-notes" / "src" / "aclip_demo_notes").exists()


def test_python_sdk_does_not_declare_a_build_cli_console_script():
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

    assert "scripts" not in pyproject["project"]


def test_cli_main_uses_default_argv(capsys):
    app = create_app()
    original_argv = sys.argv
    sys.argv = ["aclip-demo-notes", "note", "list"]
    try:
        try:
            cli_main(app)
        except SystemExit as exc:
            assert exc.code == 0
    finally:
        sys.argv = original_argv

    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "note list"


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


def test_sdk_exposes_build_cli_only_as_a_module_level_api():
    assert not hasattr(AclipApp, "build_cli")


def test_build_alias_points_to_build_cli():
    assert build is build_cli


def test_load_app_target_supports_app_instance_exports():
    app = load_app_target("aclip_demo_notes.app:app")

    assert app.name == "aclip-demo-notes"

