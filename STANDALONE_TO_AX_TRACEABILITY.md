# Standalone Subsystems to AX v0.4.2 Traceability

This document is a non-normative migration index. [SPEC.md](SPEC.md) is the only normative source; this file does not restate or extend its requirements. It accounts for the standalone *Cross-Environment Agent Session Cloning Specification v0.1.0* source identified by SHA-256 `d8e2ef73f6a07ef58219fd2c4e8e16dff681728ec0b153653fc87f1f200af475` and the standalone *AX Session Directory and Orchestration Specification v0.1.0* source identified by SHA-256 `486612e4c1a10dcfc6e75cf17c60beb974c6989b82c333a9350fa1befd1a448f`.

AX v0.4.2 preserves the v0.3.0/v0.4.0 integration mapping below and corrects its implementation baseline. Direct unmanaged move is superseded by unmanaged clone or source-local adoption followed by a newly planned managed move. Directory Node Protocol/Request `1.0.0` remain immutable with their published platform vocabulary; `2.0.0` carries the AX platform vocabulary under an explicit dual-stack binding.

Disposition codes:

- **R** — an existing AX contract or rule is reused.
- **N** — AX v0.3.0 adds an independently versioned contract, variant, flow, or gate.
- **S** — standalone wording or structure is intentionally superseded by an AX-native contract.
- **E** — evidence-only material remains non-normative.

Rows with multiple codes preserve part of the standalone intent while replacing its wire shape or ownership boundary. AX section numbers refer to [SPEC.md](SPEC.md).

## Complete section mapping

