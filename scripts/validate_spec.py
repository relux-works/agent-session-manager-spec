#!/usr/bin/env python3
"""Public, repository-only validation for AX v0.5.0.

Incorporates both retained validators (validate_spec_contracts + validate_second_rework)
and adds publication/metadata, recovery, cloning, Directory, historical v0.4.3
realm closure, and TerminalBackend conformance.
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

from validate_directory import validate as validate_directory
from validate_terminal_backend import validate as validate_terminal_backend
from validate_v043 import validate as validate_v043

ROOT = pathlib.Path(__file__).resolve().parents[1]
CURRENT_RELEASE = "0.5.0"
SPEC = ROOT / "SPEC.md"
README = ROOT / "README.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
DIAGRAMS_README = ROOT / "diagrams" / "README.md"
VERSION_FILE = ROOT / "VERSION"
LICENSE_FILE = ROOT / "LICENSE"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_NOTES = ROOT / "RELEASE_NOTES.md"
TRACEABILITY = ROOT / "STANDALONE_TO_AX_TRACEABILITY.md"
DIRECTORY_FIXTURE = ROOT / "fixtures" / "session_directory_conformance.json"
V043_FIXTURE = ROOT / "fixtures" / "v0_4_3_roadmap_terminal_realm.json"
TERMINAL_BACKEND_FIXTURE = ROOT / "fixtures" / "terminal_backend_conformance.json"
PUBLIC_CLAIM_DOCUMENTS = [SPEC, README, CONTRIBUTING, CHANGELOG, RELEASE_NOTES]
# Frozen reviewed publication prose. Hashes use UTF-8 text with all line endings
# normalized to LF, so the same checkout validates on Unix and Windows. A
# specification revision must deliberately replace this bounded map after its
# semantic checks and expected-red suite have been reviewed.
FROZEN_RELEASE_DOCUMENT_SHA256 = {
    "SPEC.md": "6bbefa4d83f981d11d6a83e8ccd46fa9f90febc006f81d989a7a0cdf909a8b5f",
    "README.md": "da7ac589d05ae41a93d2b1d94a2d4a2a008304f51e0c63d9e8fab55c71e21c99",
    "CONTRIBUTING.md": "6346872b89c114988e93c2ab4fd85f16045c09e4d87f6d534453d102f945c2ce",
    "CHANGELOG.md": "b7243c372fd6e7e1ffdcf536fedd03318b50971230611a43ddfa92f80621c081",
    "RELEASE_NOTES.md": "e544932452ea45222132e5743596bd55afefc7ed9b394da9489d1159b328bff9",
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
    "cloning_components.svg": "d9521205b83419a37582696699f43f178ed68f57a7846a2328f9aaff11a0bfbc",
    "cloning_transaction.svg": "03ec313c341ff0903ab4aa03e59e3e43c710e293059359510497a84472019d89",
    "mesh_deployment.svg": "54b23ace83d1bdb0c3313a3c8af6b2ae75707528ed72f94a4ed935e20805c268",
    "session_directory_components.svg": "fad87564d3d5877a1478728d21d321c6ef0e769798c792ade46e165cb708066a",
    "session_directory_continuation.svg": "38d0e77c3ecfc5b854a65a06306cffce168e03183d5aea7f635a64a66a1c7a2a",
    "session_directory_enrichment.svg": "4b61c7b2508a07e15f1bb3ef87a94f5cb85bda6d4bf4b552333a0c1b403b8813",
    "session_state.svg": "fae377f21fd374a40c2b831c6ced4e9f61c662a993c0b550d1c9ca0f0c0be507",
    "terminal_backend_components.svg": "7cf99e3bf0b52cc3940a54b5041b355a4e809881bdfbc2f06da2137a5d71ce38",
    "structurizr-ContainerContext-key.svg": "8fb4a6237262cb4e01855f526741d1e752ae3063162ede47f527eab8cf705ebe",
    "structurizr-ContainerContext.svg": "4cc365c3242af1bc93d753cf70b1e8658604e06c13b46d806cc5d3f1e0212fa5",
    "structurizr-SystemContext-key.svg": "d2b29e2efb08aa803166c8be5366933359c1b136d97fa01b0eedfce8406b65d1",
    "structurizr-SystemContext.svg": "9822f3bc4e90fe4d9ede96fa117f2d28aaeb87d530544473db31d81800dc6f54",
    "structurizr-TerminalBackendComponents-key.svg": "57bf0ea4bed2c35fd6a58ff442f430e8cd8b0f2ec716efcbaef6f5f15a2ec874",
    "structurizr-TerminalBackendComponents.svg": "9755f8d5835fa5afeaa5e9e71191e891029aacb104388df8a12abb9bca1a7013",
    "takeover.svg": "91afd16c0f043d7e138b2f9558b62b54a5daaea7a61792840939802e5204141f",
}

EXPECTED_HANDWRITTEN_PLANTUML = {
    "takeover.puml",
    "session_state.puml",
    "mesh_deployment.puml",
    "cloning_components.puml",
    "cloning_transaction.puml",
    "session_directory_components.puml",
    "session_directory_enrichment.puml",
    "session_directory_continuation.puml",
    "terminal_backend_components.puml",
}

FROZEN_ACCEPTED_INPUT_SHA256 = {
    "STANDALONE_TO_AX_TRACEABILITY.md": "af32e2f17ca43af7caf1d2ba585745d87b559a0f7070d8e0b517567eeb2a9a6e",
    "diagrams/README.md": "cb17e97eaee86dcaf1f8daa16765964a81cf544fc3988b8d2ed795ff9b464acf",
    "diagrams/plantuml/cloning_components.puml": "50e728af2fddbc5f3b161d661068fc33c4fe341884c4c28a8ea541c24577118a",
    "diagrams/plantuml/cloning_transaction.puml": "aadeb780d4cbbe129059dd327bd67b42c1947e13660143f7b91a06c59c99887f",
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
    "urn:ax:schema:clone-raw-object-manifest": "raw_object_manifest_id",
    "urn:ax:schema:clone-capture-manifest": "capture_manifest_id",
    "urn:ax:schema:session-clone-bundle": "bundle_manifest_id",
    "urn:ax:schema:canonical-session": "canonical_session_id",
    "urn:ax:schema:canonical-event": "event_id",
    "urn:ax:schema:migration-checkpoint": "migration_checkpoint_id",
    "urn:ax:schema:fidelity-report": "fidelity_report_id",
    "urn:ax:schema:projection-plan": "projection_plan_id",
    "urn:ax:schema:clone-projected-object-manifest": "projected_object_manifest_id",
    "urn:ax:schema:clone-read-back-evidence-manifest": "read_back_evidence_manifest_id",
    "urn:ax:schema:clone-validation-report": "validation_report_id",
    "urn:ax:schema:clone-lineage-receipt": "lineage_receipt_id",
    "urn:ax:schema:supported-environment-tuples": "registry_digest",
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
        RESEARCH, DIRECTORY_FIXTURE, V043_FIXTURE, TERMINAL_BACKEND_FIXTURE,
        ROOT / "diagrams" / "plantuml" / "takeover.puml",
        ROOT / "diagrams" / "plantuml" / "session_state.puml",
        ROOT / "diagrams" / "plantuml" / "mesh_deployment.puml",
        ROOT / "diagrams" / "plantuml" / "cloning_components.puml",
        ROOT / "diagrams" / "plantuml" / "cloning_transaction.puml",
        ROOT / "diagrams" / "plantuml" / "session_directory_components.puml",
        ROOT / "diagrams" / "plantuml" / "session_directory_enrichment.puml",
        ROOT / "diagrams" / "plantuml" / "session_directory_continuation.puml",
        ROOT / "diagrams" / "plantuml" / "terminal_backend_components.puml",
        ROOT / "STANDALONE_TO_AX_TRACEABILITY.md",
        ROOT / ".github" / "workflows" / "validate.yml",
        ROOT / "scripts" / "validate_spec.py",
        ROOT / "run_validation.sh",
        DIRECTORY_FIXTURE,
    ]
    for p in required:
        if not p.exists():
            errors.append(f"missing required file: {p.relative_to(ROOT)}")


def normalized_release_document_sha256(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def check_frozen_release_baseline(errors: list[str]) -> None:
    """Protect reviewed publication prose without pretending to parse English."""
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
                f"{document.name}: frozen v{CURRENT_RELEASE} release baseline mismatch "
                f"(expected LF-normalized SHA-256 {expected}, got {actual}); "
                "review the prose and update FROZEN_RELEASE_DOCUMENT_SHA256 only for an intentional release revision"
            )
    expected_svgs = {
        "takeover.svg", "session_state.svg", "mesh_deployment.svg",
        "cloning_components.svg", "cloning_transaction.svg",
        "session_directory_components.svg", "session_directory_enrichment.svg",
        "session_directory_continuation.svg",
        "terminal_backend_components.svg",
        "structurizr-SystemContext.svg", "structurizr-SystemContext-key.svg",
        "structurizr-ContainerContext.svg", "structurizr-ContainerContext-key.svg",
        "structurizr-TerminalBackendComponents.svg", "structurizr-TerminalBackendComponents-key.svg",
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
        "structurizr-TerminalBackendComponents.puml", "structurizr-TerminalBackendComponents-key.puml",
    }
    puml_dir = ROOT / "diagrams" / "c4"
    if puml_dir.exists():
        actual_pumls = {f.name for f in puml_dir.glob("structurizr-*.puml")}
        if actual_pumls != expected_pumls:
            errors.append(f"diagrams/c4 generated puml set mismatch: expected {sorted(expected_pumls)}, got {sorted(actual_pumls)}")
    for relative_name, expected_digest in FROZEN_ACCEPTED_INPUT_SHA256.items():
        path = ROOT / relative_name
        if not path.is_file():
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            errors.append(
                f"{relative_name}: reviewer-accepted input byte mismatch: "
                f"expected sha256:{expected_digest}, got sha256:{actual_digest}"
            )


def check_publication_metadata(errors: list[str]) -> None:
    if VERSION_FILE.exists():
        v = VERSION_FILE.read_text(encoding="utf-8").strip()
        if v != CURRENT_RELEASE:
            errors.append(f"VERSION must be exactly {CURRENT_RELEASE!r}, got {v!r}")
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
            "## [v0.5.0] - 2026-08-29",
            "## [v0.4.3] - 2026-08-28",
            "## [v0.4.2] - 2026-08-28",
            "## [v0.4.1] - 2026-08-27",
            "## [v0.4.0] - 2026-08-27",
            "## [v0.3.0] - 2026-08-27",
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
        if f"v{CURRENT_RELEASE}" not in rn:
            errors.append(f"RELEASE_NOTES.md missing v{CURRENT_RELEASE}")
        if "specification" not in rn.lower():
            errors.append("RELEASE_NOTES.md missing specification disclosure")
        if "specification artifacts only" not in rn.lower() and "specification only" not in rn.lower():
            errors.append("RELEASE_NOTES.md must disclose specification-only status caveat")
    for p in [C4_WORKSPACE, C4_MODEL, C4_VIEWS, C4_REL, C4_STYLES]:
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            if not txt.strip():
                errors.append(f"{p.relative_to(ROOT)} is empty")


def check_terminal_backend_diagram_semantics(errors: list[str]) -> None:
    """Keep the diagram entry points aligned with the TerminalBackend authority boundary."""
    required_markers = {
        C4_MODEL: (
            'terminal_runtime = container "Terminal Runtime Core"',
            'terminal_controller = component "AX Terminal Controller"',
            'terminal_registry = component "Terminal Backend Registry"',
            'terminal_backend = component "TerminalBackend Boundary"',
            'tmux_backend = component "Built-in tmux Backend"',
            'conpty_backend = component "Built-in ConPTY Backend"',
            "Owns one host-local TerminalInstance",
            "exactly ax pane SESSION_ID",
        ),
        C4_REL: (
            'terminal_controller -> terminal_backend "Delegates authorized host-local operations"',
            'aqua_broker -> tmux_backend "Creates/attests dedicated private -S server on macOS"',
            'tb_session -> terminal_backend "Presents inside one host-local TerminalInstance without changing ownership"',
        ),
        C4_VIEWS: (
            'component terminal_runtime "TerminalBackendComponents"',
        ),
        PLANTUML_DIR / "terminal_backend_components.puml": (
            "AX authority (authoritative state and decisions)",
            "TerminalBackend Boundary",
            "Built-in tmux Backend",
            "Built-in ConPTY Backend",
            "ax pane SESSION_ID",
            "Never owns or interprets LogicalSession",
            "Client mirrors never mutate ownership",
            "Superlogical is an illustrative future candidate only: unavailable",
            "No API, backend ID, support",
        ),
    }
    for path, markers in required_markers.items():
        if not path.is_file():
            errors.append(f"terminal backend diagram source missing: {path.relative_to(ROOT)}")
            continue
        source = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                errors.append(
                    f"terminal backend diagram semantic marker missing in {path.relative_to(ROOT)}: {marker!r}"
                )


def check_public_diagram_ledgers(errors: list[str]) -> None:
    """Keep public diagram inventories aligned with the reviewed diagram set."""
    if len(EXPECTED_HANDWRITTEN_PLANTUML) != 9 or len(EXPECTED_SVG_SHA256) != 15:
        errors.append("public diagram ledger validator configuration must contain nine PlantUML sources and fifteen SVG artifacts")
        return

    for document in (README, CONTRIBUTING):
        if not document.exists():
            continue
        text = document.read_text(encoding="utf-8")
        missing_sources = sorted(name for name in EXPECTED_HANDWRITTEN_PLANTUML if f"`{name}`" not in text)
        missing_svgs = sorted(name for name in EXPECTED_SVG_SHA256 if f"`{name}`" not in text)
        if "nine handwritten PlantUML sources" not in text or missing_sources:
            errors.append(
                f"{document.name}: public diagram ledger must declare nine handwritten PlantUML sources; "
                f"missing {missing_sources}"
            )
        if "fifteen committed SVG artifacts" not in text or missing_svgs:
            errors.append(
                f"{document.name}: public diagram ledger must declare fifteen committed SVG artifacts; "
                f"missing {missing_svgs}"
            )


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
        if f"v{CURRENT_RELEASE}" not in txt and CURRENT_RELEASE not in txt:
            errors.append(f"{doc.name}: missing version v{CURRENT_RELEASE}/{CURRENT_RELEASE}")
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
    stale_publication_markers = (
        "TASK-260826", "STORY-260826", "EPIC-260826",
        "Release-candidate gate status", "still identify and freeze `v0.2.1`",
        "unchanged v0.2.1 SHA-256 ledger",
    )
    for document in [SPEC, README, CONTRIBUTING, CHANGELOG, RELEASE_NOTES, DIAGRAMS_README]:
        if not document.exists():
            continue
        content = document.read_text(encoding="utf-8")
        for marker in stale_publication_markers:
            if marker in content:
                errors.append(
                    f"{document.relative_to(ROOT)}: stale/internal v{CURRENT_RELEASE} publication marker {marker!r}"
                )


def check_readme_terminal_backend_milestones(errors: list[str]) -> None:
    """Keep the public roadmap synchronized with normative SPEC Section 19.1."""
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    start = text.find("## v0.5.0 tmux-first roadmap and macOS terminal realm")
    end = text.find("\n## ", start + 3) if start != -1 else -1
    section = text[start:end] if start != -1 and end != -1 else ""
    normalized = " ".join(section.split())
    required = (
        (
            "M0",
            "M0 establishes the TerminalBackend semantic contract, registry, identity and compatibility rules, internal interface, and conformance harness.",
        ),
        (
            "historical provider-plugin SDK rule",
            "the historical provider-plugin rule that M0 does not promise a stable public plugin SDK",
        ),
        (
            "M1",
            "M1 delivers the production built-in `ax.tmux` backend and single-host durability.",
        ),
        ("M3 tmux gate", "M3 is the first daily-driver tmux gate."),
    )
    for label, literal in required:
        if literal not in normalized:
            errors.append(
                f"README.md: TerminalBackend roadmap {label} milestone missing or stale; "
                "synchronize the public summary with normative SPEC.md Section 19.1"
            )


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
    docs = [
        SPEC,
        README,
        CONTRIBUTING,
        DIAGRAMS_README,
        CHANGELOG,
        RELEASE_NOTES,
        TRACEABILITY,
    ]
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
        ("Mesh RPC", "urn:ax:protocol:rpc", "2.0.0</code>, <code>3.0.0"),
        (
            "Materialization recovery state (journal and managed-replica marker variants)",
            "urn:ax:schema:materialization-journal",
            "2.0.0",
        ),
    )
    for name, identifier, version in contract_versions:
        rows = [line for line in text.splitlines() if line.startswith("|") and f"<code>{identifier}</code>" in line]
        if name == "Mesh RPC":
            row_present = any("<code>2.0.0</code>" in row and "<code>3.0.0</code>" in row for row in rows)
        else:
            row_present = any(f"<code>{version}</code>" in row for row in rows)
        if not row_present:
            errors.append(
                f"critical contract version mismatch: {name} must expose {version} across the v0.3/v0.4 boundary"
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
    """Validate the retained v0.2.1 crash/restart gate inside v0.3.0.

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


