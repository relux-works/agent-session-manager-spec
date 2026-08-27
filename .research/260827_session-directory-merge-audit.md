# Session Directory Merge Preflight and Audit

Task: `TASK-260827-32hife`
Date: 2026-08-27
Scope: research and mapping only; no normative/public source edits

## 1. Executive decision

The current worktree is a coherent, clean, cloning-aware AX v0.3.0 release-candidate baseline at commit `f71a10a67ef57f4f0eec85b655b53ee64b022c34`. The cloning merge is committed locally and the Story branch points at that commit. It is one commit ahead of `origin/spec/cross-environment-session-cloning` (`2ca6fb8`). `origin/main` and the remote default branch remain at tagged v0.2.0 (`ffb971d`). Neither `v0.2.1` nor `v0.3.0` exists as a local or remote tag, despite current package prose describing them as immutable/current releases. Therefore this audit treats `f71a10a` as the clean v0.3.0 **baseline commit**, not as an already tagged release.

The directory integration is a new backward-compatible AX product feature and should advance the specification package to **AX/spec v0.4.0**. New directory contracts begin at `1.0.0`. Published/frozen closed AX contracts that must gain incompatible members or authority variants receive new majors: Mesh RPC `3.0.0`, Configuration `2.0.0`, CLI Result `3.0.0`, Session Record `3.0.0`, and Session Event `3.0.0`. Structured Error receives compatible minor `1.2.0`. Observation Event remains `1.0.0` because its event name is an open grammar rather than a closed enum and the existing cloning merge already adds required event names without changing its object shape. Provider Protocol remains `2.0.0`; the Directory Node is a separate companion protocol `1.0.0`. Existing cloning, transfer, checkpoint, materialization, and terminal contracts are reused without a directory-specific version bump.

This is a mapping recommendation for the normative producer. No public contract was edited in this task.

## 2. Repository and cloning baseline

| Fact | Evidence | Finding |
| --- | --- | --- |
| Worktree | `git status --short --branch` | Clean at preflight; branch `task-board/story/STORY-260827-28s5s5` |
| HEAD | `git log --oneline --decorate -20` | `f71a10a spec: integrate cross-environment session cloning` |
| Parent baseline | `git show --stat f71a10a` | Cloning merge changes 15 files, 3,420 insertions, 178 deletions |
| Remote cloning branch | `git rev-list --count origin/spec/cross-environment-session-cloning..HEAD` | Local HEAD is 1 commit ahead |
| Default branch | `git remote show origin` | `main` |
| Remote main | `git ls-remote` | `ffb971d`, tagged `v0.2.0` |
| Tags | local and remote tag reads | Only `v0.1.0` and `v0.2.0`; no `v0.2.1` or `v0.3.0` |
| Working diff | complete `git diff` and `git diff --cached` | Empty at baseline; nothing staged |
| Package version | `VERSION`, README, SPEC, release notes | All declare `0.3.0`/`v0.3.0` |
| Cloning source identity | standalone hash and traceability header | Both use SHA-256 `d8e2ef73...af475`; exact source matches |

The current AX cloning identifiers are authoritative for the directory merge: Session Adapter protocol/manifest/probe `1.0.0`; canonical, projection, fidelity, migration, clone manifest/report/receipt, and supported-tuple schemas `1.0.0`; clone-target Session Record/Event `2.0.0`; Materialization Plan `2.0.0`; clone Journal `3.0.0`; CLI Result `2.0.0`; Structured Error `1.1.0`. Provider Protocol and Mesh RPC remain `2.0.0` in v0.3.0.

## 3. Complete-read ledger

All 48 authoritative/current input files were consumed byte-completely for SHA-256 and line/byte counting. Markdown and PlantUML were additionally section/table inspected; the repository validation entry point parsed normative examples, contract registries, links, C4/PlantUML, and SVG freshness. SVGs are generated single-line XML, hence line count zero under `wc -l`; byte counts and digests are the meaningful ledger values.

The machine-readable full ledger is retained with the task evidence as `complete-read-ledger.tsv`. Key inputs are:

