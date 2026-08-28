# Changelog

All notable changes to the Agent Session Manager specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.4.3] - 2026-08-28

### Changed

- Reframed implementation delivery as M0 contract foundation, M1 single-host
  durability, M2 multi-host MVP preview with the minimum fencing/journal/
  idempotency/status-first/crash kernel, and M3 as the first daily-driver gate.
- Kept plugin wire contracts, internal interfaces, and their conformance harness
  in M0 while deferring any public stable SDK until Codex and Claude validate
  the boundary.
- Limited `ax NAME` auto-execution to one uniquely safe non-mutating route;
  takeover, fork, move, and ambiguity remain pure plans requiring confirmation.
- Made `ax sync --all` immutable-convergence-only, completed M1 Git closure over
  tracked/index/staged/unstaged/untracked/ignored-policy/symlink/submodule
  state, and required destination broker/auth readiness before ownership commit;
  graceful takeover requires verified source stop before that commit, while
  force takeover uses winning-lease fencing when source stop cannot be proved
  and still creates no runtime before ownership commits.

### Security

- Required a dedicated AX `tmux -S` server below a private 0700 runtime parent,
  with symlink/path-substitution refusal and machine-local socket/auth state.
- Split the background control plane from the minimal macOS Aqua terminal
  broker. Background callers may contact an existing broker but may not create
  a credential-dependent tmux server.
- Made `launchctl managername` diagnostic only; conformance requires a
  functional AX sentinel plus separate provider-auth smoke bound to tmux server
  generation, provider build, and macOS version. Logout/reboot without a
  verified GUI realm parks recovery until GUI login.

### Compatibility

- This specification-package patch changes no Section 1.5 contract version or
  wire shape. Structured Error remains `1.2.0`; realm/auth refusals reuse
  `capability_unavailable` or `target_auth_missing` with typed details, and
  route ambiguity continues to use `interactive_choice_required`.
- Added one strict v0.4.3 positive fixture and eight independent expected-red
  narrowing mutations through production validator entry points. Existing
  `v0.4.2` and earlier tags remain immutable.

## [v0.4.2] - 2026-08-28

### Fixed

- Restored immutable Directory Node Protocol/Request `1.0.0` semantics with the
  published `darwin|linux|windows` probe vocabulary and introduced Protocol and
  Request `2.0.0` for `macos|linux|wsl2|windows`, including WSL2.
- Added exact protocol/request/response/manifest major bindings, highest-mutual
  dual-stack negotiation, and fail-closed rejection of cross-major relabeling
  or coercion.
- Replaced value-inferred common-type checks with schema/path-directed digest,
  UUIDv4, UUIDv7, UUIDv7-or-digest, nullable, timestamp, platform, and
  sorted-unique validation. Timestamp checks now reject impossible calendar
  instants after matching the RFC 3339 UTC grammar.
- Added adversarial expected-red cases whose mutated directory self-IDs are
  recomputed, proving malformed typed values cannot hide behind a self-ID
  mismatch, plus focused protocol-major binding mutations.

### Compatibility

- Existing `v0.4.0` and `v0.4.1` tags remain immutable. Directory Node
  Manifest and Response remain `1.0.0`; only Protocol and Request advance to
  `2.0.0`. Implementations should serve v1 and v2 concurrently for at least one
  stable specification release.
- This errata is the current first safe Session Directory implementation baseline. It
  changes no AX ownership, lease, workspace, cloning, mesh namespace, record,
  or terminal authority.

## [v0.4.1] - 2026-08-27

### Fixed

- Prohibited direct unmanaged cross-environment move: an unmanaged source must
  be cloned while retained or adopted source-locally before a separately
  planned managed move can use Session Event 3 and fenced lease release.
- Repaired all positive Directory self-ID vectors to use full SHA-256
  identifiers, millisecond-precision UTC timestamps, and the AX platform enum;
  recomputed every affected JCS identity.
- Made Directory Node responses an executable `body XOR error` tagged union,
  required enrichment generator discriminators to agree, required positional
  query/result correlation, and bound lineage rows to one deterministic
  non-authoritative representative member.
- Clarified that the Section 5 Session Record/Event definitions are the closed
  v1 base variants and that v2/v3 are independently selected extensions.
- Added focused expected-red coverage for invalid common values, discriminator
  conflicts, response-union violations, query correlation, unmanaged move,
  lineage selection, and CLI registry drift.
- Improved the Directory component and C4 Container diagrams for readable
  labels and bounded width.

### Compatibility

- This patch changes no Section 1.5 contract version or authority. At its
  publication it resolved contradictory or unimplementable v0.4.0 text under
  already-settled AX invariants and superseded v0.4.0 as the first Directory
  implementation baseline; v0.4.2 now supersedes that historical claim, so
  v0.4.1 is not the current implementation baseline.

## [v0.4.0] - 2026-08-27

### Added

- Integrated Session Directory and continuation orchestration as first-class AX subsystems with source-local discovery, immutable observations/batches/lineage/annotations/job receipts, a rebuildable catalog, typed human/agent queries, and a shared four-region TUI model.
- Added the companion Directory Node protocol `1.0.0`, Directory records and Query `1.0.0`, exact-head bounded enrichment profiles/jobs, content-addressed continuation plans, immutable operation receipts, and production-path conformance fixtures.
- Added three focused Directory PlantUML views for component authority, inventory/enrichment, and continuation, and integrated Directory/Node/worker/cloning relationships into the C4 model.

