#!/bin/bash
set -euo pipefail

echo "=== Expected-red mutation suite for v0.4.3 ==="
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

mutate_v043_fixture() {
  local fixture_dir="$1"
  local mutation="$2"
  python3 - "$fixture_dir" "$mutation" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1]) / "fixtures" / "v0_4_3_roadmap_terminal_realm.json"
mutation = sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8"))
positive = {row["id"]: row for row in data["positive_cases"]}
roadmap = {row["phase"]: row for row in data["roadmap"]}

if mutation == "unsafe-server-create":
    positive["REALM-EXISTING-BROKER-POS"]["facts"]["credential_dependent_server_action"] = "create"
elif mutation == "sentinel-only":
    positive["REALM-FUNCTIONAL-EVIDENCE-POS"]["facts"]["provider_auth_smoke"] = False
elif mutation == "implicit-mutating-route":
    positive["ROUTE-UNIQUE-NONMUTATING-POS"]["facts"]["mutates_ownership"] = True
elif mutation == "ownership-changing-sync":
    positive["SYNC-IMMUTABLE-POS"]["facts"]["changes_ownership"] = True
elif mutation == "incomplete-git-closure":
    positive["GIT-CLOSURE-POS"]["facts"]["closure"].remove("submodules")
elif mutation == "unsafe-preflight-order":
    positive["TAKEOVER-PREFLIGHT-POS"]["facts"]["graceful_ordering"] = [
        "ownership-commit", "destination-broker-auth-ready", "fenced-source-stop", "destination-runtime-create"
    ]
elif mutation == "socket-replication":
    data["terminal_realm"]["socket_replication"] = "allowed"
elif mutation == "premature-sdk":
    roadmap["M0"]["public_stable_plugin_sdk"] = True
else:
    raise SystemExit(f"unknown v0.4.3 mutation {mutation}")

path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
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
printf '\nSession snapshots are encrypted at rest by default.\n' >> "$FIX/SPEC.md"
expect_fail "semantic security gate rejects active default-encryption wording" "forbidden positive default at-rest encryption claim" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 47: Active API-token replication wording outside the semantic phrase set"
FIX=$(fixture_copy "release-baseline-token-copy")
printf '\nThe mesh copies API tokens to every authorized peer.\n' >> "$FIX/CONTRIBUTING.md"
expect_fail "frozen release baseline rejects active token-copy wording" "CONTRIBUTING.md: frozen v0.4.3 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 48: Imperative live-SQLite replication-unit wording"
FIX=$(fixture_copy "release-baseline-sqlite-imperative")
printf '\nUse the live SQLite database as the replication unit.\n' >> "$FIX/CHANGELOG.md"
expect_fail "frozen release baseline rejects imperative SQLite wording" "CHANGELOG.md: frozen v0.4.3 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 49: Qwen task-board independence expressed as no dependency"
FIX=$(fixture_copy "release-baseline-qwen-no-need")
printf '\nQwen sessions do not need task-board in v0.2.1.\n' >> "$FIX/README.md"
expect_fail "frozen release baseline rejects Qwen no-dependency wording" "README.md: frozen v0.4.3 release baseline mismatch" "$FIX" "./run_validation.sh"

echo ""
echo "Mutation 50: Muse cross-host portability expressed as support"
FIX=$(fixture_copy "release-baseline-muse-supports-portability")
printf '\nMuse cron.db supports safe cross-host portability.\n' >> "$FIX/RELEASE_NOTES.md"
expect_fail "frozen release baseline rejects Muse portability wording" "RELEASE_NOTES.md: frozen v0.4.3 release baseline mismatch" "$FIX" "./run_validation.sh"

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
expect_fail "public package must not expose active internal task ownership" "stale/internal v0.4.3 publication marker" "$FIX"

echo ""
echo "Mutation 106: Stale v0.2.1 diagram-ledger wording returns"
FIX=$(fixture_copy "clone-stale-diagram-ledger")
printf '\nUses the unchanged v0.2.1 SHA-256 ledger.\n' >> "$FIX/diagrams/README.md"
expect_fail "diagram docs must describe the v0.4.3 ledger" "stale/internal v0.4.3 publication marker" "$FIX"

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
echo "Mutation 118: Public diagram ledgers regress to five PlantUML sources and nine SVG artifacts"
FIX=$(fixture_copy "clone-public-diagram-ledgers-narrowed")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
for name in ("README.md", "CONTRIBUTING.md"):
    path = root / name
    text = path.read_text(encoding="utf-8")
    text = text.replace("eight handwritten PlantUML sources", "five handwritten PlantUML sources")
    text = text.replace("twelve committed SVG artifacts", "nine committed SVG artifacts")
    path.write_text(text, encoding="utf-8")
PY
refresh_frozen_document_digest "$FIX" "README.md"
refresh_frozen_document_digest "$FIX" "CONTRIBUTING.md"
expect_fail "public diagram ledgers must not narrow to stale 5/9 counts" "public diagram ledger must declare eight handwritten PlantUML sources" "$FIX"

mutate_directory_fixture() {
  local fixture_dir="$1"
  local mutation="$2"
  python3 - "$fixture_dir" "$mutation" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "fixtures" / "session_directory_conformance.json"
data = json.loads(path.read_text(encoding="utf-8"))
exec(sys.argv[2], {"data": data})
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
}

mutate_directory_vector_and_rehash() {
  local fixture_dir="$1"
  local schema="$2"
  local mutation="$3"
  python3 - "$fixture_dir" "$schema" "$mutation" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
schema = sys.argv[2]
path = root / "fixtures" / "session_directory_conformance.json"
sys.path.insert(0, str(root / "scripts"))
from validate_spec import canonical

data = json.loads(path.read_text(encoding="utf-8"))
row = next(item for item in data["identity_vectors"] if item["schema"] == schema)
exec(sys.argv[3], {"data": data, "row": row})
row["expected_id"] = "sha256:" + hashlib.sha256(canonical(row["canonical_input"])).hexdigest()
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
}

echo ""
echo "Mutation 119: Directory object placed in wrong namespace"
FIX=$(fixture_copy "directory-wrong-namespace")
mutate_directory_fixture "$FIX" 'data["mesh"]["directory_namespace"]="record"'
expect_fail "directory object wrong namespace" "directory objects must be placed only in directory_record namespace" "$FIX"

echo ""
echo "Mutation 120: RPC 3 hello omits a directory contract"
FIX=$(fixture_copy "directory-hello-missing-contract")
mutate_directory_fixture "$FIX" 'del data["mesh"]["hello_contracts"]["session_annotation"]'
expect_fail "hello missing directory contract" "exact 24 required contract keys" "$FIX"

echo ""
echo "Mutation 121: RPC 3 retains old six-namespace cardinality"
FIX=$(fixture_copy "directory-old-namespace-cardinality")
mutate_directory_fixture "$FIX" 'data["mesh"]["namespace_count"]=6'
expect_fail "old namespace cardinality" "namespace cardinality must be seven" "$FIX"

