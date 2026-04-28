import json

import pytest
from jsonschema import validate

from aclip import AclipApp, ArgumentSpec, CommandSpec
from aclip_demo_notes.app import create_app
from aclip.schema import load_schema


def test_index_manifest_contains_progressive_command_summaries():
    app = create_app()

    manifest = app.build_index_manifest(binary_name="aclip-demo-notes")

    assert manifest["protocol"] == "aclip/0.1"
    assert manifest["name"] == "aclip-demo-notes"
    assert manifest["command_groups"] == [
        {"path": "note", "summary": "Manage notes"},
    ]
    assert manifest["commands"] == [
        {"path": "note create", "summary": "Create a note"},
        {"path": "note list", "summary": "List notes"},
    ]
    validate(manifest, load_schema("manifest"))


def test_command_detail_exposes_arguments_examples_and_output_contract():
    app = create_app()

    detail = app.build_command_detail(["note", "create"])

    assert detail["type"] == "help_command"
    assert detail["path"] == "note create"
    assert detail["usage"] == "aclip-demo-notes note create --title <string> --body <string> [--store <string>]"
    assert detail["arguments"][0]["name"] == "--title"
    assert detail["examples"][0].startswith("aclip-demo-notes note create")
    assert "output" not in detail
    assert "output_summary" not in detail
    validate(detail, load_schema("runtime-help-command"))


def test_root_help_payload_is_tree_shaped_and_excludes_registry_metadata():
    app = create_app()

    payload = app.build_help_payload()

    assert payload == {
        "protocol": "aclip/0.1",
        "type": "help_index",
        "summary": "Example notes CLI built with the aclip SDK",
        "description": "Stores notes in a local JSON file and exposes agent-first command disclosure.",
        "command_groups": [{"path": "note", "summary": "Manage notes"}],
    }
    validate(payload, load_schema("runtime-help-index"))


def test_group_help_payload_lists_only_child_commands():
    app = create_app()

    payload = app.build_help_payload(["note"])

    assert payload == {
        "protocol": "aclip/0.1",
        "type": "help_command_group",
        "path": "note",
        "summary": "Manage notes",
        "description": "Create and list notes in the local JSON store.",
        "commands": [
            {"path": "note create", "summary": "Create a note"},
            {"path": "note list", "summary": "List notes"},
        ],
    }
    validate(payload, load_schema("runtime-help-command-group"))


def test_sdk_rejects_explicit_help_flag_override():
    with pytest.raises(ValueError, match="reserved help flag"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="bad",
            description="bad",
            commands=[
                CommandSpec(
                    path=("note", "create"),
                    summary="Create",
                    description="Create",
                    arguments=[
                        ArgumentSpec(
                            name="oops",
                            flag="--help",
                            kind="string",
                            description="invalid override",
                        )
                    ],
                    examples=[],
                    handler=lambda _args: {},
                )
            ],
        )


def test_sdk_rejects_implicit_help_flag_override_from_argument_name():
    with pytest.raises(ValueError, match="reserved help flag"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="bad",
            description="bad",
            commands=[
                CommandSpec(
                    path=("note", "create"),
                    summary="Create",
                    description="Create",
                    arguments=[
                        ArgumentSpec(
                            name="help",
                            kind="string",
                            description="would generate --help",
                        )
                    ],
                    examples=[],
                    handler=lambda _args: {},
                )
            ],
        )


def test_sdk_rejects_declaring_both_flag_and_flags():
    with pytest.raises(ValueError, match="argument cannot declare both flag and flags"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="valid",
            description="valid",
            commands=[
                CommandSpec(
                    path=("oops",),
                    summary="oops",
                    description="oops",
                    arguments=[
                        ArgumentSpec(
                            name="mode",
                            kind="string",
                            description="duplicate declaration",
                            flag="--mode",
                            flags=("--mode", "-m"),
                        )
                    ],
                    examples=["bad-cli oops --mode fast"],
                    handler=lambda _args: {"ok": True},
                )
            ],
        )


def test_sdk_rejects_command_segments_that_look_like_flags():
    with pytest.raises(ValueError, match="command segments cannot start with '-'"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="bad",
            description="bad",
            commands=[
                CommandSpec(
                    path=("--help",),
                    summary="Bad",
                    description="Bad",
                    arguments=[],
                    examples=[],
                    handler=lambda _args: {},
                )
            ],
        )


