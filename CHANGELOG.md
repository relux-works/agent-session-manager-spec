# Changelog

All notable changes to the Agent Session Manager specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
