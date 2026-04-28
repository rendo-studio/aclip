# aclip-demo-notes (Python)

This is the Python example CLI for the ACLIP reference adapter.

It exists to prove that the Python SDK can:

- author a real ACLIP-compatible CLI
- package it into a binary artifact
- emit a sidecar `.aclip.json` manifest beside that artifact
- export Agent Skills-compatible packages from CLI-level and command-level hooks

Build locally:

```powershell
..\..\..\..\.venv\Scripts\python.exe .\scripts\build.py
```

Export the demo skill packages:

```powershell
..\..\..\..\.venv\Scripts\python.exe .\scripts\export_skills.py
```

This export step is explicit and optional.

It creates exported skill packages under `dist\skills`.
It does not change the runtime behavior of `aclip-demo-notes`, and running CLI commands does not automatically print these skill files.
