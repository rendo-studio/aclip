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

