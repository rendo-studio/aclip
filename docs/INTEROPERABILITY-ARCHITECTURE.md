# ACLIP Interoperability Architecture

## 1. Status

Only the boundary is settled:

- interoperability belongs outside ACLIP core
- the exact import/export UX is not settled yet
- skill export is not part of this interoperability architecture document

## 2. What is currently decided

ACLIP core owns:

- protocol docs
- schemas
- reference SDKs
- skill export hooks and skill-package export design

Future interoperability work should live in `acli`-side tooling or separate companion packages.

That includes any future work such as:

- `import mcp`
- `import openapi`
- `import cli`

Those are directionally valid ecosystem surfaces, but their exact command shapes are still open.

Skill export is different:

- it should not depend on `acli`
- it belongs in ACLIP protocol/sdk design
- it is documented separately in [SKILL-EXPORT-HOOKS-VPD.md](D:/project/rendo/aclip/docs/SKILL-EXPORT-HOOKS-VPD.md)

## 3. What is not yet resolved

The following are intentionally unresolved:

- whether `acli import ...` is the final UX for each source
- what the adapter/plugin interface should be
- how lossiness, missing context, and author overrides are reported

## 4. Current rule

Do not freeze exact interoperability commands or adapter interfaces into ACLIP core before one validated end-to-end experiment exists.

## 5. Why this boundary still matters

Even though the exact UX is open, the boundary is still valuable:

- core remains stable
- experiments can move faster
- failed adapter ideas do not pollute protocol semantics
- target-specific skill packaging can evolve independently
