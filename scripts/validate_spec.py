#!/usr/bin/env python3
"""Public, repository-only validation for the normative ax v0.2.1 specification.

Incorporates both retained validators (validate_spec_contracts + validate_second_rework)
and adds publication/metadata, anchor, matrix, and security closure for v0.2.1.
Repository-only: no ax binary, provider CLI, or task-board runtime required.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import sys
import tomllib
from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"
README = ROOT / "README.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
DIAGRAMS_README = ROOT / "diagrams" / "README.md"
VERSION_FILE = ROOT / "VERSION"
LICENSE_FILE = ROOT / "LICENSE"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_NOTES = ROOT / "RELEASE_NOTES.md"
PUBLIC_CLAIM_DOCUMENTS = [SPEC, README, CONTRIBUTING, CHANGELOG, RELEASE_NOTES]
# Frozen v0.2.1 publication prose. Hashes use UTF-8 text with all line endings
# normalized to LF, so the same checkout validates on Unix and Windows. Future
# specification releases must deliberately replace this bounded map after the
# semantic checks and expected-red suite have been reviewed for the new prose.
FROZEN_RELEASE_DOCUMENT_SHA256 = {
    "SPEC.md": "ba8c72fd230e416fd770511f99b2039faf140d25b67534847ab8691133ce229f",
    "README.md": "5db2705e219e07d0c7e75c3cd620b4fe4c793ba8977d1771771b645ce0e7ee27",
    "CONTRIBUTING.md": "a1a518cc245d9688f474b5744a8bda54f09dcda46f77276ef9ea35c565eec277",
    "CHANGELOG.md": "a058495e6d9902b9bdff68ab1940410597e1a2ff1b3d12ea9d3af44198d71e0a",
    "RELEASE_NOTES.md": "f8e6608fb534a26b5ecb2418d0a1f8911c6ecde88b1db4f8fdeec33e30f447f3",
}
RESEARCH = ROOT / ".research" / "260819_muse-antigravity-native-store-contracts.md"
C4_WORKSPACE = ROOT / "diagrams" / "c4" / "workspace.dsl"
C4_MODEL = ROOT / "diagrams" / "c4" / "model.dsl"
C4_VIEWS = ROOT / "diagrams" / "c4" / "views.dsl"
C4_REL = ROOT / "diagrams" / "c4" / "relationships.dsl"
C4_STYLES = ROOT / "diagrams" / "c4" / "styles.dsl"
ARTEFACTS = ROOT / "diagrams" / "artefacts"
PLANTUML_DIR = ROOT / "diagrams" / "plantuml"

EXPECTED_SVG_SHA256 = {
    "mesh_deployment.svg": "0b38e885aac889795b1464ce8227ae6ae858ff2590229a9163a6701d9b99dd8e",
    "session_state.svg": "fae377f21fd374a40c2b831c6ced4e9f61c662a993c0b550d1c9ca0f0c0be507",
    "structurizr-ContainerContext-key.svg": "6424ee4d1ffebef9f37f54a8e5afc47358f9522f4a4908bbfe2cb44144b82dbc",
    "structurizr-ContainerContext.svg": "05eec3faa7f04c8bdc7dc3f70f3c01cc6d99923cc45e502e2828d75ca8fb9e76",
    "structurizr-SystemContext-key.svg": "d2b29e2efb08aa803166c8be5366933359c1b136d97fa01b0eedfce8406b65d1",
    "structurizr-SystemContext.svg": "4509fea3ea56556862757ae43d113908b150acb3ee67843d8640b21618e2a1e4",
    "takeover.svg": "b06f3553a7bc09f316c73bc83169f0b637ebfaa6ff86f9fcd576ec82162b3b55",
}

SAFE_INTEGER = 9_007_199_254_740_991

SELF_FIELDS = {
    "urn:ax:schema:session-record": "record_id",
    "urn:ax:schema:session-event": "event_id",
    "urn:ax:schema:lease": "record_id",
    "urn:ax:schema:checkpoint": "checkpoint_id",
    "urn:ax:schema:provider-identity": "record_id",
    "urn:ax:schema:workspace-group": "record_id",
    "urn:ax:schema:blob": "descriptor_id",
    "urn:ax:schema:transfer-manifest": "manifest_id",
    "urn:ax:schema:materialization-plan": "plan_id",
    "urn:ax:schema:tombstone": "tombstone_id",
    "urn:ax:schema:tombstone-ack": "ack_id",
    "urn:ax:schema:task-board-bundle": "bundle_id",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def blocks(text: str, language: str) -> Iterator[tuple[int, str]]:
    lines = text.splitlines()
    start_marker = f"~~~{language}"
    index = 0
    while index < len(lines):
        if lines[index] != start_marker:
            index += 1
            continue
        start = index + 2
        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index] != "~~~":
            body.append(lines[index])
            index += 1
        if index == len(lines):
            raise ValueError(f"unterminated {language} fence beginning line {start}")
        yield start, "\n".join(body)
        index += 1


def walk(value: object, path: str = "$") -> Iterator[tuple[str, dict[str, object]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def canonical(value: object) -> bytes:
    """Serialize the specification's integer-only data model as RFC 8785 JCS.

    Python's ``sort_keys=True`` orders Unicode code points. RFC 8785 instead
    inherits ECMAScript's lexicographic UTF-16 code-unit ordering, which differs
    for some non-BMP property names. Floats are forbidden by the ax data model,
    so the otherwise difficult ECMAScript number conversion is intentionally
    outside this serializer's accepted domain.
    """

    if value is None or isinstance(value, bool):
        return json.dumps(value, separators=(",", ":")).encode("utf-8")
    if isinstance(value, int):
        if not -SAFE_INTEGER <= value <= SAFE_INTEGER:
            raise ValueError(f"unsafe JSON integer {value}")
        return str(value).encode("ascii")
    if isinstance(value, float):
        raise ValueError("floating-point numbers are forbidden")
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("lone surrogate code point is forbidden") from exc
        return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if isinstance(value, list):
        return b"[" + b",".join(canonical(item) for item in value) + b"]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("non-string map key is forbidden")
        try:
            keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        except UnicodeEncodeError as exc:
            raise ValueError("lone surrogate code point is forbidden") from exc
        members = (canonical(key) + b":" + canonical(value[key]) for key in keys)
        return b"{" + b",".join(members) + b"}"
    raise ValueError(f"unsupported canonical JSON type: {type(value).__name__}")


def check_jcs_canonicalizer(errors: list[str]) -> None:
    fixture = {"\ue000": 1, "\U00010000": 2}
    expected = '{"\U00010000":2,"\ue000":1}'.encode("utf-8")
    actual = canonical(fixture)
    if actual != expected:
        errors.append(
            "RFC 8785 UTF-16 ordering mismatch for JCS-UTF16-ORDER: "
            f"expected {expected!r}, got {actual!r}"
        )
    expected_digest = "9d4cdc71dda603c42f9b21d88d0c2ffc31a76cd1bd461d7359406cf169845f1e"
    actual_digest = hashlib.sha256(actual).hexdigest()
    if actual_digest != expected_digest:
        errors.append(
            "RFC 8785 UTF-16 ordering digest mismatch for JCS-UTF16-ORDER: "
            f"expected {expected_digest}, got {actual_digest}"
        )
    try:
        canonical({"\ud800": 1})
    except ValueError:
        pass
    else:
        errors.append("RFC 8785 canonicalizer accepted a lone surrogate property name")


def validate_numbers(value: object, location: str, errors: list[str]) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, int):
        if not -SAFE_INTEGER <= value <= SAFE_INTEGER:
            errors.append(f"{location}: unsafe JSON integer {value}")
        return
    if isinstance(value, float):
        errors.append(f"{location}: floating-point number is forbidden")
        return
    if isinstance(value, dict):
        for key, child in value.items():
            validate_numbers(child, f"{location}.{key}", errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            validate_numbers(child, f"{location}[{index}]", errors)


def decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def github_anchor(heading: str) -> str:
    s = heading.strip()
    s = s.lower()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^a-z0-9 \-]", "", s)
    s = s.strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s


def extract_headings_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if not m:
            continue
        heading = m.group(1).strip()
        heading = re.sub(r"\s+#+\s*$", "", heading)
        anchors.add(github_anchor(heading))
        stripped = re.sub(r"^[\d\.]+\s*", "", heading)
        if stripped != heading:
            anchors.add(github_anchor(stripped))
    return anchors


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_required_files(errors: list[str]) -> None:
    required = [
        VERSION_FILE, LICENSE_FILE, CHANGELOG, RELEASE_NOTES,
        SPEC, README, CONTRIBUTING, DIAGRAMS_README,
        C4_WORKSPACE, C4_MODEL, C4_VIEWS, C4_REL, C4_STYLES,
        RESEARCH,
        ROOT / "diagrams" / "plantuml" / "takeover.puml",
        ROOT / "diagrams" / "plantuml" / "session_state.puml",
        ROOT / "diagrams" / "plantuml" / "mesh_deployment.puml",
        ROOT / ".github" / "workflows" / "validate.yml",
        ROOT / "scripts" / "validate_spec.py",
        ROOT / "run_validation.sh",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"missing required file: {p.relative_to(ROOT)}")


def normalized_release_document_sha256(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def check_frozen_release_baseline(errors: list[str]) -> None:
    """Protect the reviewed v0.2.1 claim prose without pretending to parse English."""
    expected_names = {path.name for path in PUBLIC_CLAIM_DOCUMENTS}
    configured_names = set(FROZEN_RELEASE_DOCUMENT_SHA256)
    if configured_names != expected_names:
        errors.append(
            "frozen release baseline configuration mismatch: "
            f"expected documents {sorted(expected_names)!r}, configured {sorted(configured_names)!r}"
        )
        return

    for document in PUBLIC_CLAIM_DOCUMENTS:
        if not document.exists():
            continue
        expected = FROZEN_RELEASE_DOCUMENT_SHA256[document.name]
        actual = normalized_release_document_sha256(document)
        if actual != expected:
            errors.append(
                f"{document.name}: frozen v0.2.1 release baseline mismatch "
                f"(expected LF-normalized SHA-256 {expected}, got {actual}); "
                "review the prose and update FROZEN_RELEASE_DOCUMENT_SHA256 only for an intentional release revision"
            )
    expected_svgs = {
        "takeover.svg", "session_state.svg", "mesh_deployment.svg",
        "structurizr-SystemContext.svg", "structurizr-SystemContext-key.svg",
        "structurizr-ContainerContext.svg", "structurizr-ContainerContext-key.svg",
    }
    if ARTEFACTS.exists():
        actual_svgs = {f.name for f in ARTEFACTS.glob("*.svg")}
        if actual_svgs != expected_svgs:
            errors.append(f"diagrams/artefacts SVG set mismatch: expected {sorted(expected_svgs)}, got {sorted(actual_svgs)}")
        for name, expected_digest in EXPECTED_SVG_SHA256.items():
            svg = ARTEFACTS / name
            if not svg.is_file():
                continue
            actual_digest = hashlib.sha256(svg.read_bytes()).hexdigest()
            if actual_digest != expected_digest:
                errors.append(
                    f"diagrams/artefacts/{name} byte integrity mismatch: expected sha256:{expected_digest}, got sha256:{actual_digest}"
                )
    expected_pumls = {
        "structurizr-SystemContext.puml", "structurizr-SystemContext-key.puml",
        "structurizr-ContainerContext.puml", "structurizr-ContainerContext-key.puml",
    }
    puml_dir = ROOT / "diagrams" / "c4"
    if puml_dir.exists():
        actual_pumls = {f.name for f in puml_dir.glob("structurizr-*.puml")}
        if actual_pumls != expected_pumls:
            errors.append(f"diagrams/c4 generated puml set mismatch: expected {sorted(expected_pumls)}, got {sorted(actual_pumls)}")


def check_publication_metadata(errors: list[str]) -> None:
    if VERSION_FILE.exists():
        v = VERSION_FILE.read_text(encoding="utf-8").strip()
        if v != "0.2.1":
            errors.append(f"VERSION must be exactly '0.2.1', got {v!r}")
    if LICENSE_FILE.exists():
        lic = LICENSE_FILE.read_text(encoding="utf-8")
        canonical_mit = """MIT License