| Input | Lines | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `SPEC.md` | 9,647 | 653,786 | `86e675c13c4d7caf569a139b5b8376be52cdcff07d63d2745d637fc20cdbf987` |
| `README.md` | 439 | 40,899 | `1a411f2b08a7150a217e2ff2ad1136227a7cce0b78d82838e1ef2747547eeb75` |
| `CONTRIBUTING.md` | 223 | 21,331 | `fe9f0f70e5d2104f8275ec07348c58429dd099f1c18a0e2a01e977271b9a151b` |
| `CHANGELOG.md` | 55 | 4,573 | `b29fa1c18c2196a654459f7d7ee7fb9e2d70c11f80572d812b963fa07d586de2` |
| `RELEASE_NOTES.md` | 53 | 5,393 | `033f249c93e457b09bd2669671ff8649da33b3abbc30a592b35dd97eaac9364b` |
| `VERSION` | 1 | 6 | `d915cc95d6ca8f47ae297713ed46d4e5c5d99ddd29fc3c61e263bdf305f2b5b0` |
| `STANDALONE_TO_AX_TRACEABILITY.md` | 191 | 22,558 | `61d2c036ee358199f8406ab40b9663f91d7b6eeb1dc2ededde902306e93139d5` |
| Directory standalone spec | 1,709 | 104,886 | `486612e4c1a10dcfc6e75cf17c60beb974c6989b82c333a9350fa1befd1a448f` |
| Directory merge prompt (45 invariants) | 660 | 38,197 | `a6e250e74a9417d69d7bd47df5c09aca2c98ebd4db58f3b3b408f21cc151eea5` |
| Directory unresolved questions | 63 | 4,510 | `05e54e2295d097026b5699627b5c01aa7bb400243c18a0ae1273a69a24214cc3` |
| Directory component diagram | 79 | 2,401 | `ccb9226f619bbff7d248084cde140cf402020d4b8c6cea65b5553f0052340503` |
| Directory enrichment diagram | 51 | 1,830 | `898da34e3fa4f97e8c769e93b9b71c7e66cddcb2fc8a7040f6105ad989f4b38a` |
| Directory continuation diagram | 63 | 2,466 | `bde91b73969bf753baad860dd451a3907426fa400f240048319bc6a839b11088` |
| Cloning standalone spec | 1,794 | 94,615 | `d8e2ef73f6a07ef58219fd2c4e8e16dff681728ec0b153653fc87f1f200af475` |
| Cloning unresolved questions | 10 | 878 | `9059db8f0de6335b51da319fcc712ec3bdacae416f88a19ec1fe3615f4607542` |
| `scripts/validate_spec.py` | 2,133 | 107,128 | `74f3bf4515d5c3f63c3c4fadbc1ce0cd418d956e209f1d0c5040dd1e47fb234e` |
| `scripts/test_expected_red.sh` | 1,503 | 59,707 | `7c80646eaab848dd520af757646970d48f5819d2faac1b2c098c3000cdae19e0` |
| `run_validation.sh` | 111 | 4,437 | `ce7bb096b199321f13a3e83f76b484a9d89bb86b276df26c964aebd8e8237411` |
| `.github/workflows/validate.yml` | 85 | 3,517 | `2bcc9c0ed94295ed7af9e73f267f3328c858c241b4ee0bb49823a98ae0f39040` |
| retained research | 379 | 40,390 | `0001f769a111bbf7fb107ec876bc71471a799f37867e84e419ce4fe213c7b569` |
| planning epic/story artifacts | 12 / 29 | 277 / 1,099 | `a138e00...f8361` / `f71727e...f2c1` |

The ledger also covers `LICENSE`, `diagrams/README.md`, all 6 C4 DSL sources, all 4 generated C4 PlantUML intermediaries, all 5 handwritten PlantUML sources, and all 9 SVG artifacts. Their exact hashes/line/byte counts are in the attached TSV.

## 4. Directory Section 3.1 contract mapping

