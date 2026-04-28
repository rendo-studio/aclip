import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import validate

from aclip.schema import load_schema


ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = str(ROOT / "src") + ";" + str(ROOT / "examples" / "demo-notes" / "src")


def run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        PYTHONPATH if "PYTHONPATH" not in env else PYTHONPATH + ";" + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", "aclip_demo_notes", *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_root_help_returns_index_manifest():
    result = run_demo("--help")

    assert result.returncode == 0
    assert result.stdout == (
        "# aclip-demo-notes\n\n"
        "Example notes CLI built with the aclip SDK\n\n"
        "Stores notes in a local JSON file and exposes agent-first command disclosure.\n\n"
        "## Command Groups\n\n"
        "- `note`: Manage notes\n\n"
        "Next: run `aclip-demo-notes <path> --help` for one command group or command shown above.\n"
    )


def test_bare_invocation_matches_help_markdown():
    help_result = run_demo("--help")
    bare_result = run_demo()

    assert bare_result.returncode == 0
    assert bare_result.stdout == help_result.stdout


def test_help_alias_matches_root_help():
    help_result = run_demo("--help")
    alias_result = run_demo("help")

    assert alias_result.returncode == 0
    assert alias_result.stdout == help_result.stdout


def test_root_version_flags_return_plain_version():
    long_flag = run_demo("--version")
    short_flag = run_demo("-V")
    lower_short_flag = run_demo("-v")

    assert long_flag.returncode == 0
    assert long_flag.stdout == "aclip-demo-notes 0.1.0\n"
    assert short_flag.returncode == 0
    assert short_flag.stdout == "aclip-demo-notes 0.1.0\n"
    assert lower_short_flag.returncode == 0
    assert lower_short_flag.stdout == "aclip-demo-notes 0.1.0\n"


def test_natural_cli_execution_returns_app_defined_success_output(tmp_path):
    store = tmp_path / "notes.json"

    result = run_demo(
        "note",
        "create",
        "--title",
        "hello",
        "--body",
        "world",
        "--store",
        str(store),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["note"]["title"] == "hello"
    assert "protocol" not in payload
    assert "ok" not in payload
    assert "command" not in payload


def test_direct_script_execution_still_works_for_binary_packaging_entrypoint():
    entrypoint = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "demo-notes"
        / "src"
        / "aclip_demo_notes"
        / "__main__.py"
    )
    result = subprocess.run(
        [sys.executable, str(entrypoint), "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": (
                PYTHONPATH
                if "PYTHONPATH" not in os.environ
                else PYTHONPATH + ";" + os.environ["PYTHONPATH"]
            ),
        },
    )

    assert result.returncode == 0
    assert result.stdout.startswith("# aclip-demo-notes\n")


def test_command_group_help_returns_only_group_level_children():
    result = run_demo("note", "--help")

    assert result.returncode == 0
    assert result.stdout == (
        "# note\n\n"
        "Manage notes\n\n"
        "Create and list notes in the local JSON store.\n\n"
        "## Commands\n\n"
        "- `note create`: Create a note\n"
        "- `note list`: List notes\n"
    )


def test_command_help_returns_command_detail():
    result = run_demo("note", "create", "--help")

    assert result.returncode == 0
    assert result.stdout == (
        "# note create\n\n"
        "Create a note in a local JSON store.\n\n"
        "## Usage\n\n"
        "```text\n"
        "aclip-demo-notes note create --title <string> --body <string> [--store <string>]\n"
        "```\n\n"
        "## Arguments\n\n"
        "- `--title <string>` required: Title for the note.\n"
        "- `--body <string>` required: Body text for the note.\n"
        "- `--store <string>` optional, default `.aclip-demo-notes.json`: Path to the local note store.\n\n"
        "## Examples\n\n"
        "```text\n"
        "aclip-demo-notes note create --title hello --body world\n"
        "```\n"
    )


def test_help_all_expands_subtree_markdown():
    result = run_demo("note", "--help", "--all")

    assert result.returncode == 0
    assert result.stdout.startswith("# note\n\n")
    assert "\n---\n\n# note create\n\n" in result.stdout
    assert "\n---\n\n# note list\n\n" in result.stdout


def test_invalid_usage_returns_error_envelope():
    result = run_demo("note", "create", "--title", "missing-body")

    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert payload["type"] == "error"
    assert payload["ok"] is False
    validate(payload, load_schema("error"))

