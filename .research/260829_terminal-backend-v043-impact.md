# TerminalBackend v0.4.3 Baseline Evidence

Accepted source: task-board outcome `TASK-260829-2szln8`

Date: 2026-08-29

This candidate-local research record materializes the accepted baseline facts
without importing the sibling research Change Request history.

- Published tag `v0.4.3` peels to commit
  `e876e5067073b14be567fe34ebd7683bf8bda666`, which is this Story worktree's
  starting commit.
- The accepted baseline ran `./run_validation.sh` successfully with 267/267
  semantic checks, `./scripts/test_expected_red.sh` successfully with 246/246
  mutations rejected, and `git diff --check` with exit 0.
- Configuration 1.0.0/2.0.0, Provider Protocol 2.0.0 TerminalDescriptor,
  Session Event 1.0.0 terminal payloads, CLI Result 1.0.0 start/resume payloads,
  and the v0.4.3 fixture/validator definitions are closed immutable history.
- The historical terminal values are exactly `tmux|conpty`; generalization must
  use new independently versioned contracts and deterministic translation.
- AX owns Session/lease/provider/workspace/checkpoint/task-board/mesh authority.
  TerminalBackend is host-local presentation and delegated process hosting.
- tmux remains the mandatory Unix implementation with a private dedicated `-S`
  server and macOS Aqua plus functional provider-auth evidence. ConPTY remains
  the native-Windows implementation.
- Sockets, pipes, tokens, credentials/auth state, PIDs/handles, terminal output,
  backend live databases, and live process facts are machine-local exclusions.
- Public stable SDK support remains deferred.

The full accepted impact map remains attached to the active implementation task
as `accepted-v043-terminal-backend-impact.md`. `SPEC.md` is the sole normative
authority; this file is provenance-bearing research evidence only.
