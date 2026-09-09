"""Source-only selector reference evaluator, called by the public publication gate.

No AX runtime, network reader, filesystem recovery, or authority verifier exists
here. Inputs are synthetic facts and concrete records. Record validation never
attests runtime provenance, observation completeness or durability.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from selector_inventory import Inventory


class Refusal(Exception):
    pass


def refuse(code):
    raise Refusal(code)


def expression(node, context):
    if not isinstance(node, dict):
        return node
    if len(node) != 1:
        raise ValueError('guard expressions have exactly one operator')
    operator, arguments = next(iter(node.items()))
    if operator == 'get':
        return context[arguments]
    if operator not in {'eq', 'ne', 'gt', 'all', 'any'} or not isinstance(arguments, list):
        raise ValueError('unknown or malformed selector guard operator')
    values = [expression(value, context) for value in arguments]
    if operator in {'eq', 'ne', 'gt'} and len(values) != 2:
        raise ValueError('binary selector guard needs two arguments')
    if operator == 'eq': return values[0] == values[1]
    if operator == 'ne': return values[0] != values[1]
    if operator == 'gt': return values[0] > values[1]
    if operator == 'all': return all(values)
    return any(values)


def guards(stage, context, policy):
    for rule in policy['guards'][stage]:
        if set(rule) != {'when', 'error'}:
            raise ValueError('selector guard is closed')
        if expression(rule['when'], context):
            refuse(rule['error'])


def uuid7(value):
    return isinstance(value, str) and re.fullmatch(
        r'[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value
    ) is not None


def parse(value, policy):
    if not isinstance(value, str) or len(value) > 134:
        refuse('invalid_arguments')
    if '@' in value:
        key, source = (value.split('@', 1) if policy['split'] == 'first' else value.rsplit('@', 1))
        if source == 'local':
            pass
        elif source.startswith('peer:'):
            if not 1 <= len(source[5:]) <= policy['alias_max']:
                refuse('invalid_arguments')
        elif source.startswith('id:') and uuid7(source[3:]):
            pass
        else:
            refuse('invalid_arguments')
    else:
        key, source = value, None
    durable = key.startswith('id:')
    if durable:
        if not uuid7(key[3:]):
            refuse('invalid_arguments')
        key = key[3:]
    elif not re.fullmatch(policy['name_pattern'], key):
        refuse('invalid_arguments')
    return key, durable, source


def resolve(facts, policy):
    key, durable, source = parse(facts['selector'], policy)
    guards('config', facts, policy)
    hosts = facts['sources']
    aliases = [s['alias'] for s in hosts if s['id'] != facts['local_host']]
    guards('mapping', {'aliases_count': len(aliases), 'unique_aliases': len(set(aliases)), 'hosts_count': len(hosts), 'unique_hosts': len({s['id'] for s in hosts})}, policy)
    explicit = source is not None
    if explicit:
        if source == 'local':
            selected = [s for s in hosts if s['id'] == facts['local_host']]
        elif source.startswith('peer:'):
            selected = [s for s in hosts if s['id'] != facts['local_host'] and s['alias'] == source[5:]]
        else:
            selected = [s for s in hosts if s['id'] == source[3:]]
        guards('source', {'matches': len(selected)}, policy)
        guards('allowlist', selected[0], policy)
    else:
        selected = [s for s in hosts if s['allowed']]

    def read(sources):
        rows = []
        for host in sources:
            guards('read', dict(host, read_domain='local' if host['id'] == facts['local_host'] else 'remote'), policy)
            for record in host['records']:
                guards('record', record, policy)
                if not record['tombstoned']:
                    rows.append((record, host['id']))
        return rows

    def pick(rows, by_id=False):
        matches = [(r, h) for r, h in rows if (r['id'] == key if by_id else r['name'].lower() == key.lower())]
        ids = {r['id'] for r, h in matches}
        guards('collision', {'identities': len(ids), 'digests': len({r['record'] for r, h in matches})}, policy)
        if not by_id:
            matches = [(r, h) for r, h in matches if r['name'] == key]
        if matches:
            r, host = sorted(matches, key=lambda row: row[1])[0]
            return {'session_id': r['id'], 'record_id': r['record'], 'source_host_id': host}
        return None

    if explicit:
        rows = read(selected)
        result = pick(rows, True) if durable else pick(rows) or (pick(rows, True) if uuid7(key) else None)
        if result:
            return result
        if policy['explicit_fallback']:
            return pick(read(hosts)) or refuse('not_found')
    elif durable:
        result = pick(read(selected), True)
        if result:
            return result
    else:
        for tier in policy['bare_order']:
            sources = [s for s in selected if s['id'] == facts['local_host']] if tier == 'local_name' else [s for s in selected if s['id'] != facts['local_host']] if tier == 'peer_name' else selected
            if tier == 'uuid' and not uuid7(key):
                continue
            result = pick(read(sources), tier == 'uuid')
            if result:
                return result
    refuse('not_found')


def summary(facts, policy):
    guards('read', facts, policy)
    guards('record', {'valid': facts['record_valid']}, policy)
    lease = facts['lease']
    guards('summary_lease', {'required': policy['summary_requires_lease'], 'lease': lease}, policy)
    if lease is None:
        lease = {'owner': facts['source'], 'epoch': 1, 'id': facts['allocated_lease']}
    guards('summary_observation', facts, policy)
    owner = facts['source'] if policy['source_is_owner'] else lease['owner']
    return {'owner': owner, 'lease_epoch': lease['epoch'], 'lease_id': lease['id'],
            'local_role': 'owner' if owner == facts['local_host'] else 'replica',
            'checkpoint': facts['checkpoint'], 'state': facts['state']}


def revalidate(facts, policy):
    guards('plan', facts, policy)
    guards('read', facts, policy)
    guards('allowlist', facts, policy)
    for field in policy['plan_fields']:
        guards('plan_fact', {'present': field in facts['plan'] and field in facts['current'], 'expected': facts['plan'].get(field), 'current': facts['current'].get(field)}, policy)


def typed(value, kind):
    if kind.startswith('Exact '):
        return value == kind[6:]
    if kind == 'UUIDv7': return uuid7(value)
    if kind == 'UUIDv4':
        return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value) is not None
    if kind == 'digest':
        return isinstance(value, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', value) is not None
    if kind == 'Positive uint53': return type(value) is int and 1 <= value <= 9007199254740991
    if kind == 'digest array':
        return isinstance(value, list) and all(typed(v, 'digest') for v in value) and value == sorted(set(value))
    if kind == 'timestamp':
        if not isinstance(value, str) or re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z', value) is None: return False
        try: datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError: return False
        return True
    if kind == 'extensions':
        return isinstance(value, dict) and all(re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9-]+)+', k) for k in value)
    raise ValueError('unknown selector representation type: ' + kind)


def remote_attach(facts, policy):
    # Composed invocation binding precedes any resolution or revalidation. The
    # actual call is attach --local with no destination argument, so each end's
    # plan action must equal attach and each end's destination must be null. A
    # status plan, a plan for another destination, or two agreeing copies of a
    # wrong plan never authorize attach input. Source/configuration facts stay
    # endpoint-local and are bound below, never cross-compared here.
    if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':
        refuse('selector_plan_stale')
    if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:
        refuse('selector_plan_stale')
    # Composed source resolution -> initiator validation -> wire operand ->
    # owner exact-ID admission. Synthetic records never attest a live channel.
    selected = resolve(facts['selection'], policy)
    # Original single-argument binding: the initiator plan must retain the
    # literal invocation selector and the alias derived from the actually
    # selected source (null for local). Another argument resolving to the same
    # UUID, or two agreeing copies of a wrong selector/alias, never authorizes
    # input. Receiver selector/alias/source facts stay endpoint-local.
    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')
    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:
        refuse('selector_plan_stale')
    local = facts['initiator']
    if selected['session_id'] != local['plan']['session_id'] or selected['record_id'] != local['plan']['session_record_id'] or selected['source_host_id'] != local['plan']['source_host_id']:
        refuse('selector_plan_stale')
    revalidate(local, policy)
    plan = local['plan']
    expected = {field: plan[field] for field in policy['_attach_types']}
    operand = policy['_attach_operand'].replace('SESSION_UUID', plan['session_id'])
    if facts.get('operand') is not None: operand = facts['operand']
    if 'expected' in facts: expected = facts['expected']
    if facts['receiver_version'] != policy['cli_result']:
        refuse('incompatible_schema')
    if set(expected) != set(policy['_attach_types']) or any(not typed(expected[f], t) for f, t in policy['_attach_types'].items()):
        refuse('invalid_arguments')
    if not operand.startswith('id:') or not uuid7(operand[3:]):
        refuse('invalid_arguments')
    if operand[3:] != expected['session_id']:
        refuse('selector_plan_stale')
    receiver = facts['receiver']
    revalidate(receiver, policy)
    if facts['receiving_host'] != expected['owner_host_id']:
        refuse('selector_plan_stale')
    for field, value in expected.items():
        if receiver['current'].get(field) != value:
            refuse('selector_plan_stale')
    # Same-named records and UUID-shaped display names cannot choose identity.
    record = next((r for r in facts['owner_records'] if r['id'] == operand[3:]), None)
    if record is None or record['record'] != expected['session_record_id']:
        refuse('selector_plan_stale')
    guards('record', record, policy)
    if record['tombstoned']:
        refuse('selector_plan_stale')
    return {'session_id': record['id'], 'owner_host_id': expected['owner_host_id'], 'input_allowed': True}


def remote_logs(facts, policy):
    # Same invocation binding as remote_attach, against the actual logs route:
    # each end's plan action must equal logs and each end's plan destination
    # must equal the actual explicit --peer host, checked per-endpoint against
    # peer_host. Initiator and receiver plans are never compared with each
    # other; receiver-local source/configuration facts keep their own meanings.
    if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':
        refuse('selector_plan_stale')
    if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:
        refuse('selector_plan_stale')
    selected = resolve(facts['selection'], policy)
    # Original single-argument binding, same semantics as remote_attach: the
    # initiator plan retains the literal --session invocation selector and the
    # alias derived from the actually selected source (null for local).
    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')
    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:
        refuse('selector_plan_stale')
    revalidate(facts['initiator'], policy)
    if selected['session_id'] != facts['initiator']['plan']['session_id'] or selected['record_id'] != facts['initiator']['plan']['session_record_id'] or selected['source_host_id'] != facts['initiator']['plan']['source_host_id']:
        refuse('selector_plan_stale')
    if facts['receiver_version'] != policy['cli_result']:
        refuse('incompatible_schema')
    operand = policy['_logs_operand'].replace('SESSION_UUID', selected['session_id'])
    if not operand.startswith('id:') or not uuid7(operand[3:]):
        refuse('invalid_arguments')
    if facts.get('cursor') is not None:
        if facts['cursor']['host_id'] != facts['peer_host']:
            refuse('invalid_arguments')
        if facts['cursor']['session_id'] != operand[3:]:
            refuse('invalid_arguments')
    revalidate(facts['receiver'], policy)
    if facts['receiver']['plan']['session_id'] != selected['session_id'] or facts['receiver']['plan']['session_record_id'] != selected['record_id']:
        refuse('selector_plan_stale')
    if facts['emitting_host_id'] != facts['peer_host']:
        refuse('host_identity_mismatch')
    events = [e for e in facts['events'] if e['session_id'] == operand[3:]]
    if any(e['host_id'] != facts['emitting_host_id'] for e in events):
        refuse('integrity_failure')
    return {'session_id': operand[3:], 'emitting_host_id': facts['emitting_host_id'], 'events': events}


def bootstrap_record(facts, policy):
    def require(ok):
        if not ok: refuse('selector_bootstrap_incomplete')
    intent = facts.get('intent')
    fields = {'selector_version', 'session_record_id', 'workspace_group_record_id', 'creating_host_id', 'bootstrap_operation_id', 'first_checkpoint_operation_id', 'initial_lease'}
    require(isinstance(intent, dict) and set(intent) == fields)
    require(intent['selector_version'] == policy['version'])
    for field in ['creating_host_id', 'bootstrap_operation_id', 'first_checkpoint_operation_id']:
        require(uuid7(intent[field]))
    require(intent['bootstrap_operation_id'] != intent['first_checkpoint_operation_id'])
    lease = intent['initial_lease']
    require(isinstance(lease, dict) and set(lease) == set(policy['_lease_fields']))
    for field in ['record_id']:
        require(typed(lease[field], 'digest'))
    for field in ['session_id', 'subject_id', 'holder_host_id', 'issued_by_host_id', 'created_by_host_id']:
        require(uuid7(lease[field]))
    require(typed(lease['lease_id'], 'UUIDv4'))
    require(typed(lease['epoch'], 'Positive uint53'))
    require(typed(lease['created_at'], 'timestamp'))
    require(typed(lease['extensions'], 'extensions'))
    for field, value in policy['_bootstrap_values'].items():
        require(type(lease[field]) is type(value) and lease[field] == value)
    session, workspace = facts['session'], facts['workspace']
    for record in [lease, session, workspace]:
        require(record.get('record_id') == 'sha256:' + hashlib.sha256(policy['_canonical']({k:v for k,v in record.items() if k != 'record_id'})).hexdigest())
    require(intent['session_record_id'] == session['record_id'])
    require(intent['workspace_group_record_id'] == workspace['record_id'])
    require(session['schema'] == 'urn:ax:schema:session-record' and workspace['schema'] == 'urn:ax:schema:workspace-group')
    require(session['subject_id'] == session['session_id'] == lease['session_id'] == lease['subject_id'])
    require(session['workspace_group_id'] == workspace['workspace_group_id'] == workspace['subject_id'])
    require(session['launch_plan']['cwd_workspace_id'] in [m['workspace_id'] for m in workspace['members']])
    require(intent['creating_host_id'] == session['created_by_host_id'] == lease['holder_host_id'] == lease['issued_by_host_id'] == lease['created_by_host_id'] == facts['local_host'])
    require(intent == facts.get('original_intent'))
    return lease


def evaluate_body(kind, facts, policy):
    try:
        if kind == 'parse':
            key, durable, source = parse(facts['selector'], policy)
            return {'key': key, 'durable': durable, 'source': source}
        if kind == 'resolve':
            return resolve(facts, policy)
        if kind == 'plan':
            revalidate(facts, policy)
            return {'session_id': facts['plan']['session_id'], 'effect_allowed': True}
        if kind == 'remote_attach':
            return remote_attach(facts, policy)
        if kind == 'remote_logs':
            return remote_logs(facts, policy)
        if kind == 'summary':
            return summary(facts, policy)
        if kind == 'list':
            return {'sessions': [summary(row, policy) for row in facts['records']]}
        if kind == 'bootstrap':
            guards('read', facts, policy)
            lease = bootstrap_record(facts, policy)
            if facts['lease_exists']:
                return {'action': 'reconcile_existing_lease'}
            guards('bootstrap', facts, policy)
            return {'action': 'publish_original_initial_lease', 'lease_id': lease['lease_id'], 'operation_id': facts['intent']['bootstrap_operation_id']}
        if kind == 'version':
            version = facts['version']
            if version not in ['1.0.0', '2.0.0', '3.0.0', '4.0.0', policy['cli_result']]:
                return {'error': 'incompatible_schema', 'error_version': policy['error']}
            error = policy['error'] if version == policy['cli_result'] else {'1.0.0':'1.0.0','2.0.0':'1.1.0','3.0.0':'1.2.0','4.0.0':'1.3.0'}[version]
            if version != policy['cli_result'] and ('@' in facts['selector'] or facts['selector'].startswith('id:')):
                return {'error': 'invalid_arguments', 'error_version': error}
            if not facts['representable']:
                return {'error': 'selector_bootstrap_incomplete' if version == policy['cli_result'] else 'local_precondition_failed', 'error_version': error}
            return {'result_version': version, 'error_version': error}
        raise ValueError(f'unknown selector fixture kind {kind}')
    except Refusal as failure:
        return {'error': str(failure)}


def evaluate(kind, facts, policy):
    outcome = evaluate_body(kind, facts, policy)
    if 'error' in outcome:
        outcome['exit_code'] = policy['error_exits'][outcome['error']]
        outcome.setdefault('error_version', policy['error'])
        if outcome['error'].startswith('selector_'):
            outcome['retryable'] = False
    return outcome


def validate(root: Path, spec: str, canonical):
    errors = []
    try:
        policy_blocks = re.findall(r'~~~selector-policy\n(.*?)\n~~~', spec, re.S)
        if len(policy_blocks) != 1:
            raise ValueError('exactly one normative selector policy required')
        policy = json.loads(policy_blocks[0])
        policy['_canonical'] = canonical
        lease_section = spec.split('### 5.3 Lease Record and ownership', 1)[1].split('Normative example:', 1)[0]
        policy['_lease_fields'] = re.findall(r'^\| <code>([a-z_]+)</code> \|', lease_section, re.M)
        bootstrap_table = spec.split('| Bootstrap constraint | Required value |', 1)[1].split('\n\n', 1)[0]
        policy['_bootstrap_values'] = {k: json.loads(v) if v in ['1', '2', 'null'] else v for k,v in re.findall(r'^\| ([a-z_]+) \| ([^|]+) \|$', bootstrap_table, re.M)}
        attach_section = spec.split('##### CLI 5 remote attach route', 1)[1].split('#### 14.7.3', 1)[0]
        policy['_attach_operand'] = re.search(r'^ssh -t HOST ax attach (\S+) --local', attach_section, re.M)[1]
        attach_table = attach_section.split('| Attach expectation | Type |', 1)[1].split('\n\n', 1)[0]
        policy['_attach_types'] = dict(re.findall(r'^\| ([a-z_]+) \| ([^|]+) \|$', attach_table, re.M))
        logs_section = spec.split('##### CLI 5 remote log filtering', 1)[1].split('#### 14.7.3', 1)[0]
        policy['_logs_operand'] = re.search(r'^ssh HOST ax logs --session (\S+) --limit', logs_section, re.M)[1]
        data = json.loads((root / 'fixtures/session_selector_conformance.json').read_text())
        families = set(re.findall(r'^\| (SEL-[A-Z]+) \|', spec, re.M))
        expected_ids = set(re.findall(r'^\| <code>(SEL-CASE-[^<]+)</code> \|', spec, re.M))
        error_section = spec.split('Structured Error 1.4.0 keeps', 1)[1].split('#### 14.7.4', 1)[0]
        exits = {code: int(number) for number, code in re.findall(r'^\| (\d+) \| <code>(selector_[a-z_]+)</code>', error_section, re.M)}
        if exits != {code: number for code, number in policy['error_exits'].items() if code.startswith('selector_')}:
            errors.append('selector: versioned error table differs from executable policy')
        cases = data['cases']
        inventory = Inventory(root)
        expected_pairs = set(inventory.pairs)
        composition = inventory.audit(cases)
        for cell in composition['cells']:
            if cell['missing']:
                errors.append('selector: composed coverage missing ' + cell['key'] + ': ' + ', '.join(cell['missing']))
        binding = inventory.binding_audit(cases)
        for problem in binding['missing']:
            errors.append('selector: invocation binding divergence missing ' + problem)
        causal = inventory.causal_audit(cases, policy, evaluate)
        for problem in causal['missing']:
            errors.append('selector: causal binding witness noncausal ' + problem)
        actual_pairs = {(c['facts']['plan']['action'], c['facts']['boundary']) for c in cases if c['id'].startswith('SEL-CASE-boundary-')}
        if not expected_pairs or actual_pairs != expected_pairs:
            errors.append('selector: action/boundary inventory mismatch')
        covered_pairs = set()
        for action, boundary in expected_pairs:
            names = {'SEL-CASE-boundary-' + action + '-' + boundary + '-' + shape for shape in ['stable', 'stale', 'revoked', 'failed', 'forged']}
            witnesses = [c for c in cases if c['id'] in names and c['kind'] == 'plan' and c['facts']['plan']['action'] == action and c['facts']['boundary'] == boundary]
            if len(witnesses) == 5:
                covered_pairs.add((action, boundary))
            else:
                errors.append(f'selector: missing action/boundary witnesses {action}/{boundary}')
        case_ids = [case['id'] for case in cases]
        if not expected_ids or set(case_ids) != expected_ids or len(case_ids) != len(set(case_ids)):
            errors.append('selector: normative case inventory mismatch')
        if not families or {case['family'] for case in cases} != families:
            errors.append('selector: normative family coverage mismatch')
        if data['contract'] != policy['version'] or data['specification_version'] != '0.6.0':
            errors.append('selector: fixture version mismatch')
        # Source pins are explicit editorial drift guards, not execution proof.
        for start, end, digest in data['prose_sections']:
            text = spec.split(start, 1)[1].split(end, 1)[0]
            if hashlib.sha256(text.encode()).hexdigest() != digest:
                errors.append(f'selector: reviewed prose drift at {start}')
        passed = 0
        for case in cases:
            try:
                actual = evaluate(case['kind'], case['facts'], policy)
            except (ValueError, KeyError, TypeError, IndexError) as failure:
                actual = {'invalid_evaluation': str(failure)}
            if actual != case['expected']:
                errors.append(f"selector: {case['id']} expected {case['expected']!r}, got {actual!r}")
            else:
                passed += 1
        print(f'Selector publication coverage: {passed}/{len(expected_ids)} cases; {len({c["family"] for c in cases} & families)}/{len(families)} families; AX runtime coverage 0/8 (not implemented)')
        print(f'Selector boundary coverage: {len(covered_pairs)}/{len(expected_pairs)} action/boundary pairs with stable/stale/revoked/read-failed/forged witnesses (synthetic).')
        print(f"Selector composed coverage: {composition['covered_rows']}/{composition['required_rows']} scoped rows; {composition['covered_witnesses']}/{composition['required_witnesses']} witnesses (synthetic; execution checked above).")
        print(f"Selector invocation binding: {binding['covered_bindings']}/{binding['required_bindings']} divergence witnesses ({binding['bounds']})")
        print(f"Selector causal binding: {causal['covered_causal']}/{causal['required_causal']} causal witnesses ({causal['bounds']})")
        bootstrap = [c for c in cases if c['kind'] == 'bootstrap']
        remote = [c for c in cases if c['kind'] == 'remote_attach']
        logs = [c for c in cases if c['kind'] == 'remote_logs']
        print(f'Selector concrete representation: {len(bootstrap)} BootstrapIntent/Lease cases; {len(remote)} composed remote attach cases; {len(logs)} remote log cases. Provenance, IO, concurrency, full Session/Workspace schemas and transport execution are outside this evaluator.')
    except (AssertionError, OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError) as error:
        errors.append(f'selector: missing/malformed conformance input: {error}')
    return errors
