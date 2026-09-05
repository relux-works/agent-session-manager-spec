#!/usr/bin/env python3
"""Launch Plan request 1.0.0 fixture gate for ``ax start --launch-plan``.

Executes ``fixtures/launch_plan_request_conformance.json`` through a reference
implementation of the Section 14.1 document validation, the Section 13.1
planning-role resolution, and the Section 7.7 profile-flag refusal. Positive
cases must resolve to the recorded final argv, suffix split, and request
digest; negative cases must be refused with the recorded code and details. A case may carry
``plugin_answers`` -- the argv the plugin returns to the Section 13.1
planning-role ``launch`` call and to the step-4 ``launch`` against the
persisted record -- and a step-4 answer that differs from the planning answer
is refused with ``provider_protocol_error``. The fixture's provider profile
mappings must equal the Section 7.7 table, and the SPEC prose must retain the
semantic markers the gate depends on.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

FIXTURE_ID = "ax-launch-plan-request-v1"
SCHEMA = "urn:ax:schema:launch-plan-request"
SCHEMA_VERSION = "1.0.0"
AX_EXTENSION_KEY = "ax.launch-plan-request"
GATE_CLASSES = [
    "fixture_shape",
    "spec_markers",
    "profile_mappings",
    "positive_cases",
    "negative_cases",
    "coverage",
]
DOCUMENT_MEMBERS = {"schema", "schema_version", "argv", "argv_suffix", "env_names", "env_literals", "stdin", "extensions"}
CASE_KEYS = {"id", "provider", "profile", "plugin_declares_caller_launch_plan", "document", "expected"}
NEGATIVE_KEYS = {"id", "provider", "profile", "plugin_declares_caller_launch_plan", "document", "expected_error", "expected_details", "mutation"}
# Optional per-case member: the two Section 13.1 ``launch`` answers of the plugin.
PLUGIN_ANSWERS_KEY = "plugin_answers"
PLUGIN_ANSWER_MEMBERS = {"planning_launch_argv", "step_4_launch_argv"}
ENV_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z", re.ASCII)
REVERSE_DNS_RE = re.compile(r"[a-z][a-z0-9-]{0,62}(?:\.[a-z][a-z0-9-]{0,62})+\Z", re.ASCII)
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
# Bounded secret classifier for the fixture gate only; the ax implementation
# owns its Section 5.1/16.2 scanner. A name in the Section 16.2 environment-
# secret class or a value carrying a documented credential prefix is a secret.
SECRET_NAME_RE = re.compile(r".*(?:_KEY|_TOKEN|_SECRET|_PASSWORD|_PASSWD)\Z", re.ASCII)
SECRET_VALUE_RE = re.compile(r"(?:sk-|ghp_|xoxb-|AKIA|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
ARGV_MAX_ELEMENTS = 128
ARGV_ELEMENT_MAX_BYTES = 4096
ARGV_TOTAL_MAX_BYTES = 65536
ENV_MAX = 64
LITERAL_MAX_BYTES = 4096
STDIN_MAX_BYTES = 65536
EXTENSIONS_MAX_KEYS = 64
EXTENSIONS_MAX_BYTES = 65536

SPEC_MARKERS = {
    "grammar row": "ax start NAME --provider ID --launch-plan FILE|- [--profile standard|yolo] [--workspace PATH]",
    "exit class 2 code": "| 2 | <code>launch_plan_invalid</code> |",
    "profile-flag refusal": "<code>launch_plan_invalid</code>, <code>details.reason: \"profile_flag\"</code>,\nand <code>details.argv_index</code> the element's index in the final argv",
    "refusal is required": "The refusal is required, not optional",
    "secret code retained": "refuses with the existing code <code>secret_policy_violation</code>, exit\nclass 16",
    "task-board exclusivity": "a command carrying both is\n<code>invalid_arguments</code> (exit 2)",
    "argv form owns the line": "<code>argv</code> combined with <code>--profile yolo</code> is <code>invalid_arguments</code>",
    "planning-role launch": "one step precedes step 2 for both document forms",
    "determinism": "a mismatch is <code>provider_protocol_error</code> and no process is created",
    "capability refusal": "<code>details.capability: \"caller_launch_plan\"</code>, before the plugin is\n  invoked and before any process exists",
    "nine-name registry": "<code>capability_names</code> is the exact nine-name ordered registry shown.",
    "verbatim translation": "MUST NOT reorder, deduplicate, or rewrite a caller element, and it MUST NOT\n  emit a second spelling of a flag the caller supplied",
    "drift refusal": "drift MUST refuse the resume or fork by default with\n<code>policy_refused</code> (Section 15.3, exit 16) and\n<code>details.reason: \"environment_drift\"</code>",
    "drift like with like": "The comparison is like with like",
    "stdin bound": "the decoded payload is at most 65,536 bytes, the same bound as the total encoded argv",
    "stdin no replay": "A resume does not replay <code>stdin</code> by\ndefault",
    "fragment digest CCJ-1": "never of the\npretty-printed <code>--format json</code> output",
    "registry row": "| Launch Plan request | <code>urn:ax:schema:launch-plan-request</code> | <code>1.0.0</code> |",
}


class FixtureError(ValueError):
    """The fixture contradicts itself (not a gate refusal)."""


class Refusal(Exception):
    def __init__(self, code: str, details: dict[str, Any]) -> None:
        super().__init__(code)
        self.code = code
        self.details = details


def _utf8_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _decode_stdin(stdin: object) -> bytes:
    if not isinstance(stdin, dict) or set(stdin) != {"encoding", "bytes"}:
        raise Refusal("launch_plan_invalid", {"field": "stdin"})
    encoding, payload = stdin["encoding"], stdin["bytes"]
    if not isinstance(payload, str):
        raise Refusal("launch_plan_invalid", {"field": "stdin"})
    if encoding == "utf-8":
        decoded = payload.encode("utf-8")
    elif encoding == "base64url":
        if payload and (not re.fullmatch(r"[A-Za-z0-9_-]+", payload) or "=" in payload):
            raise Refusal("launch_plan_invalid", {"field": "stdin"})
        try:
            decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        except (binascii.Error, ValueError) as exc:
            raise Refusal("launch_plan_invalid", {"field": "stdin"}) from exc
        if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != payload:
            raise Refusal("launch_plan_invalid", {"field": "stdin"})
    else:
        raise Refusal("launch_plan_invalid", {"field": "stdin"})
    if len(decoded) > STDIN_MAX_BYTES:
        raise Refusal("launch_plan_invalid", {"field": "stdin"})
    if SECRET_VALUE_RE.search(decoded.decode("utf-8", errors="replace")):
        raise Refusal("secret_policy_violation", {"field": "stdin"})
    return decoded


def resolve(
    document: object,
    provider: str,
    profile: str,
    plugin_declares: bool,
    mappings: dict[str, list[str]],
    base_argv: dict[str, dict[str, list[str]]],
    curator_keys: dict[str, Any],
    canonical: Callable[[object], bytes],
    plugin_answers: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Reference ``ax start --launch-plan`` validation and planning-role resolution.

    ``plugin_answers`` models the plugin's two Section 13.1 ``launch`` answers:
    ``planning_launch_argv`` (the planning-role call before persistence, which
    by definition is the resolved final argv) and ``step_4_launch_argv`` (the
    call against the persisted record). A step-4 answer that differs from the
    planning answer is ``provider_protocol_error`` and no process is created.
    """

    if not isinstance(document, dict):
        raise Refusal("launch_plan_invalid", {"field": "schema"})
    for member in document:
        if member not in DOCUMENT_MEMBERS:
            raise Refusal("launch_plan_invalid", {"field": member})
    if document.get("schema") != SCHEMA:
        raise Refusal("launch_plan_invalid", {"field": "schema"})
    if document.get("schema_version") != SCHEMA_VERSION:
        raise Refusal("launch_plan_invalid", {"field": "schema_version"})
    has_argv, has_suffix = "argv" in document, "argv_suffix" in document
    if has_argv == has_suffix:
        raise Refusal("launch_plan_invalid", {"field": "argv" if has_argv else "argv_suffix"})
    form = "argv" if has_argv else "argv_suffix"
    if form == "argv" and profile == "yolo":
        raise Refusal("invalid_arguments", {"field": "argv"})
    caller = document[form]
    if not isinstance(caller, list) or not all(isinstance(item, str) for item in caller):
        raise Refusal("launch_plan_invalid", {"field": form})
    if form == "argv" and not caller:
        raise Refusal("launch_plan_invalid", {"field": form})
    for item in caller:
        if not 1 <= _utf8_len(item) <= ARGV_ELEMENT_MAX_BYTES:
            raise Refusal("launch_plan_invalid", {"field": form})

    env_names = document.get("env_names", [])
    if not isinstance(env_names, list) or len(env_names) > ENV_MAX:
        raise Refusal("launch_plan_invalid", {"field": "env_names"})
    if any(not isinstance(name, str) or not ENV_NAME_RE.fullmatch(name) for name in env_names):
        raise Refusal("launch_plan_invalid", {"field": "env_names"})
    if env_names != sorted(env_names) or len(set(env_names)) != len(env_names):
        raise Refusal("launch_plan_invalid", {"field": "env_names"})

    env_literals = document.get("env_literals", {})
    if not isinstance(env_literals, dict) or len(env_literals) > ENV_MAX:
        raise Refusal("launch_plan_invalid", {"field": "env_literals"})
    keys = list(env_literals)
    if keys != sorted(keys, key=lambda key: key.encode("utf-16-be")):
        raise Refusal("launch_plan_invalid", {"field": "env_literals"})
    for key, value in env_literals.items():
        if not ENV_NAME_RE.fullmatch(key) or not isinstance(value, str) or _utf8_len(value) > LITERAL_MAX_BYTES:
            raise Refusal("launch_plan_invalid", {"field": "env_literals"})
        if key in env_names:
            raise Refusal("launch_plan_invalid", {"field": "env_literals"})
    for key, value in env_literals.items():
        if SECRET_NAME_RE.fullmatch(key) or SECRET_VALUE_RE.search(value):
            raise Refusal("secret_policy_violation", {"field": "env_literals"})

    stdin = document.get("stdin")
    if stdin is not None:
        _decode_stdin(stdin)

    extensions = document.get("extensions", {})
    if not isinstance(extensions, dict):
        raise Refusal("launch_plan_invalid", {"field": "extensions"})
    for key in extensions:
        if not REVERSE_DNS_RE.fullmatch(key) or not 3 <= len(key) <= 253:
            raise Refusal("launch_plan_invalid", {"field": "extensions"})
    if AX_EXTENSION_KEY in extensions:
        raise Refusal("launch_plan_invalid", {"field": "extensions"})

    if not plugin_declares:
        raise Refusal("capability_unavailable", {"capability": "caller_launch_plan"})

    # Planning-role launch: the plugin contributes base argv only in the suffix form.
    base = list(base_argv[provider][profile]) if form == "argv_suffix" else []
    final_argv = base + list(caller)
    base_length = len(base)
    for index, element in enumerate(final_argv):
        if index >= base_length and element in mappings[provider]:
            raise Refusal("launch_plan_invalid", {"field": form, "reason": "profile_flag", "argv_index": index})
    if not 1 <= len(final_argv) <= ARGV_MAX_ELEMENTS:
        raise Refusal("launch_plan_invalid", {"field": form})
    if sum(_utf8_len(item) for item in final_argv) > ARGV_TOTAL_MAX_BYTES:
        raise Refusal("launch_plan_invalid", {"field": form})

    request_digest = "sha256:" + __import__("hashlib").sha256(canonical(document)).hexdigest()
    persisted_extensions = dict(extensions)
    persisted_extensions.update(curator_keys)
    persisted_extensions[AX_EXTENSION_KEY] = {
        "form": form,
        "base_argv_length": base_length,
        "request_digest": request_digest,
    }
    if len(persisted_extensions) > EXTENSIONS_MAX_KEYS or len(canonical(persisted_extensions)) > EXTENSIONS_MAX_BYTES:
        raise Refusal("launch_plan_invalid", {"field": "extensions"})

    # Section 13.1 determinism: the planning-role answer is the recorded argv;
    # step 4's launch against the persisted record must return the same argv.
    if plugin_answers is not None:
        if not isinstance(plugin_answers, dict) or set(plugin_answers) != PLUGIN_ANSWER_MEMBERS:
            raise FixtureError(f"{PLUGIN_ANSWERS_KEY} must carry exactly {sorted(PLUGIN_ANSWER_MEMBERS)}")
        planning, step_4 = plugin_answers["planning_launch_argv"], plugin_answers["step_4_launch_argv"]
        if planning != final_argv:
            raise FixtureError(f"planning_launch_argv {planning!r} is not the resolved final argv {final_argv!r}")
        if step_4 != planning:
            mismatch = next((index for index, pair in enumerate(zip(step_4, planning)) if pair[0] != pair[1]), min(len(step_4), len(planning)))
            raise Refusal("provider_protocol_error", {"reason": "launch_argv_mismatch", "argv_index": mismatch})

    return {
        "form": form,
        "base_argv_length": base_length,
        "final_argv": final_argv,
        "request_digest": request_digest,
        "suffix": final_argv[base_length:],
    }


