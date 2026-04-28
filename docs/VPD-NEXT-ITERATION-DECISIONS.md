# ACLIP Next Iteration VPD Decisions

## 1. Purpose

This document applies the VPD method to ACLIP's next iteration.

It answers only questions that meet one of two thresholds:

- a current pain is already visible and costly
- a future trend is deterministic enough that delaying would create avoidable debt

Anything that does not meet one of those thresholds should not enter the next ACLIP core milestone.

## 2. Evidence baseline

### Internal baseline

- [PRD.md](D:/project/rendo/aclip/docs/PRD.md)
- [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md)
- [INTERACTIVE-CLI-BOUNDARY.md](D:/project/rendo/aclip/docs/INTERACTIVE-CLI-BOUNDARY.md)
- [SESSION-CONTROL-PLANE.md](D:/project/rendo/aclip/docs/SESSION-CONTROL-PLANE.md)

### External baseline

- [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html)
- [FFprobe documentation](https://ffmpeg.org/ffprobe-all.html)
- [CLI-Anything](https://github.com/HKUDS/CLI-Anything)
- [CLI-Anything plugin / HARNESS direction](https://github.com/HKUDS/CLI-Anything/tree/main/cli-anything-plugin)
- [OpenCLI](https://github.com/jackwener/opencli)
- [mcp2cli](https://github.com/knowsuchagency/mcp2cli)

## 3. VPD framing

### Current verified pains

- Agents still lack a standard CLI-level auth contract.
- Large CLIs still need a standard diagnostic surface when commands fail, environments drift, or capability assumptions are wrong.
- Complex CLIs still need reusable skill-package export hooks, especially at the CLI and command level, without treating `workflows` as protocol truth.
- Existing adapter ecosystems prove that bridge, import, and skill-export tooling is useful, but also prove that those layers evolve faster than any stable core protocol should.

### Deterministic trends

- Agent-facing CLIs will keep needing explicit auth semantics because upstream service ecosystems are converging on OAuth, API keys, session tokens, and cached credentials rather than disappearing into one uniform model.
- Complex CLIs will keep needing layered discovery and typed introspection as command surfaces grow.
- Agent Skills-style packaging will remain useful because reusable instructions, scripts, references, and assets solve a different problem from runtime tools and APIs.

## 4. Decisions

### 4.1 Doctor and error standardization

- [x] **Q: Should ACLIP standardize `doctor`?**
  **A:** Yes, but not as a mandatory core command for every CLI. ACLIP should standardize a reserved optional `doctor` control surface and provide authoring hooks for consistent diagnostics.
  **Why:** `opencli doctor` and similar tools prove that environment diagnosis is a recurring agent pain. Agents need a predictable place to ask "what is broken?" without guessing custom commands.
  **How it should land:** As an optional control plane, similar in posture to the current session draft. ACLIP should define a recommended `doctor` command group shape, output expectations, and error vocabulary, while leaving product-specific checks to authors.

- [x] **Q: Should ACLIP standardize richer errors beyond the current envelope?**
  **A:** Yes. This belongs in core sooner than `doctor`.
  **Why:** Structured errors already exist in ACLIP core, but current envelopes are too thin for agent remediation. Agents often need retryability, remediation hints, and category-level error codes.
  **How it should land:** Extend the error contract with optional machine-useful fields such as remediation hint, retryability, and failure category. Provide author-friendly hooks in SDKs so authors can declare these without ad hoc JSON shaping.

- [x] **Q: Besides `doctor` and richer errors, what other verified CLI techniques are worth standardizing?**
  **A:** The validated next set is:
  - `help` alias plus subtree-scoped `--all`
  - auth control surface and credential source semantics
  - skill export hooks in the protocol/sdk layer
  - large-surface typed introspection patterns for future study
  **Why:** These are the patterns repeatedly validated by ACLIP's own goals plus signals from ffmpeg, mcp2cli, OpenCLI, CLI-Anything, and the Agent Skills open format. They improve discoverability, remediation, or workflow reuse without forcing ACLIP into live-session scope.

### 4.2 Auth standardization

- [x] **Q: When should auth standardization happen?**
  **A:** Immediately in the next core design milestone, before `acli` and `aclim`.
  **Why:** Auth is already the biggest unresolved core gap and a real current pain. Deferring it would force future layers to invent local semantics and then backfit them into ACLIP later.
  **How it should land:** Start with the smallest stable contract:
  - credential source vocabulary
  - auth-related error codes
  - recommended `auth` command group shape
  - clear separation between core auth contract and provider-specific flows

- [x] **Q: Should ACLIP standardize full OAuth/provider flows now?**
  **A:** No.
  **Why:** VPD rejects absorbing high-churn provider details into core before the minimal common contract is frozen. The next step is contract-level standardization, not universal auth implementation.

### 4.3 Agent skill hooks

- [x] **Q: Should ACLIP put skill export hooks into the current protocol/sdk line?**
  **A:** Yes.
  **Why:** The demand is real, the target skill format exists, and the earlier mistake was not "skill export itself" but incorrectly collapsing it into `workflows` and generic automatic conversion thinking.
  **How it should land:** ACLIP should define:
  - CLI-level skill package hooks
  - command-level skill package hooks
  - metadata alignment between ACLIP surfaces and Agent Skills package metadata
  while keeping developer-authored skill content as the source of truth

- [x] **Q: Should `workflows` remain the model for skill export?**
  **A:** No.
  **Why:** `workflows` were an overreach. They may later become an optional build input, but they should not be required or treated as the canonical export model.

### 4.4 What to absorb from ffmpeg

- [x] **Q: Is ffmpeg worth studying as a reference?**
  **A:** Yes, but selectively.
  **Why:** ffmpeg and ffprobe validate several durable patterns for very large CLI surfaces:
  - layered help depth such as normal help versus `-h full`
  - typed introspection by domain rather than a single flattened surface
  - explicit selector grammars for targeting sub-resources
  - structured machine-readable probe/error output via ffprobe writers and `-show_error`

- [x] **Q: What should ACLIP absorb from ffmpeg?**
  **A:** The useful lessons are:
  - large-surface help must be sliceable by subtree or typed domain
  - diagnostics should have a machine-readable inspection path, not only human text
  - stable selector grammar matters for complex command families

- [x] **Q: What should ACLIP not absorb from ffmpeg?**
  **A:** ACLIP should not copy:
  - cryptic terse flags as a design ideal
  - option sprawl as a single global namespace
  - overwhelming full-surface disclosure as the default experience

### 4.5 What to absorb from CLI-Anything plugin, OpenCLI, and mcp2cli

- [x] **Q: Should ACLIP absorb the CLI-Anything plugin methodology?**
  **A:** Partially, yes.
  **Why:** The validated value is not the full seven-phase generation pipeline itself. The validated value is the methodology around:
  - harness-driven generation
  - skill packaging
  - hub/discovery surfaces
  - explicit agent guidance
  ACLIP should absorb the methodology where it strengthens adapters, exporters, and scaffolding. It should not absorb a heavyweight auto-generation pipeline into core.

- [x] **Q: Should ACLIP absorb OpenCLI methodology?**
  **A:** Partially, yes.
  **Why:** OpenCLI validates:
  - optional `doctor`
  - clear split between stable commands and live interactive control
  - hub / registration / discovery value
  ACLIP should absorb the control-plane and layering lessons, not the browser daemon runtime or live-session mechanics.

- [x] **Q: Should ACLIP absorb mcp2cli methodology?**
  **A:** Partially, yes.
  **Why:** mcp2cli validates:
  - compact discovery modes such as `--list`, `--search`, `--compact`, and ranking
  - secret source indirection via `env:` and `file:`
  - OAuth token acquisition and caching as a repeatable CLI concern
  - baked wrappers as ecosystem tooling
  ACLIP should absorb the auth and discovery lessons where they define durable protocol value. It should keep ranking, baked wrappers, and bridge behavior in `acli` or other ecosystem tooling.

## 5. Priority order for the next iteration

The next iteration should follow this order:

1. **Auth standard design**
   Freeze the minimum auth contract before downstream tools invent local semantics.
2. **Richer error contract**
   Add machine-usable remediation hooks to core error semantics.
3. **Doctor control plane draft**
   Standardize a reserved optional diagnostic surface.
4. **Skill export hooks design**
   Freeze the minimum CLI-level and command-level skill hook model for Agent Skills-compatible export in the ACLIP protocol/sdk layer.
5. **Help alias plus subtree `--all`**
   Tighten the progressive disclosure ergonomics without adding paging complexity.

Current status:

- auth standard: complete
- richer error contract: minimum version complete
- doctor control plane: minimum version complete
- skill export hooks: minimum version complete in both reference SDKs
- help alias plus subtree `--all`: minimum version complete

## 6. What does not enter the next ACLIP core milestone

The following remain outside the next core milestone:

- full provider-specific OAuth implementations
- browser or daemon runtimes
- live-session interaction protocols
- `workflows` as protocol truth for skill export
- full automatic generation of skill bodies from CLI metadata alone
- usage-ranking systems
- baked wrapper installation flows
- full automatic CLI generation pipelines

Those are still valuable, but they belong in ecosystem tooling, optional extensions, or later layers beyond the current core line.
