#!/usr/bin/env python3
"""TerminalBackend 1.0.0 fixture, recursive-schema, evidence, and history gate."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

GATE_CLASSES = ["contract_versions", "historical_preservation", "manifest_probe", "identity", "capabilities", "authority", "entrypoint", "attach_takeover", "evidence_binding", "replication", "compatibility", "admission_policy"]
TOP_KEYS = {"fixture", "specification_version", "contract_versions", "historical_v0_4_3", "capability_registry", "backends", "positive_cases", "policy"}
HISTORY_KEYS = {"registry_sha256", "configuration_backends", "translations", "reverse_projection", "rewrite_or_redigest_history"}
TRANSLATION_KEYS = {"legacy", "backend_id", "implementation_version", "backend_generation", "inferred_capabilities"}
BACKEND_KEYS = {"manifest", "probe", "capability_evidence", "runtime"}
MANIFEST_KEYS = {"schema", "schema_version", "manifest_id", "terminal_backend_id", "implementation_version", "protocol_versions", "platforms", "implementation_kind", "executable_digest", "static_capability_claims", "conformance_fixture_id", "extensions"}
PROBE_KEYS = {"schema", "schema_version", "probe_id", "terminal_backend_id", "implementation_version", "protocol_version", "implementation_kind", "executable_digest", "platform", "os_version", "availability", "backend_generation_digest", "capability_claims", "evidence_ids", "probed_at", "extensions"}
CLAIM_KEYS = {"capability", "value", "origin", "generation_variable", "dependent_operations", "evidence_requirements"}
EVIDENCE_KEYS = {"schema", "schema_version", "evidence_id", "terminal_backend_id", "implementation_version", "protocol_version", "backend_generation_digest", "capability", "value", "platform", "os_version", "conformance_fixture_id", "observed_at", "expires_at", "issuer", "issuer_id", "attestation_signature", "facts", "terminal_binding_id", "provider_id", "provider_build", "sentinel_result", "provider_auth_smoke_result", "extensions"}
TMUX_RUNTIME_KEYS = {"entrypoint", "tmux_server", "ambient_server_reuse", "credential_creation_actor", "credential_proof", "gui_only_proof"}
CONPTY_RUNTIME_KEYS = {"entrypoint", "durability_claim"}

CAPABILITY_RULES: dict[str, tuple[bool, list[str], list[str]]] = {
    "durable_disconnect": (False, ["create", "status"], ["conformance_fixture", "runtime_probe"]),
    "local_attach": (True, ["attach"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
    "multi_attach": (True, ["attach"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
    "remote_attach": (True, ["attach"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
    "web_attach": (True, ["attach"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
    "headless_creation": (True, ["create"], ["conformance_fixture", "runtime_probe"]),
    "reboot_restoration": (True, ["restore"], ["conformance_fixture", "runtime_probe"]),
    "input_quiescence": (True, ["quiesce-input"], ["conformance_fixture", "runtime_probe"]),
    "safe_boundary_observation": (True, ["wait-safe-boundary"], ["conformance_fixture", "runtime_probe"]),
    "provider_process_observation": (True, ["status", "terminate-stale", "wait-safe-boundary"], ["conformance_fixture", "runtime_probe"]),
    "graceful_stop": (True, ["request-stop"], ["conformance_fixture", "runtime_probe"]),
    "stale_process_termination": (True, ["terminate-stale"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
    "terminal_state_retention": (True, ["create", "restore", "status"], ["conformance_fixture", "runtime_probe"]),
    "scrollback_retention": (True, ["create", "restore", "status"], ["conformance_fixture", "runtime_probe"]),
    "credential_capable_execution_realm": (True, ["create", "restore"], ["conformance_fixture", "credential_sentinel", "provider_auth_smoke", "runtime_probe"]),
    "multiple_input_clients": (True, ["attach"], ["conformance_fixture", "policy_authorization", "runtime_probe"]),
}
CAPABILITIES = list(CAPABILITY_RULES)
FACT_FOR_REQUIREMENT = {"conformance_fixture": "fixture_passed", "runtime_probe": "runtime_probe_passed", "credential_sentinel": "sentinel_passed", "provider_auth_smoke": "provider_auth_passed", "policy_authorization": "policy_checked"}
EVIDENCE_FACTS = set(FACT_FOR_REQUIREMENT.values()) | {"ui_absent", "prompt_absent"}
TRUSTED_ISSUERS = {
    "ax_release": {
        "issuer_id": "sha256:15db5626578c9a4df46c5d93b83aeea96fdaa9db81b2d848e6b0c399eb59689e",
        "modulus": int("BAA452F78992F8FC11AFDC85DB7A3E39743B62C0552EB759E3E479348B30DE28EA55A235AA39A052EE95F5393B594E5FE27DC972534497F6345A77746B74DF0D9789EA13310D311B8DF3A4A384EEC696A7C1F2BAAF6C4011935F23205C22DBD34BE7E1D9AB04F7B4FCF29FD74E4D3BCE267D6C3CBCA628D0004C21DA49D7F0DE010028169B26E630845D1A65C3236E3109071F55F80D1E0963CEBC8A4FEFC3755B02084D928988A2E7D0A8045DBCCE50E9EFAEE4F769CB3DBABC5B4A4475367DD7C8A187790049EDF0919876D1BEE29155E3A9551ED3CA2B01665F7615193A1C4F8CC3174D3AED153F52E5D234CBF1088E8F215182DB909EC28E553E149638BB", 16),
        "exponent": 65537,
    },
    "ax_local_probe": {
        "issuer_id": "sha256:f8ce7530e2134f18545f5c347413ed0cf27cb98b38119f075dbf97741c53f2f5",
        "modulus": int("CFEB41599A29AC9AFC0FF0DDDA675419BFC3D9C1F0E0870B35044794E62793F970B25C3C56574923A9345B13EBAD9023D402F0BE0CE8F6FF4F83B867972370A9882AD7CCE1D9A0DD9869D4DD024D9094185293A86DB7C3DC26DF8AD9B7911049AA66310A5F4B28DCA3AA0C3BBC97CFF7820E21E2C3F8B12F07EAF44709D8A9F6E7CF39607277705D6BEEB338E8759732EAA72412EB77FE595D678595C17CB0AAC09CA2D3E4CC4BA03E1DB3E9D1B213940783D7FB84737339F671E99B2C228DDF2F73F0B6BDA97DFCBFDF5DA29C34CA39897874147D09CBD3999F6C2DCAA1C22D2DB423E2E65F8671C053C37F8F7BE2E858AAC6A87754FDA3ADE28A7AB87AD591", 16),
        "exponent": 65537,
    },
}

POSITIVE_SCHEMAS = {
    "TB-TMUX-UNIX-MANIFEST-PROBE": {"id", "production_entrypoint", "expected"},
    "TB-CONPTY-WINDOWS-MANIFEST-PROBE": {"id", "production_entrypoint", "expected"},
    "TB-LEGACY-TRANSLATION": {"id", "production_entrypoint", "expected"},
    "TB-CAPABILITY-ADMISSION": {"id", "production_entrypoint", "requested_operation", "admitted_capability", "evidence_id", "expected"},
    "TB-MANIFEST-STATIC-ECHO": {"id", "production_entrypoint", "backend_id", "capability", "expected"},
    "TB-GENERATION-VARIABLE-OVERRIDE": {"id", "production_entrypoint", "backend_id", "capability", "expected"},
    "TB-ATTACH-OWNER-NEUTRAL": {"id", "production_entrypoint", "owner_before", "owner_after", "lease_epoch_before", "lease_epoch_after", "presentation_replica_is_ax_replica"},
    "TB-TAKEOVER-REBIND": {"id", "production_entrypoint", "session_before", "session_after", "backend_before", "backend_after", "supersedes", "history_mutated"},
    "TB-CREDENTIAL-EVIDENCE-BINDING": {"id", "production_entrypoint", "evidence_id"},
    "TB-RESUME-EVENT-VERSION-BINDING": {"id", "production_entrypoint", "terminal_backend_id", "implementation_version", "protocol_version", "evidence_id", "expected"},
    "TB-SANITIZED-REPLICATION": {"id", "production_entrypoint", "namespace", "included_classes", "excluded_classes"},
    "TB-BOOTSTRAP-OLD-NEW": {"id", "production_entrypoint", "new_reader_old_object", "old_reader_new_object", "first_operation", "capability_negotiation"},
    "TB-UNSUPPORTED-BROWSE-NO-ACTIVATE": {"id", "production_entrypoint", "backend_id", "browse", "sync", "activate", "restore", "fallback", "expected_error"},
}
POSITIVE_EXPECTED_FIELDS: dict[str, dict[str, Any]] = {
    "TB-TMUX-UNIX-MANIFEST-PROBE": {"production_entrypoint": "registry.admit", "expected": "available"},
    "TB-CONPTY-WINDOWS-MANIFEST-PROBE": {"production_entrypoint": "registry.admit", "expected": "available"},
    "TB-LEGACY-TRANSLATION": {"production_entrypoint": "compat.read", "expected": "identity_preserved"},
    "TB-CAPABILITY-ADMISSION": {"production_entrypoint": "activation.resolve", "requested_operation": "create", "admitted_capability": "credential_capable_execution_realm", "expected": "intersection_with_bound_evidence"},
    "TB-MANIFEST-STATIC-ECHO": {"production_entrypoint": "registry.admit", "backend_id": "ax.tmux", "capability": "local_attach", "expected": "member_for_member_equal"},
    "TB-GENERATION-VARIABLE-OVERRIDE": {"production_entrypoint": "registry.admit", "backend_id": "ax.tmux", "capability": "credential_capable_execution_realm", "expected": "false_to_true_with_derived_members_equal"},
    "TB-ATTACH-OWNER-NEUTRAL": {"production_entrypoint": "terminal.attach", "owner_before": "host-a", "owner_after": "host-a", "lease_epoch_before": 7, "lease_epoch_after": 7, "presentation_replica_is_ax_replica": False},
    "TB-TAKEOVER-REBIND": {"production_entrypoint": "takeover.execute", "session_before": "0198f4c8-7d40-7e55-8e6f-1234567890ab", "session_after": "0198f4c8-7d40-7e55-8e6f-1234567890ab", "backend_before": "ax.tmux", "backend_after": "ax.conpty", "supersedes": True, "history_mutated": False},
    "TB-CREDENTIAL-EVIDENCE-BINDING": {"production_entrypoint": "activation.resolve"},
    "TB-RESUME-EVENT-VERSION-BINDING": {"production_entrypoint": "event.derive", "terminal_backend_id": "ax.tmux", "implementation_version": "1.0.0", "protocol_version": "1.0.0", "expected": "exact_evidence_tuple"},
    "TB-SANITIZED-REPLICATION": {"production_entrypoint": "replication.select", "namespace": "terminal_backend_evidence", "included_classes": ["manifest", "probe", "capability_evidence"], "excluded_classes": ["binding", "native_reference", "raw_generation", "pid", "socket", "pipe", "endpoint", "token", "relay_credential", "backend_credential", "provider_credential", "terminal_output"]},
    "TB-BOOTSTRAP-OLD-NEW": {"production_entrypoint": "backend.bootstrap", "new_reader_old_object": "translate", "old_reader_new_object": "browse_sync_read_only", "first_operation": "manifest", "capability_negotiation": "intersection_with_bound_evidence"},
    "TB-UNSUPPORTED-BROWSE-NO-ACTIVATE": {"production_entrypoint": "activation.resolve", "backend_id": "vendor.future", "browse": True, "sync": True, "activate": False, "restore": False, "fallback": False, "expected_error": "terminal_backend_unavailable"},
}
EXPECTED_VERSIONS = {"manifest": "1.0.0", "probe": "1.0.0", "binding": "1.0.0", "capability_evidence": "1.0.0", "protocol": "1.0.0", "configuration": "3.0.0", "provider_protocol": "3.0.0", "mesh_rpc": "4.0.0", "session_event": "4.0.0", "cli_result": "4.0.0", "structured_error": "1.3.0"}
BACKEND_RE = re.compile(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z", re.ASCII)
SEMVER_RE = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z", re.ASCII)
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
UUID7_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z", re.ASCII)
NORMATIVE_SECTIONS = {
    "TerminalBackend 1.0.0": ("### 4.A TerminalBackend authority and terminology", "### 4.1 Terminal backend interface", "c8d7af4b4176d39ccced2814c3d6db4f175b79d92ef0e7b45fdeea367fa8cdad"),
    "Session Event 4.0.0": ("#### Session Event 4.0.0 Terminal Instance events", "### 5.3 Lease Record and ownership", "2d2214542078ff9e48c2347186638f6f1833a67389c360dde73d49319f09910e"),
    "Configuration 3.0.0": ("### 6.5 Configuration 3.0.0 TerminalBackend extension", "## 7.", "dff8850845bc45aa7545800b4d07e43e622387b142e6fb5984ae4a79fbedf199"),
    "Provider Protocol 3.0.0": ("### 7.A Provider Protocol 3.0.0 Terminal Instance binding", "### 7.8 Companion Session Adapter protocol", "f869ddaf9cc67d69b9561a3cfac3903320447b4c4fd71fe951346bd24f196108"),
    "Mesh RPC 4.0.0": ("### 11.9 Mesh RPC 4.0.0 TerminalBackend evidence replication", "## 12.", "d1d12504f6350a7c89b983cb6759f35328f1c6694b7af77620ff0b9e7cc37ba6"),
    "CLI Result 4.0.0": ("### 14.6 CLI Result 4.0.0 TerminalBackend surfaces", "## 15.", "9809e30fc2b78b61dd5ca8c17042394da44e3decb0a58fb1b028386ea9669299"),
    "Structured Error 1.3.0": ("#### Structured Error 1.3.0 TerminalBackend codes", "## 16. Security and threat boundary", "9f3705da80de7cf566523e0cb9369fe5eb4c0f5669d16cb8c7bec02d88b25b84"),
}
HISTORICAL_SECTIONS = {
    "Configuration 1.0.0 field constraints": (
        "### 6.3 Field constraints",
        "### 6.4 Configuration 2.0.0 directory extension",
        "eacf26cdf33bc80180e42ff6a8c00bdbf7df3cab613f121fef1078a6fd3f5e76",
    ),
}

def _sorted_unique(value: object) -> bool:
    if not isinstance(value, list):
        return False
    try:
        return value == sorted(value) and len(value) == len(set(value))
    except TypeError:
        return False

def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None

def _digest(value: object) -> bool:
    return isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None

def _bounded(value: object, low: int, high: int) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return low <= len(value.encode()) <= high
    except UnicodeEncodeError:
        return False

def _typed_equal(value: object, expected: object) -> bool:
    """Compare fixture semantics without Python's bool/int equality aliasing."""
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(value) == set(expected) and all(_typed_equal(value[key], child) for key, child in expected.items())
    if isinstance(expected, list):
        return len(value) == len(expected) and all(_typed_equal(item, child) for item, child in zip(value, expected))
    return value == expected

