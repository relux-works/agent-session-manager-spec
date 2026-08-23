#!/bin/bash
set -euo pipefail

# Single public, repository-only validation command for the whole specification package.
# Works in a clean public checkout where .temp/ and .task-board/ do not exist.
# Never overwrites committed artifacts before freshness comparison.

echo "=== ax v0.2.0 specification validation ==="
echo "Repository: relux-works/agent-session-manager-spec, branch: main, release: v0.2.0"
echo ""

echo "[1/3] Validating specification contracts, metadata, links, and examples..."
./scripts/validate_spec.py
echo "  -> contracts OK (exit 0)"
echo ""

echo "[2/3] Validating Structurizr workspace and exporting C4 to temporary directory..."
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "  Temp dir: $TEMP_DIR"
echo "  Validating workspace..."
structurizr-cli validate -w diagrams/c4/workspace.dsl
echo "  -> workspace validate OK"

mkdir -p "$TEMP_DIR/c4"
echo "  Exporting C4 to PlantUML..."
structurizr-cli export -w diagrams/c4/workspace.dsl -format plantuml -output "$TEMP_DIR/c4"
echo "  -> export OK"

mkdir -p "$TEMP_DIR/artefacts"

echo "  Rendering generated C4 PlantUML to SVG..."
if ls "$TEMP_DIR/c4/"*.puml 1>/dev/null 2>&1; then
  plantuml -tsvg "$TEMP_DIR/c4/"*.puml -o "$TEMP_DIR/artefacts"
  echo "  -> C4 SVG render OK"
else
  echo "ERROR: No C4 PlantUML files exported to $TEMP_DIR/c4"
  exit 1
fi

# Handwritten PlantUML
if ls diagrams/plantuml/*.puml 1>/dev/null 2>&1; then
  mkdir -p "$TEMP_DIR/plantuml"
  cp diagrams/plantuml/*.puml "$TEMP_DIR/plantuml/"
  echo "  Rendering handwritten PlantUML to SVG..."
  plantuml -tsvg "$TEMP_DIR/plantuml/"*.puml -o "$TEMP_DIR/artefacts"
  echo "  -> PlantUML SVG render OK"
fi

echo ""
echo "[3/3] Checking committed artifact freshness (set + byte comparison)..."
echo "  Never overwriting committed artifacts; comparing temp export against committed files."

# Compare exact file sets for generated .puml (C4 intermediaries)
echo "  Checking C4 PlantUML file sets..."
COMMITTED_PUML_DIR="diagrams/c4"
GENERATED_PUML_DIR="$TEMP_DIR/c4"
# List only structurizr-*.puml intermediaries (generated)
committed_pumls=$(mktemp)
generated_pumls=$(mktemp)
trap 'rm -rf "$TEMP_DIR" "$committed_pumls" "$generated_pumls"' EXIT
ls -1 "$COMMITTED_PUML_DIR"/structurizr-*.puml 2>/dev/null | xargs -I{} basename {} | sort > "$committed_pumls" || true
ls -1 "$GENERATED_PUML_DIR"/*.puml 2>/dev/null | xargs -I{} basename {} | sort > "$generated_pumls" || true
if ! diff -u "$committed_pumls" "$generated_pumls"; then
  echo "ERROR: Committed C4 PlantUML file set differs from generated set."
  echo "  committed: $(cat "$committed_pumls" | tr '\n' ' ')"
  echo "  generated: $(cat "$generated_pumls" | tr '\n' ' ')"
  echo "  Extra or missing files detected — commit must exactly match export."
  exit 1
fi
echo "  -> C4 PlantUML file sets match (4 files)"

echo "  Checking C4 PlantUML byte freshness..."
for f in "$GENERATED_PUML_DIR"/*.puml; do
  base=$(basename "$f")
  if ! diff -u "$COMMITTED_PUML_DIR/$base" "$f"; then
    echo "ERROR: Committed C4 PlantUML $base is stale (bytes differ from export)."
    exit 1
  fi
done
echo "  -> C4 PlantUML bytes fresh"

# Compare exact SVG file sets
echo "  Checking SVG file sets..."
committed_svgs=$(mktemp)
generated_svgs=$(mktemp)
trap 'rm -rf "$TEMP_DIR" "$committed_pumls" "$generated_pumls" "$committed_svgs" "$generated_svgs"' EXIT
ls -1 diagrams/artefacts/*.svg 2>/dev/null | xargs -I{} basename {} | sort > "$committed_svgs" || true
ls -1 "$TEMP_DIR/artefacts"/*.svg 2>/dev/null | xargs -I{} basename {} | sort > "$generated_svgs" || true
if ! diff -u "$committed_svgs" "$generated_svgs"; then
  echo "ERROR: Committed SVG file set differs from generated set."
  echo "  committed: $(cat "$committed_svgs" | tr '\n' ' ')"
  echo "  generated: $(cat "$generated_svgs" | tr '\n' ' ')"
  echo "  Extra or missing SVGs detected."
  exit 1
fi
echo "  -> SVG file sets match (7 files)"

echo "  Checking SVG release-byte integrity and cross-platform source freshness..."
for f in "$TEMP_DIR/artefacts"/*.svg; do
  base=$(basename "$f")
  if ! ./scripts/validate_spec.py --compare-svg "diagrams/artefacts/$base" "$f"; then
    echo "ERROR: Committed SVG $base is stale or its release bytes changed."
    exit 1
  fi
done
echo "  -> SVG release bytes intact; embedded sources fresh across renderer platforms"

echo ""
echo "Validation successful: all contracts, diagrams, and publication artifacts are fresh."
