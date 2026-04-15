# ACLIP Publishing Strategy

## Purpose

This document defines the only accepted publishing strategy for the ACLIP repository.

It exists to answer three questions clearly:

1. What is the canonical package name on each registry?
2. Which compatibility or competitive aliases are still worth shipping?
3. How do we publish without leaving naming ambiguity to individual maintainers?

The rule is simple:

- protocol truth stays at the repository root
- SDKs publish from their own package directories
- each package owns its own release script
- humans should not improvise registry names at publish time

## Strategic Goal

The publishing strategy exists to increase ACLIP's competitiveness and long-term growth, not just to make a release succeed technically.

That means:

- the shortest credible names we already secured should not be wasted
- canonical names should remain stable and obvious
- alias names should be used intentionally to improve discovery, adoption, and defensive positioning
- aliases must not drift into abandoned or stale packages that weaken trust in the brand

The repository should treat every already-claimed high-signal package name as an asset.

## Synchronized Alias Policy

There are only three acceptable states for a claimed package name:

1. canonical package
2. synchronized alias package
3. explicit forwarding or placeholder package with a documented reason

What is not acceptable:

- a previously secured package that silently stops updating
- a short alias that falls behind the canonical package
- a package that appears official but no longer reflects the current product

For ACLIP, the preferred policy is synchronized update whenever the alias is still useful and still under our control.

Why:

- it improves search and discovery on package registries
- it prevents competitors or stale third-party packages from owning the mindshare around the short name
- it keeps migration paths simple for users who start from the shortest obvious package name

## Registry Strategy

### GitHub

- Canonical repository: `rendo-studio/aclip`
- GitHub is the source repository, not a package alias layer.

### PyPI

- Canonical package: `rendo-aclip`
- Synchronized competitive alias: `aclip`

Why publish both:

- `rendo-aclip` is the stable first-party canonical name and should be the name used in documentation, issue reports, and future tooling.
- `aclip` is short, memorable, already secured, and improves discoverability and competitive positioning on PyPI.
- shipping both from the same SDK release keeps the short name useful without allowing it to drift into a separate product line

Important constraints:

- `rendo-aclip` and `aclip` must always carry the same released version.
- `rendo-aclip` is the real implementation package.
- `aclip` is a synchronized compatibility sibling and must not evolve independently.
- maintainers must not hand-publish only one of the two names unless there is an explicit break-glass decision.

### npm

- Canonical package: `@rendo-studio/aclip`

Why there is no npm short-name sibling:

- unscoped `aclip` is not practically available under current npm platform rules
- `@rendo-studio/aclip` is already secured and is the correct first-party execution surface
- forcing a fake alias strategy on npm would add maintenance noise without durable upside

## Family-Level Naming Posture

ACLIP does not own every ACL-family package name by itself, but this repository should still follow the same family policy:

- if a claimed name is the canonical first-party package for a product, it must be actively maintained
- if a claimed name is a short alias for a product and remains useful, it should be synchronized
- if a claimed name is only defensive, it must still have an explicit documented status and must not look abandoned by accident

Current family-level examples from the broader Rendo strategy:

- canonical first-party names:
  - `rendo-acli`
  - `rendo-aclim`
  - `rendo-aclip`
  - `@rendo-studio/acli`
  - `@rendo-studio/aclim`
  - `@rendo-studio/aclip`
- synchronized short-name opportunities on PyPI:
  - `aclim`
  - `aclip`
- names that should never be left ambiguous just because they were previously secured:
  - `aclp`
  - `aclm`
  - other family placeholders already claimed

This repository directly owns only the ACLIP release flow, but its strategy should stay compatible with the broader family rule:

- do not waste secured names
- do not let alias packages drift
- do not force every alias into core protocol maintenance

## Why This Does Not Belong In Core

Publishing strategy is not protocol truth.

It depends on:

- registry-specific naming rules
- account ownership
- defensive namespace posture
- ecosystem competition
- packaging mechanics

Those concerns change faster than the ACLIP core protocol.

If this logic lived inside core, every registry naming adjustment would create unnecessary protocol churn.

Keeping it in package-local release scripts gives us:

- clear ownership per SDK
- decoupled maintenance by ecosystem
- a stable protocol core
- the ability to adapt registry strategy later without redesigning ACLIP itself

## Why Package-Local Release Scripts Are Mandatory

Registry strategy must be executable, not just documented.

Therefore:

- Python release decisions must live in `sdk/python/scripts/publish.py`
- TypeScript release decisions must live in `sdk/typescript/scripts/publish.mjs`

This avoids ambiguity because:

- the canonical package name is encoded in the package itself
- alias publication policy is encoded in the package itself
- release verification runs from the package itself
- maintainers do not need to remember ad hoc commands or naming exceptions

## Current Release Policy

### Python SDK

- package directory: `sdk/python`
- canonical distribution: `rendo-aclip`
- synchronized alias distribution: `aclip`
- import package: `aclip`

Expected script behavior:

- build canonical and alias artifacts together
- verify both with `twine check`
- publish both in one release flow

### TypeScript SDK

- package directory: `sdk/typescript`
- canonical distribution: `@rendo-studio/aclip`
- no short-name npm alias

Expected script behavior:

- run tests, typecheck, and build
- verify the publishable package surface
- publish the canonical scoped package

## Release Commands

### Python

From `sdk/python`:

```powershell
..\..\..\.venv\Scripts\python.exe .\scripts\publish.py check
..\..\..\.venv\Scripts\python.exe .\scripts\publish.py publish
```

Required environment:

- `PYPI_TOKEN`

### TypeScript

From `sdk/typescript`:

```powershell
node .\scripts\publish.mjs check
node .\scripts\publish.mjs publish
```

Required environment:

- `NPM_TOKEN`

## Long-Term Value

This strategy is still worth maintaining in the future.

Why:

- the canonical package names remain the cleanest first-party entrypoints
- the short aliases remain useful as long as they materially improve discoverability and defensive positioning
- package-local release logic lets us evolve registry tactics without destabilizing the ACLIP protocol

When it stops being worth it:

- if a registry alias becomes harmful, misleading, or impossible to maintain safely
- if the ecosystem no longer benefits from the short-name sibling

If that happens, we can retire or freeze the alias in the release script without changing ACLIP core or SDK authoring APIs.
