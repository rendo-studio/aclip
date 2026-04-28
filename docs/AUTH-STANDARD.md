# ACLIP Auth Standard

## 1. Scope

This document defines the minimum ACLIP auth standard for the current core line.

It standardizes:

- credential source vocabulary
- auth-related error codes
- the optional reserved `auth` control plane shape

It does not standardize:

- provider-specific OAuth flows
- browser/device code flows
- token storage backends
- credential refresh implementations

## 2. Credential sources

Current core credential sources are:

- `env`
- `file`

### 2.1 `env`

Use `env` when the CLI expects a secret directly from an environment variable.

Required fields:

- `name`
- `source = "env"`
- `required`
- `description`
- `envVar`

### 2.2 `file`

Use `file` when the CLI expects a local file path that contains a credential or token material.

Required fields:

- `name`
- `source = "file"`
- `required`
- `description`
- `path`

## 3. Auth error vocabulary

Current core auth-related error codes are:

- `auth_required`
- `invalid_credential`
- `expired_credential`

These codes are reserved and portable.

Authors may still define additional product-specific error codes.

## 4. Optional `auth` control plane

ACLIP does not require every CLI to implement auth commands.

When a product needs an explicit auth lifecycle, the reserved top-level command group is:

```text
auth
```

Current recommended baseline commands are:

- `auth login`
- `auth status`
- `auth logout`

These commands are optional and author-owned.

ACLIP may provide SDK skeletons for them, but authors still own:

- descriptions
- handlers
- storage
- provider-specific flows

### 4.1 Recommended `auth status` result shape

Successful auth output remains author-owned.

For agent-friendly interoperability, `auth status` should prefer a small structured payload:

```json
{
  "state": "authenticated",
  "principal": "dev@rendo.cn",
  "expires_at": "2026-04-21T00:00:00Z",
  "next_actions": [
    {
      "summary": "refresh before expiry",
      "command": "notes auth login"
    }
  ]
}
```

Recommended `state` vocabulary:

- `authenticated`
- `unauthenticated`
- `expired`
- `partial`
- `unknown`

Recommended optional fields:

- `principal`
- `expires_at`
- `missing_credentials`
- `next_actions`
- `guidance_md`

This keeps `auth status` small, predictable, and easy for agents to act on without forcing provider-specific fields into the core.

## 5. Runtime help versus sidecar metadata

Detailed credential declarations belong in the sidecar manifest.

Runtime help should not dump full credential metadata by default.

Instead:

- the manifest carries machine-readable credential declarations
- the optional `auth` control plane carries runtime guidance when a product exposes explicit auth commands

This keeps runtime help small while preserving machine-readable auth contracts.
