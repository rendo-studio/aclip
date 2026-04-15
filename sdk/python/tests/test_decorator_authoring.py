import json

from aclip import AclipApp


def test_root_command_decorator_registration_builds_manifest_and_wraps_scalar_result(capsys):
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI.",
    )

    @app.command("version", examples=["demo version"])
    def version() -> str:
        """Show the current version."""
        return "0.1.0"

    manifest = app.build_index_manifest(binary_name="demo")

    assert manifest["commands"] == [{"path": "version", "summary": "Show the current version"}]

    exit_code = app.run(["version"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"result": "0.1.0"}


def test_group_command_decorator_uses_docstring_for_summary_and_argument_descriptions():
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI.",
    )

    note = app.group(
        "note",
        summary="Manage notes",
        description="Create and list notes.",
    )

    @note.command("create", examples=["demo note create --title hello --body world"])
    async def create(title: str, body: str, store: str = ".notes.json") -> dict:
        """Create a note in a local JSON store.

        Args:
            title: Title for the note.
            body: Body text for the note.
            store: Path to the local note store.
        """
        return {"note": {"title": title, "body": body, "store": store}}

    detail = app.build_command_detail(["note", "create"])

    assert detail["summary"] == "Create a note in a local JSON store"
    assert detail["arguments"][0]["description"] == "Title for the note."
    assert detail["arguments"][1]["description"] == "Body text for the note."
    assert detail["arguments"][2]["description"] == "Path to the local note store."