| Standalone concept/contract | Current cloning-aware AX location | Reuse/change/new contract | Final identifier/version | Compatibility impact | Validation coverage required |
| --- | --- | --- | --- | --- | --- |
| Directory node protocol | Provider §7 and Session Adapter §7.8 supply trust/framing precedent; no equivalent | New companion protocol, same environment implementation | `urn:ax:protocol:session-directory-node` `1.0.0` | Additive independent family; Provider 2 unchanged | Exact envelopes, one frame, 11 operations, deadlines, echo, size, failure binding, process exit |
| Directory node manifest | No equivalent | New schema | `urn:ax:schema:session-directory-node-manifest` `1.0.0` | Additive | Closed operations/capabilities/limits/tuple/schema registry; shared executable/module binding |
| Directory node request | No equivalent | New schema/envelope body contract | `urn:ax:schema:session-directory-node-request` `1.0.0` | Additive | Per-operation exact body and mutation/idempotency rules |
| Directory node response | No equivalent | New schema/envelope body contract | `urn:ax:schema:session-directory-node-response` `1.0.0` | Additive | Disjoint success/failure, echoed identity, no partial trust |
| Environment Observation | Environment Tuple and Provider/Adapter probes are related but not historical directory authority | New immutable directory record | `urn:ax:schema:environment-observation` `1.0.0` | Additive; must not duplicate tuple admission | Self-ID, host authority, explicit environment/provider map, auth status without credentials |
| Native Session Observation | Provider Identity is managed-only authority; no unmanaged inventory | New immutable directory record | `urn:ax:schema:native-session-observation` `1.0.0` | Additive | Self-ID, chain continuity, raw ID/path exclusion, exact/strong/weak identity |
| Inventory Batch | No equivalent | New immutable directory record | `urn:ax:schema:session-inventory-batch` `1.0.0` | Additive | Atomic membership, sequence/cursor, partial/offline cannot assert missing |
| Lineage Link Record | AX fork events and Clone Lineage Receipt provide evidence, not cross-authority grouping | New immutable directory record; derived graph reuses existing evidence | `urn:ax:schema:conversation-lineage-link` `1.0.0` | Additive | Allowed evidence classes, anchors, ambiguity/resolution, suggestions excluded |
| Session Annotation Record | No AX display metadata authority | New immutable directory record | `urn:ax:schema:session-annotation` `1.0.0` | Additive | Identity/snapshot binding, exact head, evidence, profile, supersession DAG, manual precedence |
| Enrichment Profile | Configuration has no model metadata policy | New immutable schema referenced by Config 2 | `urn:ax:schema:session-enrichment-profile` `1.0.0` | Additive | Closed generator/input/redaction/network/limit policy; no secret endpoints |
| Enrichment Job Request | No equivalent | New immutable directory record | `urn:ax:schema:session-enrichment-job-request` `1.0.0` | Additive | Exact head/profile/kinds/basis and idempotency digest |
| Enrichment Job Receipt | No equivalent | New immutable receipt-chain record | `urn:ax:schema:session-enrichment-job-receipt` `1.0.0` | Additive | Predecessor/state transitions, concurrent heads, stale/superseded behavior |
| Continuation Plan | Materialization Plans 1/2 and Projection Plan cover subordinate effects only | New pure orchestration plan referencing existing plans/receipts | `urn:ax:schema:session-continuation-plan` `1.0.0` | Additive | Self-ID, expiry, exact expectations, route matrix, no mutation/no silent replan |
| Directory Operation Receipt | Existing Journals cover materialization only | New immutable cross-subsystem receipt chain | `urn:ax:schema:session-directory-operation-receipt` `1.0.0` | Additive | State/step continuity, effect receipts, uncertain/recovery, lost-response idempotency |
| Directory Query Schema | No typed directory query contract | New schema shared by CLI/TUI/agent query | `urn:ax:schema:session-directory-query` `1.0.0` | Additive | Grammar, field/preset/filter registry, projection authorization, batch/page bounds, mutation safety |
| Structured Error | Error 1.0 core; Error 1.1 clone/Session Adapter | Compatible minor adds directory codes and exact bindings | `urn:ax:schema:error` `1.2.0` for Directory Node 1/CLI Result 3; RPC 3 binds it explicitly | Compatible schema shape, extended stable code registry | Exact code/exit map, bound-version errors, bootstrap/unparseable-frame behavior |

Every new immutable self-ID must be added to AX §1.6's self-identity field registry. `observation_id`, `batch_id`, `lineage_link_id`, `annotation_id`, `profile_id`, `job_request_id`, `job_receipt_id`, `plan_id`, and `directory_receipt_id` are total and disjoint. A generic `record_id` may instead be adopted only if every schema and namespace membership rule is made exact; silently mixing standalone self-field names is not acceptable.

## 5. Existing AX contract and version impact

