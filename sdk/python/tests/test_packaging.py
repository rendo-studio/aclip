import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

from jsonschema import validate

from aclip_demo_notes.app import create_app
from aclip import (
    AclipApp,
    AUTH_ERROR_CODES,
    AUTH_STATES,
    AuthCommandConfig,
    AuthNextAction,
    AuthStatus,
    CredentialSpec,
    DOCTOR_CHECK_SEVERITIES,
    DOCTOR_CHECK_STATUSES,
    DoctorCheck,
    DoctorCommandConfig,
    DoctorRemediation,
    DistributionSpec,
    auth_status_result,
    build,
    build_auth_control_plane,
    build_doctor_control_plane,
    cli_main,
    doctor_result,
    export_skills,
    run_cli,
)
from aclip.packaging import build_cli, inspect_app_factory, load_app_factory, load_app_target
from aclip.runtime import error_envelope
from aclip.schema import load_schema


def _write_skill_source(
    root: Path,
    *,
    name: str,
    description: str,
    metadata: dict[str, str] | None = None,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    metadata_lines = ""
    if metadata:
        metadata_lines = "\n".join(
            [f"  {key}: {value}" for key, value in metadata.items()]
        )
        metadata_lines = f"metadata:\n{metadata_lines}\n"

    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            f"{metadata_lines}"
            "---\n\n"
            f"# {name}\n\n"
            "Developer-authored skill body.\n"
        ),
        encoding="utf-8",
    )
    references_dir = skill_dir / "references"
    references_dir.mkdir(exist_ok=True)
    (references_dir / "README.md").write_text("reference", encoding="utf-8")
    return skill_dir


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
        pythonpath_entries = os.environ.get("PYTHONPATH", "").split(os.pathsep)
        assert pythonpath_entries[:3] == [
            str(source_root),
            str(extra_root),
            str(python_sdk_root),
        ]
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
    assert payload == {"notes": []}


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


def test_run_cli_alias_points_to_cli_main():
    assert run_cli is cli_main


def test_credential_spec_supports_env_and_file_sources():
    env_credential = CredentialSpec.env(
        name="notes_token",
        env_var="ACLIP_NOTES_TOKEN",
        description="Token for remote notes access.",
        required=True,
    )
    file_credential = CredentialSpec.file(
        name="notes_token_file",
        path=".secrets/notes-token.txt",
        description="Path to a local token file.",
    )

    assert env_credential.to_manifest() == {
        "name": "notes_token",
        "source": "env",
        "required": True,
        "description": "Token for remote notes access.",
        "envVar": "ACLIP_NOTES_TOKEN",
    }
    assert file_credential.to_manifest() == {
        "name": "notes_token_file",
        "source": "file",
        "required": False,
        "description": "Path to a local token file.",
        "path": ".secrets/notes-token.txt",
    }


def test_invalid_credential_source_shape_raises_value_error():
    try:
        CredentialSpec(
            name="broken",
            source="env",
            description="Broken credential shape.",
        )
    except ValueError as exc:
        assert "envVar" in str(exc)
    else:
        raise AssertionError("expected CredentialSpec to reject env credentials without env_var")


def test_auth_error_codes_are_exported():
    assert AUTH_ERROR_CODES == {
        "auth_required",
        "invalid_credential",
        "expired_credential",
    }


def test_build_auth_control_plane_provides_reserved_auth_group():
    control_plane = build_auth_control_plane(
        AuthCommandConfig(
            login_description="Login to the author-defined remote service.",
            login_examples=["notes auth login"],
            login_handler=lambda _payload: {"status": "logged_in"},
            status_description="Inspect current auth state.",
            status_examples=["notes auth status"],
            status_handler=lambda _payload: {"status": "active"},
            logout_description="Logout from the author-defined remote service.",
            logout_examples=["notes auth logout"],
            logout_handler=lambda _payload: {"status": "logged_out"},
        )
    )

    assert control_plane.command_group.path == ("auth",)
    assert [command.path for command in control_plane.commands] == [
        ("auth", "login"),
        ("auth", "status"),
        ("auth", "logout"),
    ]


def test_auth_status_result_provides_small_agent_friendly_status_shape():
    payload = auth_status_result(
        AuthStatus(
            state="authenticated",
            principal="dev@rendo.cn",
            expires_at="2026-04-21T00:00:00Z",
            next_actions=[
                AuthNextAction(
                    summary="Refresh before expiry",
                    command="notes auth login",
                )
            ],
        ),
        guidance_md="Credential is valid. Refresh before the expiry window if long-running work is expected.",
    )

    assert payload == {
        "state": "authenticated",
        "principal": "dev@rendo.cn",
        "expires_at": "2026-04-21T00:00:00Z",
        "next_actions": [
            {
                "summary": "Refresh before expiry",
                "command": "notes auth login",
            }
        ],
        "guidance_md": "Credential is valid. Refresh before the expiry window if long-running work is expected.",
    }
    assert "authenticated" in AUTH_STATES