def _identity(obj: dict[str, Any], id_member: str) -> str:
    canonical = {key: value for key, value in obj.items() if key != id_member}
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()

def _verify_evidence_signature(evidence: dict[str, Any], issuer: dict[str, Any]) -> bool:
    value = evidence.get("attestation_signature")
    if not isinstance(value, str) or not value.startswith("rsa-sha256:"):
        return False
    try:
        signature = base64.b64decode(value.removeprefix("rsa-sha256:"), validate=True)
    except (binascii.Error, ValueError):
        return False
    modulus, exponent = issuer["modulus"], issuer["exponent"]
    width = (modulus.bit_length() + 7) // 8
    if len(signature) != width:
        return False
    signature_value = int.from_bytes(signature, "big")
    if signature_value >= modulus:
        return False
    signed = {key: child for key, child in evidence.items() if key not in {"evidence_id", "attestation_signature"}}
    payload = b"ax-terminal-capability-evidence-v1\0" + json.dumps(signed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(payload).digest()
    expected = b"\x00\x01" + b"\xff" * (width - len(digest_info) - 3) + b"\x00" + digest_info
    observed = pow(signature_value, exponent, modulus).to_bytes(width, "big")
    return observed == expected

def _walk(value: object, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")

def validate(root: Path, spec: str) -> tuple[list[str], dict[str, int]]:
    try:
        data = json.loads((root / "fixtures/terminal_backend_conformance.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"terminal backend gate manifest_probe: cannot read strict JSON fixture: {exc}"], {"terminal_backend_gate_classes": len(GATE_CLASSES), "terminal_backend_failed_groups": len(GATE_CLASSES), "terminal_backend_positive_cases": 0, "terminal_backend_expected_red_minimum": 49}
    if not isinstance(data, dict):
        return ["terminal backend gate manifest_probe: fixture recursive closed shape mismatch"], {"terminal_backend_gate_classes": len(GATE_CLASSES), "terminal_backend_failed_groups": 1, "terminal_backend_positive_cases": 0, "terminal_backend_expected_red_minimum": 49}
    failures: dict[str, list[str]] = {group: [] for group in GATE_CLASSES}
    def need(group: str, condition: bool, message: str) -> None:
        if not condition:
            failures[group].append(message)
    def closed(group: str, value: object, keys: set[str], path: str) -> bool:
        valid = isinstance(value, dict) and set(value) == keys
        need(group, valid, f"{path} recursive closed shape mismatch")
        return valid

    closed("manifest_probe", data, TOP_KEYS, "fixture")
    need("manifest_probe", data.get("fixture") == "ax-terminal-backend-conformance-v1" and data.get("specification_version") == "0.5.0", "fixture discriminator/version mismatch")
    need("contract_versions", data.get("contract_versions") == EXPECTED_VERSIONS, "independently versioned TerminalBackend contract registry mismatch")
    resumed_v4_row = "| <code>session.resumed</code> | <code>checkpoint_id:digest</code>, <code>execution_profile:standard&#124;yolo</code>, <code>profile_source_event_id:digest&#124;null</code>, <code>terminal_binding_id:digest</code>, <code>terminal_backend_id:terminal-backend-id</code>, <code>implementation_version:semver</code>, <code>protocol_version:semver</code>, <code>evidence_ids:sorted unique digest[1..256]</code> |"
    need("contract_versions", resumed_v4_row in spec, "Session Event 4 session.resumed must bind backend implementation/protocol versions")
    normalized_spec = spec.replace("\r\n", "\n").replace("\r", "\n")
    for label, (start_marker, end_marker, expected) in NORMATIVE_SECTIONS.items():
        start = normalized_spec.find(start_marker)
        end = normalized_spec.find(end_marker, start + len(start_marker)) if start >= 0 else -1
        need("contract_versions", start >= 0 and end >= 0, f"normative section missing: {label}")
        if start >= 0 and end >= 0:
            need("contract_versions", hashlib.sha256(normalized_spec[start:end].encode()).hexdigest() == expected, f"normative schema fingerprint drift: {label}")
    for label, (start_marker, end_marker, expected) in HISTORICAL_SECTIONS.items():
        start = normalized_spec.find(start_marker)
        end = normalized_spec.find(end_marker, start + len(start_marker)) if start >= 0 else -1
        need("historical_preservation", start >= 0 and end >= 0, f"historical definition missing: {label}")
        if start >= 0 and end >= 0:
            observed = hashlib.sha256(normalized_spec[start:end].encode()).hexdigest()
            need("historical_preservation", observed == expected, f"historical definition fingerprint drift: {label}")

    history = data.get("historical_v0_4_3")
    closed("historical_preservation", history, HISTORY_KEYS, "historical_v0_4_3")
    history = history if isinstance(history, dict) else {}
    need("historical_preservation", history.get("registry_sha256") == "sha256:958186993a6e59bbbc8e7fafc828f5913c4252fe964df4107132209c62f9fd83", "historical v0.4.3 registry digest changed")
    need("historical_preservation", history.get("configuration_backends") == ["tmux", "conpty"], "historical Configuration 1.0.0 backend enum changed")
    translations = history.get("translations")
    need("historical_preservation", isinstance(translations, list) and len(translations) == 2, "historical translations must contain exactly tmux and conpty")
    for index, row in enumerate(translations if isinstance(translations, list) else []):
        closed("historical_preservation", row, TRANSLATION_KEYS, f"historical_v0_4_3.translations[{index}]")
    observed = {row.get("legacy"): (row.get("backend_id"), row.get("implementation_version"), row.get("backend_generation"), row.get("inferred_capabilities")) for row in translations if isinstance(row, dict)} if isinstance(translations, list) else {}
    expected = {"tmux": ("ax.tmux", "legacy_unreported", "legacy_unreported", []), "conpty": ("ax.conpty", "legacy_unreported", "legacy_unreported", [])}
    need("historical_preservation", observed == expected, "legacy tmux/conpty translation must preserve identity and infer no capabilities")
    need("historical_preservation", history.get("reverse_projection") == {"ax.tmux": "tmux", "ax.conpty": "conpty", "other": "incompatible_schema"}, "legacy reverse projection must reject unrepresentable backend IDs")
    need("historical_preservation", history.get("rewrite_or_redigest_history") is False, "historical objects must never be rewritten or re-digested")
    for marker in ("The exact historical v0.4.3 registry is the table above", "The exact v0.4.3 Configuration 1/2 <code>tmux|conpty</code>", "never rewrites or re-digests history."):
        need("historical_preservation", marker in spec, f"historical preservation marker missing: {marker}")

    need("capabilities", data.get("capability_registry") == CAPABILITIES, "closed 16-value capability registry mismatch")
    backends = data.get("backends")
    need("manifest_probe", isinstance(backends, list) and len(backends) == 2, "exact tmux and ConPTY fixture pair required")
    backend_ids: list[str] = []
    all_evidence: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(backends if isinstance(backends, list) else []):
        location = f"backends[{index}]"
        closed("manifest_probe", row, BACKEND_KEYS, location)
        row = row if isinstance(row, dict) else {}
        manifest = row.get("manifest") if isinstance(row.get("manifest"), dict) else {}
        probe = row.get("probe") if isinstance(row.get("probe"), dict) else {}
        closed("manifest_probe", manifest, MANIFEST_KEYS, f"{location}.manifest")
        closed("manifest_probe", probe, PROBE_KEYS, f"{location}.probe")
        backend_id = manifest.get("terminal_backend_id")
        if isinstance(backend_id, str): backend_ids.append(backend_id)
        need("identity", _bounded(backend_id, 1, 128) and BACKEND_RE.fullmatch(backend_id) is not None, f"{location}.manifest invalid terminal_backend_id")
        need("identity", backend_id not in {"pid", "socket", "pipe", "url", "token"}, f"{location}.manifest mutable endpoint used as identity")
        need("manifest_probe", manifest.get("schema") == "urn:ax:schema:terminal-backend-manifest" and manifest.get("schema_version") == "1.0.0", f"{location}.manifest schema/version mismatch")
        need("manifest_probe", isinstance(manifest.get("implementation_version"), str) and SEMVER_RE.fullmatch(manifest["implementation_version"]) is not None, f"{location}.manifest invalid implementation version")
        protocols, platforms = manifest.get("protocol_versions"), manifest.get("platforms")
        need("manifest_probe", _sorted_unique(protocols) and 1 <= len(protocols) <= 32 and all(isinstance(v, str) and SEMVER_RE.fullmatch(v) and v.startswith("1.") for v in protocols), f"{location}.manifest protocol versions must be sorted unique TerminalBackend major 1")
        need("manifest_probe", _sorted_unique(platforms) and 1 <= len(platforms) <= 4 and set(platforms) <= {"macos", "linux", "wsl2", "windows"}, f"{location}.manifest platforms must be sorted unique closed platform enum")
        kind, executable = manifest.get("implementation_kind"), manifest.get("executable_digest")
        need("manifest_probe", kind in {"builtin_go", "local_program", "trusted_executable", "native_runtime"}, f"{location}.manifest implementation_kind invalid")
        need("manifest_probe", _digest(executable) if kind in {"local_program", "trusted_executable"} else executable is None, f"{location}.manifest executable_digest nullability mismatch")
        need("identity", _digest(manifest.get("manifest_id")) and manifest.get("manifest_id") == _identity(manifest, "manifest_id"), f"{location}.manifest.manifest_id identity recomputation mismatch")
        need("identity", _digest(manifest.get("conformance_fixture_id")), f"{location}.manifest.conformance_fixture_id must be digest")
        need("manifest_probe", manifest.get("extensions") == {}, f"{location}.manifest extensions must be exact empty object")

        def validate_claims(value: object, path: str, manifest_side: bool) -> dict[str, dict[str, Any]]:
            claims = value if isinstance(value, list) else []
            need("capabilities", isinstance(value, list) and len(value) <= 16, f"{path} must be array[0..16]")
            names = [claim.get("capability") for claim in claims if isinstance(claim, dict)]
            need("capabilities", len(names) == len(claims) and names == sorted(names) and len(names) == len(set(names)), f"{path} claims must be sorted and unique")
            result = {}
            for claim_index, claim in enumerate(claims):
                claim_path = f"{path}[{claim_index}]"
                closed("capabilities", claim, CLAIM_KEYS, claim_path)
                if not isinstance(claim, dict): continue
                capability = claim.get("capability")
                need("capabilities", capability in CAPABILITY_RULES, f"{claim_path} unknown capability")
                need("capabilities", type(claim.get("value")) is bool and claim.get("origin") in {"static", "probed"}, f"{claim_path} value/origin invalid")
                need("capabilities", not manifest_side or claim.get("origin") == "static", f"{claim_path} Manifest claim origin must be static")
                if capability in CAPABILITY_RULES:
                    generation, operations, requirements = CAPABILITY_RULES[capability]
                    need("capabilities", claim.get("generation_variable") is generation and claim.get("dependent_operations") == operations and claim.get("evidence_requirements") == requirements, f"{claim_path} capability registry-derived members mismatch")
                    result[capability] = claim
            return result
        manifest_claims = validate_claims(manifest.get("static_capability_claims"), f"{location}.manifest.static_capability_claims", True)
        probe_claims = validate_claims(probe.get("capability_claims"), f"{location}.probe.capability_claims", False)
        for capability, static_claim in manifest_claims.items():
            claim = probe_claims.get(capability)
            need("manifest_probe", claim is not None, f"{location} static capability omitted from Probe: {capability}")
            if claim is not None and claim.get("origin") == "static":
                need("manifest_probe", claim == static_claim, f"{location} static capability echo mismatch: {capability}")
            elif claim is not None:
                need("manifest_probe", static_claim.get("generation_variable") is True, f"{location} non-generation-variable static capability cannot be probed override: {capability}")
                for member in ("generation_variable", "dependent_operations", "evidence_requirements"):
                    need("manifest_probe", claim.get(member) == static_claim.get(member), f"{location} probed override {member} mismatch: {capability}")
        for capability, claim in probe_claims.items():
            need("manifest_probe", claim.get("origin") != "static" or capability in manifest_claims, f"{location} Probe static claim lacks Manifest claim: {capability}")

        need("manifest_probe", probe.get("schema") == "urn:ax:schema:terminal-backend-probe" and probe.get("schema_version") == "1.0.0", f"{location}.probe schema/version mismatch")
        for key in ("terminal_backend_id", "implementation_version", "implementation_kind", "executable_digest"):
            need("manifest_probe", probe.get(key) == manifest.get(key), f"{location} manifest/probe identity mismatch: {key}")
        need("manifest_probe", probe.get("protocol_version") in (protocols if isinstance(protocols, list) else []), f"{location} probe protocol is not admitted by manifest")
        need("manifest_probe", probe.get("platform") in (platforms if isinstance(platforms, list) else []), f"{location} probe platform is not admitted by manifest")
        need("manifest_probe", _bounded(probe.get("os_version"), 1, 256), f"{location}.probe.os_version must be string[1..256]")
        need("manifest_probe", probe.get("availability") in {"available", "conditional", "unavailable", "unknown"}, f"{location}.probe.availability must be closed non-null enum")
        need("identity", _digest(probe.get("backend_generation_digest")), f"{location}.probe.backend_generation_digest must be digest")
        need("manifest_probe", _timestamp(probe.get("probed_at")) is not None, f"{location}.probe.probed_at must be RFC3339 UTC timestamp")
        need("manifest_probe", probe.get("extensions") == {}, f"{location}.probe extensions must be exact empty object")
        evidence_ids = probe.get("evidence_ids")
        need("evidence_binding", _sorted_unique(evidence_ids) and len(evidence_ids) <= 256 and all(_digest(v) for v in evidence_ids), f"{location}.probe.evidence_ids must be sorted unique digest[0..256]")

        evidence_objects = row.get("capability_evidence")
        need("evidence_binding", isinstance(evidence_objects, list) and len(evidence_objects) <= 256, f"{location}.capability_evidence must be array[0..256]")
        local_evidence = {}
        for evidence_index, evidence in enumerate(evidence_objects if isinstance(evidence_objects, list) else []):
            path = f"{location}.capability_evidence[{evidence_index}]"
            closed("evidence_binding", evidence, EVIDENCE_KEYS, path)
            if not isinstance(evidence, dict): continue
            evidence_id = evidence.get("evidence_id")
            need("evidence_binding", _digest(evidence_id) and evidence_id == _identity(evidence, "evidence_id"), f"{path}.evidence_id identity recomputation mismatch")
            need("evidence_binding", evidence.get("schema") == "urn:ax:schema:terminal-capability-evidence" and evidence.get("schema_version") == "1.0.0", f"{path} schema/version mismatch")
            for key in ("terminal_backend_id", "implementation_version", "protocol_version", "backend_generation_digest", "platform", "os_version"):
                need("evidence_binding", evidence.get(key) == probe.get(key), f"{path}.{key} does not bind exact Probe tuple")
            need("evidence_binding", evidence.get("conformance_fixture_id") == manifest.get("conformance_fixture_id"), f"{path}.conformance_fixture_id does not bind Manifest")
            capability = evidence.get("capability")
            claim = probe_claims.get(capability)
            need("evidence_binding", claim is not None and claim.get("value") is True and evidence.get("value") is True, f"{path} does not name exactly one present true claim")
            observed_at, expires_at, probed_at = _timestamp(evidence.get("observed_at")), _timestamp(evidence.get("expires_at")), _timestamp(probe.get("probed_at"))
            need("evidence_binding", observed_at is not None and expires_at is not None and observed_at < expires_at, f"{path} expiry must be strictly after observation")
            need("evidence_binding", observed_at is not None and expires_at is not None and probed_at is not None and observed_at <= probed_at < expires_at, f"{path} must be unexpired at Probe time")
            issuer = evidence.get("issuer")
            trusted_issuer = TRUSTED_ISSUERS.get(issuer)
            need("evidence_binding", trusted_issuer is not None and evidence.get("issuer_id") == (trusted_issuer or {}).get("issuer_id"), f"{path} issuer is untrusted or self-minted")
            need("evidence_binding", trusted_issuer is not None and _verify_evidence_signature(evidence, trusted_issuer), f"{path} attestation signature verification failed")
            facts = evidence.get("facts")
            need("evidence_binding", _sorted_unique(facts) and 1 <= len(facts) <= 7 and set(facts) <= EVIDENCE_FACTS, f"{path}.facts must be sorted unique closed fact enum")
            if claim is not None:
                required = {FACT_FOR_REQUIREMENT[item] for item in claim.get("evidence_requirements", []) if item in FACT_FOR_REQUIREMENT}
                need("evidence_binding", isinstance(facts, list) and required <= set(facts), f"{path} does not satisfy exact claim evidence requirements")
            credential = capability == "credential_capable_execution_realm"
            if credential:
                need("evidence_binding", _digest(evidence.get("terminal_binding_id")) and _bounded(evidence.get("provider_id"), 1, 128) and BACKEND_RE.fullmatch(evidence["provider_id"]) is not None and _bounded(evidence.get("provider_build"), 1, 256), f"{path} credential binding fields invalid")
                need("evidence_binding", evidence.get("sentinel_result") == "passed" and evidence.get("provider_auth_smoke_result") == "passed", f"{path} credential sentinel/provider smoke must pass")
                need("evidence_binding", isinstance(facts, list) and {"ui_absent", "prompt_absent"} <= set(facts), f"{path} credential proof must establish UI and prompt absence")
            else:
                for member in ("terminal_binding_id", "provider_id", "provider_build", "sentinel_result", "provider_auth_smoke_result"):
                    need("evidence_binding", evidence.get(member) is None, f"{path}.{member} must be null outside credential realm")
            if isinstance(evidence_id, str):
                need("evidence_binding", evidence_id not in all_evidence, f"{path}.evidence_id duplicates another returned object")
                local_evidence[evidence_id] = evidence
                all_evidence[evidence_id] = evidence
        need("evidence_binding", evidence_ids == sorted(local_evidence), f"{location}.probe evidence_ids must exactly cover returned Capability Evidence objects")
        true_claims = {name for name, claim in probe_claims.items() if claim.get("value") is True}
        evidenced_claims = [e.get("capability") for e in local_evidence.values()]
        need("evidence_binding", set(evidenced_claims) == true_claims and len(evidenced_claims) == len(set(evidenced_claims)), f"{location} every true claim requires exactly one non-conflicting evidence object")
        need("identity", _digest(probe.get("probe_id")) and probe.get("probe_id") == _identity(probe, "probe_id"), f"{location}.probe.probe_id identity recomputation mismatch")

        runtime = row.get("runtime")
        closed("manifest_probe", runtime, TMUX_RUNTIME_KEYS if backend_id == "ax.tmux" else CONPTY_RUNTIME_KEYS, f"{location}.runtime")
        runtime = runtime if isinstance(runtime, dict) else {}
        entrypoint = runtime.get("entrypoint")
        need("entrypoint", isinstance(entrypoint, list) and len(entrypoint) == 3 and entrypoint[:2] == ["ax", "pane"] and isinstance(entrypoint[2], str) and UUID7_RE.fullmatch(entrypoint[2]) is not None, f"{location} durable entrypoint must be exactly ax pane SESSION_ID")
        if backend_id == "ax.conpty":
            need("manifest_probe", runtime.get("durability_claim") == "native_windows_without_tmux_equivalence", f"{location}.runtime.durability_claim must be exact non-null ConPTY durability enum")

    need("identity", backend_ids == ["ax.tmux", "ax.conpty"] and len(set(backend_ids)) == 2, "canonical backend IDs must be unique ax.tmux and ax.conpty")
    tmux_runtime = backends[0].get("runtime", {}) if isinstance(backends, list) and backends and isinstance(backends[0], dict) else {}
    need("entrypoint", tmux_runtime.get("tmux_server") == "private--S" and tmux_runtime.get("ambient_server_reuse") is False, "tmux must use a private -S server and reject ambient/default server reuse")
    need("evidence_binding", tmux_runtime.get("credential_creation_actor") == "aqua_broker", "background credential-dependent tmux creation must be refused")
    need("evidence_binding", tmux_runtime.get("credential_proof") == ["ax_sentinel", "provider_auth_smoke"] and tmux_runtime.get("gui_only_proof") is False, "credential readiness requires sentinel plus provider-auth smoke; GUI-only proof is insufficient")

    cases = data.get("positive_cases")
    need("manifest_probe", isinstance(cases, list) and len(cases) == len(POSITIVE_SCHEMAS), "positive TerminalBackend case registry mismatch")
    case_by_id = {}
    for index, case in enumerate(cases if isinstance(cases, list) else []):
        case_id = case.get("id") if isinstance(case, dict) else None
        closed("manifest_probe", case, POSITIVE_SCHEMAS.get(case_id, set()), f"positive_cases[{index}]")
        if isinstance(case_id, str) and isinstance(case, dict): case_by_id[case_id] = case
    need("manifest_probe", set(case_by_id) == set(POSITIVE_SCHEMAS) and len(case_by_id) == len(cases if isinstance(cases, list) else []), "positive TerminalBackend case IDs must be exact and unique")
    for case_id, expected_fields in POSITIVE_EXPECTED_FIELDS.items():
        case = case_by_id.get(case_id, {})
        observed_fields = {key: case.get(key) for key in expected_fields}
        need("manifest_probe", _typed_equal(observed_fields, expected_fields), f"positive case typed/semantic mismatch: {case_id}")
    for case_id in ("TB-CAPABILITY-ADMISSION", "TB-CREDENTIAL-EVIDENCE-BINDING"):
        need("evidence_binding", _digest(case_by_id.get(case_id, {}).get("evidence_id")), f"positive case evidence_id must be digest: {case_id}")
    attach = case_by_id.get("TB-ATTACH-OWNER-NEUTRAL", {})
    need("attach_takeover", attach.get("owner_before") == attach.get("owner_after") and attach.get("lease_epoch_before") == attach.get("lease_epoch_after") and attach.get("presentation_replica_is_ax_replica") is False, "attach/client mirror must be ownership-neutral and not an AX Replica")
    takeover = case_by_id.get("TB-TAKEOVER-REBIND", {})
    need("attach_takeover", takeover.get("session_before") == takeover.get("session_after") and takeover.get("backend_before") != takeover.get("backend_after") and takeover.get("supersedes") is True and takeover.get("history_mutated") is False, "takeover rebinding must preserve LogicalSession and append immutable history")
    credential_case = case_by_id.get("TB-CREDENTIAL-EVIDENCE-BINDING", {})
    credential_evidence = all_evidence.get(credential_case.get("evidence_id"))
    need("evidence_binding", credential_evidence is not None and credential_evidence.get("capability") == "credential_capable_execution_realm", "credential binding case must resolve validated credential Capability Evidence")
    resume_case = case_by_id.get("TB-RESUME-EVENT-VERSION-BINDING", {})
    resume_evidence = all_evidence.get(resume_case.get("evidence_id"))
    need("evidence_binding", resume_evidence is not None and all(resume_case.get(key) == resume_evidence.get(key) for key in ("terminal_backend_id", "implementation_version", "protocol_version")), "Session Event 4 session.resumed backend version tuple must match validated evidence")
    admission = case_by_id.get("TB-CAPABILITY-ADMISSION", {})
    admission_evidence = all_evidence.get(admission.get("evidence_id"))
    need("capabilities", admission.get("requested_operation") == "create" and admission.get("admitted_capability") == "credential_capable_execution_realm" and admission.get("expected") == "intersection_with_bound_evidence" and admission_evidence is not None and admission_evidence.get("capability") == admission.get("admitted_capability"), "operation without its reproduced evidenced capability must be refused")
    tmux_backend = backends[0] if isinstance(backends, list) and backends and isinstance(backends[0], dict) else {}
    tmux_manifest = tmux_backend.get("manifest") if isinstance(tmux_backend.get("manifest"), dict) else {}
    tmux_probe = tmux_backend.get("probe") if isinstance(tmux_backend.get("probe"), dict) else {}
    tmux_manifest_claims = {claim.get("capability"): claim for claim in tmux_manifest.get("static_capability_claims", []) if isinstance(claim, dict)}
    tmux_probe_claims = {claim.get("capability"): claim for claim in tmux_probe.get("capability_claims", []) if isinstance(claim, dict)}
    static_case = case_by_id.get("TB-MANIFEST-STATIC-ECHO", {})
    need("manifest_probe", static_case.get("backend_id") == "ax.tmux" and static_case.get("capability") == "local_attach" and static_case.get("expected") == "member_for_member_equal" and tmux_probe_claims.get("local_attach") == tmux_manifest_claims.get("local_attach"), "positive Manifest static-echo case must reproduce exact equality")
    override_case = case_by_id.get("TB-GENERATION-VARIABLE-OVERRIDE", {})
    static_credential = tmux_manifest_claims.get("credential_capable_execution_realm", {})
    probed_credential = tmux_probe_claims.get("credential_capable_execution_realm", {})
    need("manifest_probe", override_case.get("backend_id") == "ax.tmux" and override_case.get("capability") == "credential_capable_execution_realm" and override_case.get("expected") == "false_to_true_with_derived_members_equal" and static_credential.get("value") is False and probed_credential.get("value") is True and probed_credential.get("origin") == "probed" and all(static_credential.get(member) == probed_credential.get(member) for member in ("generation_variable", "dependent_operations", "evidence_requirements")), "positive generation-variable override case must reproduce permitted override")
    replication = case_by_id.get("TB-SANITIZED-REPLICATION", {})
    exclusions = {"binding", "native_reference", "raw_generation", "pid", "socket", "pipe", "endpoint", "token", "relay_credential", "backend_credential", "provider_credential", "terminal_output"}
    need("replication", replication.get("namespace") == "terminal_backend_evidence" and replication.get("included_classes") == ["manifest", "probe", "capability_evidence"] and set(replication.get("excluded_classes", [])) == exclusions, "replication must contain only sanitized identity/capability evidence")
    for path, value in _walk(replication):
        if isinstance(value, dict): need("replication", not (set(value) & exclusions), f"replicated sensitive field at {path}")
    bootstrap = case_by_id.get("TB-BOOTSTRAP-OLD-NEW", {})
    need("compatibility", bootstrap.get("new_reader_old_object") == "translate" and bootstrap.get("old_reader_new_object") == "browse_sync_read_only" and bootstrap.get("first_operation") == "manifest" and bootstrap.get("capability_negotiation") == "intersection_with_bound_evidence", "old/new bootstrap and capability negotiation mismatch")
    unsupported = case_by_id.get("TB-UNSUPPORTED-BROWSE-NO-ACTIVATE", {})
    need("compatibility", unsupported.get("browse") is True and unsupported.get("sync") is True and unsupported.get("activate") is False and unsupported.get("restore") is False and unsupported.get("fallback") is False, "unsupported backend must remain browse/sync-only with no activation fallback")
    policy = data.get("policy")
    closed("authority", policy, {"backend_authority", "logical_session_authority", "relay_admitted", "public_sdk_stable", "superlogical"}, "policy")
    policy = policy if isinstance(policy, dict) else {}
    need("authority", policy.get("backend_authority") == "host_local_terminal_instance_only" and policy.get("logical_session_authority") == "AX", "TerminalBackend must not claim AX LogicalSession/Owner/Replica authority")
    need("admission_policy", policy.get("relay_admitted") is False, "third-party relay policy bypass is forbidden")
    need("admission_policy", policy.get("public_sdk_stable") is False, "stable public SDK is premature")
    superlogical = policy.get("superlogical")
    closed("admission_policy", superlogical, {"normative", "available", "backend_id_reserved"}, "policy.superlogical")
    need("admission_policy", superlogical == {"normative": False, "available": False, "backend_id_reserved": False}, "Superlogical must remain future-only, non-normative, unavailable, and unreserved")
    public_claims: dict[str, str] = {}
    for name in ("README.md", "CHANGELOG.md", "RELEASE_NOTES.md"):
        try:
            public_claims[name] = (root / name).read_text(encoding="utf-8")
        except OSError as exc:
            need("admission_policy", False, f"cannot read public release artifact {name}: {exc}")
    combined_public_claims = "\n".join(public_claims.values())
    need(
        "admission_policy",
        "TerminalBackend implementations are shipped and available." not in combined_public_claims,
        "release artifact must not claim TerminalBackend implementation availability",
    )
    need(
        "admission_policy",
        "A stable public TerminalBackend SDK is available." not in combined_public_claims,
        "release artifact must not claim stable public TerminalBackend SDK",
    )
    need(
        "admission_policy",
        "Superlogical is unavailable, non-normative, and future-only" in public_claims.get("README.md", "")
        and "Superlogical unavailable, non-normative, and future-only" in public_claims.get("CHANGELOG.md", "")
        and "Superlogical is an unavailable, non-normative, future-only candidate" in public_claims.get("RELEASE_NOTES.md", ""),
        "public release artifacts must keep Superlogical future-only, non-normative, and unavailable",
    )
    errors = [f"terminal backend gate {group}: {message}" for group in GATE_CLASSES for message in failures[group]]
    return errors, {"terminal_backend_gate_classes": len(GATE_CLASSES), "terminal_backend_failed_groups": sum(bool(failures[g]) for g in GATE_CLASSES), "terminal_backend_positive_cases": len(case_by_id), "terminal_backend_expected_red_minimum": 49}