| AX contract | Current v0.3.0 | Proposed after directory merge | Reason and migration |
| --- | ---: | ---: | --- |
| AX/spec package | `0.3.0` | **`0.4.0`** | New backward-compatible directory/TUI/query/orchestration feature |
| Normative registry | cloning-aware v0.3 set | Register 15 directory contracts plus Error 1.2 | Registry change accompanies v0.4; no implicit versions |
| Mesh RPC | `2.0.0`, six closed namespaces, exact 14-key hello map | **`3.0.0`** | Seventh `directory_record` namespace, new hello contract keys/cardinalities/membership; serve RPC 2 dual-stack for at least one stable release |
| Configuration | `1.0.0`, closed root/tables | **`2.0.0`** | New closed directory/enrichment/disclosure/query/schedule/retention tables; explicit `ax migrate config`, backup, atomic write; old binary read-only |
| CLI Result | `1.0.0`; `2.0.0` clone-only | **`3.0.0`** | New directory result bodies and Directory Entry; do not alter SessionSummary 1/clone Result 2 |
| Structured Error | `1.0.0`; `1.1.0` clone-only | **`1.2.0`** | Shape-compatible new codes; Directory Node 1/CLI 3 bind it; RPC 3 states its binding |
| Observation Event | `1.0.0` with open event-name grammar | **`1.0.0` reused** | Add required directory event names; no top-level/member/enum change. If implementation closes event names, use 1.1 instead |
| Provider Protocol | `2.0.0` | **`2.0.0` reused** | Directory Node is companion façade; Provider retains native transaction/launch/resume and store mutation authority |
| Provider manifest/probe | `1.0.0` | **`1.0.0` reused** | Directory capability declarations live in Directory Node Manifest/Environment Observation; cross-façade consistency is validated |
| Session Record | v1 general; v2 clone-target derivation union | **`3.0.0`** for unified `origin|same_provider_fork|cross_environment_clone|native_adoption` creation provenance | Adding adoption authority to closed v2 union is not safe as in-place change; provider immutability retained; move is not a creation variant |
| Session Event | v1 general; v2 clone-target lifecycle | **`3.0.0`** | Closed authority event union adds native adoption and cross-environment move/source-release lifecycle; display annotations stay directory records |
| Materialization Plan | v1 general; v2 clone | Reuse `1.0.0`/`2.0.0` | Continuation Plan selects existing subordinate plans; do not add directory route tags to materialization plans |
| Materialization Journal | v2 general; v3 clone | Reuse `2.0.0`/`3.0.0` | Directory Operation Receipt chains orchestration; underlying journal semantics unchanged |
| Checkpoint, Provider Identity, Workspace Group, transfer/chunk/blob/tombstone | `1.0.0` | Reuse `1.0.0` | Existing authority, closure, transfer, and retention semantics are sufficient |
| Session Adapter and cloning schemas | current v0.3 versions | Reuse unchanged | Directory consumes final v0.3 identifiers; no duplicate converter schemas |

### Why CLI Result 3 rather than extending 2

The cloning commit freezes v0.3.0 public claim digests, has a complete 118-mutation gate, and explicitly scopes CLI Result 2 to `session.clone.*`. Even though v0.3.0 is not tagged, the assigned task requires treating it as a clean baseline before directory edits. Directory bodies therefore should not be folded silently into clone-only major 2; major 3 is the exact closed-contract decision.

### Why Session Record/Event 3

Session Record 2 has a closed derivation union of `origin`, `same_provider_fork`, and `cross_environment_clone`, with origin/fork reserved. Native adoption establishes a new AX logical authority around an existing native identity and cannot be inferred from timestamps or hidden in extensions. Adding `native_adoption` changes authority interpretation. Session Event 2 similarly has clone-only closed variants. Major 3 makes the general creation/lifecycle union explicit. A cross-environment move uses clone creation provenance plus later move/source-release events and operation receipts; it never changes the target record's provider or rewrites the source.

## 6. Environment and cloning reconciliation