echo ""
echo "Mutation 122: Closed directory object admits unknown field"
FIX=$(fixture_copy "directory-unknown-field")
mutate_directory_fixture "$FIX" 'data["closed_shapes"]["environment_observation"].append("unexpected")'
expect_fail "closed directory object unknown field" "unknown field admitted" "$FIX"

echo ""
echo "Mutation 123: Directory JCS self-ID is wrong"
FIX=$(fixture_copy "directory-wrong-self-id")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][0]["expected_id"]="sha256:00"'
expect_fail "wrong directory self-ID" "wrong self-ID for urn:ax:schema:environment-observation" "$FIX"

echo ""
echo "Mutation 124: Directory digest array is unsorted"
FIX=$(fixture_copy "directory-unsorted-ids")
mutate_directory_fixture "$FIX" 'data["sorted_id_fixture"].reverse()'
expect_fail "unsorted directory IDs" "must be bytewise sorted and unique" "$FIX"

echo ""
echo "Mutation 125: Replication policy admits raw transcript metadata"
FIX=$(fixture_copy "directory-raw-transcript-replication")
mutate_directory_fixture "$FIX" 'data["disclosure"]["excluded_from_mesh"].remove("raw_transcript")'
expect_fail "raw transcript admitted to mesh" "replicated metadata must exclude raw IDs/paths/transcripts" "$FIX"

echo ""
echo "Mutation 126: Partial scan asserts missing"
FIX=$(fixture_copy "directory-partial-missing")
mutate_directory_fixture "$FIX" 'data["observation_cases"]["partial"]="missing"'
expect_fail "partial scan asserts missing" "offline/partial scan cannot assert presence=missing" "$FIX"

echo ""
echo "Mutation 127: Observation conflict resolves by wall clock"
FIX=$(fixture_copy "directory-clock-conflict")
mutate_directory_fixture "$FIX" 'data["observation_cases"]["conflict_resolution"]="wall_clock"'
expect_fail "wall-clock conflict resolution" "never wall clock" "$FIX"

echo ""
echo "Mutation 128: Generated annotation omits evidence binding"
FIX=$(fixture_copy "directory-generated-unbound")
mutate_directory_fixture "$FIX" 'data["annotation_cases"]["generated_requires"].remove("evidence_ids")'
expect_fail "generated annotation without evidence" "requires exact subject head, profile, and evidence" "$FIX"

echo ""
echo "Mutation 129: Enrichment overwrites manual title"
FIX=$(fixture_copy "directory-enrichment-overwrites-manual")
mutate_directory_fixture "$FIX" 'data["annotation_cases"]["manual_precedence"]=False'
expect_fail "enrichment overwrites manual title" "must not overwrite manual title metadata" "$FIX"

echo ""
echo "Mutation 130: Supersession omits a concurrent head"
FIX=$(fixture_copy "directory-incomplete-supersession")
mutate_directory_fixture "$FIX" 'data["annotation_cases"]["conflict_resolution"]="supersede_one_head"'
expect_fail "incomplete supersession resolution" "supersede every concurrent head" "$FIX"

echo ""
echo "Mutation 131: Mutation ID changed input reuses success receipt"
FIX=$(fixture_copy "directory-idempotency-changed-input")
mutate_directory_fixture "$FIX" 'data["directory_node"]["idempotency"]["same_mutation_changed_input"]="same_receipt"'
expect_fail "changed-input mutation ID reuse" "must return idempotency_mismatch" "$FIX"

echo ""
echo "Mutation 132: Stale plan silently replans"
FIX=$(fixture_copy "directory-stale-plan-replans")
mutate_directory_fixture "$FIX" 'data["continuation_plan"]["silent_replan"]=True'
expect_fail "stale plan silent replan" "without silent replan/route substitution" "$FIX"

echo ""
echo "Mutation 133: Remote unmanaged open is admitted"
FIX=$(fixture_copy "directory-remote-unmanaged-open")
mutate_directory_fixture "$FIX" 'data["remote_unmanaged"]["open_allowed"]=True'
expect_fail "remote unmanaged open" "remote unmanaged open is forbidden" "$FIX"

echo ""
echo "Mutation 134: Cross-environment route changes provider in place"
FIX=$(fixture_copy "directory-provider-change-in-place")
mutate_directory_fixture "$FIX" 'data["cloning"]["provider_change_in_place"]=True'
expect_fail "provider change in place" "cannot change provider in place" "$FIX"

echo ""
echo "Mutation 135: Clone succeeds without fidelity/read-back evidence"
FIX=$(fixture_copy "directory-clone-without-evidence")
mutate_directory_fixture "$FIX" 'data["cloning"]["success_requires_fidelity"]=False; data["cloning"]["success_requires_read_back"]=False'
expect_fail "clone without fidelity/read-back" "requires fidelity/read-back" "$FIX"

echo ""
echo "Mutation 136: Move stops source before target commit"
FIX=$(fixture_copy "directory-source-stop-first")
mutate_directory_fixture "$FIX" 'data["move_trace"]=["capture","source_stop_release","transfer","project","validate","target_commit","lineage_publish"]'
expect_fail "source stop before target commit" "commit target and lineage before source stop/release" "$FIX"

echo ""
echo "Mutation 137: Launch example permits shell concatenation"
FIX=$(fixture_copy "directory-shell-concatenation")
mutate_directory_fixture "$FIX" 'data["security"]["launch"]["shell_concatenation"]=True'
expect_fail "shell-concatenated launch" "forbids shell concatenation" "$FIX"

echo ""
echo "Mutation 138: Default directory output contains raw transcript"
FIX=$(fixture_copy "directory-default-raw-transcript")
mutate_directory_fixture "$FIX" 'data["interfaces"]["default_contains_raw_transcript"]=True'
expect_fail "raw transcript in default output" "default output must exclude raw transcript" "$FIX"

echo ""
echo "Mutation 139: Unsupported v0.4 implementation claim in README"
FIX=$(fixture_copy "directory-unsupported-readme-claim")
printf '\nAX v0.4.3 directory implementation is shipped and available.\n' >> "$FIX/README.md"
refresh_frozen_document_digest "$FIX" "README.md"
expect_fail "unsupported README implementation claim" "README/release claim is not supported by SPEC and fixtures" "$FIX"

echo ""
echo "Mutation 140: Publication ownership is stolen from the publication task"
FIX=$(fixture_copy "directory-publication-owner")
mutate_directory_fixture "$FIX" 'data["publication"]["frozen_digest_owner"]="conformance-task"'
expect_fail "directory publication hash ownership" "candidate/release ownership" "$FIX"

mutate_directory_spec() {
  local fixture_dir="$1"
  local mutation="$2"
  python3 - "$fixture_dir" "$mutation" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "SPEC.md"
before = path.read_text(encoding="utf-8")
scope = {"text": before}
exec(sys.argv[2], scope)
after = scope["text"]
if after == before:
    raise SystemExit("directory SPEC mutation made no change")
path.write_text(after, encoding="utf-8")
PY
}

