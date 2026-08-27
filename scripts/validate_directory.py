"""Session Directory conformance gate used by validate_spec.py."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable


# Source fingerprints bind validation to the accepted normative schema text,
# not merely to duplicated Python and fixture registries. They cover only the
# sections defining Directory-facing members, types, tagged unions, and enums;
# they are not publication/frozen-document digests.
NORMATIVE_SCHEMA_SECTIONS = {
    "Configuration 2.0.0 directory extension": (
        "### 6.4 Configuration 2.0.0 directory extension", "## 7.",
        "d6e9a78f719dc5c5ee4905c6bf73e2f64f1f5ecd7d6be0d53b3ffd88fb72c417",
    ),
    "Directory Node protocol": (
        "### 7.9 Companion Directory Node protocol", "## 8.",
        "8701c84372234bca4e19b650de7ec5deeafe456782ae4635c220b1fed5848da1",
    ),
    "directory records and query": (
        "### 10.8 Directory records, lineage, enrichment, query, and continuation", "## 11.",
        "03e0077f6356e281560d8cf37643baee7d46c004cc453f5f5379ebfc076eacaf",
    ),
    "Mesh RPC 3 directory replication": (
        "### 11.8 Mesh RPC 3.0.0 directory replication", "## 12.",
        "a2a6f9c94d09ff946a1b24e4d29f4eba94e66b18090ff2d4f6f3f9b388c211b6",
    ),
    "directory continuation planning and execution": (
        "### 13.15 Directory continuation planning and execution", "## 14.",
        "ef152b32402559322bf866e0a59a852cb65f10094b8dc9029cab985b818d3650",
    ),
    "CLI Result 3 and Directory Query": (
        "### 14.5 Session Directory CLI Result 3, query, and TUI", "## 15.",
        "2e3bc8620ea4f9fc88c149cfa644b3c6d99f4a20e450825f535e0a6b68de26bf",
    ),
    "Structured Error 1.2": (
        "### 15.1 Structured Error", "### 15.2",
        "7a88623998c9aabc39b01ae7b2d7140d640473936dbf8027ae86a80323b786be",
    ),
}


GATE_CLASSES = [
    "contract_registry", "self_id_jcs", "strict_examples", "closed_shapes",
    "directory_node", "mesh_namespace", "environment_mapping", "observation_chains",
    "annotation_dag", "receipt_chains", "lineage", "disclosure_policy",
    "continuation_plan", "route_outcomes", "target_first_move", "remote_unmanaged",
    "cloning_fidelity", "interfaces", "tuple_matrix", "security", "traceability",
    "publication_consistency",
]

CONTRACTS = {
    "urn:ax:protocol:session-directory-node": "1.0.0",
    "urn:ax:schema:session-directory-node-manifest": "1.0.0",
    "urn:ax:schema:session-directory-node-request": "1.0.0",
    "urn:ax:schema:session-directory-node-response": "1.0.0",
    "urn:ax:schema:environment-observation": "1.0.0",
    "urn:ax:schema:native-session-observation": "1.0.0",
    "urn:ax:schema:session-inventory-batch": "1.0.0",
    "urn:ax:schema:conversation-lineage-link": "1.0.0",
    "urn:ax:schema:session-annotation": "1.0.0",
    "urn:ax:schema:session-enrichment-profile": "1.0.0",
    "urn:ax:schema:session-enrichment-job-request": "1.0.0",
    "urn:ax:schema:session-enrichment-job-receipt": "1.0.0",
    "urn:ax:schema:session-continuation-plan": "1.0.0",
    "urn:ax:schema:session-directory-operation-receipt": "1.0.0",
    "urn:ax:schema:session-directory-query": "1.0.0",
    "urn:ax:protocol:rpc": "3.0.0",
    "urn:ax:schema:config": "2.0.0",
    "urn:ax:schema:cli-result": "3.0.0",
    "urn:ax:schema:error": "1.2.0",
    "urn:ax:schema:session-record": "3.0.0",
    "urn:ax:schema:session-event": "3.0.0",
}

SELF_FIELDS = {
    "urn:ax:schema:environment-observation": "observation_id",
    "urn:ax:schema:native-session-observation": "observation_id",
    "urn:ax:schema:session-inventory-batch": "batch_id",
    "urn:ax:schema:conversation-lineage-link": "lineage_link_id",
    "urn:ax:schema:session-annotation": "annotation_id",
    "urn:ax:schema:session-enrichment-profile": "profile_id",
    "urn:ax:schema:session-enrichment-job-request": "job_request_id",
    "urn:ax:schema:session-enrichment-job-receipt": "job_receipt_id",
    "urn:ax:schema:session-continuation-plan": "plan_id",
    "urn:ax:schema:session-directory-operation-receipt": "directory_receipt_id",
}

NODE_OPERATIONS = ["manifest", "probe", "scan", "inventory", "preview", "enrichment-plan", "enrichment-run", "enrichment-status", "continuation-inspect", "runtime-observe", "doctor"]
NAMESPACES = ["record", "event", "manifest", "tombstone", "tombstone_ack", "blob", "directory_record"]
HELLO_KEYS = {"rpc", "session_record", "session_event", "lease", "checkpoint", "workspace_group", "provider_identity", "blob", "transfer_manifest", "chunk", "materialization_plan", "tombstone", "tombstone_ack", "task_board_bundle", "environment_observation", "native_session_observation", "session_inventory_batch", "conversation_lineage_link", "session_annotation", "session_enrichment_profile", "session_enrichment_job_request", "session_enrichment_job_receipt", "session_continuation_plan", "session_directory_operation_receipt"}
ROUTES = ["managed_local_attach", "managed_remote_attach", "managed_local_resume", "managed_takeover", "managed_fork", "adopt_existing_native", "same_environment_clone", "cross_environment_clone", "cross_environment_move", "open_unmanaged_local", "archive_or_context_fallback"]
QUERY_OPERATIONS = ["schema", "sessions", "session", "lineage", "hosts", "environments", "jobs", "plans", "count", "distinct", "directory_summary"]
DIRECTORY_SCHEMAS = list(SELF_FIELDS)
HELLO_CONTRACTS = {
    "rpc": ["3.0.0"], "session_record": ["1.0.0", "2.0.0", "3.0.0"], "session_event": ["1.0.0", "2.0.0", "3.0.0"],
    "lease": ["1.0.0"], "checkpoint": ["1.0.0"], "workspace_group": ["1.0.0"], "provider_identity": ["1.0.0"], "blob": ["1.0.0"],
    "transfer_manifest": ["1.0.0"], "chunk": ["1.0.0"], "materialization_plan": ["1.0.0", "2.0.0"], "tombstone": ["1.0.0"],
    "tombstone_ack": ["1.0.0"], "task_board_bundle": ["1.0.0"], "environment_observation": ["1.0.0"], "native_session_observation": ["1.0.0"],
    "session_inventory_batch": ["1.0.0"], "conversation_lineage_link": ["1.0.0"], "session_annotation": ["1.0.0"], "session_enrichment_profile": ["1.0.0"],
    "session_enrichment_job_request": ["1.0.0"], "session_enrichment_job_receipt": ["1.0.0"], "session_continuation_plan": ["1.0.0"], "session_directory_operation_receipt": ["1.0.0"],
}
JOB_TRANSITIONS = {
    "root": ["queued"], "queued": ["claimed", "canceled"], "claimed": ["claimed", "running", "canceled"],
    "running": ["succeeded", "superseded", "failed", "canceled"], "succeeded": [], "superseded": [], "failed": [], "canceled": [],
}
OPERATION_TRANSITIONS = {
    "root": ["validating"], "validating": ["executing", "failed", "uncertain"],
    "executing": ["executing", "finalizing", "failed", "uncertain"], "finalizing": ["succeeded", "failed", "uncertain"],
    "failed": ["compensated"], "uncertain": ["executing", "finalizing", "failed", "succeeded", "compensated"],
    "succeeded": [], "compensated": [],
}

DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\."
    r"[0-9]{3,9}Z\Z"
)
TIMESTAMP_FIELDS = {
    "as_of", "claim_acquired_at", "claim_expires_at", "completed_at",
    "created_at", "deadline", "ended_at", "expires_at",
    "last_successful_contact_at", "observed_at", "receipt_at", "started_at",
    "updated_at", "validated_at",
}
AX_PLATFORMS = ["macos", "linux", "wsl2", "windows"]

CLOSED_OBJECTS = {
    "directory_node_manifest": ["schema", "schema_version", "node_id", "node_version", "host_id", "executable_sha256", "provider_manifest_digest", "session_adapter_manifest_digest", "supported_protocol_versions", "operations", "schemas", "environment_tuple_registry_id", "capabilities", "redaction_policy_ids", "enrichment_profile_ids", "limits", "extensions"],
    "directory_request": ["schema", "schema_version", "protocol", "protocol_version", "request_id", "operation", "deadline_ms", "body"],
    "directory_response_success": ["schema", "schema_version", "protocol", "protocol_version", "request_id", "operation", "ok", "body"],
    "directory_response_failure": ["schema", "schema_version", "protocol", "protocol_version", "request_id", "operation", "ok", "error"],
    "environment_observation": ["schema", "schema_version", "observation_id", "host_id", "installation_id", "environment_id", "environment_version", "provider_id", "platform", "architecture", "backend_realm_fingerprint", "capabilities", "authentication_status", "runtime_status", "observed_at", "extensions"],
    "native_session_observation": ["schema", "schema_version", "observation_id", "instance_id", "host_id", "installation_id", "observation_sequence", "previous_observation_id", "managed_session_id", "provider_identity_record_id", "lineage_anchor_hint", "source_generation", "head_digest", "identity_confidence", "presence", "native_state", "resumability", "workspace_identity", "provider_title", "created_at", "updated_at", "message_counts", "preview_status", "warnings", "observed_at", "extensions"],
    "inventory_batch": ["schema", "schema_version", "batch_id", "host_id", "batch_sequence", "previous_batch_id", "cursor_before", "cursor_after", "environment_observation_ids", "native_observation_ids", "scan_root_authority_ids", "adapter_builds", "started_at", "completed_at", "partial", "error_codes", "extensions"],
    "conversation_lineage_link": ["schema", "schema_version", "lineage_link_id", "link_kind", "from_kind", "from_id", "to_kind", "to_id", "canonical_anchor_id", "member_root_id", "evidence_ids", "supersedes_link_ids", "authorized_by_host_id", "created_at", "extensions"],
    "session_annotation": ["schema", "schema_version", "annotation_id", "subject_kind", "subject_id", "binding", "subject_head_digest", "kind", "payload", "author_kind", "author_host_id", "profile_id", "generator", "evidence_ids", "redaction_summary", "supersedes_annotation_ids", "created_at", "extensions"],
    "enrichment_profile": ["schema", "schema_version", "profile_id", "subject_kinds", "provider_ids", "input_classes", "max_events", "max_bytes", "delta_window_events", "redaction_policy_id", "generator_kind", "generator", "network_policy", "endpoint_class", "title_min_words", "title_max_words", "summary_schema_version", "incremental_policy", "full_rebuild_after_updates", "full_rebuild_after_delta_bytes", "minimum_incremental_confidence", "refresh_debounce_seconds", "stale_after_seconds", "extensions"],
    "enrichment_job_request": ["schema", "schema_version", "job_request_id", "job_id", "subject_kind", "subject_id", "expected_head_digest", "source_host_id", "source_instance_id", "profile_id", "requested_kinds", "prior_annotation_ids", "delta_start_evidence_id", "idempotency_key", "requester", "priority", "deadline", "created_at", "extensions"],
    "enrichment_job_receipt": ["schema", "schema_version", "job_receipt_id", "previous_job_receipt_id", "job_request_id", "job_id", "profile_id", "subject_head_digest", "state", "claim_host_id", "claim_lease_id", "claim_attempt", "claim_acquired_at", "claim_expires_at", "receipt_at", "input_event_count", "input_byte_count", "redaction_summary", "generator", "produced_annotation_ids", "usage", "failure_code", "started_at", "ended_at", "superseded_by_head_digest", "extensions"],
    "continuation_plan": ["schema", "schema_version", "plan_id", "operation_id", "created_at", "expires_at", "entry_id", "lineage_anchor_id", "source_session_id", "source_instance_id", "source_host_id", "source_observation_id", "source_head_digest", "source_lease", "source_checkpoint_id", "source_runtime", "target", "workspace", "policy_digest", "intent", "route", "steps", "adoption_plan_id", "projection_plan_id", "fidelity_report_id", "expected_bytes", "expected_model_calls", "expected_processes", "required_capabilities", "contract_assertions", "confirmations", "allowed_fallback_outcomes", "request_digest", "adapter_digest", "controller_digest", "extensions"],
    "directory_operation_receipt": ["schema", "schema_version", "directory_receipt_id", "previous_directory_receipt_id", "operation_id", "plan_id", "request_digest", "actor", "initiating_host_id", "responsible_host_id", "step_index", "step_id", "idempotency_key", "validated_source", "validated_target", "effect_receipt_ids", "state", "safe_retry", "error", "durable_effects", "compensations", "outcome", "created_at", "extensions"],
    "directory_query": ["schema", "schema_version", "query_id", "operations", "caller", "extensions"],
    "capability_result": ["status", "reason_code", "evidence_ids", "observed_at", "extensions"],
    "directory_node_limits": ["max_frame_bytes", "max_scan_instances", "max_inventory_take", "max_excerpt_count", "max_excerpt_bytes", "max_enrichment_events", "max_enrichment_bytes", "extensions"],
    "preview_excerpt": ["role", "ordinal", "text", "source_event_id", "truncated", "extensions"],
    "management_binding": ["state", "session_id", "provider_identity_record_id", "evidence_ids", "extensions"],
    "directory_node_build": ["node_id", "node_version", "executable_sha256", "provider_manifest_digest", "session_adapter_manifest_digest", "extensions"],
    "workspace_identity": ["logical_workspace_id", "repository_identity", "workspace_digest", "branch"],
    "message_counts": ["user", "assistant"],
    "adapter_build": ["environment_id", "adapter_version", "executable_sha256"],
    "generator_identity": ["kind", "implementation", "implementation_version", "model_id", "prompt_digest", "output_schema_version", "extensions"],
    "redaction_summary": ["policy_digest", "classes", "class_counts", "extensions"],
    "usage_summary": ["input_units", "output_units", "total_units", "cost_minor_units", "currency", "extensions"],
    "runtime_expectation": ["native_state", "resumability", "managed_runtime_ref", "evidence_kind", "evidence_id", "observed_at", "extensions"],
    "directory_target": ["host_id", "installation_id", "environment_tuple", "provider_id", "backend_realm_fingerprint", "authentication_status", "reachability", "extensions"],
    "workspace_route": ["workspace_group_id", "workspace_record_id", "checkpoint_id", "cohort_session_ids", "conflict_policy", "transfer_manifest_id", "materialization_plan_id", "extensions"],
    "contract_assertion": ["contract_id", "exact_version", "extensions"],
    "continuation_step": ["step_id", "subsystem", "input_digest", "prerequisite_step_ids", "retry_policy", "mutation", "expected_receipt_type", "extensions"],
    "validated_source": ["session_id", "instance_id", "host_id", "observation_id", "head_digest", "lease_id", "lease_epoch", "checkpoint_id", "runtime", "extensions"],
    "validated_target": ["target", "environment_observation_id", "capability_evidence_ids", "workspace", "policy_digest", "contract_assertions", "validated_at", "extensions"],
    "caller_context": ["caller_id", "authentication_subject", "origin_host_id", "interaction", "scopes", "disclosure_policy_digest", "extensions"],
    "query_operation": ["operation_index", "name", "parameters", "fields", "preset", "skip", "take", "sort", "dry_run", "confirm", "expectation_digest", "idempotency_key", "extensions"],
    "query_sort": ["field", "direction", "extensions"],
    "directory_filters": ["kinds", "lineage_anchors", "provider_ids", "host_ids", "workspace_ids", "states", "management_states", "reachability", "freshness", "warnings", "updated_before", "updated_after", "extensions"],
    "summary_payload": ["topic", "status", "last_user_intent", "last_agent_action", "suggested_next_step", "open_loops", "risks", "recent_activity", "language", "confidence", "truncated"],
    "directory_freshness": ["state", "age_seconds", "effective_threshold_seconds", "as_of", "reason_codes", "extensions"],
    "directory_entry": ["id", "kind", "lineage_anchor", "management_state", "display_title", "title_source", "title_subject_id", "selected_session_id", "selected_instance_id", "provider_id", "environment_id", "host_id", "workspace_id", "owner_host_id", "local_role", "state", "updated_at", "summary", "recent_activity", "annotation_freshness", "inventory_freshness", "reachability", "authentication_status", "branch_count", "clone_count", "warnings", "available_intents", "extensions"],
    "lineage_node": ["node_kind", "node_id", "anchor_id", "head_digest", "selected", "extensions"],
    "suggested_relation": ["from_kind", "from_id", "to_kind", "to_id", "method", "score_millionths", "evidence_ids", "created_at", "extensions"],
    "directory_host": ["host_id", "display_name", "reachability", "last_successful_contact_at", "inventory_freshness", "environment_observation_ids", "warnings", "extensions"],
    "query_schema_registry": ["query_schema_version", "registry_digest", "operations", "fields", "presets", "limits", "extensions"],
    "query_operation_descriptor": ["name", "kind", "parameters_schema_id", "result_tag", "required_scope", "supports_dry_run", "requires_confirmation", "idempotency", "extensions"],
    "query_field_descriptor": ["name", "type", "cost", "required_scope", "filterable", "sortable", "extensions"],
    "query_preset_descriptor": ["name", "fields", "extensions"],
    "query_limits": ["max_operations", "max_take", "max_skip", "max_sort_keys", "max_fields", "max_cursor_bytes", "extensions"],
    "query_result": ["operation_index", "operation_name", "result_tag", "body", "extensions"],
}

SELF_SCHEMA_SHAPES = {
    "urn:ax:schema:environment-observation": "environment_observation",
    "urn:ax:schema:native-session-observation": "native_session_observation",
    "urn:ax:schema:session-inventory-batch": "inventory_batch",
    "urn:ax:schema:conversation-lineage-link": "conversation_lineage_link",
    "urn:ax:schema:session-annotation": "session_annotation",
    "urn:ax:schema:session-enrichment-profile": "enrichment_profile",
    "urn:ax:schema:session-enrichment-job-request": "enrichment_job_request",
    "urn:ax:schema:session-enrichment-job-receipt": "enrichment_job_receipt",
    "urn:ax:schema:session-continuation-plan": "continuation_plan",
    "urn:ax:schema:session-directory-operation-receipt": "directory_operation_receipt",
}

NODE_REQUEST_BODIES = {
    "manifest": [], "probe": ["platform", "architecture", "requested_environment_ids", "requested_capabilities", "extensions"],
    "scan": ["operation_id", "installation_ids", "prior_batch_id", "cursor", "max_instances", "extensions"],
    "inventory": ["installation_ids", "fields", "after", "take", "extensions"],
    "preview": ["instance_id", "expected_observation_id", "expected_head_digest", "roles", "excerpt_count", "excerpt_bytes", "redaction_policy_id", "extensions"],
    "enrichment-plan": ["request", "extensions"], "enrichment-run": ["operation_id", "request", "extensions"],
    "enrichment-status": ["job_id", "extensions"],
    "continuation-inspect": ["instance_id", "expected_observation_id", "expected_head_digest", "extensions"],
    "runtime-observe": ["instance_id", "expected_observation_id", "extensions"],
    "doctor": ["installation_ids", "include_conformance_age", "extensions"],
}

NODE_SUCCESS_BODIES = {
    "manifest": CLOSED_OBJECTS["directory_node_manifest"], "probe": ["host_id", "node_build", "policy_digest", "environments", "findings", "extensions"],
    "scan": ["batch", "environment_observation_ids", "native_observation_ids", "next_cursor", "extensions"],
    "inventory": ["observations", "next_cursor", "partial", "extensions"],
    "preview": ["host_id", "instance_id", "observation_id", "head_digest", "excerpts", "truncated", "redaction_summary", "freshness", "extensions"],
    "enrichment-plan": ["accepted", "expected_input_events", "expected_input_bytes", "expected_model_calls", "disclosure_classes", "blockers", "extensions"],
    "enrichment-run": ["job_id", "current_receipt_id", "produced_annotation_ids", "extensions"],
    "enrichment-status": ["job_id", "current_receipt_id", "receipt_chain_ids", "produced_annotation_ids", "extensions"],
    "continuation-inspect": ["observation_id", "head_digest", "management_binding", "safe_boundary_status", "runtime_status", "warnings", "extensions"],
    "runtime-observe": ["runtime", "extensions"],
    "doctor": ["healthy", "findings", "environment_capabilities", "cloning_contracts", "extensions"],
}

QUERY_PARAMETER_BODIES = {
    "schema": ["extensions"], "directory_summary": ["extensions"], "sessions": ["filters", "extensions"], "count": ["filters", "extensions"],
    "session": ["subject_kind", "subject_id", "extensions"], "lineage": ["anchor_id", "include_suggestions", "extensions"],
    "hosts": ["host_ids", "reachable", "extensions"], "environments": ["host_ids", "environment_ids", "authentication_status", "extensions"],
    "jobs": ["job_ids", "profile_ids", "states", "extensions"], "plans": ["plan_ids", "operation_ids", "include_expired", "extensions"],
    "distinct": ["field", "filters", "extensions"], "set_title": ["subject_kind", "subject_id", "title", "supersedes_annotation_ids", "extensions"],
    "set_tags": ["subject_kind", "subject_id", "tags", "supersedes_annotation_ids", "extensions"],
    "set_pin": ["subject_kind", "subject_id", "value", "supersedes_annotation_ids", "extensions"],
    "enrich": ["subject_kind", "subject_id", "profile_id", "kinds", "expected_head_digest", "extensions"],
    "plan_continue": ["subject_kind", "subject_id", "source_instance_id", "to_host_id", "to_installation_id", "intent", "workspace_policy", "source_after_success", "extensions"],
    "execute_plan": ["plan_id", "operation_id", "confirmations", "extensions"],
}

ANNOTATION_PAYLOAD_BODIES = {
    "text": ["text"], "tags": ["values"], "boolean": ["value"],
    "summary": ["topic", "status", "last_user_intent", "last_agent_action", "suggested_next_step", "open_loops", "risks", "recent_activity", "language", "confidence", "truncated"],
}

CLI_RESULT_BODIES = {
    "directory_entries": ["entries", "next_cursor", "partial", "freshness"],
    "directory_inspection": ["entry", "observations", "annotations", "provenance_ids"],
    "directory_lineage": ["anchor_id", "nodes", "authoritative_links", "suggestions", "ambiguous"],
    "directory_hosts_environments": ["hosts", "environments"], "directory_jobs": ["requests", "receipts", "next_cursor"],
    "directory_plan": ["plan", "outcome", "mutated"], "directory_operation": ["operation_id", "receipt_chain", "current_state", "outcome"],
    "directory_attach_continue": ["plan_id", "operation_id", "outcome", "target_session_id", "runtime_ref", "current_receipt_id"],
    "directory_doctor": ["healthy", "findings", "contract_versions", "tuple_evidence_age_seconds"],
    "directory_query": ["query_id", "results"], "annotation_mutation": ["annotation", "would_write", "extensions"],
    "enrichment_mutation": ["request", "would_enqueue", "extensions"],
}

QUERY_RESULT_BODIES = {
    "schema_registry": ["registry", "extensions"],
    "directory_entries": ["entries", "next_cursor", "partial", "freshness", "extensions"],
    "directory_inspection": ["entry", "observations", "annotations", "provenance_ids", "extensions"],
    "directory_lineage": ["anchor_id", "nodes", "authoritative_links", "suggestions", "ambiguous", "extensions"],
    "directory_hosts_environments": ["hosts", "environments", "extensions"],
    "directory_jobs": ["requests", "receipts", "next_cursor", "extensions"],
    "directory_plans": ["plans", "next_cursor", "extensions"],
    "directory_count": ["count", "partial", "extensions"],
    "directory_distinct": ["field", "values", "partial", "extensions"],
    "directory_summary": ["total_entries", "managed", "unmanaged", "missing", "offline", "conflicted", "running", "warning_count", "as_of", "extensions"],
    "annotation_mutation": ["annotation", "would_write", "extensions"],
    "enrichment_mutation": ["request", "would_enqueue", "extensions"],
    "directory_plan": ["plan", "outcome", "mutated", "extensions"],
    "directory_operation": ["operation_id", "receipt_chain", "current_state", "outcome", "extensions"],
}


def validate(root: Path, spec: str, canonical: Callable[[object], bytes]) -> tuple[list[str], dict[str, int]]:
    path = root / "fixtures" / "session_directory_conformance.json"
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"directory gate strict_examples: cannot read strict JSON fixture: {exc}"], {"directory_gate_classes": 22, "directory_failed_groups": 22}

    failures: dict[str, list[str]] = {name: [] for name in GATE_CLASSES}
    def need(group: str, condition: bool, message: str) -> None:
        if not condition:
            failures[group].append(message)

    # Evaluate exact source binding before fixture parity. A SPEC-only enum
    # widening, member removal/addition, or type change must fail even when the
    # fixture and executable registries are left untouched.
    normalized_spec = spec.replace("\r\n", "\n").replace("\r", "\n")
    for section, (start_marker, end_marker, expected_digest) in NORMATIVE_SCHEMA_SECTIONS.items():
        start = normalized_spec.find(start_marker)
        end = normalized_spec.find(end_marker, start + len(start_marker)) if start >= 0 else -1
        if start < 0 or end < 0:
            need("closed_shapes", False, f"exact normative schema section missing: {section}")
            continue
        actual_digest = hashlib.sha256(normalized_spec[start:end].encode("utf-8")).hexdigest()
        need(
            "closed_shapes",
            actual_digest == expected_digest,
            f"exact normative directory schema registry drift in {section} (members/types/enums)",
        )

    need("strict_examples", data.get("fixture") == "ax-session-directory-conformance-v1", "fixture discriminator mismatch")
    need("strict_examples", data.get("gate_classes") == GATE_CLASSES, "gate_classes must be the exact ordered 22-group registry")
    need("strict_examples", data.get("strict_examples") == {"json": True, "toml": True, "jsonc": True, "reject_floats": True, "safe_integer_max": 9007199254740991}, "strict JSON/TOML/JSONC or safe-number policy mismatch")

    need("contract_registry", data.get("contracts") == CONTRACTS, "exact contract registry/version mismatch")
    for contract, version in CONTRACTS.items():
        rows = [line for line in spec.splitlines() if f"<code>{contract}</code>" in line]
        need("contract_registry", bool(rows) and any(f"<code>{version}</code>" in row for row in rows), f"SPEC registry missing {contract} version {version}")

    need("self_id_jcs", data.get("self_id_fields") == SELF_FIELDS, "exact directory self-ID field registry mismatch")
    vectors = data.get("identity_vectors")
    if not isinstance(vectors, list):
        vectors = []
        need("self_id_jcs", False, "identity_vectors must be an array with exactly one vector for every immutable directory schema")
    vector_schemas = [row.get("schema") for row in vectors if isinstance(row, dict)]
    need(
        "self_id_jcs",
        len(vectors) == len(SELF_FIELDS) and set(vector_schemas) == set(SELF_FIELDS) and len(vector_schemas) == len(set(vector_schemas)),
        "identity vector coverage must contain exactly one vector for every immutable directory schema",
    )

    def validate_common_values(value: object, location: str, field_name: str | None = None) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                validate_common_values(child, f"{location}.{key}", key)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                validate_common_values(child, f"{location}[{index}]", field_name)
            return
        if not isinstance(value, str):
            return
        if value.startswith("sha256:"):
            need("self_id_jcs", bool(DIGEST_RE.fullmatch(value)), f"invalid SHA-256 digest identifier at {location}")
        if field_name in TIMESTAMP_FIELDS:
            need("self_id_jcs", bool(TIMESTAMP_RE.fullmatch(value)), f"timestamp must be UTC RFC 3339 with at least millisecond precision at {location}")
        if field_name == "platform":
            need("self_id_jcs", value in AX_PLATFORMS, f"platform must use the AX enum macos|linux|wsl2|windows at {location}")

    for row in vectors:
        if not isinstance(row, dict):
            need("self_id_jcs", False, "each identity vector must be an object")
            continue
        schema = row.get("schema")
        canonical_input = row.get("canonical_input")
        self_field = SELF_FIELDS.get(schema)
        need("self_id_jcs", self_field is not None, f"identity vector uses unregistered immutable schema: {schema}")
        if self_field is None or not isinstance(canonical_input, dict):
            need("self_id_jcs", False, f"identity vector canonical_input must be an object for {schema}")
            continue
        need("self_id_jcs", canonical_input.get("schema") == schema and canonical_input.get("schema_version") == "1.0.0", f"identity vector canonical_input schema/version mismatch for {schema}")
        validate_common_values(canonical_input, f"identity_vectors[{schema}].canonical_input")
        validate_common_values(row.get("expected_id"), f"identity_vectors[{schema}].expected_id", "expected_id")
        need("self_id_jcs", self_field not in canonical_input, f"identity vector canonical_input must omit only self field {self_field} for {schema}")
        expected_members = set(CLOSED_OBJECTS[SELF_SCHEMA_SHAPES[schema]]) - {self_field}
        need("self_id_jcs", set(canonical_input) == expected_members, f"identity vector canonical_input must contain every closed member except self field {self_field} for {schema}")
        actual = "sha256:" + hashlib.sha256(canonical(canonical_input)).hexdigest()
        need("self_id_jcs", row.get("expected_id") == actual, f"wrong self-ID for {schema}: expected {actual}")
    ids = data.get("sorted_id_fixture", [])
    need("self_id_jcs", ids == sorted(set(ids)), "sorted_id_fixture must be bytewise sorted and unique")
    for index, identity in enumerate(ids):
        validate_common_values(identity, f"sorted_id_fixture[{index}]", "id")

    shapes = data.get("closed_shapes", {})
    need("closed_shapes", shapes == CLOSED_OBJECTS, "closed directory object member registry mismatch or unknown field admitted")
    bodies = data.get("closed_body_unions", {})
    need("closed_shapes", bodies.get("directory_node_request") == NODE_REQUEST_BODIES, "Directory Node request body union/member registry mismatch")
    need("closed_shapes", bodies.get("directory_node_success") == NODE_SUCCESS_BODIES, "Directory Node success body union/member registry mismatch")
    need("closed_shapes", bodies.get("query_parameters") == QUERY_PARAMETER_BODIES, "Directory Query parameter union/member registry mismatch")
    need("closed_shapes", bodies.get("query_results") == QUERY_RESULT_BODIES, "Directory Query result union/member registry mismatch")
    need("closed_shapes", bodies.get("annotation_payloads") == ANNOTATION_PAYLOAD_BODIES, "Session Annotation payload union/member registry mismatch")
    need("closed_shapes", bodies.get("cli_result_bodies") == CLI_RESULT_BODIES, "CLI Result 3 body union/member registry mismatch")

    node = data.get("directory_node", {})
    need("directory_node", node.get("operations") == NODE_OPERATIONS and node.get("mutations") == ["scan", "enrichment-run"], "Directory Node exact operation/mutation registry mismatch")
    need("directory_node", node.get("idempotency") == {"same_mutation_same_input": "same_receipt", "same_mutation_changed_input": "idempotency_mismatch"}, "mutation-ID reuse with changed input must return idempotency_mismatch")
    need("directory_node", node.get("platforms") == AX_PLATFORMS, "Directory Node probe platform registry must be macos|linux|wsl2|windows")
    need("directory_node", node.get("response_union") == {"success": "body_without_error", "failure": "error_without_body"}, "Directory Node response must be body XOR error")

    mesh = data.get("mesh", {})
    need("mesh_namespace", mesh.get("namespace_count") == 7 and mesh.get("namespaces") == NAMESPACES, "RPC 3 namespace cardinality must be seven with exact members")
    need("mesh_namespace", mesh.get("directory_namespace") == "directory_record", "directory objects must be placed only in directory_record namespace")
    need("mesh_namespace", mesh.get("directory_schemas") == DIRECTORY_SCHEMAS, "directory_record namespace membership must contain the exact ten immutable directory schemas")
    hello = mesh.get("hello_contracts", {})
    need("mesh_namespace", set(hello) == HELLO_KEYS and len(hello) == 24, "RPC 3 hello map must contain the exact 24 required contract keys")
    need("mesh_namespace", hello == HELLO_CONTRACTS, "RPC 3 hello contract version map mismatch")
    merkle = mesh.get("merkle_fixture", {})
    mids = merkle.get("ids", [])
    need("mesh_namespace", mids == sorted(set(mids)) and merkle.get("cardinality") == len(mids), "directory_record Merkle cardinality/ordering mismatch")
    need("mesh_namespace", mesh.get("old_peer_state") == "directory_mesh_unsupported", "RPC 2 peer must be directory_mesh_unsupported")

    need("environment_mapping", data.get("environment_mapping") == {"claude-code": "claude", "codex": "codex"}, "mapping must be exactly claude-code->claude and codex->codex")

    obs = data.get("observation_cases", {})
    need("observation_chains", obs.get("partial") != "missing" and obs.get("offline") != "missing", "offline/partial scan cannot assert presence=missing")
    need("observation_chains", obs.get("missing_requires") == "successful_non_partial_same_root_realm", "missing requires a successful non-partial same-root/realm scan")
    need("observation_chains", obs.get("conflict_resolution") == "predecessor_chain", "observation conflicts use predecessor chains, never wall clock")

    ann = data.get("annotation_cases", {})
    need("annotation_dag", ann.get("generated_requires") == ["subject_head_digest", "profile_id", "evidence_ids"], "generated annotation requires exact subject head, profile, and evidence")
    need("annotation_dag", ann.get("manual_precedence") is True, "enrichment must not overwrite manual title metadata")
    profile_vectors = [row.get("canonical_input", {}) for row in vectors if row.get("schema") == "urn:ax:schema:session-enrichment-profile"]
    need("annotation_dag", ann.get("generator_discriminators") == "must_match" and len(profile_vectors) == 1 and profile_vectors[0].get("generator_kind") == profile_vectors[0].get("generator", {}).get("kind"), "enrichment profile generator_kind must equal generator.kind")
    need("annotation_dag", ann.get("conflict_resolution") == "supersede_all_concurrent_heads" and ann.get("clock_is_authority") is False, "resolution must supersede every concurrent head without wall-clock authority")

    receipts = data.get("receipt_cases", {})
    need("receipt_chains", receipts.get("requires_predecessor") is True and receipts.get("lost_response_replay") == "same_receipt_chain", "receipt chains require predecessors and same-chain lost-response replay")
    job_states = ["queued", "claimed", "running", "succeeded", "superseded", "failed", "canceled"]
    operation_states = ["validating", "executing", "finalizing", "succeeded", "failed", "uncertain", "compensated"]
    need("receipt_chains", receipts.get("job_states") == job_states and receipts.get("operation_states") == operation_states, "job/operation receipt state registry mismatch")
    need("receipt_chains", receipts.get("job_transitions") == JOB_TRANSITIONS, "Enrichment Job Receipt transition oracle mismatch")
    need("receipt_chains", receipts.get("operation_transitions") == OPERATION_TRANSITIONS, "Directory Operation Receipt transition oracle mismatch")

    lineage = data.get("lineage", {})
    edges = ["ax_fork", "session_clone", "cross_environment_move", "native_adoption", "managed_instance_binding", "operator_link"]
    need("lineage", lineage.get("authoritative_edges") == edges and lineage.get("suggested_relation_authoritative") is False, "lineage authority requires exact evidence-backed edges; suggestions are excluded")
    need("lineage", lineage.get("cycles_allowed") is False and lineage.get("ambiguity") == "visible_until_explicit_resolution", "cycles are forbidden and ambiguity remains visible")
    representative = lineage.get("representative", {})
    need("lineage", representative == {"required_for_lineage_row": True, "singular_fields_bind_to_representative": True, "selection_is_authority": False, "clock_is_tiebreaker": False, "stable_final_tiebreaker": "member_id_bytewise"}, "lineage DirectoryEntry must bind singular fields to one non-authoritative deterministic representative")

    disclosure = data.get("disclosure", {})
    excluded = {"raw_native_session_id", "absolute_native_store_path", "raw_transcript", "raw_preview", "credentials", "auth_store", "terminal_output", "pid", "pty", "socket", "model_payload", "embedding", "sqlite_index"}
    need("disclosure_policy", disclosure.get("modes") == ["local_only", "mesh_sanitized", "reference_only"] and disclosure.get("default_excerpt") == "local_only", "disclosure modes/default excerpt policy mismatch")
    need("disclosure_policy", set(disclosure.get("excluded_from_mesh", [])) == excluded, "replicated metadata must exclude raw IDs/paths/transcripts, credentials, runtime handles, model payloads, embeddings, and SQLite")

    plan = data.get("continuation_plan", {})
    revalidates = ["source_head", "observation", "lease", "checkpoint", "runtime", "target_tuple", "target_auth", "workspace", "policy", "capability"]
    need("continuation_plan", plan.get("pure") is True and plan.get("requires_operation_id") is True and plan.get("requires_unexpired_plan") is True, "plan must be pure, unexpired, and operation-ID-bound")
    need("continuation_plan", plan.get("revalidates") == revalidates and plan.get("mismatch") == "continuation_plan_stale" and plan.get("silent_replan") is False and plan.get("route_substitution") is False, "stale plan must fail exact revalidation without silent replan/route substitution")

    route_map = data.get("route_outcomes", {})
    need("route_outcomes", list(route_map) == ROUTES, "exact ordered route registry mismatch")
    all_outcomes = {outcome for outcomes in route_map.values() for outcome in outcomes}
    required_outcomes = {"attached", "resumed_managed", "taken_over", "forked", "adopted", "cloned", "moved_cross_environment", "cloned_source_still_active", "opened_unmanaged_local", "planned_only", "archive_or_context_fallback"}
    need("route_outcomes", all_outcomes == required_outcomes and route_map.get("cross_environment_move") == ["moved_cross_environment", "cloned_source_still_active", "planned_only"], "route/outcome matrix completeness mismatch")

    need("target_first_move", data.get("move_trace") == ["capture", "transfer", "project", "validate", "target_commit", "lineage_publish", "source_stop_release"], "move must commit target and lineage before source stop/release")
    unmanaged = data.get("remote_unmanaged")
    need("remote_unmanaged", unmanaged == {"open_allowed": False, "move_allowed": False, "alternatives": ["source_local_adoption", "managed_clone", "adoption_then_managed_move"]}, "remote unmanaged open is forbidden; direct unmanaged move is forbidden")

    clone = data.get("cloning", {})
    clone_refs = ["urn:ax:schema:clone-capture-manifest", "urn:ax:schema:canonical-session", "urn:ax:schema:projection-plan", "urn:ax:schema:fidelity-report", "urn:ax:schema:clone-read-back-evidence-manifest", "urn:ax:schema:clone-validation-report", "urn:ax:schema:clone-lineage-receipt"]
    need("cloning_fidelity", clone.get("cross_environment_requires") == clone_refs, "cross-environment route must reference final cloning contracts")
    need("cloning_fidelity", clone.get("success_requires_fidelity") is True and clone.get("success_requires_read_back") is True and clone.get("provider_change_in_place") is False, "clone requires fidelity/read-back and cannot change provider in place")

    interface = data.get("interfaces", {})
    need("interfaces", interface.get("query_operations") == QUERY_OPERATIONS and interface.get("query_presets") == ["minimal", "overview", "activity", "routing", "full"], "query operation/preset registry mismatch")
    need("interfaces", interface.get("guarded_mutations") == ["set_title", "set_tags", "set_pin", "enrich", "plan_continue", "execute_plan"] and interface.get("delete_mutation") is False, "guarded mutation registry mismatch or delete admitted")
    need("interfaces", interface.get("default_contains_raw_transcript") is False and interface.get("tui_uses_typed_engine") is True, "default output must exclude raw transcript and TUI must use typed engine")
    need("interfaces", interface.get("human_cli_leaves") == ["list", "inspect", "lineage", "scan", "enrich", "jobs", "plan", "continue", "operation", "attach", "doctor"] and interface.get("agent_cli_leaves") == ["q", "grep", "m"], "ax sessions human and agent CLI leaf registries mismatch")
    correlation = interface.get("query_correlation", {})
    request_operations = correlation.get("request", [])
    response_results = correlation.get("response", [])
    expected_indexes = list(range(len(request_operations)))
    request_indexes = [row.get("operation_index") for row in request_operations if isinstance(row, dict)]
    response_indexes = [row.get("operation_index") for row in response_results if isinstance(row, dict)]
    request_names = [row.get("name") for row in request_operations if isinstance(row, dict)]
    response_names = [row.get("operation_name") for row in response_results if isinstance(row, dict)]
    need("interfaces", request_indexes == expected_indexes, "Directory Query operation_index must be unique, contiguous, and equal array position")
    need("interfaces", response_indexes == expected_indexes and response_names == request_names and len(response_results) == len(request_operations), "QueryResult must preserve request order and exact operation index/name correlation")

    tuples = data.get("tuple_matrix", {})
    tuple_keys = {"claude-code/claude/macos/arm64", "claude-code/claude/linux/amd64", "codex/codex/macos/arm64", "codex/codex/linux/amd64"}
    need("tuple_matrix", set(tuples) == tuple_keys | {"adoption_default"} and all(tuples.get(k) == "acceptance_required" for k in tuple_keys) and tuples.get("adoption_default") == "disabled_until_fixture_evidence", "Claude/Codex tuple matrix or adoption release gate mismatch")

    security = data.get("security", {})
    hostile = ["ansi", "osc", "bidi", "control", "invalid_width", "hostile_grapheme", "prompt_injection", "path_traversal", "symlink", "special_file"]
    need("security", data.get("sanitized") is True and security.get("hostile_inputs") == hostile and security.get("rendering") == "remove_or_visibly_escape", "sanitized hostile-string registry/escaping mismatch")
    need("security", security.get("launch") == {"structured_argv": True, "explicit_cwd": True, "environment_allowlist": True, "shell_concatenation": False}, "launch requires structured argv/cwd/env allowlist and forbids shell concatenation")
    canaries = ("-----BEGIN PRIVATE KEY-----", "-----BEGIN OPENSSH PRIVATE KEY-----", "ghp_", "sk-proj-", "/Users/", "C:\\Users\\")
    need("security", security.get("secret_canary_absent") is True and not any(value in raw for value in canaries), "fixture contains credential/private-path canary")
    families = data.get("synthetic_fixture_families", [])
    required_families = {f"{provider}_{shape}" for provider in ("claude", "codex") for shape in ("empty", "one_turn", "long", "compacted", "branched", "active", "stopped", "corrupt")} | {"identity", "freshness", "annotation", "enrichment", "lineage", "mesh_convergence", "route", "crash_point", "tui_hostile_string", "disclosure_policy"}
    need("security", set(families) == required_families and len(families) == len(required_families), "synthetic sanitized fixture family registry incomplete")
    cases = data.get("synthetic_cases", {})
    expected_case_groups = {"provider_sessions", "identity", "freshness", "annotation", "enrichment", "lineage", "mesh_convergence", "routes", "crash_points", "tui", "disclosure_policy"}
    need("security", isinstance(cases, dict) and set(cases) == expected_case_groups, "synthetic fixture case groups must be exact and structured")
    if isinstance(cases, dict):
        provider_cases = cases.get("provider_sessions", [])
        provider_shapes = {(row.get("provider"), row.get("shape")) for row in provider_cases if isinstance(row, dict)}
        expected_provider_shapes = {(provider, shape) for provider in ("claude", "codex") for shape in ("empty", "one_turn", "long", "compacted", "branched", "active", "stopped", "corrupt")}
        need("security", len(provider_cases) == 16 and provider_shapes == expected_provider_shapes, "provider session fixtures must cover every Claude/Codex shape exactly once")
        identity_kinds = {row.get("case") for row in cases.get("identity", []) if isinstance(row, dict)}
        need("security", identity_kinds == {"managed_exact", "unmanaged_exact", "unmanaged_strong", "unmanaged_weak", "invalid_binding", "multiple_realms"}, "identity fixtures must cover managed/unmanaged/weak/exact, invalid binding, and multiple realms")
        freshness_states = {row.get("expected_freshness") for row in cases.get("freshness", []) if isinstance(row, dict)}
        need("observation_chains", freshness_states == {"current", "stale", "offline", "partial", "conflicted"} and any(row.get("expected_presence") == "missing" for row in cases.get("freshness", []) if isinstance(row, dict)), "freshness fixtures must cover current/stale/offline/partial/missing/conflicted outcomes")
        annotation_kinds = {row.get("case") for row in cases.get("annotation", []) if isinstance(row, dict)}
        need("annotation_dag", annotation_kinds == {"manual_title", "provider_title", "generated_title", "fallback_title", "concurrent_manual_heads"}, "annotation fixtures must cover title precedence and concurrent heads")
        enrichment_kinds = {row.get("case") for row in cases.get("enrichment", []) if isinstance(row, dict)}
        need("annotation_dag", enrichment_kinds == {"deterministic", "model", "stale_head_race", "model_failure", "prompt_injection"}, "enrichment fixtures must cover deterministic/model/race/failure/prompt-injection cases")
        lineage_kinds = {row.get("case") for row in cases.get("lineage", []) if isinstance(row, dict)}
        need("lineage", lineage_kinds == {"fork", "clone", "move", "adoption", "similar_unrelated"} and all(row.get("authoritative") is (row.get("case") != "similar_unrelated") for row in cases.get("lineage", []) if isinstance(row, dict)), "lineage fixtures must distinguish evidence-backed edges from similarity")
        mesh_kinds = {row.get("case") for row in cases.get("mesh_convergence", []) if isinstance(row, dict)}
        need("mesh_namespace", mesh_kinds == {"reorder", "duplicate", "gap", "conflict", "clock_skew"}, "mesh fixtures must cover reorder/duplicate/gap/conflict/clock-skew convergence")
        route_cases = cases.get("routes", [])
        route_source_kinds = {
            "managed_local_attach": "managed",
            "managed_remote_attach": "managed",
            "managed_local_resume": "managed",
            "managed_takeover": "managed",
            "managed_fork": "managed",
            "adopt_existing_native": "unmanaged",
            "same_environment_clone": "managed_or_unmanaged",
            "cross_environment_clone": "managed_or_unmanaged",
            "cross_environment_move": "managed",
            "open_unmanaged_local": "unmanaged",
            "archive_or_context_fallback": "any",
        }
        need("route_outcomes", len(route_cases) == len(ROUTES) and [row.get("route") for row in route_cases if isinstance(row, dict)] == ROUTES and all(row.get("expected_outcomes") == route_map.get(row.get("route")) and row.get("source_kind") == route_source_kinds.get(row.get("route")) for row in route_cases if isinstance(row, dict)), "route fixtures must cover every route with its exact outcome matrix and source-kind")
        durable_steps = ["capture", "transfer", "project", "validate", "target_commit", "lineage_publish", "source_stop_release"]
        crash_cases = cases.get("crash_points", [])
        crash_matrix = {(row.get("step"), row.get("position")) for row in crash_cases if isinstance(row, dict)}
        need("receipt_chains", len(crash_cases) == len(durable_steps) * 2 and crash_matrix == {(step, position) for step in durable_steps for position in ("before", "after")} and all(row.get("recovery") in {"no_effect_retry", "status_first_same_chain"} for row in crash_cases if isinstance(row, dict)), "crash fixtures must cover before/after every durable step with same-chain recovery")
        tui_cases = cases.get("tui", [])
        tui_kinds = {row.get("case") for row in tui_cases if isinstance(row, dict)}
        need("security", tui_kinds == {"narrow", "wide", "ansi", "osc", "bidi", "control", "invalid_width", "hostile_grapheme"} and all(row.get("expected") in {"bounded_layout", "remove_or_visibly_escape"} for row in tui_cases if isinstance(row, dict)), "TUI fixtures must cover narrow/wide layout and every hostile terminal class")
        disclosure_modes = {row.get("mode") for row in cases.get("disclosure_policy", []) if isinstance(row, dict)}
        need("disclosure_policy", disclosure_modes == {"local_only", "mesh_sanitized", "reference_only"} and all(row.get("contains_private_content") is False for row in cases.get("disclosure_policy", []) if isinstance(row, dict)), "disclosure fixtures must cover all policies without private content")

    trace = data.get("traceability", [])
    need("traceability", len(trace) == 10 and len(set(trace)) == 10, "traceability registry must contain ten unique directory AC IDs")
    for ac in trace:
        need("traceability", f"<code>{ac}</code>" in spec, f"SPEC Appendix A missing {ac}")

    publication = data.get("publication", {})
    docs = ["SPEC.md", "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "RELEASE_NOTES.md", "VERSION", "STANDALONE_TO_AX_TRACEABILITY.md"]
    need("publication_consistency", publication.get("spec_version") == "0.4.1" and publication.get("frozen_digest_owner") == "publication-task" and publication.get("required_documents") == docs, "v0.4.1 candidate/release ownership or document registry mismatch")
    claim = "AX v0.4.1 Session Directory is specification-only until conforming implementations publish tuple evidence."
    need("publication_consistency", publication.get("claim") == claim, "README/release claim is not supported by SPEC and fixtures")
    need("publication_consistency", "The following versions are active in v0.4.1." in spec and "implementation release acceptance rule" in spec, "SPEC does not support v0.4.1 specification-only claim")
    public_prose = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("README.md", "RELEASE_NOTES.md")
        if (root / name).is_file()
    )
    need("publication_consistency", "AX v0.4.1 directory implementation is shipped and available." not in public_prose, "README/release claim is not supported by SPEC and fixtures")
    for doc in docs:
        need("publication_consistency", (root / doc).is_file(), f"required publication document missing: {doc}")

    # Fixture expectations are never sufficient by themselves: every semantic
    # group is also bound to the accepted normative source.  These are scoped
    # section markers, registry sentences, and security invariants rather than
    # broad token-presence checks.
    spec_requirements = {
        "self_id_jcs": ["each a digest in its one registered schema", "with only that self field omitted", "timestamps MUST be UTC RFC 3339 with at least millisecond precision", "SHA-256 digest identifiers MUST use"],
        "strict_examples": ["A negative mutation is applied alone to a fresh", "MUST NOT repair, round, ignore, or default the changed fact"],
        "closed_shapes": ["Every complete object is\nclosed and contains the exact registry", "Each displayed body is closed"],
        "directory_node": ["The exact operation registry and bodies are:", "<code>enrichment-run</code>", "A success response contains exactly the common envelope", "A failure response contains exactly the common envelope", "a changed body is\n<code>idempotency_mismatch</code> without new records"],
        "mesh_namespace": ["replace <code>contracts</code> with an exact 24-key map", "<code>Namespace[1..7]</code>", "<code>directory_record</code> namespace contains only schema-valid"],
        "environment_mapping": ["initial mapping is exactly <code>claude-code -> claude</code> and\n<code>codex -> codex</code>"],
        "observation_chains": ["Only a successful non-partial batch for the same root authority and realm may\npublish <code>presence=missing</code>", "Timestamps never order the chain"],
        "annotation_dag": ["Enrichment cannot supersede manual\nmetadata", "supersedes every head", "<code>generator_kind</code> MUST equal <code>generator.kind</code>"],
        "receipt_chains": ["State derives only from a valid\ncontiguous receipt chain", "recovered by operation ID before\nretry"],
        "lineage": ["Authoritative edges are exactly", "excluded from the\nauthoritative connected component", "the representative member from which the singular provider"],
        "disclosure_policy": ["Raw\nnative/transcript/preview/model payloads, credentials/auth state, terminal\noutput, PIDs/PTYs/sockets, absolute native-store paths, runtime observations,\nand SQLite rows are excluded"],
        "continuation_plan": ["Planning may perform read-only probes but MUST NOT quiesce", "no silent replan, target/intent/route\nsubstitution"],
        "route_outcomes": ["Continuation routes are the closed registry", "Outcomes are separately the closed\nregistry"],
        "target_first_move": ["lineage publication before source\nstop/release", "returns\n<code>cloned_source_still_active</code>"],
        "remote_unmanaged": ["Remote unmanaged open is always\n<code>unmanaged_remote_forbidden</code>", "A direct unmanaged move is unavailable"],
        "cloning_fidelity": ["Cross-environment routes reference the exact v0.3 Clone Capture/Raw Object", "Fidelity Report", "Read-Back Evidence"],
        "interfaces": ["Read operations are exactly <code>schema</code>", "<code>execute_plan</code>; there is no delete", "operation_index</code> MUST equal that operation's zero-based array", "drive one typed query engine", "exact agent-oriented leaves"],
        "tuple_matrix": ["The initial mapping is exactly", "Adoption is source-local and unavailable unless the exact accepted tuple proves"],
        "security": ["ANSI, OSC, bidi overrides,\ncontrols, invalid width, and hostile grapheme sequences are removed or visibly\nescaped", "All native/process launches use structured argv, explicit workspace-derived cwd,\nminimal environment allowlists"],
        "traceability": ["Appendix D. Requirement traceability", "<code>AC-DIR-INV-001</code>"],
        "publication_consistency": ["The following versions are active in v0.4.1.", "implementation release acceptance rule"],
    }
    for group, literals in spec_requirements.items():
        for literal in literals:
            need(group, literal in spec, f"SPEC semantic binding missing: {literal!r}")

    errors = [f"directory gate {group}: {message}" for group in GATE_CLASSES for message in failures[group]]
    failed = sum(bool(failures[group]) for group in GATE_CLASSES)
    return errors, {
        "directory_gate_classes": 22,
        "directory_failed_groups": failed,
        "directory_contracts": len(data.get("contracts", {})),
        "directory_fixture_families": len(families),
        "directory_expected_red_minimum": 31,
    }