def test_authoring_can_omit_version_until_manifest_build(capsys):
    app = AclipApp(
        name="demo",
        summary="valid",
        description="valid",
        commands=[
            CommandSpec(
                path=("ping",),
                summary="Ping",
                description="Ping something",
                arguments=[],
                examples=["demo ping"],
                handler=lambda _args: {"pong": True},
            )
        ],
    )

    exit_code = app.run(["ping"])

    assert exit_code == 0
    assert capsys.readouterr().out == '{"pong": true}\n'


def test_manifest_build_requires_version():
    app = AclipApp(
        name="demo",
        summary="valid",
        description="valid",
        commands=[
            CommandSpec(
                path=("ping",),
                summary="Ping",
                description="Ping something",
                arguments=[],
                examples=["demo ping"],
                handler=lambda _args: {"pong": True},
            )
        ],
    )

    with pytest.raises(ValueError, match="version is required"):
        app.build_index_manifest(binary_name="demo")


def test_manifest_name_override_must_match_canonical_cli_name():
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="valid",
        description="valid",
    )

    with pytest.raises(ValueError, match="binary_name override is no longer supported"):
        app.build_index_manifest(binary_name="demo-cli")


def test_root_help_command_can_override_default_help_alias(capsys):
    app = AclipApp(
        name="demo",
        summary="valid",
        description="valid",
    )

    @app.command("help", examples=["demo help"])
    def help_command() -> str:
        """Show custom help."""
        return "custom help"

    exit_code = app.run(["help"])

    assert exit_code == 0
    assert capsys.readouterr().out == "custom help\n"

    exit_code = app.run(["--help"])

    assert exit_code == 0
    assert capsys.readouterr().out.startswith("# demo\n\n")


def test_root_version_flags_render_plain_version(capsys):
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="valid",
        description="valid",
    )

    assert app.run(["--version"]) == 0
    assert capsys.readouterr().out == "demo 0.1.0\n"

    assert app.run(["-V"]) == 0
    assert capsys.readouterr().out == "demo 0.1.0\n"

    assert app.run(["-v"]) == 0
    assert capsys.readouterr().out == "demo 0.1.0\n"


def test_root_version_flag_returns_validation_error_when_version_missing(capsys):
    app = AclipApp(
        name="demo",
        summary="valid",
        description="valid",
    )

    exit_code = app.run(["--version"])

    assert exit_code == 2
    error = json.loads(capsys.readouterr().err)
    assert error["error"]["code"] == "validation_error"
    assert error["error"]["message"] == "version is not configured for this CLI"


def test_command_owned_version_flags_are_not_intercepted(capsys):
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="valid",
        description="valid",
    )

    app.command(
        "status",
        summary="Status",
        description="Show status",
        arguments=[
            ArgumentSpec(
                name="show_version",
                kind="boolean",
                description="Expose command-owned version state.",
                flags=("--version", "-V", "-v"),
            )
        ],
        examples=["demo status --version"],
        handler=lambda show_version=False: {"command_version": show_version},
    )

    assert app.run(["status", "--version"]) == 0
    assert capsys.readouterr().out == '{"command_version": true}\n'

    assert app.run(["status", "-V"]) == 0
    assert capsys.readouterr().out == '{"command_version": true}\n'

    assert app.run(["status", "-v"]) == 0
    assert capsys.readouterr().out == '{"command_version": true}\n'


def test_sdk_rejects_blank_root_summary():
    with pytest.raises(ValueError, match="summary must be a non-empty string"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="   ",
            description="valid",
            command_groups=[],
            commands=[],
        )


def test_sdk_rejects_names_that_are_not_cli_tokens():
    with pytest.raises(ValueError, match="name must be a CLI token"):
        AclipApp(
            name="Agent CLI",
            version="0.1.0",
            summary="valid",
            description="valid",
            command_groups=[],
            commands=[],
        )


def test_sdk_rejects_blank_group_description():
    from aclip import CommandGroupSpec

    with pytest.raises(ValueError, match="description must be a non-empty string"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="valid",
            description="valid",
            command_groups=[
                CommandGroupSpec(
                    path=("note",),
                    summary="Manage notes",
                    description="   ",
                )
            ],
            commands=[],
        )


def test_sdk_rejects_command_without_examples():
    with pytest.raises(ValueError, match="examples must contain at least one entry"):
        AclipApp(
            name="bad-cli",
            version="0.1.0",
            summary="valid",
            description="valid",
            command_groups=[],
            commands=[
                CommandSpec(
                    path=("ping",),
                    summary="Ping",
                    description="Ping something",
                    arguments=[],
                    examples=[],
                    handler=lambda _args: {},
                )
            ],
        )

