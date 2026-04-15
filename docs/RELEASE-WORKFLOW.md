# ACLIP Release Workflow

This document is for maintainers of the ACLIP repository.

It is intentionally internal-facing.

User-facing package pages must not contain this workflow.

## Purpose

This document answers:

- how ACLIP SDK packages are released
- which scripts are the only supported release entrypoints
- how to avoid ambiguous manual publishing
- how to recover from the known secret-format pitfall in `.repositorys`

## Package Surfaces

ACLIP currently releases these package surfaces:

- PyPI canonical: `rendo-aclip`
- PyPI synchronized alias: `aclip`
- npm canonical: `@rendo-studio/aclip`

## Required Rule

Releases must be performed through package-local scripts only.

Do not hand-run ad hoc `twine upload` or `npm publish` commands unless debugging a broken release script.

Supported entrypoints:

- Python: `sdk/python/scripts/publish.py`
- TypeScript: `sdk/typescript/scripts/publish.mjs`

## Python Release

Working directory:

- `D:\project\rendo\aclip\sdk\python`

Check:

```powershell
..\..\..\.venv\Scripts\python.exe .\scripts\publish.py check
```

Publish:

```powershell
$env:PYPI_TOKEN = "<token>"
..\..\..\.venv\Scripts\python.exe .\scripts\publish.py publish
```

Behavior:

- builds `rendo-aclip`
- builds synchronized alias `aclip`
- runs `twine check`
- uploads with `--non-interactive`
- uses `--skip-existing` so partial prior uploads do not force manual cleanup

### Secret Pitfall

When copying the PyPI token from `.repositorys/pypi.md`, the token may appear markdown-escaped as `\_`.

Before exporting it as `PYPI_TOKEN`, convert:

- `\_` -> `_`

Otherwise PyPI returns invalid-authentication `403`.

## TypeScript Release

Working directory:

- `D:\project\rendo\aclip\sdk\typescript`

Check:

```powershell
node .\scripts\publish.mjs check
```

Publish:

```powershell
$env:NPM_TOKEN = "<token>"
node .\scripts\publish.mjs publish
```

Behavior:

- runs tests
- runs typecheck
- runs build
- runs publish dry-run
- publishes `@rendo-studio/aclip`

## GitHub Push

Repository:

- `https://github.com/rendo-studio/aclip`

If local credential cache points to the wrong GitHub account, use the PAT in `.repositorys/github.md` explicitly for the push instead of relying on ambient git auth.

## User-Facing Boundary

The following belong here, not in package READMEs:

- release commands
- internal environment variable names
- maintainer token handling
- GitHub push recovery steps
- registry troubleshooting notes
