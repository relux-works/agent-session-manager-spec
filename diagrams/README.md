# Architecture Diagrams

This directory contains the architecture diagrams rendered for Agent Session Manager (`ax`) v0.4.3. The C4 views integrate Directory and the minimal macOS Aqua terminal broker as bounded AX components; focused PlantUML views keep ownership/deployment, cloning, Directory component authority, source-local inventory/enrichment, and continuation execution separate and reviewable.

## Matching SPEC.md References

- **C4 System / Container**: `SPEC.md` Sections 3.1 (required components), 7.9 (Directory Node companion façade), 9.1 (task-board distinct boundary), 10.5-10.8 (materialization, records, Directory), and 13.14-13.15 (cloning and continuation)
- **Mesh Deployment**: `SPEC.md` Sections 3.2, 4.2/4.4, 11 (Mesh/RPC), 14, 16.2, 18 (allowlisted peers, split background/Aqua broker, dedicated tmux server, machine-local socket/auth state)
- **Session State**: `SPEC.md` Sections 13.1-13.10 (Logical Session Ownership, single active owner, explicit handoff/takeover/fork)
- **Takeover Sequence**: `SPEC.md` Sections 4.2 and 13.6-13.8 (destination broker/auth readiness, fenced source stop, ownership commit, runtime creation, takeover/fork)
- **Clone Components**: `SPEC.md` Sections 7.8 and 13.14.1-13.14.2 (companion Session Adapters, isolated Object Sinks, per-host stores, canonical projection, Provider-owned transactions)
- **Clone Transaction**: `SPEC.md` Sections 13.14.3-13.14.4 (G0-G4 bundle chain, staged/live validation, rollback retention, Provider commit, target Checkpoint, and lineage publication)
- **Directory Components**: `SPEC.md` Sections 3.1, 7.9, 10.8, and 16.7 (control plane, source-local node, isolated worker, derived index, immutable records, and existing AX/cloning authority)
- **Directory Inventory/Enrichment**: `SPEC.md` Sections 10.8 and 16.7 (bounded inventory, exact-head annotation jobs, stale-result receipts, sanitization, and allowed mesh records)
- **Directory Continuation**: `SPEC.md` Sections 10.8, 13.15, and 14.5 (selection, pure planning, exact revalidation, delegated AX/cloning effects, target-first move, and attach)

## Prerequisites and Versions

The following tool versions are required to ensure byte-reproducible renders:
- **Structurizr CLI**: 2025.11.09
- **Structurizr Java**: 5.0.2
- **PlantUML**: 1.2026.6 / 6287b33
- **Java**: 26.0.1

**Installation (macOS via Homebrew):**
```bash
brew install structurizr-cli plantuml
```

## Validation and Render Commands

All diagram validation and rendering is handled by the single repository entry point. Run from the project root:

```bash
./run_validation.sh
```

To validate and render all eight handwritten diagrams from the project root, use these exact commands. PlantUML resolves the relative output directory from `diagrams/plantuml/`, so `../artefacts` writes the canonical files under `diagrams/artefacts/`:

```bash
plantuml -checkonly diagrams/plantuml/*.puml

plantuml -tsvg diagrams/plantuml/*.puml -o ../artefacts
```

This single command:
1. Validates the C4 Structurizr workspace.
2. Exports C4 to PlantUML in a temporary directory.
3. Renders all SVGs (C4 and handwritten PlantUML) into the temporary directory.
4. Compares generated C4 `.puml` bytes exactly, checks every committed SVG against the v0.4.3 SHA-256 ledger, and compares embedded PlantUML source/version metadata with the fresh render. Font and Graphviz geometry may vary by platform without weakening committed-byte integrity or source freshness.

## Artifact Map

All paths below are root-relative. The rendered SVGs are stored in `diagrams/artefacts/`:

- `diagrams/artefacts/structurizr-SystemContext.svg`: C4 System Context view.
- `diagrams/artefacts/structurizr-ContainerContext.svg`: focused C4 Container
  view of AX-internal deployable units and actors; external systems remain in
  the System Context view so the container artifact stays bounded and readable.
- `diagrams/artefacts/mesh_deployment.svg`: Physical and network deployment boundaries.
- `diagrams/artefacts/session_state.svg`: Ownership and lifecycle state machine.
- `diagrams/artefacts/takeover.svg`: Detailed graceful and force takeover sequences.
- `diagrams/artefacts/cloning_components.svg`: AX-native cloning components, companion-adapter boundaries, per-host stores, isolated sinks, and Provider-owned target transaction authority.
- `diagrams/artefacts/cloning_transaction.svg`: Ordered capture, projection, staged/live validation, pre-commit Provider Transfer Manifest capture, rollback, Provider commit, target Checkpoint, and lineage publication flow.
- `diagrams/artefacts/session_directory_components.svg`: Directory client/control-plane/source-node boundaries and delegation to existing AX and cloning authority.
- `diagrams/artefacts/session_directory_enrichment.svg`: Source-local inventory, exact-head bounded enrichment, stale-job handling, and allowed mesh convergence.
- `diagrams/artefacts/session_directory_continuation.svg`: Pure planning, exact source/target revalidation, route selection, delegated execution, and terminal attach.

## Visual-Inspection Procedure

After rendering, visually inspect all SVGs to ensure:
1. **Readable Labels:** Text has high contrast against shapes/backgrounds and is legible at normal 100% zoom.
2. **Unclipped Content:** All nodes, lines, and notes fit within the view boundaries.
3. **One Clear Purpose:** Each diagram expresses only its scoped concern without visual clutter.
4. **Layout:** C4 views use top-to-bottom layout to prevent excessive width.
5. **Clone Semantics:** The component view has no shared native store or source×target converter matrix; the transaction view captures the ordinary Provider Transfer Manifest before G3/finalizing while rollback remains retained, commits Provider state before sealing the target Checkpoint, and publishes lineage last.
6. **Directory Authority:** The Directory views keep native stores and exact-head reads source-local, make SQLite/display text derived rather than authoritative, isolate enrichment, and delegate continuation effects to existing AX/cloning transactions.
7. **Arrow Direction:** Inventory and preview reads point toward the source-local adapter/store; immutable publication points toward record storage/mesh; continuation planning precedes confirmation/revalidation; target commit and evidence precede attach, and a move never releases the source first.
8. **macOS Realm:** Background control-plane arrows only contact an existing Aqua broker; the broker alone creates/attests the dedicated tmux server; takeover shows broker/auth readiness before ownership commit and runtime creation after commit.
