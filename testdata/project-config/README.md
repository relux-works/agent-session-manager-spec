# Explicit operator launch policy example

This sanitized, copyable configuration admits only `codex/gpt-6-astra` with
`medium` or `high` reasoning effort. It is a reproducible example, not an
auto-loaded configuration or a second policy authority. The live root
`task-board.config.json` remains local, operator-owned and ignored.

The approved migration replaces the legacy model ceiling with explicit
`spawn-policy-v4` equal-pair entries and supplies workload recommendations,
including the required `unified` class. Recommendations do not widen admission.
The initial bootstrap preflight refused the missing `unified` class; it was
corrected before any spawn. Existing parallelism, isolation and validation
settings are preserved.

To adopt, explicitly review and copy or merge `task-board.example.json` into
the control root’s `task-board.config.json`, preserving any unrelated local
settings. The example filename is intentionally not auto-loaded. Run fresh read-only
preflights from the control root before selecting either exact pair:

```sh
task-board q 'project_config(view=spawn-preflight, role=developer, agent=codex, task_class=code)'
task-board q 'project_config(view=spawn-preflight, role=reviewer, agent=codex, task_class=code)'
```

Check `admitted_pairs` for exactly Astra medium and high, and the allowed
provider for exactly Codex. No other provider, model or effort is authorized.