def check_cloning_contract_gate(
    text: str, objects: list[dict[str, object]], errors: list[str]
) -> tuple[int, int, dict[str, int]]:
    """Machine-check the v0.3.0 cloning contract closure and invariants.

    Checks are deliberately scoped to the normative registry and cloning
    sections so an unrelated prose occurrence cannot mask a missing contract.
    """

    initial_error_count = len(errors)
    gate = Gate(text)
    ledger: dict[str, int] = {}

    registry_rows = first_table_in_section(
        text, "### 1.5 Normative contract registry", "### 1.6 Common data rules"
    )
    registry: dict[str, tuple[str, str]] = {}
    identifiers: dict[str, list[str]] = {}
    for row in registry_rows:
        if len(row) != 3:
            errors.append(f"clone gate contract registry malformed row: {row!r}")
            continue
        name, identifier, version = row
        identifier = re.sub(r"</?code>", "", identifier)
        if name in registry:
            errors.append(f"clone gate contract registry duplicate name: {name}")
        registry[name] = (identifier, version)
        identifiers.setdefault(identifier, []).append(name)
    ledger["contracts"] = len(registry)
    for identifier, names in identifiers.items():
        if len(names) > 1 and not (
            identifier == "urn:ax:schema:materialization-journal"
            and names == [
                "Materialization recovery state (journal and managed-replica marker variants)",
                "Clone materialization recovery state (journal variant)",
            ]
        ):
            errors.append(
                f"clone gate contract registry identifier is not unique: {identifier} -> {names}"
            )

    required_contracts = {
        "Session Adapter protocol": ("urn:ax:protocol:session-adapter", "1.0.0"),
        "Session Adapter manifest": ("urn:ax:schema:session-adapter-manifest", "1.0.0"),
        "Session Adapter probe": ("urn:ax:schema:session-adapter-probe", "1.0.0"),
        "Clone Raw Object Manifest": ("urn:ax:schema:clone-raw-object-manifest", "1.0.0"),
        "Clone Capture Manifest": ("urn:ax:schema:clone-capture-manifest", "1.0.0"),
        "Clone Bundle Manifest": ("urn:ax:schema:session-clone-bundle", "1.0.0"),
        "Canonical Session": ("urn:ax:schema:canonical-session", "1.0.0"),
        "Canonical Event": ("urn:ax:schema:canonical-event", "1.0.0"),
        "Migration Checkpoint": ("urn:ax:schema:migration-checkpoint", "1.0.0"),
        "Fidelity Report": ("urn:ax:schema:fidelity-report", "1.0.0"),
        "Projection Plan": ("urn:ax:schema:projection-plan", "1.0.0"),
        "Clone Projected Object Manifest": ("urn:ax:schema:clone-projected-object-manifest", "1.0.0"),
        "Clone Read-Back Evidence Manifest": ("urn:ax:schema:clone-read-back-evidence-manifest", "1.0.0"),
        "Clone Validation Report": ("urn:ax:schema:clone-validation-report", "1.0.0"),
        "Clone Lineage Receipt": ("urn:ax:schema:clone-lineage-receipt", "1.0.0"),
        "Supported Environment Tuple Registry": ("urn:ax:schema:supported-environment-tuples", "1.0.0"),
    }
    for name, (identifier, version) in required_contracts.items():
        gate.checks += 1
        actual = registry.get(name)
        if actual is None or actual[0] != identifier or f"<code>{version}</code>" not in actual[1]:
            gate.errors.append(
                f"clone gate contract registry mismatch for {name}: expected {identifier} {version}, got {actual}"
            )

    registered_schema_ids = {
        identifier for identifier in identifiers if identifier.startswith("urn:ax:schema:")
    }
    for candidate in objects:
        schema = candidate.get("schema")
        if not isinstance(schema, str) or schema == "board-goal-v2":
            continue
        gate.checks += 1
        if schema not in registered_schema_ids:
            gate.errors.append(f"clone gate JSON schema reference is not registered: {schema}")

    adapter_start = text.find("### 7.8 Companion Session Adapter protocol")
    adapter_end = text.find("## 8. Provider and platform contracts", adapter_start)
    adapter = text[adapter_start:adapter_end] if adapter_start >= 0 and adapter_end >= 0 else ""
    adapter_rows = first_table_in_section(
        adapter,
        "The exact request and success <code>body</code> registry is:",
        "Candidate objects are addressed only",
    )
    adapter_operations = [re.sub(r"</?code>", "", row[0]) for row in adapter_rows if row]
    expected_adapter_operations = [
        "manifest", "probe", "discover", "inspect", "snapshot-proof",
        "capture-plan", "capture", "normalize", "projection-plan", "project",
        "read-back", "validate", "resume-plan", "doctor",
    ]
    ledger["adapter_operations"] = len(adapter_operations)
    gate.checks += 1
    if adapter_operations != expected_adapter_operations:
        gate.errors.append(
            "clone gate Session Adapter operation registry mismatch: "
            f"expected {expected_adapter_operations}, got {adapter_operations}"
        )

    capability_start = adapter.find("The exact capability names are")
    capability_end = adapter.find("Each value contains exactly", capability_start)
    capability_section = adapter[capability_start:capability_end]
    adapter_capabilities = re.findall(r"<code>([a-z_]+)</code>", capability_section)
    expected_adapter_capabilities = [
        "native_discovery", "stable_snapshot", "raw_capture", "canonical_read",
        "canonical_write", "native_read_back", "native_resume_plan", "official_import",
        "same_environment_lossless_clone", "tool_history", "usage_history",
        "compaction_history", "subagent_graph", "opaque_reasoning_roundtrip",
        "workspace_binding",
    ]
    ledger["adapter_capabilities"] = len(adapter_capabilities)
    gate.checks += 1
    if adapter_capabilities != expected_adapter_capabilities:
        gate.errors.append(
            "clone gate Session Adapter capability registry mismatch: "
            f"expected {expected_adapter_capabilities}, got {adapter_capabilities}"
        )

    for label, literal in (
        ("adapter/provider executable binding", "same host-observed executable digest as Provider Protocol 2.0.0"),
        ("adapter failure/absence distinction", "Partial, malformed, over-limit, or escaped results are errors, never absence or fallback permission"),
        ("adapter trust binding refresh", "Before every call and target mutation, these facts MUST equal freshly read trusted-candidate facts and the Journal binding"),
        ("target-write capability conjunction", "A target write requires available canonical-write or official-import"),
        ("target-write signed tuple admission", "accepted non-revoked signed source/target tuple entries"),
        ("target-write force bypass prohibition", "--force</code>, experimental profiles, and environment-name-only matches cannot bypass these gates"),
    ):
        gate.normalized_has(f"clone gate {label}", literal)

    clone_start = text.find("### 13.14 Cross-environment clone")
    clone_end = text.find("## 14. CLI and operator experience", clone_start)
    clone = text[clone_start:clone_end] if clone_start >= 0 and clone_end >= 0 else ""
    clone_gate = Gate(clone)

    session_record_start = text.find("### 5.1 Session Record")
    session_record_end = text.find("### 5.2 Session Event", session_record_start)
    session_record = (
        text[session_record_start:session_record_end]
        if session_record_start >= 0 and session_record_end >= 0
        else ""
    )
    session_record_gate = Gate(session_record)
    session_record_gate.normalized_has(
        "clone gate target derivation preserves source provider identity",
        "The new target Session ID and target <code>provider_id</code> are allocated at "
        "creation and never reuse or mutate the source Session or source provider ID",
    )
    session_record_gate.normalized_has(
        "clone gate source authority non-transfer",
        "source goals, manager references, leases, approvals, tokens, and pending operations do not transfer",
    )

    capture_start = clone.find("#### 13.14.1 Capture and canonical contracts")
    capture_end = clone.find("#### 13.14.2 Fidelity, projection, and lineage", capture_start)
    capture = clone[capture_start:capture_end] if capture_start >= 0 and capture_end >= 0 else ""
    capture_gate = Gate(capture)
    capture_gate.normalized_has(
        "clone gate historical tools remain inert",
        "Historical tools are inert; incomplete calls become aborted history and block pending action",
    )
    capture_gate.normalized_has(
        "clone gate reasoning and usage authority stripping",
        "foreign encrypted/signed reasoning is opaque-preserved, and source usage is not target accounting",
    )
    capture_gate.normalized_has(
        "clone gate raw evidence remains content-addressed",
        "key, capture class, byte count, blob ID, Blob Descriptor ID, and extensions",
    )

    fidelity_start = clone.find("#### 13.14.2 Fidelity, projection, and lineage")
    fidelity_end = clone.find("#### 13.14.3 Immutable bundle chain", fidelity_start)
    fidelity = clone[fidelity_start:fidelity_end] if fidelity_start >= 0 and fidelity_end >= 0 else ""
    fidelity_gate = Gate(fidelity)
    fidelity_gate.normalized_has(
        "clone gate continuation context fidelity disclosure",
        "Continuation context is explicitly non-native historical fidelity",
    )
    fidelity_gate.normalized_has(
        "clone gate visible migration text has no control authority",
        "Visible text comes from typed escaped fields and is user context, never an assistant reply or control instruction",
    )
    expected_dispositions = [
        "exact", "semantic", "summarized", "opaque_preserved",
        "synthesized", "omitted", "unrecoverable",
    ]
    disposition_match = re.search(
        r"The dispositions are <code>([^<]+)</code>\.", fidelity
    )
    counts_match = re.search(
        r"<code>FidelityCounts</code> contains exactly the seven uint53 members\s+(.*?)\.",
        fidelity,
        re.DOTALL,
    )
    declared_dispositions = disposition_match.group(1).split("|") if disposition_match else []
    counted_dispositions = (
        re.findall(r"<code>([a-z_]+)</code>", counts_match.group(1))
        if counts_match
        else []
    )
    fidelity_gate.checks += 1
    if declared_dispositions != expected_dispositions or counted_dispositions != expected_dispositions:
        fidelity_gate.errors.append(
            "clone gate fidelity disposition registry mismatch: "
            f"expected {expected_dispositions}, got dispositions={declared_dispositions}, "
            f"FidelityCounts={counted_dispositions}"
        )

    bundle_start = clone.find("#### 13.14.3 Immutable bundle chain")
    bundle_end = clone.find("#### 13.14.4 Transaction and target Checkpoint", bundle_start)
    bundle = clone[bundle_start:bundle_end] if bundle_start >= 0 and bundle_end >= 0 else ""
    bundle_gate = Gate(bundle)
    bundle_gate.normalized_has(
        "clone gate canonical generation retains raw evidence",
        "G0 names Capture Manifest. G1 adds Canonical Session/Events",
    )

    transaction_start = clone.find("#### 13.14.4 Transaction and target Checkpoint")
    transaction_end = clone.find("#### 13.14.5 Events, state, and tuple admission", transaction_start)
    transaction = (
        clone[transaction_start:transaction_end]
        if transaction_start >= 0 and transaction_end >= 0
        else ""
    )
    transaction_gate = Gate(transaction)
    transaction_gate.normalized_has(
        "clone gate reuses AX transfer contracts",
        "Only a clone Plan 2 may use Projected Object Manifest as provider merge input; "
        "Transfer Manifest 1.0.0 remains unchanged",
    )
    phase_match = re.search(
        r"~~~text\s+(resolving\s*->.*?lineage_published)\s+archive:",
        transaction,
        re.DOTALL,
    )
    actual_phases = (
        [part.strip() for part in re.sub(r"\s+", " ", phase_match.group(1)).split("->")]
        if phase_match
        else []
    )
    expected_phases = [
        "resolving", "snapshotting", "captured", "normalized", "planned",
        "preparing", "prepared", "publishing", "published", "live_validating",
        "finalizing", "provider_committed", "sealing_checkpoint", "committed",
        "lineage_published",
    ]
    transaction_gate.checks += 1
    if actual_phases != expected_phases:
        transaction_gate.errors.append(
            "clone gate transaction phase ordering mismatch: "
            f"expected {expected_phases}, got {actual_phases}"
        )
    for label, literal in (
        ("source immutability", "MUST leave source bytes, Session Record, provider ID, lease, workspace authority, task-board binding, and native identity unchanged"),
        ("new target identities", "creates one new direct Session Record 2.0.0, target workspace identity, native identity, and epoch-1 lease"),
        ("stable snapshot digest equality", "Capture digests are equal"),
        ("size is not snapshot proof", "File-size equality is never proof"),
        ("security class stripping", "Credential, auth, runtime, and lock classes are always excluded"),
        ("opaque native preservation", "Unknown native records become raw-addressable opaque events"),
        ("foreign authority stripping", "Foreign instructions are low-authority history"),
        ("per-item fidelity closure", "Every Capture Manifest item and Canonical Event occurs in exactly one non-synthesized disposition row"),
        ("non-exact reason requirement", "every other disposition requires at least one reason"),
        ("exact reason prohibition", "Exact requires an empty reason set"),
        ("fidelity aggregate reconciliation", "Aggregate maps reconcile exactly to the rows and cannot replace them"),
        ("fidelity/report digest acyclicity", "A target report does not name Clone Validation Report, Lineage Receipt, G4, or a future event"),
        ("projection/report digest acyclicity", "never a report locator"),
        ("lineage G3/G4 acyclicity", "It names G3, never G4; G4 names it"),
        ("immutable generation chain", "one predecessor cannot\nhave byte-different successors"),
        ("branch-exclusive generation", "generation 2 is exactly A2 naming G1\nor G2 naming G1. A2 is terminal. The target branch continues G2 to G3 to G4"),
        ("clone rollback required", "Clone requires rollback, null prior checkpoint, collision absence"),
        ("journal 3 independent schema", "Journal 3.0.0 is a complete clone-only schema and does not inherit Journal 2"),
        ("journal facts immutable", "Fields become non-null only at their phase and then remain immutable"),
        ("rollback retention through finalizing", "Provider remains rollback-capable"),
        ("post-commit rollback forbidden", "Post-commit rollback is forbidden"),
        ("target checkpoint identity proof", "proves the exact native identity, input blocked, full idle, zero processes and handles"),
        ("checkpoint before clone committed", "then core emits <code>checkpoint.created</code> and\n<code>clone.committed</code>"),
        ("failed-read integrity", "failed, partial, or malformed Journal, Provider, adapter, registry, or native-store\nread is <code>integrity_failure</code>, never absence"),
        ("new-session retry prohibition", "No status result authorizes a fresh Provider materialization, target native\nidentity, Session Record, lease, process, or transaction authority"),
        ("tuple source archive restriction", "Source-read entries have exactly <code>strategies=[archive_only]</code>"),
        ("tuple target smoke gate", "Target-write entries exclude archive-only, require current\nnon-null passing resume evidence"),
        ("tuple read failure fail-closed", "Failed/partial reads never mean absence"),
        ("tuple local policy monotonicity", "local policy may further\ndeny but cannot self-approve or override revocation"),
    ):
        clone_gate.normalized_has(f"clone gate {label}", literal)

    for scoped_gate in (
        session_record_gate,
        capture_gate,
        fidelity_gate,
        bundle_gate,
        transaction_gate,
    ):
        clone_gate.checks += scoped_gate.checks
        clone_gate.errors.extend(scoped_gate.errors)
    gate.normalized_has("clone gate clone crash boundary closure", "CR-CLONE-01..16")

    expected_events = [
        "clone.planned", "clone.target_prepared", "clone.target_published",
        "clone.target_validation_failed", "clone.rolled_back", "clone.committed",
        "clone.lineage_published", "clone.failed",
    ]
    event_rows = first_table_in_section(
        clone, "| Event type | Exact payload members beyond the tag |", "Clone adds one derived-state edge"
    )
    event_types = [re.sub(r"</?code>", "", row[0]) for row in event_rows if row]
    ledger["clone_events"] = len(event_types)
    clone_gate.checks += 1
    if event_types != expected_events:
        clone_gate.errors.append(
            f"clone gate lifecycle event registry mismatch: expected {expected_events}, got {event_types}"
        )

    cli_start = text.find("### 14.1 Command surface")
    cli_end = text.find("### 14.2 Common flags and output", cli_start)
    cli = text[cli_start:cli_end] if cli_start >= 0 and cli_end >= 0 else ""
    command_rows = first_table_in_section(
        cli, "| Command tag | Exact body |", "<code>CloneAdapterSummary</code> contains exactly"
    )
    clone_commands = [re.sub(r"</?code>", "", row[0]) for row in command_rows if row]
    expected_clone_commands = [f"session.clone.{leaf}" for leaf in (
        "adapters", "doctor", "list", "inspect", "plan", "run", "verify", "open"
    )]
    ledger["clone_commands"] = len(clone_commands)
    clone_gate.checks += 1
    if clone_commands != expected_clone_commands:
        clone_gate.errors.append(
            f"clone gate CLI command registry mismatch: expected {expected_clone_commands}, got {clone_commands}"
        )
    for label, literal in (
        ("sole namespace", "There is no <code>ax clone</code> alias"),
        ("plan sole no-write", "<code>plan</code> is the sole no-target-write surface"),
        ("run dry-run rejected", "<code>run --dry-run</code> is invalid before target allocation"),
        ("open no blank fallback", "cannot fall back to blank launch"),
    ):
        gate.normalized_has(f"clone gate CLI {label}", literal)

    error_start = text.find("Session Adapter 1.0 and <code>session.clone.*</code> bind Structured Error")
    error_end = text.find("Existing semantically identical codes remain reused", error_start)
    error_rows: list[tuple[str, ...]] = []
    if error_start >= 0 and error_end >= 0:
        table_started = False
        for line in text[error_start:error_end].splitlines():
            if line == "| Exit | Stable clone codes |":
                table_started = True
                continue
            if not table_started or not line.startswith("|"):
                continue
            cells = table_cells(line)
            if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                continue
            error_rows.append(cells)
    expected_error_exits = ["4", "6", "9", "11", "12", "13", "16"]
    actual_error_exits = [row[0] for row in error_rows]
    ledger["clone_error_classes"] = len(actual_error_exits)
    clone_gate.checks += 1
    if actual_error_exits != expected_error_exits:
        clone_gate.errors.append(
            f"clone gate error registry exit classes mismatch: expected {expected_error_exits}, got {actual_error_exits}"
        )
    for required_code in (
        "unsupported_environment_tuple", "credential_material_detected",
        "source_changed_during_clone", "target_validation_failed",
        "target_checkpoint_failed", "transaction_unknown",
        "projection_loss_unacceptable", "unsafe_pending_action",
    ):
        gate.has(f"clone gate error registry {required_code}", f"<code>{required_code}</code>")

    observation_start = text.find("### 18.2 Required events")
    observation_end = text.find("### 18.3 Metrics and health", observation_start)
    observation = text[observation_start:observation_end]
    for event in (
        "clone.started", "source.snapshot_established", "source.captured",
        "canonical.normalized", "projection.planned", "projection.policy_rejected",
        "target.prepared", "target.staged_validated", "target.published",
        "target.live_validated", "target.committed", "target.rolled_back",
        "lineage.published", "target.opened", "clone.failed",
    ):
        gate.has(f"clone gate observation event {event}", f"<code>{event}</code>")

    traceability = ROOT / "STANDALONE_TO_AX_TRACEABILITY.md"
    clone_gate.checks += 1
    if not traceability.is_file():
        clone_gate.errors.append("clone gate standalone traceability document missing")
    else:
        trace_text = traceability.read_text(encoding="utf-8")
        mapping_start = trace_text.find("## Complete section mapping")
        mapping_end = trace_text.find("## Resolved deferred decisions", mapping_start)
        mapping_rows = [
            line for line in trace_text[mapping_start:mapping_end].splitlines()
            if line.startswith("| ") and not line.startswith("| ---")
            and "Standalone section" not in line
        ]
        ledger["traceability_rows"] = len(mapping_rows)
        if len(mapping_rows) != 129:
            clone_gate.errors.append(
                f"clone gate standalone traceability row count mismatch: expected 129, got {len(mapping_rows)}"
            )
        for literal in (
            "No AX implementation or release process needs it to interpret `SPEC.md`",
            "None of these decisions weakens the adapter boundary",
        ):
            clone_gate.checks += 1
            if " ".join(literal.split()) not in " ".join(trace_text.split()):
                clone_gate.errors.append(
                    f"clone gate standalone traceability completeness: missing {literal!r}"
                )

    clone_gate.checks += 1
    diagram_sources = {
        "cloning_components.puml": ("No source×target converter pair", "sole live-store mutation"),
        "cloning_transaction.puml": ("rollback remains retained", "publish Lineage Receipt, then G4 committed bundle"),
    }
    for name, required_literals in diagram_sources.items():
        source = PLANTUML_DIR / name
        if not source.is_file():
            clone_gate.errors.append(f"clone gate diagram source missing: {name}")
            continue
        source_text = source.read_text(encoding="utf-8")
        for literal in required_literals:
            if literal not in source_text:
                clone_gate.errors.append(
                    f"clone gate diagram semantic marker missing in {name}: {literal!r}"
                )

    errors.extend(gate.errors)
    errors.extend(clone_gate.errors)
    checks = gate.checks + clone_gate.checks
    return checks, len(errors) - initial_error_count, ledger


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
    gate.normalized_has("no direct qwen claim", "no v0.3.0 direct")
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
    check_terminal_backend_diagram_semantics(errors)
    check_public_diagram_ledgers(errors)
    check_changelog_release_caveats(errors)
    check_contextual_forbidden_claims(errors)
    check_cross_file_consistency(errors)
    check_readme_terminal_backend_milestones(errors)
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
    clone_checks, clone_failures, clone_ledger = check_cloning_contract_gate(text, objects, errors)
    checks += clone_checks
    failed += clone_failures
    passed += clone_checks - clone_failures
    ledger.update(clone_ledger)
    directory_errors, directory_ledger = validate_directory(ROOT, text, canonical)
    errors.extend(directory_errors)
    checks += directory_ledger["directory_gate_classes"]
    failed += directory_ledger["directory_failed_groups"]
    passed += directory_ledger["directory_gate_classes"] - directory_ledger["directory_failed_groups"]
    ledger.update(directory_ledger)
    v043_errors, v043_ledger = validate_v043(ROOT, text)
    errors.extend(v043_errors)
    checks += v043_ledger["v043_gate_classes"]
    failed += v043_ledger["v043_failed_groups"]
    passed += v043_ledger["v043_gate_classes"] - v043_ledger["v043_failed_groups"]
    ledger.update(v043_ledger)
    terminal_backend_errors, terminal_backend_ledger = validate_terminal_backend(ROOT, text)
    errors.extend(terminal_backend_errors)
    checks += terminal_backend_ledger["terminal_backend_gate_classes"]
    failed += terminal_backend_ledger["terminal_backend_failed_groups"]
    passed += terminal_backend_ledger["terminal_backend_gate_classes"] - terminal_backend_ledger["terminal_backend_failed_groups"]
    ledger.update(terminal_backend_ledger)

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
    print(f"  Clone ledger: contracts={ledger.get('contracts',0)}, adapter_operations={ledger.get('adapter_operations',0)}, adapter_capabilities={ledger.get('adapter_capabilities',0)}, clone_commands={ledger.get('clone_commands',0)}, clone_events={ledger.get('clone_events',0)}, clone_error_classes={ledger.get('clone_error_classes',0)}, traceability_rows={ledger.get('traceability_rows',0)}")
    print(f"  Directory ledger: gate_classes={ledger.get('directory_gate_classes',0)}, contracts={ledger.get('directory_contracts',0)}, fixture_families={ledger.get('directory_fixture_families',0)}, expected_red_minimum={ledger.get('directory_expected_red_minimum',0)}")
    print(f"  v0.4.3 ledger: gate_classes={ledger.get('v043_gate_classes',0)}, positive_cases={ledger.get('v043_positive_cases',0)}, negative_cases={ledger.get('v043_negative_cases',0)}")
    print(f"  TerminalBackend ledger: gate_classes={ledger.get('terminal_backend_gate_classes',0)}, positive_cases={ledger.get('terminal_backend_positive_cases',0)}, expected_red_minimum={ledger.get('terminal_backend_expected_red_minimum',0)}")
    print("  Registry evidence: parsed provider, bridge, RPC-body, CLI-body, SessionState, Git-payload, cloning contract/adapter/CLI/event/error, and standalone traceability registries; no aggregate parity count is claimed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--compare-svg":
        sys.exit(compare_svg_source_metadata(sys.argv[2], sys.argv[3]))
    if len(sys.argv) != 1:
        print("usage: validate_spec.py [--compare-svg COMMITTED GENERATED]", file=sys.stderr)
        sys.exit(2)
    sys.exit(main())
