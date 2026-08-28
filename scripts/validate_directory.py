"""Session Directory conformance gate used by validate_spec.py."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime
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
        "281dcffdb097544c191e57564ee054514f074050c8d6dc192b9e280fe701fa54",
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
    "urn:ax:protocol:session-directory-node": "2.0.0",
    "urn:ax:schema:session-directory-node-manifest": "1.0.0",
    "urn:ax:schema:session-directory-node-request": "2.0.0",
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
SEMVER_RE = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z"
)
TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\."
    r"[0-9]{3,9}Z\Z"
)
AX_PLATFORMS = ["macos", "linux", "wsl2", "windows"]
DIRECTORY_NODE_PROTOCOL_BINDINGS = {
    "1.0.0": {
        "request_version": "1.0.0",
        "response_version": "1.0.0",
        "manifest_version": "1.0.0",
        "probe_platforms": ["darwin", "linux", "windows"],
    },
    "2.0.0": {
        "request_version": "2.0.0",
        "response_version": "1.0.0",
        "manifest_version": "1.0.0",
        "probe_platforms": AX_PLATFORMS,
    },
}
DIRECTORY_NODE_NEGOTIATION = {
    "preference": "highest_mutual_major",
    "no_shared_major": "incompatible_protocol",
    "no_shared_major_exit_code": 6,
    "cross_major_coercion": False,
    "fresh_process_per_attempt": True,
    "manifest_success_exit_code": 0,
    "downgrade_trigger": {
        "operation": "manifest",
        "code": "incompatible_protocol",
        "exit_code": 6,
        "retryable": False,
        "require_exact_echo": True,
    },
    "non_downgrade_failures": [
        "authentication_failure",
        "integrity_failure",
        "malformed_frame",
        "operation_error",
        "wrong_echo",
    ],
    "v1_wsl2": "unrepresentable",
}
DIRECTORY_NODE_NEGOTIATION_CASES = {
    "v2-selected": {"caller_supported_majors": [2, 1], "peer_supported_majors": [2, 1]},
    "v2-to-v1": {"caller_supported_majors": [2, 1], "peer_supported_majors": [1]},
    "v1-only": {"caller_supported_majors": [1], "peer_supported_majors": [1]},
    "no-common-major": {"caller_supported_majors": [2, 1], "peer_supported_majors": [3]},
}
DIRECTORY_NODE_NEGOTIATION_ATTEMPT_FIELDS = {
    "process_id",
    "request_id",
    "request_major",
    "request_schema",
    "request_schema_version",
    "request_protocol",
    "request_protocol_version",
    "request_operation",
    "request_deadline_ms",
    "request_body",
    "response_kind",
    "response_echo_major",
    "response_schema",
    "response_schema_version",
    "response_echo_protocol",
    "response_echo_protocol_version",
    "response_echo_request_id",
    "response_echo_operation",
    "manifest_supported_protocol_versions",
    "error",
    "exit_code",
}
DIRECTORY_CAPABILITIES = {
    "directory_discovery",
    "directory_incremental_scan",
    "directory_head_digest",
    "directory_tail_preview",
    "native_title_read",
    "native_runtime_observation",
    "existing_session_adoption",
    "native_resume",
}

# These rules are keyed by the immutable schema and an exact JSON path. They
# deliberately do not infer a type from a value prefix or a field-name suffix:
# a malformed value must still be checked against its declared contract type.
# ``*`` descends through every member of an array. The optional fourth rule
# member names a nullable ancestor separately from leaf nullability: a null
# parent may stop traversal, but every member is still required and non-null
# when that parent is an object.
COMMON_TYPE_RULES = {
    "urn:ax:schema:environment-observation": [
        ("host_id", "uuidv7", False),
        ("installation_id", "digest", False),
        ("backend_realm_fingerprint", "digest", False),
        ("platform", "ax_platform", False),
        ("observed_at", "timestamp", False),
        ("capabilities.{}.status", "enum:available|conditional|unavailable|unknown", False),
        ("capabilities.{}.reason_code", "string", True),
        ("capabilities.{}.evidence_ids", "sorted_unique:digest", False),
        ("capabilities.{}.observed_at", "timestamp", False),
    ],
    "urn:ax:schema:native-session-observation": [
        ("instance_id", "digest", False),
        ("host_id", "uuidv7", False),
        ("installation_id", "digest", False),
        ("previous_observation_id", "digest", True),
        ("managed_session_id", "uuidv7", True),
        ("provider_identity_record_id", "digest", True),
        ("lineage_anchor_hint", "uuidv7_or_digest", True),
        ("head_digest", "digest", False),
        ("created_at", "timestamp", True),
        ("updated_at", "timestamp", False),
        ("observed_at", "timestamp", False),
        ("warnings", "sorted_unique:string", False),
    ],
    "urn:ax:schema:session-inventory-batch": [
        ("host_id", "uuidv7", False),
        ("previous_batch_id", "digest", True),
        ("environment_observation_ids", "sorted_unique:digest", False),
        ("native_observation_ids", "sorted_unique:digest", False),
        ("scan_root_authority_ids", "sorted_unique:digest", False),
        ("adapter_builds", "sorted_unique:jcs", False),
        ("adapter_builds.*.executable_sha256", "digest", False),
        ("adapter_builds.*.adapter_version", "semver", False),
        ("started_at", "timestamp", False),
        ("completed_at", "timestamp", False),
        ("error_codes", "sorted_unique:string", False),
    ],
    "urn:ax:schema:conversation-lineage-link": [
        ("from_id", "uuidv7_or_digest", False),
        ("to_id", "uuidv7_or_digest", False),
        ("canonical_anchor_id", "uuidv7_or_digest", False),
        ("member_root_id", "uuidv7_or_digest", False),
        ("evidence_ids", "sorted_unique:digest", False),
        ("supersedes_link_ids", "sorted_unique:digest", False),
        ("authorized_by_host_id", "uuidv7", False),
        ("created_at", "timestamp", False),
    ],
    "urn:ax:schema:session-annotation": [
        ("subject_id", "uuidv7_or_digest", False),
        ("subject_head_digest", "digest", True),
        ("author_host_id", "uuidv7", False),
        ("profile_id", "digest", True),
        ("generator.prompt_digest", "digest", True),
        ("evidence_ids", "sorted_unique:digest", False),
        ("redaction_summary.policy_digest", "digest", False),
        ("redaction_summary.classes", "sorted_unique:string", False),
        ("supersedes_annotation_ids", "sorted_unique:digest", False),
        ("created_at", "timestamp", False),
    ],
    "urn:ax:schema:session-enrichment-profile": [
        ("subject_kinds", "sorted_unique:string", False),
        ("provider_ids", "sorted_unique:string", False),
        ("input_classes", "sorted_unique:string", False),
        ("redaction_policy_id", "digest", False),
        ("generator.prompt_digest", "digest", True),
    ],
    "urn:ax:schema:session-enrichment-job-request": [
        ("job_id", "uuidv7", False),
        ("subject_id", "uuidv7_or_digest", False),
        ("expected_head_digest", "digest", False),
        ("source_host_id", "uuidv7", False),
        ("source_instance_id", "digest", False),
        ("profile_id", "digest", False),
        ("requested_kinds", "sorted_unique:string", False),
        ("prior_annotation_ids", "sorted_unique:digest", False),
        ("delta_start_evidence_id", "digest", True),
        ("idempotency_key", "digest", False),
        ("deadline", "timestamp", False),
        ("created_at", "timestamp", False),
    ],
    "urn:ax:schema:session-enrichment-job-receipt": [
        ("previous_job_receipt_id", "digest", True),
        ("job_request_id", "digest", False),
        ("job_id", "uuidv7", False),
        ("profile_id", "digest", False),
        ("subject_head_digest", "digest", False),
        ("claim_host_id", "uuidv7", True),
        ("claim_lease_id", "uuidv7", True),
        ("claim_acquired_at", "timestamp", True),
        ("claim_expires_at", "timestamp", True),
        ("receipt_at", "timestamp", False),
        ("redaction_summary.policy_digest", "digest", False),
        ("redaction_summary.classes", "sorted_unique:string", False),
        ("generator.prompt_digest", "digest", True),
        ("produced_annotation_ids", "sorted_unique:digest", False),
        ("started_at", "timestamp", True),
        ("ended_at", "timestamp", True),
        ("superseded_by_head_digest", "digest", True),
    ],
    "urn:ax:schema:session-continuation-plan": [
        ("operation_id", "uuidv7", False),
        ("created_at", "timestamp", False),
        ("expires_at", "timestamp", False),
        ("entry_id", "uuidv7_or_digest", False),
        ("lineage_anchor_id", "uuidv7_or_digest", False),
        ("source_session_id", "uuidv7", True),
        ("source_instance_id", "digest", False),
        ("source_host_id", "uuidv7", False),
        ("source_observation_id", "digest", False),
        ("source_head_digest", "digest", False),
        ("source_lease.epoch", "positive_uint53", False, "source_lease"),
        ("source_lease.lease_id", "uuidv4", False, "source_lease"),
        ("source_lease.holder_host_id", "uuidv7", False, "source_lease"),
        ("source_checkpoint_id", "digest", True),
        ("source_runtime.evidence_id", "digest", True),
        ("source_runtime.observed_at", "timestamp", False),
        ("target.host_id", "uuidv7", False),
        ("target.installation_id", "digest", False),
        ("target.backend_realm_fingerprint", "digest", False),
        ("target.environment_tuple.environment_id", "nonempty_string", False),
        ("target.environment_tuple.environment_version", "nonempty_string", False),
        ("target.environment_tuple.platform", "ax_platform", False),
        ("target.environment_tuple.architecture", "architecture", False),
        ("target.environment_tuple.store_schema_fingerprint", "digest", False),
        ("target.environment_tuple.adapter_version", "semver", False),
        ("workspace.workspace_group_id", "uuidv7", True),
        ("workspace.workspace_record_id", "digest", True),
        ("workspace.checkpoint_id", "digest", True),
        ("workspace.cohort_session_ids", "sorted_unique:uuidv7", False),
        ("workspace.transfer_manifest_id", "digest", True),
        ("workspace.materialization_plan_id", "digest", True),
        ("policy_digest", "digest", False),
        ("steps.*.input_digest", "digest", False),
        ("steps.*.prerequisite_step_ids", "sorted_unique:string", False),
        ("adoption_plan_id", "digest", True),
        ("projection_plan_id", "digest", True),
        ("fidelity_report_id", "digest", True),
        ("required_capabilities", "sorted_unique:string", False),
        ("contract_assertions", "sorted_unique:jcs", False),
        ("confirmations", "sorted_unique:string", False),
        ("allowed_fallback_outcomes", "sorted_unique:string", False),
        ("request_digest", "digest", False),
        ("adapter_digest", "digest", False),
        ("controller_digest", "digest", False),
    ],
    "urn:ax:schema:session-directory-operation-receipt": [
        ("previous_directory_receipt_id", "digest", True),
        ("operation_id", "uuidv7", False),
        ("plan_id", "digest", False),
        ("request_digest", "digest", False),
        ("initiating_host_id", "uuidv7", False),
        ("responsible_host_id", "uuidv7", False),
        ("idempotency_key", "digest", False),
        ("validated_source.session_id", "uuidv7", True),
        ("validated_source.instance_id", "digest", False),
        ("validated_source.host_id", "uuidv7", False),
        ("validated_source.observation_id", "digest", False),
        ("validated_source.head_digest", "digest", False),
        ("validated_source.lease_id", "uuidv7", True),
        ("validated_source.checkpoint_id", "digest", True),
        ("validated_source.runtime.evidence_id", "digest", True),
        ("validated_source.runtime.observed_at", "timestamp", False),
        ("validated_target.target.host_id", "uuidv7", False),
        ("validated_target.target.installation_id", "digest", False),
        ("validated_target.target.backend_realm_fingerprint", "digest", False),
        ("validated_target.target.environment_tuple.environment_id", "nonempty_string", False),
        ("validated_target.target.environment_tuple.environment_version", "nonempty_string", False),
        ("validated_target.target.environment_tuple.platform", "ax_platform", False),
        ("validated_target.target.environment_tuple.architecture", "architecture", False),
        ("validated_target.target.environment_tuple.store_schema_fingerprint", "digest", False),
        ("validated_target.target.environment_tuple.adapter_version", "semver", False),
        ("validated_target.environment_observation_id", "digest", False),
        ("validated_target.capability_evidence_ids", "sorted_unique:digest", False),
        ("validated_target.workspace.workspace_group_id", "uuidv7", True),
        ("validated_target.workspace.workspace_record_id", "digest", True),
        ("validated_target.workspace.checkpoint_id", "digest", True),
        ("validated_target.workspace.cohort_session_ids", "sorted_unique:uuidv7", False),
        ("validated_target.workspace.transfer_manifest_id", "digest", True),
        ("validated_target.workspace.materialization_plan_id", "digest", True),
        ("validated_target.policy_digest", "digest", False),
        ("validated_target.contract_assertions", "sorted_unique:jcs", False),
        ("validated_target.validated_at", "timestamp", False),
        ("effect_receipt_ids", "sorted_unique:digest", False),
        ("durable_effects", "sorted_unique:string", False),
        ("compensations", "sorted_unique:string", False),
        ("created_at", "timestamp", False),
    ],
}

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
    "environment_tuple": ["environment_id", "environment_version", "platform", "architecture", "store_schema_fingerprint", "adapter_version"],
    "lease_expectation": ["epoch", "lease_id", "holder_host_id"],
    "annotation_text_payload": ["text"],
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

# Every closed object reachable from an immutable positive vector is validated
# at its exact path. Array and map wildcards are intentionally distinct: a
# dict cannot impersonate an array (or vice versa) and skip child validation.
# Nullable applies to the object itself, never to omitted members.
RECURSIVE_SHAPE_RULES = {
    "urn:ax:schema:environment-observation": [
        ("capabilities", "capability_result", "map", False, DIRECTORY_CAPABILITIES),
    ],
    "urn:ax:schema:native-session-observation": [
        ("workspace_identity", "workspace_identity", "object", True, None),
        ("message_counts", "message_counts", "object", False, None),
    ],
    "urn:ax:schema:session-inventory-batch": [
        ("adapter_builds", "adapter_build", "array", False, None),
    ],
    "urn:ax:schema:conversation-lineage-link": [],
    "urn:ax:schema:session-annotation": [
        ("payload", "annotation_text_payload", "object", False, None),
        ("generator", "generator_identity", "object", True, None),
        ("redaction_summary", "redaction_summary", "object", False, None),
    ],
    "urn:ax:schema:session-enrichment-profile": [
        ("generator", "generator_identity", "object", False, None),
    ],
    "urn:ax:schema:session-enrichment-job-request": [],
    "urn:ax:schema:session-enrichment-job-receipt": [
        ("redaction_summary", "redaction_summary", "object", False, None),
        ("generator", "generator_identity", "object", False, None),
        ("usage", "usage_summary", "object", True, None),
    ],
    "urn:ax:schema:session-continuation-plan": [
        ("source_lease", "lease_expectation", "object", True, None),
        ("source_runtime", "runtime_expectation", "object", False, None),
        ("target", "directory_target", "object", False, None),
        ("target.environment_tuple", "environment_tuple", "object", False, None),
        ("workspace", "workspace_route", "object", False, None),
        ("steps", "continuation_step", "array", False, None),
        ("contract_assertions", "contract_assertion", "array", False, None),
    ],
    "urn:ax:schema:session-directory-operation-receipt": [
        ("validated_source", "validated_source", "object", False, None),
        ("validated_source.runtime", "runtime_expectation", "object", False, None),
        ("validated_target", "validated_target", "object", False, None),
        ("validated_target.target", "directory_target", "object", False, None),
        ("validated_target.target.environment_tuple", "environment_tuple", "object", False, None),
        ("validated_target.workspace", "workspace_route", "object", False, None),
        ("validated_target.contract_assertions", "contract_assertion", "array", False, None),
    ],
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
        rows = [line for line in spec.splitlines() if line.startswith("|") and f"<code>{contract}</code>" in line]
        need("contract_registry", bool(rows) and any(f"<code>{version}</code>" in row for row in rows), f"SPEC registry missing {contract} version {version}")
    for contract in (
        "urn:ax:protocol:session-directory-node",
        "urn:ax:schema:session-directory-node-request",
    ):
        rows = [line for line in spec.splitlines() if line.startswith("|") and f"<code>{contract}</code>" in line]
        need(
            "contract_registry",
            len(rows) == 1 and "<code>1.0.0</code>" in rows[0] and "<code>2.0.0</code>" in rows[0],
            f"Directory Node contract history missing immutable v1/v2 versions for {contract}",
        )

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

    def path_values(
        value: object,
        path: tuple[str, ...],
        location: str,
    ) -> tuple[list[tuple[object, str]], list[tuple[str, bool]]]:
        if not path:
            return [(value, location)], []
        head, *tail = path
        if head == "*":
            if not isinstance(value, list):
                return [], [(location, value is None)]
            found: list[tuple[object, str]] = []
            missing: list[tuple[str, bool]] = []
            for index, child in enumerate(value):
                child_found, child_missing = path_values(child, tuple(tail), f"{location}[{index}]")
                found.extend(child_found)
                missing.extend(child_missing)
            return found, missing
        if head == "{}":
            if not isinstance(value, dict):
                return [], [(location, value is None)]
            found = []
            missing = []
            for key, child in value.items():
                child_found, child_missing = path_values(child, tuple(tail), f"{location}[{key!r}]")
                found.extend(child_found)
                missing.extend(child_missing)
            return found, missing
        if not isinstance(value, dict):
            return [], [(location, value is None)]
        if head not in value:
            return [], [(f"{location}.{head}", False)]
        return path_values(value[head], tuple(tail), f"{location}.{head}")

    def valid_uuid(value: object, version: int) -> bool:
        if not isinstance(value, str):
            return False
        try:
            parsed = uuid.UUID(value)
        except (ValueError, AttributeError):
            return False
        return str(parsed) == value and parsed.version == version and parsed.variant == uuid.RFC_4122

    def valid_timestamp(value: object) -> tuple[bool, bool]:
        if not isinstance(value, str) or not TIMESTAMP_RE.fullmatch(value):
            return False, False
        try:
            parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError:
            return True, False
        return True, parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0

    def validate_scalar(kind: str, value: object, location: str) -> None:
        if kind == "digest":
            need("self_id_jcs", isinstance(value, str) and bool(DIGEST_RE.fullmatch(value)), f"schema-directed digest validation failed at {location}")
        elif kind == "uuidv7":
            need("self_id_jcs", valid_uuid(value, 7), f"schema-directed UUIDv7 validation failed at {location}")
        elif kind == "uuidv4":
            need("self_id_jcs", valid_uuid(value, 4), f"schema-directed UUIDv4 validation failed at {location}")
        elif kind == "uuidv7_or_digest":
            need("self_id_jcs", valid_uuid(value, 7) or (isinstance(value, str) and bool(DIGEST_RE.fullmatch(value))), f"schema-directed UUIDv7-or-digest validation failed at {location}")
        elif kind == "timestamp":
            shape_valid, calendar_valid = valid_timestamp(value)
            need("self_id_jcs", shape_valid, f"timestamp must be UTC RFC 3339 with at least millisecond precision at {location}")
            if shape_valid:
                need("self_id_jcs", calendar_valid, f"timestamp is not a real UTC calendar instant at {location}")
        elif kind == "ax_platform":
            need("self_id_jcs", value in AX_PLATFORMS, f"platform must use the AX enum macos|linux|wsl2|windows at {location}")
        elif kind == "architecture":
            need("self_id_jcs", value in {"amd64", "arm64"}, f"schema-directed architecture validation failed at {location}")
        elif kind == "semver":
            need("self_id_jcs", isinstance(value, str) and bool(SEMVER_RE.fullmatch(value)), f"schema-directed SemVer validation failed at {location}")
        elif kind == "uint53":
            need("self_id_jcs", isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9007199254740991, f"schema-directed uint53 validation failed at {location}")
        elif kind == "positive_uint53":
            need("self_id_jcs", isinstance(value, int) and not isinstance(value, bool) and 0 < value <= 9007199254740991, f"schema-directed positive uint53 validation failed at {location}")
        elif kind.startswith("enum:"):
            allowed = kind.split(":", 1)[1].split("|")
            need("self_id_jcs", value in allowed, f"schema-directed enum validation failed at {location}")
        elif kind == "nonempty_string":
            need("self_id_jcs", isinstance(value, str) and bool(value), f"schema-directed non-empty string validation failed at {location}")
        elif kind == "string":
            need("self_id_jcs", isinstance(value, str), f"schema-directed string validation failed at {location}")
        else:
            need("self_id_jcs", False, f"unknown schema-directed common type {kind} at {location}")

    def validate_typed_value(kind: str, value: object, nullable: bool, location: str) -> None:
        if value is None:
            need("self_id_jcs", nullable, f"null is forbidden by schema-directed common type at {location}")
            return
        if kind.startswith("sorted_unique:"):
            element_kind = kind.split(":", 1)[1]
            if not isinstance(value, list):
                need("self_id_jcs", False, f"schema-directed sorted-unique validation failed at {location}")
                return
            if element_kind == "jcs":
                byte_keys = [canonical(child) for child in value]
            else:
                for index, child in enumerate(value):
                    validate_scalar(element_kind, child, f"{location}[{index}]")
                byte_keys = [canonical(child) for child in value if isinstance(child, str)]
            need(
                "self_id_jcs",
                len(byte_keys) == len(value) and byte_keys == sorted(set(byte_keys)),
                f"schema-directed sorted-unique validation failed at {location}",
            )
            return
        validate_scalar(kind, value, location)

    def validate_common_values(schema: str, canonical_input: dict[str, object], location: str) -> None:
        rules = COMMON_TYPE_RULES.get(schema)
        need("self_id_jcs", rules is not None, f"schema-directed common-type rule registry missing for {schema}")
        if rules is None:
            return
        for rule in rules:
            path, kind, nullable = rule[:3]
            nullable_ancestor = rule[3] if len(rule) == 4 else None
            values, missing_locations = path_values(canonical_input, tuple(path.split(".")), location)
            for missing_location, null_parent in missing_locations:
                need(
                    "self_id_jcs",
                    (nullable_ancestor is None and nullable and null_parent)
                    or (
                        null_parent
                        and nullable_ancestor is not None
                        and missing_location == f"{location}.{nullable_ancestor}"
                    ),
                    f"required schema-directed path missing at {missing_location}",
                )
            for value, value_location in values:
                validate_typed_value(kind, value, nullable, value_location)

    def validate_closed_instance(value: object, shape: str, location: str) -> None:
        expected_members = CLOSED_OBJECTS.get(shape)
        need("self_id_jcs", expected_members is not None, f"recursive closed shape registry missing for {shape}")
        if expected_members is None:
            return
        need("self_id_jcs", isinstance(value, dict), f"recursive closed shape {shape} must be an object at {location}")
        if not isinstance(value, dict):
            return
        need(
            "self_id_jcs",
            set(value) == set(expected_members),
            f"recursive closed shape {shape} member mismatch at {location}",
        )
        if "extensions" in expected_members:
            need(
                "self_id_jcs",
                isinstance(value.get("extensions"), dict),
                f"recursive closed shape {shape} extensions must be an object at {location}.extensions",
            )
        if shape == "capability_result":
            status = value.get("status")
            reason = value.get("reason_code")
            need(
                "self_id_jcs",
                (status == "available" and reason is None)
                or (status in {"conditional", "unavailable", "unknown"} and isinstance(reason, str) and bool(reason)),
                f"CapabilityResult status/reason conditional mismatch at {location}",
            )

    def validate_recursive_shapes(schema: str, canonical_input: dict[str, object], location: str) -> None:
        rules = RECURSIVE_SHAPE_RULES.get(schema)
        need("self_id_jcs", rules is not None, f"recursive closed-shape rule registry missing for {schema}")
        if rules is None:
            return
        for path, shape, container, nullable, exact_keys in rules:
            values, missing_locations = path_values(canonical_input, tuple(path.split(".")), location)
            for missing_location, _ in missing_locations:
                need("self_id_jcs", False, f"required recursive closed shape missing at {missing_location}")
            for value, value_location in values:
                if value is None:
                    need("self_id_jcs", nullable, f"null recursive closed shape forbidden at {value_location}")
                    continue
                if container == "object":
                    validate_closed_instance(value, shape, value_location)
                    continue
                if container == "array":
                    need("self_id_jcs", isinstance(value, list), f"recursive closed shape array required at {value_location}")
                    if isinstance(value, list):
                        for index, child in enumerate(value):
                            validate_closed_instance(child, shape, f"{value_location}[{index}]")
                    continue
                if container == "map":
                    need("self_id_jcs", isinstance(value, dict), f"recursive closed shape map required at {value_location}")
                    if isinstance(value, dict):
                        if exact_keys is not None:
                            need(
                                "self_id_jcs",
                                set(value) == exact_keys,
                                f"recursive closed shape map cardinality/key mismatch at {value_location}",
                            )
                        for key, child in value.items():
                            validate_closed_instance(child, shape, f"{value_location}[{key!r}]")
                    continue
                need("self_id_jcs", False, f"unknown recursive closed shape container {container} at {value_location}")

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
        validate_common_values(schema, canonical_input, f"identity_vectors[{schema}].canonical_input")
        validate_recursive_shapes(schema, canonical_input, f"identity_vectors[{schema}].canonical_input")
        validate_typed_value("digest", row.get("expected_id"), False, f"identity_vectors[{schema}].expected_id")
        need("self_id_jcs", self_field not in canonical_input, f"identity vector canonical_input must omit only self field {self_field} for {schema}")
        expected_members = set(CLOSED_OBJECTS[SELF_SCHEMA_SHAPES[schema]]) - {self_field}
        need("self_id_jcs", set(canonical_input) == expected_members, f"identity vector canonical_input must contain every closed member except self field {self_field} for {schema}")
        actual = "sha256:" + hashlib.sha256(canonical(canonical_input)).hexdigest()
        need("self_id_jcs", row.get("expected_id") == actual, f"wrong self-ID for {schema}: expected {actual}")
    ids = data.get("sorted_id_fixture", [])
    need("self_id_jcs", ids == sorted(set(ids)), "sorted_id_fixture must be bytewise sorted and unique")
    for index, identity in enumerate(ids):
        validate_typed_value("digest", identity, False, f"sorted_id_fixture[{index}]")

    common_cases = data.get("common_type_cases", {})
    if not isinstance(common_cases, dict):
        need("self_id_jcs", False, "common_type_cases must be a closed object")
        common_cases = {}
    need(
        "self_id_jcs",
        set(common_cases) == {"digest", "uuidv4", "uuidv7", "uuidv7_or_digest", "nullable_digest", "timestamps", "sorted_unique"}
        and len(common_cases.get("uuidv7_or_digest", [])) == 2
        and len(common_cases.get("nullable_digest", [])) == 2
        and len(common_cases.get("timestamps", [])) == 2,
        "common-type positive oracle must contain every exact typed case",
    )
    validate_typed_value("digest", common_cases.get("digest"), False, "common_type_cases.digest")
    validate_typed_value("uuidv4", common_cases.get("uuidv4"), False, "common_type_cases.uuidv4")
    validate_typed_value("uuidv7", common_cases.get("uuidv7"), False, "common_type_cases.uuidv7")
    for index, identity in enumerate(common_cases.get("uuidv7_or_digest", [])):
        validate_typed_value("uuidv7_or_digest", identity, False, f"common_type_cases.uuidv7_or_digest[{index}]")
    for index, digest in enumerate(common_cases.get("nullable_digest", [])):
        validate_typed_value("digest", digest, True, f"common_type_cases.nullable_digest[{index}]")
    for index, timestamp in enumerate(common_cases.get("timestamps", [])):
        validate_typed_value("timestamp", timestamp, False, f"common_type_cases.timestamps[{index}]")
    validate_typed_value("sorted_unique:string", common_cases.get("sorted_unique"), False, "common_type_cases.sorted_unique")

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
    protocol_bindings = node.get("protocol_bindings", {})
    need("directory_node", protocol_bindings.get("1.0.0", {}).get("request_version") == "1.0.0" and protocol_bindings.get("2.0.0", {}).get("request_version") == "2.0.0", "Directory Node protocol/request major binding mismatch")
    need("directory_node", protocol_bindings.get("2.0.0", {}).get("probe_platforms") == AX_PLATFORMS, "Directory Node 2 probe platform registry must be macos|linux|wsl2|windows")
    need("directory_node", protocol_bindings == DIRECTORY_NODE_PROTOCOL_BINDINGS, "Directory Node protocol/request major binding mismatch")
    need("directory_node", node.get("negotiation") == DIRECTORY_NODE_NEGOTIATION, "Directory Node dual-stack negotiation registry mismatch")
    negotiation_cases = node.get("negotiation_cases", [])
    case_ids = [case.get("case_id") for case in negotiation_cases if isinstance(case, dict)]
    need(
        "directory_node",
        len(negotiation_cases) == len(DIRECTORY_NODE_NEGOTIATION_CASES)
        and set(case_ids) == set(DIRECTORY_NODE_NEGOTIATION_CASES)
        and len(case_ids) == len(set(case_ids)),
        "Directory Node bootstrap fixtures must contain exact v2-selected, v2-to-v1, v1-only, and no-common-major cases",
    )
    for case in negotiation_cases if isinstance(negotiation_cases, list) else []:
        if not isinstance(case, dict):
            need("directory_node", False, "Directory Node bootstrap fixture case must be an object")
            continue
        case_id = case.get("case_id", "unknown")
        caller_majors = case.get("caller_supported_majors")
        peer_majors = case.get("peer_supported_majors")
        attempts = case.get("attempts")
        caller_valid = isinstance(caller_majors, list) and bool(caller_majors) and all(type(major) is int and major in {1, 2} for major in caller_majors)
        caller_valid = caller_valid and caller_majors == sorted(set(caller_majors), reverse=True)
        peer_valid = isinstance(peer_majors, list) and bool(peer_majors) and all(type(major) is int and major > 0 for major in peer_majors)
        peer_valid = peer_valid and peer_majors == sorted(set(peer_majors), reverse=True)
        need("directory_node", caller_valid, f"Directory Node bootstrap {case_id} caller majors must be unique descending supported majors")
        need("directory_node", peer_valid, f"Directory Node bootstrap {case_id} peer majors must be unique descending positive majors")
        scenario = DIRECTORY_NODE_NEGOTIATION_CASES.get(case_id)
        need(
            "directory_node",
            scenario is not None
            and caller_majors == scenario["caller_supported_majors"]
            and peer_majors == scenario["peer_supported_majors"],
            f"Directory Node bootstrap {case_id} must match its exact named caller/peer scenario",
        )
        if not caller_valid or not peer_valid or not isinstance(attempts, list):
            need("directory_node", False, f"Directory Node bootstrap {case_id} attempts must be executable")
            continue
        first_mutual = next((major for major in caller_majors if major in peer_majors), None)
        attempted_majors = caller_majors[: caller_majors.index(first_mutual) + 1] if first_mutual is not None else caller_majors
        need("directory_node", len(attempts) == len(attempted_majors), f"Directory Node bootstrap {case_id} must terminate at first mutual major or after exhaustion")
        process_ids = [attempt.get("process_id") for attempt in attempts if isinstance(attempt, dict)]
        need(
            "directory_node",
            len(process_ids) == len(attempts) and len(process_ids) == len(set(process_ids)) and all(isinstance(value, str) and value for value in process_ids),
            f"Directory Node bootstrap {case_id} must use a fresh process for every attempt",
        )
        for index, expected_major in enumerate(attempted_majors):
            if index >= len(attempts) or not isinstance(attempts[index], dict):
                continue
            attempt = attempts[index]
            request_id = attempt.get("request_id")
            expected_version = f"{expected_major}.0.0"
            need(
                "directory_node",
                set(attempt) == DIRECTORY_NODE_NEGOTIATION_ATTEMPT_FIELDS,
                f"Directory Node bootstrap {case_id} attempt {index + 1} must contain the exact closed attempt fields",
            )
            valid_request = (
                valid_uuid(request_id, 7)
                and attempt.get("request_schema") == "urn:ax:schema:session-directory-node-request"
                and attempt.get("request_operation") == "manifest"
                and type(attempt.get("request_deadline_ms")) is int
                and 1 <= attempt.get("request_deadline_ms") <= 3600000
                and attempt.get("request_body") == {}
            )
            need("directory_node", valid_request, f"Directory Node bootstrap {case_id} attempt {index + 1} request must be closed schema-valid manifest input")
            exact_echo = (
                type(attempt.get("request_major")) is int
                and attempt.get("request_major") == expected_major
                and attempt.get("request_protocol") == "urn:ax:protocol:session-directory-node"
                and attempt.get("request_protocol_version") == expected_version
                and attempt.get("request_schema_version") == expected_version
                and type(attempt.get("response_echo_major")) is int
                and attempt.get("response_echo_major") == expected_major
                and attempt.get("response_schema") == "urn:ax:schema:session-directory-node-response"
                and attempt.get("response_echo_protocol") == attempt.get("request_protocol")
                and attempt.get("response_echo_protocol_version") == attempt.get("request_protocol_version")
                and attempt.get("response_schema_version") == "1.0.0"
                and attempt.get("response_echo_request_id") == request_id
                and attempt.get("response_echo_operation") == attempt.get("request_operation")
            )
            need("directory_node", exact_echo, f"Directory Node bootstrap {case_id} attempt {index + 1} must exactly echo request identity")
            if expected_major in peer_majors:
                supported_versions = attempt.get("manifest_supported_protocol_versions")
                valid_success = (
                    attempt.get("response_kind") == "manifest_success"
                    and attempt.get("error") is None
                    and type(attempt.get("exit_code")) is int
                    and attempt.get("exit_code") == 0
                    and supported_versions == sorted(f"{major}.0.0" for major in peer_majors if major in {1, 2})
                )
                need("directory_node", valid_success, f"Directory Node bootstrap {case_id} selected-major manifest success framing mismatch")
            else:
                valid_downgrade = (
                    attempt.get("response_kind") == "unsupported_major"
                    and attempt.get("manifest_supported_protocol_versions") is None
                    and attempt.get("error") == {"code": "incompatible_protocol", "exit_code": 6, "retryable": False}
                    and type(attempt.get("exit_code")) is int
                    and attempt.get("exit_code") == 6
                )
                need("directory_node", valid_downgrade, f"Directory Node bootstrap {case_id} downgrade requires exact incompatible_protocol/6/non-retryable response and exit")
        expected_error = None if first_mutual is not None else "incompatible_protocol"
        expected_exit = 0 if first_mutual is not None else 6
        selected_major_valid = (
            case.get("expected_selected_major") is None
            if first_mutual is None
            else type(case.get("expected_selected_major")) is int and case.get("expected_selected_major") == first_mutual
        )
        need(
            "directory_node",
            selected_major_valid
            and case.get("expected_manifest_trusted") is (first_mutual is not None)
            and case.get("expected_error") == expected_error
            and type(case.get("expected_exit_code")) is int
            and case.get("expected_exit_code") == expected_exit,
            f"Directory Node bootstrap {case_id} terminal outcome mismatch",
        )
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
    need("publication_consistency", publication.get("spec_version") == "0.4.2" and publication.get("frozen_digest_owner") == "publication-task" and publication.get("required_documents") == docs, "v0.4.2 candidate/release ownership or document registry mismatch")
    claim = "AX v0.4.2 Session Directory is specification-only until conforming implementations publish tuple evidence."
    need("publication_consistency", publication.get("claim") == claim, "README/release claim is not supported by SPEC and fixtures")
    need("publication_consistency", "The following versions are active in v0.4.2." in spec and "implementation release acceptance rule" in spec, "SPEC does not support v0.4.2 specification-only claim")
    public_prose = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("README.md", "RELEASE_NOTES.md")
        if (root / name).is_file()
    )
    need("publication_consistency", "AX v0.4.2 directory implementation is shipped and available." not in public_prose, "README/release claim is not supported by SPEC and fixtures")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    current_baseline_claim = "current first safe Session Directory implementation baseline"
    superseded_v041_claim = "v0.4.2 now supersedes that historical claim"
    need("publication_consistency", changelog.count(current_baseline_claim) == 1, "CHANGELOG must contain exactly one current first-safe Session Directory implementation baseline claim")
    need("publication_consistency", superseded_v041_claim in changelog and "v0.4.1 is not the current implementation baseline" in changelog, "CHANGELOG v0.4.1 baseline history must be explicitly superseded by v0.4.2")
    for doc in docs:
        need("publication_consistency", (root / doc).is_file(), f"required publication document missing: {doc}")

    # Fixture expectations are never sufficient by themselves: every semantic
    # group is also bound to the accepted normative source.  These are scoped
    # section markers, registry sentences, and security invariants rather than
    # broad token-presence checks.
    spec_requirements = {
        "self_id_jcs": ["each a digest in its one registered schema", "with only that self field omitted", "timestamps MUST be real UTC RFC 3339 calendar instants", "schema/version and exact JSON path", "SHA-256 digest identifiers MUST use"],
        "strict_examples": ["A negative mutation is applied alone to a fresh", "MUST NOT repair, round, ignore, or default the changed fact"],
        "closed_shapes": ["Every complete object is\nclosed and contains the exact registry", "Each displayed body is closed"],
        "directory_node": ["strictly descending numeric order", "Each\nattempt MUST launch a fresh process", "There is exactly one downgrade trigger", "wrong or missing\necho", "If every locally supported major returns the exact downgrade tuple", "The exact operation registry and bodies are:", "<code>enrichment-run</code>", "A success response contains exactly the common envelope", "A failure response contains exactly the common envelope", "a changed body is\n<code>idempotency_mismatch</code> without new records"],
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
        "publication_consistency": ["The following versions are active in v0.4.2.", "implementation release acceptance rule"],
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
