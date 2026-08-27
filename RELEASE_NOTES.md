# Agent Session Manager (`ax`) Specification v0.3.0

This minor specification release adds cross-environment session cloning as a first-class AX subsystem. It supersedes `v0.2.1` without moving or rewriting the `v0.1.0`, `v0.2.0`, or `v0.2.1` tags.

**Status caveat:** this release publishes specification artifacts only. It contains no executable `ax` product binary, and publication does not imply that any provider/platform product-conformance lane has passed.

## Cross-environment cloning

The sole public namespace is `ax session clone`; there is no `ax clone` alias in `v0.3.0`. Its closed leaf commands are `adapters`, `doctor`, `list`, `inspect`, `plan`, `run`, `verify`, and `open`. `plan` is the only no-target-write operation, while `run --dry-run` is rejected before target allocation.

A clone derives a new AX logical session and native target identity without moving, stopping, or mutating the source. The source lease, task-board authority, approvals, credentials, pending operations, and foreign instruction authority never transfer. Raw evidence is retained, every canonical item and projection is accounted for, and non-exact fidelity is disclosed per item with stable reasons.

The transaction requires a stable source capture, authority-scoped target staging, independent staged read-back, publication with rollback retained, live discovery/read-back, a resume plan, a second source-generation check, Provider commit, an ordinary target AX Checkpoint, and lineage publication. Crash/restart behavior remains limited to `safe_retry`, `explicit_rollback`, or `recoverable_parked_state`.

## Plugin and contract boundary

Semantic conversion uses companion `urn:ax:protocol:session-adapter` `1.0.0`, served by the same trusted `ax-provider-<id>` executable and bound to its observed executable digest. The Session Adapter performs native-to-canonical capture and canonical-to-native projection; Provider Protocol `2.0.0` retains native object-sink, transaction, commit, rollback, discovery, capture, and resume-plan responsibilities. This release does not introduce Provider Protocol `3.0.0`, change Mesh RPC `2.0.0`, or create pairwise environment converters.

New or clone-specific contract versions include:

| Contract | Version |
| --- | --- |
| Session Adapter protocol, manifest, and probe | `1.0.0` |
| Canonical Session/Event, Projection Plan, Fidelity Report, Migration Checkpoint, clone manifests/reports/receipt, supported-tuple registry | `1.0.0` |
| Session Record and Session Event for cross-environment clone targets | `2.0.0` |
| Materialization Plan | `2.0.0` |
| Clone-only Materialization Journal | `3.0.0` |
| CLI Result for `session.clone.*` | `2.0.0` |
| Structured Error for Session Adapter and clone commands | `1.1.0` |

Session Record `2.0.0` is emitted in `v0.3.0` only for cross-environment clone targets. Provider Protocol `2.0.0` launch and fork continue to use Session Record `1.0.0` and the existing fork provenance until an explicit containing-protocol revision adopts the tagged major-2 record.

## Supported-evidence policy

Support is granted only to an exact source-reader or target-writer environment tuple admitted by the signed `compatibility/supported-environment-tuples-v1.json` registry. The tuple, provider and adapter manifests/probes, host-observed executable binding, contract versions, fixture corpus, native smoke evidence, validity interval, and non-revoked status must agree.

Missing, malformed, stale, partially readable, mismatched, self-minted, wildcard, or revoked evidence fails closed. Only the AX release authority may globally accept or revoke tuples. A local operator may deny additional tuples but cannot approve an absent tuple or override a revocation. Provider-name support, a healthy probe by itself, and archive-only source evidence do not establish target-write support.

## Compatibility and retained boundaries

- Provider Protocol and Mesh RPC remain `2.0.0`; the task-board bridge remains `1.0.0`.
- The `v0.2.1` crash/restart outcome gate remains normative and now covers the clone boundaries `CR-CLONE-01..16`.
- Qwen is only supported via task-board prompt-mode bundles (no direct native `ax-provider-qwen` claim).
- Muse relies on a narrow, version- and platform-gated native store/resume probe and advertises `portable_store=false` (`cron.db` is durable but not safely portable).
- Antigravity resumes via conversation UUID through its authenticated backend/account realm, rather than relying on copying local cache as a portable store or checkpoint.
- For Claude, the direct adapter's `appserver` capability is unsupported, but `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are available through task-board.
- Native Windows and WSL2 are distinctly partitioned. Native Windows does not claim `tmux` support, using native process supervision and ConPTY instead.
- Payload encryption at rest is not provided; `mesh.payload_encryption` remains `none`.
- Credentials, secrets, live PIDs/sockets/locks, and live SQLite files remain excluded from replication and clone bundles.

## Traceability

`STANDALONE_TO_AX_TRACEABILITY.md` maps every standalone section to the resulting AX section, identifies reused and new contracts, lists superseded standalone rules with rationale, and records closure of all four deferred AX merge decisions. `SPEC.md` remains the only normative source.
