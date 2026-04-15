# aclip Implementation Plan

> **For agentic workers:** implement this plan with tests first and keep the first milestone limited to the smallest end-to-end closure.

**Goal:** ship the first `aclip` closed loop with a reference SDK and a packaged example binary CLI.

**Architecture:** canonical contracts in `schema/`, a Python reference adapter in `sdk/python/src/aclip/`, and a sample notes CLI in `sdk/python/examples/demo-notes/src/aclip_demo_notes/` that emits compliant envelopes and tree-shaped help surfaces.

**Tech Stack:** Python 3.12, setuptools, pytest, PyInstaller

---

## Task 1: lock the protocol surface

**Files:**

- `docs/PRD.md`
- `docs/SPEC.md`

Steps:

- freeze the smallest protocol core only
- avoid remote registry implementation details in this repo
- ensure `aclim` and `acli` can build on the manifest without redefining it later

## Task 2: write failing tests for the SDK and the demo CLI

**Files:**

- `sdk/python/tests/test_manifest.py`
- `sdk/python/tests/test_demo_cli.py`

Steps:

- write tests for manifest index generation
- write tests for command detail disclosure
- write tests for natural CLI execution and structured result envelopes

## Task 3: implement the reference SDK

**Files:**

- `sdk/python/src/aclip/contracts.py`
- `sdk/python/src/aclip/app.py`
- `sdk/python/src/aclip/runtime.py`

Steps:

- model commands, arguments, credentials, and manifests
- generate command detail and index disclosure from one source of truth
- emit structured result and error envelopes with stable exit codes

## Task 4: implement the example CLI

**Files:**

- `sdk/python/examples/demo-notes/src/aclip_demo_notes/app.py`
- `sdk/python/examples/demo-notes/src/aclip_demo_notes/__main__.py`

Steps:

- define `note create` and `note list`
- store notes in a local JSON file
- expose progressive disclosure through `--help` and `<command> --help`

## Task 5: package the binary and generate distribution metadata

**Files:**

- `sdk/python/examples/demo-notes/scripts/build.py`

Steps:

- build the one-file binary
- compute the binary sha256
- generate the sidecar `.aclip.json` manifest beside the binary

## Task 6: verify the closure

Steps:

- run unit tests
- build the binary
- execute the binary for both disclosure and normal command execution
- confirm the built artifact still behaves as a compliant `aclip` CLI