| Standalone section | AX v0.3.0 target | Disposition and migration result |
| --- | --- | --- |
| 1. Conformance, scope, and product boundary | §§1-2, 13.14, 16, 19 | R/N — integrated as an AX conformance target and product feature. |
| 1.1 Conformance language | §§1.1, 19.3-19.5 | R — AX normative language and conformance model control. |
| 1.2 Objective | §§1.2, 2.1, 13.14 | N — native resumable cross-environment derivation is added. |
| 1.3 Non-goals | §16.6 | R — exclusions merge into the AX threat/product boundary. |
| 1.4 Terminology | §§2.1, 7.8, 13.14.1-13.14.5 | R/S — AX names win where vocabularies overlap. |
| 1.5 Global invariants | §§2.2, 13.13-13.14, 16 | R/N — all fifteen standalone invariants are preserved across AX-owned contracts and gates. |
| 1.6 Clone semantics and AX ownership | §§5.1, 13.14 | N — clone creates a new logical/native identity and leaves source authority unchanged. |
| 2. System architecture | §§3.1, 7.8, 13.14.1-13.14.5 | R/N/S — pipeline retained inside existing AX components. |
| 2.1 Required components | §3.1 | R — existing CLI, provider host, object store, and materializer are reused. |
| 2.2 One adapter per environment | §7.8 | R/S — one companion protocol per provider executable replaces separate adapter executables. |
| 2.3 Trust boundaries | §§7.1, 7.8, 16 | R — AX plugin trust remains authoritative; operation authorities are narrowed. |
| 2.4 Pipeline overview | §13.14 | R/N — sequence retained using AX journals, records, and events. |
| 3. Contract registry and common data rules | §§1.5-1.6 | R/N — AX registry owns every reused and new contract. |
| 3.1 Contract registry | §1.5 | N — cloning contracts and changed majors are registered independently. |
| 3.2 Common logical model | §1.6 | R — JCS, safe integers, timestamps, IDs, paths, extensions, and limits are reused. |
| 3.3 Object identity | §§1.6, 10.2-10.4, 13.14.1-13.14.3 | R/N — AX CAS rules are reused and new self-identifying clone objects are registered. |
| 3.4 Size model | §§7.8, 13.14.1 | R — canonical size ceilings and blob references are retained. |
| 4. Environment adapter plugin protocol | §§7.1, 7.8, 13.14.5 | N/S — companion Session Adapter 1.0 replaces the standalone plugin surface. |
| 4.1 Discovery and trust | §§7.1, 7.8 | R/S — same trusted provider executable and host-observed digest replace separate discovery. |
| 4.2 Framing and lifecycle | §7.8 | N/S — exact disjoint Session Adapter success/failure envelopes replace nullable standalone responses. |
| 4.3 Adapter manifest | §7.8 | N/S — Session Adapter Manifest/Probe bind provider, environment, and executable evidence. |
| 4.4 Capability registry and probe | §§7.8, 13.14.5 | N — closed adapter capabilities are conjoined with Provider Probe and signed tuple admission. |
| 4.5 Operation registry | §7.8 | N/S — conversion operations remain; standalone materialization operations move to Provider 2 plus AX materialization. |
| 4.6 Source and target authority rules | §§7.5, 7.8, 16.3-16.4 | R — AX read, object-sink, transaction, path, and process authorities control. |
| 5. Clone bundle and raw layer | §§10.2, 13.14.1, 13.14.3 | N/S — immutable branch-exclusive AX generation chains replace one standalone bundle shape. |
| 5.1 Bundle properties | §13.14.3 | N — archive and target-bearing generation chains are immutable and branch-exclusive. |
| 5.2 Bundle manifest | §13.14.3 | N/S — generation-selected content and three registered object-manifest roles replace one nullable manifest. |
| 5.3 Raw capture completeness | §13.14.1 | N — Capture and Raw Object Manifests close every source item without fabricated AX identity. |
| 5.4 Stable snapshot proof | §§7.8, 13.14.1, 13.14.4 | R/N — pre/post capture proof is retained and a post-publication source recheck is added. |
| 5.5 Project capsule | §§5.4, 10.4, 12 | S — AX Checkpoint and Workspace Transfer Manifest references replace it. |
| 6. Canonical session model | §13.14.1 | N — AX owns a new independently versioned canonical family. |
| 6.1 Canonical Session | §13.14.1 | N — Canonical Session 1.0.0. |
| 6.2 Canonical Event envelope | §13.14.1 | N — Canonical Event 1.0.0 remains distinct from lifecycle Session Event. |
| 6.3 Event-kind registry | §13.14.1 | N — closed registry retained, including opaque events. |
| 6.4 Content blocks | §§10.2, 13.14.1 | R/N — closed canonical union reuses AX Blob Descriptor. |
| 6.5 Canonical tool identity | §13.14.1 | N — source identity and semantic confidence are preserved without authorization transfer. |
| 6.6 Usage events | §§13.14.1-13.14.2 | N — source metadata remains descriptive; unknown values stay unknown. |
| 7. Fidelity Model | §13.14.2 | N — core-owned item/class reconciliation is added. |
| 7.1 Principle | §13.14.2 | N — the seven-disposition model is retained. |
| 7.2 Reason registry | §13.14.2 | N — closed core reasons plus namespaced extensions are retained. |
| 7.3 Fidelity profiles | §§13.14.2, 14.1 | N — profiles and default become AX CLI policy. |
| 7.4 Fidelity Report | §13.14.2 | N — Fidelity Report 1.0.0 is core-owned. |
| 7.5 No-fabrication rule | §§13.14.1-13.14.2, 16 | R/N — preserved as an unconditional AX boundary. |
| 8. Target Projection | §§7.8, 13.14.1-13.14.4 | N/S — projection is AX-planned; Provider 2 retains native writes. |
| 8.1 Projection strategies | §13.14.2 | N — exact strategies retained; continuation context is explicitly non-native. |
| 8.2 Projection Plan | §13.14.2 | N/S — final-report prediction is replaced by a fidelity-basis digest and read-back-derived report. |
| 8.3 Messages and instructions | §§13.14.1-13.14.2, 16 | R/N — history is preserved without foreign instruction authority. |
| 8.4 Reasoning | §§13.14.1-13.14.2 | N — foreign signed/encrypted reasoning is opaque evidence only. |
| 8.5 Tool definitions, calls, and results | §§13.14.1-13.14.2 | N — tools are inert history; pairing and pending-action checks remain. |
| 8.6 Usage and accounting | §§13.14.1-13.14.2 | N — source usage never becomes target accounting. |
| 8.7 Compaction and context limits | §§13.14.1-13.14.2 | N — deterministic priority and explicit loss remain. |
| 8.8 Subagents and branching | §§13.14.1-13.14.2 | N — preserve the DAG or disclose semantic/summarized flattening. |
| 8.9 Attachments and large outputs | §§10.2, 13.14.1-13.14.2, 16.3 | R/N — AX blobs and path safety are reused. |
| 8.10 Native metadata and derived indexes | §§7.5, 10.5-10.6 | R/S — indexes are rebuilt transactionally, never copied wholesale. |
| 9. Migration Checkpoints and Lineage | §§13.14.2-13.14.3 | N — machine/visible checkpoint and receipt chain are AX-owned. |
| 9.1 Purpose | §13.14.2 | N — machine-readable and visible low-authority context retained. |
| 9.2 Canonical Migration Checkpoint | §13.14.2 | N/S — locator and fidelity-basis fields avoid cycles. |
| 9.3 Visible checkpoint projection | §§13.14.2, 16.4 | N — typed escaped user context replaces synthetic assistant output. |
| 9.4 Lineage chain | §§13.14.2-13.14.3 | N — receipt hash chain is descriptive and non-authoritative. |
| 9.5 Idempotency | §§7.8, 13.13-13.14 | R/N — stable request digest yields one target, checkpoint, and receipt. |
| 10. Transaction and Validation Contracts | §§10.5-10.6, 13.13-13.14.4 | R/N/S — AX outer materialization owns target lifecycle and recovery. |
| 10.1 Transaction states | §§10.6, 13.14.4 | N/S — Journal 3 adds explicit published/finalizing clone facts. |
| 10.2 Prepare | §§10.5-10.6, 13.14 | R — authority-scoped staging and predecessor capture are reused. |
| 10.3 Read-back validation | §§7.8, 13.14.2, 13.14.4 | N — separate staged/live Clone Read-Back Evidence Manifests; neither is a provider Transfer Manifest. |
| 10.4 Source race check | §§13.14.1, 13.14.4 | R/N — retained and repeated after target publication. |
| 10.5 Publish and finalize | §§5.4, 10.6, 13.14 | R/N — Provider commit is followed by live validation and AX Checkpoint closure. |
| 10.6 Resume validation | §§13.14.4-13.14.5, 19.3 | R/N — plan validation is runtime evidence; native smoke is a signed release gate. |
| 10.7 Rollback and recovery | §§10.6, 13.13-13.14 | R/S — AX's three exhaustive recovery outcomes replace any fourth orphan state. |
| 11. End-to-End Clone Procedure | §§13.13-13.14 | N — all sixteen phases map to the normative flow and `CR-CLONE-01..16`. |
| 11.1 Controller versus adapter responsibilities | §§3.1, 7.8, 13.14.1-13.14.5 | R/N — core owns policy/attestation; adapter owns native semantics. |
| 11.2 Continue while source is active | §§7.8, 13.14.1 | R — only immutable snapshot or proven prefix qualifies; size-only copying does not. |
| 11.3 Multiple hops | §§13.14.2-13.14.3 | N — richest ancestor evidence and prior receipt are retained. |
| 12. Initial Environment Profiles | §§13.14.5, 19.3, Appendix B | S — exact tuple evidence replaces blanket product profiles. |
| 12.1 Codex source capture | §§13.14.1, 13.14.5, 19.3 | R/N — fixture-gated facts and exclusions remain. |
| 12.2 Codex target materialization | §§13.14.2, 13.14.4-13.14.5 | R/N — official import/native writer is measured by the common gates. |
| 12.3 Claude Code source capture | §§13.14.1, 13.14.5, 19.3 | R/N — fixture-gated JSONL/sidechain capture and exclusions remain. |
| 12.4 Claude Code target materialization | §§13.14.2, 13.14.4-13.14.5 | R/N — native writer or labeled context fallback only. |
| 12.5 Initial direction requirements | §§19.3-19.4 | N/S — architecture requires both directions; release admission remains tuple-specific. |
| 12.5 Claude Code → Codex | §§13.14.5, 19.3-19.4 | N — independently admitted source-reader/target-writer tuple. |
| 12.5 Codex → Claude Code | §§13.14.5, 19.3-19.4 | N — independently admitted source-reader/target-writer tuple. |
| 12.6 Minimum canonical tool mappings | §13.14.1 | N — interpretation aid only, never target authorization. |
| 12.7 Supported-tuple registry | §§13.14.5, 19.3; compatibility artifacts | N/S — signed exact-tuple registry and revocation replace prose support claims. |
| 13. CLI and Operator Experience | §§14.1-14.3 | N/S — final hierarchy is `ax session clone`. |
| 13.1 Required commands | §14.1 | N/S — eight closed leaves; `plan` is sole no-write surface and `run --dry-run` is invalid. |
| 13.2 Plan output | §§14.2-14.3 | N — registered plan/report result with predicted loss, security findings, and write set. |
| 13.3 Successful clone output | §§14.2-14.3 | N — three disjoint CLI Result 2.0.0 run outcomes. |
| 13.4 Interactive warnings | §14.2 | R/N — structured mode never prompts; force cannot bypass gates. |
| 14. Errors and Exit Semantics | §§15.1-15.3 | R/N — AX exits are reused and Structured Error 1.1 adds closed clone errors. |
| 15. Security and Privacy | §§16.1-16.6 | R/N — AX security boundary controls clone-specific evidence handling. |
| 15.1 Threat model | §16.1 | R — session data remains untrusted within the trusted host mesh. |
| 15.2 Filesystem and process isolation | §§7.8, 16.3-16.4 | R — AX path, process, and authority rules control. |
| 15.3 Credentials and authority | §§13.14.2, 16.2 | R/N — control credentials remain excluded; transcript evidence follows explicit policy. |
| 15.4 Prompt-injection boundaries | §§13.14.2, 16.4 | R/N — imported content never becomes controller instruction. |
| 15.5 Plugin trust | §§7.1, 7.8 | R/S — same executable trust digest; network remains denied unless declared. |
| 15.6 Integrity and authenticity | §§1.6, 10.2, 13.14.1-13.14.5 | R/N — AX digest rules plus signed tuple registry. |
| 15.7 Data lifecycle | §§13.14.1-13.14.3, 18.4 | R/N — raw evidence retained; deletion is explicit; source cleanup is never implicit. |
| 16. Compatibility and Versioning | §§17.1-17.4 | R/N — AX SemVer and migration rules own every clone contract. |
| 16.1 Contract versioning | §17.1 | R/N — exact independently versioned registry entries apply. |
| 16.2 Native format gates | §§13.14.5, 19.3 | N/S — unknown source is archive-only; unknown target is disabled. |
| 16.3 Adapter downgrade and revocation | §§13.14.5, 17.2-17.4 | N — signed revocation disables writes while read/rollback evidence remains. |
| 16.4 Determinism | §§1.6, 13.14.1-13.14.4 | R/N — fresh inputs are explicit; normalization and selection remain deterministic. |
| 17. Observability | §§18.1-18.4 | R/N — Observation Event is reused and its closed required-event list is extended. |
| 18. Conformance and Test Requirements | §§19.3-19.4, Appendix D | R/N — AX acceptance suites and fixture catalog own all gates. |
| 18.1 Test layers | §§19.3-19.4, Appendix D | N — protocol, raw, golden, read-back, fault, security, and native layers retained. |
| 18.2 Required fixture corpus | Appendix D | N — synthetic/sanitized corpus is retained in the AX fixture catalog. |
| 18.3 Fidelity assertions | §19.3, Appendix D | N — total item-level reconciliation is release evidence. |
| 18.4 Semantic marker test | §§19.3-19.4 | N — bounded markers and native smoke remain distinct evidence. |
| 18.5 Initial acceptance matrix | §§13.14.5, 19.3-19.4 | S — exact directional tuples fail closed until signed evidence passes. |
| 19. Integration with Agent Session Manager (AX) | §§1.5, 5, 7.8, 13.14.1-13.14.5 | N/S — integration choices are now resolved in the normative AX contract. |
| 19.1 Reused AX contracts | §§1.6, 5.4, 7.5, 10.2-10.6, 15.1, 16 | R — reused directly rather than duplicated. |
| 19.2 New AX contract family | §§1.5, 7.8, 13.14.1-13.14.5 | N/S — companion protocol selected; Provider major 3 rejected. |
| 19.3 AX logical session ownership | §§5.1, 13.14 | N — new logical/native IDs; immutable source binding. |
| 19.4 Session Record evolution | §5.1 | N/S — tagged Session Record 2 provenance; final facts move to events and receipt. |
| 19.5 AX events and audit | §§5.2, 18.2 | N — closed clone Session Event variants and observation events added. |
| 19.6 AX CLI mapping | §14.1 | N/S — `ax session clone` selected; no alias. |
| 19.7 Ownership and move semantics | §§13.14, 16.6 | R — clone never transfers or stops source; move remains a future compound flow. |
| 19.8 Task-board and external orchestration | §§5.1, 9, 16 | R/N — opaque artifacts may be captured, but authority never transfers. |
| 20. Delivery Phases | §19.1 | S — implementation sequencing is folded into AX implementation phases. |
| Phase 0 — Schemas and fixtures | §19.1, Appendix D | N — schema, fixture, registry, and harness phase. |
| Phase 1 — Read and archive | §19.1 | N — read/archive/normalize with target writes disabled. |
| Phase 2 — Claude Code → Codex | §§19.1, 19.3 | N — enabled only for accepted exact tuples. |
| Phase 3 — Codex → Claude Code | §§19.1, 19.3 | N — accepted exact tuple or honest disabled fallback. |
| Phase 4 — AX merge | AX v0.3.0 | N — contracts, provenance, events, CLI, validation, and docs merged. |
| Phase 5 — Ecosystem | §19.1 | S — same-environment fast paths, SDKs, and new environments remain future work. |
| Appendix A. Prior-Art Audit | Appendix C | E — evidence retained without normative dependency. |
| Appendix B. Example Clone | §14.3 | S — examples use registered `ax session clone plan/run` commands and IDs. |
| Appendix C. Schema Publication Layout | §20.1-20.2, Appendix D | S — AX repository registry and fixture catalog replace standalone paths. |
| Appendix D. Primary References | Appendix C | E — claims remain evidence-gated; references do not become normative. |
| Appendix E. Explicitly Deferred Editorial Decisions | §§1.5, 5.1, 7.8, 13.14.5, 14.1 | S — all four decisions are closed below; no merge decision remains deferred. |