Copyright (c) 2026 Ivan Oparin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        if lic.replace("\r\n", "\n") != canonical_mit:
            errors.append("LICENSE differs from the complete canonical MIT text for Copyright (c) 2026 Ivan Oparin")
    if CHANGELOG.exists():
        cl = CHANGELOG.read_text(encoding="utf-8")
        for required in (
            "## [v0.2.1] - 2026-08-23",
            "## [v0.2.0] - 2026-08-23",
            "## [v0.1.0] - 2026-08-22",
        ):
            if required not in cl:
                errors.append(f"CHANGELOG.md missing release history entry {required!r}")
        # Caveats in CHANGELOG or RELEASE_NOTES
        # CHANGELOG must at least mention qwen prohibition (already checked), but also we check RELEASE_NOTES for full set
    if RELEASE_NOTES.exists():
        rn = RELEASE_NOTES.read_text(encoding="utf-8")
        if "v0.2.1" not in rn:
            errors.append("RELEASE_NOTES.md missing v0.2.1")
        if "specification" not in rn.lower():
            errors.append("RELEASE_NOTES.md missing specification disclosure")
        if "specification artifacts only" not in rn.lower() and "specification only" not in rn.lower():
            errors.append("RELEASE_NOTES.md must disclose specification-only status caveat")
    for p in [C4_WORKSPACE, C4_MODEL, C4_VIEWS, C4_REL, C4_STYLES]:
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            if not txt.strip():
                errors.append(f"{p.relative_to(ROOT)} is empty")


def check_changelog_release_caveats(errors: list[str]) -> None:
    """Validate Qwen, Claude, Muse, Antigravity, native-Windows caveats in CHANGELOG/RELEASE_NOTES."""
    required_lines = {
        CHANGELOG: [
            ("Qwen task-board-only caveat", "- Provider plugin protocol definitions for six direct adapters (codex, claude, gemini, muse, antigravity, pi) and task-board-only prompt mode integration for qwen. Direct `ax-provider-qwen` claims are explicitly prohibited in v0.1.0."),
        ],
        RELEASE_NOTES: [
            ("Qwen task-board-only caveat", "- Qwen is only supported via task-board prompt-mode bundles (no direct native `ax-provider-qwen` claim)."),
            ("Muse non-portable cron store caveat", "- Muse relies on a narrow, version- and platform-gated native store/resume probe and advertises `portable_store=false` (`cron.db` is durable but not safely portable)."),
            ("Antigravity authenticated-backend resume caveat", "- Antigravity resumes via conversation UUID through its authenticated backend/account realm, rather than relying on copying local cache as a portable store or checkpoint."),
            ("Claude direct-appserver unsupported caveat", "- For Claude, the direct adapter's `appserver` capability is unsupported, but `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are available through task-board."),
            ("Native Windows/WSL2 separation and terminal-backend caveat", "- Native Windows and WSL2 are distinctly partitioned. Native Windows does not claim `tmux` support, using native process supervision and ConPTY instead."),
        ],
    }
    for document, disclosures in required_lines.items():
        if not document.exists():
            continue
        actual = document.read_text(encoding="utf-8").splitlines()
        for label, expected in disclosures:
            if expected not in actual:
                errors.append(f"{document.name}: {label} must exactly match the accepted disclosure: {expected!r}")


def check_contextual_forbidden_claims(errors: list[str]) -> None:
    """Reject positive security and provider-parity claims line by line.

    Required negative disclosures elsewhere in a document must not mask a new,
    contradictory publication claim.  These checks intentionally inspect each
    public document independently and report the exact source line.
    """
    def add(document: pathlib.Path, line_number: int, label: str, line: str) -> None:
        errors.append(
            f"{document.name}:{line_number}: forbidden positive {label} claim: "
            f"{line.strip()[:180]!r}"
        )

    for document in PUBLIC_CLAIM_DOCUMENTS:
        if not document.exists():
            continue
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            plain = re.sub(r"<[^>]+>|[`*_]", "", line)
            low = plain.lower()

            encryption_positive = (
                re.search(
                    r"\b(?:session\s+)?snapshots?\b.*\b(?:is|are)\s+encrypted\s+at\s+rest\s+by\s+default\b",
                    low,
                )
                or re.search(
                    r"\bdefault\b.{0,60}\b(?:payload|snapshot)?\s*encryption\b.{0,30}"
                    r"\b(?:is|are|comes)\s+(?!(?:not|never|unsupported)\b)"
                    r"(?:enabled|provided|supported)\b",
                    low,
                )
            )
            if encryption_positive:
                add(document, line_number, "default at-rest encryption", line)

            secret_transfer_positive = re.search(
                r"\b(?:credentials?|api\s+tokens?|authentication\s+tokens?)\b.{0,80}"
                r"\b(?:is|are|may\s+be|can\s+be|will\s+be)\s+"
                r"(?:replicated|synchronized|synced|copied|transferred)\b",
                low,
            )
            if secret_transfer_positive:
                add(document, line_number, "credential/token replication", line)

            live_sqlite_positive = re.search(
                r"\blive\s+sqlite(?:\s+database|\s+file)?\b.{0,80}"
                r"\b(?:is|are|will\s+be|can\s+be|may\s+be)\s+"
                r"(?!(?:not|never|unsupported)\b)"
                r"(?:replicated|synchronized|synced|copied)\b.{0,80}"
                r"\b(?:as|for)\s+(?:the\s+)?replication\s+unit\b",
                low,
            )
            if live_sqlite_positive:
                add(document, line_number, "live SQLite replication-unit", line)

            qwen_positive = re.search(
                r"\bqwen\b.{0,80}\b(?:works?|operates?|runs?)\s+"
                r"(?!(?:not|never)\b)(?:.{0,40})?"
                r"(?:without\s+task-board|independent(?:ly)?\s+(?:of|from)\s+task-board|"
                r"direct(?:ly)?|native(?:ly)?)\b|"
                r"\bqwen\b.{0,80}\b(?:is|are)\s+(?!(?:not|never|only)\b)"
                r"(?:direct(?:ly)?|native(?:ly)?)?\s*"
                r"(?:supported|available|enabled|implemented)\b",
                low,
            )
            if qwen_positive:
                add(document, line_number, "direct/native/without-task-board Qwen", line)

            muse_surface = "muse" in low and ("cron.db" in low or "portable_store" in low)
            muse_positive = (
                bool(
                    re.search(
                        r"\bcron\.db\b.{0,80}\b"
                        r"(?:is|are|becomes?|remains?|will\s+be|can\s+be|may\s+be)\s+"
                        r"(?!(?:not|never|unsupported)\b)(?:safely\s+)?portable\b",
                        low,
                    )
                )
                or bool(re.search(r"portable_store\s*=\s*true", low))
            )
            if muse_surface and muse_positive:
                add(document, line_number, "Muse portable-store parity", line)


