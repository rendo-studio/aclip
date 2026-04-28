# ACLIP Ten-Year Agent TODO

## Purpose

This document is the current production TODO for pushing ACLIP toward a durable ten-year agent foundation.

It is intentionally narrow.

Per VPD, this file includes only items that satisfy at least one of these conditions:

- a current pain is already visible and costly
- a future trend is deterministic enough that delaying would create avoidable debt

Reference:

- [VPD.md](D:/project/rendo/docs/project-introduction/core/VPD.md)

## Already complete

- [x] natural CLI invocation remains the default
- [x] progressive disclosure help surface is standardized
- [x] author-owned success output and structured errors are standardized
- [x] auth contract and auth control-plane hooks exist
- [x] doctor control-plane hooks exist
- [x] Python and TypeScript reference SDKs exist

## Current release scope

The current release scope is limited to the smallest VPD-justified next step:

- production-grade skill export hooks and package export for Agent Skills-compatible skill packages

The following are explicitly out of scope for this TODO:

- full automatic generation of skill bodies from CLI metadata
- reintroducing `workflows` as protocol truth
- external `acli`-dependent export flows
- registry and remote distribution systems
- live-session protocol standardization

## TODO

### 1. Skill export protocol/sdk surface

- [x] Freeze the minimum CLI-level skill hook shape
- [x] Freeze the minimum command-level skill hook shape
- [x] Freeze the metadata alignment rules between ACLIP surfaces and exported skill packages
- [x] Freeze the rule that developer-authored skill content remains the source of truth

### 2. Python production implementation

- [x] Add Python skill hook contracts and app registration hooks
- [x] Add Python Agent Skills package export utility
- [x] Add Python export validation for `SKILL.md` and package shape
- [x] Add Python tests for CLI-level and command-level export

### 3. TypeScript production implementation

- [x] Add TypeScript skill hook contracts and app registration hooks
- [x] Add TypeScript Agent Skills package export utility
- [x] Add TypeScript export validation for `SKILL.md` and package shape
- [x] Add TypeScript tests for CLI-level and command-level export

### 4. Demo and documentation

- [x] Add demo skill package sources for the notes example
- [x] Add end-to-end export examples to Python docs
- [x] Add end-to-end export examples to TypeScript docs
- [x] Update architecture and product docs to reflect the implemented skill export surface

### 5. Production verification and release

- [x] Run focused Python verification
- [x] Run focused TypeScript verification
- [x] Run full Python test suite
- [x] Run full TypeScript test suite
- [x] Run release checks for both packages
- [x] Bump release versions for the new public surface
- [x] Publish Python package
- [x] Publish TypeScript package

Published release:

- PyPI: `rendo-aclip==0.3.4`
- PyPI alias: `aclip==0.3.4`
- npm: `@rendo-studio/aclip@0.3.4`

## Completion rule

This TODO is complete only when every unchecked item above is done and the repository is in release-ready condition for the implemented scope.