def test_error_envelope_supports_richer_machine_metadata():
    payload = error_envelope(
        "note sync",
        "auth_required",
        "authentication required",
        category="auth",
        retryable=False,
        hint="run `notes auth login` first",
    )

    assert payload["error"] == {
        "code": "auth_required",
        "message": "authentication required",
        "category": "auth",
        "retryable": False,
        "hint": "run `notes auth login` first",
    }


def test_build_doctor_control_plane_provides_reserved_doctor_group():
    control_plane = build_doctor_control_plane(
        DoctorCommandConfig(
            check_description="Run author-defined environment checks.",
            check_examples=["notes doctor check"],
            check_handler=lambda _payload: {"checks": []},
            fix_description="Apply author-defined fixes for failed checks.",
            fix_examples=["notes doctor fix"],
            fix_handler=lambda _payload: {"checks": []},
        )
    )

    assert control_plane.command_group.path == ("doctor",)
    assert [command.path for command in control_plane.commands] == [
        ("doctor", "check"),
        ("doctor", "fix"),
    ]


def test_doctor_result_provides_stable_check_vocabulary_and_guidance():
    payload = doctor_result(
        checks=[
            DoctorCheck(
                id="credentials",
                status="warn",
                severity="medium",
                category="auth",
                summary="Credential is missing or expired.",
                hint="Run the auth flow before retrying the command.",
                remediation=[
                    DoctorRemediation(
                        summary="Login to refresh the credential.",
                        command="notes auth login",
                        automatable=True,
                    )
                ],
            )
        ],
        guidance_md="Fix the auth check first, then rerun the original command.",
    )

    assert payload == {
        "checks": [
            {
                "id": "credentials",
                "status": "warn",
                "severity": "medium",
                "category": "auth",
                "summary": "Credential is missing or expired.",
                "hint": "Run the auth flow before retrying the command.",
                "remediation": [
                    {
                        "summary": "Login to refresh the credential.",
                        "command": "notes auth login",
                        "automatable": True,
                    }
                ],
            }
        ],
        "guidance_md": "Fix the auth check first, then rerun the original command.",
    }
    assert "warn" in DOCTOR_CHECK_STATUSES
    assert "medium" in DOCTOR_CHECK_SEVERITIES


def test_export_skills_copies_cli_and_command_skill_packages(tmp_path: Path):
    app = create_app()
    cli_skill_dir = _write_skill_source(
        tmp_path,
        name="notes-overview",
        description="Use the notes CLI safely.",
        metadata={"author": "demo"},
    )
    command_skill_dir = _write_skill_source(
        tmp_path,
        name="note-create-best-practice",
        description="Create notes with the recommended flow.",
    )

    app.add_cli_skill(cli_skill_dir)
    app.add_command_skill(("note", "create"), command_skill_dir, metadata={"custom": "true"})

    artifact = export_skills(app, output_dir=tmp_path / "dist" / "skills")

    assert artifact.index_path.name == "skills.aclip.json"
    assert [package["kind"] for package in artifact.index["packages"]] == ["cli", "command"]
    assert artifact.output_dir == tmp_path / "dist" / "skills"

    exported_cli_skill = artifact.output_dir / "notes-overview" / "SKILL.md"
    exported_command_skill = artifact.output_dir / "note-create-best-practice" / "SKILL.md"
    assert exported_cli_skill.exists()
    assert exported_command_skill.exists()
    assert (artifact.output_dir / "notes-overview" / "references" / "README.md").exists()

    cli_text = exported_cli_skill.read_text(encoding="utf-8")
    assert "aclip-cli-name: aclip-demo-notes" in cli_text
    assert "aclip-hook-kind: cli" in cli_text
    assert "author: demo" in cli_text

    command_text = exported_command_skill.read_text(encoding="utf-8")
    assert "aclip-hook-kind: command" in command_text
    assert "aclip-command-path: note create" in command_text
    assert "aclip-command-summary: Create a note" in command_text
    assert "custom: true" in command_text


def test_export_skills_rejects_missing_skill_markdown(tmp_path: Path):
    app = create_app()
    broken_skill_dir = tmp_path / "broken-skill"
    broken_skill_dir.mkdir(parents=True, exist_ok=True)
    app.add_cli_skill(broken_skill_dir)

    try:
        export_skills(app, output_dir=tmp_path / "dist" / "skills")
    except ValueError as exc:
        assert "SKILL.md" in str(exc)
    else:
        raise AssertionError("expected export_skills to reject a skill package without SKILL.md")