echo ""
echo "Mutation 141: SPEC drops Directory Node operation registry authority"
FIX=$(fixture_copy "directory-spec-node-registry")
mutate_directory_spec "$FIX" 'text=text.replace("The exact operation registry and bodies are:", "The illustrative operation registry and bodies are:", 1)'
expect_fail "SPEC Directory Node registry regression" "directory gate directory_node: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 142: SPEC narrows RPC 3 hello to 23 keys"
FIX=$(fixture_copy "directory-spec-hello-map")
mutate_directory_spec "$FIX" 'text=text.replace("exact 24-key map", "exact 23-key map", 1)'
expect_fail "SPEC RPC 3 hello regression" "directory gate mesh_namespace: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 143: SPEC opens the route registry"
FIX=$(fixture_copy "directory-spec-route-registry")
mutate_directory_spec "$FIX" 'text=text.replace("Continuation routes are the closed registry", "Continuation routes are an open registry", 1)'
expect_fail "SPEC route registry regression" "directory gate route_outcomes: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 144: SPEC drops immutable receipt-chain derivation"
FIX=$(fixture_copy "directory-spec-receipt-chain")
mutate_directory_spec "$FIX" 'text=text.replace("State derives only from a valid\ncontiguous receipt chain", "State may derive from a mutable current row", 1)'
expect_fail "SPEC receipt chain regression" "directory gate receipt_chains: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 145: SPEC weakens mesh disclosure exclusions"
FIX=$(fixture_copy "directory-spec-disclosure")
mutate_directory_spec "$FIX" 'text=text.replace("Raw\nnative/transcript/preview/model payloads, credentials/auth state, terminal\noutput, PIDs/PTYs/sockets, absolute native-store paths, runtime observations,\nand SQLite rows are excluded", "Raw transcript and credential payloads may replicate", 1)'
expect_fail "SPEC disclosure exclusion regression" "directory gate disclosure_policy: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 146: SPEC moves source release before lineage publication"
FIX=$(fixture_copy "directory-spec-move-order")
mutate_directory_spec "$FIX" 'text=text.replace("lineage publication before source\nstop/release", "source stop/release before lineage publication", 1)'
expect_fail "SPEC target-first move regression" "directory gate target_first_move: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 147: SPEC drops remote unmanaged refusal"
FIX=$(fixture_copy "directory-spec-remote-unmanaged")
mutate_directory_spec "$FIX" 'text=text.replace("Remote unmanaged open is always\n<code>unmanaged_remote_forbidden</code>", "Remote unmanaged open is conditionally allowed", 1)'
expect_fail "SPEC remote unmanaged regression" "directory gate remote_unmanaged: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 148: SPEC drops final cloning contract linkage"
FIX=$(fixture_copy "directory-spec-cloning-links")
mutate_directory_spec "$FIX" 'text=text.replace("Cross-environment routes reference the exact v0.3 Clone Capture/Raw Object", "Cross-environment routes use an implementation-defined converter", 1)'
expect_fail "SPEC cloning linkage regression" "directory gate cloning_fidelity: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 149: SPEC opens the typed query registry"
FIX=$(fixture_copy "directory-spec-query-registry")
mutate_directory_spec "$FIX" 'text=text.replace("Read operations are exactly <code>schema</code>", "Read operations include <code>schema</code>", 1)'
expect_fail "SPEC query registry regression" "directory gate interfaces: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 150: SPEC drops explicit environment/provider mapping"
FIX=$(fixture_copy "directory-spec-environment-map")
mutate_directory_spec "$FIX" 'text=text.replace("The initial mapping is exactly <code>claude-code -> claude</code>", "The initial mapping is inferred from equal strings", 1)'
expect_fail "SPEC environment mapping regression" "directory gate environment_mapping: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 151: SPEC drops structured launch boundary"
FIX=$(fixture_copy "directory-spec-launch-boundary")
mutate_directory_spec "$FIX" 'text=text.replace("All native/process launches use structured argv, explicit workspace-derived cwd,\nminimal environment allowlists", "Native/process launches may concatenate a shell command", 1)'
expect_fail "SPEC launch boundary regression" "directory gate security: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 152: SPEC permits silent continuation replan"
FIX=$(fixture_copy "directory-spec-silent-replan")
mutate_directory_spec "$FIX" 'text=text.replace("no silent replan, target/intent/route\nsubstitution", "silent replan and route substitution are allowed", 1)'
expect_fail "SPEC continuation replan regression" "directory gate continuation_plan: SPEC semantic binding missing" "$FIX"

echo ""
echo "Mutation 153: Immutable self-ID vector coverage is narrowed"
FIX=$(fixture_copy "directory-self-id-coverage-narrowed")
mutate_directory_fixture "$FIX" 'data["identity_vectors"]=[row for row in data["identity_vectors"] if row["schema"] != "urn:ax:schema:native-session-observation"]'
expect_fail "directory self-ID vector coverage narrowed" "identity vector coverage must contain exactly one vector for every immutable directory schema" "$FIX"

echo ""
echo "Mutation 154: Canonical self-ID input retains its self field"
FIX=$(fixture_copy "directory-self-id-field-retained")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][0]["canonical_input"]["observation_id"]="sha256:self-minted"'
expect_fail "directory self-ID omission rule" "canonical_input must omit only self field observation_id" "$FIX"

echo ""
echo "Mutation 155: Native Session Observation closed shape admits a field"
FIX=$(fixture_copy "directory-native-observation-open-shape")
mutate_directory_fixture "$FIX" 'data["closed_shapes"]["native_session_observation"].append("native_store_path")'
expect_fail "native observation closed schema narrowed" "closed directory object member registry mismatch or unknown field admitted" "$FIX"

echo ""
echo "Mutation 156: Directory Node preview request body drops head binding"
FIX=$(fixture_copy "directory-preview-body-narrowed")
mutate_directory_fixture "$FIX" 'data["closed_body_unions"]["directory_node_request"]["preview"].remove("expected_head_digest")'
expect_fail "Directory Node request union narrowed" "Directory Node request body union/member registry mismatch" "$FIX"

echo ""
echo "Mutation 157: Structured Claude/Codex session case coverage is narrowed"
FIX=$(fixture_copy "directory-provider-case-narrowed")
mutate_directory_fixture "$FIX" 'data["synthetic_cases"]["provider_sessions"]=[row for row in data["synthetic_cases"]["provider_sessions"] if row["case_id"] != "codex-corrupt"]'
expect_fail "provider session fixture coverage narrowed" "provider session fixtures must cover every Claude/Codex shape exactly once" "$FIX"

echo ""
echo "Mutation 158: Structured route execution coverage omits one route"
FIX=$(fixture_copy "directory-route-case-narrowed")
mutate_directory_fixture "$FIX" 'data["synthetic_cases"]["routes"]=[row for row in data["synthetic_cases"]["routes"] if row["route"] != "managed_remote_attach"]'
expect_fail "route fixture coverage narrowed" "route fixtures must cover every route with its exact outcome matrix" "$FIX"

echo ""
echo "Mutation 159: Crash matrix omits post-commit lost response"
FIX=$(fixture_copy "directory-crash-point-narrowed")
mutate_directory_fixture "$FIX" 'data["synthetic_cases"]["crash_points"]=[row for row in data["synthetic_cases"]["crash_points"] if not (row["step"] == "target_commit" and row["position"] == "after")]'
expect_fail "crash-point fixture coverage narrowed" "crash fixtures must cover before/after every durable step with same-chain recovery" "$FIX"

