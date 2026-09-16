# Agent Session Manager (`ax`) Specification v0.7.0 — prepared, unpublished

This prepared minor revision adds caller-supplied launch plans over immutable
v0.6.0 history with no release tag. `ax start --launch-plan FILE|-` accepts a
closed Launch Plan request 1.0.0 document in `argv` or `argv_suffix` form,
validated before any Session Record exists; violations refuse with the new
`launch_plan_invalid` code under Structured Error 1.5.0. Session Record 3.1.0
adds the optional Launch Stdin member, Provider Protocol 2.1.0 and 3.1.0 carry
`SpawnPlan.stdin` with `resume.launch_plan` replay behind the
`caller_launch_plan` and `stdin_resume_replay` capabilities, and Provider
manifest/probe 1.1.0 carry the nine-name capability registry while 1.0.0
readers keep accepting seven names. CLI Result stays at 5.0.0. Historical
contracts and release tags stay immutable.

These are specification artifacts only: this repository has no `ax` product
binary, no executed provider deployment or platform conformance result, and no
AX implementation, platform acceptance, or release tag. Synthetic fixtures and
source mutations validate the contract package, not live provider behavior,
key custody, or product runtime behavior. The parent coordinates publication
after all constituent Stories pass review and land. This work does not create
a v0.7.0 release tag.

Resume and fork refuse on `environment_drift` by default when the recorded
`system-modules` provenance is true and warn otherwise; the Curator umbrella
names this specification's implementation `curator session` with no new `ax`
surface. See SPEC Sections 5.1, 7.3–7.5, 13.1, 13.10, 14.1 and 15.3 for the
launch-plan contract, Section 19.4 `AC-LAUNCH-003` for acceptance, and Appendix
A.12 for the curator-spec Decision 0013 traceability.

Publication evidence: `./run_validation.sh`, `./scripts/test_expected_red.sh`,
`python3 scripts/test_selector_publication.py`, the host-channel publication
gate, and the launch-plan fixture gate; measured source-only coverage and
mutation bounds are reported by those commands. SPEC remains authoritative.

## Retained v0.6.0 release notes

This minor revision combines two approved source deltas. The selector delta
adds Session selector 1.0.0, CLI Result 5.0.0 and Structured Error 1.4.0.
Literal first-at qualification accepts exact
configured aliases; explicit id:UUID bypasses name precedence. Plans bind
source, record, configuration and lease facts and revalidate before effects.
Public summaries require real initial leases and observations; record-only
bootstrap returns a typed refusal and recovers only from original durable
bootstrap inputs. No invented owner or lease is produced. The authentication
delta adds the standard mutually authenticated host channel over SSH, exact
public credential enrollment and UUID binding, credential rotation/revocation,
and explicit configuration/launch migration. Config 4.0.0 and RPC 5.0.0 select
Host Channel 1.0.0 with Host Trust Store 1.0.0. Historical contracts and
release tags stay immutable. There is no resumption, 0-RTT, plaintext fallback,
silent downgrade or inferred trust from SSH identity.

These are specification artifacts only: this repository has no `ax` product
binary, no executed TLS deployment or platform conformance result, and no AX
implementation, platform acceptance, or release tag. Synthetic fixtures and
source mutations validate the contract package, not key custody, live
revocation, or product runtime behavior. The parent coordinates publication
after all constituent Stories pass review and land. The v0.6.0 release tag was
published separately by the parent after landing.

The host profile authenticates enrolled-key possession. Copied keys and
compromised local accounts are outside physical-host assurance; revocation must
reach each peer explicitly. See SPEC Sections 6.6, 11.10, 16 and 20. See SPEC
Section 14.7 for the selector contract and Sections 6.6/11.10 for the host
channel contract.

Publication evidence: `./run_validation.sh`, `./scripts/test_expected_red.sh`,
`python3 scripts/test_selector_publication.py`, and the host-channel
publication gate; measured source-only coverage and mutation bounds are
reported by those commands. SPEC remains authoritative.

## Retained v0.5.0 release notes

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

Selector review refinements freeze the CLI5 remote attach expectation operand,
real action/boundary revalidation matrix, and concrete BootstrapIntent/Lease1
conformance. Historical CLI1–4 routes remain version-bound. The v0.6.0 revision
is source publication only; no product implementation is asserted.
