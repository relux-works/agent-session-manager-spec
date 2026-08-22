#!/bin/bash
set -euo pipefail

echo "=== Expected-red mutation suite for v0.1.0 specification validation ==="
echo "Each mutation creates an isolated fixture copy, proves validator exits nonzero with actionable diagnostic,"
echo "and never mutates the working tree."
echo ""

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TEMP_ROOT"' EXIT

PASS=0
FAIL=0
TOTAL=0

expect_fail() {
  local label="$1"
  local should_contain="${2:-ERROR}"
  local fixture_dir="${3:-.}"
  local cmd="${4:-./scripts/validate_spec.py}"
  TOTAL=$((TOTAL+1))
  echo "  [$TOTAL] $label"
  set +e
  output=$(cd "$fixture_dir" && $cmd 2>&1)
  code=$?
  set -e
  if [ $code -eq 0 ]; then
    echo "    FAIL: expected nonzero exit, got 0"
    echo "    output: $output" | head -n 20
    FAIL=$((FAIL+1))
    return 0
  fi
  if ! echo "$output" | grep -q "$should_contain"; then
    echo "    FAIL: expected diagnostic containing '$should_contain', got:"
    echo "$output" | head -n 20
    FAIL=$((FAIL+1))
    return 0
  fi
  echo "    PASS: exit $code, diagnostic contains '$should_contain'"
  PASS=$((PASS+1))
}

# Deterministic fail-closed fixture copy: tar with excludes, no fallback, never copy .git/.temp/.task-board
fixture_copy() {
  local name="$1"
  local dir="$TEMP_ROOT/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  # Fail closed: if tar fails, exit suite
  (cd "$REPO_DIR" && tar cf - --exclude='.git' --exclude='.temp' --exclude='.task-board' --exclude='task-board.config.json' --exclude='spawn-runs' . ) | (cd "$dir" && tar xf -)
  # Ensure excluded directories are absent
  rm -rf "$dir/.git" "$dir/.temp" "$dir/.task-board"
  if [ ! -f "$dir/SPEC.md" ] || [ ! -f "$dir/scripts/validate_spec.py" ]; then
    echo "ERROR: fixture_copy $name failed — missing SPEC.md or validator in copy"
    exit 1
  fi
  echo "$dir"
}

echo "Mutation 1: Missing required file (VERSION)"
FIX=$(fixture_copy "missing-version")
rm "$FIX/VERSION"
expect_fail "missing VERSION file" "missing required file" "$FIX"

echo ""
echo "Mutation 2: Inconsistent version (VERSION file 0.9.9)"
FIX=$(fixture_copy "bad-version")
echo "0.9.9" > "$FIX/VERSION"
expect_fail "inconsistent version" "VERSION" "$FIX"

echo ""
echo "Mutation 3: Inconsistent repository identity"
FIX=$(fixture_copy "bad-repo")
python3 -c "import pathlib; p=pathlib.Path('$FIX/SPEC.md'); t=p.read_text(); p.write_text(t.replace('relux-works/agent-session-manager-spec','evil/repo'))"
expect_fail "inconsistent repository" "repository" "$FIX"

echo ""
echo "Mutation 4: Broken local link"
FIX=$(fixture_copy "broken-link")
echo "[broken](nonexistent-file-12345.md)" >> "$FIX/SPEC.md"
expect_fail "broken local link" "missing local link" "$FIX"

echo ""
echo "Mutation 5: Broken anchor (file + anchor)"
FIX=$(fixture_copy "broken-anchor")
echo "[bad anchor](SPEC.md#this-anchor-does-not-exist-12345)" >> "$FIX/README.md"
expect_fail "broken anchor" "broken anchor" "$FIX"

echo ""
echo "Mutation 6: Invalid JSON example (malformed)"
FIX=$(fixture_copy "bad-json")
python3 -c "
import pathlib, re
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('\"schema\": \"urn:ax:schema:session-record\"', '\"schema\": urn:ax:schema:session-record', 1)
p.write_text(t)
"
expect_fail "invalid JSON" "JSON" "$FIX"

echo ""
echo "Mutation 7: Invalid TOML example (malformed)"
FIX=$(fixture_copy "bad-toml")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('payload_encryption = \"none\"', 'payload_encryption = none', 1)
p.write_text(t)
"
expect_fail "invalid TOML" "TOML" "$FIX"