echo ""
echo "Mutation 160: RPC hello retains the right key with a stale version"
FIX=$(fixture_copy "directory-hello-version-narrowed")
mutate_directory_fixture "$FIX" 'data["mesh"]["hello_contracts"]["session_record"]=["1.0.0", "2.0.0"]'
expect_fail "RPC hello version map narrowed" "RPC 3 hello contract version map mismatch" "$FIX"

echo ""
echo "Mutation 161: directory_record membership omits one immutable schema"
FIX=$(fixture_copy "directory-namespace-membership-narrowed")
mutate_directory_fixture "$FIX" 'data["mesh"]["directory_schemas"].remove("urn:ax:schema:session-enrichment-job-receipt")'
expect_fail "directory namespace membership narrowed" "namespace membership must contain the exact ten immutable directory schemas" "$FIX"

echo ""
echo "Mutation 162: Operation receipt transition oracle omits uncertain recovery"
FIX=$(fixture_copy "directory-receipt-transition-narrowed")
mutate_directory_fixture "$FIX" 'data["receipt_cases"]["operation_transitions"]["uncertain"].remove("succeeded")'
expect_fail "operation receipt transition oracle narrowed" "Directory Operation Receipt transition oracle mismatch" "$FIX"

echo ""
echo "Mutation 163: Directory Query result body drops its partial marker"
FIX=$(fixture_copy "directory-query-result-narrowed")
mutate_directory_fixture "$FIX" 'data["closed_body_unions"]["query_results"]["directory_entries"].remove("partial")'
expect_fail "Directory Query result union narrowed" "Directory Query result union/member registry mismatch" "$FIX"

echo ""
echo "Mutation 164: SPEC-only closed authentication enum is widened"
FIX=$(fixture_copy "directory-spec-auth-enum-widened")
mutate_directory_spec "$FIX" 'text=text.replace("available|missing|expired|unknown", "available|missing|expired|unknown|admin")'
refresh_frozen_spec_digest "$FIX"
expect_fail "SPEC-only closed enum widening" "exact normative directory schema registry drift in directory records and query (members/types/enums)" "$FIX"

echo ""
echo "Mutation 165: SPEC-only Environment Observation member is removed"
FIX=$(fixture_copy "directory-spec-member-removed")
mutate_directory_spec "$FIX" 'text=text.replace("<code>observed_at</code>, <code>extensions</code> | diagnostic timestamp and reverse-DNS object |", "<code>observed_at</code> | diagnostic timestamp |", 1)'
refresh_frozen_spec_digest "$FIX"
expect_fail "SPEC-only closed schema member removal" "exact normative directory schema registry drift in directory records and query (members/types/enums)" "$FIX"

echo ""
echo "Mutation 166: SPEC-only Environment Observation member type changes"
FIX=$(fixture_copy "directory-spec-member-type-changed")
mutate_directory_spec "$FIX" 'text=text.replace("<code>runtime_status</code> | <code>available|degraded|unavailable</code> |", "<code>runtime_status</code> | <code>string</code> |", 1)'
refresh_frozen_spec_digest "$FIX"
expect_fail "SPEC-only closed schema member type change" "exact normative directory schema registry drift in directory records and query (members/types/enums)" "$FIX"

echo ""
echo "Mutation 167: Standalone traceability link uses a stale SPEC anchor"
FIX=$(fixture_copy "traceability-stale-spec-anchor")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "STANDALONE_TO_AX_TRACEABILITY.md"
text = path.read_text(encoding="utf-8")
old = "SPEC.md#1314-cross-environment-clone"
new = "SPEC.md#1314-cross-environment-session-cloning"
if old not in text:
    raise SystemExit("traceability anchor mutation source missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
refresh_frozen_document_digest "$FIX" "STANDALONE_TO_AX_TRACEABILITY.md"
expect_fail "traceability stale SPEC anchor" "STANDALONE_TO_AX_TRACEABILITY.md: broken anchor '1314-cross-environment-session-cloning' in link to SPEC.md" "$FIX"

echo ""
echo "Mutation 168: Positive directory vector contains a shortened digest"
FIX=$(fixture_copy "directory-vector-short-digest")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][0]["canonical_input"]["installation_id"]="sha256:10"'
expect_fail "directory vector shortened digest" "schema-directed digest validation failed" "$FIX"

echo ""
echo "Mutation 169: Positive directory vector timestamp loses millisecond precision"
FIX=$(fixture_copy "directory-vector-coarse-timestamp")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][0]["canonical_input"]["observed_at"]="2026-08-27T00:00:00Z"'
expect_fail "directory vector timestamp without milliseconds" "timestamp must be UTC RFC 3339 with at least millisecond precision" "$FIX"

echo ""
echo "Mutation 170: Environment Observation uses non-AX darwin platform"
FIX=$(fixture_copy "directory-vector-darwin-platform")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][0]["canonical_input"]["platform"]="darwin"'
expect_fail "directory vector non-AX platform" "platform must use the AX enum macos|linux|wsl2|windows" "$FIX"

echo ""
echo "Mutation 171: Enrichment profile generator discriminators disagree"
FIX=$(fixture_copy "directory-generator-discriminator-mismatch")
mutate_directory_fixture "$FIX" 'data["identity_vectors"][5]["canonical_input"]["generator"]["kind"]="remote_model"'
expect_fail "enrichment generator discriminator mismatch" "generator_kind must equal generator.kind" "$FIX"

echo ""
echo "Mutation 172: Directory Node response success admits both body and error"
FIX=$(fixture_copy "directory-response-body-and-error")
mutate_directory_fixture "$FIX" 'data["directory_node"]["response_union"]["success"]="body_and_error"'
expect_fail "Directory Node response body and error" "Directory Node response must be body XOR error" "$FIX"

echo ""
echo "Mutation 173: Directory Query reuses an operation index"
FIX=$(fixture_copy "directory-query-duplicate-index")
mutate_directory_fixture "$FIX" 'data["interfaces"]["query_correlation"]["request"][1]["operation_index"]=0'
expect_fail "Directory Query duplicate operation index" "operation_index must be unique, contiguous, and equal array position" "$FIX"

echo ""
echo "Mutation 174: QueryResult name no longer echoes its request"
FIX=$(fixture_copy "directory-query-result-name-mismatch")
mutate_directory_fixture "$FIX" 'data["interfaces"]["query_correlation"]["response"][1]["operation_name"]="sessions"'
expect_fail "QueryResult request correlation mismatch" "QueryResult must preserve request order and exact operation index/name correlation" "$FIX"

echo ""
echo "Mutation 175: Direct unmanaged cross-environment move is admitted"
FIX=$(fixture_copy "directory-unmanaged-move-admitted")
mutate_directory_fixture "$FIX" 'data["remote_unmanaged"]["move_allowed"]=True'
expect_fail "direct unmanaged move admitted" "direct unmanaged move is forbidden" "$FIX"