- `environment_id = claude-code` maps explicitly to AX `provider_id = claude`.
- `environment_id = codex` maps explicitly to AX `provider_id = codex`.
- Future mappings are manifest/registry data and are never inferred by string equality.
- The current `EnvironmentTuple` already separates `provider_id` and `environment_id`; Directory Environment Observation must reuse that tuple semantics rather than create a second admission model.
- One environment implementation/library backs Provider 2, Session Adapter 1, and Directory Node 1 façades. Protocol boundaries preserve privilege/version separation; parser, native identity, redaction, tuple gates, and fixtures have one source of truth.
- Cross-environment directory routes consume v0.3 Clone Capture/Raw Object manifests, Canonical Session/Event, Projection Plan, Fidelity Report, Migration Checkpoint, Read-Back Evidence, Validation Report, target Checkpoint, and Clone Lineage Receipt. Directory planning must never manufacture fidelity or relabel continuation context as a native clone.

## 7. Route and outcome mapping

| Route | Existing AX/cloning owner | Directory addition | Exact successful/partial outcome |
| --- | --- | --- | --- |
| `managed_local_attach` | AX terminal/lease/runtime | Select exact local owner; pure plan | `attached` |
| `managed_remote_attach` | AX authenticated remote attach | Resolve owner/reachability | `attached` |
| `managed_local_resume` | AX owner resume + Provider 2 | Exact head/runtime preflight | `resumed_managed` |
| `managed_takeover` | AX graceful/force takeover, workspace cohort | Directory selects intent/target only | `taken_over` |
| `managed_fork` | AX fork/checkpoint/materialization | Lineage link derived from fork evidence | `forked` |
| `adopt_existing_native` | AX new Session/Workspace/lease/checkpoint + Provider identify/resume | New gated adoption transaction/receipt | `adopted` |
| `same_environment_clone` | Provider-native safe clone when declared, otherwise canonical cloning pipeline | Exact source/target tuple planning | `cloned` |
| `cross_environment_clone` | v0.3 cloning subsystem + AX transfer/target launch | Host/workspace route and post-clone attach | `cloned` |
| `cross_environment_move` | Clone first; AX/Provider source stop/release after target commit | Compound target-first plan/receipt | `moved_cross_environment`; `cloned_source_still_active` if source release fails |
| `open_unmanaged_local` | Source-local native resume only | Explicit unmanaged warning; no AX claims | `opened_unmanaged_local` |
| `archive_or_context_fallback` | Clone archive/context terminal | Explicitly non-native/no managed target | `archive_or_context_fallback` |

`planned_only` is returned by successful pure planning for any eligible route. Route names and outcomes remain separate registries. Attach/resume/takeover/fork/adopt/clone/move are not interchangeable labels.

Target-first move semantics are exact: capture -> transfer -> project -> staged/live validate -> create/finalize target AX authority -> publish lineage -> only then stop/release source. Failure after target commit is partial success `cloned_source_still_active`, never rollback or deletion of the valid target.

## 8. Replication, records, and authority

Mesh RPC 3 adds exactly one disjoint namespace, `directory_record`. Its membership is:

1. Environment Observations;
2. Native Session Observations and Inventory Batches;
3. Lineage Link/Resolution Records;
4. Session Annotations and Enrichment Profiles allowed by disclosure policy;
5. Enrichment Job Requests and Receipts;
6. Continuation Plans; and
7. Directory Operation Receipts.

Raw/native transcripts, preview bodies, credentials/auth state, model-provider payloads, terminal output, live PIDs/PTY/socket facts, absolute native-store paths, and the derived SQLite index are not members. `objects.get`, Merkle roots/children, hello contract maps, namespace cardinality (six -> seven), membership validation, size limits, and examples all must change together. RPC 2 peers continue core sync and are represented as `directory_mesh_unsupported`, not empty inventory.

Authority remains split cleanly:

- AX records/leases/checkpoints own managed session identity and lifecycle.
- Provider native stores own native history.
- Clone receipts own cross-environment derivation evidence.
- Source-host observations own native inventory facts.
- Directory records own annotations, explicit operator links, plans, and orchestration receipts.
- SQLite is a rebuildable projection and no timestamp resolves an authority conflict.

## 9. Configuration 2 mapping

Configuration 2 must add closed, secret-free structures for:

| Area | Required content |
| --- | --- |
| Directory service | enablement, on-demand/service mode, scan schedule, bounded concurrency |
| Installations/scan roots | adapter installation selection and opaque allowed root authorities; no credentials/auth roots |
| Freshness | current/aging/stale thresholds, scan debounce, plan expiry |
| Metadata disclosure | `local_only|mesh_sanitized|reference_only`, per peer/data class where supported |
| Enrichment profiles | immutable profile IDs, deterministic/local/remote generator selection, data classes, model endpoint class without credential, debounce/limits |
| Query/search | page/batch/result/grep limits; lexical default; optional local-only embeddings |
| Retention | observation/job/operation retention and provenance-preserving compaction |
| Upgrade policy | existing-mesh generated-summary replication requires explicit choice |