echo ""
echo "Mutation 8: Omitted matrix platform row (remove WSL2)"
FIX=$(fixture_copy "missing-wsl2")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('WSL2','__MISSING_WSL2__')
p.write_text(t)
"
expect_fail "omitted WSL2 matrix row" "WSL2" "$FIX"

echo ""
echo "Mutation 9: Omitted capability caveat (remove prompt_spawn)"
FIX=$(fixture_copy "missing-prompt-spawn")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('prompt_spawn','__MISSING__')
p.write_text(t)
"
expect_fail "omitted prompt_spawn caveat" "prompt_spawn" "$FIX"

echo ""
echo "Mutation 10: Forbidden encryption claim (positive default encryption)"
FIX=$(fixture_copy "forbidden-encryption")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('default payload encryption at rest and MUST NOT claim otherwise','default payload encryption at rest is enabled by default')
p.write_text(t)
"
expect_fail "forbidden encryption claim" "forbidden" "$FIX"

echo ""
echo "Mutation 11: Forbidden replication claim (claim qwen direct available)"
FIX=$(fixture_copy "forbidden-qwen")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('there is no v0.1.0 direct <code>ax-provider-qwen</code> claim.','ax-provider-qwen is available for direct use.')
p.write_text(t)
"
expect_fail "forbidden qwen direct claim" "forbidden" "$FIX"

echo ""
echo "Mutation 12: Invalid diagram sources (empty workspace.dsl)"
FIX=$(fixture_copy "bad-diagram")
python3 -c "import pathlib; pathlib.Path('$FIX/diagrams/c4/workspace.dsl').write_text('')"
expect_fail "invalid diagram sources" "empty" "$FIX"

echo ""
echo "Mutation 13: Stale SVG file set (extra committed SVG)"
FIX=$(fixture_copy "stale-svg-set")
touch "$FIX/diagrams/artefacts/extra-stale.svg"
expect_fail "extra stale SVG" "SVG set" "$FIX"

echo ""
echo "Mutation 14: Missing native Windows caveat (remove MUST NOT claim tmux)"
FIX=$(fixture_copy "missing-windows-caveat")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace('MUST NOT claim tmux','MAY claim tmux')
p.write_text(t)
"
expect_fail "missing Windows tmux caveat" "MUST NOT claim tmux" "$FIX"

echo ""
echo "Mutation 15: Same-document anchor false positive (README anchor exists only in SPEC)"
# Add an anchor in README that does not exist in README but does exist in SPEC, should fail same-doc check
FIX=$(fixture_copy "same-doc-anchor-false-positive")
# Use a SPEC heading anchor that is not in README, e.g., provider-manager or a numbered section anchor that README doesn't have
python3 -c "
import pathlib
p=pathlib.Path('$FIX/README.md')
t=p.read_text()
# Find a SPEC anchor: use '8-provider-and-platform-contracts' which exists only in SPEC
t+=\"\n[spec-only anchor](#8-provider-and-platform-contracts)\n\"
p.write_text(t)
"
expect_fail "same-doc anchor that exists only in SPEC" "broken same-document anchor" "$FIX"

echo ""
echo "Mutation 16: Unbalanced Markdown fence"
FIX=$(fixture_copy "unbalanced-fence")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/README.md')
t=p.read_text()
t+=\"\n\`\`\`shell\necho unbalanced\n\"
p.write_text(t)
"
expect_fail "unbalanced Markdown fence" "unbalanced" "$FIX"

echo ""
echo "Mutation 17: Positive direct-Qwen claim while negative disclosure remains"
FIX=$(fixture_copy "qwen-positive-with-negative")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
# Keep the negative disclosure but add a new positive claim on a new line
t+=\"\nax-provider-qwen is available for direct use.\n\"
p.write_text(t)
"
expect_fail "positive direct-Qwen claim with negative still present" "forbidden positive" "$FIX"

