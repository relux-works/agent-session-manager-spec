# Architecture Diagrams

This directory contains the architecture diagrams rendered for Agent Session Manager (ax) v0.2.0 and retained unchanged as the architecture baseline for v0.2.1. Section 13.13 adds a crash/restart conformance gate over existing flows without changing diagram topology.

## Matching SPEC.md References

- **C4 System / Container**: `SPEC.md` Sections 3.1 (Required components), 9.1 (Task-board distinct boundary), 10.5-10.6 (Materialization/journal)
- **Mesh Deployment**: `SPEC.md` Sections 3.2, 11 (Mesh/RPC), 14, 18 (Allowlisted peers, SSH transport, no auto-authorization)
- **Session State**: `SPEC.md` Sections 13.1-13.10 (Logical Session Ownership, single active owner, explicit handoff/takeover/fork)
- **Takeover Sequence**: `SPEC.md` Sections 13.6-13.8 (Takeover/fork, Graceful takeover lease advance rules, destination validation, sync)

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

This single command:
1. Validates the C4 Structurizr workspace.
2. Exports C4 to PlantUML in a temporary directory.
3. Renders all SVGs (C4 and handwritten PlantUML) into the temporary directory.
4. Compares generated C4 `.puml` bytes exactly, checks every committed SVG against the unchanged v0.2.1 SHA-256 ledger, and compares embedded PlantUML source/version metadata with the fresh render. Font and Graphviz geometry may vary by platform without weakening committed-byte integrity or source freshness.

## Artifact Map

All paths below are root-relative. The rendered SVGs are stored in `diagrams/artefacts/`:

- `diagrams/artefacts/structurizr-SystemContext.svg`: C4 System Context view.
- `diagrams/artefacts/structurizr-ContainerContext.svg`: C4 Container view.
- `diagrams/artefacts/mesh_deployment.svg`: Physical and network deployment boundaries.
- `diagrams/artefacts/session_state.svg`: Ownership and lifecycle state machine.
- `diagrams/artefacts/takeover.svg`: Detailed graceful and force takeover sequences.

## Visual-Inspection Procedure

After rendering, visually inspect all SVGs to ensure:
1. **Readable Labels:** Text has high contrast against shapes/backgrounds and is legible at normal 100% zoom.
2. **Unclipped Content:** All nodes, lines, and notes fit within the view boundaries.
3. **One Clear Purpose:** Each diagram expresses only its scoped concern without visual clutter.
4. **Layout:** C4 views use top-to-bottom layout to prevent excessive width.
