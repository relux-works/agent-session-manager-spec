"""v0.4.3 roadmap and macOS terminal-realm conformance gate."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_NEGATIVE_CASES = {
    "REALM-UNSAFE-SERVER-CREATE": ("terminal.ensure", "capability_unavailable"),
    "REALM-SENTINEL-ONLY": ("terminal.attest", "target_auth_missing"),
    "ROUTE-IMPLICIT-MUTATION": ("ax NAME", "interactive_choice_required"),
    "SYNC-OWNERSHIP-MUTATION": ("ax sync --all", "capability_unavailable"),
    "GIT-INCOMPLETE-CLOSURE": ("workspace.capture", "workspace_conflict"),
    "TAKEOVER-UNSAFE-PREFLIGHT-ORDER": ("takeover.execute", "target_auth_missing"),
    "SOCKET-REPLICATION": ("replication.select", "capability_unavailable"),
    "SDK-PREMATURE-STABILITY": ("release.admit", "capability_unavailable"),
}

EXPECTED_POSITIVE_CASES = {
    "REALM-EXISTING-BROKER-POS",
    "REALM-FUNCTIONAL-EVIDENCE-POS",
    "ROUTE-UNIQUE-NONMUTATING-POS",
    "SYNC-IMMUTABLE-POS",
    "GIT-CLOSURE-POS",
    "TAKEOVER-PREFLIGHT-POS",
    "SOCKET-LOCAL-EXCLUSION-POS",
    "SDK-INTERNAL-CONTRACT-POS",
}

EXPECTED_GIT_CLOSURE = [
    "dirty-index",
    "ignored-policy",
    "staged",
    "submodules",
    "symlinks",
    "tracked",
    "unstaged",
    "untracked",
]

SPEC_MARKERS = {
    "unsafe server creation": "A Background caller MUST NOT create a credential-dependent tmux server",
    "sentinel-only claims": "Aqua alone and sentinel-only evidence are insufficient",
    "implicit mutating route choice": "Takeover, fork, move, and every ambiguous route MUST remain a pure plan",
    "ownership-changing sync": "ax sync --all MUST NOT change ownership or launch a runtime",
    "complete Git closure": "tracked, dirty-index, staged, unstaged, untracked, ignored-policy, symlink, and submodule state",
    "unsafe preflight ordering": "Destination broker and provider-auth readiness MUST be proved before ownership commit",
    "socket replication": "The tmux socket and provider authentication state are machine-local exclusions and MUST NOT be replicated",
    "premature SDK stability": "M0 MUST NOT advertise a public stable plugin SDK",
}


def validate(root: Path, spec: str) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    path = root / "fixtures" / "v0_4_3_roadmap_terminal_realm.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"v0.4.3 gate fixture: cannot read strict JSON fixture: {exc}"], {
            "v043_gate_classes": 8,
            "v043_failed_groups": 8,
            "v043_positive_cases": 0,
            "v043_negative_cases": 0,
        }

    def need(label: str, condition: bool, detail: str) -> None:
        if not condition:
            errors.append(f"v0.4.3 gate {label}: {detail}")

    def normalized(text: str) -> str:
        return " ".join(re.sub(r"</?code>", "", text).split())

    def bounded(text: str, start: str, end: str) -> str:
        start_index = text.find(start)
        end_index = text.find(end, start_index + len(start)) if start_index >= 0 else -1
        return "" if start_index < 0 or end_index < 0 else normalized(text[start_index:end_index])

    def bounded_lines(text: str, start: str, end: str) -> list[str]:
        start_index = text.find(start)
        end_index = text.find(end, start_index + len(start)) if start_index >= 0 else -1
        if start_index < 0 or end_index < 0:
            return []
        return [line.strip() for line in text[start_index:end_index].splitlines() if line.strip()]

    def ordered(text: str, markers: list[str]) -> bool:
        positions = [text.find(marker) for marker in markers]
        return all(position >= 0 for position in positions) and positions == sorted(positions)

    need("fixture identity", data.get("fixture") == "ax-v0.4.3-roadmap-terminal-realm-v1", "fixture discriminator mismatch")
    need("release", data.get("specification_release") == "0.4.3", "specification release must be 0.4.3")

    semver = data.get("contract_semver", {})
    need("contract SemVer", semver.get("changed_contracts") == [], "roadmap/realm patch must not claim a wire-contract version change")
    need("error compatibility", semver.get("structured_error_version") == "1.2.0", "Structured Error must remain 1.2.0")
    need("error compatibility", semver.get("allowed_error_codes") == ["capability_unavailable", "target_auth_missing"], "must reuse capability_unavailable and target_auth_missing")

    roadmap = data.get("roadmap", [])
    roadmap_by_phase = {row.get("phase"): row for row in roadmap if isinstance(row, dict)}
    need("roadmap", set(roadmap_by_phase) == {"M0", "M1", "M2", "M3"}, "roadmap must contain exact M0..M3 phases")
    m0 = roadmap_by_phase.get("M0", {})
    need("SDK stability", m0.get("public_stable_plugin_sdk") is False, "M0 MUST NOT advertise a public stable plugin SDK")
    need("SDK stability", m0.get("requirements") == ["plugin-wire-contracts", "internal-plugin-interfaces", "plugin-conformance-harness"], "M0 plugin boundary must remain internal and harnessed")
    m2 = roadmap_by_phase.get("M2", {})
    need("roadmap", m2.get("product_gate") == "multi-host-mvp-preview", "M2 must be the multi-host MVP preview")
    need("roadmap", m2.get("requirements") == ["lease-fencing", "durable-journal", "idempotency", "status-first-recovery", "crash-boundary-kernel"], "M2 recovery kernel mismatch")
    need("roadmap", roadmap_by_phase.get("M3", {}).get("product_gate") == "first-daily-driver", "M3 must be the first daily-driver gate")

    positive = data.get("positive_cases", [])
    positive_by_id = {row.get("id"): row for row in positive if isinstance(row, dict)}
    need("positive cases", set(positive_by_id) == EXPECTED_POSITIVE_CASES, "positive case registry mismatch")
    need("server creation", positive_by_id.get("REALM-EXISTING-BROKER-POS", {}).get("facts", {}).get("credential_dependent_server_action") == "contact-only", "background caller may contact only an existing broker")
    realm_evidence = positive_by_id.get("REALM-FUNCTIONAL-EVIDENCE-POS", {}).get("facts", {})
    need("sentinel-only claims", realm_evidence.get("functional_sentinel") is True and realm_evidence.get("provider_auth_smoke") is True, "sentinel and separate provider-auth smoke are both required")
    need("sentinel-only claims", realm_evidence.get("evidence_binding") == ["macos_version", "provider_build", "tmux_server_generation"], "realm evidence must bind macOS version, provider build, and tmux server generation")
    route = positive_by_id.get("ROUTE-UNIQUE-NONMUTATING-POS", {}).get("facts", {})
    need("route choice", route == {"candidate_count": 1, "route": "remote_attach", "mutates_ownership": False, "launches_runtime": False}, "automatic route must be unique and non-mutating")
    sync = positive_by_id.get("SYNC-IMMUTABLE-POS", {}).get("facts", {})
    need("sync authority", sync.get("changes_ownership") is False and sync.get("launches_runtime") is False, "sync must not change ownership or launch a runtime")
    need("sync authority", sync.get("converges") == ["immutable-objects", "policy-allowed-projections"], "sync convergence scope mismatch")
    closure = positive_by_id.get("GIT-CLOSURE-POS", {}).get("facts", {}).get("closure")
    need("Git closure", closure == EXPECTED_GIT_CLOSURE, "complete Git closure registry mismatch")
    takeover = positive_by_id.get("TAKEOVER-PREFLIGHT-POS", {}).get("facts", {})
    need("preflight ordering", takeover.get("graceful_ordering") == ["destination-broker-auth-ready", "fenced-source-stop", "ownership-commit", "destination-runtime-create"], "graceful destination readiness/stop/commit/runtime ordering mismatch")
    need("preflight ordering", takeover.get("force_ordering") == ["destination-broker-auth-ready", "winning-force-lease-commit", "destination-runtime-create", "prior-owner-logically-fenced"], "force destination readiness/lease/runtime/fencing ordering mismatch")
    need("preflight ordering", takeover.get("force_verified_source_stop") is False, "force takeover must not claim a verified source-process stop")
    exclusions = positive_by_id.get("SOCKET-LOCAL-EXCLUSION-POS", {}).get("facts", {})
    need("socket replication", exclusions == {"tmux_socket": "machine-local-excluded", "provider_auth_state": "machine-local-excluded"}, "tmux socket and auth state must be machine-local exclusions")

    negative = data.get("negative_cases", [])
    negative_by_id = {row.get("id"): row for row in negative if isinstance(row, dict)}
    need("negative cases", set(negative_by_id) == set(EXPECTED_NEGATIVE_CASES), "negative case registry mismatch")
    for case_id, (entrypoint, error_code) in EXPECTED_NEGATIVE_CASES.items():
        row = negative_by_id.get(case_id, {})
        need(case_id, row.get("production_entrypoint") == entrypoint, f"production entrypoint must remain {entrypoint}")
        need(case_id, row.get("expected_error") == error_code, f"expected error must remain {error_code}")
        need(case_id, isinstance(row.get("mutation"), str) and bool(row.get("mutation")), "negative mutation description is required")

    terminal = data.get("terminal_realm", {})
    need("server creation", terminal.get("socket_mode") == "dedicated--S" and terminal.get("runtime_parent_mode") == "0700", "dedicated -S socket under private 0700 parent required")
    need("server creation", terminal.get("reject_symlink_or_path_substitution") is True, "symlink/path substitution must be rejected")
    need("sentinel-only claims", terminal.get("managername_role") == "diagnostic-hint-only", "launchctl managername must remain diagnostic only")
    need("socket replication", terminal.get("socket_replication") == "forbidden", "socket replication must be forbidden")
    need("sentinel-only claims", terminal.get("required_evidence") == ["functional-ax-sentinel", "provider-auth-smoke"], "functional sentinel and auth smoke are separately required")
    need("sentinel-only claims", terminal.get("evidence_binding") == ["macos-version", "provider-build", "tmux-server-generation"], "functional evidence binding mismatch")
    need("preflight ordering", terminal.get("logout_or_reboot_without_verified_gui_realm") == "park-until-gui-login", "logout/reboot recovery must park until GUI login")

    normalized_spec = normalized(spec)
    for label, marker in SPEC_MARKERS.items():
        normalized_marker = " ".join(marker.split())
        need(label, normalized_marker in normalized_spec, f"SPEC semantic marker missing: {marker!r}")

    graceful = bounded(spec, "### 13.6 Graceful takeover", "### 13.7 Force takeover")
    need(
        "preflight ordering",
        ordered(graceful, [
            "Destination broker and provider-auth readiness MUST be proved before ownership commit",
            "Destination calls handoff.stop",
            "destination creates each member's epoch",
            "destination validates native discovery and resumes",
        ]),
        "Section 13.6 must prove readiness, stop source, commit ownership, then create the graceful destination runtime",
    )
    force = bounded(spec, "### 13.7 Force takeover", "### 13.8 Fork")
    need(
        "preflight ordering",
        ordered(force, [
            "Force takeover MUST NOT claim or require a verified source-process stop",
            "Destination realm and provider-auth readiness MUST be proved before the force lease is persisted",
            "Only the winning committed force lease authorizes destination runtime creation",
            "the old process MAY continue until it observes that losing lease",
        ]),
        "Section 13.7 must retain the no-source-stop force exception with readiness-before-lease and runtime-after-winning-lease fencing",
    )

    takeover_diagram_path = root / "diagrams" / "plantuml" / "takeover.puml"
    continuation_diagram_path = root / "diagrams" / "plantuml" / "session_directory_continuation.puml"
    try:
        takeover_diagram = normalized(takeover_diagram_path.read_text(encoding="utf-8"))
        continuation_diagram_source = continuation_diagram_path.read_text(encoding="utf-8")
        continuation_diagram = normalized(continuation_diagram_source)
    except OSError as exc:
        need("preflight ordering", False, f"cannot read takeover/continuation production diagrams: {exc}")
    else:
        automatic_route = bounded_lines(
            continuation_diagram_source,
            "else Exactly one safe non-mutating attach/resume route",
            "else Operator confirms exact plan",
        )
        need(
            "preflight ordering",
            ordered(takeover_diagram, [
                "Prove destination realm/auth readiness",
                "Source stop is not claimed; old process may still exist",
                "Commit force lease / recompute winner",
                "Winning lease authorizes activation",
                "Create exact runtime / finalize",
                "Fenced! (Stale lease)",
            ]),
            "takeover.puml force branch must show readiness, no source-stop claim, winning lease, runtime creation, and stale-owner fencing in order",
        )
        execution = bounded(
            continuation_diagram,
            "== Revalidation and execution ==",
            "@enduml",
        )
        remote_attach = bounded(
            execution,
            "alt Remote attach to current owner",
            "else Same managed owner and environment",
        )
        local_resume = bounded(
            execution,
            "else Same managed owner and environment",
            "else Ownership takeover without conversion",
        )
        ownership_start = execution.find("else Ownership takeover without conversion")
        ownership_routes = "" if ownership_start < 0 else execution[ownership_start:]
        need(
            "route revalidation",
            ordered(continuation_diagram, [
                "else Exactly one safe non-mutating attach/resume route",
                "execute unique non-mutating route",
                "== Revalidation and execution ==",
                "verify head/lease/runtime still match",
                "verify tuple/workspace/auth still match",
                "alt Remote attach to current owner",
            ])
            and automatic_route == [
                "else Exactly one safe non-mutating attach/resume route",
                "TUI -> Planner: execute unique non-mutating route",
            ],
            "unique automatic attach/resume must pass through execution-time revalidation",
        )
        need(
            "route finalization isolation",
            ordered(remote_attach, [
                "existing owner endpoint; no lease/runtime mutation",
                "break Remote attach terminates without target finalization",
            ])
            and "finalize managed target and winning ownership" not in remote_attach,
            "remote attach must terminate before mutating target finalization",
        )
        need(
            "route finalization isolation",
            ordered(local_resume, [
                "revalidate existing winning lease and execution realm",
                "opt Current-owner resume target is macOS",
                "attest existing broker/server + provider auth",
                "create/resume under existing winning lease",
                "break Current-owner resume terminates without ownership finalization",
            ])
            and "finalize managed target and winning ownership" not in local_resume
            and "create runtime after ownership commit" not in local_resume,
            "local current-owner resume must terminate without ownership transfer/finalization",
        )
        need(
            "platform-scoped realm",
            ordered(ownership_routes, [
                "opt Ownership-creating target is macOS",
                "prove broker + separate provider-auth readiness",
                "finalize managed target and winning ownership",
                "create runtime after ownership commit",
            ]),
            "Aqua broker readiness must be conditional on a macOS target",
        )

    failed_groups = len({error.split(":", 1)[0] for error in errors})
    return errors, {
        "v043_gate_classes": 8,
        "v043_failed_groups": min(8, failed_groups),
        "v043_positive_cases": len(positive_by_id),
        "v043_negative_cases": len(negative_by_id),
    }
