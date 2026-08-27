#!/bin/bash
set -euo pipefail

echo "=== Expected-red mutation suite for v0.3.0 specification validation ==="
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

# Semantic mutations intentionally advance the frozen SPEC digest inside their
# isolated fixture. This proves the semantic diagnostic survives a reviewed
# release-baseline refresh instead of passing only because content integrity
# noticed that SPEC.md changed.
refresh_frozen_spec_digest() {
  local fixture_dir="$1"
  python3 - "$fixture_dir" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
spec = root / "SPEC.md"
validator = root / "scripts" / "validate_spec.py"
normalized = spec.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()
digest = hashlib.sha256(normalized).hexdigest()
text = validator.read_text(encoding="utf-8")
updated, count = re.subn(
    r'("SPEC\.md": ")[0-9a-f]{64}("[,])',
    rf'\g<1>{digest}\2',
    text,
    count=1,
)
if count != 1:
    raise SystemExit("could not refresh frozen SPEC.md digest in fixture validator")
validator.write_text(updated, encoding="utf-8")
PY
}

refresh_frozen_document_digest() {
  local fixture_dir="$1"
  local document_name="$2"
  python3 - "$fixture_dir" "$document_name" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
name = sys.argv[2]
document = root / name
validator = root / "scripts" / "validate_spec.py"
normalized = document.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()
digest = hashlib.sha256(normalized).hexdigest()
text = validator.read_text(encoding="utf-8")
updated, count = re.subn(
    rf'("{re.escape(name)}": ")[0-9a-f]{{64}}("[,])',
    rf'\g<1>{digest}\2',
    text,
    count=1,
)
if count != 1:
    raise SystemExit(f"could not refresh frozen {name} digest in fixture validator")
validator.write_text(updated, encoding="utf-8")
PY
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
old='there is no v0.2.1 direct claim and no v0.3.0 direct <code>ax-provider-qwen</code> claim.'
assert old in t
t=t.replace(old, 'there is no v0.2.1 direct claim, but Qwen is directly supported in v0.3.0.', 1)
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
printf '\nQwen works without task-board in v0.2.1.\n' >> "$FIX/README.md"
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
printf '\nQwen works independently of task-board in v0.2.1.\n' >> "$FIX/README.md"
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
expect_fail "frozen release baseline rejects active default-encryption wording" "SPEC.md: frozen v0.3.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 47: Active API-token replication wording outside the semantic phrase set"
FIX=$(fixture_copy "release-baseline-token-copy")
printf '\nThe mesh copies API tokens to every authorized peer.\n' >> "$FIX/CONTRIBUTING.md"
expect_fail "frozen release baseline rejects active token-copy wording" "CONTRIBUTING.md: frozen v0.3.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 48: Imperative live-SQLite replication-unit wording"
FIX=$(fixture_copy "release-baseline-sqlite-imperative")
printf '\nUse the live SQLite database as the replication unit.\n' >> "$FIX/CHANGELOG.md"
expect_fail "frozen release baseline rejects imperative SQLite wording" "CHANGELOG.md: frozen v0.3.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 49: Qwen task-board independence expressed as no dependency"
FIX=$(fixture_copy "release-baseline-qwen-no-need")
printf '\nQwen sessions do not need task-board in v0.2.1.\n' >> "$FIX/README.md"
expect_fail "frozen release baseline rejects Qwen no-dependency wording" "README.md: frozen v0.3.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 50: Muse cross-host portability expressed as support"
FIX=$(fixture_copy "release-baseline-muse-supports-portability")
printf '\nMuse cron.db supports safe cross-host portability.\n' >> "$FIX/RELEASE_NOTES.md"
expect_fail "frozen release baseline rejects Muse portability wording" "RELEASE_NOTES.md: frozen v0.3.0 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 51: Mesh materialize.prepare loses caller operation ID"
FIX=$(fixture_copy "rpc-prepare-without-operation-id")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
start=t.index('### 11.3 RPC operations')
row=t.index('| <code>materialize.prepare</code> | Tagged <code>{', start)
t=t[:row] + t[row:].replace('initiator_host_id:UUIDv7,operation_id:UUIDv7,materialization_id:UUIDv7', 'initiator_host_id:UUIDv7,materialization_id:UUIDv7', 1)
p.write_text(t)
"
expect_fail "prepare request without caller operation ID" "materialize.prepare request must carry caller-stable operation_id and materialization_id" "$FIX"

echo ""
echo "Mutation 52: Provider status is incorrectly made a mutation receipt"
FIX=$(fixture_copy "provider-status-with-operation-id")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace(
    '<code>{materialization_id:UUIDv7, transaction_id:UUIDv7, transaction:ProviderTransactionAuthority}</code> | <code>ProviderTransactionStatus</code>',
    '<code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, transaction:ProviderTransactionAuthority}</code> | <code>ProviderTransactionStatus</code>',
    1,
)
p.write_text(t)
"
expect_fail "provider status carries forbidden operation ID" "provider materialize-status must be an evolving read" "$FIX"

echo ""
echo "Mutation 53: Strict JSONC fixture is malformed"
FIX=$(fixture_copy "bad-jsonc")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
start=t.index('~~~jsonc')
tail=t[start:]
q=chr(34)
old=q+'schema'+q+': '+q+'urn:ax:schema:materialization-plan'+q
new=q+'schema'+q+': urn:ax:schema:materialization-plan'
assert old in tail
tail=tail.replace(old, new, 1)
p.write_text(t[:start] + tail)
"
expect_fail "malformed strict JSONC fixture" "JSONC block" "$FIX"

echo ""
echo "Mutation 54: Canonicalizer regresses to Unicode code-point ordering"
FIX=$(fixture_copy "jcs-codepoint-ordering")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/scripts/validate_spec.py')
t=p.read_text()
q=chr(34)
old='keys = sorted(value, key=lambda key: key.encode('+q+'utf-16-be'+q+'))'
assert old in t
t=t.replace(old, 'keys = sorted(value)', 1)
p.write_text(t)
"
expect_fail "JCS canonicalizer uses code-point ordering" "RFC 8785 UTF-16 ordering" "$FIX"

echo ""
echo "Mutation 55: Recovery journal cannot represent a maximum-size closure"
FIX=$(fixture_copy "journal-cardinality-regression")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
t=t.replace(
    '<code>verified_blob_ids</code> | sorted unique digest[0..65536]',
    '<code>verified_blob_ids</code> | sorted unique digest[0..4096]',
    1,
)
p.write_text(t)
"
expect_fail "journal verified blob cardinality regresses" "materialization recovery cardinality mismatch" "$FIX"

echo ""
echo "Mutation 56: Prepare request digest is not persisted"
FIX=$(fixture_copy "journal-without-prepare-digest")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
lines=p.read_text().splitlines()
lines=[line for line in lines if not line.startswith('| <code>prepare_request_digest</code> |')]
p.write_text('\n'.join(lines) + '\n')
"
expect_fail "journal omits prepare request digest" "Materialization Journal missing durable prepare receipt field prepare_request_digest" "$FIX"

echo ""
echo "Mutation 57: Breaking provider shape is mislabeled as protocol 1.0.0"
FIX=$(fixture_copy "provider-contract-version-regression")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='| Provider protocol | <code>urn:ax:protocol:provider</code> | <code>2.0.0</code> |'
new='| Provider protocol | <code>urn:ax:protocol:provider</code> | <code>1.0.0</code> |'
assert old in t
p.write_text(t.replace(old, new, 1))
"
expect_fail "breaking provider shape keeps old major" "critical contract version mismatch" "$FIX"

echo ""
echo "Mutation 58: Active provider semantics regress to a protocol-v1 label"
FIX=$(fixture_copy "provider-active-version-label-regression")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='single Provider protocol 2.0.0 idempotency key'
new='single protocol-v1 idempotency key'
assert old in t
p.write_text(t.replace(old, new, 1))
"
expect_fail "active provider semantics use stale major label" "critical active contract version label missing or regressed" "$FIX"

echo ""
echo "Mutation 59: Active Mesh RPC operation table regresses to Version 1"
FIX=$(fixture_copy "rpc-active-version-label-regression")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Mesh RPC 2.0.0 operations are:'
new='Version 1 operations are:'
assert old in t
p.write_text(t.replace(old, new, 1))
"
expect_fail "active Mesh RPC operation table uses stale major label" "critical active contract version label missing or regressed" "$FIX"

echo ""
echo "Mutation 60: Active Mesh RPC anti-entropy fixtures regress to protocol 1.0.0"
FIX=$(fixture_copy "rpc-fixture-version-label-regression")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='These Mesh RPC 2.0.0 fixtures are normative.'
new='These protocol-1.0.0 fixtures are normative.'
assert old in t
p.write_text(t.replace(old, new, 1))
"
expect_fail "active Mesh RPC fixtures use stale major label" "critical active contract version label missing or regressed" "$FIX"

echo ""
echo "Mutation 61: Crash outcome exhaustiveness clause is weakened"
FIX=$(fixture_copy "crash-outcome-not-exhaustive")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='They are collectively exhaustive:'
assert old in t
p.write_text(t.replace(old, 'They are usually sufficient:', 1))
"
expect_fail "crash outcomes must remain collectively exhaustive" "crash/restart gate outcome collective exhaustiveness" "$FIX"

echo ""
echo "Mutation 62: Owner-resume crash boundary family is removed"
FIX=$(fixture_copy "crash-boundary-resume-removed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
lines=p.read_text().splitlines()
prefix='| <code>CR-RESUME-01..06</code> |'
assert any(line.startswith(prefix) for line in lines)
p.write_text('\n'.join(line for line in lines if not line.startswith(prefix)) + '\n')
"
expect_fail "crash registry must retain owner-resume boundaries" "crash/restart gate boundary registry mismatch" "$FIX"

echo ""
echo "Mutation 63: Duplicate live-owner prohibition is weakened"
FIX=$(fixture_copy "crash-duplicate-owner-weakened")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='two hosts or two native\nprocesses/managers can both be treated as live or authoritative for the same\nlogical session'
assert old in t
new='two hosts or two native\nprocesses/managers may both be treated as live or authoritative for the same\nlogical session'
p.write_text(t.replace(old, new, 1))
"
expect_fail "crash recovery must reject duplicate live owners" "crash/restart gate duplicate-owner prohibition" "$FIX"

echo ""
echo "Mutation 64: Silent fresh native-session prohibition is removed"
FIX=$(fixture_copy "crash-fresh-native-allowed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='invokes a new-session launch, allocates a fresh native handle or manager\nreference, relabels blank state, or resumes a different provider/account realm'
assert old in t
new='reuses any available provider or manager session'
p.write_text(t.replace(old, new, 1))
"
expect_fail "crash recovery must preserve exact native identity" "crash/restart gate fresh native identity prohibition" "$FIX"

echo ""
echo "Mutation 65: Required external-effect status evidence is removed"
FIX=$(fixture_copy "crash-evidence-status-probe-removed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='external effect and status probe'
assert old in t
p.write_text(t.replace(old, 'external effect note', 1))
"
expect_fail "crash classification must retain external-effect status evidence" "crash/restart gate classification evidence field external effect and status probe" "$FIX"

echo ""
echo "Mutation 66: Session Adapter contract is removed from the normative registry"
FIX=$(fixture_copy "clone-contract-registry-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
lines=p.read_text().splitlines()
prefix='| Session Adapter protocol |'
assert any(line.startswith(prefix) for line in lines)
p.write_text('\n'.join(line for line in lines if not line.startswith(prefix)) + '\n')
"
expect_fail "clone contract registry must close over Session Adapter" "clone gate contract registry mismatch for Session Adapter protocol" "$FIX"

echo ""
echo "Mutation 67: Adapter normalize operation is independently removed"
FIX=$(fixture_copy "clone-adapter-operation-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
lines=p.read_text().splitlines()
prefix='| <code>normalize</code> |'
assert any(line.startswith(prefix) for line in lines)
p.write_text('\n'.join(line for line in lines if not line.startswith(prefix)) + '\n')
"
expect_fail "Session Adapter operation registry must remain exact" "clone gate Session Adapter operation registry mismatch" "$FIX"

echo ""
echo "Mutation 68: Adapter canonical-write capability is narrowed away"
FIX=$(fixture_copy "clone-adapter-capability-narrowed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
start=t.index('The exact capability names are')
pos=t.index('<code>canonical_write</code>', start)
t=t[:pos] + t[pos:].replace('<code>canonical_write</code>', '<code>canonical_archive_only</code>', 1)
p.write_text(t)
"
expect_fail "Session Adapter capability registry must remain exact" "clone gate Session Adapter capability registry mismatch" "$FIX"

echo ""
echo "Mutation 69: Snapshot proof is narrowed to file-size equality"
FIX=$(fixture_copy "clone-snapshot-size-proxy")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='File-size equality is never proof.'
assert old in t
p.write_text(t.replace(old, 'File-size equality is sufficient proof.', 1))
"
expect_fail "stable snapshot must reject size-only proxy evidence" "clone gate size is not snapshot proof" "$FIX"

echo ""
echo "Mutation 70: Foreign instruction authority stripping is weakened"
FIX=$(fixture_copy "clone-foreign-instruction-authority")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Foreign instructions are low-authority history'
assert old in t
p.write_text(t.replace(old, 'Foreign instructions retain controller authority', 1))
"
expect_fail "foreign instructions must remain inert history" "clone gate foreign authority stripping" "$FIX"

echo ""
echo "Mutation 71: Unknown native records stop being opaque-preserved"
FIX=$(fixture_copy "clone-opaque-preservation-removed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Unknown native records become raw-addressable opaque\nevents.'
assert old in t
p.write_text(t.replace(old, 'Unknown native records are discarded.\n', 1))
"
expect_fail "unknown native records must remain opaque evidence" "clone gate opaque native preservation" "$FIX"

echo ""
echo "Mutation 72: Exact fidelity rows are allowed to carry reasons"
FIX=$(fixture_copy "clone-exact-reasons-weakened")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Exact requires an empty reason set'
assert old in t
p.write_text(t.replace(old, 'Exact may carry reason codes', 1))
"
expect_fail "exact fidelity rows must have no reason codes" "clone gate exact reason prohibition" "$FIX"

echo ""
echo "Mutation 73: Non-exact fidelity rows no longer require reasons"
FIX=$(fixture_copy "clone-nonexact-reasons-weakened")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='every other\ndisposition requires at least one reason'
assert old in t
p.write_text(t.replace(old, 'every other\ndisposition may omit reasons', 1))
"
expect_fail "non-exact fidelity rows must name stable reasons" "clone gate non-exact reason requirement" "$FIX"

echo ""
echo "Mutation 74: Per-item fidelity reconciliation is narrowed to events only"
FIX=$(fixture_copy "clone-per-item-reconciliation-narrowed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Every Capture Manifest item and Canonical Event occurs in exactly one\nnon-synthesized disposition row'
assert old in t
p.write_text(t.replace(old, 'Every Canonical Event occurs in a disposition row', 1))
"
expect_fail "fidelity must reconcile capture items and canonical events" "clone gate per-item fidelity closure" "$FIX"

echo ""
echo "Mutation 75: Fidelity report is allowed to point at validation report"
FIX=$(fixture_copy "clone-fidelity-digest-cycle")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='A target report does not name Clone Validation Report,\nLineage Receipt, G4, or a future event'
assert old in t
p.write_text(t.replace(old, 'A target report may name Clone Validation Report', 1))
"
expect_fail "fidelity graph must remain acyclic" "clone gate fidelity/report digest acyclicity" "$FIX"

echo ""
echo "Mutation 76: Bundle predecessor admits byte-different successors"
FIX=$(fixture_copy "clone-generation-mutable")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='one predecessor cannot\nhave byte-different successors'
assert old in t
p.write_text(t.replace(old, 'one predecessor may\nhave byte-different successors', 1))
"
expect_fail "clone generations must be immutable" "clone gate immutable generation chain" "$FIX"

echo ""
echo "Mutation 77: Archive and target generation-2 branches are collapsed"
FIX=$(fixture_copy "clone-generation-branch-collapse")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='generation 2 is exactly A2 naming G1\nor G2 naming G1. A2 is terminal. The target branch continues G2 to G3 to G4'
assert old in t
p.write_text(t.replace(old, 'generation 2 may mix archive and target facts', 1))
"
expect_fail "archive and target bundle branches must remain exclusive" "clone gate branch-exclusive generation" "$FIX"

echo ""
echo "Mutation 78: Clone materialization no longer requires rollback"
FIX=$(fixture_copy "clone-rollback-not-required")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Clone requires rollback, null prior checkpoint, collision absence'
assert old in t
p.write_text(t.replace(old, 'Clone permits no rollback and a prior checkpoint', 1))
"
expect_fail "clone transaction must require rollback retention" "clone gate clone rollback required" "$FIX"

echo ""
echo "Mutation 79: Journal 3 is changed into an inherited delta"
FIX=$(fixture_copy "clone-journal-inherits-v2")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Journal 3.0.0 is a complete clone-only schema and does not\ninherit Journal 2'
assert old in t
p.write_text(t.replace(old, 'Journal 3.0.0 inherits Journal 2 as a partial delta', 1))
"
expect_fail "clone journal must remain independently complete" "clone gate journal 3 independent schema" "$FIX"

echo ""
echo "Mutation 80: Journal phase facts are allowed to change after admission"
FIX=$(fixture_copy "clone-journal-facts-mutable")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Fields become non-null only at their phase and then\nremain immutable'
assert old in t
p.write_text(t.replace(old, 'Fields may be rewritten after later phases', 1))
"
expect_fail "journal facts must remain phase-monotonic and immutable" "clone gate journal facts immutable" "$FIX"

echo ""
echo "Mutation 81: Finalizing discards rollback before Provider commit"
FIX=$(fixture_copy "clone-finalizing-without-rollback")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Provider remains rollback-capable'
assert old in t
p.write_text(t.replace(old, 'Provider rollback is already discarded', 1))
"
expect_fail "rollback must survive through finalizing intent" "clone gate rollback retention through finalizing" "$FIX"

echo ""
echo "Mutation 82: Post-commit byte rollback is allowed"
FIX=$(fixture_copy "clone-postcommit-rollback")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Post-commit rollback is forbidden'
assert old in t
p.write_text(t.replace(old, 'Post-commit rollback is allowed', 1))
"
expect_fail "post-commit recovery must not byte-rollback" "clone gate post-commit rollback forbidden" "$FIX"

echo ""
echo "Mutation 83: Recovery status is allowed to mint a fresh target"
FIX=$(fixture_copy "clone-recovery-mints-target")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='No status result authorizes a fresh Provider materialization, target native\nidentity, Session Record, lease, process, or transaction authority'
assert old in t
p.write_text(t.replace(old, 'A status result may authorize a fresh Provider materialization', 1))
"
expect_fail "recovery must preserve the exact target identity" "clone gate new-session retry prohibition" "$FIX"

echo ""
echo "Mutation 84: Clone committed lifecycle event is independently removed"
FIX=$(fixture_copy "clone-lifecycle-event-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
lines=p.read_text().splitlines()
prefix='| <code>clone.committed</code> |'
assert any(line.startswith(prefix) for line in lines)
p.write_text('\n'.join(line for line in lines if not line.startswith(prefix)) + '\n')
"
expect_fail "clone lifecycle event registry must remain exact" "clone gate lifecycle event registry mismatch" "$FIX"

echo ""
echo "Mutation 85: Source tuple entry gains target-write strategy"
FIX=$(fixture_copy "clone-source-tuple-writes")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Source-read entries have exactly <code>strategies=[archive_only]</code>'
assert old in t
p.write_text(t.replace(old, 'Source-read entries may use target_native_writer', 1))
"
expect_fail "source tuple evidence must not authorize target writing" "clone gate tuple source archive restriction" "$FIX"

echo ""
echo "Mutation 86: Target tuple admission no longer requires resume smoke"
FIX=$(fixture_copy "clone-target-tuple-no-smoke")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Target-write entries exclude archive-only, require current\nnon-null passing resume evidence'
assert old in t
p.write_text(t.replace(old, 'Target-write entries may omit resume evidence', 1))
"
expect_fail "target tuple admission must require bounded resume smoke" "clone gate tuple target smoke gate" "$FIX"

echo ""
echo "Mutation 87: Partial tuple-registry read is treated as absence"
FIX=$(fixture_copy "clone-tuple-partial-as-absence")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Failed/partial reads never mean absence.'
assert old in t
p.write_text(t.replace(old, 'Failed/partial reads mean absence.', 1))
"
expect_fail "tuple read failures must fail closed" "clone gate tuple read failure fail-closed" "$FIX"

echo ""
echo "Mutation 88: Clone run becomes a no-target-write surface"
FIX=$(fixture_copy "clone-run-no-write-bypass")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='<code>plan</code> is the sole no-target-write surface'
assert old in t
p.write_text(t.replace(old, '<code>plan</code> and <code>run</code> are no-target-write surfaces', 1))
"
expect_fail "plan must remain the sole no-write surface" "clone gate CLI plan sole no-write" "$FIX"

echo ""
echo "Mutation 89: run --dry-run becomes valid"
FIX=$(fixture_copy "clone-run-dry-run")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='<code>run --dry-run</code> is invalid before\ntarget allocation'
assert old in t
p.write_text(t.replace(old, '<code>run --dry-run</code> is valid', 1))
"
expect_fail "run dry-run must fail before target allocation" "clone gate CLI run dry-run rejected" "$FIX"

echo ""
echo "Mutation 90: Standalone traceability drops one mapped section"
FIX=$(fixture_copy "clone-traceability-row-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/STANDALONE_TO_AX_TRACEABILITY.md')
lines=p.read_text().splitlines()
prefix='| 20. Delivery Phases |'
assert any(line.startswith(prefix) for line in lines)
p.write_text('\n'.join(line for line in lines if not line.startswith(prefix)) + '\n')
"
expect_fail "standalone traceability must retain all 129 rows" "clone gate standalone traceability row count mismatch" "$FIX"

echo ""
echo "Mutation 91: Component diagram loses the no-converter marker"
FIX=$(fixture_copy "clone-component-diagram-marker-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/diagrams/plantuml/cloning_components.puml')
t=p.read_text()
old='No source×target converter pair'
assert old in t
p.write_text(t.replace(old, 'A source×target converter pair exists', 1))
"
expect_fail "component diagram must retain companion-adapter boundary" "clone gate diagram semantic marker missing in cloning_components.puml" "$FIX"

echo ""
echo "Mutation 92: Transaction diagram loses lineage-last ordering"
FIX=$(fixture_copy "clone-transaction-diagram-ordering-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/diagrams/plantuml/cloning_transaction.puml')
t=p.read_text()
old='publish Lineage Receipt, then G4 committed bundle'
assert old in t
p.write_text(t.replace(old, 'publish G4 before Lineage Receipt', 1))
"
expect_fail "transaction diagram must retain lineage-last order" "clone gate diagram semantic marker missing in cloning_transaction.puml" "$FIX"

echo ""
echo "Mutation 93: Critical transaction_unknown error code is removed"
FIX=$(fixture_copy "clone-error-code-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
start=t.index('Session Adapter 1.0 and <code>session.clone.*</code> bind Structured Error')
pos=t.index('<code>transaction_unknown</code>', start)
t=t[:pos] + t[pos:].replace('<code>transaction_unknown</code>', '<code>transaction_status_missing</code>', 1)
p.write_text(t)
"
expect_fail "clone error registry must retain ambiguous transaction code" "clone gate error registry transaction_unknown" "$FIX"

echo ""
echo "Mutation 94: Required target.staged_validated observation is removed"
FIX=$(fixture_copy "clone-observation-event-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
start=t.index('### 18.2 Required events')
pos=t.index('<code>target.staged_validated</code>', start)
t=t[:pos] + t[pos:].replace('<code>target.staged_validated</code>', '<code>target.staged</code>', 1)
p.write_text(t)
"
expect_fail "clone observation closure must include staged validation" "clone gate observation event target.staged_validated" "$FIX"

echo ""
echo "Mutation 95: Target Checkpoint no longer proves fully idle identity"
FIX=$(fixture_copy "clone-checkpoint-proof-narrowed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='proves the exact native identity, input blocked,\nfull idle, zero processes and handles'
assert old in t
p.write_text(t.replace(old, 'proves only the target path exists', 1))
"
expect_fail "target Checkpoint must prove identity and full idle" "clone gate target checkpoint identity proof" "$FIX"

echo ""
echo "Mutation 96: Clone is allowed to mutate the source lease"
FIX=$(fixture_copy "clone-source-immutability-weakened")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='MUST leave source\nbytes, Session Record, provider ID, lease, workspace authority, task-board\nbinding, and native identity unchanged'
assert old in t
p.write_text(t.replace(old, 'MAY rewrite the source lease and native identity', 1))
"
expect_fail "clone must preserve source authority and identity" "clone gate source immutability" "$FIX"

echo ""
echo "Mutation 97: Credential capture class is allowed into projection"
FIX=$(fixture_copy "clone-credential-class-included")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Credential, auth, runtime, and lock classes are always excluded'
assert old in t
p.write_text(t.replace(old, 'Credential classes may be included for fidelity', 1))
"
expect_fail "clone must strip credential and runtime authority" "clone gate security class stripping" "$FIX"

echo ""
echo "Mutation 98: Local policy is allowed to self-approve a tuple"
FIX=$(fixture_copy "clone-local-policy-self-approval")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='local policy may further\ndeny but cannot self-approve or override revocation'
assert old in t
p.write_text(t.replace(old, 'local policy may self-approve and override revocation', 1))
"
expect_fail "local policy may only restrict tuple admission" "clone gate tuple local policy monotonicity" "$FIX"

echo ""
echo "Mutation 99: Execution binding is no longer refreshed before target mutation"
FIX=$(fixture_copy "clone-binding-refresh-removed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Before every call and\ntarget mutation, these facts MUST equal freshly read trusted-candidate facts\nand the Journal binding'
assert old in t
p.write_text(t.replace(old, 'Execution binding is trusted once at startup', 1))
"
expect_fail "target mutation must refresh observed execution binding" "clone gate adapter trust binding refresh" "$FIX"

echo ""
echo "Mutation 100: Malformed adapter result falls back as absence"
FIX=$(fixture_copy "clone-adapter-malformed-as-absence")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Partial, malformed, over-limit, or escaped results are errors, never\nabsence or fallback permission'
assert old in t
p.write_text(t.replace(old, 'Malformed results are treated as absence and permit fallback', 1))
"
expect_fail "adapter result failure must remain distinct from absence" "clone gate adapter failure/absence distinction" "$FIX"

echo ""
echo "Mutation 101: Lineage receipt is allowed to name G4"
FIX=$(fixture_copy "clone-lineage-g4-cycle")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='It names G3,\nnever G4; G4 names it'
assert old in t
p.write_text(t.replace(old, 'It names G4 and G4 names it', 1))
"
expect_fail "lineage and committed bundle must remain acyclic" "clone gate lineage G3/G4 acyclicity" "$FIX"

echo ""
echo "Mutation 102: Clone crash boundary family is removed"
FIX=$(fixture_copy "clone-crash-boundary-family-missing")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='<code>CR-CLONE-01..16</code>'
assert old in t
p.write_text(t.replace(old, '<code>CR-CLONE-01..15</code>'))
"
expect_fail "clone crash boundary registry must remain closed" "clone gate clone crash boundary closure" "$FIX"

echo ""
echo "Mutation 103: Public ax clone alias is introduced"
FIX=$(fixture_copy "clone-public-alias-added")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='There is no <code>ax clone</code> alias.'
assert old in t
p.write_text(t.replace(old, 'The <code>ax clone</code> alias is supported.', 1))
"
expect_fail "clone namespace must remain ax session clone only" "clone gate CLI sole namespace" "$FIX"

echo ""
echo "Mutation 104: Target write no longer requires signed tuple evidence"
FIX=$(fixture_copy "clone-target-write-self-evidence")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='accepted non-revoked signed source/target tuple entries'
assert old in t
p.write_text(t.replace(old, 'self-minted source/target tuple entries', 1))
"
expect_fail "target write must require signed non-revoked tuple evidence" "clone gate target-write signed tuple admission" "$FIX"

echo ""
echo "Mutation 105: Internal v0.3.0 task ownership ID leaks into public docs"
FIX=$(fixture_copy "clone-public-internal-task-id")
printf '\nGate owner: TASK-260826-example.\n' >> "$FIX/README.md"
expect_fail "public package must not expose active internal task ownership" "stale/internal v0.3.0 publication marker" "$FIX"

echo ""
echo "Mutation 106: Stale v0.2.1 diagram-ledger wording returns"
FIX=$(fixture_copy "clone-stale-diagram-ledger")
printf '\nUses the unchanged v0.2.1 SHA-256 ledger.\n' >> "$FIX/diagrams/README.md"
expect_fail "diagram docs must describe the v0.3.0 ledger" "stale/internal v0.3.0 publication marker" "$FIX"

echo ""
echo "Mutation 107: Target derivation mutates the source provider identity after digest refresh"
FIX=$(fixture_copy "clone-target-mutates-source-provider")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='The new target Session ID and target <code>provider_id</code> are allocated at\ncreation and never reuse or mutate the source Session or source provider ID.'
assert old in t
p.write_text(t.replace(old, 'AX mutates the source Session <code>provider_id</code> in place to represent the target environment.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "target derivation must not mutate source provider identity" "clone gate target derivation preserves source provider identity" "$FIX"

echo ""
echo "Mutation 108: Source authorities transfer to the target after digest refresh"
FIX=$(fixture_copy "clone-source-authority-transfers")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='source goals, manager references, leases,\napprovals, tokens, and pending operations do not transfer.'
assert old in t
p.write_text(t.replace(old, 'source goals, manager references, leases, approvals, tokens, and pending operations transfer to the target.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "source authority must not transfer" "clone gate source authority non-transfer" "$FIX"

echo ""
echo "Mutation 109: Historical tools replay as live pending actions after digest refresh"
FIX=$(fixture_copy "clone-historical-tools-replay")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Historical tools\nare inert; incomplete calls become aborted history and block pending action.'
assert old in t
p.write_text(t.replace(old, 'Historical tools may replay as live actions; incomplete calls remain pending target actions.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "historical tools must remain inert" "clone gate historical tools remain inert" "$FIX"

echo ""
echo "Mutation 110: Foreign reasoning and source usage gain target authority after digest refresh"
FIX=$(fixture_copy "clone-reasoning-usage-authority")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='foreign encrypted/signed\nreasoning is opaque-preserved, and source usage is not target accounting.'
assert old in t
p.write_text(t.replace(old, 'foreign encrypted/signed reasoning is presented as target-native, and source usage becomes target billing.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "foreign reasoning and usage must remain non-authoritative" "clone gate reasoning and usage authority stripping" "$FIX"

echo ""
echo "Mutation 111: Continuation context claims native historical fidelity after digest refresh"
FIX=$(fixture_copy "clone-continuation-native-claim")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Continuation context is explicitly non-native historical fidelity.'
assert old in t
p.write_text(t.replace(old, 'Continuation context is reported as a native historical clone.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "continuation context must disclose non-native fidelity" "clone gate continuation context fidelity disclosure" "$FIX"

echo ""
echo "Mutation 112: Visible migration text gains assistant control authority after digest refresh"
FIX=$(fixture_copy "clone-visible-text-control-authority")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Visible text comes from\ntyped escaped fields and is user context, never an assistant reply or control\ninstruction.'
assert old in t
p.write_text(t.replace(old, 'Visible text may be fabricated as an assistant acknowledgement with control authority.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "visible migration text must remain low-authority user context" "clone gate visible migration text has no control authority" "$FIX"

echo ""
echo "Mutation 113: Raw evidence becomes a lossy inline summary after digest refresh"
FIX=$(fixture_copy "clone-raw-evidence-lossy-summary")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='key, capture class, byte count, blob ID, Blob Descriptor ID, and extensions.'
assert old in t
p.write_text(t.replace(old, 'key, capture class, byte count, a lossy inline summary, and extensions.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "raw evidence must remain content-addressed" "clone gate raw evidence remains content-addressed" "$FIX"

echo ""
echo "Mutation 114: G1 discards raw evidence after digest refresh"
FIX=$(fixture_copy "clone-g1-discards-raw")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='G0 names Capture Manifest. G1 adds Canonical Session/Events.'
assert old in t
p.write_text(t.replace(old, 'G0 names Capture Manifest. G1 discards raw evidence and keeps only target text.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "G1 must retain raw evidence while adding canonical records" "clone gate canonical generation retains raw evidence" "$FIX"

echo ""
echo "Mutation 115: Fidelity disposition registry collapses after digest refresh"
FIX=$(fixture_copy "clone-fidelity-dispositions-collapsed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='<code>exact</code>, <code>semantic</code>, <code>summarized</code>,\n<code>opaque_preserved</code>, <code>synthesized</code>, <code>omitted</code>,\nand <code>unrecoverable</code>.'
assert old in t
p.write_text(t.replace(old, '<code>exact</code>, <code>semantic</code>, and <code>omitted</code>.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "fidelity disposition registry must retain seven exact values" "clone gate fidelity disposition registry mismatch" "$FIX"

echo ""
echo "Mutation 116: Journal publishes before prepared after digest refresh"
FIX=$(fixture_copy "clone-transaction-order-reversed")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='resolving -> snapshotting -> captured -> normalized -> planned\n-> preparing -> prepared -> publishing -> published'
assert old in t
p.write_text(t.replace(old, 'resolving -> snapshotting -> captured -> normalized -> planned\n-> preparing -> publishing -> prepared -> published', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "transaction must reach prepared before publishing" "clone gate transaction phase ordering mismatch" "$FIX"

echo ""
echo "Mutation 117: Clone introduces a second blob-transfer subsystem after digest refresh"
FIX=$(fixture_copy "clone-second-transfer-subsystem")
python3 -c "
import pathlib
p=pathlib.Path('$FIX/SPEC.md')
t=p.read_text()
old='Transfer Manifest 1.0.0 remains unchanged.'
assert old in t
p.write_text(t.replace(old, 'Cloning introduces a second independent blob-transfer subsystem.', 1))
"
refresh_frozen_spec_digest "$FIX"
expect_fail "clone must reuse AX transfer contracts" "clone gate reuses AX transfer contracts" "$FIX"

echo ""
echo "Mutation 118: Public diagram ledgers regress to three PlantUML sources and seven SVG artifacts"
FIX=$(fixture_copy "clone-public-diagram-ledgers-narrowed")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
for name in ("README.md", "CONTRIBUTING.md"):
    path = root / name
    text = path.read_text(encoding="utf-8")
    text = text.replace("five handwritten PlantUML sources", "three handwritten PlantUML sources")
    text = text.replace("nine committed SVG artifacts", "seven committed SVG artifacts")
    path.write_text(text, encoding="utf-8")
PY
refresh_frozen_document_digest "$FIX" "README.md"
refresh_frozen_document_digest "$FIX" "CONTRIBUTING.md"
expect_fail "public diagram ledgers must not narrow to stale 3/7 counts" "public diagram ledger must declare five handwritten PlantUML sources" "$FIX"

echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed out of $TOTAL mutations"
if [ $FAIL -ne 0 ]; then
  echo "Expected-red suite FAILED"
  exit 1
fi
echo "Expected-red suite PASSED — all mutations correctly rejected with actionable diagnostics."
