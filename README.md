# aclip

`aclip` is the reference repository for the Agent Command Line Interface Protocol.

The repository is intentionally split into two layers:

- **protocol layer at the root**
  - [docs](/D:/project/rendo/aclip/docs)
  - [schema](/D:/project/rendo/aclip/schema)
- **reference adapters under [sdk](/D:/project/rendo/aclip/sdk)**
  - [sdk/python](/D:/project/rendo/aclip/sdk/python)
  - [sdk/typescript](/D:/project/rendo/aclip/sdk/typescript)

## Repository layout

```text
aclip/
  docs/
  schema/
  sdk/
    python/
    typescript/
```

Root ownership:

- `docs/`: protocol and product documents
- `schema/`: canonical machine-readable contracts
- `sdk/python/`: Python reference adapter package plus example CLI
- `sdk/typescript/`: TypeScript reference adapter package plus example CLI

Canonical package entrypoints:

- PyPI: `rendo-aclip`
- PyPI short-name alias: `aclip`
- npm: `@rendo-studio/aclip`

## Current status

The repository currently proves:

- a stable ACLIP core with canonical Markdown help, author-owned success output, and structured errors
- cross-language reference adapters in Python and TypeScript
- working example CLI artifacts in both ecosystems

## Local verification

Python:

```powershell
cd .\sdk\python
..\..\..\.venv\Scripts\python.exe -m pytest tests -q
..\..\..\.venv\Scripts\python.exe .\examples\demo-notes\scripts\build.py
```

TypeScript:

```powershell
cd .\sdk\typescript
npm install
npm test
npm run check
npm run build
node --import tsx .\examples\demo-notes\scripts\build.ts
```