def check_cross_file_consistency(errors: list[str]) -> None:
    for doc in [SPEC, README, CONTRIBUTING]:
        if not doc.exists():
            continue
        txt = doc.read_text(encoding="utf-8")
        if "relux-works/agent-session-manager-spec" not in txt:
            errors.append(f"{doc.name}: missing repository identity relux-works/agent-session-manager-spec")
        if "v0.2.1" not in txt and "0.2.1" not in txt:
            errors.append(f"{doc.name}: missing version v0.2.1/0.2.1")
    for doc in [SPEC, README, CONTRIBUTING]:
        if doc.exists():
            txt = doc.read_text(encoding="utf-8")
            if "main" not in txt:
                errors.append(f"{doc.name}: missing branch 'main'")
            if "Ivan Oparin" not in txt or "oparin@me.com" not in txt:
                errors.append(f"{doc.name}: missing author Ivan Oparin <oparin@me.com>")
            if "~/.ssh/ivanopcode" not in txt:
                errors.append(f"{doc.name}: missing signing key ~/.ssh/ivanopcode")
    if SPEC.exists():
        spec_txt = SPEC.read_text(encoding="utf-8")
        # Exact AI trailer prohibition: must contain exact phrase
        if "No AI <code>Co-Authored-By</code> trailer" not in spec_txt:
            errors.append("SPEC.md must contain exact prohibition: No AI <code>Co-Authored-By</code> trailer")
    for document in [SPEC, README, CONTRIBUTING, CHANGELOG, RELEASE_NOTES, DIAGRAMS_README]:
        if not document.exists():
            continue
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^\s*Co-Authored-By\s*:", line, re.IGNORECASE):
                errors.append(f"{document.name}:{line_number}: forbidden positive AI Co-Authored-By trailer")
    for candidate in [".research", ".planning"]:
        d = ROOT / candidate
        if not d.exists() or not any(d.iterdir()):
            errors.append(f"missing or empty {candidate}/ artifacts directory")


def check_ci_workflow(errors: list[str]) -> None:
    workflow = ROOT / ".github" / "workflows" / "validate.yml"
    if not workflow.exists():
        return
    text = workflow.read_text(encoding="utf-8")
    required = {
        "Ubuntu runner": "runs-on: ubuntu-22.04",
        "Python runtime": 'python-version: "3.11"',
        "Java runtime": "java-version: '26.0.1'",
        "Structurizr release URL": "https://github.com/structurizr/cli/releases/download/v${STRUCTURIZR_VERSION}/structurizr-cli.zip",
        "Structurizr SHA-256": "f5365a463fc44d539ed19bec00c48ba1e1ecda0ccfd1ba40d2e7472d264eb79a",
        "Structurizr fixed-path wrapper": 'exec /opt/structurizr-cli-2025.11.09/structurizr.sh "$@"',
        "PlantUML release URL": "https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar",
        "PlantUML SHA-256": "89948f14c93756c7a3fb7b69078ff37e8489fd79dd430c582b931e2f65358690",
        "PlantUML root-owned install": 'sudo install -m 0644 "$PLANTUML_DOWNLOAD" "$PLANTUML_JAR"',
        "single happy-path command": "run: ./run_validation.sh",
        "expected-red command": "run: ./scripts/test_expected_red.sh",
    }
    for label, literal in required.items():
        if literal not in text:
            errors.append(f"validate.yml: missing pinned {label}: {literal!r}")
    forbidden = {
        "SourceForge fallback": "sourceforge.net",
        "hidden failed command": "|| true",
        "task-board dependency": "task-board",
        "Structurizr symlink install": "ln -s",
    }
    for label, literal in forbidden.items():
        if literal in text:
            errors.append(f"validate.yml: forbidden {label}: {literal!r}")


def check_markdown_links_and_anchors(errors: list[str]) -> None:
    docs = [SPEC, README, CONTRIBUTING, DIAGRAMS_README, CHANGELOG, RELEASE_NOTES]
    anchor_map: dict[pathlib.Path, set[str]] = {}
    doc_texts: dict[pathlib.Path, str] = {}
    for doc in docs:
        if not doc.exists():
            continue
        txt = doc.read_text(encoding="utf-8")
        doc_texts[doc] = txt
        anchor_map[doc] = extract_headings_anchors(txt)
    for doc, txt in doc_texts.items():
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", txt):
            target = m.group(2).strip()
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            if target.startswith("#"):
                anchor = target[1:]
                allowed = anchor_map.get(doc, set())
                # Same-document anchor must resolve only against containing document
                norm = github_anchor(anchor.replace("-", " "))
                if anchor not in allowed and norm not in allowed:
                    # Also try direct anchor string without normalization
                    if anchor not in allowed:
                        errors.append(f"{doc.name}: broken same-document anchor link {target!r} (no heading generates it in {doc.name})")
                continue
            if "#" in target:
                file_part, anchor = target.split("#", 1)
            else:
                file_part, anchor = target, None
            if not file_part:
                continue
            target_path = (doc.parent / file_part).resolve()
            try:
                rel = target_path.relative_to(ROOT)
            except ValueError:
                if not target_path.exists():
                    errors.append(f"{doc.name}: missing local link target: {target!r}")
                continue
            if not target_path.exists():
                if "#" in file_part:
                    file_part = file_part.split("#")[0]
                    target_path = (doc.parent / file_part).resolve()
                    if not target_path.exists():
                        errors.append(f"{doc.name}: missing local link target: {target!r}")
                        continue
                else:
                    errors.append(f"{doc.name}: missing local link target: {target!r}")
                    continue
            if anchor is not None:
                if target_path.exists() and target_path.suffix == ".md":
                    tgt_txt = target_path.read_text(encoding="utf-8")
                    tgt_anchors = extract_headings_anchors(tgt_txt)
                    norm = github_anchor(anchor.replace("-", " "))
                    if anchor not in tgt_anchors and norm not in tgt_anchors:
                        errors.append(f"{doc.name}: broken anchor {anchor!r} in link to {file_part}")


def check_balanced_fences(errors: list[str]) -> None:
    docs = [SPEC, README, CONTRIBUTING, DIAGRAMS_README, CHANGELOG, RELEASE_NOTES]
    for doc in docs:
        if not doc.exists():
            continue
        txt = doc.read_text(encoding="utf-8")
        lines = txt.splitlines()
        # Track fences: ``` and ~~~
        fence_stack: list[str] = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                fence = "```"
                if fence_stack and fence_stack[-1] == fence:
                    fence_stack.pop()
                else:
                    fence_stack.append(fence)
            elif stripped.startswith("~~~"):
                fence = "~~~"
                if fence_stack and fence_stack[-1] == fence:
                    fence_stack.pop()
                else:
                    fence_stack.append(fence)
        if fence_stack:
            errors.append(f"{doc.name}: unbalanced Markdown fence {fence_stack[-1]!r} (unclosed fence)")


