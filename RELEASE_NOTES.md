# Agent Session Manager (`ax`) Specification v0.5.0

This minor specification release adds the first-class TerminalBackend contract
family over immutable `v0.4.3` history. It is a specification-only release:
this repository contains no `ax` binary, proves no product implementation
available, and does not claim that any Section 19 platform or provider lane has
passed. This release publishes specification artifacts only.

## Authority and module boundary

AX remains the sole authority for LogicalSession identity and lineage,
Owner/Replica state, leases and fencing, provider lifecycle and native state,
workspace/materialization, checkpoints and evidence, task-board integration,
mesh replication, and takeover.

A TerminalBackend owns only one host-local TerminalInstance: AX-delegated
PTY/process hosting, presentation and attach/reconnect, backend-local IPC, and
backend-specific process observation. Attach clients and presentation mirrors
are not AX Replicas and never acquire, renew, or transfer ownership. Every
backend ultimately executes exactly `ax pane SESSION_ID`; a raw provider command
is not a durable entry point.

## Current targets and future candidates

- `ax.tmux` remains the mandatory built-in Unix target on macOS, Linux, and
  WSL2. It uses an AX-owned private runtime directory, a dedicated `tmux -S`
  server, no ambient/default server reuse, and the existing macOS Aqua broker
  plus functional sentinel and provider-auth evidence.
- `ax.conpty` remains the native-Windows built-in path under the same semantic
  boundary. The specification does not claim tmux-equivalent durability for
  ConPTY.
- Superlogical is an unavailable, non-normative, future-only candidate. No
  normative ID is reserved and no API, SDK, support, compatibility, automation,
  or conformance behavior is invented by this release.

These are normative specification targets, not implementation-availability
claims.

## Contracts and compatibility

| Contract | v0.5.0 disposition |
| --- | --- |
| Terminal Backend protocol / manifest / probe | New independently versioned `1.0.0` family |
| Terminal Instance binding / capability evidence | New independently versioned `1.0.0` schemas |
| Configuration | New `3.0.0` selection/policy shape; Configuration 1/2 remain immutable |
| Provider Protocol | New `3.0.0` Terminal Instance descriptor; Provider 2 remains immutable |
| Session Event | New `4.0.0` Terminal Instance binding events; older majors remain immutable |
| Mesh RPC | New `4.0.0` sanitized backend-evidence replication; RPC 2/3 remain dual-readable as specified |
| Structured Error | New `1.3.0` TerminalBackend surface binding; earlier bindings remain exact |
| CLI Result | New `4.0.0` backend inspection and generalized start/resume results |

Historical `tmux|conpty` values translate exactly into the new built-in IDs only
at the explicit compatibility boundary. Readers never rewrite or re-digest
historical self-identifying objects. Unknown or unsupported backend history may
remain browseable/synchronizable where the negotiated containing contract
allows it, but it cannot activate, silently downgrade, or trigger restore
fallback.

## Lifecycle, capabilities, and evidence

The semantic boundary closes backend identity, generation, manifest/probe
agreement, states, operations, deadlines, retry disposition, and capability
evidence. It defines `manifest`, `probe`, `create`, `attach`, `status`,
`quiesce-input`, `wait-safe-boundary`, `request-stop`, `terminate-stale`, and
`restore`. Create preserves `(session_id, bootstrap_operation_id)` idempotency
across controller crash and lost result. Attach remains ownership-observational.

Capabilities are closed, versioned, and fail closed. Claims must reproduce from
the required static or probed evidence and may vary by backend generation only
where declared. Multi-attach, remote/web attach, and multiple authorized input
clients are independent capabilities; one never implies another.

## Security and credential realm

Runtime IPC, tmux sockets, named pipes, attach tokens, relay credentials,
backend auth state, provider credentials, backend-private live databases,
GUI/login attestations, process facts, and terminal state remain machine-local
and non-replicable. Only explicitly sanitized backend identity and conformance
evidence may persist in AX records.

Credential readiness is functional evidence inside the exact TerminalInstance:
an AX-owned sentinel plus a provider-auth smoke bound to backend ID, versions,
generation, provider build, platform, and OS version. Aqua or GUI presence alone
is not proof. This release adds no permanent public TCP listener and approves no
third-party relay/public-service transport.

## Implementation milestones and SDK status

- M0 defines the internal semantic boundary, registry, identity,
  compatibility, and conformance harness.
- M1 delivers the production built-in tmux path and single-host durability.
- M2 adds the multi-host preview and its minimum fencing, idempotency, journal,
  and recovery safety kernel.
- M3 is the first daily-driver tmux gate on required macOS/Linux lanes,
  including Aqua/provider-auth evidence and full recovery.

A stable public TerminalBackend SDK remains deferred until tmux and at least one
materially different backend validate the boundary. The local adapter protocol
and internal interfaces in this specification are not a stable public SDK.

## Retained provider and platform caveats

- Qwen is only supported via task-board prompt-mode bundles (no direct native `ax-provider-qwen` claim).
- Muse relies on a narrow, version- and platform-gated native store/resume probe and advertises `portable_store=false` (`cron.db` is durable but not safely portable).
- Antigravity resumes via conversation UUID through its authenticated backend/account realm, rather than relying on copying local cache as a portable store or checkpoint.
- For Claude, the direct adapter's `appserver` capability is unsupported, but `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are available through task-board.
- Native Windows and WSL2 are distinctly partitioned. Native Windows does not claim `tmux` support, using native process supervision and ConPTY instead.
- Payload encryption at rest is not provided; `mesh.payload_encryption` remains `none`.

## Validation, diagrams, and traceability

The release adds `fixtures/terminal_backend_conformance.json`, the focused
TerminalBackend validator and expected-red mutations, a C4 component view, and a
focused PlantUML authority/lifecycle view. These are specification-conformance
artifacts; they do not execute or attest a product implementation.

Appendix A.11 of `SPEC.md` maps the owner brief and release requirements to the
normative sections and fixture gates. Appendix D catalogs the independently
versioned contracts and negative mutations. `STANDALONE_TO_AX_TRACEABILITY.md`
retains the historical cloning/Directory mappings and adds a non-normative
v0.5.0 TerminalBackend release-delta index. `SPEC.md` remains the only normative
source.
