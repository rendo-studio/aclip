# aclip PRD

## 1. Core demand

`aclip` exists to solve one demand:

**Agents need a CLI standard that stays natural like a traditional CLI, but is no longer human-first in its disclosure, output, auth, and portability model.**

Today the market is stuck between bad options:

1. keep consuming human-first CLIs with brittle parsing and token waste
2. keep building one-off wrappers that never become a stable standard
3. keep pushing everything into MCP or HTTP even when the natural product surface should remain a CLI

ACLIP exists to make a fourth path real:

- natural CLI invocation
- agent-first progressive disclosure
- structured runtime outputs
- stable machine-readable contracts
- cheap SDK authoring
- future portability across registries, runtimes, and languages

If a feature does not clearly move ACLIP toward that demand, it is out of scope or should be postponed.

## 2. Final target

The final target is not "a useful Python SDK" and not "a nice demo CLI".

The final target is:

**a clear, unified, low-ambiguity, low-overhead standard for agent-native CLIs, with reference adapters that make compliant CLI construction cheap enough to become the default.**

In practical terms, the finished direction must be strong enough that:

- a new product can choose ACLIP as its default CLI contract
- `rendo-cli` can be built on it without inventing local conventions
- future distribution and execution layers such as `aclim` and `acli` can depend on it without rewriting core semantics
- different language adapters can stay semantically equivalent

## 3. Current repository milestone

This repository is currently focused on the ACLIP core, not the full family.

Current milestone:

**ship a release-grade ACLIP core with canonical contracts, protocol docs, and Python plus TypeScript reference adapters.**

That milestone is complete only when all of the following are true:

1. the protocol truth source is explicit and enforceable
2. the runtime help format is stable and protocol-level
3. the runtime result and error shapes are stable and cross-language
4. Python and TypeScript reference adapters conform to the same protocol surfaces
5. each adapter can produce a real CLI artifact plus sidecar manifest

## 4. Guardrails

The following constraints exist to keep ACLIP on-topic.

### 4.1 Agent-first, not human-first

If a design choice does not clearly help agents, it is probably unnecessary complexity.

### 4.2 Natural CLI invocation

ACLIP cannot require a magic wrapper or mandatory agent-only flag to run a command.

That means normal execution must remain:

```text
tool subcommand --flag value
```

### 4.3 Progressive disclosure, not up-front overload

Agents should not need to ingest the full product surface on the first turn.

### 4.4 Non-interactive core

ACLIP standardizes one-shot CLI invocations only.

Wizard prompts, REPLs, TUIs, PTY control, and live session behavior are outside the ACLIP core unless they can also be flattened into normal commands.

### 4.5 Stable core, extensible ecosystem

ACLIP should freeze the smallest useful stable core and push adoption tooling, importers, exporters, registries, and migration helpers into ecosystem layers unless they truly belong in the protocol.

This is especially important for compatibility layers around external systems such as:

- MCP
- OpenAPI
- legacy human-first CLIs
- skill packaging for specific agent runtimes

Those surfaces evolve faster than ACLIP core and often involve lossy or tool-specific mappings.

Therefore ACLIP should prefer:

- a stable core protocol
- decoupled adapters, extensions, plugins, and import/export tooling on top of that core

rather than bloating the core with fast-moving interoperability logic.

## 5. Research baseline

This PRD is grounded in the ecosystem signals that matter most to the problem.

### Input projects