echo ""
echo "Mutation 18: Changed matrix cell while capability tokens remain elsewhere"
FIX=$(fixture_copy "matrix-cell-changed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
# Change a specific matrix cell: Claude appserver from 'U for direct' to 'A'
t=t.replace('U for direct adapter','A for direct adapter',1)
p.write_text(t)
"
expect_fail "changed matrix cell (Claude appserver)" "Claude" "$FIX"

echo ""
echo "Mutation 19: Generic Qwen mentions without task-board-only release disclosure"
FIX=$(fixture_copy "generic-qwen-release-caveat")
python3 -c "
import pathlib
for name in ['CHANGELOG.md', 'RELEASE_NOTES.md']:
    p=pathlib.Path('$FIX') / name
    t=p.read_text()
    t=t.replace('task-board-only prompt mode integration for qwen', 'direct prompt mode integration for qwen')
    t=t.replace('Qwen is only supported via task-board prompt-mode bundles (no direct native \`ax-provider-qwen\` claim).', 'Qwen support is available.')
    p.write_text(t)
"
expect_fail "generic Qwen mentions do not prove task-board-only disclosure" "Qwen task-board-only caveat" "$FIX"

echo ""
echo "Mutation 20: Claude provider mention with positive direct appserver claim"
FIX=$(fixture_copy "false-claude-release-caveat")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/RELEASE_NOTES.md')
t=p.read_text().replace(\"direct adapter's \`appserver\` capability is unsupported\", \"direct adapter's \`appserver\` capability is available\")
p.write_text(t)
"
expect_fail "Claude name does not prove unsupported direct appserver disclosure" "Claude direct-appserver unsupported caveat" "$FIX"

echo ""
echo "Mutation 21: Muse provider mention with portable cron store claim weakened"
FIX=$(fixture_copy "false-muse-release-caveat")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/RELEASE_NOTES.md')
t=p.read_text().replace('portable_store=false', 'portable_store=true')
p.write_text(t)
"
expect_fail "Muse name does not prove non-portable cron store disclosure" "Muse non-portable cron store caveat" "$FIX"

echo ""
echo "Mutation 22: Generic Antigravity mention without backend-realm caveat"
FIX=$(fixture_copy "generic-antigravity-release-caveat")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/RELEASE_NOTES.md')
lines=p.read_text().splitlines()
lines=['- Antigravity is supported.' if line.startswith('- Antigravity resumes via') else line for line in lines]
p.write_text('\\n'.join(lines) + '\\n')
"
expect_fail "Antigravity name does not prove authenticated-backend resume disclosure" "Antigravity authenticated-backend resume caveat" "$FIX"

echo ""
echo "Mutation 23: Generic Windows/WSL2 mention without separation and backend caveat"
FIX=$(fixture_copy "generic-windows-release-caveat")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/RELEASE_NOTES.md')
lines=p.read_text().splitlines()
lines=['- Native Windows and WSL2 are supported.' if line.startswith('- Native Windows and WSL2 are distinctly') else line for line in lines]
p.write_text('\\n'.join(lines) + '\\n')
"
expect_fail "platform names do not prove Windows/WSL2 separation and backend disclosure" "Native Windows/WSL2 separation and terminal-backend caveat" "$FIX"

echo ""
echo "Diagram mutations via full ./run_validation.sh (requires structurizr-cli and plantuml):"

echo ""
echo "Mutation 24: Invalid non-empty Structurizr source (syntactically invalid DSL)"
FIX=$(fixture_copy "invalid-structurizr")
echo "this is not valid structurizr dsl {{{" > "$FIX/diagrams/c4/workspace.dsl"
expect_fail "invalid non-empty Structurizr source" "Unexpected" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 25: Byte-modified existing generated .puml"
FIX=$(fixture_copy "stale-puml-bytes")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/diagrams/c4/structurizr-SystemContext.puml')
t=p.read_text()
p.write_text(t + '\n// stale modification\n')
"
expect_fail "byte-modified existing generated puml" "stale" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 26: Byte-modified existing SVG"
FIX=$(fixture_copy "stale-svg-bytes")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/diagrams/artefacts/takeover.svg')
t=p.read_text()
p.write_text(t.replace('<svg','<svg><!-- stale -->',1))
"
expect_fail "byte-modified existing SVG" "byte integrity mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 27: Unknown RPC body operation while the row count remains 23"
FIX=$(fixture_copy "rpc-body-renamed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
section=t.index('### 11.3 RPC operations')
marker='| Operation | Exact request body | Exact success body |'
start=t.index(marker, section)
old='| <code>health.get</code>'
row=t.index(old, start)
t=t[:row] + t[row:].replace(old, '| <code>health.evil</code>', 1)
p.write_text(t)
"
expect_fail "renamed RPC body operation" "rpc_body_operations registry mismatch" "$FIX"

echo ""
echo "Mutation 28: Claude native_resume capability changed while tokens remain elsewhere"
FIX=$(fixture_copy "claude-native-resume-cell")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text().replace(
    '| Claude | A | C | C | U for direct adapter |',
    '| Claude | U | C | C | U for direct adapter |', 1)
p.write_text(t)
"
expect_fail "changed Claude native_resume cell" "8.3 capability matrix row 2 mismatch" "$FIX"

echo ""
echo "Mutation 29: Codex/macOS platform status changed while row remains present"
FIX=$(fixture_copy "codex-macos-status-cell")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text().replace('| Codex / macOS | A / C / C |', '| Codex / macOS | U / U / U |', 1)
p.write_text(t)
"
expect_fail "changed Codex/macOS platform cells" "8.4 provider/platform matrix row 1 mismatch" "$FIX"

echo ""
echo "Mutation 30: Canonical MIT grant text changed"
FIX=$(fixture_copy "license-body-changed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/LICENSE')
t=p.read_text().replace('Software\"), to deal\nin the Software', 'Software\"), to frobnicate\nin the Software', 1)
p.write_text(t)
"
expect_fail "changed canonical MIT body" "complete canonical MIT text" "$FIX"

echo ""
echo "Mutation 31: Release note claims Muse cron.db is safely portable"
FIX=$(fixture_copy "release-muse-portable-positive")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/RELEASE_NOTES.md')
t=p.read_text().replace('cron.db\` is durable but not safely portable', 'cron.db\` is durable and safely portable', 1)
p.write_text(t)
"
expect_fail "positive Muse cron portability release claim" "Muse non-portable cron store caveat" "$FIX"

echo ""
echo "Mutation 32: Fenced commit template adds an AI Co-Authored-By trailer"
FIX=$(fixture_copy "ai-trailer-template")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/CONTRIBUTING.md')
t=p.read_text() + '\n~~~text\nSubject\n\nCo-Authored-By: AI Bot <ai@example.com>\n~~~\n'
p.write_text(t)
"
expect_fail "positive AI attribution trailer in fenced template" "forbidden positive AI Co-Authored-By trailer" "$FIX"

echo ""
echo "Mutation 33: Alternate positive native-Qwen parity wording"
FIX=$(fixture_copy "qwen-native-positive-wording")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text() + '\nQwen is natively supported by ax without task-board.\n'
p.write_text(t)
"
expect_fail "positive native Qwen support wording" "direct/native/without-task-board Qwen" "$FIX"

echo ""
echo "Mutation 34: Valid handwritten PlantUML source changed without refreshing SVG"
FIX=$(fixture_copy "handwritten-svg-source-stale")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/diagrams/plantuml/takeover.puml')
t=p.read_text().replace('@startuml', '@startuml\n\x27 freshness mutation', 1)
p.write_text(t)
"
expect_fail "changed valid PlantUML source with stale SVG" "embedded PlantUML source metadata differs" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 35: CI Structurizr asset URL regresses to a nonexistent version-named asset"
FIX=$(fixture_copy "ci-structurizr-url")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/.github/workflows/validate.yml')
t=p.read_text().replace('structurizr-cli.zip\" -O', 'structurizr-cli-2025.11.09.zip\" -O', 1)
p.write_text(t)
"
expect_fail "invalid CI Structurizr asset URL" "missing pinned Structurizr release URL" "$FIX"

echo ""
echo "Mutation 36: Contradictory default snapshot-encryption claim while prohibition remains"
FIX=$(fixture_copy "contradictory-default-encryption")
printf '\nAll session snapshots are encrypted at rest by default.\n' >> "$FIX/SPEC.md"
expect_fail "retained prohibition plus default encryption claim" "default at-rest encryption" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 37: Contradictory credential/token replication claim while exclusions remain"
FIX=$(fixture_copy "contradictory-credential-replication")
printf '\nCredentials and API tokens are replicated across mesh hosts.\n' >> "$FIX/CONTRIBUTING.md"
expect_fail "retained exclusions plus credential/token replication claim" "credential/token replication" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 38: Contradictory live-SQLite replication-unit claim while prohibition remains"
FIX=$(fixture_copy "contradictory-live-sqlite")
printf '\nThe live SQLite database is synchronized as the replication unit.\n' >> "$FIX/CHANGELOG.md"
expect_fail "retained prohibition plus live SQLite replication claim" "live SQLite replication-unit" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 39: Qwen works without task-board while task-board-only caveat remains"
FIX=$(fixture_copy "contradictory-qwen-without-task-board")
printf '\nQwen works without task-board in v0.1.0.\n' >> "$FIX/README.md"
expect_fail "retained caveat plus without-task-board Qwen claim" "without-task-board Qwen" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 40: Muse cron.db portable-store parity while caveat remains"
FIX=$(fixture_copy "contradictory-muse-portability")
printf '\nMuse cron.db is safely portable between hosts.\n' >> "$FIX/RELEASE_NOTES.md"
expect_fail "retained caveat plus Muse portable-store parity claim" "Muse portable-store parity" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 41: Default encryption claim with an unrelated without-setup qualifier"
FIX=$(fixture_copy "default-encryption-without-setup")
printf '\nAll session snapshots are encrypted at rest by default without requiring operator setup.\n' >> "$FIX/SPEC.md"
expect_fail "default encryption remains positive despite without-setup qualifier" "default at-rest encryption" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 42: Credential replication claim with an unrelated without-intervention qualifier"
FIX=$(fixture_copy "credential-replication-without-intervention")
printf '\nCredentials and API tokens are replicated between mesh hosts without user intervention.\n' >> "$FIX/CONTRIBUTING.md"
expect_fail "credential replication remains positive despite without-intervention qualifier" "credential/token replication" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 43: Live-SQLite replication claim with an unrelated without-staging qualifier"
FIX=$(fixture_copy "live-sqlite-without-staging")
printf '\nThe live SQLite database is synchronized as the replication unit without staging.\n' >> "$FIX/CHANGELOG.md"
expect_fail "live SQLite replication remains positive despite without-staging qualifier" "live SQLite replication-unit" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 44: Qwen task-board independence claim"
FIX=$(fixture_copy "qwen-independent-of-task-board")
printf '\nQwen works independently of task-board in v0.1.0.\n' >> "$FIX/README.md"
expect_fail "Qwen task-board independence wording" "direct/native/without-task-board Qwen" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 45: Muse portability claim with an unrelated without-conversion qualifier"
FIX=$(fixture_copy "muse-portability-without-conversion")
printf '\nMuse cron.db is safely portable between hosts without conversion.\n' >> "$FIX/RELEASE_NOTES.md"
expect_fail "Muse portability remains positive despite without-conversion qualifier" "Muse portable-store parity" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 46: Active default-encryption wording outside the semantic phrase set"
FIX=$(fixture_copy "release-baseline-encryption-active")
printf '\nBy default, all session snapshots receive at-rest encryption.\n' >> "$FIX/SPEC.md"
expect_fail "frozen release baseline rejects active default-encryption wording" "SPEC.md: frozen v0.1.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 47: Active API-token replication wording outside the semantic phrase set"
FIX=$(fixture_copy "release-baseline-token-copy")
printf '\nThe mesh copies API tokens to every authorized peer.\n' >> "$FIX/CONTRIBUTING.md"
expect_fail "frozen release baseline rejects active token-copy wording" "CONTRIBUTING.md: frozen v0.1.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 48: Imperative live-SQLite replication-unit wording"
FIX=$(fixture_copy "release-baseline-sqlite-imperative")
printf '\nUse the live SQLite database as the replication unit.\n' >> "$FIX/CHANGELOG.md"
expect_fail "frozen release baseline rejects imperative SQLite wording" "CHANGELOG.md: frozen v0.1.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 49: Qwen task-board independence expressed as no dependency"
FIX=$(fixture_copy "release-baseline-qwen-no-need")
printf '\nQwen sessions do not need task-board in v0.1.0.\n' >> "$FIX/README.md"
expect_fail "frozen release baseline rejects Qwen no-dependency wording" "README.md: frozen v0.1.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 50: Muse cross-host portability expressed as support"
FIX=$(fixture_copy "release-baseline-muse-supports-portability")
printf '\nMuse cron.db supports safe cross-host portability.\n' >> "$FIX/RELEASE_NOTES.md"
expect_fail "frozen release baseline rejects Muse portability wording" "RELEASE_NOTES.md: frozen v0.1.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed out of $TOTAL mutations"
if [ $FAIL -ne 0 ]; then
  echo "Expected-red suite FAILED"
  exit 1
fi
echo "Expected-red suite PASSED — all mutations correctly rejected with actionable diagnostics."
