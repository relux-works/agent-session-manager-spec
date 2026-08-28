# Agent Session Manager (`ax`) Specification v0.4.3

This patch specification release preserves the v0.4.2 wire registry and
reconciles the owner-approved implementation roadmap with macOS tmux/Keychain
execution-realm safety. Existing tags remain immutable. No independently
consumed contract changes version or shape; v0.4.3 is the current implementation
baseline and retains v0.4.2's corrected Directory Node dual-stack contract.

**Status caveat:** this release publishes specification artifacts only. It contains no executable `ax` product binary, and publication does not imply that any provider/platform product-conformance lane has passed.

## Roadmap and ownership boundary

- M0 establishes plugin wire contracts, internal interfaces, and a conformance
  harness without advertising a public stable SDK. M1 closes local durability
  and complete Git state. M2 is the multi-host MVP preview and already contains
  lease fencing, durable journaling, idempotency, status-first recovery, and the
  crash-boundary kernel. M3 is the first daily-driver gate.
- `ax NAME` auto-executes only one uniquely safe non-mutating attach/resume
  route. Takeover, fork, move, and ambiguity remain pure plans requiring
  confirmation or return `interactive_choice_required`.
- `ax sync --all` converges immutable objects and policy-allowed projections;
  it never changes ownership or launches a runtime. Remote attach targets the
  current owner. Graceful takeover creates the destination runtime only after a
  verified source stop and ownership commit. Force takeover cannot claim that
  an unreachable source stopped: it proves destination broker/auth readiness
  before committing the force lease and creates a runtime only under the
  winning lease, which fences the prior owner logically.
- M1 Git closure covers tracked, dirty-index, staged, unstaged, untracked,
  ignored-policy, symlink, and submodule state.

## macOS terminal execution realm

- AX uses a dedicated `tmux -S` server below an AX-owned 0700 runtime parent and
  rejects symlink or path substitution before socket operations.
- The background control plane is separate from the minimal Aqua terminal
  broker. Background CLI/SSH/daemon processes may contact an existing broker
  but may not create a credential-dependent tmux server.
- `launchctl managername` is diagnostic only. Functional acceptance requires
  an AX sentinel plus a separate provider-auth smoke bound to the tmux server
  generation, provider build, and macOS version. Aqua alone and sentinel-only
  evidence fail closed.
- tmux sockets and provider authentication state are machine-local exclusions.
  Logout/reboot without a verified GUI realm parks recovery until GUI login.

## Errata resolved

- Directory Node Protocol/Request `1.0.0` retain their published
  `darwin|linux|windows` probe vocabulary. Protocol/Request `2.0.0` use the AX
  `macos|linux|wsl2|windows` vocabulary. Manifest and Response remain `1.0.0`;
  both protocol majors bind them explicitly and negotiate without cross-major
  coercion.
- Directory identity fixtures are now checked using declared schema paths, not
  value prefixes or suggestive field names. Digest, UUIDv4, UUIDv7,
  UUIDv7-or-digest, nullable, platform, real-calendar timestamp, and
  sorted-unique constraints are executable. Adversarial fixtures recompute
  self-IDs so these checks are independently proven.

- Direct unmanaged cross-environment move is forbidden because an unmanaged
  source has no AX Session, winning lease, epoch, Checkpoint, or fenced source
  release. Operators may retain the source and clone it, or adopt it
  source-locally before creating a new managed-move plan.
- Positive Directory identity vectors now satisfy common digest, timestamp, and
  platform grammars before their RFC 8785 identities are accepted.
- Directory Node success/failure responses are a strict `body XOR error` union;
  enrichment generator discriminators must match; batched query/result indexes
  are positional and exact; lineage rows expose the deterministic member that
  supplies singular projection fields.
- Session Record/Event v1 base text now points explicitly to the independently
  closed v2/v3 variants, and the complete `ax sessions` leaf registry includes
  the typed `q`, `grep`, and `m` agent surfaces.
- Focused diagrams were rerendered after eliminating overlapping labels and
  reducing the C4 Container view to its intended internal-container scope.

## Session Directory

The human namespace is `ax sessions`, with the closed leaves `list`, `inspect`, `lineage`, `scan`, `enrich`, `jobs`, `plan`, `continue`, `operation`, `attach`, and `doctor`. Agents use the same typed Directory Query engine through `ax sessions q`, `ax sessions grep`, and `ax sessions m`; terminal/TUI scraping is not a supported interface. Existing `ax list`, `ax status`, and `ax session clone` keep their v0.3 semantics.

The Directory Node companion protocol performs source-local discovery, bounded preview, exact-head reads, runtime observation, and sanitized record publication through the same environment implementation used by Provider 2 and Session Adapter 1. It does not gain native-write, lease, workspace, or session authority. The catalog/search SQLite database and display text are rebuildable derived views, never truth.