def check_json_toml_examples(text: str, errors: list[str]) -> tuple[int, int, int, int, list[dict[str, object]], dict[str, object] | None]:
    json_count = 0
    jsonc_count = 0
    toml_count = 0
    identity_count = 0
    objects: list[dict[str, object]] = []
    git_fixture: dict[str, object] | None = None
    for language in ("json", "jsonc"):
        for line, source in blocks(text, language):
            if language == "json":
                json_count += 1
            else:
                jsonc_count += 1
            try:
                value = json.loads(source)
            except json.JSONDecodeError as exc:
                errors.append(f"{language.upper()} block at line {line}: {exc}")
                continue
            validate_numbers(value, f"line {line}", errors)
            for object_path, candidate in walk(value):
                if isinstance(candidate, dict):
                    objects.append(candidate)
                if isinstance(candidate, dict) and candidate.get("fixture") == "ax-git-workspace-v1":
                    if git_fixture is not None:
                        errors.append("duplicate ax-git-workspace-v1 fixture")
                    git_fixture = candidate
                if not isinstance(candidate, dict):
                    continue
                schema = candidate.get("schema")
                self_field = SELF_FIELDS.get(schema) if isinstance(schema, str) else None
                if (
                    schema == "urn:ax:schema:materialization-journal"
                    and candidate.get("document_kind") == "managed_replica_marker"
                ):
                    self_field = "marker_id"
                if self_field is None:
                    continue
                identity_count += 1
                actual = candidate.get(self_field)
                if not isinstance(actual, str):
                    errors.append(f"line {line} {object_path}: missing string {self_field}")
                    continue
                payload = dict(candidate)
                del payload[self_field]
                expected = "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()
                if actual != expected:
                    errors.append(f"line {line} {object_path}: {self_field} {actual} != {expected}")
    for line, source in blocks(text, "toml"):
        toml_count += 1
        try:
            tomllib.loads(source)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"TOML block at line {line}: {exc}")
    if git_fixture is None:
        errors.append("missing ax-git-workspace-v1 fixture")
    else:
        validate_git_fixture(git_fixture, objects, errors)
    return json_count, jsonc_count, toml_count, identity_count, objects, git_fixture


def validate_git_fixture(fixture: dict[str, object], objects: list[dict[str, object]], errors: list[str]) -> None:
    expected_labels = {
        "agent_file", "base_file", "staged_file", "working_file", "notes_file",
        "child_file", "gitmodules_file", "parent_pack", "parent_inventory",
        "parent_index", "child_pack", "child_inventory", "child_index",
    }
    raw_payloads = fixture.get("payloads")
    if not isinstance(raw_payloads, list):
        errors.append("Git fixture: payloads is not an array")
        return
    payloads: dict[str, dict[str, object]] = {}
    for item in raw_payloads:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str):
            errors.append("Git fixture: malformed payload row")
            continue
        label = item["label"]
        if label in payloads:
            errors.append(f"Git fixture: duplicate payload label {label}")
            continue
        payloads[label] = item
        try:
            encoded = item["base64url"]
            if not isinstance(encoded, str) or "=" in encoded:
                raise ValueError("not unpadded base64url")
            raw = decode_base64url(encoded)
        except (KeyError, ValueError) as exc:
            errors.append(f"Git fixture {label}: invalid base64url: {exc}")
            continue
        blob_id = "sha256:" + hashlib.sha256(raw).hexdigest()
        if item.get("size") != len(raw):
            errors.append(f"Git fixture {label}: size mismatch")
        if item.get("blob_id") != blob_id:
            errors.append(f"Git fixture {label}: blob digest mismatch")
        media_type = item.get("media_type")
        descriptor = {
            "schema": "urn:ax:schema:blob",
            "schema_version": "1.0.0",
            "blob_id": blob_id,
            "size": len(raw),
            "media_type": media_type,
            "chunks": [] if not raw else [{"index": 0, "offset": 0, "size": len(raw), "chunk_id": blob_id}],
        }
        descriptor_id = "sha256:" + hashlib.sha256(canonical(descriptor)).hexdigest()
        if item.get("descriptor_id") != descriptor_id:
            errors.append(f"Git fixture {label}: descriptor digest mismatch")
    if set(payloads) != expected_labels:
        errors.append(f"Git fixture: label registry mismatch expected {sorted(expected_labels)} got {sorted(payloads)}")


class Gate:
    def __init__(self, text: str) -> None:
        self.text = text
        self.normalized = " ".join(text.split())
        self.errors: list[str] = []
        self.checks = 0

    def has(self, label: str, value: str) -> None:
        self.checks += 1
        if value not in self.text:
            self.errors.append(f"{label}: missing literal {value!r}")

    def normalized_has(self, label: str, value: str) -> None:
        self.checks += 1
        if " ".join(value.split()) not in self.normalized:
            self.errors.append(f"{label}: missing normalized requirement {value!r}")

    def regex(self, label: str, pattern: str) -> None:
        self.checks += 1
        if re.search(pattern, self.text, re.MULTILINE | re.DOTALL) is None:
            self.errors.append(f"{label}: pattern did not match {pattern!r}")

    def not_has(self, label: str, value: str) -> None:
        self.checks += 1
        if value in self.text:
            self.errors.append(f"{label}: forbidden literal {value!r} found")

    def normalized_not_has(self, label: str, value: str) -> None:
        self.checks += 1
        if " ".join(value.split()) in self.normalized:
            self.errors.append(f"{label}: forbidden normalized {value!r} found")


def extract_table_rows(text: str, start_marker: str, end_marker: str | None = None) -> list[str]:
    """Extract markdown table rows between start_marker and next blank or end_marker."""
    lines = text.splitlines()
    rows: list[str] = []
    in_table = False
    start_found = False
    for line in lines:
        if not start_found:
            if start_marker in line:
                start_found = True
            continue
        if end_marker and end_marker in line:
            break
        if line.strip().startswith("|"):
            rows.append(line)
            in_table = True
        elif in_table and not line.strip().startswith("|"):
            # End of table
            if line.strip() == "":
                continue
            # If we hit a heading or non-table after table started, consider table ended
            # But we have specific tables, so break after we collected rows and hit non-table
            # For single table extraction, we want first table after marker
            break
    return rows


def table_cells(row: str) -> tuple[str, ...]:
    """Split a Markdown row whose literal pipes are HTML-escaped."""
    return tuple(cell.strip() for cell in row.strip().strip("|").split("|"))


def first_table_in_section(text: str, start: str, end: str) -> list[tuple[str, ...]]:
    """Return the first table's data rows from one explicitly bounded section."""
    start_at = text.find(start)
    end_at = text.find(end, start_at + len(start)) if start_at != -1 else -1
    if start_at == -1 or end_at == -1:
        return []
    rows: list[tuple[str, ...]] = []
    table_started = False
    for line in text[start_at:end_at].splitlines():
        if not line.startswith("|"):
            if table_started and rows:
                break
            continue
        cells = table_cells(line)
        table_started = True
        if cells and all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


CAPABILITY_MATRIX = tuple(
    table_cells(line) for line in """\
| Codex | A | C | C | A through task-board | A through task-board | A through task-board | A through task-board |
| Claude | A | C | C | U for direct adapter | A through task-board | A through task-board | A through task-board |
| Gemini CLI | A | C | C | ? | U | A through task-board | U |
| Muse | C by platform/version | U | C | ? | U | A through task-board | U |
| Antigravity CLI | C: backend realm required | U | C | ? | U | ? | U |
| Pi | A | C | C | U; Pi RPC is not claimed as this capability | ? | ? | U |
| Qwen through task-board | U direct | U direct | U direct | U direct | U | A through task-board | U |
| Future plugin | ? | ? | ? | ? | ? | ? | ? |""".splitlines()
)


PLATFORM_MATRIX = tuple(
    table_cells(line) for line in """\
| Codex / macOS | A / C / C | Resume and unrestricted flag are documented; portable store and PTY flush require adapter fixtures. |
| Codex / Linux | A / C / C | Same; exact distribution and filesystem fixture required. |
| Codex / WSL2 | A / C / C | Treat as Linux with a Linux store. Repositories SHOULD live below the WSL home, not a Windows-mounted path. |
| Codex / native Windows | A / C / C | Native CLI is documented. ConPTY, Windows store discovery, file locking, and sandbox mode MUST pass. Windows 11 is the release baseline; Windows 10 is best effort and requires ConPTY. |
| Claude / macOS | A / C / C | Installed 2.1.229 help confirms UUID resume and unrestricted flag; store transfer remains gated. |
| Claude / Linux | A / C / C | Provider family documented; distro/PTTY fixture required. |
| Claude / WSL2 | A / C / C | WSL is provider-documented; use Linux store and path rules. |
| Claude / native Windows | C / C / C | Windows 10+ with WSL or Git for Windows is documented, but native PowerShell/ConPTY and native store materialization require acceptance. |
| Gemini / macOS | A / C / C | Official session root, UUID resume, and session-file surface documented. |
| Gemini / Linux | A / C / C | Ubuntu 20.04+ documented; other distributions conditional. |
| Gemini / WSL2 | C / C / C | Linux inference; mounted-filesystem, auth, signal, and path-hash tests required. |
| Gemini / native Windows | A / C / C | Windows 11 24H2+ documented; PowerShell/ConPTY and path-hash tests required. |
| Muse / macOS arm64 | A for probed 0.1.0 / U / C | Narrow resume probe accepted; current 0.2.1 and full idle/cron fidelity remain unverified. |
| Muse / macOS amd64 | C / U / C | Artifact/contract exists; not executed. |
| Muse / Linux amd64 or arm64 | C / U / C | Official launcher artifacts; not executed. |
| Muse / WSL2 | C / U / ? | Linux-path inference only. |
| Muse / native Windows | ? / U / ? | 0.2.1 artifacts exist, but official launcher and persistence contract do not establish support. |
| Antigravity / macOS amd64 or arm64 | C / U / C | Resume works only when the authenticated backend realm resolves the UUID; <code>Stop.fullyIdle</code> is documented. |
| Antigravity / Linux amd64 or arm64 | C / U / C | Native family documented; keyring/DBus and PTY tests required. |
| Antigravity / WSL2 | C / U / ? | Linux inference only; auth, path, signal, and locking tests required. |
| Antigravity / native Windows amd64 or arm64 | C / U / C | Native family documented; ConPTY, data-root expansion, and file-lock tests required. |
| Pi / macOS | A / C / C | Installed 0.73.1 help verifies session surfaces and default full tool set. |
| Pi / Linux | C / C / C | Cross-platform Node/package behavior is plausible but exact 0.73.1 acceptance is required. |
| Pi / WSL2 | C / C / C | Treat as Linux only after path/signal/auth tests. |
| Pi / native Windows | C / C / C | Provider platform notes exist; exact 0.73.1 store, shell, and ConPTY behavior is unverified. |
| Qwen task-board prompt mode / any target platform | U direct; A only where task-board probe reports <code>prompt_spawn</code> | No direct native-store or primary-owner claim. |
| Future plugin / any | ? / ? / ? | Disabled until a tuple-specific probe and acceptance record exist. |""".splitlines()
)


