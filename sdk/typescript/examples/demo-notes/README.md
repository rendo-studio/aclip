# aclip-demo-notes (TypeScript)

This is the TypeScript example CLI for the ACLIP reference adapter.

It exists to prove that the TypeScript SDK can:

- author a real ACLIP-compatible CLI
- bundle it into a runnable Node CLI artifact
- emit a sidecar `.aclip.json` manifest beside that artifact

Build locally:

```powershell
node --import tsx .\scripts\build.ts
```
