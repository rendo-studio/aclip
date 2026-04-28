# rendo-aclip

`rendo-aclip` is the canonical Python SDK for ACLIP, the Agent Command Line Interface Protocol.

It keeps normal CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- app-defined success output plus structured error envelopes
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
from aclip import run_cli
from main import app


run_cli(app)
```

If you prefer lazy initialization at process start, the launcher also accepts the factory directly:

```python
from aclip import run_cli
from main import create_app


run_cli(create_app)
```

Run it like a normal CLI:

```bash
python cli.py --help
python cli.py note --help
python cli.py note create --help
python cli.py note create --title hello --body world
```

The final command prints app-defined success output:

- strings stay plain text
- objects and arrays are emitted as plain JSON

`AclipApp.name` is the canonical CLI command token, not a display title. Keep it executable-safe, with no spaces.
`version` is optional during local authoring. Set it before manifest build, packaging, publish, skill export, or the default root `--version` / `-V` / `-v` surface, which prints `<cli-name> <version>`.
`--help` / `-h` remain protocol-reserved discovery flags, while `--version` / `-V` / `-v` are only default root fallbacks and become author-owned again after a concrete command path is selected.
When one author-owned argument should accept multiple aliases, declare `flags=(\"--long\", \"-S\")` on `ArgumentSpec` instead of splitting aliases across multiple parameters.

## Build A Distributable CLI

From a dedicated build script:

```python
import aclip


artifact = aclip.build("main:app")

print(artifact.binary_path)
print(artifact.manifest_path)
```

`build(...)` is the shortest first-class path. `"main:app"` is the runtime import target the packaged binary will execute.
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

If you want the fully explicit name, `build_cli(...)` is the same API.

## Authentication

ACLIP now standardizes a minimum auth contract around portable credential declarations and an optional reserved `auth` control plane.

```python
from aclip import (
    AuthCommandConfig,
    AuthNextAction,
    AuthStatus,
    CredentialSpec,
    auth_status_result,
    build_auth_control_plane,
)


credentials = [
    CredentialSpec.env(
        name="notes_token",
        env_var="ACLIP_NOTES_TOKEN",
        description="Remote notes API token.",
        required=True,
    ),
    CredentialSpec.file(
        name="notes_token_file",
        path=".secrets/notes-token.txt",
        description="Optional local token file.",
    ),
]

auth = build_auth_control_plane(
    AuthCommandConfig(
        login_description="Login to the author-defined remote service.",
        login_examples=["notes auth login"],
        login_handler=lambda _payload: {"status": "logged_in"},
        status_description="Inspect current auth state.",
        status_examples=["notes auth status"],
        status_handler=lambda _payload: auth_status_result(
            AuthStatus(
                state="authenticated",
                principal="dev@rendo.cn",
                next_actions=[
                    AuthNextAction(
                        summary="Refresh before expiry",
                        command="notes auth login",
                    )
                ],
            ),
            guidance_md="Credential is valid. Refresh before running long-lived jobs.",
        ),
        logout_description="Logout from the author-defined remote service.",
        logout_examples=["notes auth logout"],
        logout_handler=lambda _payload: {"status": "logged_out"},
    )
)
```

## Diagnostics

ACLIP also provides a reserved optional `doctor` control plane and helper payload builders for stable agent-facing checks.

```python
from aclip import (
    DoctorCheck,
    DoctorCommandConfig,
    DoctorRemediation,
    build_doctor_control_plane,
    doctor_result,
)

doctor = build_doctor_control_plane(
    DoctorCommandConfig(
        check_description="Run author-defined environment checks.",
        check_examples=["notes doctor check"],
        check_handler=lambda _payload: doctor_result(
            checks=[
                DoctorCheck(
                    id="credentials",
                    status="warn",
                    severity="medium",
                    category="auth",
                    summary="Credential is missing or expired.",
                    hint="Run the login flow before retrying.",
                    remediation=[
                        DoctorRemediation(
                            summary="Refresh the credential.",
                            command="notes auth login",
                            automatable=True,
                        )
                    ],
                )
            ],
            guidance_md="Fix the auth check first, then rerun the original command.",
        ),
        fix_description="Apply author-defined fixes for failed checks.",
        fix_examples=["notes doctor fix"],
        fix_handler=lambda _payload: {"checks": []},
    )
)
```

## Export Agent Skills Packages

ACLIP can export developer-authored skill packages while keeping CLI and command metadata aligned as anchors.

There are two different hook scopes:

- `add_cli_skill(...)`
  Attach one skill package to the whole CLI.
  Use this for top-level usage strategy, cross-command navigation, auth/doctor preparation, or other whole-tool guidance.
- `add_command_skill(...)`
  Attach one skill package to one command path.
  Use this for command-specific best practices, prerequisites, recovery steps, or multi-step invocation guidance.

These hooks do **not** change normal runtime behavior.

They do not automatically print skill text when the CLI runs.
They only register export-time linkage so that `export_skills(...)` knows which developer-authored packages to materialize.

```python
from pathlib import Path

from aclip import export_skills

from main import create_app


app = create_app()
skills_root = Path("skills")
app.add_cli_skill(skills_root / "notes-overview")
app.add_command_skill(
    ("note", "create"),
    skills_root / "note-create-best-practice",
    metadata={"owner": "docs"},
)

artifact = export_skills(app, output_dir=Path("dist") / "skills")
print(artifact.index_path)
```

What happens here:

1. `app.add_cli_skill(...)` registers one whole-CLI package
2. `app.add_command_skill(...)` registers one command-bound package
3. `export_skills(...)` validates each source package
4. ACLIP copies those packages into the output directory
5. ACLIP injects anchor metadata into `SKILL.md`
6. ACLIP writes a `skills.aclip.json` index beside the exported packages

Each source package must contain a developer-authored `SKILL.md`.

Important boundary:

- hook registration does not install anything into a user workspace
- `export_skills(...)` is an explicit optional API
- if you want `init` or another command to copy exported skills into a project, that copy step is still your command logic, not automatic ACLIP runtime behavior

In a conventional project layout, ACLIP infers:

- project root
- source root
- executable name

`src/` is optional. Advanced overrides such as `project_root`, `source_root`, and `extra_paths` are still available for monorepos or non-standard layouts, but they are no longer the default path.

## What You Get

- `AclipApp` for tree-shaped CLI authoring
- direct `handler=...` registration and decorator authoring
- `app.run(...)` for direct execution in tests or custom hosts
- `run_cli(...)` for the default launcher path without manual `sys.argv[1:]`
- `build(...)` for the shortest packaging path, with `build_cli(...)` as the explicit equivalent
- `export_skills(...)` for Agent Skills-compatible package export from CLI-level and command-level hooks

## When To Use ACLIP

Use `rendo-aclip` when you want a CLI that still feels natural to command-line users while giving agents:

- predictable help disclosure
- predictable machine-readable failures
- a stable packaging and distribution path

If your goal is only a human-first CLI with free-form text output, ACLIP is probably more structure than you need.

## Python vs TypeScript

The Python and TypeScript SDKs now share the same primary story:

- define `app` in `main`
- launch with `run_cli(app)` / `runCli(app)`
- package with `build("main:app")`

One intentional difference remains: Python also supports `build(create_app)` for a top-level factory function. TypeScript does not expose the same shortcut because a JavaScript function object is not a stable packaging import target on its own.

## Repository

- <https://github.com/rendo-studio/aclip>