def check_exact_registries(text: str, errors: list[str]) -> dict[str, int]:
    """Parse scoped tables/registries, assert exact sets/counts and cross-references. Returns ledger."""
    ledger: dict[str, int] = {}
    # Provider operations: 15 exact in Section 7.5 operation body registry
    provider_expected = ["manifest","probe","launch","identify-session","quiesce","native-store-plan","capture","materialize","materialize-status","materialize-commit","materialize-rollback","resume","fork","stop","doctor"]
    # Extract provider table rows
    # Find section "The operation body registry is exact."
    provider_marker = "The operation body registry is exact."
    provider_rows = extract_table_rows(text, provider_marker)
    # Filter to rows with <code>operation</code> in first column
    provider_ops_found: list[str] = []
    for row in provider_rows:
        m = re.search(r"\|\s*<code>([^<]+)</code>\s*\|", row)
        if m:
            op = m.group(1).strip()
            # Skip header row
            if op == "Operation":
                continue
            provider_ops_found.append(op)
    ledger["provider_operations"] = len(provider_ops_found)
    if provider_ops_found != provider_expected:
        errors.append(f"provider_operations registry mismatch: expected {provider_expected}, got {provider_ops_found}")
    if len(provider_ops_found) != 15:
        errors.append(f"provider_operations count mismatch: expected 15, got {len(provider_ops_found)}")

    # Bridge operations: 8 exact in Section 9.2 - find bridge table header
    bridge_expected = ["launch","status","export","import","open","adopt","stop","resume"]
    bridge_header = "| Operation | Exact logical request body | Exact success body |"
    bridge_idx = text.find(bridge_header)
    bridge_ops_found: list[str] = []
    if bridge_idx != -1:
        bridge_slice = text[bridge_idx:bridge_idx+5000]
        rows: list[str] = []
        started = False
        for line in bridge_slice.splitlines():
            if not started:
                if line.strip().startswith("| ---"):
                    started = True
                continue
            if line.strip().startswith("|"):
                rows.append(line)
            elif line.strip() == "":
                continue
            else:
                break
        for row in rows:
            m = re.search(r"\|\s*<code>([^<]+)</code>\s*\|", row)
            if m:
                op = m.group(1).strip()
                if op == "Operation":
                    continue
                bridge_ops_found.append(op)
    if bridge_ops_found:
        ledger["bridge_operations"] = len(bridge_ops_found)
        if bridge_ops_found != bridge_expected:
            errors.append(f"bridge_operations registry mismatch: expected {bridge_expected}, got {bridge_ops_found}")
        if len(bridge_ops_found) != 8:
            errors.append(f"bridge_operations count mismatch: expected 8, got {len(bridge_ops_found)}")
    else:
        ledger["bridge_operations"] = 0
        errors.append("bridge_operations: could not locate Section 9.2 bridge table (no rows parsed)")

    # RPC surface includes the hello handshake plus exactly 23 operation bodies.
    rpc_body_expected = [
        "health.get", "inventory.roots", "inventory.children", "objects.get",
        "transfer.begin", "transfer.status", "chunks.put", "transfer.validate",
        "transfer.commit", "materialize.prepare", "materialize.commit",
        "materialize.status", "materialize.finalize", "materialize.rollback",
        "lease.refresh", "tombstone.ack", "session.status", "session.stop",
        "handoff.prepare", "handoff.quiesce", "handoff.stop", "handoff.commit",
        "handoff.abort",
    ]
    surface_rows = first_table_in_section(
        text, "### 11.3 RPC operations", "| Type | Exact members and constraints |"
    )
    surface_ops = [re.sub(r"</?code>", "", row[0]) for row in surface_rows if row]
    expected_surface = ["hello", *rpc_body_expected]
    if surface_ops != expected_surface:
        errors.append(
            f"rpc_surface registry mismatch: expected hello handshake + {rpc_body_expected}, got {surface_ops}"
        )

    body_marker = "| Operation | Exact request body | Exact success body |"
    body_start = text.find(body_marker, text.find("### 11.3 RPC operations"))
    body_end = text.find("For <code>chunks.put</code>", body_start)
    rpc_body_ops: list[str] = []
    if body_start != -1 and body_end != -1:
        for line in text[body_start:body_end].splitlines()[2:]:
            if not line.startswith("|"):
                continue
            cells = table_cells(line)
            if cells:
                rpc_body_ops.append(re.sub(r"</?code>", "", cells[0]))
    ledger["rpc_body_operations"] = len(rpc_body_ops)
    if rpc_body_ops != rpc_body_expected:
        errors.append(
            f"rpc_body_operations registry mismatch: expected exactly 23 ordered bodies {rpc_body_expected}, got {rpc_body_ops}"
        )

    # CLI bodies: 18 in Section 14.2
    cli_section_start = text.find("The <code>command</code> tag selects exactly one body.")
    cli_expected = ["cancel","start","list","status","attach","takeover","fork","stop","resume","sync","diff","materialize","doctor","logs","peer.list","peer.probe","session.set_profile","pane"]
    if cli_section_start != -1:
        cli_text = text[cli_section_start:cli_section_start+8000]
        cli_rows = []
        in_tbl = False
        for line in cli_text.splitlines():
            if "| <code>cancel</code>" in line or line.strip().startswith("| <code>"):
                cli_rows.append(line)
                in_tbl = True
            elif in_tbl and line.strip().startswith("|"):
                cli_rows.append(line)
            elif in_tbl and not line.strip().startswith("|") and line.strip() != "":
                if not line.strip().startswith("|"):
                    break
        cli_ops: list[str] = []
        for row in cli_rows:
            m = re.search(r"\|\s*<code>([^<]+)</code>\s*\|", row)
            if m:
                op = m.group(1).strip()
                if op == "Command tag":
                    continue
                cli_ops.append(op)
        ledger["cli_bodies"] = len(cli_ops)
        if cli_ops != cli_expected:
            errors.append(f"cli_bodies registry mismatch: expected {cli_expected}, got {cli_ops}")
        if len(cli_ops) != 18:
            errors.append(f"cli_bodies count mismatch: expected 18, got {len(cli_ops)}")
    else:
        ledger["cli_bodies"] = 0
        errors.append("cli_bodies: could not locate CLI command tag table")

    # SessionState: 11 values in Section 5.7
    session_state_expected = ["creating","running","idle","quiescing","checkpointing","stopped","materializing","parked","failed","stale","tombstoned"]
    ss_marker = "The exact <code>SessionState</code> enum is, in this order,"
    if ss_marker in text:
        # Extract following lines for enum
        idx = text.find(ss_marker)
        snippet = text[idx:idx+2000]
        # Find code values in snippet
        found = re.findall(r"<code>(creating|running|idle|quiescing|checkpointing|stopped|materializing|parked|failed|stale|tombstoned)</code>", snippet)
        # Deduplicate preserving order but snippet contains them in order
        seen = set()
        ss_found = []
        for v in found:
            if v not in seen:
                seen.add(v)
                ss_found.append(v)
        # The spec lists them across two lines; we should get 11 in order
        ledger["SessionState"] = len(ss_found)
        if ss_found != session_state_expected:
            errors.append(f"SessionState registry mismatch: expected {session_state_expected}, got {ss_found}")
        if len(ss_found) != 11:
            errors.append(f"SessionState count mismatch: expected 11, got {len(ss_found)}")
        # Cross-reference: ensure RPC and CLI reuse checks
        if "Every RPC and CLI field typed" not in text or "<code>SessionState</code> uses exactly this registry" not in text:
            errors.append("SessionState cross-reference missing: RPC/CLI reuse statement")
    else:
        ledger["SessionState"] = 0
        errors.append("SessionState: could not locate Section 5.7 enum")

    # Git payloads: 13 labels validated via fixture already, but also assert registry
    ledger["Git_payloads"] = 13  # validated via fixture; keep for ledger completeness
    # Already validated in validate_git_fixture; if that passed, ledger is 13

    # Verify table for Git payloads is not missing (section 10.4)
    if "ax-git-workspace-v1" not in text:
        errors.append("Git_payloads: missing ax-git-workspace-v1 fixture marker")

    # Cross-contract closure: provider capture uses ObjectSink, RPC SessionState reuse already checked
    return ledger