echo ""
echo "Mutation 176: Lineage representative is selected by wall clock"
FIX=$(fixture_copy "directory-lineage-clock-representative")
mutate_directory_fixture "$FIX" 'data["lineage"]["representative"]["clock_is_tiebreaker"]=True'
expect_fail "lineage representative wall-clock selection" "non-authoritative deterministic representative" "$FIX"

echo ""
echo "Mutation 177: Agent CLI leaf registry omits mutation surface"
FIX=$(fixture_copy "directory-agent-cli-leaf-missing")
mutate_directory_fixture "$FIX" 'data["interfaces"]["agent_cli_leaves"].remove("m")'
expect_fail "agent CLI exact leaf registry narrowed" "human and agent CLI leaf registries mismatch" "$FIX"

echo ""
echo "Mutation 178: Cross-environment move admits an unmanaged source"
FIX=$(fixture_copy "directory-route-unmanaged-move")
mutate_directory_fixture "$FIX" 'next(row for row in data["synthetic_cases"]["routes"] if row["route"] == "cross_environment_move")["source_kind"]="managed_or_unmanaged"'
expect_fail "cross-environment move source-kind widened" "exact outcome matrix and source-kind" "$FIX"

echo ""
echo "Mutation 179: Non-prefixed value bypasses a digest-typed schema path"
FIX=$(fixture_copy "directory-schema-path-non-digest")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'row["canonical_input"]["installation_id"]="not-a-digest"'
expect_fail "schema-path digest bypass" "schema-directed digest validation failed" "$FIX"

echo ""
echo "Mutation 180: Malformed UUID bypasses a UUIDv7-typed schema path"
FIX=$(fixture_copy "directory-schema-path-bad-uuid")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'row["canonical_input"]["host_id"]="not-a-uuid"'
expect_fail "schema-path UUIDv7 bypass" "schema-directed UUIDv7 validation failed" "$FIX"

echo ""
echo "Mutation 181: Reversed typed array bypasses sorted-unique validation"
FIX=$(fixture_copy "directory-schema-path-unsorted-array")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-enrichment-profile" 'row["canonical_input"]["input_classes"].reverse()'
expect_fail "schema-path sorted-unique bypass" "schema-directed sorted-unique validation failed" "$FIX"

echo ""
echo "Mutation 182: Regex-shaped impossible calendar timestamp is accepted"
FIX=$(fixture_copy "directory-schema-path-impossible-date")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'row["canonical_input"]["observed_at"]="2026-02-31T00:00:00.000Z"'
expect_fail "schema-path impossible calendar date" "timestamp is not a real UTC calendar instant" "$FIX"

echo ""
echo "Mutation 183: Directory Node 1 is rebound to Request 2 wire values"
FIX=$(fixture_copy "directory-v1-rebound-to-request-v2")
mutate_directory_fixture "$FIX" 'data["directory_node"]["protocol_bindings"]["1.0.0"]["request_version"]="2.0.0"'
expect_fail "Directory Node 1 request-major rebinding" "Directory Node protocol/request major binding mismatch" "$FIX"

echo ""
echo "Mutation 184: Directory Node 2 loses the AX platform registry"
FIX=$(fixture_copy "directory-v2-platform-regression")
mutate_directory_fixture "$FIX" 'data["directory_node"]["protocol_bindings"]["2.0.0"]["probe_platforms"]=["darwin", "linux", "windows"]'
expect_fail "Directory Node 2 platform regression" "Directory Node 2 probe platform registry must be macos|linux|wsl2|windows" "$FIX"

echo ""
echo "Mutation 185: Malformed UUIDv4 bypasses the common-type oracle"
FIX=$(fixture_copy "directory-common-type-bad-uuid4")
mutate_directory_fixture "$FIX" 'data["common_type_cases"]["uuidv4"]="550e8400-e29b-71d4-a716-446655440000"'
expect_fail "common-type UUIDv4 bypass" "schema-directed UUIDv4 validation failed" "$FIX"

echo ""
echo "Mutation 186: Nested structured sorted-unique array is reversed"
FIX=$(fixture_copy "directory-nested-jcs-array-unsorted")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["contract_assertions"]=[{"contract_id":"urn:z","exact_version":"1.0.0","extensions":{}},{"contract_id":"urn:a","exact_version":"1.0.0","extensions":{}}]'
expect_fail "nested structured sorted-unique bypass" "schema-directed sorted-unique validation failed" "$FIX"

echo ""
echo "Mutation 187: Nested scalar sorted-unique array contains a duplicate"
FIX=$(fixture_copy "directory-nested-array-duplicate")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-enrichment-profile" 'row["canonical_input"]["provider_ids"]=["codex", "codex"]'
expect_fail "nested scalar sorted-unique duplicate" "schema-directed sorted-unique validation failed" "$FIX"

echo ""
echo "Mutation 188: Contract registry drops immutable Directory Node Request v1"
FIX=$(fixture_copy "directory-contract-history-narrowed")
mutate_directory_spec "$FIX" 'text=text.replace("| Directory Node request | <code>urn:ax:schema:session-directory-node-request</code> | <code>1.0.0</code>, <code>2.0.0</code> for the AX platform vocabulary |", "| Directory Node request | <code>urn:ax:schema:session-directory-node-request</code> | <code>2.0.0</code> for the AX platform vocabulary |", 1)'
refresh_frozen_spec_digest "$FIX"
expect_fail "Directory Node immutable contract history narrowed" "Directory Node contract history missing immutable v1/v2 versions" "$FIX"

echo ""
echo "Mutation 189: Required nested continuation-step digest is omitted"
FIX=$(fixture_copy "directory-required-nested-digest-missing")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'del row["canonical_input"]["steps"][0]["input_digest"]'
expect_fail "required nested schema path omission" "required schema-directed path missing" "$FIX"

echo ""
echo "Mutation 190: Required nullable generator digest member is omitted"
FIX=$(fixture_copy "directory-required-nullable-digest-missing")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-enrichment-profile" 'del row["canonical_input"]["generator"]["prompt_digest"]'
expect_fail "required nullable schema path omission" "required schema-directed path missing" "$FIX"

echo ""
echo "Mutation 191: Directory Node bootstrap fixture coverage omits v1-only"
FIX=$(fixture_copy "directory-bootstrap-case-narrowed")
mutate_directory_fixture "$FIX" 'data["directory_node"]["negotiation_cases"]=[case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] != "v1-only"]'
expect_fail "Directory Node bootstrap case coverage narrowed" "bootstrap fixtures must contain exact v2-selected, v2-to-v1, v1-only, and no-common-major cases" "$FIX"

echo ""
echo "Mutation 192: Directory Node bootstrap attempts majors in ascending order"
FIX=$(fixture_copy "directory-bootstrap-major-order")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["caller_supported_majors"]=[1, 2]'
expect_fail "Directory Node bootstrap descending-major gate" "caller majors must be unique descending supported majors" "$FIX"