## Resolved deferred decisions

### Directory section mapping

Each row covers the named standalone section and all of its subsections. The
accepted mapping authority is
`.research/260827_session-directory-merge-audit.md` and board outcome
`TASK-260827-32hife_session-directory-merge-audit.md`.

| Standalone directory section | AX v0.4.2 target | Disposition and migration result |
| --- | --- | --- |
| 1. Conformance, scope, and product boundary | §§1–2, 19 | N/S — product outcomes are integrated and all 45 merge invariants are individually registered as `DIR-INV-01..45`. |
| 2. Architecture and responsibility boundaries | §§3.1, 7.9, 10.8, 11.8 | R/N — local-first topology is retained; Directory Node is a companion façade backed by the same environment implementation and gains no separate Provider/workspace authority. |
| 3. Contract registry and common data rules | §§1.5–1.6 | R/N — AX canonicalization is reused and all independently consumed directory contracts receive exact closed versions. |
| 4. Directory domain model | §§2.1, 5.1, 10.8 | N/S — observations, lineage, annotations, profiles, jobs, plans, receipts, and queries become AX records; derived entries remain non-authoritative. |
| 5. Directory node and adapter contracts | §§7.9, 15 | N/S — dual-stack Directory Node 1/2 is separately negotiated; Provider 2 and Session Adapter 1 stay authoritative for their existing boundaries. |
| 6. Catalog convergence, freshness, and search indexing | §§10.8, 11.8, 12 | R/N — catalog/index remains rebuildable; sanitized immutable records use AX anti-entropy and exact source-local freshness. |
| 7. Enrichment profiles, jobs, and annotations | §§10.8, 16.7 | N — exact-head, immutable receipt, supersession-DAG, model policy, and isolated-worker rules are integrated. |
| 8. Human and agent query interfaces | §§10.8, 14.5 | N/S — one typed query engine replaces standalone textual shapes; projection, batching, pagination, scoped grep, schema discovery, and guarded mutations are closed. |
| 9. Continuation planning and routing | §§10.8, 13.15 | N — pure content-addressed plans, exact route/outcome registries, visibility, expiry, and revalidation are integrated. |
| 10. Continuation execution | §§5.2, 10.8, 13.15 | R/N/S — immutable receipts drive operation state while AX/cloning transactions retain all mutation authority. |
| 11. Human TUI and CLI | §14.5 | N/S — merged into `ax sessions`, CLI Result 3, query commands, four-region TUI, and shared planner/executor. |
| 12. Mesh catalog and convergence | §§11.4, 11.8, 17.5 | R/N — RPC 3 adds one disjoint `directory_record` namespace and remains dual-stack with RPC 2; no transcript/index server is introduced. |
| 13. Security and privacy | §§16.1–16.7 | R/N — AX trust/path/process rules are reused and directory disclosure, enrichment, query, log, metric, and terminal exclusions are added. |
| 14. Errors and exit semantics | §15.3 | N — Structured Error 1.2 adds exact directory codes and bindings without changing older envelopes. |
| 15. Compatibility and versioning | §§1.5, 17.5 | N/S — v0.4.2 preserves immutable Request 1 and introduces Request/Protocol 2 for the AX platform vocabulary; the entire v0.3 cloning/workspace/transfer/materialization authority is reused unchanged. |
| 16. Observability and operation | §§18.1–18.4 | R/N — the open Observation Event 1 grammar is reused and directory lifecycle, doctor, metric, and audit requirements are added. |
| 17. Conformance and test requirements | §§19.1–19.5, Appendix D | N/S — AX production-path and focused-negative fixture gates replace the standalone harness layout. |
| 18. AX integration and merge contract | §§1.5, 5, 7.9, 10.8, 11.8, 13.15, 17.5 | N/S — all merge decisions are closed; duplicate Provider/workspace/blob/transfer/materialization/lease/terminal/cloning authority is forbidden. |
| 19. Delivery phases | §19.1 | S — standalone delivery sequencing is folded into AX implementation phases. |
| Appendix A. Prior-art audit | Appendix C | E — evidence only; no runtime dependency. |
| Appendix B. Example directory and continuation flow | §§10.8, 13.15, 14.5, Appendix D | S — registered AX records/results/fixtures replace standalone examples. |
| Appendix C. Schema publication layout | §§1.5, 3.2, 17.5, Appendix D | S — AX registry, storage, compatibility, and fixture authorities replace standalone paths. |
| Appendix D. Requirement traceability | SPEC Appendix A.10 and `AC-DIR-*` | N/S — every requirement is mapped into normative AX sections and acceptance gates. |