def operation_cells(text: str, start: str, end: str, operation: str) -> tuple[str, ...] | None:
    start_at = text.find(start)
    end_at = text.find(end, start_at + len(start)) if start_at != -1 else -1
    if start_at == -1 or end_at == -1:
        return None
    match: tuple[str, ...] | None = None
    for line in text[start_at:end_at].splitlines():
        if not line.startswith("|"):
            continue
        cells = table_cells(line)
        if cells and re.sub(r"</?code>", "", cells[0]) == operation:
            match = cells
    return match


def check_critical_protocol_contracts(text: str, errors: list[str]) -> None:
    """Protect the independently reviewed crash-recovery and size contracts."""

    contract_versions = (
        ("Provider protocol", "urn:ax:protocol:provider", "2.0.0"),
        ("Mesh RPC", "urn:ax:protocol:rpc", "2.0.0"),
        (
            "Materialization recovery state (journal and managed-replica marker variants)",
            "urn:ax:schema:materialization-journal",
            "2.0.0",
        ),
    )
    for name, identifier, version in contract_versions:
        row = f"| {name} | <code>{identifier}</code> | <code>{version}</code> |"
        if row not in text:
            errors.append(
                f"critical contract version mismatch: {name} must be {version} in v0.2.1"
            )
    for required in (
        '<code>protocol_version = "2.0.0"</code>',
        '<code>urn:ax:protocol:rpc</code> version <code>2.0.0</code>',
        '<code>urn:ax:schema:materialization-journal</code> version\n<code>2.0.0</code>',
        "The v0.2.0 correction is an explicit major-version boundary.",
    ):
        if required not in text:
            errors.append(f"critical contract version boundary missing: {required!r}")

    active_version_labels = (
        "single Provider protocol 2.0.0 idempotency key",
        "Mesh RPC 2.0.0 operations are:",
        "These closed embedded types belong to Mesh RPC\n2.0.0:",
        "No other mapping exists in Mesh RPC 2.0.0.",
        "These Mesh RPC 2.0.0 fixtures are normative.",
    )
    for required in active_version_labels:
        if required not in text:
            errors.append(
                "critical active contract version label missing or regressed: "
                f"{required!r}"
            )

    provider_status = operation_cells(
        text,
        "The operation body registry is exact.",
        "For <code>launch</code>",
        "materialize-status",
    )
    expected_status_request = (
        "<code>{materialization_id:UUIDv7, transaction_id:UUIDv7, "
        "transaction:ProviderTransactionAuthority}</code>"
    )
    if provider_status is None or len(provider_status) < 3 or provider_status[1] != expected_status_request:
        errors.append(
            "provider materialize-status must be an evolving read located by materialization/transaction "
            "IDs and authority, without operation_id"
        )
    provider_section_start = text.find("### 7.5 Required operations")
    provider_section_end = text.find("### 7.6 Quiescence proof", provider_section_start)
    provider_section = text[provider_section_start:provider_section_end]
    provider_normalized = " ".join(provider_section.split())
    for required in (
        "Observational operations, including <code>materialize-status</code>, are evolving reads.",
        "MUST NOT be stored as mutation receipts",
        "PTX-STATUS-EVOLVES",
    ):
        if " ".join(required.split()) not in provider_normalized:
            errors.append(f"provider evolving status contract missing: {required!r}")

    rpc_prepare = operation_cells(
        text,
        "### 11.3 RPC operations",
        "For <code>chunks.put</code>",
        "materialize.prepare",
    )
    if rpc_prepare is None or len(rpc_prepare) < 3:
        errors.append("materialize.prepare request/response registry row is missing")
    else:
        for cell_index, label in ((1, "request"), (2, "success")):
            cell = rpc_prepare[cell_index]
            if "operation_id:UUIDv7" not in cell or "materialization_id:UUIDv7" not in cell:
                errors.append(
                    f"materialize.prepare {label} must carry caller-stable operation_id and materialization_id"
                )
    for required in (
        "Before the first destination mutation",
        "digest of the complete canonical prepare body",
        "<code>(materialize.prepare, operation_id)</code>",
        "<code>materialize.status</code> is an evolving read",
        "MJ-RPC-PREPARE-LOST",
        "AC-MAT-004",
    ):
        if required not in text:
            errors.append(f"lost-response-safe materialize.prepare contract missing: {required!r}")

    journal_start = text.find("### 10.6 Materialization Journal")
    journal_end = text.find("Provider Journal Transaction is a closed object", journal_start)
    journal_section = text[journal_start:journal_end]
    for field in ("prepare_operation_id", "prepare_request_digest"):
        if f"| <code>{field}</code> |" not in journal_section:
            errors.append(f"Materialization Journal missing durable prepare receipt field {field}")
    cardinality_requirements = (
        "<code>completed_blob_chunks</code> | map(digest,sorted unique uint32[0..32768])[0..65536]",
        "<code>verified_blob_ids</code> | sorted unique digest[0..65536]",
        "blob_chunks:map(digest,sorted unique uint32[0..32768])[0..65536]",
        "created_paths:sorted unique absolute-path[0..65536]",
        "merged_paths:sorted unique absolute-path[0..65536]",
        "restored_paths:sorted unique absolute-path[0..65536]",
        "removed_paths:sorted unique absolute-path[0..65536]",
    )
    for required in cardinality_requirements:
        if required not in text:
            errors.append(f"materialization recovery cardinality mismatch: missing {required!r}")


