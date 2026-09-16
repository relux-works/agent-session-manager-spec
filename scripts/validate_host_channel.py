#!/usr/bin/env python3
"""Source-only Host Channel contract gate; does not implement TLS or AX dispatch.

The fact vectors are synthetic inputs, never evidence of an actual handshake.
The public caller is validate_spec.main via validate(root, spec).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from host_admission import read_policy, render_table, TABLE, failures, admits, unique_pairs

GATES = ["HC-TLS", "HC-CERT", "HC-MAP", "HC-HELLO", "HC-DISPATCH", "HC-MIGRATE",
         "HC-LIFECYCLE", "HC-GENERATION", "HC-EXCLUDE", "HC-PARITY"]
UUID_A = "0198f4c8-4a10-7b22-8b3c-1234567890ab"
UUID_B = "0198f4c8-7d40-7e55-8e6f-1234567890ab"
# Each check is scoped to the section owning the requirement. No whole-document
# keyword scan may satisfy a host-channel obligation from unrelated prose.
CLAUSES = {
    "HC-TLS": ["Both sides require TLS 1.3 exclusively", 'ALPN exactly <code>ax-host/1</code>',
               '<code>InsecureSkipVerify=false</code>', '<code>ClientAuth=tls.RequireAndVerifyClientCert</code>',
               'Session tickets, PSKs, session resumption, 0-RTT, TLS 1.2,',
               'at most 1 MiB of incoming handshake bytes per side'],
    "HC-CERT": ['Root self-signature, leaf signature, exact fields above',
                'Both EKUs are required by the profile',
                'current validity of both certificates MUST be checked at enrollment and handshake'],
    "HC-MAP": ['a leaf, leaf public key or root MUST NOT map to more than one host UUID',
               'an exact leaf/root/SPKI match against one currently admitted entry yields the verified UUID',
               'SAN alone and CA membership alone are insufficient'],
    "HC-HELLO": ['Every received hello host ID MUST equal the uniquely verified enrolled host UUID',
                 'that UUID MUST also equal the selected configured destination',
                 'No authentication, trust, configuration, error or transport key is added to hello'],
    "HC-DISPATCH": ['There is no RPC frame, error envelope, health read, version probe, or application dispatch before mutual authentication',
                    'server MUST finish verifying the client\'s Certificate, CertificateVerify and Finished before parsing hello',
                    'initiator MUST receive and validate that success before any other RPC operation'],
    "HC-MIGRATE": ['A Config-4 installation refuses the unflagged legacy server invocation before reading stdin',
                   'A Config-1/2/3 installation refuses the flagged host-channel invocation',
                   'No per-peer override exists', 'Replacement is atomic and crash durable'],
    "HC-LIFECYCLE": ['verified over an independent authenticated out-of-band channel',
                     'no more than 24 hours after that transition', 'There is no overlap extension',
                     'Revoked entries retain their public bytes permanently as reuse tombstones',
                     'Revocation is local'],
    "HC-GENERATION": ['including daemonless RPC children, MUST close them within one second',
                      'Every application dispatch checks current generation',
                      'Each mutation, including resumed transfer, retry, queued work and recovery, additionally rechecks these facts',
                      'The generation check and that boundary serialize with revocation/config commit',
                      'Missing/failed generation reads close the stream'],
    "HC-EXCLUDE": ['Credential/trust files, backups, private keys and authorization caches MUST NOT enter replication, snapshots, cloning, Session Directory, logs or exported diagnostic bundles'],
    "HC-PARITY": ['OpenSSH over a Tailscale network and native Tailscale SSH both carry the same ordered binary stdin/stdout stream',
                  'OpenSSH <code>authorized_keys</code>/forced-command behavior MUST NOT be assumed for it',
                  'A copied key authenticates until each verifier revokes it'],
}
PROFILE = {
    "key": "ECDSA-P256", "signature": "ECDSA-SHA256", "leaf_days": 90,
    "root_days": 366, "backdate_seconds": 300, "root_path_len": 0,
    "leaf_key_usage": ["digitalSignature"], "root_key_usage": ["keyCertSign"],
    "leaf_eku": ["clientAuth", "serverAuth"], "san": "HOST_UUID.host.ax.invalid",
    "online_ca": False, "tls_sends": "leaf_only", "pin": ["leaf_der", "root_der", "leaf_spki"],
}
VERSIONS = {"configuration": "4.0.0", "rpc": "5.0.0", "host_channel": "1.0.0", "trust_store": "1.0.0", "error": "1.3.0"}


def _closed(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def _exact(a, b):
    """Reject bool/int aliases and malformed nested facts, not just inequality."""
    return type(a) is type(b) and (set(a) == set(b) and all(_exact(a[k], b[k]) for k in b)
                                  if isinstance(b, dict) else
                                  len(a) == len(b) and all(_exact(x, y) for x, y in zip(a, b))
                                  if isinstance(b, list) else a == b)



def validate(root: pathlib.Path, spec: str) -> tuple[list[str], dict[str, int]]:
    errors = []
    def need(gate, condition, detail):
        if not condition:
            errors.append(f"host channel gate {gate}: {detail}")
    try:
        policy = read_policy(spec)
    except (ValueError, TypeError) as exc:
        need("policy", False, str(exc))
        return errors, {}
    # Full projection consistency is separate from executable predicate coverage.
    # A prose hash refresh cannot waive an inconsistent operational explanation.
    for name, start, end in [
        ('config', '### 6.6 Configuration 4.0.0', '## 7.'),
        ('channel', '### 11.10 Host Channel', '#### 11.10.5 Executable admission obligations'),
    ]:
        try:
            expected = (root / 'scripts/host_channel_templates' / (name + '.md')).read_text()
            # Templates end with one newline; the document separator is not
            # part of their content. Keep every other byte comparison exact.
            actual = spec[spec.index(start):spec.index(end)]
            expected += '\n'
            need('source-projection', actual == expected,
                 f'{name}: operational explanation differs from review-bound renderer; predicate/table and explanation must be reviewed together')
        except (OSError, ValueError) as exc:
            need('source-projection', False, f'{name}: missing/unreadable projection: {exc}')
    try:
        contributing = (root / 'CONTRIBUTING.md').read_text()
        publication = contributing[contributing.index('## Signing, release, and attribution'):contributing.index('## Repository layout')]
        publication += contributing[contributing.index('## Checklist for a spec PR'):]
        need('publication-authority', publication == (root / 'scripts/host_channel_templates/publication.md').read_text(),
             'active delivery workflow/checklist differs from authorized signed PR and parent-only release template')
    except (OSError, ValueError) as exc:
        need('publication-authority', False, f'unreadable publication authority: {exc}')
    tables = TABLE.findall(spec)
    need('source-projection', tables == [render_table(policy)], 'admission table disagrees with executable source policy')
    normalized = " ".join(spec.split())
    section_start = spec.find("### 11.10 Host Channel")
    section_end = spec.find("## 12.", section_start)
    config_start = spec.find("### 6.6 Configuration 4.0.0")
    config_end = spec.find("## 7.", config_start)
    section = " ".join(spec[section_start:section_end].split()) if section_start >= 0 and section_end > section_start else ""
    config = " ".join(spec[config_start:config_end].split()) if config_start >= 0 and config_end > config_start else ""
    gates = re.findall(r"^\| (HC-[A-Z]+) \|", spec, re.M)
    need("registry", gates == GATES, "exact ten normative gate families required")
    need("policy", list(policy["gates"]) == gates, "policy must cover exact source registry families")
    for gate, clauses in CLAUSES.items():
        for clause in clauses:
            need(gate, clause in (config if gate == "HC-MIGRATE" else section), f"missing normative clause: {clause}")
    # Exact standard profile table, independent of the synthetic fixture fields.
    for row in [
        '| Basic Constraints (critical) | CA=true, pathLen=0 | CA=false, no pathLen |',
        '| Key Usage (critical) | keyCertSign only | digitalSignature only |',
        '| Extended Key Usage (noncritical) | Absent | Exactly clientAuth and serverAuth |',
        '| Subject Alternative Name (noncritical) | Absent | Exactly one DNS name <code>HOST_UUID.host.ax.invalid</code>; no other SAN type |',
        '| Validity | notBefore=issuance time minus 300s; notAfter=notBefore plus 366 days | Same notBefore; notAfter=notBefore plus 90 days |',
    ]:
        need("HC-CERT", row in spec, "exact certificate profile row changed: " + row)
    registry = spec[spec.find('### 1.5 Normative'):spec.find('### 1.6 Common')]
    for title, urn, version in [("Configuration", "urn:ax:schema:config", "4.0.0"),
                                ("Mesh RPC", "urn:ax:protocol:rpc", "5.0.0"),
                                ("Host Channel", "urn:ax:transport:host-channel", "1.0.0"),
                                ("Host Trust Store", "urn:ax:schema:host-trust-store", "1.0.0")]:
        rows = [line for line in registry.splitlines() if line.startswith(f"| {title} |")]
        need("HC-MIGRATE", len(rows) == 1 and urn in rows[0] and f'<code>{version}</code>' in rows[0], f"registry missing {title} {version}")
    legacy_rows = []
    for line in registry.splitlines():
        if not line.startswith('| ') or line.startswith(('| Host Channel |', '| Host Trust Store |', '| Session selector |', '| Launch Plan request |')):
            continue
        line = line.replace(', <code>4.0.0</code> for mutual host authentication', '')
        line = line.replace(', <code>5.0.0</code> for authenticated host dispatch', '')
        line = line.replace(', <code>1.4.0</code> for selector-capable CLI failures', '')
        line = line.replace(', <code>5.0.0</code> for source-qualified selection and authoritative summaries', '')
        legacy_rows.append(line)
    need("HC-MIGRATE", hashlib.sha256('\n'.join(legacy_rows).encode()).hexdigest() == "739618336efef1857eeeb268b5bda1d43f80a7cb3ca8326d3ed9449dde05fe40", "historical v0.5.0 registry projection changed")
    need("HC-HELLO", 'with only the containing <code>protocol_version</code> and <code>contracts.rpc</code> changed to <code>5.0.0</code> and <code>["5.0.0"]</code>' in section, "RPC-5 map delta must preserve exact RPC-4 shape")
    need("HC-MIGRATE", 'Exact <code>4.0.0</code>' in config and 'exact <code>ssh_tls13</code>; no default or alternative' in config, "Config-4 transport selection mismatch")
    need("publication", "SPEC-PUB-HOST-001" in spec and "AC-HOST-001" in spec and "not an executed TLS deployment" in section, "source/product assurance boundary missing")
    path = root / 'fixtures/host_channel_conformance.json'
    try:
        data = json.loads(path.read_text(), object_pairs_hook=unique_pairs)
    except (OSError, ValueError) as exc:
        need("fixture", False, f"unreadable or malformed fixture: {exc}")
        return errors, {"host_channel_families": len(gates), "host_channel_covered": 0, "host_channel_vectors": 0}
    need("fixture", _closed(data, ['fixture', 'specification_version', 'evidence_kind', 'versions', 'certificate_profile', 'cases']), "closed fixture root mismatch")
    if not isinstance(data, dict):
        return errors, {"host_channel_families": len(gates), "host_channel_covered": 0, "host_channel_vectors": 0}
    need("fixture", data.get('fixture') == 'ax-host-channel-conformance-v1' and data.get('specification_version') == '0.6.0' and data.get('evidence_kind') == 'synthetic_contract_vectors_not_runtime', 'fixture discriminator/assurance mismatch')
    need("HC-MIGRATE", _exact(data.get('versions'), VERSIONS), "exact independent versions mismatch")
    need("HC-CERT", _exact(data.get('certificate_profile'), PROFILE), "certificate issuance profile mismatch")
    cases = data.get('cases')
    need("fixture", isinstance(cases, list), "cases must be an array")
    cases = cases if isinstance(cases, list) else []
    seen = set()
    coverage = {gate: set() for gate in gates}
    witnessed = set()
    witnessed_contexts = set()
    admitted_contexts = set()
    unknown_field_contexts = set()
    total_obligations = sum(len(rules) for rules in policy['gates'].values())
    for case in cases:
        if not _closed(case, ['id', 'gate', 'facts', 'expected']):
            need("fixture", False, "closed case shape mismatch")
            continue
        ident, gate, facts, expected = (case[k] for k in ['id', 'gate', 'facts', 'expected'])
        if not isinstance(ident, str) or ident in seen or gate not in GATES or expected not in ['admit', 'refuse']:
            need("fixture", False, "case ID/gate/expectation invalid or duplicate")
            continue
        seen.add(ident)
        try:
            observed = 'admit' if admits(policy, gate, facts) else 'refuse'
        except (TypeError, ValueError, KeyError):
            observed = 'refuse'
        need(gate, observed == expected, f"vector {ident}: expected {expected}, observed {observed}")
        if observed == expected and gate in coverage:
            coverage[gate].add(expected)
            context = (facts.get('entrypoint'), facts.get('carrier')) if isinstance(facts, dict) else (None, None)
            # Invalid context values are refusal inputs, not hashable ledger
            # keys. A malformed vector must never crash publication.
            if not all(isinstance(value, str) for value in context):
                context = (None, None)
            if expected == 'admit':
                admitted_contexts.add((gate, *context))
            failed = failures(policy, gate, facts)
            if expected == 'refuse' and isinstance(facts, dict):
                rules = policy['gates'][gate]
                extra = set(facts) - set(rules)
                if len(extra) == 1 and admits(policy, gate, {k: v for k, v in facts.items() if k in rules}):
                    unknown_field_contexts.add((gate, *context))
            if expected == 'refuse' and len(failed) == 1 and 'closed-shape' not in failed:
                field = next(iter(failed))
                witnessed.add((gate, field))
                witnessed_contexts.add((gate, field, *context))
    covered = sum(kinds == {'admit', 'refuse'} for kinds in coverage.values())
    need("coverage", covered == len(gates) == 10, f"positive/negative families {covered}/{len(gates)}")
    # The denominator comes from the normative policy, not a Python fact table.
    # A malformed/missing-field vector does not count as an isolated predicate witness.
    missing = {(gate, field) for gate, rules in policy['gates'].items() for field in rules} - witnessed
    need('obligation-coverage', not missing, 'no isolated negative witness: ' + ', '.join(f'{g}.{f}' for g, f in sorted(missing)))
    expected_contexts = set()
    expected_closed_contexts = set()
    for gate, rules in policy['gates'].items():
        try:
            contexts = [(entry, carrier) for entry in rules['entrypoint']['in'] for carrier in rules['carrier']['in']]
        except (KeyError, TypeError):
            need('context-coverage', False, f'{gate}: closed context domains required')
            continue
        for entry, carrier in contexts:
            expected_closed_contexts.add((gate, entry, carrier))
            need('context-coverage', (gate, entry, carrier) in admitted_contexts,
                 f'{gate}: no positive witness at {entry}/{carrier}')
            for field in rules:
                if field not in {'entrypoint', 'carrier'}:
                    expected_contexts.add((gate, field, entry, carrier))
    missing_contexts = expected_contexts - witnessed_contexts
    need('context-coverage', not missing_contexts,
         'no isolated contextual refusal witness: ' + ', '.join('.'.join(item) for item in sorted(missing_contexts)))
    missing_closed = expected_closed_contexts - unknown_field_contexts
    need('closed-coverage', not missing_closed,
         'no isolated unknown-field refusal witness: ' + ', '.join('.'.join(item) for item in sorted(missing_closed)))
    for gate, rules in policy['gates'].items():
        positives = [c['facts'] for c in cases if isinstance(c, dict) and c.get('gate') == gate and c.get('expected') == 'admit' and admits(policy, gate, c.get('facts'))]
        if not positives:
            continue
        base = positives[0]
        for field in rules:
            need(gate, any(c.get('expected') == 'refuse' and c.get('gate') == gate
                           and c.get('facts') == {k: v for k, v in base.items() if k != field}
                           for c in cases if isinstance(c, dict)), f'missing absent-evidence vector for {field}')
    return errors, {"host_channel_families": len(gates), "host_channel_covered": covered,
                    "host_channel_vectors": len(cases), "host_obligations": total_obligations,
                    "host_obligations_witnessed": len(witnessed),
                    "host_contexts": len(expected_contexts),
                    "host_contexts_witnessed": len(expected_contexts & witnessed_contexts),
                    "host_closed_contexts": len(expected_closed_contexts),
                    "host_closed_contexts_witnessed": len(expected_closed_contexts & unknown_field_contexts)}