echo ""
echo "Mutation 193: Directory Node fallback reuses the failed v2 process"
FIX=$(fixture_copy "directory-bootstrap-process-reuse")
mutate_directory_fixture "$FIX" 'case=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1"); case["attempts"][1]["process_id"]=case["attempts"][0]["process_id"]'
expect_fail "Directory Node bootstrap fresh-process gate" "must use a fresh process for every attempt" "$FIX"

echo ""
echo "Mutation 194: Authentication failure is admitted as a downgrade trigger"
FIX=$(fixture_copy "directory-bootstrap-auth-downgrade")
mutate_directory_fixture "$FIX" 'attempt=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["attempts"][0]; attempt["error"]["code"]="authentication_failed"'
expect_fail "Directory Node bootstrap exact downgrade trigger" "downgrade requires exact incompatible_protocol/6/non-retryable response and exit" "$FIX"

echo ""
echo "Mutation 195: Directory Node fallback accepts a wrong request echo"
FIX=$(fixture_copy "directory-bootstrap-wrong-echo")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["attempts"][0]["response_echo_request_id"]="0198f4c8-9000-7000-8000-000000000099"'
expect_fail "Directory Node bootstrap exact echo gate" "must exactly echo request identity" "$FIX"

echo ""
echo "Mutation 196: No-common-major bootstrap reports success"
FIX=$(fixture_copy "directory-bootstrap-no-common-success")
mutate_directory_fixture "$FIX" 'case=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "no-common-major"); case["expected_error"]=None; case["expected_exit_code"]=0'
expect_fail "Directory Node no-common-major termination gate" "terminal outcome mismatch" "$FIX"

echo ""
echo "Mutation 197: Directory Node bootstrap admits cross-major coercion"
FIX=$(fixture_copy "directory-bootstrap-cross-major-coercion")
mutate_directory_fixture "$FIX" 'data["directory_node"]["negotiation"]["cross_major_coercion"]=True'
expect_fail "Directory Node cross-major coercion gate" "dual-stack negotiation registry mismatch" "$FIX"

echo ""
echo "Mutation 198: CHANGELOG restores v0.4.1 as an unsuperseded baseline"
FIX=$(fixture_copy "changelog-v041-current-baseline")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "CHANGELOG.md"
text = path.read_text(encoding="utf-8")
old = "; v0.4.2 now supersedes that historical claim, so\n  v0.4.1 is not the current implementation baseline."
if old not in text:
    raise SystemExit("v0.4.1 supersession annotation missing before mutation")
path.write_text(text.replace(old, ".", 1), encoding="utf-8")
PY
refresh_frozen_document_digest "$FIX" "CHANGELOG.md"
expect_fail "CHANGELOG v0.4.1 supersession gate" "baseline history must be explicitly superseded by v0.4.2" "$FIX"

echo ""
echo "Mutation 199: Directory Node fallback accepts a wrong protocol-version echo"
FIX=$(fixture_copy "directory-bootstrap-wrong-version-echo")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["attempts"][0]["response_echo_protocol_version"]="1.0.0"'
expect_fail "Directory Node bootstrap exact version echo gate" "must exactly echo request identity" "$FIX"

echo ""
echo "Mutation 200: Selected v2 manifest omits the selected protocol version"
FIX=$(fixture_copy "directory-bootstrap-manifest-selected-version-missing")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["manifest_supported_protocol_versions"]=["1.0.0"]'
expect_fail "Directory Node bootstrap manifest selected-version gate" "selected-major manifest success framing mismatch" "$FIX"

echo ""
echo "Mutation 201: Retryable incompatible-protocol error is admitted as a downgrade trigger"
FIX=$(fixture_copy "directory-bootstrap-retryable-downgrade")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["attempts"][0]["error"]["retryable"]=True'
expect_fail "Directory Node bootstrap non-retryable downgrade gate" "downgrade requires exact incompatible_protocol/6/non-retryable response and exit" "$FIX"

echo ""
echo "Mutation 202: Downgrade response exit and process exit disagree"
FIX=$(fixture_copy "directory-bootstrap-exit-mismatch")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-to-v1")["attempts"][0]["exit_code"]=7'
expect_fail "Directory Node bootstrap response/process exit agreement gate" "downgrade requires exact incompatible_protocol/6/non-retryable response and exit" "$FIX"

echo ""
echo "Mutation 203: Required Directory Node bootstrap case labels are swapped"
FIX=$(fixture_copy "directory-bootstrap-case-label-swap")
mutate_directory_fixture "$FIX" 'a=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected"); b=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only"); a["case_id"], b["case_id"]=b["case_id"], a["case_id"]'
expect_fail "Directory Node bootstrap named-scenario gate" "must match its exact named caller/peer scenario" "$FIX"

echo ""
echo "Mutation 204: Request and echo share a non-UUID identity"
FIX=$(fixture_copy "directory-bootstrap-invalid-request-id")
mutate_directory_fixture "$FIX" 'attempt=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]; attempt["request_id"]="not-a-uuid"; attempt["response_echo_request_id"]="not-a-uuid"'
expect_fail "Directory Node bootstrap UUIDv7 request identity gate" "request must be closed schema-valid manifest input" "$FIX"

echo ""
echo "Mutation 205: Request and echo use a non-manifest operation"
FIX=$(fixture_copy "directory-bootstrap-non-manifest-request")
mutate_directory_fixture "$FIX" 'attempt=next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]; attempt["request_operation"]="probe"; attempt["response_echo_operation"]="probe"'
expect_fail "Directory Node bootstrap manifest-operation gate" "request must be closed schema-valid manifest input" "$FIX"

echo ""
echo "Mutation 206: Manifest bootstrap request body is non-empty"
FIX=$(fixture_copy "directory-bootstrap-nonempty-request-body")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["request_body"]={"unexpected": True}'
expect_fail "Directory Node bootstrap empty-body gate" "request must be closed schema-valid manifest input" "$FIX"

echo ""
echo "Mutation 207: Bootstrap attempt admits an unknown field"
FIX=$(fixture_copy "directory-bootstrap-unknown-attempt-field")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["unexpected"]=True'
expect_fail "Directory Node bootstrap closed-attempt gate" "must contain the exact closed attempt fields" "$FIX"

echo ""
echo "Mutation 208: Boolean masquerades as caller major 1"
FIX=$(fixture_copy "directory-bootstrap-boolean-caller-major")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only")["caller_supported_majors"]=[True]'
expect_fail "Directory Node bootstrap strict caller-major type gate" "caller majors must be unique descending supported majors" "$FIX"

echo ""
echo "Mutation 209: Float masquerades as peer major 1"
FIX=$(fixture_copy "directory-bootstrap-noninteger-peer-major")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only")["peer_supported_majors"]=[1.0]'
expect_fail "Directory Node bootstrap strict peer-major type gate" "peer majors must be unique descending positive majors" "$FIX"

echo ""
echo "Mutation 210: Bootstrap request uses the wrong schema identity"
FIX=$(fixture_copy "directory-bootstrap-wrong-request-schema")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["request_schema"]="urn:ax:schema:session-directory-node-response"'
expect_fail "Directory Node bootstrap request-schema gate" "request must be closed schema-valid manifest input" "$FIX"

