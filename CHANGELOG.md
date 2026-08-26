# Changelog

All notable changes to the Agent Session Manager specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
