from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aclip import AclipApp


def create_app() -> AclipApp:
    app = AclipApp(
        name="aclip-demo-notes",
        version="0.1.0",
        summary="Example notes CLI built with the aclip SDK",
        description=(
            "Stores notes in a local JSON file and exposes agent-first command "
            "disclosure."
        ),
    )
    note = app.group(
        "note",
        summary="Manage notes",
        description="Create and list notes in the local JSON store.",
    )

    @note.command(
        "create",
        summary="Create a note",
        examples=["aclip-demo-notes note create --title hello --body world"],
    )
    def create(title: str, body: str, store: str = ".aclip-demo-notes.json") -> dict:
        """Create a note in a local JSON store.

        Args:
            title: Title for the note.
            body: Body text for the note.
            store: Path to the local note store.
        """
        return create_note({"title": title, "body": body, "store": store})

    @note.command(
        "list",
        summary="List notes",
        examples=["aclip-demo-notes note list --store .aclip-demo-notes.json"],
    )
    def list_(store: str = ".aclip-demo-notes.json") -> dict:
        """List notes from the local JSON store.

        Args:
            store: Path to the local note store.
        """
        return list_notes({"store": store})

    return app

def create_note(arguments: dict[str, Any]) -> dict[str, Any]:
    store = Path(arguments["store"])
    notes = _read_store(store)
    note = {
        "id": f"note-{len(notes) + 1}",
        "title": arguments["title"],
        "body": arguments["body"],
    }
    notes.append(note)
    _write_store(store, notes)
    return {"note": note}


def list_notes(arguments: dict[str, Any]) -> dict[str, Any]:
    store = Path(arguments["store"])
    return {"notes": _read_store(store)}


def _read_store(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_store(path: Path, notes: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, ensure_ascii=True, indent=2), encoding="utf-8")