echo ""
echo "Mutation 211: Boolean masquerades as a valid request deadline"
FIX=$(fixture_copy "directory-bootstrap-boolean-deadline")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["request_deadline_ms"]=True'
expect_fail "Directory Node bootstrap uint53 deadline gate" "request must be closed schema-valid manifest input" "$FIX"

echo ""
echo "Mutation 212: Bootstrap response uses the wrong schema identity"
FIX=$(fixture_copy "directory-bootstrap-wrong-response-schema")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["response_schema"]="urn:ax:schema:session-directory-node-request"'
expect_fail "Directory Node bootstrap response-schema gate" "must exactly echo request identity" "$FIX"

echo ""
echo "Mutation 213: Boolean masquerades as request major 1"
FIX=$(fixture_copy "directory-bootstrap-boolean-request-major")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only")["attempts"][0]["request_major"]=True'
expect_fail "Directory Node bootstrap strict request-major type gate" "must exactly echo request identity" "$FIX"

echo ""
echo "Mutation 214: Float masquerades as response echo major 1"
FIX=$(fixture_copy "directory-bootstrap-noninteger-response-major")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only")["attempts"][0]["response_echo_major"]=1.0'
expect_fail "Directory Node bootstrap strict response-major type gate" "must exactly echo request identity" "$FIX"

echo ""
echo "Mutation 215: False masquerades as successful process exit 0"
FIX=$(fixture_copy "directory-bootstrap-boolean-process-exit")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["attempts"][0]["exit_code"]=False'
expect_fail "Directory Node bootstrap strict process-exit type gate" "selected-major manifest success framing mismatch" "$FIX"

echo ""
echo "Mutation 216: False masquerades as successful terminal exit 0"
FIX=$(fixture_copy "directory-bootstrap-boolean-terminal-exit")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v2-selected")["expected_exit_code"]=False'
expect_fail "Directory Node bootstrap strict terminal-exit type gate" "terminal outcome mismatch" "$FIX"

echo ""
echo "Mutation 217: True masquerades as selected major 1"
FIX=$(fixture_copy "directory-bootstrap-boolean-selected-major")
mutate_directory_fixture "$FIX" 'next(case for case in data["directory_node"]["negotiation_cases"] if case["case_id"] == "v1-only")["expected_selected_major"]=True'
expect_fail "Directory Node bootstrap strict selected-major type gate" "terminal outcome mismatch" "$FIX"
echo "Mutation 218: Required nullable WorkspaceRoute transfer manifest member is omitted"
FIX=$(fixture_copy "directory-workspace-transfer-member-missing")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'del row["canonical_input"]["workspace"]["transfer_manifest_id"]'
expect_fail "WorkspaceRoute required T|null member omission" "required schema-directed path missing" "$FIX"

echo ""
echo "Mutation 219: Required AdapterBuild executable digest member is omitted"
FIX=$(fixture_copy "directory-adapter-build-executable-missing")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-inventory-batch" 'del row["canonical_input"]["adapter_builds"][0]["executable_sha256"]'
expect_fail "AdapterBuild required executable digest omission" "required schema-directed path missing" "$FIX"

echo ""
echo "Mutation 220: Conditional source lease carries a malformed UUIDv4"
FIX=$(fixture_copy "directory-source-lease-malformed-uuid4")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["source_lease"]={"epoch":1,"lease_id":"0198f4c8-4444-7444-8444-1234567890ab","holder_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab"}'
expect_fail "LeaseExpectation UUIDv4 type gate" "schema-directed UUIDv4 validation failed" "$FIX"

echo ""
echo "Mutation 221: Conditional source lease uses an array parent"
FIX=$(fixture_copy "directory-source-lease-wrong-container")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["source_lease"]=[]'
expect_fail "LeaseExpectation conditional parent shape" "recursive closed shape lease_expectation must be an object" "$FIX"

echo ""
echo "Mutation 222: Environment capability map drops one of its eight keys"
FIX=$(fixture_copy "directory-capability-map-cardinality")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'del row["canonical_input"]["capabilities"]["native_resume"]'
expect_fail "CapabilityResult exact eight-entry map" "recursive closed shape map cardinality/key mismatch" "$FIX"

echo ""
echo "Mutation 223: CapabilityResult omits its required observed timestamp"
FIX=$(fixture_copy "directory-capability-value-shape")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'del row["canonical_input"]["capabilities"]["native_resume"]["observed_at"]'
expect_fail "CapabilityResult closed value shape" "recursive closed shape capability_result member mismatch" "$FIX"

echo ""
echo "Mutation 224: CapabilityResult status bypasses its typed enum"
FIX=$(fixture_copy "directory-capability-value-type")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'row["canonical_input"]["capabilities"]["native_resume"]["status"]=1'
expect_fail "CapabilityResult typed status leaf" "schema-directed enum validation failed" "$FIX"

echo ""
echo "Mutation 225: Capability map wildcard is replaced with an array"
FIX=$(fixture_copy "directory-capability-map-wrong-container")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:environment-observation" 'row["canonical_input"]["capabilities"]=[]'
expect_fail "CapabilityResult map wildcard container" "recursive closed shape map required" "$FIX"

echo ""
echo "Mutation 226: EnvironmentTuple omits one of its exact six members"
FIX=$(fixture_copy "directory-environment-tuple-member-missing")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'del row["canonical_input"]["target"]["environment_tuple"]["adapter_version"]'
expect_fail "EnvironmentTuple exact six-member shape" "recursive closed shape environment_tuple member mismatch" "$FIX"

echo ""
echo "Mutation 227: EnvironmentTuple adapter version bypasses its typed leaf"
FIX=$(fixture_copy "directory-environment-tuple-leaf-type")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["target"]["environment_tuple"]["adapter_version"]={}'
expect_fail "EnvironmentTuple typed SemVer leaf" "schema-directed SemVer validation failed" "$FIX"

echo ""
echo "Mutation 228: EnvironmentTuple object is replaced with an array"
FIX=$(fixture_copy "directory-environment-tuple-wrong-container")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-directory-operation-receipt" 'row["canonical_input"]["validated_target"]["target"]["environment_tuple"]=[]'
expect_fail "EnvironmentTuple object container" "recursive closed shape environment_tuple must be an object" "$FIX"

echo ""
echo "Mutation 229: AdapterBuild array wildcard is replaced with a map"
FIX=$(fixture_copy "directory-adapter-build-wrong-container")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-inventory-batch" 'row["canonical_input"]["adapter_builds"]={}'
expect_fail "AdapterBuild array wildcard container" "recursive closed shape array required" "$FIX"

echo ""
echo "Mutation 230: Nested ContinuationStep admits an unknown member"
FIX=$(fixture_copy "directory-continuation-step-unknown-member")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["steps"][0]["unknown"]=True'
expect_fail "ContinuationStep recursively closed shape" "recursive closed shape continuation_step member mismatch" "$FIX"

echo ""
echo "Mutation 231: Conditional source lease carries a null epoch leaf"
FIX=$(fixture_copy "directory-source-lease-null-epoch")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["source_lease"]={"epoch":None,"lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","holder_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab"}'
expect_fail "LeaseExpectation non-null epoch leaf" "null is forbidden by schema-directed common type" "$FIX"

