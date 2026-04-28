# aclip Architecture

## 1. Layers

This repository now separates ACLIP into three layers:

1. protocol contracts
2. reference adapter
3. artifact build pipeline

## 2. Protocol contracts

Canonical contracts live in `schema/`.

These files are the machine-readable truth source for:

- sidecar manifest
- runtime help index data
- runtime help command group data
- runtime help command data
- error envelope

The optional compatibility helper `schema/result.schema.json` may still exist for SDK-owned convenience output, but it is not part of ACLIP core conformance.

If a reference adapter changes behavior, tests should fail unless the behavior still matches these schemas.

## 3. Reference adapters

This repository now carries two reference adapters:

- `sdk/python/`: Python reference adapter
- `sdk/typescript/`: TypeScript reference adapter

Their current internal parser backends are:

- Python: Click
- TypeScript: Commander

Their job is:

- let authors declare command groups, commands, arguments, and examples
- let authors declare nested command trees while compiling them to flat runtime paths
- let authors use decorator-based authoring on top of the same command contracts
- let authors attach portable credential declarations and optional auth control-plane skeletons
- let authors attach optional doctor control-plane skeletons
- let authors attach CLI-level and command-level skill export hooks
- reserve `--help` and `<command> --help` for protocol disclosure
- render canonical Markdown help from structured help data
- leave successful stdout author-owned while emitting ACLIP error envelopes
- expose SDK-owned packaging helpers for artifact generation and skill-package export

Their job is not:

- define protocol truth by itself
- be the only future implementation path
- force one CLI parser library forever
- define a general live-session, PTY, REPL, or TUI protocol
- take ownership of author session storage or session lifecycle logic

Using Click or Commander internally does not change the ACLIP protocol surface:

- authors still declare `CommandSpec` and `ArgumentSpec`
- authors may now declare nested `command_groups` and `commands`
- authors may also use decorator registration instead of manual spec construction
- ACLIP still renders canonical Markdown help itself
- ACLIP still owns error envelopes and help semantics
- adapter parser backends are implementation details

## 4. Build pipeline

`sdk/python/examples/demo-notes/scripts/build.py` is now the Python example build script and emits a sidecar manifest alongside the binary.

`sdk/typescript/examples/demo-notes/scripts/build.ts` is the equivalent TypeScript example build script and emits a sidecar manifest alongside a bundled Node CLI artifact.

`sdk/python/examples/demo-notes/scripts/export_skills.py` and `sdk/typescript/examples/demo-notes/scripts/export-skills.ts` prove the same adapters can export Agent Skills-compatible packages from developer-authored `SKILL.md` directories.

This proves:

- protocol contracts can drive real CLIs in multiple languages
- CLIs can be shipped through language-appropriate artifact pipelines
- runtime Markdown help and offline manifest are related but not identical
- skill-package export belongs in the protocol/sdk layer without collapsing into interoperability tooling

## 5. Why this separation matters

Without this split, ACLIP would collapse into one Python implementation detail.

With this split:

- the protocol can stay stable while adapters change
- future adapters can target Click, Typer, Node.js frameworks, Go, or Rust
- `rendo-cli`, `aclim`, and `acli` can consume the same protocol contracts
- long-lived interactive session behavior can stay outside the ACLIP core unless a separate protocol is justified
- any future session support can stay as an optional control plane instead of leaking into normal business command shapes
