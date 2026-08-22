# Contributing to the Agent Session Manager specification

This guide is for contributors editing the `v0.1.0` specification in `relux-works/agent-session-manager-spec` (public, MIT, default branch `main`). It summarizes and links to the normative rules in [SPEC.md](SPEC.md) — it does not create a second contract. When this guide and [SPEC.md](SPEC.md) disagree, [SPEC.md](SPEC.md) wins.

## Scope and publication target

The repository is **specification only** in `v0.1.0`. It does not contain an `ax` product binary, and publishing the spec does not claim that any future product acceptance matrix has passed. See [SPEC.md §1.5](SPEC.md#15-normative-contract-registry), [§19.5](SPEC.md#195-ax-implementation-release-acceptance-rule), and [§20](SPEC.md#20-specification-publication-and-governance).

The first specification release is `v0.1.0`. Every document, metadata file, and tag in that release must say `v0.1.0` consistently — see [Signing, release, and attribution](#signing-release-and-attribution).

## Spec-change workflow

### 1 — Before editing

- Read the settled product and architecture decisions (attached to `TASK-260819-1h306n` and summarized in [SPEC.md §1.4](SPEC.md#14-source-authority-and-evidence) and [Appendix A.1](SPEC.md#a1-settled-decision-traceability)). Preserve those decisions unless a contradiction makes implementation impossible; record any necessary refinement explicitly.
- Read the accepted Muse and Antigravity evidence report at [`.research/260819_muse-antigravity-native-store-contracts.md`](.research/260819_muse-antigravity-native-store-contracts.md). Its retained unknowns must remain `unknown` or `unsupported` in `v0.1.0`.
- Check [Appendix B](SPEC.md#appendix-b-explicit-provider-version-gates) — the only intentionally unsettled facts. Do not invent parity for a gated cell.

### 2 — Making changes

- Edit `SPEC.md` as the single normative source. `README.md` and `CONTRIBUTING.md` summarize and link to `SPEC.md`; they must not duplicate or weaken a requirement.
- Keep the five-entry environment-override registry (`AX_CONFIG`, `AX_DATA_DIR`, `AX_STATE_DIR`, `AX_CACHE_DIR`, `AX_RUNTIME_DIR`) and the five-row path-precedence rule intact. See [SPEC.md §3.2](SPEC.md#32-platform-paths) and [§6.1](SPEC.md#61-loading-and-precedence).
- Keep the exact five-variable override table, the platform-default paths table, and the closing rules for every contract's `extensions` map (reverse-DNS keys only, closed top-level objects). See [SPEC.md §1.6](SPEC.md#16-common-data-rules).
- Do not add default payload encryption, do not auto-authorize Tailscale-discovered peers, do not replicate credentials/secrets/PIDs/sockets/locks/live SQLite, and do not claim a `tmux` backend on native Windows. See [§6.3](SPEC.md#63-field-constraints), [§11.1](SPEC.md#111-transport-and-peer-authentication), [§16](SPEC.md#16-security-and-threat-boundary), and [§4.3](SPEC.md#43-native-windows-backend).
- Do not collapse WSL2 and native Windows into one provider/platform row. See [§8.4](SPEC.md#84-providerplatform-matrix).

### 3 — Traceability

Every spec change must remain traceable:

- Map the edited sections to the settled-decision input that authorizes them (see [Appendix A.1](SPEC.md#a1-settled-decision-traceability)).
- If the change affects a story or task acceptance criterion, update the corresponding row in [Appendix A.2-A.3](SPEC.md#a2-story-acceptance-traceability).
- If closing a reviewer finding, add or update the row in [Appendix A.4-A.7](SPEC.md#a4-second-review-closure-traceability) rather than leaving the finding silently resolved.
- Keep the normative contract registry in [§1.5](SPEC.md#15-normative-contract-registry) and the fixture catalog in [Appendix D](SPEC.md#appendix-d-normative-contract-fixture-catalog) consistent with the edit — a new field, enum value, or tagged-union variant requires a fixture update there.

### 4 — Review

All changes require an independent reviewer acceptance before publication. The `to-review` board status means the author's work is handed off to review, not that it is accepted. See the task-board workflow and [SPEC.md §20.2](SPEC.md#202-publication-gate) items 8-10.

## Diagrams

### Sources

- **C4**: `diagrams/c4/workspace.dsl` (includes `model.dsl`, `views.dsl`, `relationships.dsl`, `styles.dsl`). The required views are `SystemContext` and `ContainerContext` — see [SPEC.md §3.1](SPEC.md#31-required-components). The exported intermediaries `diagrams/c4/structurizr-*.puml` are generated from `workspace.dsl` and are not hand-edited.
- **PlantUML**: `diagrams/plantuml/*.puml` — the three scoped diagrams for `v0.1.0` are `takeover.puml`, `session_state.puml`, and `mesh_deployment.puml`. Together they cover the ownership state machine, the takeover/force-takeover/fork flows, and the allowlisted mesh/terminal-backend deployment required by [SPEC.md §3](SPEC.md#3-architecture-and-durable-local-layout) and [§13](SPEC.md#13-end-to-end-lifecycle-flows). Do not claim a broader per-flow diagram set for `v0.1.0`; see the committed artefacts under `diagrams/artefacts/`.

Committed `*.puml` and `*.dsl` sources are part of the spec artifact and must match [§3](SPEC.md#3-architecture-and-durable-local-layout) and [§13](SPEC.md#13-end-to-end-lifecycle-flows) semantically.

### Render rules

- Render C4 via Structurizr and PlantUML via the PlantUML renderer. The rendered SVGs are committed under `diagrams/artefacts/` for review — see acceptance case `AC-DIAG-001` in [SPEC.md §19.4](SPEC.md#194-end-to-end-acceptance-cases). The expected committed SVGs for `v0.1.0` are `takeover.svg`, `session_state.svg`, `mesh_deployment.svg`, plus the four `structurizr-*.svg` files exported from the C4 model.
- Committed SVGs must be visually inspected and must match [§3](SPEC.md#3-architecture-and-durable-local-layout) and [§13](SPEC.md#13-end-to-end-lifecycle-flows). A source change without a re-rendered and re-inspected SVG is incomplete.
- The render step must use the same sources that are committed — do not render from a stale or patched copy. Record the exact render commands and tool versions in the PR/task evidence (see [Validation](#validation)).

Validated commands (run from the repository root; versions after `TASK-260819-37heok` rework):

```shell
# 1 — Validate Structurizr workspace (standalone, retain exit code)
structurizr-cli validate -w diagrams/c4/workspace.dsl
echo "exit code: $?"

# 2 — Export C4 to PlantUML intermediaries (produces diagrams/c4/structurizr-*.puml)
structurizr-cli export -w diagrams/c4/workspace.dsl -format plantuml -output diagrams/c4
echo "exit code: $?"

# 3a — Render C4 SVGs (from repository root; artefacts lands in diagrams/artefacts/)
plantuml -tsvg diagrams/c4/*.puml -o artefacts
# or, when running from diagrams/c4:
# plantuml -tsvg *.puml -o ../artefacts

# 3b — Render PlantUML SVGs
plantuml -tsvg diagrams/plantuml/*.puml -o artefacts
echo "exit code: $?"
```

The single public whole-package entry point that also checks freshness and contracts is:

```shell
./run_validation.sh
echo "exit code: $?"
```

The exact flags are `validate -w`, `export -w ... -format plantuml -output`, and `plantuml -tsvg`. There is no `./diagrams/render.sh` helper — use `./run_validation.sh` or the explicit commands above. Run each command as a standalone process and retain its real exit code. See [README.md](README.md#tools-validation-and-artifacts) and [diagrams/README.md](diagrams/README.md) for the matching summary.

## Validation

### What the publication validator does and does not do

The accepted validation entry point checks spec structure, contract fixtures, links, JCS identity and numeric-boundary vectors, diagram presence, publication metadata, and the frozen `v0.1.0` content baseline for the five public claim documents. The baseline uses SHA-256 over UTF-8 text with line endings normalized to LF, making the check stable across supported checkout platforms. It is a bounded release-integrity control, not general natural-language theorem proving; for a future specification revision, update the digest map in `scripts/validate_spec.py` only after the changed prose and expected-red coverage have been reviewed. The validator **must not** require an `ax` binary, provider runtime, platform lane, or any [§19](SPEC.md#19-ax-implementation-conformance-and-product-release) product-conformance result. Any validator that tries to execute product acceptance cases fails publication case `SPEC-PUB-001`. See [SPEC.md §20.2](SPEC.md#202-publication-gate).

### Exact commands

Run each validation as a standalone process and retain its real exit code. Do not pipe through `tee` without `pipefail`.

```shell
# 1 — Full repository validation (specification contracts, diagrams freshness, structure)
./run_validation.sh
echo "exit code: $?"

# 2 — Expected-red mutation suite (proves each failure class exits nonzero with actionable diagnostic)
./scripts/test_expected_red.sh
echo "exit code: $?"

# 3 — Board structure (local board data; not required in clean public checkout)
task-board validate
echo "exit code: $?"


# 5 — Link, whitespace, and file-reference sanity
rg --version
rg -n "SPEC\.md#|Appendix [A-D]" SPEC.md | head
git diff --check
echo "exit code: $?"
```

Expected: each validator exits `0` on a conforming checkout. The publication gate (see [Signing, release, and attribution](#signing-release-and-attribution)) also requires a fixture checkout verification that `SPEC-PUB-001` passes with no `ax` executable present. Diagram render is covered by `./run_validation.sh` (`structurizr-cli validate`, `structurizr-cli export`, `plantuml`), whose exact flags and artefact locations are defined in [Diagrams](#diagrams).

### Toolchain

Observed after `TASK-260819-37heok` rework:

| Command | Version |
| --- | --- |
| `rg --version` | `ripgrep 15.2.0` |
| `git --version` | `git version 2.50.1 (Apple Git-155)` |
| `python3 --version` | `Python 3.14.4` |
| `node --version` | `v25.6.1` |
| `task-board --version` | `0.24.3-17-g7ac2be8 (commit 7ac2be8)` |
| `java --version` | `OpenJDK 26.0.1` |
| `structurizr-cli version` | `structurizr-cli 2025.11.09`, `structurizr-java 5.0.2` |
| `plantuml -version` | `PlantUML 1.2026.6 / 6287b33` |

Provider binaries are not required. Keep link, command, metadata, and terminology consistent with [SPEC.md](SPEC.md) — especially `v0.1.0` naming, repository `relux-works/agent-session-manager-spec`, default branch `main`, and capability values `available`/`conditional`/`unsupported`/`unknown`.

## Compatibility and versioning

- Each contract in [§1.5](SPEC.md#15-normative-contract-registry) versions independently with SemVer. A major increment may break syntax/semantics and requires explicit negotiation/migration; a minor increment may add optional operations, enum values, or namespaced `extensions` fields but must preserve prior semantics; a patch clarifies constraints or fixes a validator defect. See [SPEC.md §17.1](SPEC.md#171-semantic-version-rules).
- Protocol peers choose the highest mutually supported minor within a common major and must not coerce a major. Provider protocol, task-board bridge, and Mesh RPC major `1` each bind Structured Error `1.0.0` explicitly — see [§15.1](SPEC.md#151-structured-error).
- A writer emits exactly the negotiated version. A reader rejects an unsupported major, accepts the same/lower minor, preserves unknown namespaced extensions byte-for-byte when forwarding immutable objects, rejects an unknown ownership/security enum, and may retain an unknown event as inert history without deriving state. An `enabled = true` capability is valid only for the exact negotiated contract and provider tuple. See [§17.2](SPEC.md#172-readerwriter-behavior).
- Immutable objects are never edited in place. A migration creates a new schema-versioned object that references the prior object in `extensions["works.relux.ax.migrated-from"]`, a closed object containing exactly `schema_id`, `schema_version`, and `object_id`. The writer validates the new object and atomically advances a local reference. Old objects remain for rollback until retention allows collection. Configuration migration requires `ax migrate config` for a major change and a backup + atomic write. The derived SQLite index may be rebuilt at any time and is never a migration source of truth. See [§17.3](SPEC.md#173-immutable-data-migration).
- Before upgrading, checkpoint locally owned sessions and run schema/plugin/task-board compatibility checks before auto-resume. A downgraded binary that cannot understand current records must enter read-only diagnostic mode and must not resume, transfer ownership, materialize, or write lower-version replacements. Provider upgrades invalidate prior tuple-specific acceptance until the adapter's declared version range and compatibility fixture cover the new version. See [§17.4](SPEC.md#174-upgrade-and-downgrade).

Specification releases use SemVer; independent schema/protocol versions remain as listed in [§1.5](SPEC.md#15-normative-contract-registry). See [§20](SPEC.md#20-specification-publication-and-governance).

## Signing, release, and attribution

### Publication gate

The full gate is normative in [SPEC.md §20.2](SPEC.md#202-publication-gate). In order:

1. Verify a clean checkout contains `SPEC.md`, `README.md`, `CONTRIBUTING.md`, diagram sources and rendered SVGs, `VERSION`, `CHANGELOG`, release notes, and `LICENSE` (MIT).
2. Run the accepted validation entry point as a standalone process and retain its real exit code.
3. Explicitly verify that the validator does not require an `ax` binary, provider runtime, platform lane, or any [§19](SPEC.md#19-ax-implementation-conformance-and-product-release) result.
4. Verify `VERSION`, document metadata, changelog, release notes, and tag all say `v0.1.0`.
5. Prepare the exact signed-commit command with author `Ivan Oparin <oparin@me.com>` and no AI trailer; hand it to the user for explicit review. Automation MUST NOT stage or commit before human approval.
6. Prepare the exact signed annotated `v0.1.0` tag command; hand it to the user for explicit review. Automation MUST NOT create the tag before human approval.
7. After the human creates the commit and tag, verify both signatures locally.
8. Hand the exact `git push` commands for `main` and the `v0.1.0` tag to the user; automation MUST NOT push before explicit human approval and only after accepted validation/review.
9. Verify the public repository, default branch, license, commit signature, tag signature, and release URL.
10. Attach publication evidence to the board.

No automation may publish, stage, commit, tag, or push before validation acceptance and explicit human review of every stage/commit/tag/push command. Automation MUST stop before those operations and hand the exact reviewed commands to the user. See [§20.2](SPEC.md#202-publication-gate) and `SPEC-PUB-001`.

### Signing

- **Author**: `Ivan Oparin <oparin@me.com>` — this is the commit author for the release commit. No AI `Co-Authored-By` trailer is included.
- **Signing key**: `~/.ssh/ivanopcode` (SSH signing key). Both the release commit and the annotated tag `v0.1.0` must be signed with this key. The repository's Git config must set `gpg.format ssh`, `user.signingkey ~/.ssh/ivanopcode`, `commit.gpgsign true`, and `tag.gpgsign true`.
- **Human commit gate**: Automation MUST NOT stage, commit, tag, or push. It MUST stop before those operations and hand the exact `git commit`, `git tag`, and `git push` commands to the user for explicit human execution.
- Verify locally after the human signs:

```shell
git log --show-signature -1
git tag --verify v0.1.0
```

### AI attribution policy

No commit message — including the release commit — may contain an AI `Co-Authored-By` trailer or other AI attribution trailer. The model is not a commit co-author. If an acknowledgement is explicitly requested, it MAY appear only in prose documentation outside commit metadata, clearly marked as non-commit attribution; it MUST NOT appear as a commit trailer. See [SPEC.md §20.1](SPEC.md#201-repository-and-release).

## Repository layout and file ownership

```
SPEC.md                         # normative contract — edit here
README.md                       # operator summary — links to SPEC, no second contract
CONTRIBUTING.md                 # this file
diagrams/c4/*.dsl               # C4 sources (Structurizr)
diagrams/c4/structurizr-*.puml  # generated C4 intermediaries (from workspace.dsl, not hand-edited)
diagrams/plantuml/*.puml        # PlantUML sources (takeover, session_state, mesh_deployment)
diagrams/artefacts/*.svg        # rendered SVGs (committed, visually inspected)
scripts/validate_spec.py        # public repository-only validator (contracts, links, matrices, examples, metadata, fences, license)
scripts/test_expected_red.sh    # expected-red mutation suite (proves both validator and whole-package entry point fail nonzero with actionable diagnostics)
run_validation.sh               # single public whole-package validation command (contracts + diagrams + freshness)
.github/workflows/validate.yml  # CI path with pinned documentation-tool versions (single command + expected-red)
diagrams/README.md              # diagram render quick-reference
.research/                      # required public provider evidence for the v0.1.0 specification package
.planning/                      # public planning and audit evidence

Local-only (not in clean checkout): .task-board/ (board data), task-board.config.json (board config)
```

Do not add a second normative spec file. Do not commit provider credentials, SSH private keys, environment secrets, live PIDs/sockets/locks, or derived SQLite files. See [SPEC.md §16.2](SPEC.md#162-mandatory-exclusions).

## Checklist for a spec PR

- [ ] Change is authorized by a settled decision or an explicit recorded refinement.
- [ ] `SPEC.md` is the only normative edit; `README.md`/`CONTRIBUTING.md` only summarize and link.
- [ ] Traceability rows in [Appendix A](SPEC.md#appendix-a-normative-traceability) updated.
- [ ] Contract registry and fixture catalog updated if a contract or variant changed.
- [ ] No unsupported capability claimed; no default-encryption claim added; WSL2 and native Windows remain distinct.
- [ ] Diagram sources re-rendered, SVGs committed, and visual inspection done.
- [ ] `./run_validation.sh` exits `0` as a standalone process.
- [ ] `task-board validate` exits `0`.
- [ ] Commit carries correct author `Ivan Oparin <oparin@me.com>`, is SSH-signed with `~/.ssh/ivanopcode`, contains no AI `Co-Authored-By` trailer, and was created only after explicit human review of the handed commands.