echo ""
echo "Mutation 232: Conditional source lease carries a null lease UUID leaf"
FIX=$(fixture_copy "directory-source-lease-null-lease-id")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["source_lease"]={"epoch":1,"lease_id":None,"holder_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab"}'
expect_fail "LeaseExpectation non-null lease_id leaf" "null is forbidden by schema-directed common type" "$FIX"

echo ""
echo "Mutation 233: Conditional source lease carries a null holder host leaf"
FIX=$(fixture_copy "directory-source-lease-null-holder-host-id")
mutate_directory_vector_and_rehash "$FIX" "urn:ax:schema:session-continuation-plan" 'row["canonical_input"]["source_lease"]={"epoch":1,"lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","holder_host_id":None}'
expect_fail "LeaseExpectation non-null holder_host_id leaf" "null is forbidden by schema-directed common type" "$FIX"

echo ""
echo "Mutation 234: Background caller creates a credential-dependent tmux server"
FIX=$(fixture_copy "v043-unsafe-server-create")
mutate_v043_fixture "$FIX" "unsafe-server-create"
expect_fail "v0.4.3 unsafe server creation" "background caller may contact only an existing broker" "$FIX"

echo ""
echo "Mutation 235: Functional sentinel is treated as sufficient without provider auth"
FIX=$(fixture_copy "v043-sentinel-only")
mutate_v043_fixture "$FIX" "sentinel-only"
expect_fail "v0.4.3 sentinel-only attestation" "sentinel and separate provider-auth smoke are both required" "$FIX"

echo ""
echo "Mutation 236: Unique route is allowed to mutate ownership implicitly"
FIX=$(fixture_copy "v043-implicit-mutating-route")
mutate_v043_fixture "$FIX" "implicit-mutating-route"
expect_fail "v0.4.3 implicit mutating route" "automatic route must be unique and non-mutating" "$FIX"

echo ""
echo "Mutation 237: ax sync --all changes ownership"
FIX=$(fixture_copy "v043-ownership-changing-sync")
mutate_v043_fixture "$FIX" "ownership-changing-sync"
expect_fail "v0.4.3 ownership-changing sync" "sync must not change ownership or launch a runtime" "$FIX"

echo ""
echo "Mutation 238: Git closure omits submodules"
FIX=$(fixture_copy "v043-incomplete-git-closure")
mutate_v043_fixture "$FIX" "incomplete-git-closure"
expect_fail "v0.4.3 incomplete Git closure" "complete Git closure registry mismatch" "$FIX"

echo ""
echo "Mutation 239: Ownership commits before destination broker/auth readiness"
FIX=$(fixture_copy "v043-unsafe-preflight-order")
mutate_v043_fixture "$FIX" "unsafe-preflight-order"
expect_fail "v0.4.3 unsafe preflight ordering" "graceful destination readiness/stop/commit/runtime ordering mismatch" "$FIX"

echo ""
echo "Mutation 240: Dedicated tmux socket becomes replicable"
FIX=$(fixture_copy "v043-socket-replication")
mutate_v043_fixture "$FIX" "socket-replication"
expect_fail "v0.4.3 socket replication" "socket replication must be forbidden" "$FIX"

echo ""
echo "Mutation 241: M0 advertises a public stable plugin SDK"
FIX=$(fixture_copy "v043-premature-sdk")
mutate_v043_fixture "$FIX" "premature-sdk"
expect_fail "v0.4.3 premature SDK stability" "M0 MUST NOT advertise a public stable plugin SDK" "$FIX"

echo ""
echo "Mutation 242: Force takeover falsely claims a verified source-process stop"
FIX=$(fixture_copy "v043-force-source-stop-claim")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "SPEC.md"
text = path.read_text(encoding="utf-8")
old = "Force takeover MUST NOT claim or require a verified source-process stop."
new = "Force takeover MAY claim or require a verified source-process stop."
if text.count(old) != 1:
    raise SystemExit("force source-stop marker cardinality mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
refresh_frozen_spec_digest "$FIX"
expect_fail "v0.4.3 force source-stop exception" "Section 13.7 must retain the no-source-stop force exception" "$FIX"

echo ""
echo "Mutation 243: Remote attach loses its terminating production-diagram boundary"
FIX=$(fixture_copy "v043-remote-attach-fallthrough")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "diagrams" / "plantuml" / "session_directory_continuation.puml"
text = path.read_text(encoding="utf-8")
old = "break Remote attach terminates without target finalization"
new = "group Remote attach continues into target finalization"
if text.count(old) != 1:
    raise SystemExit("remote-attach termination marker cardinality mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
expect_fail "v0.4.3 remote attach finalization isolation" "remote attach must terminate before mutating target finalization" "$FIX"

echo ""
echo "Mutation 244: Unique automatic attach/resume bypasses execution-time revalidation"
FIX=$(fixture_copy "v043-auto-route-revalidation-bypass")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "diagrams" / "plantuml" / "session_directory_continuation.puml"
text = path.read_text(encoding="utf-8")
old = "TUI -> Planner: execute unique non-mutating route"
new = """TUI -> Planner: execute unique non-mutating route
    Planner -> AX: attach/resume before execution-time revalidation
    break Unique automatic route bypasses execution-time revalidation
        AX --> Operator: attached/resumed without fresh facts
    end"""
if text.count(old) != 1:
    raise SystemExit("unique-route execution marker cardinality mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
expect_fail "v0.4.3 automatic-route execution revalidation" "unique automatic attach/resume must pass through execution-time revalidation" "$FIX"

echo ""
echo "Mutation 245: Local current-owner resume falls through ownership finalization"
FIX=$(fixture_copy "v043-local-resume-finalization-fallthrough")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "diagrams" / "plantuml" / "session_directory_continuation.puml"
text = path.read_text(encoding="utf-8")
old = "break Current-owner resume terminates without ownership finalization"
new = "group Current-owner resume continues into ownership finalization"
if text.count(old) != 1:
    raise SystemExit("local-resume termination marker cardinality mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
expect_fail "v0.4.3 local-resume finalization isolation" "local current-owner resume must terminate without ownership transfer/finalization" "$FIX"

echo ""
echo "Mutation 246: Non-macOS ownership target is forced through Aqua broker"
FIX=$(fixture_copy "v043-aqua-broker-unconditional")
python3 - "$FIX" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "diagrams" / "plantuml" / "session_directory_continuation.puml"
text = path.read_text(encoding="utf-8")
old = "opt Ownership-creating target is macOS"
new = "group Every ownership-creating target, including non-macOS"
if text.count(old) != 1:
    raise SystemExit("ownership-route macOS condition marker cardinality mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
expect_fail "v0.4.3 platform-scoped Aqua broker" "Aqua broker readiness must be conditional on a macOS target" "$FIX"

echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed out of $TOTAL mutations"
if [ $FAIL -ne 0 ]; then
  echo "Expected-red suite FAILED"
  exit 1
fi
echo "Expected-red suite PASSED — all mutations correctly rejected with actionable diagnostics."