Mesh RPC 3 adds the disjoint `directory_record` namespace for allowed immutable observations, batches, lineage, annotations/profiles, enrichment job records, continuation plans, and operation receipts. Raw transcripts, preview bodies, credentials/auth state, absolute native-store paths, model-provider payloads, terminal output, live process facts, and the derived SQLite index remain source-local and are never Directory replication members.

## Enrichment, query, and TUI

Enrichment is exact-head, bounded, redacted, and governed by immutable profiles. The isolated worker receives typed input and no AX, provider, shell, filesystem, native-store, credential, or mutation authority. Manual metadata cannot be overwritten by enrichment; concurrent manual heads remain a visible conflict; a result whose subject head changed is retained only as stale/superseded evidence.

Default list/query output contains sanitized projections and no raw excerpt. Preview and transcript grep are explicit, bounded, redacted, and source-host scoped. The Session Browser TUI uses the same planner/query/executor contracts as CLI and agent surfaces; there is no TUI-only mutation path.

## Continuation planning and execution

Planning is pure and content-addressed. Execution requires explicit confirmation and revalidates the exact source head, lease/runtime state, target Environment Tuple, authentication/workspace facts, route, and expiry. A mismatch refuses execution; AX does not silently replan or substitute another route.

Managed attach/resume/takeover/fork routes delegate to existing AX ownership, transfer, materialization, and terminal authority. Cross-environment continuation delegates to the v0.3 cloning transaction and its fidelity/read-back/Checkpoint gates. A managed cross-environment move commits and validates the target before attempting fenced source stop/release; if that last step fails, the valid target remains and the truthful partial-success outcome is `cloned_source_still_active`.

## Contract and compatibility boundary

| Contract | v0.4.3 version / disposition |
| --- | --- |
| Directory Node protocol / request | `2.0.0`; immutable `1.0.0` remains dual-stack |
| Directory Node manifest / response | `1.0.0`, explicitly bound by both protocol majors |
| Environment/Native observations, Inventory Batch, lineage, annotations, enrichment, continuation, operation receipt, and Directory Query | `1.0.0` |
| Mesh RPC | `3.0.0` for Directory; `2.0.0` remains dual-stack for core sync |
| Configuration | `2.0.0` with explicit migration/read-only downgrade behavior |
| CLI Result | `3.0.0` for `sessions.*`; Result 1/2 remain unchanged |
| Session Record and Session Event | `3.0.0` for native adoption and move lifecycle; historical v1/v2 remain valid |
| Structured Error | `1.2.0` for Directory Node 1/2, Mesh RPC 3, Directory Query 1, and CLI Result 3 |
| Provider Protocol / Session Adapter | `2.0.0` / `1.0.0`, unchanged |
| Existing cloning, transfer, materialization, Checkpoint, lease, workspace, terminal, and task-board contracts | Reused unchanged |

An RPC 2 peer continues core synchronization but is represented as `directory_mesh_unsupported`, never as an empty or current Directory inventory. An old Configuration 1 binary opens Configuration 2 only in read-only diagnostic mode and cannot write a downgraded replacement.

## Diagrams and validation

The C4 System Context and Container views now include the Directory control plane and its relationships to source-local native stores, immutable records, mesh, cloning, provider, and terminal authority. Three focused PlantUML diagrams cover component boundaries, source-local inventory/enrichment, and continuation planning/execution. All twelve committed SVGs are pinned by SHA-256, regenerated from committed sources, and visually inspected.

The public repository validator remains specification-only. It validates contract fixtures, links, publication metadata, frozen public-document bytes, diagram source/artifact freshness, retained crash/restart and cloning gates, and Directory schema/namespace/query/route/security invariants. The expected-red suite succeeds only when every focused mutation is rejected by the production validator with its expected diagnostic.

## Retained provider and platform caveats

- Qwen is only supported via task-board prompt-mode bundles (no direct native `ax-provider-qwen` claim).
- Muse relies on a narrow, version- and platform-gated native store/resume probe and advertises `portable_store=false` (`cron.db` is durable but not safely portable).
- Antigravity resumes via conversation UUID through its authenticated backend/account realm, rather than relying on copying local cache as a portable store or checkpoint.
- For Claude, the direct adapter's `appserver` capability is unsupported, but `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are available through task-board.
- Native Windows and WSL2 are distinctly partitioned. Native Windows does not claim `tmux` support, using native process supervision and ConPTY instead.
- Payload encryption at rest is not provided; `mesh.payload_encryption` remains `none`.

## Traceability

`STANDALONE_TO_AX_TRACEABILITY.md` maps every cloning and Session Directory standalone section to the resulting AX v0.4.3 section and records reuse, addition, or supersession without becoming normative. Appendix A of `SPEC.md` maps accepted decisions, task criteria, and Directory publication artifacts; Appendix D defines the exhaustive contract and fixture catalog. `SPEC.md` remains the only normative source.
The v0.4.3 roadmap and terminal-realm decisions map directly to SPEC Sections
2–4, 7.1, 12–17, 19, and Appendix D; no public summary becomes a second
normative authority.
