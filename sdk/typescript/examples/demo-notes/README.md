# aclip-demo-notes (TypeScript)

This is the TypeScript example CLI for the ACLIP reference adapter.

It exists to prove that the TypeScript SDK can:

- author a real ACLIP-compatible CLI
- bundle it into a runnable Node CLI artifact
- emit a sidecar `.aclip.json` manifest beside that artifact
- export Agent Skills-compatible packages from CLI-level and command-level hooks

Build locally:

```powershell
node --import tsx .\scripts\build.ts
```

Export the demo skill packages:

```powershell
node --import tsx .\scripts\export-skills.ts
```

This export step is explicit and optional.

It creates exported skill packages under `dist\skills`.
It does not change the runtime behavior of `aclip-demo-notes`, and running CLI commands does not automatically print these skill files.