Major migration requires `ax migrate config`, backup, atomic replacement, and downgrade read-only behavior. No arbitrary environment passthrough or secret value is accepted.

## 10. CLI, query, and TUI mapping

Human namespace: `ax sessions`, with closed leaves `list`, `inspect`, `lineage`, `scan`, `enrich`, `jobs`, `plan`, `continue`, `operation`, `attach`, and `doctor`. Existing `ax list`, `ax status`, and `ax session clone` retain their v0.3 semantics.

CLI Result 3 adds separate Directory Entry, inspection, lineage, host/environment, job, plan, operation, attach/continue, and doctor bodies. It must not add fields to `SessionSummary 1.0.0` or clone Result `2.0.0`.

Directory Query Schema 1 defines `schema`, `sessions`, `session`, `lineage`, `hosts`, `environments`, `jobs`, `plans`, `count`, `distinct`, and `directory_summary`; field presets `minimal`, `overview`, `activity`, `routing`, and `full`; bounded `skip`/`take`; typed filters/sorts; and guarded `set_title`, `set_tags`, `set_pin`, `enrich`, `plan_continue`, and `execute_plan`. There is no delete mutation. Transcript grep is explicit, source-local, single-host/session scoped, authorized, bounded, and never a default mesh fan-out.

The TUI is another client of the same typed engine. It adds four bounded regions, stable-ID selection across refresh, hostile-string escaping, source-local preview after explicit selection, disabled actions with reasons, job/receipt views, and the continuation wizard. TUI navigation/filter/preview/plan inspection are read-only; all mutations go through the same planner/executor.

## 11. Forty-five invariant reconciliation

| # | Merge disposition and AX destination |
| ---: | --- |
| 1 | Preserve provider-bound `session_id`; AX §§2/5 |
| 2 | Clone/move creates target Session; v0.3 §13.14 plus Session Record 3 |
| 3 | Conversation Lineage is derived, no lease domain; directory domain section |
| 4 | Name/native ID/instance/anchor/title remain distinct; AX §2 + directory records |
| 5 | Display title never rewrites name or identity; annotation/query rules |
| 6 | Observation authored only by resolving source host; Directory Node + record schema |
| 7 | Native store is content authority; SQLite rebuild rules |
| 8 | Similarity/path/title/time/text never author lineage; lineage validator |
| 9 | Only fork/clone/move/adopt/binding/operator evidence authorizes edges |
| 10 | Weak identity blocks remote continuation/linking; planner gate |
| 11 | Generated annotations bind exact semantic head; Annotation 1 |
| 12 | Same head survives rescan; changed subject head stales; catalog selection |
| 13 | Manual metadata identity-bound and enrichment cannot overwrite it |
| 14 | Supersession DAG conflicts visible; clocks never win |
| 15 | Profiles/jobs/receipts/annotations/plans are immutable/content-addressed as specified |
| 16 | Job/operation state derives from receipt chains |
| 17 | Deterministic extraction has no model dependency; Config/Profile 2/1 |
| 18 | Default enrichment input is bounded public user/assistant only |
| 19 | Worker has no mutation/shell/ambient credential authority |
| 20 | Session content is untrusted data, never control input |
| 21 | Directory stays local-first/leaderless; source node authority |
| 22 | Sanitized immutable metadata uses AX anti-entropy/RPC 3 |
| 23 | Transcript/preview/secrets/runtime/path data excluded from `directory_record` |
| 24 | `missing` requires successful non-partial same-root/realm scan |
| 25 | Offline sessions remain visible with age/state |
| 26 | Gaps/branches visible; no wall-clock resolution |
| 27 | Policy tightening never claims remote erasure |
| 28 | Continuation planning is pure; Continuation Plan 1 |
| 29 | Mutations require exact unexpired plan and operation UUID |
| 30 | All source/target/lease/runtime/workspace/policy/capability expectations revalidated |
| 31 | Mismatch is stale-plan; no replan/host/intent/fidelity/force/fallback substitution |
| 32 | Ownership/fencing/checkpoint/workspace/transfer/materialization/terminal/recovery stay AX-owned |
| 33 | Capture/canonical/projection/fidelity/validation stay cloning-owned |
| 34 | Remote unmanaged open impossible; adopt locally or clone managed |
| 35 | Move commits target before source stop/release |
| 36 | Post-commit stop failure is `cloned_source_still_active`; target retained |
| 37 | Spawn is not success; native discovery/identity/readability/resume/readiness required |
| 38 | Lost-response replay cannot duplicate any durable target/effect |
| 39 | TUI/CLI/agent use one typed engine |
| 40 | Agent surface provides schema/projection/batch/page/grep/guarded mutations; never scrapes TUI |
| 41 | Default list/status has sanitized metadata, no excerpts |
| 42 | Excerpts bounded/redacted/source-local/explicit |
| 43 | Terminal rendering escapes ANSI/OSC/bidi/control/hostile width |
| 44 | Launch uses argv/cwd/env allowlist; never shell concatenation |
| 45 | Auth status may be observed; credentials/auth stores excluded everywhere |

