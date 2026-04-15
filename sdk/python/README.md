# rendo-aclip

`rendo-aclip` is the canonical Python SDK for ACLIP, the Agent Command Line Interface Protocol.

It keeps normal CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- structured result and error envelopes
- sidecar manifests for distribution metadata
- packaging helpers for shipping runnable CLI artifacts

## Install

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

If you want the canonical dependency name in project manifests, prefer `rendo-aclip`.
If you want the shortest install command, `aclip` is the official alias.

## Smallest End-to-End CLI

`main.py`

```python
from aclip import AclipApp


def create_app() -> AclipApp:
    app = AclipApp(
        name="notes",
        version="0.2.2",
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

    app.group(
        "note",
        summary="Manage notes",
        description="Create and inspect notes.",
    ).command(
        "create",
        handler=create_note,
        examples=["notes note create --title hello --body world"],
    )

    return app


app = create_app()
```

`cli.py`

```python
from aclip import cli_main
from main import app


cli_main(app)
```

Run it like a normal CLI:

```bash
python cli.py --help
python cli.py note --help
python cli.py note create --help
python cli.py note create --title hello --body world
```

The final command emits a structured result envelope instead of ad hoc text.

## Build A Distributable CLI

From a dedicated build script:

```python
import aclip


artifact = aclip.build("main:app")

print(artifact.binary_path)
print(artifact.manifest_path)
```

`"main:app"` is the runtime import target the packaged binary will execute.
That is why the recommended pattern is a separate `build.py` script instead of having the app object “build itself”.

If you prefer to keep initialization behind a function, ACLIP also supports an explicit factory target:

```python
import aclip


artifact = aclip.build(factory="main:create_app")
```

Python also supports a shorthand when you already imported a top-level factory:

```python
import aclip
from main import create_app


artifact = aclip.build(create_app)
```

In a conventional project layout, ACLIP infers:

- project root
- source root
- executable name

`src/` is optional. Advanced overrides such as `project_root`, `source_root`, and `extra_paths` are still available for monorepos or non-standard layouts, but they are no longer the default path.

## What You Get

- `AclipApp` for tree-shaped CLI authoring
- direct `handler=...` registration and decorator authoring
- `cli_main(...)` so launchers do not need manual `sys.argv[1:]`
- `build_cli()` as the canonical packaging API

## When To Use ACLIP

Use `rendo-aclip` when you want a CLI that still feels natural to command-line users while giving agents:

- predictable help disclosure
- predictable machine-readable command results
- a stable packaging and distribution path

If your goal is only a human-first CLI with free-form text output, ACLIP is probably more structure than you need.

## Repository

- <https://github.com/rendo-studio/aclip>
