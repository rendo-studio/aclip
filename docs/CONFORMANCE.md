# ACLIP Conformance

## 1. Truth source order

ACLIP protocol truth is ordered:

1. `schema/`
2. protocol docs under `docs/`
3. reference adapters

If an adapter disagrees with `schema/` or the protocol docs, the adapter is wrong.

## 2. What conformance means

An ACLIP-compatible adapter must produce protocol-visible surfaces that match canonical contracts.

Those surfaces are:

- sidecar manifest
- runtime help index payload
- runtime help command group payload
- runtime help command payload
- canonical Markdown help rendering
- error envelope

## 3. Cross-language requirement

Different language adapters may expose different authoring APIs.

They may not expose different protocol semantics.

Python and TypeScript reference adapters must therefore remain semantically equivalent for:

- reserved `--help` behavior
- manifest field meanings
- runtime Markdown section order
- error envelope shape
- default exit code semantics

## 4. Release verification

Before claiming release readiness, verify:

- Python tests pass
- TypeScript tests pass
- TypeScript type-check passes
- TypeScript build passes
- example Python binary rebuild passes
- shared schemas validate generated protocol payloads

## 5. Non-goals

Conformance does not require:

- identical internal parser implementations
- identical authoring ergonomics
- identical packaging toolchains

ACLIP standardizes protocol surfaces, not adapter internals.
