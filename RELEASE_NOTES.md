# Agent Session Manager (`ax`) Specification v0.1.0

This is the initial specification release of the Agent Session Manager (`ax`) architecture and normative protocol contract.

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
- No payload encryption at rest is provided in v0.1.0 (`mesh.payload_encryption` MUST be `none`).
- Transport uses standard Tailscale SSH or OpenSSH.
- Secrets, active sockets, tmux servers, and live database files are explicitly excluded from replication.

## Known Limitations
- Network split-brain scenarios must be explicitly managed by force takeover, retaining both histories for manual resolution.
- Workspace conflict resolution is fail-closed, prioritizing explicit user choices (copy, worktree, or verified replace) over automated merges.
- v0.1.0 does not specify Byzantine consensus or isolate hostile peers.