### Cloning merge decisions

| Deferred question | AX v0.3.0 decision | Rationale and normative destination |
| --- | --- | --- |
| Final CLI namespace | `ax session clone`; no `ax clone` alias | Keeps the feature inside the existing session domain and permits closed plan/run results; [§14.1](SPEC.md#141-command-surface). |
| Companion Session Adapter or Provider major | Keep `urn:ax:protocol:session-adapter` `1.0.0` in the same trusted provider executable; Provider remains `2.0.0` | Separates semantic conversion from the already evidenced native transaction/write boundary; [§7.8](SPEC.md#78-companion-session-adapter-protocol). |
| Tagged derivation provenance | Session Record `2.0.0` uses closed `origin`, `same_provider_fork`, and `cross_environment_clone` variants; v0.3 emits major 2 only for clone targets | Avoids inventing final native facts before materialization and avoids silently changing Provider 2 launch/fork records; [§5.1](SPEC.md#51-session-record). |
| Tuple registry publication and revocation | Release artifacts `compatibility/supported-environment-tuples-v1.json` and `.sshsig`; AX release authority accepts/revokes, local policy may only deny more | Makes target-write admission monotonic, signed, exact, and non-self-authorizing; [§13.14.5](SPEC.md#13145-events-state-and-tuple-admission). |

None of these decisions weakens the adapter boundary, item-level fidelity accounting, stable-snapshot proof, rollback-retaining transaction, independent read-back, target Checkpoint closure, or lineage.

## Supersession register

This register identifies standalone-only rules that must not remain as normative dependencies. The AX references contain the replacement contracts.

| # | Standalone-only rule | AX replacement and rationale |
| ---: | --- | --- |
| 1 | AX `v0.2.0` merge target | `v0.3.0` release over immutable `v0.2.1` baseline; §20. |
| 2 | Separate `ax-session-adapter-<id>` executable | Same trusted `ax-provider-<id>` serves Session Adapter 1.0; §7.8. |
| 3 | Adapter-owned materialize operations | Provider 2 transactions plus AX Plan/Journal own native writes; §§7.5, 10.5-10.6. |
| 4 | Standalone project capsule | AX Checkpoint and Workspace Transfer Manifest references; §§5.4, 10.4, 12. |
| 5 | Predicted final Fidelity Report digest | `fidelity_basis_digest`; final report depends on read-back; §13.14.2. |
| 6 | Final target native identity/receipt in Session Record at creation | Tagged pre-materialization derivation plus later Provider Identity/events/receipt; §§5.1-5.2, 13.14.2. |
| 7 | Orphaned unopened target as a fourth recovery outcome | Existing `recoverable_parked_state` or durable rollback; §§13.13-13.14. |
| 8 | Standalone CLI spelling and shared `--dry-run` | `ax session clone`; dedicated `plan`; `run --dry-run` invalid; §14.1. |
| 9 | Standalone schema publication directories | AX contract registry, repository layout, and fixture catalog; §1.5, §20, Appendix D. |
| 10 | Blanket environment/product support | Signed exact tuple admission and revocation; §13.14.5, §19.3. |
| 11 | Provider commit or Migration Checkpoint alone establishes resumability | Ordinary target AX Checkpoint and event closure are also required; §§5.4, 13.14. |
| 12 | Plan 1 mandatory source Checkpoint/lease basis | Plan 2 `source_basis` union supports external-native sources without placeholder AX authority; §10.5. |
| 13 | One nullable bundle manifest shape | Branch-exclusive archive/target generation chain and stage-selected content union; §13.14.3. |
| 14 | Manifest-declared executable trust | Host-observed execution binding plus Provider/Session Adapter manifests and probes; §§7.1, 7.8. |
| 15 | Journal 2 inherited for clone | Clone-only non-inheriting Journal 3 and Journal Source Basis; §10.6. |
| 16 | Executable provenance inside `EnvironmentTuple` | Six-member tuple plus separate supported-key/journal execution bindings; §§7.8, 13.14.4-13.14.5. |
| 17 | Pre-target or staged failures as target Session Events | Structured Error, Observation Event, and Journal evidence; §§5.2, 15, 18. |
| 18 | Nullable Session Adapter responses | Disjoint exact success and failure envelopes; §7.8. |
| 19 | `adapter_id` as wire identity | `provider_id` plus `environment_id`; executable digest remains a host-observed binding; §§7.8, 13.14.5. |
| 20 | Archive-only as a target-bearing projection | Targetless archive terminal only; target chains require complete target facts; §13.14.3. |
| 21 | Session Record 2 as blanket Provider 2 replacement | Major 2 is clone-target-only in v0.3; Provider 2 launch/fork retain major 1; §§5.1, 7.5. |
| 22 | Generic source/project/evidence manifest roles | Registered Raw, Projected, and Read-Back Evidence Manifests; Transfer Manifest remains unchanged; §§10.4, 13.14.1-13.14.2. |
| 23 | Source-only capability or locally generated evidence authorizes target writing | Exact signed target-writer tuple with independent fixture/smoke/binding evidence; §§13.14.5, 19.3. |

## Dependency closure

The standalone cloning document is retained only as a historical input
identified by its digest. No AX implementation or release process needs it to
interpret `SPEC.md`. The standalone directory document is retained under the
same historical-input rule and is likewise not a runtime or release-process
dependency. All normative contracts are registered in
[SPEC.md §1.5](SPEC.md#15-normative-contract-registry). Cloning rules live in
[§7.8](SPEC.md#78-companion-session-adapter-protocol),
[§13.14](SPEC.md#1314-cross-environment-clone), and Appendix D;
directory rules live in [§7.9](SPEC.md#79-companion-directory-node-protocol),
[§10.8](SPEC.md#108-directory-records-lineage-enrichment-query-and-continuation),
[§11.8](SPEC.md#118-mesh-rpc-300-directory-replication),
[§13.15](SPEC.md#1315-directory-continuation-planning-and-execution),
[§14.5](SPEC.md#145-session-directory-cli-result-3-query-and-tui), and Appendix D.
