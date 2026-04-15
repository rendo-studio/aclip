# rendo-aclip

`rendo-aclip` is the Python reference adapter for ACLIP.

It does not define the ACLIP protocol.

It implements the shared protocol contracts maintained at the repository root and provides Python authoring, runtime, and packaging helpers for ACLIP-compatible CLIs.

## What it provides

- `AclipApp` tree-shaped authoring
- `CommandSpec`, `CommandGroupSpec`, and `ArgumentSpec`
- canonical ACLIP Markdown help rendering
- structured result and error envelopes
- binary packaging through `package_binary()`
- packaging CLI through `aclip-package`

## Install

```bash
pip install rendo-aclip
```

Short-name compatibility alias:

```bash
pip install aclip
```

`aclip` is published as a synchronized alias package and should always resolve to the same SDK release as `rendo-aclip`.

## Quick Start

```python
from aclip import AclipApp, ArgumentSpec

app = AclipApp(
    name="demo",
    version="0.1.0",
    summary="Demo CLI",
    description="Demo CLI.",
)

app.command_groups.append(...)
```

The recommended higher-level authoring path is to use `AclipApp.group()` and `@group.command()` from your own module entrypoint.

## Packaging

```python
from pathlib import Path

from aclip import package_binary

artifact = package_binary(
    app=app,
    binary_name="demo",
    entry_script=Path("src/demo_cli/__main__.py"),
    project_root=Path(".").resolve(),
    source_root=Path("src").resolve(),
)
```

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .[dev]
.\.venv\Scripts\python -m pytest tests -q
```