All 45 are compatible with current AX invariants. None requires duplicating lease, workspace, transfer, materialization, terminal, or cloning authority.

## 12. Unresolved-question decisions

| Question | Decision |
| --- | --- |
| CLI namespace | `ax sessions`; preserve `ax list/status` |
| Adapter packaging | Separate Directory Node 1 façade, shared implementation with Provider/Session Adapter |
| RPC release/dual stack | RPC 3 in AX/spec v0.4; serve RPC 2 for at least one stable release |
| Cloning identifiers | Use exact v0.3 identifiers listed in §2; no standalone aliases |
| Session provenance | Session Record 3 unified creation union with native adoption; move represented by clone provenance + lifecycle receipts/events |
| Default enrichment | Deterministic extraction available; no silent remote model |
| Metadata disclosure | New meshes may use documented trusted-mesh defaults; existing meshes require explicit upgrade choice |
| Adoption release | Disabled per exact tuple until identity/boundary/binding/checkpoint/resume/idempotency/crash tests pass |
| Search | Lexical/structured v1; embeddings optional, local-only, non-authoritative |
| Language/TUI library | Implementation technology remains non-normative; use AX's Go distribution model and test behavior, not library identity |

The four cloning deferred questions are already closed by v0.3: `ax session clone`; companion Session Adapter 1 in the provider executable; Session Record 2 clone provenance; signed release-authority tuple registry with local deny-only policy.

## 13. Diagrams, fixtures, and validator delta

### Diagrams

Required source/artifact changes for the normative merge:

1. Extend C4 model/relationships/views with Directory Controller, Catalog/Freshness, Lineage, Enrichment Scheduler/Worker, Directory Node, derived index, immutable directory records, query/TUI clients, and cloning/AX boundaries.
2. Add focused handwritten `session_directory_enrichment.puml` and `session_directory_continuation.puml` (names may follow repository snake_case convention); either adapt the standalone component diagram into C4 or add one focused component PlantUML only if C4 cannot express the needed internal boundary.
3. Render corresponding SVGs into `diagrams/artefacts`, update diagram README/source/artifact counts, frozen SVG ledger, and source metadata checks.
4. Visually inspect readability, clipping, width, contrast, source-local arrows, pure-plan boundary, target-first move order, and AX/cloning authority separation.

### Fixture expansion

Appendix D must add directory registry fixtures, all closed tagged unions, self-ID/JCS examples, Claude/Codex managed/unmanaged/weak/exact/corrupt/active/stopped stores, multiple realms, observation freshness/presence/gap/conflict chains, annotation supersession and stale-head races, deterministic/model/prompt-injection jobs, authoritative/suggested lineage, metadata policies, all 11 routes/outcomes, lost responses at every durable step, TUI width/hostile strings, RPC 3 negotiation/namespace membership, and Config 2/CLI 3/Error 1.2/Session 3 migration fixtures.

### Current baseline coverage

`validate_spec.py` covers publication metadata/frozen digests, links/fences/examples, exact current registries, provider/platform matrices, Provider/RPC/materialization corrections, crash/restart gates, and the v0.3 cloning contract gate. `test_expected_red.sh` contains 118 green expected-red mutations, including clone trust/fidelity/transaction/read-back/tuple/traceability/diagram/security regressions. It contains **no directory contract, namespace, query, enrichment, lineage, route, TUI, Config 2, RPC 3, or Session 3 coverage yet**.

