# Agent Session Manager (`ax`) Specification v0.4.0

This minor specification release integrates Session Directory and continuation orchestration as first-class AX subsystems. It advances the accepted v0.3 cloning baseline without rewriting any existing release tag or changing the Provider 2 / Session Adapter 1 cloning authority.

**Status caveat:** this release publishes specification artifacts only. It contains no executable `ax` product binary, and publication does not imply that any provider/platform product-conformance lane has passed.

## Session Directory

The human namespace is `ax sessions`, with the closed leaves `list`, `inspect`, `lineage`, `scan`, `enrich`, `jobs`, `plan`, `continue`, `operation`, `attach`, and `doctor`. Agents use the same typed Directory Query engine through `ax sessions q`, `ax sessions grep`, and `ax sessions m`; terminal/TUI scraping is not a supported interface. Existing `ax list`, `ax status`, and `ax session clone` keep their v0.3 semantics.

The Directory Node companion protocol performs source-local discovery, bounded preview, exact-head reads, runtime observation, and sanitized record publication through the same environment implementation used by Provider 2 and Session Adapter 1. It does not gain native-write, lease, workspace, or session authority. The catalog/search SQLite database and display text are rebuildable derived views, never truth.

Mesh RPC 3 adds the disjoint `directory_record` namespace for allowed immutable observations, batches, lineage, annotations/profiles, enrichment job records, continuation plans, and operation receipts. Raw transcripts, preview bodies, credentials/auth state, absolute native-store paths, model-provider payloads, terminal output, live process facts, and the derived SQLite index remain source-local and are never Directory replication members.

## Enrichment, query, and TUI

Enrichment is exact-head, bounded, redacted, and governed by immutable profiles. The isolated worker receives typed input and no AX, provider, shell, filesystem, native-store, credential, or mutation authority. Manual metadata cannot be overwritten by enrichment; concurrent manual heads remain a visible conflict; a result whose subject head changed is retained only as stale/superseded evidence.

Default list/query output contains sanitized projections and no raw excerpt. Preview and transcript grep are explicit, bounded, redacted, and source-host scoped. The Session Browser TUI uses the same planner/query/executor contracts as CLI and agent surfaces; there is no TUI-only mutation path.

## Continuation planning and execution

Planning is pure and content-addressed. Execution requires explicit confirmation and revalidates the exact source head, lease/runtime state, target Environment Tuple, authentication/workspace facts, route, and expiry. A mismatch refuses execution; AX does not silently replan or substitute another route.

Managed attach/resume/takeover/fork routes delegate to existing AX ownership, transfer, materialization, and terminal authority. Cross-environment continuation delegates to the v0.3 cloning transaction and its fidelity/read-back/Checkpoint gates. A cross-environment move commits and validates the target before attempting source stop/release; if that last step fails, the valid target remains and the truthful partial-success outcome is `cloned_source_still_active`.

## Contract and compatibility boundary

| Contract | v0.4.0 version / disposition |
| --- | --- |
| Directory Node protocol, manifest, request, and response | `1.0.0` |
| Environment/Native observations, Inventory Batch, lineage, annotations, enrichment, continuation, operation receipt, and Directory Query | `1.0.0` |
| Mesh RPC | `3.0.0` for Directory; `2.0.0` remains dual-stack for core sync |
| Configuration | `2.0.0` with explicit migration/read-only downgrade behavior |
| CLI Result | `3.0.0` for `sessions.*`; Result 1/2 remain unchanged |
| Session Record and Session Event | `3.0.0` for native adoption and move lifecycle; historical v1/v2 remain valid |
| Structured Error | `1.2.0` for Directory Node 1, Mesh RPC 3, Directory Query 1, and CLI Result 3 |
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

`STANDALONE_TO_AX_TRACEABILITY.md` maps every cloning and Session Directory standalone section to the resulting AX v0.4.0 section and records reuse, addition, or supersession without becoming normative. Appendix A of `SPEC.md` maps accepted decisions, task criteria, and Directory publication artifacts; Appendix D defines the exhaustive contract and fixture catalog. `SPEC.md` remains the only normative source.