def _profile_table(spec: str) -> dict[str, list[str]]:
    start = spec.find("### 7.7 Profile mapping")
    end = spec.find("### 7.A", start)
    table: dict[str, list[str]] = {}
    for line in spec[start:end].splitlines():
        if not line.startswith("| ") or line.startswith("| Provider") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        flags = re.findall(r"<code>(--[^<]+)</code>", cells[1])
        if flags:
            table[cells[0]] = flags
    return table


def validate(root: Path, spec: str, canonical: Callable[[object], bytes]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    ledger = {
        "launch_plan_gate_classes": len(GATE_CLASSES),
        "launch_plan_failed_groups": 0,
        "launch_plan_positive_cases": 0,
        "launch_plan_negative_cases": 0,
    }

    def need(group: str, condition: bool, detail: str) -> None:
        if not condition:
            errors.append(f"launch-plan gate {group}: {detail}")

    path = root / "fixtures" / "launch_plan_request_conformance.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"launch-plan gate fixture_shape: cannot read strict JSON fixture: {exc}")
        ledger["launch_plan_failed_groups"] = len(GATE_CLASSES)
        return errors, ledger

    need("fixture_shape", data.get("fixture") == FIXTURE_ID, "fixture discriminator mismatch")
    need("fixture_shape", data.get("schema") == SCHEMA and data.get("schema_version") == SCHEMA_VERSION, "fixture must bind the Launch Plan request 1.0.0 schema")
    need("fixture_shape", set(data) == {"fixture", "schema", "schema_version", "profile_mappings", "base_argv", "curator_extension_keys", "positive_cases", "negative_cases"}, "fixture top-level members are closed")

    for label, marker in SPEC_MARKERS.items():
        need("spec_markers", marker in spec, f"SPEC semantic marker missing ({label}): {marker!r}")

    mappings = data.get("profile_mappings", {})
    base_argv = data.get("base_argv", {})
    curator_keys = data.get("curator_extension_keys", {})
    spec_table = _profile_table(spec)
    for provider, spec_flags in (("Codex", spec_table.get("Codex")), ("Claude", spec_table.get("Claude"))):
        fixture_flags = mappings.get(provider.lower())
        need("profile_mappings", isinstance(spec_flags, list) and fixture_flags == spec_flags, f"fixture {provider.lower()} profile mapping must equal the Section 7.7 table {spec_flags}, got {fixture_flags}")
    need("profile_mappings", set(mappings) == set(base_argv) and set(mappings) >= {"codex", "claude"}, "profile_mappings and base_argv must cover the same providers including codex and claude")
    for provider, profiles in base_argv.items():
        need("profile_mappings", set(profiles) == {"standard", "yolo"}, f"base_argv[{provider}] must carry standard and yolo")
        yolo = profiles.get("yolo", [])
        standard = profiles.get("standard", [])
        need("profile_mappings", isinstance(yolo, list) and isinstance(standard, list) and yolo[:1] == standard[:1] and standard[1:] == [] and set(yolo[1:]) <= set(mappings.get(provider, [])), f"base_argv[{provider}] yolo must be executable plus only mapping flags; standard must be the bare executable")
    need("fixture_shape", isinstance(curator_keys, dict) and set(curator_keys) == {"works.relux.curator.profile-name", "works.relux.curator.profile-pin", "works.relux.curator.fragment-digest", "works.relux.curator.system-modules"}, "curator_extension_keys must be exactly the four Section 5.1 keys")

    positive = data.get("positive_cases", [])
    seen_ids: set[str] = set()
    for row in positive if isinstance(positive, list) else []:
        case_id = row.get("id") if isinstance(row, dict) else None
        need("positive_cases", isinstance(row, dict) and set(row) - {PLUGIN_ANSWERS_KEY} == CASE_KEYS, f"positive case {case_id} members are closed")
        if not isinstance(row, dict) or set(row) - {PLUGIN_ANSWERS_KEY} != CASE_KEYS:
            continue
        seen_ids.add(case_id)
        try:
            result = resolve(row["document"], row["provider"], row["profile"], row["plugin_declares_caller_launch_plan"], mappings, base_argv, curator_keys, canonical, row.get(PLUGIN_ANSWERS_KEY))
        except Refusal as refusal:
            need("positive_cases", False, f"{case_id} refused with {refusal.code} {refusal.details}")
            continue
        except (KeyError, TypeError, FixtureError) as exc:
            need("positive_cases", False, f"{case_id} fixture reference error: {exc!r}")
            continue
        expected = row["expected"]
        for member in ("form", "base_argv_length", "final_argv", "request_digest"):
            need("positive_cases", expected.get(member) == result[member], f"{case_id} {member}: expected {expected.get(member)!r}, resolved {result[member]!r}")
        need("positive_cases", DIGEST_RE.fullmatch(str(expected.get("request_digest", ""))) is not None, f"{case_id} request_digest must be a Section 1.6 digest")
        need("positive_cases", result["final_argv"][result["base_argv_length"]:] == row["document"].get("argv_suffix", row["document"].get("argv")), f"{case_id} suffix split must reproduce the caller elements")
        need("positive_cases", row["profile"] == "standard" or result["form"] == "argv_suffix", f"{case_id} argv form is never positive under yolo")
    ledger["launch_plan_positive_cases"] = len(seen_ids)
    required_positives = {"LAUNCH-PLAN-SUFFIX-POS", "LAUNCH-PLAN-ARGV-POS", "LAUNCH-PLAN-EXTENSIONS-POS", "LAUNCH-PLAN-EXTENSIONS-KEYS-POS"}
    need("coverage", required_positives <= seen_ids, f"positive coverage missing {sorted(required_positives - seen_ids)}")

    negative = data.get("negative_cases", [])
    negative_ids: set[str] = set()
    observed_codes: set[str] = set()
    for row in negative if isinstance(negative, list) else []:
        case_id = row.get("id") if isinstance(row, dict) else None
        need("negative_cases", isinstance(row, dict) and set(row) - {PLUGIN_ANSWERS_KEY} == NEGATIVE_KEYS, f"negative case {case_id} members are closed")
        if not isinstance(row, dict) or set(row) - {PLUGIN_ANSWERS_KEY} != NEGATIVE_KEYS:
            continue
        negative_ids.add(case_id)
        need("negative_cases", isinstance(row.get("mutation"), str) and bool(row.get("mutation")), f"{case_id} mutation description is required")
        try:
            result = resolve(row["document"], row["provider"], row["profile"], row["plugin_declares_caller_launch_plan"], mappings, base_argv, curator_keys, canonical, row.get(PLUGIN_ANSWERS_KEY))
        except Refusal as refusal:
            observed_codes.add(refusal.code)
            need("negative_cases", refusal.code == row["expected_error"], f"{case_id} expected {row['expected_error']}, gate refused with {refusal.code} {refusal.details}")
            need("negative_cases", refusal.details == row["expected_details"], f"{case_id} expected details {row['expected_details']}, gate produced {refusal.details}")
        except (KeyError, TypeError, FixtureError) as exc:
            need("negative_cases", False, f"{case_id} fixture reference error: {exc!r}")
        else:
            need("negative_cases", False, f"{case_id} was admitted by the gate: resolved {result['final_argv']} (expected {row['expected_error']})")
    ledger["launch_plan_negative_cases"] = len(negative_ids)
    required_negatives = {
        "LAUNCH-PLAN-PROFILE-FLAG-NEG",
        "LAUNCH-PLAN-PROFILE-FLAG-ALIAS-NEG",
        "LAUNCH-PLAN-PROFILE-FLAG-ARGV-FORM-NEG",
        "LAUNCH-PLAN-SECRET-NEG",
        "LAUNCH-PLAN-SECRET-STDIN-NEG",
        "LAUNCH-PLAN-EXTENSIONS-NEG",
        "LAUNCH-PLAN-CAPABILITY-NEG",
        "LAUNCH-PLAN-BOTH-FORMS-NEG",
        "LAUNCH-PLAN-UNKNOWN-MEMBER-NEG",
        "LAUNCH-PLAN-SCHEMA-VERSION-NEG",
        "LAUNCH-PLAN-ARGV-YOLO-PROFILE-NEG",
        "LAUNCH-PLAN-STDIN-BOUND-NEG",
        "LAUNCH-PLAN-AX-KEY-COLLISION-NEG",
        "LAUNCH-PLAN-DETERMINISM-NEG",
        "LAUNCH-PLAN-SCHEMA-NEG",
        "LAUNCH-PLAN-ARGV-ELEMENTS-BOUND-NEG",
        "LAUNCH-PLAN-ARGV-ELEMENT-BYTES-BOUND-NEG",
        "LAUNCH-PLAN-ARGV-BYTES-BOUND-NEG",
        "LAUNCH-PLAN-ENV-NAMES-BOUND-NEG",
        "LAUNCH-PLAN-LITERAL-BOUND-NEG",
        "LAUNCH-PLAN-EXTENSIONS-KEYS-BOUND-NEG",
    }
    need("coverage", required_negatives <= negative_ids, f"negative coverage missing {sorted(required_negatives - negative_ids)}")
    need("coverage", {"launch_plan_invalid", "secret_policy_violation", "capability_unavailable", "invalid_arguments", "provider_protocol_error"} <= observed_codes, f"negative cases must exercise every caller-plan refusal code, observed {sorted(observed_codes)}")
    need("coverage", not (seen_ids & negative_ids), "positive and negative case IDs must be disjoint")

    ledger["launch_plan_failed_groups"] = min(len(GATE_CLASSES), len({error.split(":", 1)[0] for error in errors}))
    return errors, ledger