### Required positive/static gates

The producer must add the 22 checks enumerated in the merge prompt: registry/version completeness; directory self-IDs/JCS; strict examples; closed shapes; Node operation/idempotency; namespace/hello/Merkle membership; environment/provider mapping; observation chains; annotation heads/DAG; receipt chains; lineage evidence; disclosure exclusions; pure/revalidated plans; route/outcome completeness; target-first move; remote-unmanaged refusal; cloning/Fidelity linkage; CLI/query/TUI result registry; tuple acceptance; security/terminal escaping; traceability; and document/diagram/release consistency.

### Required negative evidence

At minimum add isolated expected-red mutations for wrong namespace, missing hello contract, stale six-namespace cardinality, unknown directory field, wrong self-ID/unsorted IDs, raw native/path/transcript replication, missing-after-partial/offline, clock conflict resolution, unbound generated annotation, enrichment overwriting manual title, incomplete supersession resolution, changed-input idempotency reuse, stale-plan execution/route substitution, remote unmanaged open, provider change in place, clone success without final fidelity/read-back, source stop before target commit, shell-concatenated launch, raw excerpt in default output, stale diagrams/hashes, and unsupported README/release claims. Gate tests must drive the production validator entry point and narrowing mutations, not helper-only/delete-only proxies.

## 14. Baseline validation evidence

All commands were run directly as standalone processes with `PYTHONDONTWRITEBYTECODE=1`; output is persisted under `.temp/TASK-260827-32hife/` and included in the task evidence bundle.

| Command | Exit | Evidence |
| --- | ---: | --- |
| `./run_validation.sh` | 0 | `run-validation-02.log`, `run-validation-02.exit` |
| `./scripts/test_expected_red.sh` | 0 | `expected-red-01.log`, `expected-red-01.exit`; 118 passed, 0 failed |
| `task-board validate` | 0 | `task-board-validate-01.log`, `.exit` |
| `git diff --check` | 0 | `git-diff-check-01.log`, `.exit` |

The first `run_validation` invocation also appeared green but the execution wrapper did not return an explicit process code; it is not counted. The second run has an explicit persisted `0`. Expected-red exceeded the first tool yield but remained the same foreground process; it was polled until its own exit file reported `0`. No background gate was abandoned.

## 15. Deviations and risks

1. **Release-reference anomaly:** v0.3 package prose says v0.2.1/v0.3.0 tags are immutable/current, but neither tag exists locally or remotely. The normative producer must not claim published/tagged v0.4 until the human release step actually creates it.
2. **Session Record major:** the standalone suggests a new version only if provenance is not external. This audit chooses Session Record 3 because current v2 already provides the preferred closed derivation union and adoption is authority-bearing; an external-only adoption record would split creation provenance.
3. **Observation Event:** kept at 1.0 because `event` is a grammar, not a closed enum. If the producer changes it to a closed required-name registry, bump to 1.1 and update bindings.
4. **Provider Protocol:** remains 2; adding Directory operations there would require Provider 3 and blur privilege separation. The companion Node is cleaner and matches the recommended resolution.
5. **Materialization contracts:** no directory tags are added. Continuation Plan/Receipt orchestrate existing AX/cloning plans and journals. Any later need for a new materialization kind/intent must trigger its own exact major analysis.
6. **Existing-mesh privacy:** generated summary replication is not enabled silently; operator choice is required because v0.3 disclosed less metadata.
7. **Adoption:** remains unavailable until exact tuple evidence passes; clone is the safe fallback. No specification prose may imply availability merely because discovery works.

## 16. Handoff recommendation

The normative producer can begin from commit `f71a10a` after accepting this mapping. The safe edit order is: registry/common self-IDs -> domain records -> Directory Node/shared environment mapping -> catalog/lineage/enrichment -> RPC 3 and Config 2 -> query/CLI Result 3/TUI -> continuation planning/execution and Session Record/Event 3 -> errors/observability -> fixtures/validator/expected-red -> diagrams/public docs/version/frozen digests -> full clean validation.

No unresolved issue requires a human product decision before normative drafting. The only release-owner action remains the later human stage/commit/tag/push/signing workflow; it is outside this research task.
