# Agent Session Manager (`ax`) Specification v0.2.1

This patch release supersedes `v0.2.0` without moving or rewriting the
`v0.1.0` or `v0.2.0` tags. It adds a normative crash/restart outcome gate
without changing any wire-contract version.

## Crash/restart outcome gate

- Every inter-phase crash/restart boundary in launch, sync, materialization,
  graceful and force takeover, fork, stop, owner resume, and reboot restore
  must classify into exactly one of `safe_retry`, `explicit_rollback`, or
  `recoverable_parked_state`.
- Safe retry preserves caller-stable operation IDs and the exact persisted
  native provider identity or task-board manager binding.
- Explicit rollback is durable, visible, and proves predecessor restoration or
  closure; parked recovery is fail-closed and preserves reconciliation facts.
- Recovery may not produce duplicate live/authoritative owners, treat an
  unfenced continuation as safe, or silently allocate a fresh native session.
- `AC-CRASH-001` and `SPEC-PUB-CRASH-001` gate runtime conformance and
  specification publication respectively.

## Critical Corrections

- Mesh `materialize.prepare` uses caller-stable IDs and a durable request receipt, so a lost response cannot create a second materialization.
- Provider `materialize-status` is an evolving read rather than a byte-identical mutation receipt.
- Provider protocol, Mesh RPC, and Materialization recovery state are versioned `2.0.0`; their published `1.0.0` shapes are not wire-compatible with these corrections.
- All normative strict-JSON `jsonc` fixtures are parsed and identity-checked.
- JCS property ordering follows RFC 8785 UTF-16 code units, including non-BMP keys.
- Recovery state represents the full 65,536-entry materialization closure.

**Status Caveat:** This release publishes **specification artifacts only**. It does not contain an executable `ax` product binary, and no runtime product validation is implied by this release.

## Normative Architecture
The `ax` product manages durable coding-agent sessions across an explicitly trusted, allowlisted mesh. Highlights include:
- A single active owner host with zero or more dormant replicas.
- Versioned JSON-over-stdio provider plugin protocol supporting Codex, Claude, Gemini, Muse, Antigravity, and Pi.
- Content-addressed anti-entropy replication mechanism over SSH without a permanent public TCP listener.
- Task-board integration preserving `tb-sessiond` ownership while transporting opaque bundles.
- C4 container context and rigorous ownership state machine documentation.

## Capability Limits and Unimplemented Features
Capabilities are gated and reported per-provider and per-platform:
- Qwen is only supported via task-board prompt-mode bundles (no direct native `ax-provider-qwen` claim).
- Muse relies on a narrow, version- and platform-gated native store/resume probe and advertises `portable_store=false` (`cron.db` is durable but not safely portable).
- Antigravity resumes via conversation UUID through its authenticated backend/account realm, rather than relying on copying local cache as a portable store or checkpoint.
- For Claude, the direct adapter's `appserver` capability is unsupported, but `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are available through task-board.
- Native Windows and WSL2 are distinctly partitioned. Native Windows does not claim `tmux` support, using native process supervision and ConPTY instead.

## Security Boundary
The system assumes an explicitly allowlisted trusted mesh.
- No payload encryption at rest is provided in v0.2.1 (`mesh.payload_encryption` MUST be `none`).
- Transport uses standard Tailscale SSH or OpenSSH.
- Secrets, active sockets, tmux servers, and live database files are explicitly excluded from replication.

## Known Limitations
- Network split-brain scenarios must be explicitly managed by force takeover, retaining both histories for manual resolution.
- Workspace conflict resolution is fail-closed, prioritizing explicit user choices (copy, worktree, or verified replace) over automated merges.
- v0.2.1 does not specify Byzantine consensus or isolate hostile peers.
