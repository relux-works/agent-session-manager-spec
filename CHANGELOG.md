# Changelog

All notable changes to the Agent Session Manager specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
