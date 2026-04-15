# rendo-aclip

`rendo-aclip` is the canonical Python SDK for ACLIP, the Agent Command Line Interface Protocol.

ACLIP keeps normal CLI invocation natural:

- `tool --help`
- `tool group --help`
- `tool command --help`
- `tool command --flag value`

At the same time, it standardizes the parts agents actually depend on:

- progressive Markdown help
- structured result and error envelopes
- sidecar manifests for registry and distribution flows
- packaging helpers for shipping runnable CLI artifacts

## Which package name should I install?

Canonical package:

```bash
pip install rendo-aclip
```

Short-name official alias:

```bash
pip install aclip
```

Both install paths are first-party and synchronized. The import path is the same either way:

```python
from aclip import AclipApp
```

If you want the official dependency name for long-term project manifests, prefer `rendo-aclip`.

If you want the shortest install command, `aclip` is the official alias.

## What you get

- `AclipApp` for tree-shaped CLI authoring
- direct `handler=...` registration and decorator authoring
- canonical ACLIP Markdown help rendering
- structured JSON result and error envelopes
- `build_cli()` and `app.build_cli()` for building a distributable binary CLI
- `aclip-build-cli` as the canonical packaging CLI entrypoint

## First Working CLI

```python
from __future__ import annotations

import sys

from aclip import AclipApp


app = AclipApp(
    name="notes",
    version="0.1.2",
    summary="A minimal notes CLI.",
    description="Create and list notes from a small local CLI.",
)
def create_note(title: str, body: str) -> dict:
    """Create a note in a local JSON store.

    Args:
        title: Title for the note.
        body: Body text for the note.
    """
    return {"note": {"title": title, "body": body}}


note = app.group(
    "note",
    summary="Manage notes",
    description="Create and inspect notes.",
).command(
    "create",
    handler=create_note,
    examples=["notes note create --title hello --body world"],
)


if __name__ == "__main__":
    raise SystemExit(app.run(sys.argv[1:]))
```

Run it like a normal CLI:

```bash
notes --help
notes note --help
notes note create --help
notes note create --title hello --body world
```

The final command returns a structured result envelope instead of ad hoc text.

If you prefer decorators, `@app.command(...)` and `@group.command(...)` remain fully supported.

## Binary Packaging

```python
from pathlib import Path

artifact = app.build_cli(
    entry_script=Path("src/notes_cli/__main__.py"),
    project_root=Path(".").resolve(),
)

print(artifact.binary_path)
print(artifact.manifest_path)
```

This produces:

- a runnable CLI binary
- a sidecar `.aclip.json` manifest

The lower-level `build_cli(...)` function is also available if you prefer a module-level API.

The packaged CLI wrapper is:

```bash
aclip-build-cli --app-factory notes_cli.app:create_app --entry-script ./src/notes_cli/__main__.py
```

## When to use ACLIP

Use `rendo-aclip` when you want to build a CLI that should feel natural to normal command-line users while also giving agents:

- predictable help disclosure
- predictable machine-readable command results
- a stable packaging and distribution path

If your goal is only a human-first CLI with free-form text output, ACLIP is probably more structure than you need.

## Repository

Source repository:

- <https://github.com/rendo-studio/aclip>

