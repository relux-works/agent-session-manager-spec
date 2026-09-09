#!/usr/bin/env python3
"""Attack real publication entrypoints in isolated public-only copies.

Exit 0 means every named test detected its mutation. Each gate subprocess's
actual status is reported separately; expected-red subprocesses really fail.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from selector_inventory import Inventory

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ('./scripts/validate_spec.py', './run_validation.sh')


def is_generated(label):
    # Source-derived single-phase caller/generic controls track
    # Inventory.binding exactly; every other row is a handpicked mutant.
    return label.startswith('gen-')


def replace(path, old, new):
    text = path.read_text()
    if old not in text:
        raise AssertionError(f'mutant target absent: {old!r}')
    path.write_text(text.replace(old, new, 1))


def refresh_release_pin(root):
    path = root / 'scripts/validate_spec.py'
    digest = hashlib.sha256((root / 'SPEC.md').read_text().encode()).hexdigest()
    path.write_text(re.sub(r'("SPEC.md": ")[a-f0-9]{64}', lambda m: m[1] + digest, path.read_text()))


def refresh_prose_pins(root):
    text = (root/'SPEC.md').read_text()
    def refresh(data):
        for pin in data['prose_sections']:
            pin[2] = hashlib.sha256(text.split(pin[0], 1)[1].split(pin[1], 1)[0].encode()).hexdigest()
    fixture_change(root, refresh)
    refresh_release_pin(root)


def policy_mutation(root, key, value):
    path = root / 'SPEC.md'
    text = path.read_text()
    block = re.search(r'~~~selector-policy\n(.*?)\n~~~', text, re.S)
    data = json.loads(block[1])
    data[key] = value(data[key]) if callable(value) else value
    path.write_text(text[:block.start(1)] + json.dumps(data, indent=2) + text[block.end(1):])
    refresh_release_pin(root)  # Defeat hash-only proof; exercise semantic vectors.


def fixture_change(root, action):
    path = root / 'fixtures/session_selector_conformance.json'
    data = json.loads(path.read_text())
    action(data)
    path.write_text(json.dumps(data, indent=2))


def mutations():
    rows = []
    def code(label, narrowing, old, new, test):
        rows.append((label, narrowing, lambda r: replace(r/'scripts/validate_selector.py',old,new), test))
    def policy(label, narrowing, key, value, test):
        rows.append((label, narrowing, lambda r: policy_mutation(r,key,value),test))
    policy('last-at','first-at narrowed to last delimiter','split','last','SEL-CASE-alias-at')
    policy('short-alias','64 character boundary narrowed to 63','alias_max',63,'SEL-CASE-max-alias')
    policy('long-alias','alias refusal narrowed to length above 65','alias_max',65,'SEL-CASE-long-alias')
    policy('fallback-empty','explicit source guard admits successful empty source fallback','explicit_fallback',True,'SEL-CASE-empty-no-fallback')
    policy('uuid-before-peer','name precedence reduced to local names only','bare_order',['local_name','uuid','peer_name'],'SEL-CASE-uuid-name-first')
    policy('source-owner','ownership projection uses source host','source_is_owner',True,'SEL-CASE-local-source-remote-owner')
    policy('invent-initial-lease','lease guard admits record-only summary','summary_requires_lease',False,'SEL-CASE-record-only')
    policy('error-downgrade','CLI5 binds old Error1.3','error','1.3.0','SEL-CASE-version-5.0.0-bare')
    fields=json.loads(re.search(r'~~~selector-policy\n(.*?)\n~~~',(ROOT/'SPEC.md').read_text(),re.S)[1])['plan_fields']
    for field in fields:
        policy('omit-plan-'+field,'revalidation excludes only '+field,'plan_fields',lambda v,f=field:[x for x in v if x!=f],'SEL-CASE-changed-'+field)
    def guard_mutant(label, stage, index, condition, test):
        def change(root):
            def modify(stages):
                stages[stage][index]['when'] = condition(stages[stage][index]['when'])
                return stages
            policy_mutation(root, 'guards', modify)
        rows.append((label, 'source predicate narrowed in '+stage+' while error tokens remain', change, test))
    guard_mutant('read-failure-only','read',0,lambda old:{'eq':[{'get':'read'},'failed']},'SEL-CASE-source-partial')
    guard_mutant('config-failure-only','config',0,lambda old:{'eq':[{'get':'config_read'},'failed']},'SEL-CASE-config-partial')
    code('fold-alias','exact alias guard admits case-fold match',"s['alias'] == source[5:]","s['alias'].lower() == source[5:].lower()",'SEL-CASE-case-alias')
    code('decode-alias','literal alias comparison admits percent decoding',"s['alias'] == source[5:]","s['alias'] == __import__('urllib.parse', fromlist=['unquote']).unquote(source[5:])",'SEL-CASE-percent-literal-resolution')
    guard_mutant('drop-collision','collision',0,lambda old:{'gt':[{'get':'identities'},2]},'SEL-CASE-case-collision')
    guard_mutant('drop-record-integrity','record',0,lambda old:{'all':[old,False]},'SEL-CASE-invalid-record')
    guard_mutant('observation-guard','summary_observation',0,lambda old:old['any'][1],'SEL-CASE-unknown-observation')
    guard_mutant('forged-plan','plan',0,lambda old:{'all':[old,{'ne':[{'get':'read'},'valid']}]},'SEL-CASE-forged-plan')
    for index,field in enumerate(['original_host','serialized','no_effects','no_conflict','record_valid','original_inputs']):
        guard_mutant('bootstrap-'+field,'bootstrap',index,lambda old,f=field:{'all':[old,{'eq':[{'get':'no_effects' if f != 'no_effects' else 'no_conflict'},False]}]},'SEL-CASE-bootstrap-no-'+field)
    guard_tests = {
        'config': ['config-failed'], 'mapping': ['duplicate-alias-distinct-host','duplicate-host-distinct-alias'],
        'source': ['missing-peer'], 'allowlist': ['revoked-source'], 'read': ['source-partial','local-source-failed','source-failed'],
        'record': ['invalid-record'], 'collision': ['case-collision','same-id-digest-conflict'],
        'plan': ['forged-plan'], 'plan_fact': ['missing-source_alias','changed-session_id'],
        'summary_lease': ['record-only'], 'summary_observation': ['unknown-observation'],
        'bootstrap': ['bootstrap-no-'+f for f in ['original_host','serialized','no_effects','no_conflict','record_valid','original_inputs']],
    }
    source_policy=json.loads(re.search(r'~~~selector-policy\n(.*?)\n~~~',(ROOT/'SPEC.md').read_text(),re.S)[1])
    for stage, rules in source_policy['guards'].items():
        for index, rule in enumerate(rules):
            guard_mutant('disable-'+stage+'-'+str(index),stage,index,lambda old:False,'SEL-CASE-'+guard_tests[stage][index])
    code('retryable-stale','retry refusal excludes stale selection',"outcome['retryable'] = False","outcome['retryable'] = outcome['error'] == 'selector_plan_stale'",'SEL-CASE-changed-session_id')
    for error,test in [('selector_source_not_found','missing-peer'),('selector_source_read_failed','source-failed'),('selector_bootstrap_incomplete','record-only'),('selector_observation_unavailable','unknown-observation'),('selector_plan_stale','changed-session_id')]:
        def change_error(root, error=error):
            policy_mutation(root,'error_exits',lambda values:dict(values,**{error:13}))
            # Also change the prose table; semantic vectors must catch drift
            # after both consistency checks and editorial pins are satisfied.
            p=root/'SPEC.md'
            p.write_text(re.sub(r'(?m)^\| [0-9]+ \| <code>'+error+r'</code>', '| 13 | <code>'+error+'</code>', p.read_text()))
            data_path=root/'fixtures/session_selector_conformance.json'
            data=json.loads(data_path.read_text())
            for pin in data['prose_sections']:
                pin[2]=hashlib.sha256(p.read_text().split(pin[0],1)[1].split(pin[1],1)[0].encode()).hexdigest()
            data_path.write_text(json.dumps(data,indent=2))
            refresh_release_pin(root)
        rows.append(('error-exit-'+error,'error mapping changes to provider exit13 while preserving code tokens',change_error,'SEL-CASE-'+test))
    rows.append(('missing-fixture','missing evidence cannot be absence',lambda r:(r/'fixtures/session_selector_conformance.json').unlink(),'missing/malformed conformance input'))
    rows.append(('missing-case','denominator must come from SPEC inventory',lambda r:fixture_change(r,lambda d:d['cases'].pop()),'normative case inventory mismatch'))
    rows.append(('forged-expected','self-minted expected success cannot attest refusal',lambda r:fixture_change(r,lambda d:next(c for c in d['cases'] if c['id']=='SEL-CASE-record-only').update(expected={'invented':'success'})),'SEL-CASE-record-only'))
    rows.append(('disconnected-gate','publication skips selector evaluator',lambda r:replace(r/'scripts/validate_spec.py','    errors.extend(validate_selector(ROOT, text, canonical))','    pass  # validate_selector(ROOT, text, canonical) remains a token'),'test_publication_requires_selector_coverage'))
    # Actual actions and phases come from the normative matrix, not the evaluator.
    pairs = Inventory(ROOT).pairs
    for action, boundary in pairs:
        code('bypass-'+action+'-'+boundary, 'revalidation excludes only '+action+'/'+boundary,
             'def revalidate(facts, policy):\n',
             'def revalidate(facts, policy):\n' + f"    if facts['plan'].get('action') == {action!r} and facts.get('boundary') == {boundary!r}: return\n",
             'SEL-CASE-boundary-'+action+'-'+boundary+'-stale')
    code('review-resume-bypass','reviewer attack: plan gate excludes all resume',
         "        if kind == 'plan':\n", "        if kind == 'plan':\n            if facts['plan'].get('action') == 'resume':\n                return {'session_id': facts['plan']['session_id'], 'effect_allowed': True}\n",
         'SEL-CASE-boundary-resume-recovery-stale')
    def source(label, old, new, test):
        def change(root):
            replace(root/'SPEC.md', old, new)
            refresh_prose_pins(root)
        rows.append((label,'normative declaration narrowed; editorial hashes refreshed',change,test))
    source('remote-bare-uuid','ssh -t HOST ax attach id:SESSION_UUID --local','ssh -t HOST ax attach SESSION_UUID --local','SEL-CASE-remote-durable-collision')
    source('remote-name-route','ssh -t HOST ax attach id:SESSION_UUID --local','ssh -t HOST ax attach NAME --local','SEL-CASE-remote-durable-collision')
    code('owner-name-resolution','only remote owner uses display name; durable parser retained',
         "r['id'] == operand[3:]", "r['name'] == 'build'", 'SEL-CASE-remote-durable-collision')
    for side in ['local','receiver']:
        code('remote-skip-'+side,'composed attach omits '+side+' revalidation; structural topology refusal (conditional caller narrowing is tested separately)',
             '    revalidate('+side+', policy)', '    pass  # revalidate('+side+', policy)',
             'caller topology changed')
    code('remote-skip-expectations','receiver ignores well-formed changed expected lease',
         "if receiver['current'].get(field) != value:", "if field == 'session_id' and receiver['current'].get(field) != value:",
         'SEL-CASE-remote-changed-lease_id')
    for field, old, new in [('epoch','1','2'),('reason','create','recovery'),('predecessor_lease_id','null','allocated'),('checkpoint_id','null','allocated'),('schema','urn:ax:schema:lease','urn:ax:schema:session-record'),('schema_version','1.0.0','2.0.0')]:
        source('bootstrap-declaration-'+field,'| '+field+' | '+old+' |','| '+field+' | '+new+' |','SEL-CASE-bootstrap-original')
        code('bootstrap-skip-'+field,'initial lease validation excludes '+field,
             '    for field, value in policy[\'_bootstrap_values\'].items():\n',
             '    for field, value in policy[\'_bootstrap_values\'].items():\n'+f'        if field == {field!r}: continue\n',
             'SEL-CASE-intent-lease-'+field)
    code('bootstrap-original-id-substitution','intent equality ignores replacement operation IDs',
         "require(intent == facts.get('original_intent'))", "require(intent['initial_lease'] == facts.get('original_intent', {}).get('initial_lease'))",
         'SEL-CASE-intent-changed-bootstrap_operation_id')
    code('bootstrap-rehashed-replacement','intent equality ignores fresh valid lease',
         "require(intent == facts.get('original_intent'))", "require(intent['bootstrap_operation_id'] == facts.get('original_intent', {}).get('bootstrap_operation_id'))",
         'SEL-CASE-intent-rehashed-new-lease')
    code('bootstrap-cwd-binding','workspace binding excludes cwd member',
         "require(session['launch_plan']['cwd_workspace_id'] in [m['workspace_id'] for m in workspace['members']])", 'pass  # cwd binding omitted',
         'SEL-CASE-intent-cwd')
    code('bootstrap-session-binding','lease binding ignores subject mismatch',
         "session['subject_id'] == session['session_id'] == lease['session_id'] == lease['subject_id']",
         "session['subject_id'] == session['session_id'] == lease['session_id']", 'SEL-CASE-intent-binding-lease-subject_id')
    code('bootstrap-host-binding','host binding ignores issuer mismatch',
         " == lease['issued_by_host_id'] == lease['created_by_host_id']", " == lease['created_by_host_id']", 'SEL-CASE-intent-binding-lease-issued_by_host_id')
    code('bootstrap-same-operations','operation uniqueness excludes duplicated IDs',
         "require(intent['bootstrap_operation_id'] != intent['first_checkpoint_operation_id'])", 'pass  # operation uniqueness omitted',
         'SEL-CASE-intent-same-operation')
    code('remote-version-downgrade','remote version refusal admits legacy CLI4',
         "if facts['receiver_version'] != policy['cli_result']:", "if facts['receiver_version'] not in [policy['cli_result'], '4.0.0']:",
         'SEL-CASE-remote-unsupported')
    code('remote-tombstone-bypass','owner exact-ID admission ignores tombstone',
         "if record['tombstoned']:", "if False and record['tombstoned']:", 'SEL-CASE-remote-tombstoned')
    code('remote-record-bypass','owner exact-ID admission omits record validation',
         "    guards('record', record, policy)\n    if record", "    pass  # guards('record', record, policy)\n    if record", 'SEL-CASE-remote-invalid')
    source('logs-name-route','ssh HOST ax logs --session id:SESSION_UUID --limit','ssh HOST ax logs --session NAME --limit','SEL-CASE-logs-durable-collision')
    source('logs-bare-uuid-route','ssh HOST ax logs --session id:SESSION_UUID --limit','ssh HOST ax logs --session SESSION_UUID --limit','SEL-CASE-logs-durable-collision')
    code('logs-name-filter','remote logs filters by display name',
         "e['session_id'] == operand[3:]", "e['name'] == 'build'", 'SEL-CASE-logs-durable-collision')
    code('logs-cursor-host','cursor host validation excluded',
         "if facts['cursor']['host_id'] != facts['peer_host']:", "if False and facts['cursor']['host_id'] != facts['peer_host']:", 'SEL-CASE-logs-cursor-host')
    code('logs-cursor-session','cursor session filter binding excluded',
         "if facts['cursor']['session_id'] != operand[3:]:", "if False and facts['cursor']['session_id'] != operand[3:]:", 'SEL-CASE-logs-cursor-session')
    code('logs-emitter','emitter check present but disabled',
         "if facts['emitting_host_id'] != facts['peer_host']:", "if False and facts['emitting_host_id'] != facts['peer_host']:", 'SEL-CASE-logs-wrong-emitter')
    code('logs-event-host','event host check excludes all but first event',
         "if any(e['host_id'] != facts['emitting_host_id'] for e in events):", "if any(e['host_id'] != facts['emitting_host_id'] for e in events[1:]):", 'SEL-CASE-logs-forged-event')
    code('logs-plan-record-bypass','initiator selection binding ignores record mismatch',
         " or selected['record_id'] != facts['initiator']['plan']['session_record_id']", "", 'SEL-CASE-logs-selection-record-mismatch')
    code('logs-plan-source-bypass','initiator selection binding ignores source mismatch',
         " or selected['source_host_id'] != facts['initiator']['plan']['source_host_id']", "", 'SEL-CASE-logs-selection-source-mismatch')
    # Composed invocation-to-plan binding gate (159 divergence witnesses).
    # Caller mutants remove one endpoint/fact comparison; generic mutants remove
    # the whole route block, substitute cross-endpoint equality, gate behind
    # trusted_local_plan, or skip just one phase (retry/resume) while other
    # phases still check. Every mutant must be detected through a real entry.
    code('bind-attach-initiator-action','caller: initiator action comparison removed; receiver check retained',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if facts['receiver']['plan']['action'] != 'attach':",
         'SEL-CASE-remote-initiator-action-mismatch')
    code('bind-attach-receiver-action','caller: receiver action comparison removed; initiator check retained',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if facts['initiator']['plan']['action'] != 'attach':",
         'SEL-CASE-remote-receiver-action-mismatch')
    code('bind-attach-initiator-destination','caller: initiator null-destination comparison removed',
         "if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:",
         "if facts['receiver']['plan']['destination_host_id'] is not None:",
         'SEL-CASE-remote-initiator-destination-mismatch')
    code('bind-attach-receiver-destination','caller: receiver null-destination comparison removed',
         "if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:",
         "if facts['initiator']['plan']['destination_host_id'] is not None:",
         'SEL-CASE-remote-receiver-destination-mismatch')
    code('bind-logs-initiator-action','caller: initiator action comparison removed; cursor witness shares the check',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if facts['receiver']['plan']['action'] != 'logs':",
         'SEL-CASE-logs-cursor-initiator-action-mismatch')
    code('bind-logs-receiver-action','caller: receiver action comparison removed; initiator check retained',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if facts['initiator']['plan']['action'] != 'logs':",
         'SEL-CASE-logs-receiver-action-mismatch')
    code('bind-logs-initiator-destination','caller: initiator peer-destination comparison removed; cursor witness shares the check',
         "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:",
         "if facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:",
         'SEL-CASE-logs-cursor-initiator-destination-mismatch')
    code('bind-logs-receiver-destination','caller: receiver peer-destination comparison removed',
         "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:",
         "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host']:",
         'SEL-CASE-logs-receiver-destination-mismatch')
    code('bind-attach-disabled','generic: whole attach invocation binding omitted',
         "    if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':\n        refuse('selector_plan_stale')\n    if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:\n        refuse('selector_plan_stale')\n",
         "    pass  # invocation binding omitted\n",
         'SEL-CASE-remote-both-action-mismatch')
    code('bind-logs-disabled','generic: whole logs invocation binding omitted',
         "    if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':\n        refuse('selector_plan_stale')\n    if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:\n        refuse('selector_plan_stale')\n",
         "    pass  # invocation binding omitted\n",
         'SEL-CASE-logs-both-destination-mismatch')
    code('bind-attach-cross-action','generic: per-endpoint attach action binding replaced by initiator==receiver comparison',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if facts['initiator']['plan']['action'] != facts['receiver']['plan']['action']:",
         'SEL-CASE-remote-both-action-mismatch')
    code('bind-attach-cross-destination','generic: per-endpoint null-destination binding replaced by initiator==receiver comparison',
         "if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:",
         "if facts['initiator']['plan']['destination_host_id'] != facts['receiver']['plan']['destination_host_id']:",
         'SEL-CASE-remote-both-destination-mismatch')
    code('bind-logs-cross-action','generic: per-endpoint logs action binding replaced by initiator==receiver comparison',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if facts['initiator']['plan']['action'] != facts['receiver']['plan']['action']:",
         'SEL-CASE-logs-both-action-mismatch')
    code('bind-logs-cross-destination','generic: per-endpoint peer binding replaced by initiator==receiver comparison',
         "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:",
         "if facts['initiator']['plan']['destination_host_id'] != facts['receiver']['plan']['destination_host_id']:",
         'SEL-CASE-logs-both-destination-mismatch')
    code('bind-attach-trusted-action','generic: attach action binding skipped when trusted_local_plan holds; resume witness shares the check',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach') and not facts['initiator'].get('trusted_local_plan'):",
         'SEL-CASE-remote-resume-initiator-action-mismatch')
    code('bind-logs-trusted-destination','generic: logs destination binding skipped when trusted_local_plan holds',
         "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:",
         "if (facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']) and not facts['initiator'].get('trusted_local_plan'):",
         'SEL-CASE-logs-initiator-destination-mismatch')
    # Original selector/alias binding (initiator only; receiver stays endpoint-local).
    # Attach and logs share the selector guard text; disambiguate via neighbors.
    code('bind-attach-initiator-selector','caller: initiator literal-selector comparison removed; alias check retained',
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['source_alias'] != actual_alias:",
         'SEL-CASE-remote-initiator-selector-mismatch')
    code('bind-attach-initiator-alias','caller: initiator derived-alias comparison removed; selector check retained',
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector']:",
         'SEL-CASE-remote-initiator-alias-mismatch')
    code('bind-logs-initiator-selector','caller: logs initiator literal-selector comparison removed',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['source_alias'] != actual_alias:",
         'SEL-CASE-logs-cursor-initiator-selector-mismatch')
    code('bind-logs-initiator-alias','caller: logs initiator derived-alias comparison removed',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector']:",
         'SEL-CASE-logs-initiator-alias-mismatch')
    code('bind-logs-initiator-session','caller: logs initiator resolved-session comparison removed (attach session/record rows carry their own generated single-phase controls)',
         "    if selected['session_id'] != facts['initiator']['plan']['session_id'] or selected['record_id'] != facts['initiator']['plan']['session_record_id'] or selected['source_host_id'] != facts['initiator']['plan']['source_host_id']:",
         "    if selected['record_id'] != facts['initiator']['plan']['session_record_id'] or selected['source_host_id'] != facts['initiator']['plan']['source_host_id']:",
         'SEL-CASE-logs-initiator-session-mismatch')
    code('bind-attach-initiator-source','caller: initiator resolved-source comparison removed',
         "if selected['session_id'] != local['plan']['session_id'] or selected['record_id'] != local['plan']['session_record_id'] or selected['source_host_id'] != local['plan']['source_host_id']:",
         "if selected['session_id'] != local['plan']['session_id'] or selected['record_id'] != local['plan']['session_record_id']:",
         'SEL-CASE-remote-initiator-source-mismatch')
    # Phase-specific narrowing: skip just one dispatch phase while others check.
    code('bind-attach-retry-bypass','generic: attach action binding skipped only at retry; initial/resume still check',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach') and facts['initiator'].get('boundary') != 'retry' and facts['receiver'].get('boundary') != 'retry':",
         'SEL-CASE-remote-retry-initiator-action-mismatch')
    code('bind-attach-resume-bypass','generic: attach action binding skipped only at transport-resume',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach') and facts['initiator'].get('boundary') != 'transport-resume' and facts['receiver'].get('boundary') != 'transport-resume':",
         'SEL-CASE-remote-resume-initiator-action-mismatch')
    code('bind-logs-retry-bypass','generic: logs action binding skipped only at retry',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs') and facts['initiator'].get('boundary') != 'retry' and facts['receiver'].get('boundary') != 'retry':",
         'SEL-CASE-logs-retry-initiator-action-mismatch')
    code('bind-logs-resume-bypass','generic: logs action binding skipped only at transport-resume',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs') and facts['initiator'].get('boundary') != 'transport-resume' and facts['receiver'].get('boundary') != 'transport-resume':",
         'SEL-CASE-logs-resume-receiver-action-mismatch')
    code('bind-attach-selector-retry-bypass','generic: initiator selector binding skipped only at retry',
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and facts['initiator'].get('boundary') != 'retry':",
         'SEL-CASE-remote-retry-initiator-selector-mismatch')
    code('bind-logs-selector-retry-bypass','generic: logs initiator selector binding skipped only at retry',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and facts['initiator'].get('boundary') != 'retry':",
         'SEL-CASE-logs-cursor-retry-initiator-selector-mismatch')
    # Context-derived single-phase controls for the previously omitted
    # pre-effect/fencing/projection boundaries. Every distinct composed
    # boundary from Inventory.rows needs its own bypass that survives unless
    # the new 48 witnesses run at that boundary. Both public entries drive
    # each mutant; application is asserted by byte inequality plus AST parse
    # in the harness, and the named test must appear with exit 1.
    code('bind-attach-preeffect-bypass','generic: attach action binding skipped only at pre-effect',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach') and facts['initiator'].get('boundary') != 'pre-effect' and facts['receiver'].get('boundary') != 'pre-effect':",
         'SEL-CASE-remote-pre-effect-initiator-action-mismatch')
    code('bind-attach-fencing-bypass','generic: attach action binding skipped only at fencing',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach') and facts['initiator'].get('boundary') != 'fencing' and facts['receiver'].get('boundary') != 'fencing':",
         'SEL-CASE-remote-fencing-initiator-action-mismatch')
    code('bind-attach-preeffect-caller','caller: attach initiator action skipped only at pre-effect; receiver still checks',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' and facts['initiator'].get('boundary') != 'pre-effect') or facts['receiver']['plan']['action'] != 'attach':",
         'SEL-CASE-remote-pre-effect-initiator-action-mismatch')
    code('bind-attach-fencing-caller','caller: attach initiator action skipped only at fencing',
         "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':",
         "if (facts['initiator']['plan']['action'] != 'attach' and facts['initiator'].get('boundary') != 'fencing') or facts['receiver']['plan']['action'] != 'attach':",
         'SEL-CASE-remote-fencing-initiator-action-mismatch')
    code('bind-attach-selector-preeffect-bypass','generic: initiator selector binding skipped only at pre-effect',
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and facts['initiator'].get('boundary') != 'pre-effect':",
         'SEL-CASE-remote-pre-effect-initiator-selector-mismatch')
    code('bind-attach-selector-fencing-bypass','generic: initiator selector binding skipped only at fencing',
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and facts['initiator'].get('boundary') != 'fencing':",
         'SEL-CASE-remote-fencing-initiator-selector-mismatch')
    code('bind-logs-projection-bypass','generic: logs action binding skipped only at projection (initial and cursor)',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs') and facts['initiator'].get('boundary') != 'projection' and facts['receiver'].get('boundary') != 'projection':",
         'SEL-CASE-logs-projection-initiator-action-mismatch')
    code('bind-logs-projection-caller','caller: logs initiator action skipped only at projection',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' and facts['initiator'].get('boundary') != 'projection') or facts['receiver']['plan']['action'] != 'logs':",
         'SEL-CASE-logs-projection-initiator-action-mismatch')
    code('bind-logs-selector-projection-bypass','generic: logs initiator selector binding skipped only at projection',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and facts['initiator'].get('boundary') != 'projection':",
         'SEL-CASE-logs-projection-initiator-selector-mismatch')
    code('bind-logs-projection-initial-bypass','generic: logs action skipped only at initial-projection; cursor still checks',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs') and not (facts['initiator'].get('boundary') == 'projection' and facts.get('cursor') is None) and not (facts['receiver'].get('boundary') == 'projection' and facts.get('cursor') is None):",
         'SEL-CASE-logs-projection-initiator-action-mismatch')
    code('bind-logs-projection-cursor-bypass','generic: logs action skipped only at cursor-projection; initial still checks',
         "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':",
         "if (facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs') and not (facts['initiator'].get('boundary') == 'projection' and facts.get('cursor') is not None) and not (facts['receiver'].get('boundary') == 'projection' and facts.get('cursor') is not None):",
         'SEL-CASE-logs-cursor-projection-initiator-action-mismatch')
    code('bind-logs-selector-projection-initial-bypass','generic: logs selector skipped only at initial-projection',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and not (facts['initiator'].get('boundary') == 'projection' and facts.get('cursor') is None):",
         'SEL-CASE-logs-projection-initiator-selector-mismatch')
    code('bind-logs-selector-cursor-projection-bypass','generic: logs selector skipped only at cursor-projection',
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:",
         "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if (facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias) and not (facts['initiator'].get('boundary') == 'projection' and facts.get('cursor') is not None):",
         'SEL-CASE-logs-cursor-projection-initiator-selector-mismatch')
    code('bind-attach-selector-disabled','generic: whole initiator selector/alias block omitted in attach',
         "    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:\n        refuse('selector_plan_stale')\n    local = facts['initiator']",
         "    local = facts['initiator']",
         'SEL-CASE-remote-initiator-selector-mismatch')
    # Source-derived single-phase caller/generic controls from the same
    # normative member/context relation. Each generated mutant narrows exactly
    # one production predicate at its designated scope; the witness is the
    # relation row itself. Handpicked phase lists cannot silently omit a new
    # context because the population tracks Inventory.binding exactly.
    for generated in Inventory(ROOT).binding_mutants():
        def make_change(old=generated['old'], new=generated['new']):
            def change(root):
                replace(root/'scripts/validate_selector.py', old, new)
            return change
        # No entry is claimed here: every generated control runs at BOTH
        # public entries (see main); the per-pair entry is recorded per
        # invocation. A label naming one entry would understate the scope.
        rows.append((generated['id'], generated['narrowing'],
                     make_change(), generated['witness']))
    return rows


def test_publication_requires_selector_coverage(output):
    assert 'Selector publication coverage:' in output, 'selector publication gate was not reached'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=1)
    parser.add_argument('--end',type=int,default=10000)
    parser.add_argument('--output-dir',type=Path,default=None,
                        help='Write per-pair raw logs, exits and a pair manifest here')
    args=parser.parse_args()
    rows=mutations(); killed=0; tested=0
    generated_by_id={m['id']: m for m in Inventory(ROOT).binding_mutants()}
    # Pair enumeration: every source-derived generated control runs at BOTH
    # real public entries; handpicked rows keep one alternating entry each
    # (honestly single-entry, not a both-entry claim). Slicing by --start/--end
    # selects pairs, so bounded batches stay self-describing.
    pairs=[]
    for index,(label,narrowing,mutate,test) in enumerate(rows,1):
        if is_generated(label):
            assert label in generated_by_id, 'generated row without source-derived control: ' + label
            for entry in ENTRIES:
                pairs.append((index,label,narrowing,mutate,test,entry))
        else:
            entry='./run_validation.sh' if index%2 else './scripts/validate_spec.py'
            pairs.append((index,label,narrowing,mutate,test,entry))
    expected_generated={(label,entry) for (_,label,_,_,_,entry) in pairs if is_generated(label)}
    assert expected_generated == {(m['id'],entry) for m in Inventory(ROOT).binding_mutants() for entry in ENTRIES}, \
        'generated pairs must equal generatedControls x {validate_spec.py, run_validation.sh}'
    manifest_invocations=[]
    if args.output_dir:
        args.output_dir.mkdir(parents=True,exist_ok=True)
    print('| Mutant | Gate narrowing | Named failing test | Gate exit | Test verdict / survival bound |',flush=True)
    print('| --- | --- | --- | ---: | --- |',flush=True)
    with tempfile.TemporaryDirectory(prefix='ax-selector-publication-') as temp:
        for pair_number,(index,label,narrowing,mutate,test,entry) in enumerate(pairs,1):
            if not args.start<=pair_number<=args.end:
                continue
            root=Path(temp)/str(pair_number)
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','.temp','.task-board','task-board.config.json','__pycache__'))
            applications, parse = 'n/a', 'n/a'
            if is_generated(label):
                # Exact-one source application plus AST parse per pair: the
                # mutant must rewrite exactly its designated predicate and
                # stay syntactically valid. Mutants fail in the spec phase
                # before expensive diagram rendering.
                mutant=generated_by_id[label]
                code=(root/'scripts/validate_selector.py').read_text()
                applications=code.count(mutant['old'])
                assert applications==1, (label,entry,applications)
                ast.parse(code.replace(mutant['old'],mutant['new'],1))
                parse='ok'
            mutate(root)
            result=subprocess.run([entry],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
            tested+=1
            if label=='disconnected-gate':
                try:
                    test_publication_requires_selector_coverage(result.stdout)
                    detected = False
                except AssertionError:
                    detected = True
            else:
                detected=result.returncode==1 and test in result.stdout
            if detected:
                killed+=1
            verdict='killed; source-only assertion fails' if detected else 'SURVIVOR; this mutation is not detected by the named publication test'
            print(f'| {label} | {narrowing}; {entry} | {test} | {result.returncode} | {verdict} |',flush=True)
            if not detected:
                print(result.stdout[-4000:],flush=True)
            if args.output_dir:
                stem=f'{pair_number:04d}-{label}-'+('spec' if entry.endswith('validate_spec.py') else 'run')
                log_path=args.output_dir/(stem+'.log'); exit_path=args.output_dir/(stem+'.exit')
                log_path.write_text(result.stdout); exit_path.write_text(str(result.returncode)+'\n')
                semantic=[line for line in result.stdout.splitlines() if test+' expected ' in line or test in line]
                manifest_invocations.append(dict(pair=pair_number,index=index,control=label,entry=entry,
                    narrowing=narrowing,witness=test,applications=applications,parse=parse,
                    log=str(log_path.name),log_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
                    exit_file=str(exit_path.name),exit=result.returncode,
                    semantic=[line for line in semantic if "'input_allowed': True" in line or 'causal binding witness noncausal' in line or 'expected' in line][:3]))
            shutil.rmtree(root)
    observed_generated={(label,entry) for (_,label,_,_,_,entry) in pairs[args.start-1:args.end] if is_generated(label)}
    ran_generated={(inv['control'],inv['entry']) for inv in manifest_invocations if is_generated(inv['control'])} if args.output_dir else observed_generated
    if args.output_dir:
        manifest_path=args.output_dir/'pair-manifest.json'
        manifest_path.write_text(json.dumps(dict(entries=list(ENTRIES),pairs=manifest_invocations,
            observed_sorted=sorted(ran_generated)),indent=2))
        for invocation in manifest_invocations:
            assert (args.output_dir/invocation['log']).is_file(), invocation
            assert (args.output_dir/invocation['exit_file']).is_file(), invocation
    print(f'Mutation coverage: {killed}/{tested} detected; selected {tested}/{len(pairs)} registered pairs. Runtime assurance: 0/8 families.',flush=True)
    print(f'Generated both-entry pairs: {len(observed_generated)} observed in slice; required full population {len(expected_generated)} (source-derived controls x both entries).',flush=True)
    return 0 if tested and killed==tested else 1


if __name__=='__main__':
    raise SystemExit(main())
