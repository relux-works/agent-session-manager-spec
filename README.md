# Agent Session Manager (`ax`) v0.2.0 — Specification Repository

| Field | Value |
| --- | --- |
| Public command | `ax` |
| Specification release | `v0.2.0` |
| Repository | `relux-works/agent-session-manager-spec` |
| Default branch | `main` |
| License | MIT |
| Normative contract | [`SPEC.md`](SPEC.md) |
| Status | Specification only — no `ax` product binary in this repository |

> This repository publishes the normative, implementation-ready contract for Agent Session Manager v0.2.0. It specifies behavior; it does not implement `ax`. Publishing the specification does not claim that any future product acceptance matrix has passed. See [SPEC.md §1](SPEC.md#1-conformance-language-and-scope), [§19](SPEC.md#19-ax-implementation-conformance-and-product-release), and [§20](SPEC.md#20-specification-publication-and-governance).

## Read first

- [SPEC.md](SPEC.md) is the only normative source. Its uppercase `MUST`/`SHOULD`/`MAY` requirements control implementations. This README summarizes and links to it — it does not create a second contract.
- [`.research/260819_muse-antigravity-native-store-contracts.md`](.research/260819_muse-antigravity-native-store-contracts.md) is the accepted, version-sensitive persistence evidence for the Muse and Antigravity adapters (see [SPEC.md §1.4](SPEC.md#14-source-authority-and-evidence) and [Appendix C](SPEC.md#appendix-c-evidence-and-primary-references)).
- [`.planning/260819_022043_story-260819-iscto1.md`](.planning/260819_022043_story-260819-iscto1.md) is planning evidence; it is not a competing protocol definition.

Appendix A of [SPEC.md](SPEC.md#appendix-a-normative-traceability) maps every settled decision and acceptance criterion to its normative sections. Appendix D defines the exhaustive fixture catalog.

## What `ax` is

`ax` manages durable coding-agent sessions across an explicitly trusted, allowlisted mesh of computers. One logical session has exactly one active owner host and zero or more replicas; a host lease epoch fences stale owners, and a replica never resumes as owner without an explicit handoff, force-takeover, or fork. See [SPEC.md §1.2](SPEC.md#12-product-boundary), [§2](SPEC.md#2-product-and-operator-model), and [§5.3](SPEC.md#53-lease-record-and-ownership).

The operator can:

1. launch a direct provider session or a task-board-managed session;
2. keep the terminal durable across a local disconnect and, where the backend supports it, a reboot;
3. list ownership and replica state across the mesh;
4. synchronize immutable session metadata, provider state, task-board state, and workspace state;
5. attach to the current owner without changing ownership;
6. transfer ownership gracefully or, as an explicit recovery action, forcibly;
7. fork from a checkpoint into a new logical session and workspace identity;
8. stop a session without deleting its durable state; and
9. resume a stopped session on its owner host.

`ax` is a Go CLI, optional per-user background service, provider plugin host, terminal supervisor, SSH RPC client/server, and Go-native replication engine. It is not a cloud service, public relay, multi-tenant scheduler, replacement for a provider native store or for task-board/`tb-sessiond`, general-purpose backup, secrets manager, source-control system, distributed shell that auto-authorizes discovered machines, guarantee that every provider supports every operation, or encrypted-at-rest snapshot product. See [SPEC.md §1.2](SPEC.md#12-product-boundary) and [§16](SPEC.md#16-security-and-threat-boundary).

There is no permanent public TCP listener. The remote entry point is `ax rpc serve --stdio`, normally started by Tailscale SSH or ordinary OpenSSH. See [SPEC.md §1.2](SPEC.md#12-product-boundary) and [§11.1](SPEC.md#111-transport-and-peer-authentication).

## Installation and status caveat

This is a **specification-only** repository at `v0.2.0`. There is no `ax` binary to install, no provider runtime requirement to validate or publish the spec, and no Section 19 product-conformance result implied by publication. See [SPEC.md §1.5](SPEC.md#15-normative-contract-registry), [§19.5](SPEC.md#195-ax-implementation-release-acceptance-rule), and [§20.2](SPEC.md#202-publication-gate).

To work with the spec:

```shell
git clone https://github.com/relux-works/agent-session-manager-spec.git
cd agent-session-manager-spec
git checkout main
```

A future `ax` product release will add its own install instructions and will be gated separately by the platform/provider acceptance matrix in [SPEC.md §19](SPEC.md#19-ax-implementation-conformance-and-product-release). Until then, the validation in this repo checks only spec structure, contract fixtures, links, diagrams, and publication metadata (see [Tools, validation, and artifacts](#tools-validation-and-artifacts)).

## Operator journey

The surface below is normative in [SPEC.md §14](SPEC.md#14-cli-and-operator-experience). Flags shown without `=` use a space separator. `NAME` is the mesh-unique human alias (`[A-Za-z0-9][A-Za-z0-9._-]{0,63}`); every command also accepts a UUID when `NAME` is one. See [§2.3](SPEC.md#23-session-name-resolution) and [§14.1](SPEC.md#141-command-surface).

### 1 — Launch

Direct provider session (native provider store):

```shell
ax start payments-api --provider codex --profile yolo --workspace .
ax start payments-api --provider claude --profile standard --workspace /srv/relux
```

Direct sessions are materialized into the native locations where each provider normally discovers and resumes them (for example `~/.codex/sessions`, `~/.claude/projects`, `~/.gemini/tmp/<project-hash>/chats`, `~/.pi/agent/sessions`, Muse's native store/index, Antigravity's cache/backend identity). Source absolute paths are never identities; providers compute platform-specific keys from logical workspace mappings. See [SPEC.md §7-§8](SPEC.md#8-provider-and-platform-contracts) and [§13.1](SPEC.md#131-direct-session-launch).

Task-board session — prompt-tracked mode (e.g. Gemini/Muse/Qwen through task-board):

```shell
ax start qwen-investigation --task-board --provider qwen \
  --task TASK-260819-example \
  --board-id agent-session-manager-spec \
  --launch-mode tracked-prompt --binding prompt \
  --profile standard --workspace .
```

Task-board session — goal-bound primary mode (Codex and Claude where `task_board_primary` is available):

```shell
ax start codex-primary --task-board --provider codex \
  --task TASK-260819-example \
  --board-id agent-session-manager-spec \
  --launch-mode primary-owner \
  --goal PRIMARY-GOAL-260819-example --goal-revision 3 \
  --profile yolo --workspace .
```

Rules: `--board-id` is required and uses the logical-ID grammar; omitting `--board-url` selects a local board, supplying it selects a remote board and it must be an absolute `https://` URL without userinfo/query/fragment; `primary-owner` requires both `--goal` and positive `--goal-revision` and forbids `--binding`; `tracked-prompt` requires explicit `--binding prompt|none` and requires `--goal`/`--goal-revision` either together or both absent. No provider-ID heuristic may infer these values. See [SPEC.md §14.1](SPEC.md#141-command-surface), [§9](SPEC.md#9-task-board-integration), and [§13.2](SPEC.md#132-task-board-session-launch).

Every durable pane runs the stable wrapper `ax pane <logical-session-id>`, never a raw provider command. On restore the wrapper consults ownership and either resumes locally, offers remote attach/takeover, or parks. See [SPEC.md §4](SPEC.md#4-terminal-persistence).

### 2 — List and status

```shell
ax list
ax list --all-peers
ax status payments-api
ax status payments-api --json
```

`list`/`status` expose session ID and name, direct/task-board kind and provider, winning owner host/name, lease epoch and abbreviated lease ID, local role `owner`/`replica`, derived state, newest validated checkpoint and age, workspace materialization status/conflict, provider/platform capability statuses, last successful sync per peer, and warnings. See [SPEC.md §14.4](SPEC.md#144-list-and-status-fields).

### 3 — Sync and diff

```shell
ax sync payments-api
ax sync --all
ax sync --peer workstation --resume 0198f4c8-19e0-78ff-8879-2234567890ab
ax diff payments-api
ax diff payments-api --peer workstation
```

Sync is a set-union of immutable identity-addressed records/events and content-addressed blobs with content hashing/chunking, resumable transfer, staging, validation, and atomic materialization. The live SQLite file is a derived index and is never the replication unit. Deletions are managed tombstones. See [SPEC.md §10](SPEC.md#10-immutable-records-blobs-manifests-and-tombstones), [§11](SPEC.md#11-mesh-rpc-and-replication), and [§13.3](SPEC.md#133-sync).

### 4 — Attach

```shell
ax attach payments-api
ax attach payments-api --local
ax payments-api --action attach --non-interactive   # umbrella form, explicit
```

Remote attach executes `ssh -t HOST ax attach NAME --local` (or equivalent PowerShell-safe invocation) and never changes ownership. See [SPEC.md §13.5](SPEC.md#135-remote-attach) and [§14.1](SPEC.md#141-command-surface).

### 5 — Takeover (graceful vs force)

Graceful takeover waits for a provider safe-turn boundary, quiesces input, performs final workspace/provider/board sync, gracefully stops the old owner, verifies destination materialization, advances the lease epoch, and resumes with the persisted profile. The old host becomes a replica.

```shell
# interactive: ax resolves the destination and prompts
ax takeover payments-api --to local
ax takeover payments-api --to workstation

# non-interactive: --to is required
ax payments-api --non-interactive --action takeover --to local
```

Force takeover is an explicit recovery action, not a default choice. It advances the epoch, marks the previous owner stale, warns about split-brain risk, and preserves both divergent histories. The old process may still exist but is fenced from syncing/resuming.

```shell
ax takeover payments-api --to local --force \
  --expect-owner 0198f4c8-4a10-7b22-8b3c-1234567890ab \
  --expect-epoch 4 --yes
```

When the migration cohort has more than one session sharing a checkout, supply `--workspace-mode whole-group|separate-worktrees`. The flag is forbidden for singleton cohorts. See [SPEC.md §13.6](SPEC.md#136-graceful-takeover), [§13.7](SPEC.md#137-force-takeover), and [§16.5](SPEC.md#165-force-takeover-risk).

### 6 — Fork

Fork creates a new logical session and workspace identity from a checkpoint, with independent ownership and history.

```shell
ax fork payments-api --as payments-api-experiment --to local
ax fork payments-api --from sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50 \
  --as payments-api-experiment --to workstation
```

`--as` (new name) is required and only valid with `fork`; `--to` is required non-interactively. See [SPEC.md §13.8](SPEC.md#138-fork) and [§10.5](SPEC.md#105-materialization-plan).

### 7 — Stop and resume

```shell
ax stop payments-api
ax stop payments-api --force --yes   # only when graceful stop times out
ax resume payments-api
ax session set-profile payments-api yolo   # persisted profile change; confirmation required to yolo
```

`stop` without `--force` creates a checkpoint, closes the provider, retains lease/state, and remains resumable with the persisted profile. `resume` is only valid on the owner host. Changing `standard`↔`yolo` requires `ax session set-profile` and a new event under the current lease. See [SPEC.md §2.4](SPEC.md#24-execution-profiles), [§13.9](SPEC.md#139-stop), and [§13.10](SPEC.md#1310-resume).

### 8 — Workspace conflict choices

Conflicts fail closed — `ax` never silently overwrites divergent destination state. Use:

```shell
ax diff payments-api
ax materialize payments-api --as-copy /srv/relux/replicas/payments
ax materialize payments-api --as-worktree /srv/relux/worktrees/payments
ax materialize payments-api --replace-managed-replica \
  --expect-checkpoint sha256:2222222222222222222222222222222222222222222222222222222222222222 --yes
```

`--as-copy` and `--as-worktree` require an absent or empty path, do not fork, and do not change ownership; `--as-worktree` requires at least one Git member and creates each Git member as a managed worktree at its group-relative path. `--replace-managed-replica` targets only the configured path, requires `--expect-checkpoint` equal to its managed marker, refuses `unmanaged_nonempty`, and needs the owner's `replica.replace_confirmed` event plus a matching tombstone; non-interactive replacement also requires `--yes`. A copy/worktree/replacement materialization remains dormant even after success. See [SPEC.md §11.6-§11.7](SPEC.md#116-atomic-commit), [§12](SPEC.md#12-workspace-replication), and [§14.1](SPEC.md#141-command-surface).

All commands support `--config`, `--data-dir`, `--state-dir`, `--cache-dir`, `--runtime-dir`, `--json` (exactly one CLI Result `1.0.0` or Structured Error `1.0.0` on stdout), `--no-color`, `--non-interactive`, `--timeout`, and `--verbose`. Destructive or split-brain-risk operations prompt interactively and require `--yes` plus every documented expectation flag non-interactively. Text mode writes data to stdout and diagnostics to stderr; JSON mode writes exactly one document to stdout. See [SPEC.md §14.2](SPEC.md#142-common-flags-and-output) and [§15](SPEC.md#15-errors-and-exit-semantics).

## Two persistence paths

| Path | What `ax` persists and where | What native commands still do |
| --- | --- | --- |
| **Direct** | Provider adapter snapshots the closed provider session and stages it through the Object Sink / provider transactions. On materialization `ax` writes into the native locations where the provider normally discovers/resumes (Codex `~/.codex/sessions`, Claude `~/.claude/projects`, etc.), computing the destination key from the logical workspace mapping. | Native `codex resume UUID`, `claude --resume UUID`, `gemini --resume UUID`, `muse resume UUID`, `agy --conversation <id>`, `pi --session <path\|id>` continue to work without `ax`. See [SPEC.md §7.5](SPEC.md#75-required-operations), [§8.2](SPEC.md#82-native-store-contract-matrix), and [§10.4-§10.6](SPEC.md#104-transfer-manifest). |
| **Task-board** | `tb-sessiond` owns private app-server/thread, PTY, reattach, and goal-binding state. `ax` uses only the official `task-board-bridge` `1.0.0` contract (`launch`/`export`/`import`/`open`/`adopt`/`status`/`stop`/`resume`) and treats the portable bundle as opaque. A bundle carries the durable manager record, provider snapshot, sanitized launch plan (no secrets), owner, `board-goal-v2` reference/revision, native goal-binding state, and logical board/workspace identities. | Local file-backed boards replicate `.task-board` with the workspace and run `task-board validate` after materialization. Remote boards retain the remote URL/board identity and use machine-local credentials. See [SPEC.md §9](SPEC.md#9-task-board-integration) and [§13.2](SPEC.md#132-task-board-session-launch). |

`ax` must not inspect private manager state directly. Until task-board advertises the exact bridge version and required operations, task-board takeover reports `task_board_bridge_unavailable`. See [SPEC.md §9.1-§9.2](SPEC.md#91-ownership-boundary).

## Remote-owner choice prompt

`ax NAME` resolves in order: exact live local name, exact live name learned from allowlisted peers, exact UUID, then not found. Ambiguous names fail with `name_ambiguous`. See [SPEC.md §2.3](SPEC.md#23-session-name-resolution).

When the resolved owner is remote, interactive `ax NAME` offers exactly:

1. remote attach,
2. graceful takeover here,
3. fork here, or
4. cancel.

Force takeover never appears as the default choice; it is exposed only by explicit `ax takeover NAME --to HOST --force --expect-owner ID --expect-epoch N --yes`. Non-interactive commands must select the same actions explicitly (`--action attach|takeover|fork|cancel` with `--to`/`--as` as applicable) and must not prompt or infer one. See [SPEC.md §2.3](SPEC.md#23-session-name-resolution) and [§14.1](SPEC.md#141-command-surface).

## Persisted `yolo` profile

The persisted profile enum is `standard` or `yolo` (`yolo` = the provider-specific unrestricted/no-approval mode; it does not mean `ax` ignores ownership, conflict, allowlist, or integrity checks). `ax` normalizes `yolo` to each provider's actual flag on every initial launch and resume. YOLO mappings include Codex's bypass/no-approval mode, Claude `--dangerously-skip-permissions`, Gemini `--approval-mode=yolo`, Muse `--yolo`, Antigravity `--dangerously-skip-permissions`; Pi 0.73.1 has no YOLO flag and its adapter describes the default full tool set as the provider-specific unrestricted profile instead of inventing a flag. See [SPEC.md §2.4](SPEC.md#24-execution-profiles) and [§7.7](SPEC.md#77-profile-mapping).

The effective profile is the Session Record creation value followed by the newest authoritative `profile.changed` event in lease/sequence order. Every `provider.launched`, `task_board.launched`, `session.resumed`, and `fork.created` event repeats the effective `ax` profile and the digest of its source `profile.changed` event (or null). A checkpoint's event-head closure fixes both values; bundles, resumes, and forks must not fall back to the creation value when the closure contains a later change. Fork creates a new authority boundary with the source-checkpoint effective profile as its creation profile. Pi's equal provider mapping does not erase the `ax` profile history — the two `ax` profiles remain distinct even when both map to `default_unrestricted_tool_set`. See [SPEC.md §2.4](SPEC.md#24-execution-profiles) and [§5.4](SPEC.md#54-checkpoint-record).

Change the profile with `ax session set-profile NAME standard|yolo`, which requires a new event under the current lease and confirmation when changing to `yolo`; resume fails with `profile_mapping_unavailable` if the adapter cannot map the stored profile for the probed provider version.

## Trusted mesh and security exclusions

Peers are explicitly allowlisted in `~/.config/ax/config.toml` (or the platform-equivalent directory — see [SPEC.md §3.2](SPEC.md#32-platform-paths) and [§6](SPEC.md#6-configuration-contract)) with stable host ID, Tailscale/OpenSSH endpoint, platform, and workspace-root mappings. Tailscale discovery may suggest hosts but may not auto-authorize them. Transport is Tailscale SSH or ordinary OpenSSH; the remote side is `ax rpc serve --stdio`; no permanent public TCP listener is required. See [SPEC.md §11.1](SPEC.md#111-transport-and-peer-authentication).

The project owner does not require payload encryption at rest. The spec must not claim default snapshot encryption — and this README does not. SSH protects transport. The security boundary remains a trusted project mesh. `mesh.payload_encryption` must be `none` in `v0.2.0`; any other value fails as unsupported. See [SPEC.md §6.3](SPEC.md#63-field-constraints) and [§16.1](SPEC.md#161-trusted-mesh-model).

Never replicated: credentials/tokens, SSH private keys, environment secrets, live PIDs, sockets, tmux server sockets, transient locks, machine-local authentication state, or the live SQLite database file (rebuildable derived index). Opaque durable history may contain historical path/PID facts as inert bytes required for native resume, but they are not current authority. See [SPEC.md §2.2](SPEC.md#22-global-invariants), [§10-§11](SPEC.md#10-immutable-records-blobs-manifests-and-tombstones), and [§16.2](SPEC.md#162-mandatory-exclusions).

Cross-host state uses set-union of immutable identity-addressed records/events and content-addressed blobs. A local SQLite database may be a derived transactional index, but the live database file is never the replication unit. Sync is implemented in Go (not `rsync`/`robocopy`) with manifests, content hashing/chunking (4 MiB chunks), resumable transfer, staging, validation, and atomic materialization; deletions are managed tombstones. Workspace replication is on by default and must capture remote URLs, HEAD/branch or detached state, staged/unstaged/untracked files, submodules, repo-relative cwd, and agent project configuration. See [SPEC.md §11.4-§11.6](SPEC.md#114-anti-entropy-union) and [§12](SPEC.md#12-workspace-replication).

## Workspace conflicts

Conflicts fail closed: never silently overwrite divergent destination changes. `ax diff` shows `added`/`removed`/`modified`/`type_changed`/`mode_changed`/`conflict` entries with source/destination digests. Remediation is diff, materialize-as-copy, materialize-as-worktree, or explicit managed-replacement (see operator journey §8 above). If several active sessions share one checkout, migrate the whole workspace group or materialize separate worktrees — one member cannot move alone while busy. See [SPEC.md §11.7](SPEC.md#117-conflict-handling) and [§12.6](SPEC.md#126-workspace-groups-and-worktrees).

## Native Windows vs WSL2

| Platform | Terminal backend | Reboot recovery | What to use for full `tmux` restore |
| --- | --- | --- | --- |
| **macOS / Linux / WSL2** | `tmux` via `tmux-resurrect` + `tmux-continuum` (local reboot only, not cross-host migration). Every pane runs `ax pane <logical-session-id>`. | Wrapper consults ownership after restore: resume locally only if winning lease + valid materialization, else offer remote attach/takeover or park. | Native `tmux` path — see [SPEC.md §4.2](SPEC.md#42-tmux-backend) and [§13.11](SPEC.md#1311-reboot-restore). |
| **Native Windows (PowerShell)** | Terminal-backend abstraction with Windows process/ConPTY backend. Supports mesh sync, materialization, direct/provider resume, remote attach, takeover, and continuation. | Reboot destroys live ConPTY. The user service recreates `ax pane SESSION_ID` and resumes only after lease/checkpoint validation. | Do not claim `tmux` on native Windows. Use a terminal-backend abstraction with a Windows process/ConPTY backend. See [SPEC.md §4.3](SPEC.md#43-native-windows-backend). |
| **WSL2** | Linux `tmux` backend inside the distribution | Same as Linux | Full `tmux` resurrection on a Windows computer is a **WSL2** feature and uses Linux paths, process model, and provider installation. A native Windows provider store and a WSL2 provider store are distinct materialization targets. See [SPEC.md §4.3](SPEC.md#43-native-windows-backend). |

User service: launchd agent on macOS, systemd user service on Linux/WSL2 where available, Windows Scheduled Task or user service on native Windows. Core CLI commands remain usable without the daemon. See [SPEC.md §4.4](SPEC.md#44-user-services).

Native Windows does not pretend to have `tmux`; the backend abstraction is normative. See [SPEC.md §4.1](SPEC.md#41-terminal-backend-interface).

## Provider capability summary

Capabilities are `native_resume`, `portable_store`, `managed_pty`, `appserver`, `task_board_primary`, `prompt_spawn`, and `native_goal_binding`. Every not-yet-proven cell is `conditional`, `unsupported`, or `unknown` and is **disabled** until its acceptance gate passes — capability reporting must prevent fake parity. See [SPEC.md §7.4](SPEC.md#74-capability-result) and [§8.3](SPEC.md#83-capability-matrix).

| Provider | `native_resume` | `portable_store` | `managed_pty` | `appserver` | `task_board_primary` | `prompt_spawn` | `native_goal_binding` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | A | C | C | A through task-board | A through task-board | A through task-board | A through task-board |
| Claude | A | C | C | U for direct | A through task-board | A through task-board | A through task-board |
| Gemini CLI | A | C | C | ? | U | A through task-board | U |
| Muse | C by platform/version | U | C | ? | U | A through task-board | U |
| Antigravity CLI | C (backend realm required) | U | C | ? | U | ? | U |
| Pi | A | C | C | U | ? | ? | U |
| Qwen (task-board only) | U direct | U direct | U direct | U direct | U | A through task-board | U |

`A` = available, `C` = conditional, `U` = unsupported, `?` = unknown. All `C`/`?`/`U` cells are `enabled = false`. The same matrix by platform, and the full native-store contract including required exclusions and limits, is normative in [SPEC.md §8.2](SPEC.md#82-native-store-contract-matrix) and [§8.4](SPEC.md#84-providerplatform-matrix).

Selected caveats (non-exhaustive — see [§8](SPEC.md#8-provider-and-platform-contracts) and [Appendix B](SPEC.md#appendix-b-explicit-provider-version-gates)):

- **Pi 0.73.1** has no YOLO flag; both `ax` profiles map to `default_unrestricted_tool_set` but remain distinct `ax` authority — see [§2.4](SPEC.md#24-execution-profiles).
- **Qwen** has no direct `ax-provider-qwen` claim in `v0.2.0`; task-board prompt-mode bundles only — see [§8.2](SPEC.md#82-native-store-contract-matrix).
- **Muse** and **Antigravity** unknowns in [Appendix B](SPEC.md#appendix-b-explicit-provider-version-gates) (store, cron, resume, import, quiesce, backend realm, checkpoint, Windows behavior) remain gated and disabled.
- **WSL2 and native Windows are never collapsed** into one row — an adapter accepted in WSL2 does not establish native Windows support. See [§8.4](SPEC.md#84-providerplatform-matrix).
- Known resume surfaces: Codex `codex resume UUID`; Pi `--session <path|id>` / `--continue` / `--resume` / `--session-dir`; Gemini UUID/session import; Muse `muse resume UUID`; Antigravity `agy --conversation <id>` / continue. See settled decisions § Providers and native stores and [SPEC.md §7](SPEC.md#7-provider-plugin-protocol).

## Repository layout

```
.
├── SPEC.md                          # normative v0.2.0 contract (only normative source)
├── README.md                        # this file — operator summary with links to SPEC
├── CONTRIBUTING.md                  # contributor workflow (traceability, diagrams, versioning, signing)
├── diagrams/
│   ├── c4/
│   │   ├── workspace.dsl            # Structurizr workspace (includes model/views)
│   │   ├── model.dsl                # system/container model
│   │   ├── views.dsl                # system/container views
│   │   ├── relationships.dsl        # relationships
│   │   ├── styles.dsl               # styles
│   │   ├── structurizr-SystemContext.puml      # generated C4 intermediaries (from workspace.dsl)
│   │   ├── structurizr-SystemContext-key.puml
│   │   ├── structurizr-ContainerContext.puml
│   │   └── structurizr-ContainerContext-key.puml
│   ├── plantuml/                    # PlantUML sources (takeover, session_state, mesh_deployment)
│   │   ├── takeover.puml
│   │   ├── session_state.puml
│   │   └── mesh_deployment.puml
│   ├── artefacts/                   # rendered SVGs committed for review (see CONTRIBUTING)
│   │   ├── takeover.svg
│   │   ├── session_state.svg
│   │   ├── mesh_deployment.svg
│   │   └── structurizr-*.svg (4 files)
│   └── README.md                    # diagram render quick-reference
├── scripts/
│   ├── validate_spec.py             # public repository-only validator (contracts, links, matrices, examples, metadata, fences, license, frozen-release integrity)
│   └── test_expected_red.sh         # expected-red mutation suite (proves validator and run_validation.sh fail nonzero with actionable diagnostics)
├── .github/workflows/validate.yml   # CI path with pinned documentation-tool versions (single command + expected-red)
├── .research/                       # required public provider evidence for the v0.2.0 specification package (do not weaken)
├── .planning/                       # public planning and audit evidence
├── run_validation.sh                # single public whole-package validation command (contracts + diagrams + freshness)
└── VERSION, LICENSE, CHANGELOG.md, RELEASE_NOTES.md  # publication metadata

Local-only (excluded from clean public checkout): `.task-board/` (file-backed board data) and `task-board.config.json` (local board config) — not required for `run_validation.sh`.
```

Durable `ax` data roots, SQLite-derived index, and object stores are defined in [SPEC.md §3.2-§3.3](SPEC.md#32-platform-paths) and are not part of this spec repository's layout. Path resolution precedence is flag → `AX_*` environment override (`AX_CONFIG`, `AX_DATA_DIR`, `AX_STATE_DIR`, `AX_CACHE_DIR`, `AX_RUNTIME_DIR`) → config file → platform default. See [§3.2](SPEC.md#32-platform-paths) and [§6.1](SPEC.md#61-loading-and-precedence).

## Tools, validation, and artifacts

### Toolchain used to author and validate this specification

| Command | Observed version | Purpose |
| --- | --- | --- |
| `rg --version` | `ripgrep 15.2.0` | Contract and cross-reference audits |
| `git --version` | `git version 2.50.1 (Apple Git-155)` | Git pack/index fixture generation and validation |
| `python3 --version` | `Python 3.14.4` | JSON/strict-JSONC/TOML parsing, RFC 8785 UTF-16-ordered JCS identity checks, fixture validation |
| `node --version` | `v25.6.1` | Independent JCS identity, fork projection, digest-path verification |
| `task-board --version` | `0.24.3-17-g7ac2be8 (commit 7ac2be8)` | Task evidence and board validation |
| `java --version` | `OpenJDK 26.0.1` | Pinned PlantUML runtime (CI uses Temurin 26.0.1) |
| `structurizr-cli version` | `structurizr-cli 2025.11.09`, `structurizr-java 5.0.2` | C4 validate and PlantUML export (see CONTRIBUTING) |
| `plantuml -version` | `PlantUML 1.2026.6 / 6287b33` | C4 and PlantUML SVG render |

Provider binaries are not required to validate or publish this specification. Provider/platform runtime probes belong to the future implementation-conformance suites in [SPEC.md §19](SPEC.md#19-ax-implementation-conformance-and-product-release); publication is governed separately by [§20](SPEC.md#20-specification-publication-and-governance).

For `v0.2.0`, the validator also compares LF-normalized SHA-256 digests for the five reviewed public claim documents (`SPEC.md`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `RELEASE_NOTES.md`). This is a bounded frozen-release content-integrity control, not general natural-language theorem proving. A future specification revision must intentionally update the digest map in `scripts/validate_spec.py` after reviewing the changed prose and mutation coverage.

### Exact validation commands


```shell
./run_validation.sh
echo "exit code: $?"

./scripts/test_expected_red.sh
echo "exit code: $?"
```

Board structure check (local board data, not required in a clean public checkout):

```shell
task-board validate
echo "exit code: $?"
```

Diagram sources and render are covered by the same single command; see the exact `structurizr-cli`/`plantuml` flags in [CONTRIBUTING.md](CONTRIBUTING.md#diagrams) and [diagrams/README.md](diagrams/README.md). The validator compares generated C4 PlantUML bytes exactly, validates committed SVG bytes against the v0.2.0 SHA-256 ledger, and compares PlantUML's embedded source/version metadata with a fresh render. This keeps source freshness strict while allowing font and Graphviz geometry to vary across supported documentation platforms. Verify links separately:

```shell
git diff --check
echo "exit code: $?"
```

### Diagram rendering

Sources live in `diagrams/c4/*.dsl` (Structurizr) and `diagrams/plantuml/*.puml` (three scoped diagrams: `takeover.puml`, `session_state.puml`, `mesh_deployment.puml`). Rendered SVGs are committed under `diagrams/artefacts/` for review. The single validated entry point is `./run_validation.sh` (validates Structurizr, exports C4 to PlantUML, and renders all SVGs); the exact `structurizr-cli` and `plantuml` invocations and artifact locations are documented in [CONTRIBUTING.md](CONTRIBUTING.md#diagrams) and [diagrams/README.md](diagrams/README.md). Committed SVGs must be visually inspected against [SPEC.md §3](SPEC.md#3-architecture-and-durable-local-layout) and [§13](SPEC.md#13-end-to-end-lifecycle-flows). See also [§19.4](SPEC.md#194-end-to-end-acceptance-cases) `AC-DIAG-001`.

### Artifact locations

| Artifact | Location |
| --- | --- |
| Normative spec | `SPEC.md` |
| Operator guide | `README.md` (this file) |
| Contributor guide | `CONTRIBUTING.md` |
| C4 sources | `diagrams/c4/*.dsl` |
| PlantUML sources | `diagrams/plantuml/*.puml` |
| Rendered diagrams | `diagrams/artefacts/*.svg` |
| Muse/Antigravity evidence | `.research/260819_muse-antigravity-native-store-contracts.md` |
| Board data (local) | `.task-board/` |

## License and release target

The repository is intended for public release under the **MIT License**, default branch `main`. The initial specification release was `v0.1.0`; the current corrected specification release is `v0.2.0`. The signing and authorship metadata — author `Ivan Oparin <oparin@me.com>`, SSH key `~/.ssh/ivanopcode`, SSH-signed commit and annotated tag with local signature verification, no AI `Co-Authored-By` trailer, and an explicit human approval gate before stage/commit/tag/push — are normative in [SPEC.md §20](SPEC.md#20-specification-publication-and-governance) and summarized in [CONTRIBUTING.md](CONTRIBUTING.md#signing-release-and-attribution).

## Contract map

Major implementation boundaries (see [SPEC.md](SPEC.md) for the normative definitions):

- immutable session, event, lease, checkpoint, identity, workspace, manifest, tombstone, and acknowledgement records;
- independently versioned provider, mesh RPC, task-board bridge/bundle, configuration, observation, error, and CLI-result contracts, with explicit protocol-major bindings for failure envelopes;
- one fenced owner with zero or more dormant replicas;
- content-addressed union replication with a total, disjoint object-namespace registry, resumable staging, and no live SQLite-file replication;
- exact Git and managed-tree state, including index, working bytes, submodules, cwd, and project configuration;
- exact task-board Session/bridge projection and deterministic bundle-member paths, plus restart-stable import/open/adopt/resume journal recovery;
- tagged active/passive workspace, provider, task-board, and composite materialization plans with closed kind/source/authority/action/validation/strategy combinations and stopped-session rules;
- deterministic fork re-identification of workspace topology/manifests, epoch-1 bootstrap retry/abort semantics, and transactionally complete owner resume paths;
- checkpoint-derived execution-profile authority across direct and task-board launch, takeover, resume, and fork, including providers whose two profiles map to the same native invocation;
- one Windows-safe two-hex-shard/62-hex-leaf digest path grammar across every durable/object/bundle/marker store, plus isolated parent/submodule Git pack validation and exact staged/unstaged pointer state;
- restart-stable provider object/transaction authorities, immutable managed-replica markers, derived workspace-group membership, fail-closed conflicts, version-gated provider capabilities, and explicit recovery transactions; and
- one allowlisted SSH remote-log path whose result always identifies the emitting host and is never rewritten as Mesh RPC output.

Appendix A of [SPEC.md](SPEC.md#appendix-a-normative-traceability) maps these to the settled decisions, acceptance criteria, and reviewer findings. Appendix D defines the exhaustive contract, tagged-union, cross-contract, and static-reference fixture catalog.