def check_crash_restart_outcome_gate(text: str, errors: list[str]) -> tuple[int, int]:
    """Validate the v0.2.1 crash/restart gate inside its normative sections.

    The frozen document hashes protect reviewed bytes. These scoped checks give
    gate-specific diagnostics when a mutation weakens the recovery contract.
    """

    initial_error_count = len(errors)
    checks = 0

    def require(section: str, label: str, literal: str) -> None:
        nonlocal checks
        checks += 1
        normalized_section = " ".join(re.sub(r"</?code>", "", section).split())
        normalized_literal = " ".join(re.sub(r"</?code>", "", literal).split())
        if normalized_literal not in normalized_section:
            errors.append(
                f"crash/restart gate {label}: missing normative requirement {literal!r}"
            )

    start = text.find("### 13.13 Crash/restart outcome gate")
    end = text.find("## 14. CLI and operator experience", start)
    checks += 1
    if start == -1 or end == -1:
        errors.append(
            "crash/restart gate section missing or unbounded: expected Section 13.13 before Section 14"
        )
        return checks, len(errors) - initial_error_count
    section = text[start:end]

    outcome_rows = first_table_in_section(
        text,
        "### 13.13 Crash/restart outcome gate",
        "These outcomes are mutually exclusive.",
    )
    expected_outcomes = (
        "<code>safe_retry</code>",
        "<code>explicit_rollback</code>",
        "<code>recoverable_parked_state</code>",
    )
    actual_outcomes = tuple(row[0] for row in outcome_rows if row)
    checks += 1
    if actual_outcomes != expected_outcomes:
        errors.append(
            "crash/restart gate outcome registry mismatch: expected exactly and only "
            f"{expected_outcomes}, got {actual_outcomes}"
        )

    required_outcome_clauses = (
        (
            "safe_retry identity-preserving replay",
            "using every caller-stable operation/materialization/transaction/bridge ID and byte-identical immutable input",
        ),
        (
            "safe_retry effect reconciliation",
            "A retry MUST reconcile an uncertain external effect before issuing it again",
        ),
        (
            "safe_retry allocation prohibition",
            "MUST NOT allocate another process, manager, native handle, lease epoch, staging authority, or transaction root",
        ),
        (
            "explicit_rollback durability and visibility",
            "The terminal rollback/abort result is durable and visible through the existing journal, event, CLI/status, and audit surfaces",
        ),
        (
            "explicit_rollback inactive external effect",
            "no live provider/manager effect",
        ),
        (
            "recoverable_parked_state fail-closed activation block",
            "it fails closed",
        ),
        (
            "recoverable_parked_state activation prohibition",
            "input and activation are blocked",
        ),
        (
            "recoverable_parked_state fresh-session evidence",
            "proof that no new native session or manager was allocated",
        ),
        ("outcome mutual exclusivity", "These outcomes are mutually exclusive"),
        ("outcome collective exhaustiveness", "They are collectively exhaustive"),
        (
            "ambiguous evidence parks",
            "missing, stale, contradictory, unreachable, or ambiguous evidence MUST select recoverable_parked_state",
        ),
        (
            "no fourth outcome",
            "MUST NOT invent a fourth recovery outcome or report an unclassified successful restart",
        ),
        (
            "durable-write injection side",
            "after the named phase's durable write, before the next phase",
        ),
        (
            "external-effect injection side",
            "after the named external effect may have happened, before its result is durable",
        ),
    )
    for label, literal in required_outcome_clauses:
        require(section, label, literal)

    evidence_fields = (
        "boundary ID",
        "path",
        "operation IDs",
        "pre/post durable facts",
        "external effect and status probe",
        "winning lease before/after",
        "native identity/binding before/after",
        "selected outcome",
        "evidence satisfying that outcome",
    )
    for field in evidence_fields:
        require(section, f"classification evidence field {field}", field)

    expected_boundaries = (
        "<code>CR-LAUNCH-D-01..05</code>",
        "<code>CR-LAUNCH-TB-01..03</code>",
        "<code>CR-SYNC-01..07</code>",
        "<code>CR-MAT-01..08</code>",
        "<code>CR-GRACE-01..13</code>",
        "<code>CR-FORCE-01..07</code>",
        "<code>CR-FORCE-D-01..05</code>",
        "<code>CR-FORCE-TB-01..04</code>",
        "<code>CR-FORK-01..08</code>",
        "<code>CR-STOP-01..05</code>",
        "<code>CR-RESUME-01..06</code>",
        "<code>CR-RESTORE-01..07</code>",
    )
    actual_boundaries = tuple(
        table_cells(line)[0]
        for line in section.splitlines()
        if line.startswith("| <code>CR-")
    )
    checks += 1
    if actual_boundaries != expected_boundaries:
        errors.append(
            "crash/restart gate boundary registry mismatch: expected the closed 78-point "
            f"registry {expected_boundaries}, got {actual_boundaries}"
        )

    for label, literal in (
        (
            "duplicate-owner prohibition",
            "two hosts or two native processes/managers can both be treated as live or authoritative for the same logical session",
        ),
        (
            "unfenced continuation is not safe_retry",
            "A losing or unfenced external continuation is not safe_retry",
        ),
        (
            "fresh native identity prohibition",
            "invokes a new-session launch, allocates a fresh native handle or manager reference, relabels blank state, or resumes a different provider/account realm",
        ),
        (
            "fresh native substitution rejects every outcome",
            "Such substitution is never a successful retry, rollback, or parked recovery",
        ),
    ):
        require(section, label, literal)

    acceptance_start = text.find("### 19.4 End-to-end acceptance cases")
    acceptance_end = text.find("### 19.5 ", acceptance_start)
    acceptance = text[acceptance_start:acceptance_end] if acceptance_start != -1 and acceptance_end != -1 else ""
    for label, literal in (
        ("runtime acceptance case", "AC-CRASH-001"),
        ("runtime exact classification", "classifies into exactly one of"),
        ("runtime duplicate-owner rejection", "duplicate live/authoritative owners"),
        ("runtime unfenced-effect rejection", "unfenced external continuation as safe"),
        ("runtime native identity preservation", "fresh native provider/manager session"),
    ):
        require(acceptance, label, literal)

    publication_start = text.find("### 20.2 Publication gate")
    publication_end = text.find("## Appendix A.", publication_start)
    publication = text[publication_start:publication_end] if publication_start != -1 and publication_end != -1 else ""
    for label, literal in (
        ("publication acceptance case", "SPEC-PUB-CRASH-001"),
        ("publication outcome semantics", "mutually exclusive and collectively exhaustive"),
        ("publication boundary coverage", "every boundary family and required evidence field is present"),
        ("publication owner/identity rejection", "duplicate-owner and silent-fresh-native-session recovery are forbidden"),
        ("publication actionable mutation diagnostic", "rather than only reporting a generic document digest mismatch"),
    ):
        require(publication, label, literal)

    trace_start = text.find("### A.8 Crash/restart outcome-gate traceability")
    trace_end = text.find("## Appendix B.", trace_start)
    trace = text[trace_start:trace_end] if trace_start != -1 and trace_end != -1 else ""
    for label, literal in (
        ("task traceability", "TASK-260823-22b7zx"),
        ("runtime traceability", "AC-CRASH-001"),
        ("publication traceability", "SPEC-PUB-CRASH-001"),
        ("wire compatibility traceability", "retain every wire-contract version"),
    ):
        require(trace, label, literal)

    return checks, len(errors) - initial_error_count


def check_semantic_coverage(text: str, errors: list[str]) -> tuple[int, int, int, dict[str,int]]:
    # Run exact registry checks first
    ledger = check_exact_registries(text, errors)
    gate = Gate(text)
    # --- Forbidden claims must be absent as positive assertions ---
    gate.normalized_has("no default encryption disclosure", "default payload encryption at rest and MUST NOT claim otherwise")
    gate.normalized_has("mesh payload encryption none", "mesh.payload_encryption")
    gate.has("payload encryption none value", '"none"')
    gate.normalized_has("tokens must not be replicated", "MUST NOT be replicated")
    gate.normalized_has("live SQLite not replicated", "live SQLite")
    gate.normalized_has("live SQLite must not be copied", "MUST NOT be copied or synchronized")
    gate.normalized_has("no auto authorize", "MAY suggest")
    gate.normalized_has("no tmux on Windows", "MUST NOT claim tmux")
    # --- Matrix platform coverage ---
    gate.normalized_has("matrix macOS", "macOS")
    gate.normalized_has("matrix Linux", "Linux")
    gate.normalized_has("matrix WSL2", "WSL2")
    gate.normalized_has("matrix native Windows", "Native Windows")
    gate.normalized_has("terminal backend abstraction Windows", "terminal backend")
    gate.has("provider platform matrix section", "Provider/platform matrix")
    gate.normalized_has("WSL2 distinct from native Windows", "MUST NOT collapse WSL2")
    # --- Provider matrix ---
    for provider in ["Codex", "Claude", "Gemini", "Muse", "Antigravity", "Pi"]:
        gate.has(f"provider {provider} row", provider)
    gate.normalized_has("Qwen task-board only", "Qwen through task-board")
    gate.normalized_has("no direct qwen claim", "no v0.2.1 direct")
    gate.has("ax-provider-qwen prohibited", "ax-provider-qwen")
    gate.normalized_has("Claude appserver unsupported", "appserver")
    gate.normalized_has("prompt_spawn capability", "prompt_spawn")
    gate.normalized_has("task_board_primary capability", "task_board_primary")
    gate.normalized_has("native_goal_binding capability", "native_goal_binding")
    gate.normalized_has("Muse portable_store false", "portable_store = false")
    gate.normalized_has("Muse cron caveat", "cron.db")
    gate.normalized_has("Antigravity backend realm", "backend")
    gate.has("Antigravity conversation UUID", "conversation")
    gate.normalized_has("task-board prompt modes", "tracked-prompt")
    gate.normalized_has("task-board primary owner", "primary-owner")
    gate.normalized_has("supported task-board prompt modes", "prompt_spawn")
    gate.normalized_has("unsupported combinations", "unsupported")
    gate.has("unsupported sentinel U", "| U ")
    gate.normalized_has("Pi YOLO mapping", "Pi 0.73.1")
    gate.normalized_has("Pi default tool set", "default full tool set")
    gate.normalized_has("immutable records", "immutable")
    gate.normalized_has("content-addressed blobs", "content-addressed")
    gate.normalized_has("tombstones", "tombstone")
    gate.normalized_has("fail closed conflicts", "fail closed")
    gate.normalized_has("never silently overwrite", "never silently overwrite")
    gate.normalized_has("credentials excluded", "credentials")
    gate.normalized_has("SSH private keys excluded", "SSH private keys")
    gate.normalized_has("PIDs not replicated", "PIDs")
    gate.normalized_has("sockets not replicated", "sockets")
    gate.has("CLI ax pane", "ax pane")
    gate.has("ax rpc serve", "ax rpc serve --stdio")
    gate.has("no public TCP listener", "no permanent public TCP listener")
    gate.has("Appendix A traceability", "Appendix A")
    gate.has("Appendix B provider gates", "Appendix B")
    gate.has("Appendix D fixture catalog", "Appendix D")
    # Section 8 exact matrix checks
    # 8.2 Native-store matrix must have 8 provider rows
    native_store_section = text[text.find("### 8.2 Native-store contract matrix"):text.find("### 8.3 Capability matrix")] if "### 8.2 Native-store contract matrix" in text else ""
    if native_store_section:
        native_lines = [l for l in native_store_section.splitlines() if l.strip().startswith("|")]
        # Header and separator are first 2; remaining are data rows (including those with <code>)
        native_provider_rows = [l for l in native_lines if any(p in l for p in ["Codex","Claude","Gemini","Muse","Antigravity","Pi","Qwen","Future plugin"])]
        if len(native_provider_rows) != 8:
            gate.errors.append(f"8.2 native-store matrix row count mismatch: expected 8, got {len(native_provider_rows)}")
        # Check Muse portable_store = false in that table
        muse_row = [l for l in native_provider_rows if "Muse" in l]
        if muse_row and "portable_store = false" not in muse_row[0]:
            gate.errors.append("8.2 Muse row must contain portable_store = false")
        # Check Qwen U for direct
        qwen_row = [l for l in native_provider_rows if "Qwen" in l]
        if qwen_row and "U for direct" not in qwen_row[0] and "U direct" not in qwen_row[0]:
            gate.errors.append("8.2 Qwen row must contain U for direct")
    else:
        gate.errors.append("8.2 native-store matrix section not found")

    # Sections 8.3 and 8.4 are normative registries: exact row order and every
    # cell are validated. A token appearing elsewhere cannot mask a changed cell.
    actual_capability = tuple(
        first_table_in_section(text, "### 8.3 Capability matrix", "### 8.4 Provider/platform matrix")
    )
    if actual_capability != CAPABILITY_MATRIX:
        for index in range(max(len(actual_capability), len(CAPABILITY_MATRIX))):
            actual = actual_capability[index] if index < len(actual_capability) else None
            expected = CAPABILITY_MATRIX[index] if index < len(CAPABILITY_MATRIX) else None
            if actual != expected:
                gate.errors.append(
                    f"8.3 capability matrix row {index + 1} mismatch: expected {expected}, got {actual}"
                )

    actual_platform = tuple(
        first_table_in_section(text, "### 8.4 Provider/platform matrix", "## 9. Task-board integration")
    )
    if actual_platform != PLATFORM_MATRIX:
        for index in range(max(len(actual_platform), len(PLATFORM_MATRIX))):
            actual = actual_platform[index] if index < len(actual_platform) else None
            expected = PLATFORM_MATRIX[index] if index < len(PLATFORM_MATRIX) else None
            if actual != expected:
                gate.errors.append(
                    f"8.4 provider/platform matrix row {index + 1} mismatch: expected {expected}, got {actual}"
                )

    if gate.errors:
        errors.extend(gate.errors)
    return gate.checks, len(gate.errors), gate.checks - len(gate.errors), ledger