- [Model Context Protocol](https://modelcontextprotocol.io)
- [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk)
- [jackwener/opencli](https://github.com/jackwener/opencli)
- [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
- [knowsuchagency/mcp2cli](https://github.com/knowsuchagency/mcp2cli)
- [@lifeprompt/acli](https://www.npmjs.com/package/@lifeprompt/acli)
- [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html)
- [FFprobe documentation](https://ffmpeg.org/ffprobe-all.html)

### What these projects show

- MCP proves that structured machine tooling matters, but its tool schemas are still verbose and remote-first.
- CLI-Anything proves demand for agent-usable CLIs, but mainly solves wrapper generation and distribution around existing software.
- `@lifeprompt/acli` proves there is appetite for CLI-shaped agent interaction and compact discovery, but it remains an MCP command gateway rather than a standalone CLI standard.
- OpenCLI and `mcp2cli` prove demand for adapters, bridges, and import surfaces, but not a stable contract for newly built agent-native CLIs.
- FFmpeg and FFprobe prove that very large CLI surfaces need typed introspection, layered help depth, and machine-readable diagnostics, but they also show how quickly global flag sprawl becomes hostile to both humans and agents if it is not constrained.

## 6. Q&A tracker

This section is the working control panel for the project.

Rules:

- every question belongs to one category
- if a question has been answered clearly enough to guide execution, it must be checked
- every checked answer must explain how the answer was achieved or where it is enforced
- unchecked items are still open, even if they are partially understood

### 6.1 Pain points and core answers

- [x] **Q: What demand is ACLIP actually solving?**
  **A:** ACLIP solves the need for a CLI standard that remains natural like a traditional CLI while standardizing the machine-facing parts that agents actually depend on: discovery, envelopes, auth declarations, and distribution reservation.
  **How this was completed:** This PRD now defines the core demand and final target explicitly. The protocol scope is enforced in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md).

- [x] **Q: How does an ACLIP CLI run without forcing unnatural invocation?**
  **A:** Normal execution stays natural and cannot depend on special protocol-only flags.
  **How this was completed:** The rule is defined in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md), and both reference adapters preserve natural invocation in [sdk/python/src/aclip/app.py](D:/project/rendo/aclip/sdk/python/src/aclip/app.py) and [sdk/typescript/src/app.ts](D:/project/rendo/aclip/sdk/typescript/src/app.ts).

- [x] **Q: How do agents discover capability without ingesting the whole CLI at once?**
  **A:** ACLIP reserves `--help` and `<path> --help` as canonical progressive disclosure surfaces with constrained Markdown output.
  **How this was completed:** The disclosure contract is defined in [PROGRESSIVE-DISCLOSURE-MARKDOWN-SPEC.md](D:/project/rendo/aclip/docs/PROGRESSIVE-DISCLOSURE-MARKDOWN-SPEC.md) and implemented in both renderers: [sdk/python/src/aclip/render_markdown.py](D:/project/rendo/aclip/sdk/python/src/aclip/render_markdown.py) and [sdk/typescript/src/renderMarkdown.ts](D:/project/rendo/aclip/sdk/typescript/src/renderMarkdown.ts).

- [x] **Q: How do we avoid free-form help drift across implementations?**
  **A:** Runtime help is not ad hoc copywriting. It is a protocol surface with fixed section order, fixed omission rules, and fixed next-step guidance.
  **How this was completed:** The canonical runtime help rules live in [PROGRESSIVE-DISCLOSURE-MARKDOWN-SPEC.md](D:/project/rendo/aclip/docs/PROGRESSIVE-DISCLOSURE-MARKDOWN-SPEC.md), and schema-backed help payloads live under [schema](D:/project/rendo/aclip/schema).

- [x] **Q: How do we keep command results parseable by agents?**
  **A:** ACLIP requires structured JSON result and error envelopes by default.
  **How this was completed:** The envelope contract lives in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md), [result.schema.json](D:/project/rendo/aclip/schema/result.schema.json), and [error.schema.json](D:/project/rendo/aclip/schema/error.schema.json), and is implemented in both adapters.

- [x] **Q: How do we keep protocol truth from collapsing into one SDK implementation?**
  **A:** Protocol truth is ordered: `schema/` first, protocol docs second, reference adapters third.
  **How this was completed:** This is now explicit in [CONFORMANCE.md](D:/project/rendo/aclip/docs/CONFORMANCE.md), [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md), and [ARCHITECTURE.md](D:/project/rendo/aclip/docs/ARCHITECTURE.md).

- [x] **Q: How do we avoid getting trapped in one implementation language?**
  **A:** ACLIP is protocol-first and now has both Python and TypeScript reference adapters with cross-language conformance expectations.
  **How this was completed:** Python now lives under [sdk/python](D:/project/rendo/aclip/sdk/python), TypeScript now lives under [sdk/typescript](D:/project/rendo/aclip/sdk/typescript), and their relationship is defined in [CONFORMANCE.md](D:/project/rendo/aclip/docs/CONFORMANCE.md).

- [x] **Q: How do we stop live-session scope creep from derailing the core?**
  **A:** ACLIP explicitly standardizes non-interactive one-shot CLI invocations only.
  **How this was completed:** The boundary is locked in [INTERACTIVE-CLI-BOUNDARY.md](D:/project/rendo/aclip/docs/INTERACTIVE-CLI-BOUNDARY.md) and restated in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md).

### 6.2 Scope and architecture decisions

- [x] **Q: What is inside ACLIP core today?**
  **A:** Natural invocation, progressive disclosure, structured envelopes, credential declaration, distribution reservation, canonical schemas, and cross-language conformance.
  **How this was completed:** The current core surface is defined in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md) and backed by [schema](D:/project/rendo/aclip/schema).

- [x] **Q: What is explicitly outside ACLIP core today?**
  **A:** Registry APIs, remote download flows, full auth provider standardization, PTY/REPL/TUI/live-session protocols, and arbitrary implementation-specific help formats.
  **How this was completed:** These non-goals are stated in [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md), [INTERACTIVE-CLI-BOUNDARY.md](D:/project/rendo/aclip/docs/INTERACTIVE-CLI-BOUNDARY.md), and [ARCHITECTURE.md](D:/project/rendo/aclip/docs/ARCHITECTURE.md).

- [x] **Q: What is the current release-grade proof that ACLIP works?**
  **A:** The repository now ships Python and TypeScript reference adapters plus working demo artifacts in both ecosystems.
  **How this was completed:** The Python demo now lives in [sdk/python/examples/demo-notes](D:/project/rendo/aclip/sdk/python/examples/demo-notes), and the TypeScript demo lives in [sdk/typescript/examples/demo-notes](D:/project/rendo/aclip/sdk/typescript/examples/demo-notes).

### 6.3 Accepted directions for next stages

- [x] **Q: Should ACLIP provide interoperability surfaces such as `import mcp`, `export mcp`, `import openapi`, `import cli`, and `export skill`?**
  **A:** Yes. These are worth doing, but they should be provided as ACLIP adapters, extensions, plugins, or ecosystem tooling rather than entering ACLIP core.
  **How this was answered:** We concluded that ACLIP now has a more native protocol foundation than point solutions like `mcp2cli` or MCP command gateways. That makes these capabilities natural to add on top of ACLIP contracts. They still do not belong in core because they depend on external systems whose semantics evolve independently and often cannot be mapped without loss.

- [x] **Q: Why should these interoperability capabilities stay outside ACLIP core?**
  **A:** Because they are interoperability concerns, not core CLI protocol semantics.
  **How this was answered:** ACLIP core should standardize the stable contract for agent-native CLIs. By contrast, `import mcp`, `export mcp`, `import openapi`, `import cli`, and `export skill` all depend on external schemas, upstream protocol changes, and target-runtime conventions. Keeping them decoupled prevents fast-moving bridge logic from destabilizing the core.

- [x] **Q: Why is decoupled maintenance the correct strategy here?**
  **A:** Because these integrations will drift at different speeds and for different reasons.
  **How this was answered:** MCP, OpenAPI ecosystems, legacy CLIs, and skill packaging targets will all change independently. If ACLIP core absorbs that churn directly, the core becomes harder to freeze and harder to reason about. If adapters and plugins absorb the churn instead, ACLIP can remain stable while ecosystem tooling keeps evolving.

- [x] **Q: Will these import/export capabilities still be worth sustaining in the future if upstream systems improve?**
  **A:** Yes, but their value will likely shift.
  **How this was answered:** Even if MCP or other upstream systems eventually solve today’s biggest pain points natively, ACLIP-side adapters still retain value as bridge, migration, normalization, and export tooling. Over time they may become less important as substitutes and more important as interoperability layers. That is still worth sustaining, but it does not justify pulling them into core.

- [x] **Q: Should ACLIP support skill export?**
  **A:** Yes, but not as protocol truth. Skill export should be a derived ecosystem artifact generated from ACLIP contracts.
  **How this was answered:** We decided that skills solve discoverability and agent instruction packaging, but they belong in `acli` or SDK tooling, not ACLIP core.

- [x] **Q: Should `mcp2cli`-style work be absorbed, and where?**
  **A:** Yes, but the higher-value direction is MCP client to ACLI import or bridge tooling, not redefining ACLIP core around MCP server command gateways.
  **How this was answered:** We concluded that import and bridge tooling is ecosystem value, likely under `acli`, rather than a core protocol concern.

- [x] **Q: Should we build `cli2acli` for traditional CLI migration?**
  **A:** Yes, as a scaffold or migration assistant, not as a promise of perfect automatic conversion.
  **How this was answered:** We concluded that legacy CLI migration is real adoption value, but its correct shape is starter generation and manifest/spec scaffolding, not pretending arbitrary CLIs can be losslessly converted.

- [x] **Q: Should auth become a standardized ACLIP concern?**
  **A:** Yes. This is one of the most important next core directions.
  **How this was answered:** We concluded that ACLIP should standardize auth contracts at the protocol level: credential slot semantics, auth-related error codes, and a recommended `auth` control surface. Full provider-specific flows are later work.

- [x] **Q: When should auth standardization happen?**
  **A:** Immediately in the next core design milestone, before `acli` and `aclim`.
  **How this was answered:** VPD review now treats auth as both a current pain and a deterministic dependency for downstream layers. Deferring it would force local conventions into later products. The iteration order is now recorded in [VPD-NEXT-ITERATION-DECISIONS.md](D:/project/rendo/aclip/docs/VPD-NEXT-ITERATION-DECISIONS.md).

- [x] **Q: Should ACLIP expose a default `help` command alias and `--all` expansion?**
  **A:** Yes, but only as a lightweight extension. `help` can be an alias to the canonical `--help` behavior, and `--all` can expand the current subtree. We should not invent a paging protocol now.
  **How this was answered:** We concluded that `help` alias plus `--all` improves weaker-agent usability, while paging introduces unnecessary state and protocol weight.

- [x] **Q: Should ACLIP standardize `doctor` and richer remediation errors?**
  **A:** Yes, but they land at different layers. Richer remediation fields belong in the core error contract sooner. `doctor` belongs as an optional reserved control plane, not as a mandatory core command for every CLI.
  **How this was answered:** VPD review found that environment diagnosis and remediation are recurring real pains across agent-facing CLIs, while a mandatory `doctor` command would be unnecessary overhead for smaller tools. The current direction is recorded in [VPD-NEXT-ITERATION-DECISIONS.md](D:/project/rendo/aclip/docs/VPD-NEXT-ITERATION-DECISIONS.md).

- [x] **Q: Should ACLIP provide a hook for named agent skills or workflows?**
  **A:** Yes, but as optional metadata or export-layer hooks, not as core runtime command semantics.
  **How this was answered:** We concluded that complex workflows need reusable task-oriented guidance, but that guidance should remain an extension surface that can feed skill export and agent packaging rather than polluting command execution semantics.

- [x] **Q: Should ACLIP absorb lessons from FFmpeg, CLI-Anything plugin, OpenCLI, and `mcp2cli`?**
  **A:** Yes, selectively.
  **How this was answered:** The next-iteration VPD review concluded that ACLIP should absorb layered help, typed introspection, machine-readable diagnostics, optional diagnostic control planes, skill/export methodology, and auth/discovery lessons. It should not absorb live browser runtimes, REPL/session mechanics, heavy auto-generation pipelines, or ranking systems into core. See [VPD-NEXT-ITERATION-DECISIONS.md](D:/project/rendo/aclip/docs/VPD-NEXT-ITERATION-DECISIONS.md).

### 6.4 Open questions that remain unresolved

- [ ] **Q: What is the minimum ACLIP auth standard for the next milestone?**
  **A:** Solved.
  The minimum auth standard is now:
  - core credential sources: `env` and `file`
  - reserved portable auth error codes: `auth_required`, `invalid_credential`, `expired_credential`
  - optional reserved `auth` control plane with `auth login`, `auth status`, and `auth logout`
  - detailed credential declarations in the sidecar manifest, not dumped into runtime help by default
  **How this was completed:** The contract is now written into [AUTH-STANDARD.md](D:/project/rendo/aclip/docs/AUTH-STANDARD.md) and [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md), with matching SDK implementations in [sdk/python/src/aclip](D:/project/rendo/aclip/sdk/python/src/aclip) and [sdk/typescript/src](D:/project/rendo/aclip/sdk/typescript/src).

- [ ] **Q: What is the minimum richer error contract for the next milestone?**
  **A:** Not solved yet.
  The next pass should answer:
  - which extra error fields are core versus optional
  - whether retryability is standardized
  - how remediation hints are represented
  - which codes are reserved versus author-defined

- [ ] **Q: What is the minimum `doctor` control plane shape?**
  **A:** Not solved yet.
  The next pass should answer:
  - whether `doctor` is a reserved top-level command or command group
  - what result payload shape it uses
  - whether checks are categorized
  - which exit-code and error interactions are required

- [ ] **Q: What is the minimum metadata shape for named agent skills or workflows?**
  **A:** Not solved yet.
  The next pass should answer:
  - whether the hook is called `skills`, `workflows`, or another name
  - what fields are mandatory
  - whether it lives in the manifest, a sidecar companion, or export-only tooling
  - how it maps to future skill export targets

- [ ] **Q: What is the exact export format for skill generation?**
  **A:** Not solved yet.
  The next pass should decide whether ACLIP exports one canonical intermediate skill model or multiple target-specific generators.

- [ ] **Q: What is the exact shape of `mcp -> acli` and `cli -> acli` tooling?**
  **A:** Not solved yet.
  The next pass should decide whether these become `acli import ...` commands, standalone tools, or SDK-side generators.

- [ ] **Q: What is the exact adapter/plugin architecture for interoperability features?**
  **A:** Not solved yet.
  The next pass should decide:
  - whether interoperability lives under `acli`, separate packages, or both
  - what the canonical adapter interface is
  - what parts are maintained by first-party ACLIP tooling versus third-party plugins
  - how import/export tools declare lossiness, unsupported features, and generated scaffolds

- [ ] **Q: What is the exact syntax and semantics of `help` alias and `--all`?**
  **A:** Not solved yet.
  The direction is accepted, but the concrete protocol behavior is not yet written into [SPEC.md](D:/project/rendo/aclip/docs/SPEC.md).

## 7. Users

### Primary users

- developers building new agent-native CLIs
- Rendo itself, which will use ACLIP to build `rendo-cli`

### Secondary users

- future registries such as `aclim`
- future execution clients such as `acli`
- agent runtimes that need stable CLI disclosure
- migration and import tooling built on top of ACLIP contracts

## 8. Non-goals for the current core

- build the online `aclim` registry
- build the remote execution client `acli`
- standardize live-session PTY/REPL/TUI behavior
- define every provider-specific auth flow now
- make skill export the protocol truth source
- promise full automatic conversion for arbitrary legacy CLIs
- absorb MCP/OpenAPI/legacy-CLI interoperability logic directly into ACLIP core

## 9. Implementation posture

Python was the first reference adapter because it was the fastest route to a closed loop in the current environment.

That is not a protocol limitation.

The repository now treats:

- [sdk/python](D:/project/rendo/aclip/sdk/python) as the Python reference adapter
- [sdk/typescript](D:/project/rendo/aclip/sdk/typescript) as the TypeScript reference adapter
- [schema](D:/project/rendo/aclip/schema) as the machine-readable truth source

That split is deliberate. ACLIP must remain stable even when adapters, build toolchains, or packaging ecosystems change.