### Changed

- Advanced the specification package from the accepted v0.3 cloning baseline to `v0.4.0` without changing Provider Protocol `2.0.0`, Session Adapter `1.0.0`, or the existing cloning transaction authority.
- Added directory-capable Mesh RPC `3.0.0`, Configuration `2.0.0`, CLI Result `3.0.0`, Session Record/Event `3.0.0`, and Structured Error `1.2.0`; RPC 2 remains dual-stack for core sync and reports Directory support as unavailable.
- Expanded publication validation and focused expected-red coverage to the closed Directory schema/namespace/query/route/security invariants, the twelve-diagram artifact ledger, and the frozen v0.4.0 public-document baseline.

### Security

- Kept raw transcripts, preview bodies, credentials/auth state, absolute native-store paths, model-provider payloads, terminal output, live process facts, and derived SQLite outside mesh Directory records.
- Required source-local bounded reads, explicit disclosure policy, sandboxed enrichment workers, server-side field authorization, stale-plan refusal, and target-first cross-environment move semantics.

## [v0.3.0] - 2026-08-27

### Added

- Integrated cross-environment session cloning as a first-class `ax session clone` subsystem with closed plan, run, verification, and open outcomes.
- Added the companion Session Adapter protocol `1.0.0`, canonical capture/projection contracts, immutable clone bundle generations, per-item fidelity accounting, migration checkpoints, target-native read-back evidence, lineage receipts, and signed exact-environment-tuple admission/revocation.
- Added Session Record and Session Event `2.0.0` variants for cross-environment clone targets, Materialization Plan `2.0.0`, clone-only Materialization Journal `3.0.0`, CLI Result `2.0.0`, and Structured Error `1.1.0` bindings.
- Added complete non-normative standalone-to-AX traceability in `STANDALONE_TO_AX_TRACEABILITY.md`.

### Changed

- Advanced the specification release from `v0.2.1` to `v0.3.0`; existing `v0.1.0`, `v0.2.0`, and `v0.2.1` tags remain immutable.
- Kept Provider Protocol and Mesh RPC at `2.0.0`; semantic conversion is independently versioned and served by the same trusted provider executable instead of introducing Provider Protocol `3.0.0` or an N-by-N converter matrix.
- Restricted support claims to signed, unexpired, non-revoked exact environment tuples with binding and fixture evidence. Provider-name claims and self-minted evidence do not establish support.
- Resolved all four deferred merge decisions: the sole public namespace is `ax session clone`; the Session Adapter remains a companion protocol; clone targets use tagged Session Record `2.0.0` derivation provenance; and the AX release authority publishes and revokes the signed tuple registry while local policy may only restrict it further.

## [v0.2.1] - 2026-08-23
### Added
- Defined `safe_retry`, `explicit_rollback`, and `recoverable_parked_state` as the mutually exclusive and collectively exhaustive outcomes for every inter-phase crash/restart boundary.
- Added a closed crash-injection boundary registry covering launch, sync, materialization, graceful and force takeover, fork, stop, owner resume, and reboot restore.
- Added runtime and specification-publication acceptance cases plus task traceability for the crash/restart outcome gate.

### Changed
- Recovery now fails closed unless it proves one allowed outcome with durable authority, external-effect, and exact native identity evidence.
- Recovery explicitly rejects duplicate live/authoritative owners, unfenced continuation represented as safe, and silent fresh native provider or task-board manager sessions.
- Advanced specification and publication metadata to `v0.2.1` without changing any wire-contract version or moving the existing `v0.1.0` and `v0.2.0` tags.

## [v0.2.0] - 2026-08-23
### Changed
- Made Mesh `materialize.prepare` recoverable after a lost response by requiring caller-stable operation and materialization IDs plus a durable request receipt.
- Separated evolving provider `materialize-status` reads from byte-identical mutation replay semantics.
- Raised the Provider protocol, Mesh RPC, and Materialization recovery state contracts to `2.0.0` because those corrected request and journal shapes are intentionally incompatible with their published `1.0.0` forms.
- Aligned materialization recovery and provider path-result cardinalities with the maximum valid 65,536-entry closure.

### Fixed
- Parse and identity-check every normative strict-JSON `jsonc` fixture.
- Canonicalize JCS object property names using RFC 8785 UTF-16 code-unit ordering and reject lone surrogates.

## [v0.1.0] - 2026-08-22
### Added
- Initial normative contract specification for Agent Session Manager (`ax`).
- Terminal backend and persistence architecture definitions.
- Mesh RPC, capability discovery, and cross-host sync protocol schemas.
- Task-board opaque bundle and materialization contract.
- Complete C4 architecture and state machine diagrams.
- Provider plugin protocol definitions for six direct adapters (codex, claude, gemini, muse, antigravity, pi) and task-board-only prompt mode integration for qwen. Direct `ax-provider-qwen` claims are explicitly prohibited in v0.1.0.
- Exact normative definitions for graceful takeover, force takeover, and fork semantics.
- Security and threat boundaries documenting trusted mesh assumptions.