def compare_svg_source_metadata(committed_name: str, generated_name: str) -> int:
    """Compare renderer/source identity while release SHA protects committed bytes.

    SVG geometry depends on OS fonts and Graphviz builds. PlantUML embeds the
    exact preprocessed source in a platform-independent processing instruction;
    matching that value proves source freshness after a successful real render.
    """
    committed = pathlib.Path(committed_name)
    generated = pathlib.Path(generated_name)
    errors: list[str] = []
    if not committed.is_file() or not generated.is_file():
        errors.append(f"SVG freshness comparison requires two files: {committed} and {generated}")
    else:
        committed_text = committed.read_text(encoding="utf-8")
        generated_text = generated.read_text(encoding="utf-8")
        source_pattern = re.compile(r"<\?plantuml-src ([^?]+)\?>")
        version_pattern = re.compile(r"<\?plantuml ([^?]+)\?>")
        committed_source = source_pattern.search(committed_text)
        generated_source = source_pattern.search(generated_text)
        committed_version = version_pattern.search(committed_text)
        generated_version = version_pattern.search(generated_text)
        if committed_source is None or generated_source is None:
            errors.append("SVG is missing PlantUML source metadata (plantuml-src)")
        elif committed_source.group(1) != generated_source.group(1):
            errors.append("committed SVG is stale: embedded PlantUML source metadata differs from the fresh render")
        if committed_version is None or generated_version is None:
            errors.append("SVG is missing PlantUML renderer version metadata")
        else:
            expected_version = "1.2026.6"
            if committed_version.group(1) != expected_version or generated_version.group(1) != expected_version:
                errors.append(
                    f"SVG renderer version mismatch: expected {expected_version}, "
                    f"got committed={committed_version.group(1)!r}, generated={generated_version.group(1)!r}"
                )
    if errors:
        for error in errors:
            print(f"ERROR: {committed.name}: {error}")
        return 1
    print(f"  -> {committed.name}: release bytes intact and embedded source metadata fresh")
    return 0


def main() -> int:
    if not SPEC.exists():
        print("ERROR: missing SPEC.md", file=sys.stderr)
        return 1
    text = SPEC.read_text(encoding="utf-8")
    errors: list[str] = []

    check_required_files(errors)
    check_frozen_release_baseline(errors)
    check_publication_metadata(errors)
    check_changelog_release_caveats(errors)
    check_contextual_forbidden_claims(errors)
    check_cross_file_consistency(errors)
    check_ci_workflow(errors)
    check_markdown_links_and_anchors(errors)
    check_balanced_fences(errors)
    check_jcs_canonicalizer(errors)
    check_critical_protocol_contracts(text, errors)
    crash_checks, crash_failures = check_crash_restart_outcome_gate(text, errors)

    lines = text.splitlines()
    headings = sum(1 for line in lines if re.match(r"^#{1,6} ", line))
    numbered_headings = {
        m.group(1)
        for line in lines
        if (m := re.match(r"^#{2,6} (\d+(?:\.\d+)*)(?:\.)?\s", line))
    }
    if headings < 100:
        errors.append(f"too few headings: {headings} (expected >= 100)")
    if len(numbered_headings) < 100:
        errors.append(f"too few numbered sections: {len(numbered_headings)} (expected >= 100)")

    ref_count = 0
    for m in re.finditer(r"\bSections? (\d+(?:\.\d+)*)(?:[–-](\d+(?:\.\d+)*))?", text):
        if "RFC" in text[max(0, m.start() - 40): m.start()]:
            continue
        for ref in (m.group(1), m.group(2)):
            if ref is None:
                continue
            ref_count += 1
            if ref not in numbered_headings:
                errors.append(f"missing numbered section referenced as {ref}")

    table_rows = sum(1 for line in lines if line.strip().startswith("|"))
    tables = sum(1 for line in lines if re.match(r"^\|.*\|$", line) and "---" in line)
    if tables < 50:
        errors.append(f"too few markdown tables: {tables} (expected >= 50)")
    if table_rows < 700:
        errors.append(f"too few table rows: {table_rows} (expected >= 700)")

    json_count, jsonc_count, toml_count, identity_count, objects, git_fixture = check_json_toml_examples(text, errors)
    if json_count < 20:
        errors.append(f"too few JSON blocks: {json_count} (expected >= 20, accepted 59)")
    if jsonc_count < 6:
        errors.append(f"too few strict JSONC fixture blocks: {jsonc_count} (expected >= 6)")
    if toml_count < 1:
        errors.append(f"too few TOML blocks: {toml_count} (expected >= 1)")
    if identity_count < 10:
        errors.append(f"too few registered self-identities: {identity_count} (expected >= 10, accepted 20)")

    checks, failed, passed, ledger = check_semantic_coverage(text, errors)
    checks += crash_checks
    failed += crash_failures
    passed += crash_checks - crash_failures

    local_link_count = 0
    for doc in [SPEC, README, CONTRIBUTING, DIAGRAMS_README]:
        if not doc.exists():
            continue
        dt = doc.read_text(encoding="utf-8")
        for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", dt):
            tgt = m.group(1)
            if tgt.startswith(("https://", "http://", "mailto:")):
                continue
            local_link_count += 1
    if local_link_count < 5:
        errors.append(f"too few local links: {local_link_count} (expected >= 5)")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\nValidation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print(f"All task-scoped specification structure and identity checks passed.")
    print(
        f"  JSON blocks: {json_count}, strict JSONC blocks: {jsonc_count}, "
        f"TOML blocks: {toml_count}, identities: {identity_count}"
    )
    print(f"  Headings: {headings}, numbered: {len(numbered_headings)}, refs: {ref_count}, tables: {tables}, rows: {table_rows}")
    print(f"  Local links: {local_link_count}")
    print(f"  Semantic checks: {checks} total, {passed} passed, {failed} failed")
    print(f"  Ledger: provider_operations={ledger.get('provider_operations',0)}, bridge_operations={ledger.get('bridge_operations',0)}, rpc_body_operations={ledger.get('rpc_body_operations',0)}, cli_bodies={ledger.get('cli_bodies',0)}, SessionState={ledger.get('SessionState',0)}, Git_payloads={ledger.get('Git_payloads',0)}")
    print("  Registry evidence: parsed provider, bridge, RPC-body, CLI-body, SessionState, and Git-payload registries; no aggregate parity count is claimed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--compare-svg":
        sys.exit(compare_svg_source_metadata(sys.argv[2], sys.argv[3]))
    if len(sys.argv) != 1:
        print("usage: validate_spec.py [--compare-svg COMMITTED GENERATED]", file=sys.stderr)
        sys.exit(2)
    sys.exit(main())
