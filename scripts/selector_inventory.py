"""Source-derived selector composition inventory adopted from accepted gate
TASK-260908-2131b6 (bundle SHA256 510f3ea9b82e8aeb1d9b6652cddf41e7d769e88841e4a135afe7e542f6d37e53).
One owner supplies public coverage, vector construction and mutation obligations.
No fixed CR2 export dependency: the public gate reads the current SPEC and fixtures.
Synthetic endpoint facts do not attest runtime authority or temporal execution.
"""
from __future__ import annotations
import ast, copy, json, re
CODE = 'scripts/validate_selector.py'
FIXTURE = 'fixtures/session_selector_conformance.json'

def read(path):
    # Missing and failed/malformed reads are never collapsed to empty inventory.
    try: return json.loads(path.read_text())
    except FileNotFoundError as exc: raise ValueError('input_missing: ' + str(path)) from exc
    except (OSError, ValueError) as exc: raise ValueError('input_read_failed: ' + str(path)) from exc

def section(text, start, end):
    assert text.count(start) == 1, 'unknown/ambiguous source: ' + start
    tail = text.split(start,1)[1]
    assert end in tail, 'missing section terminator: ' + end
    return tail.split(end,1)[0]

class Inventory:
    """Single owner for normative obligations, projection, vectors and mutants.

    Boundary membership comes from normative prose table, never evaluator policy
    or existing cases. The side projection is an explicit reviewed interpretation:
    both ends inherit action boundaries except the opposite transport endpoint.
    """
    def __init__(self, root):
        self.root = root
        self.spec = (root/'SPEC.md').read_text()
        table = section(self.spec, '| Selector action | Required boundary classes |', '\n\n')
        self.actions = dict(re.findall(r'^\| ([a-z][a-z.-]*) \| ([^|]+) \|$', table, re.M))
        assert self.actions and len(self.actions) == len(re.findall(r'^\| [a-z]', table,re.M)), 'unparsed boundary row'
        self.actions = {a: bs.split(', ') for a,bs in self.actions.items()}
        self.pairs = [(a,b) for a,bs in self.actions.items() for b in bs]
        members = section(self.spec, '| Member | Type and binding |', '\n\n')
        self.fields = re.findall(r'<code>([a-z_]+)</code>', '\n'.join(line.split(' | ')[0] for line in members.splitlines() if line.startswith('| <code>')))
        assert self.fields and len(self.fields) == len(set(self.fields)), 'unparsed plan fields'
        remote = section(self.spec, '##### CLI 5 remote attach route', '#### 14.7.3')
        routes = re.findall(r'^ssh(?: -t)? HOST ax ([a-z-]+) ', remote, re.M)
        assert len(routes) == len(set(routes)) == 2 and set(routes)=={'attach','logs'}, 'unknown remote route grammar'
        assert 'Both ends revalidate their own plans at their applicable boundaries.' in remote
        assert 'Receiver retry and transport-resume repeat exact-identity authority validation;' in remote
        assert 'Original plan\nexpectations must be revalidated at retry/transport-resume/projection boundaries.' in remote
        assert 'A continuation cursor remains opaque to the initiator' in remote
        self.routes = ['remote_'+a for a in routes]
        self.data = read(root/FIXTURE)
        # Canonical positive seeds are fixed normative IDs, never order-dependent:
        # sorting the fixture must not change the derivation base.
        by_id = {c['id']: c for c in self.data['cases']}
        self.seeds = {'remote_attach': by_id['SEL-CASE-remote-durable-collision'], 'remote_logs': by_id['SEL-CASE-logs-durable-collision']}
        self.cursor = by_id['SEL-CASE-logs-cursor']['facts']['cursor']
        # AST discovery prevents per-site string replacement ownership. A new
        # caller shape fails closed and needs an independently reviewed mapping.
        self.code = (root/CODE).read_text()
        self.calls = {}
        for fn in ast.parse(self.code).body:
            if isinstance(fn, ast.FunctionDef) and fn.name in self.routes:
                found = []
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id=='revalidate':
                        arg = ast.unparse(node.args[0])
                        side = {'local':'initiator','receiver':'receiver',"facts['initiator']":'initiator',"facts['receiver']":'receiver'}.get(arg)
                        assert side and len(node.args)==2, 'unmapped revalidation call'
                        found.append((side,node.lineno,ast.unparse(node)))
                assert {x[0] for x in found} == {'initiator','receiver'} and len(found)==2, 'caller topology changed'
                self.calls[fn.name] = {s:dict(line=n,call=c) for s,n,c in found}
        assert set(self.calls)==set(self.routes)
        self.rows = []
        self.exclusions = []
        for route in self.routes:
            action = route.removeprefix('remote_')
            scopes = ['initial','cursor'] if action=='logs' else ['initial']
            for side in ['initiator','receiver']:
                for boundary in self.actions[action]:
                    opposite = 'remote-admission' if side=='initiator' else 'remote-dispatch'
                    if boundary==opposite:
                        self.exclusions.append(dict(route=route,side=side,boundary=boundary,reason='Opposite endpoint phase; covered at its owning endpoint.'))
                        continue
                    for scope in scopes:
                        self.rows.append(dict(route=route,action=action,side=side,boundary=boundary,scope=scope,callsite=f'{CODE}:{self.calls[route][side]["line"]}',key='.'.join([action,side,boundary,scope])))
        self.shapes = ['stable','revoked','forged','failed-local','failed-remote','partial-local','partial-remote','malformed-local','malformed-remote']
        self.shapes += ['changed-'+f for f in self.fields] + ['missing-'+f for f in self.fields]
        # Explicit invocation-to-plan binding relation. Each row names the exact
        # production invocation fact, the bound plan field, the required value
        # and the committed plan/current-agree divergence witness. The witness
        # keeps plan and current in agreement while disagreeing with the actual
        # invocation; cross-endpoint equality never counts as binding.
        # Member disposition: every SelectionPlan member has exactly one row;
        # independent facts must appear in the binding relation at every
        # applicable scope, endpoint-local facts must not. A new member, a new
        # revalidation call site, or an unreviewed relation fails closed.
        disposition_table = section(self.spec, '| Plan member | Disposition | Independent fact and transformation, or endpoint-local evidence |', '\n\n')
        self.disposition = {}
        for match in re.finditer(r'^\| ([a-z_]+) \| (independent invocation fact[^\|]*|endpoint-local observation[^\|]*) \| ([^|]+) \|$', disposition_table, re.M):
            member, disp, evidence = match.groups()
            self.disposition[member.strip()] = disp.strip()
        assert set(self.disposition) == set(self.fields), 'member disposition must cover every SelectionPlan member exactly once: ' + str(sorted(set(self.fields) ^ set(self.disposition)))
        self.independent_fields = {m for m, d in self.disposition.items() if d.startswith('independent')}
        assert self.independent_fields == {'selector', 'session_id', 'session_record_id', 'source_host_id', 'source_alias', 'action', 'destination_host_id'}, 'independent set drift needs reviewed mapping: ' + str(sorted(self.independent_fields))
        binding_table = section(self.spec, '| Composed route | Plan side | Scope | Invocation fact | Plan field | Required relation | Divergence witness |', '\n\n')
        self.binding = []
        for match in re.finditer(r'^\| (attach|logs) \| (initiator|receiver|both) \| ([a-z-]+) \| ([^|]+) \| ([a-z_]+) \| ([^|]+) \| <code>(SEL-CASE-[^<]+)</code> \|$', binding_table, re.M):
            route, side, scope, fact, field, relation, witness = match.groups()
            self.binding.append(dict(route=route, side=side, scope=scope, fact=fact.strip(), field=field, relation=relation.strip(), witness=witness))
        assert len(self.binding) == 159 and len(binding_table.strip().splitlines()) == 160, 'unparsed invocation binding rows'
        assert len({b['witness'] for b in self.binding}) == 159, 'binding witness IDs must be unique'
        # Coverage: every independent field appears at every applicable scope;
        # endpoint-local fields never appear as bound plan fields.
        assert not ({b['field'] for b in self.binding} - self.independent_fields), 'binding must not claim endpoint-local members'
        def have(route, side, scope, field):
            return any(b['route']==route and b['side']==side and b['scope']==scope and b['field']==field for b in self.binding)
        for scope in ['initial', 'initial-retry', 'initial-resume', 'initial-pre-effect', 'initial-fencing']:
            for field in ['action', 'destination_host_id', 'selector', 'source_alias', 'session_id', 'session_record_id', 'source_host_id']:
                assert have('attach', 'initiator', scope, field), f'missing attach initiator {scope} {field}'
            for field in ['action', 'destination_host_id']:
                assert have('attach', 'receiver', scope, field), f'missing attach receiver {scope} {field}'
                assert have('attach', 'both', scope, field), f'missing attach both {scope} {field}'
        for scope in ['initial', 'cursor', 'initial-retry', 'cursor-retry', 'initial-resume', 'cursor-resume', 'initial-projection', 'cursor-projection']:
            for field in ['action', 'destination_host_id', 'selector', 'source_alias', 'session_id', 'session_record_id', 'source_host_id']:
                assert have('logs', 'initiator', scope, field), f'missing logs initiator {scope} {field}'
            for field in ['session_id', 'session_record_id', 'action', 'destination_host_id']:
                assert have('logs', 'receiver', scope, field), f'missing logs receiver {scope} {field}'
            for field in ['action', 'destination_host_id']:
                assert have('logs', 'both', scope, field), f'missing logs both {scope} {field}'
        # Derived completeness: every source-derived composed context must map
        # to its binding scope. A new boundary without binding witnesses fails
        # closed here instead of shrinking the denominator.
        def binding_scope_for(row):
            action, boundary, scope = row['action'], row['boundary'], row['scope']
            if action == 'attach':
                if boundary in ('remote-dispatch', 'remote-admission'):
                    return 'initial'
                if boundary == 'transport-resume':
                    return 'initial-resume'
                return 'initial-' + boundary
            if action == 'logs':
                if boundary == 'projection':
                    return 'initial-projection' if scope == 'initial' else 'cursor-projection'
                if boundary in ('remote-dispatch', 'remote-admission'):
                    return scope
                if boundary == 'retry':
                    return 'initial-retry' if scope == 'initial' else 'cursor-retry'
                if boundary == 'transport-resume':
                    return 'initial-resume' if scope == 'initial' else 'cursor-resume'
            raise ValueError('unmapped composed context: ' + str(row))
        for row in self.rows:
            expect = binding_scope_for(row)
            route = row['action']
            if row['route'] == 'remote_attach':
                assert route == 'attach'
            else:
                assert route == 'logs'
            if route == 'attach' and row['side'] == 'initiator':
                want = ['action', 'destination_host_id', 'selector', 'source_alias', 'session_id', 'session_record_id', 'source_host_id']
            elif route == 'attach':
                want = ['action', 'destination_host_id']
            elif route == 'logs' and row['side'] == 'initiator':
                want = ['action', 'destination_host_id', 'selector', 'source_alias', 'session_id', 'session_record_id', 'source_host_id']
            else:
                want = ['session_id', 'session_record_id', 'action', 'destination_host_id']
            for field in want:
                assert have(route, row['side'], expect, field), f'missing derived binding {route} {row["side"]} {expect} {field} for context {row["key"]}'

    def required_value(self, row, facts, seed_facts, side):
        # Closed relation semantics: every bound field maps to exactly one
        # reviewed required value. Anything unreviewed fails closed instead of
        # falling into a peer_host default.
        field, relation = row['field'], row['relation']
        if field == 'action':
            if row['route'] not in relation:
                raise ValueError('unreviewed action relation: ' + relation)
            return row['route']
        if field == 'destination_host_id':
            if 'null' in relation:
                return None
            if 'peer_host' in relation:
                if 'peer_host' not in facts:
                    raise LookupError('peer-bound relation without peer_host')
                return facts['peer_host']
            raise ValueError('unreviewed destination relation: ' + relation)
        if field == 'selector':
            if 'selection.selector' not in relation:
                raise ValueError('unreviewed selector relation: ' + relation)
            return seed_facts['selection']['selector']
        if field == 'source_alias':
            if 'selected source alias' not in relation:
                raise ValueError('unreviewed alias relation: ' + relation)
            # Seed is valid: plan source equals resolved source; alias is that source's configured alias.
            want = seed_facts['initiator']['plan']['source_host_id'] if (side == 'initiator' or (row['side'] == 'both' and side == 'initiator')) else seed_facts['receiver']['plan']['source_host_id']
            return next(h.get('alias') for h in seed_facts['selection']['sources'] if h['id'] == want)
        if field in ('session_id', 'session_record_id', 'source_host_id'):
            if 'resolved' not in relation:
                raise ValueError('unreviewed selection relation: ' + relation)
            plan_field = {'session_id': 'session_id', 'session_record_id': 'session_record_id', 'source_host_id': 'source_host_id'}[field]
            return seed_facts['initiator']['plan'][plan_field] if (side == 'initiator' or (row['side'] == 'both' and side == 'initiator')) else seed_facts['receiver']['plan'][plan_field]
        raise ValueError('unreviewed bound field: ' + field)

    def causal_required(self, row, facts, policy):
        # Invocation-derived required value, never seed-derived. Fails closed
        # on any unreviewed relation instead of falling into a default.
        field, relation = row['field'], row['relation']
        if field == 'action':
            if row['route'] not in relation:
                raise ValueError('unreviewed action relation: ' + relation)
            return row['route']
        if field == 'destination_host_id':
            if 'null' in relation:
                return None
            if 'peer_host' in relation:
                if 'peer_host' not in facts:
                    raise LookupError('peer-bound relation without peer_host')
                return facts['peer_host']
            raise ValueError('unreviewed destination relation: ' + relation)
        if field == 'selector':
            if 'selection.selector' not in relation:
                raise ValueError('unreviewed selector relation: ' + relation)
            return facts['selection']['selector']
        if field == 'source_alias':
            if 'selected source alias' not in relation:
                raise ValueError('unreviewed alias relation: ' + relation)
            from validate_selector import resolve
            selected = resolve(facts['selection'], policy)
            for host in facts['selection']['sources']:
                if host['id'] == selected['source_host_id']:
                    return host.get('alias')
            raise LookupError('selected source missing for alias')
        if field in ('session_id', 'session_record_id', 'source_host_id'):
            if 'resolved' not in relation:
                raise ValueError('unreviewed selection relation: ' + relation)
            from validate_selector import resolve
            selected = resolve(facts['selection'], policy)
            mapping = {'session_id': 'session_id', 'session_record_id': 'record_id', 'source_host_id': 'source_host_id'}
            return selected[mapping[field]]
        raise ValueError('unreviewed bound field: ' + field)

    @staticmethod
    def coupled_downstream(row):
        # Attach initiator session/record bindings need coupled downstream
        # facts. Production remote_attach checks the initiator plan against
        # the resolve()-selected source first, while receiver admission and
        # owner exact-ID admission both compare against initiator-plan-derived
        # expectations, never against the selected source. Receiver/owner
        # agreement with the plan therefore never proves agreement with
        # selection, so an isolating witness couples downstream to the
        # diverged plan value: receiver plan/current follow it, and the owner
        # record for the plan session carries it. Restoring the designated
        # binding then requires restoring the coupled downstream to the same
        # invocation-derived required value. Session rows need no owner
        # restore: the owner lookup is keyed by the restored session, whose
        # record is untouched and correct.
        return row['route'] == 'attach' and row['side'] == 'initiator' and row['field'] in ('session_id', 'session_record_id')

    def substantive_problem(self, kind, restored, policy, outcome):
        # Route-specific substantive restoration proof. Production
        # post-conditions are checked against independently
        # invocation-derived facts (resolve() over the restored selection
        # plus untouched endpoint facts), never against the mere absence of
        # an error key. Empty, malformed, wrong-typed, error-less-denial and
        # wrong-result instruments are all rejected with named diagnostics.
        # Returns None on substantive success, else the refusal diagnostic.
        if not isinstance(outcome, dict):
            return 'causal restore returned a non-mapping result; witness is noncausal or proof is vacuous'
        if 'error' in outcome:
            return f"causal restore still refuses {outcome.get('error')}; witness is noncausal or production is vacuous"
        from validate_selector import resolve
        try:
            selected = resolve(restored['selection'], policy)
        except Exception as exc:
            return f'causal restore selection unresolvable {exc}; witness is noncausal or proof is vacuous'
        if kind == 'remote_attach':
            # Production grants attach input as {session_id, owner_host_id,
            # input_allowed: True}. The session must be the resolved
            # selection and the owner the receiving endpoint fact.
            for key in ('session_id', 'owner_host_id', 'input_allowed'):
                if key not in outcome:
                    return f'causal restore omits {key}; error-less malformed success is not restoration'
            if outcome['input_allowed'] is not True:
                return 'causal restore lacks attach authorization (input_allowed is not True); error-less denial is not success'
            if not isinstance(outcome['session_id'], str) or not isinstance(outcome['owner_host_id'], str):
                return 'causal restore identity wrong-typed; malformed success is not restoration'
            if outcome['session_id'] != selected['session_id']:
                return 'causal restore session disagrees with resolved selection; wrong-result success is not restoration'
            if outcome['owner_host_id'] != restored.get('receiving_host'):
                return 'causal restore owner disagrees with the receiving endpoint fact; wrong-result success is not restoration'
            return None
        if kind == 'remote_logs':
            # Production projects logs as {session_id, emitting_host_id,
            # events}. The session must be the resolved selection, the
            # emitter the peer endpoint fact, and the projection exactly the
            # session-filtered input events (no dropped or padded entries).
            for key in ('session_id', 'emitting_host_id', 'events'):
                if key not in outcome:
                    return f'causal restore omits {key}; error-less malformed success is not restoration'
            if not isinstance(outcome['session_id'], str) or not isinstance(outcome['emitting_host_id'], str):
                return 'causal restore identity wrong-typed; malformed success is not restoration'
            if outcome['session_id'] != selected['session_id']:
                return 'causal restore session disagrees with resolved selection; wrong-result success is not restoration'
            if outcome['emitting_host_id'] != restored.get('peer_host'):
                return 'causal restore emitter disagrees with the peer endpoint fact; wrong-result success is not restoration'
            events = outcome['events']
            expected = [e for e in restored.get('events', [])
                        if isinstance(e, dict) and e.get('session_id') == selected['session_id']]
            if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
                return 'causal restore events projection malformed; error-less shape is not restoration'
            if any(e.get('session_id') != selected['session_id'] or e.get('host_id') != restored.get('peer_host')
                   for e in events):
                return 'causal restore events carry wrong session/emitter identity; wrong-result success is not restoration'
            if events != expected:
                return 'causal restore events projection incomplete or padded; error-less denial is not success'
            return None
        return f'unknown restoration route {kind}; witness is noncausal or proof is vacuous'

    def causal_audit(self, cases, policy, evaluator):
        # Causal witness isolation for every member/context row. Restoring only
        # the designated divergence to its independently required invocation
        # value must yield a substantive route-specific success through the
        # production evaluator: attach authorization with the resolved session
        # and receiving owner, or the exact logs identity/projection (see
        # substantive_problem). Any extra independent defect keeps the refusal
        # and fails the row, so a poisoned witness cannot count as evidence
        # for its designated binding. Both-side rows restore their exact
        # declared set; no extra defect is admitted silently. Endpoint-local
        # facts are untouched, so valid distinct-source/configuration
        # differences are preserved. The proof is substantive evaluator
        # success, never seed equality and never the mere absence of an error
        # key. Coupled attach initiator session/record rows additionally
        # assert and restore their contract-defined downstream coupling (see
        # coupled_downstream).
        by_id = {c['id']: c for c in cases}
        cells = []
        for row in self.binding:
            kind = 'remote_' + row['route']
            sides_all = ['initiator', 'receiver'] if row['side'] == 'both' else [row['side']]
            detail = dict(row=row, ok=False, reason='')
            case = by_id.get(row['witness'])
            if case is None or case['kind'] != kind:
                detail['reason'] = 'witness absent or wrong composed kind'
            elif case['expected'] != self.error('selector_plan_stale'):
                detail['reason'] = 'witness must refuse selector_plan_stale'
            else:
                facts = case['facts']
                if ('cursor' in row['scope']) != (facts.get('cursor') is not None):
                    detail['reason'] = 'witness cursor scope mismatch'
                else:
                    problems = []
                    for side in sides_all:
                        if 'pre-effect' in row['scope']:
                            expected_boundary = 'pre-effect'
                        elif 'fencing' in row['scope']:
                            expected_boundary = 'fencing'
                        elif 'projection' in row['scope']:
                            expected_boundary = 'projection'
                        elif 'retry' in row['scope']:
                            expected_boundary = 'retry'
                        elif 'resume' in row['scope']:
                            expected_boundary = 'transport-resume'
                        else:
                            expected_boundary = self.seeds[kind]['facts'][side]['boundary']
                        if facts[side]['boundary'] != expected_boundary:
                            problems.append(side + f': scope must run at {expected_boundary}')
                            continue
                        try:
                            required = self.causal_required(row, facts, policy)
                        except (ValueError, LookupError, StopIteration) as exc:
                            problems.append(side + ': ' + str(exc))
                            continue
                        plan_value = facts[side]['plan'].get(row['field'])
                        current_value = facts[side]['current'].get(row['field'])
                        if plan_value == required:
                            problems.append(side + ': plan agrees with invocation, no divergence')
                        elif plan_value != current_value:
                            problems.append(side + ': plan/current disagree; revalidation already covers this')
                        elif self.coupled_downstream(row) and side == 'initiator':
                            receiver = facts.get('receiver', {})
                            receiver_plan = receiver.get('plan', {}).get(row['field'])
                            receiver_current = receiver.get('current', {}).get(row['field'])
                            if receiver_plan != plan_value or receiver_current != plan_value:
                                problems.append(side + ': coupled downstream must follow the diverged plan value; receiver/owner agreement with the plan never proves agreement with selection')
                            elif receiver_plan == required:
                                problems.append(side + ': coupled downstream agrees with invocation, no isolation')
                            else:
                                owners = facts.get('owner_records', [])
                                if row['field'] == 'session_record_id':
                                    session = facts[side]['plan'].get('session_id')
                                    matches = [r for r in owners if isinstance(r, dict) and r.get('id') == session]
                                    if len(matches) != 1 or matches[0].get('record') != plan_value:
                                        problems.append(side + ': owner record for the plan session must carry the diverged record value')
                                else:
                                    matches = [r for r in owners if isinstance(r, dict) and r.get('id') == plan_value]
                                    plan_record = facts[side]['plan'].get('session_record_id')
                                    if len(matches) != 1 or matches[0].get('record') != plan_record:
                                        problems.append(side + ': owner record for the diverged session must carry the plan record value')
                    if problems:
                        detail['reason'] = '; '.join(problems)
                    else:
                        try:
                            required = self.causal_required(row, facts, policy)
                        except (ValueError, LookupError, StopIteration) as exc:
                            detail['reason'] = 'required derivation failed: ' + str(exc)
                        else:
                            restored = copy.deepcopy(facts)
                            for side in sides_all:
                                restored[side]['plan'][row['field']] = required
                                restored[side]['current'][row['field']] = required
                            coupled_owner_ok = True
                            if self.coupled_downstream(row):
                                restored['receiver']['plan'][row['field']] = required
                                restored['receiver']['current'][row['field']] = required
                                if row['field'] == 'session_record_id':
                                    session = restored['initiator']['plan']['session_id']
                                    matches = [r for r in restored.get('owner_records', []) if r.get('id') == session]
                                    if len(matches) != 1:
                                        detail['reason'] = 'coupled owner record for the plan session is missing or ambiguous'
                                        coupled_owner_ok = False
                                    else:
                                        matches[0]['record'] = required
                            if coupled_owner_ok:
                                try:
                                    outcome = evaluator(kind, restored, policy)
                                except (ValueError, KeyError, TypeError, IndexError) as exc:
                                    detail['reason'] = f'causal restore raised {exc}'
                                except Exception as exc:
                                    # A raising instrument (including a raw
                                    # production Refusal bypassing evaluate())
                                    # is a refusal, never a success proof.
                                    detail['reason'] = f'causal restore raised {type(exc).__name__}; witness is noncausal or proof is vacuous'
                                else:
                                    problem = self.substantive_problem(kind, restored, policy, outcome)
                                    if problem is None:
                                        detail['ok'] = True
                                    else:
                                        detail['reason'] = problem
            cells.append(detail)
        covered = sum(1 for cell in cells if cell['ok'])
        return dict(required_causal=len(self.binding), covered_causal=covered,
                    missing=[cell['row']['witness'] + ': ' + cell['reason'] for cell in cells if not cell['ok']],
                    bounds='Restoring the designated divergence (plus contract-defined coupled downstream for attach initiator session/record rows) to invocation-derived required values must yield substantive route-specific evaluator success per endpoint and context (attach authorization with resolved session/receiving owner, exact logs identity/projection). The mere absence of an error key never counts, and cross-endpoint equality never counts.')

    def _phase_guard(self, route, side, scope):
        # Single-phase guard true exactly at the row scope for the given side.
        # Production facts use facts[side].get(boundary) and facts.get(cursor).
        parts = []
        if 'pre-effect' in scope:
            parts.append(f"facts[{side!r}].get('boundary') == 'pre-effect'")
        elif 'fencing' in scope:
            parts.append(f"facts[{side!r}].get('boundary') == 'fencing'")
        elif 'projection' in scope:
            parts.append(f"facts[{side!r}].get('boundary') == 'projection'")
        elif 'retry' in scope:
            parts.append(f"facts[{side!r}].get('boundary') == 'retry'")
        elif 'resume' in scope:
            parts.append(f"facts[{side!r}].get('boundary') == 'transport-resume'")
        else:
            base = 'remote-dispatch' if side == 'initiator' else 'remote-admission'
            parts.append(f"facts[{side!r}].get('boundary') == {base!r}")
        if route == 'logs':
            if 'cursor' in scope:
                parts.append("facts.get('cursor') is not None")
            else:
                parts.append("facts.get('cursor') is None")
        return ' and '.join(parts)

    def binding_mutants(self):
        # Source-derived single-phase caller/generic population from the same
        # normative member/context relation. Each mutant narrows exactly one
        # production predicate to skip only its designated scope, with explicit
        # mapping to the real check. Adding/removing a binding row changes this
        # population; a new obligation without a control fails the gate because
        # the witness has no killer. Caller mutants skip the designated side;
        # both-side rows yield generic mutants skipping both ends at the phase.
        old_attach_action = "if facts['initiator']['plan']['action'] != 'attach' or facts['receiver']['plan']['action'] != 'attach':"
        old_logs_action = "if facts['initiator']['plan']['action'] != 'logs' or facts['receiver']['plan']['action'] != 'logs':"
        old_attach_dest = "if facts['initiator']['plan']['destination_host_id'] is not None or facts['receiver']['plan']['destination_host_id'] is not None:"
        old_logs_dest = "if facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] or facts['receiver']['plan']['destination_host_id'] != facts['peer_host']:"
        old_attach_sel_head = "    # input. Receiver selector/alias/source facts stay endpoint-local.\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:"
        old_logs_sel_head = "    # alias derived from the actually selected source (null for local).\n    actual_alias = next((h.get('alias') for h in facts['selection']['sources'] if h['id'] == selected['source_host_id']), 'unmapped')\n    if facts['initiator']['plan']['selector'] != facts['selection']['selector'] or facts['initiator']['plan']['source_alias'] != actual_alias:"
        old_attach_triple = "if selected['session_id'] != local['plan']['session_id'] or selected['record_id'] != local['plan']['session_record_id'] or selected['source_host_id'] != local['plan']['source_host_id']:"
        old_logs_init_triple = "    if selected['session_id'] != facts['initiator']['plan']['session_id'] or selected['record_id'] != facts['initiator']['plan']['session_record_id'] or selected['source_host_id'] != facts['initiator']['plan']['source_host_id']:"
        old_logs_recv_double = "    if facts['receiver']['plan']['session_id'] != selected['session_id'] or facts['receiver']['plan']['session_record_id'] != selected['record_id']:"
        for old in [old_attach_action, old_logs_action, old_attach_dest, old_logs_dest, old_attach_sel_head, old_logs_sel_head, old_attach_triple, old_logs_init_triple, old_logs_recv_double]:
            assert self.code.count(old) == 1, 'unmapped production predicate for generated binding controls: ' + old[:80]
        result = []
        for row in self.binding:
            route, side, scope, field = row['route'], row['side'], row['scope'], row['field']
            witness = row['witness']
            if side == 'both':
                guard_init = self._phase_guard(route, 'initiator', scope)
                guard_recv = self._phase_guard(route, 'receiver', scope)
                guard_both = f"({guard_init}) and ({guard_recv})"
                if field == 'action':
                    old = old_attach_action if route == 'attach' else old_logs_action
                    # Preserve the exact `if A or B:` shape: skip both at the phase.
                    # `if A or B:` -> `if (A or B) and not (guard):`
                    prefix = old.split(':')[0]
                    new = prefix.replace('if ', 'if (', 1) + f") and not ({guard_both}):"
                    result.append(dict(id=f"gen-{route}-both-{scope}-{field}-generic", level='generic', row=row, old=old, new=new, witness=witness,
                                       narrowing=f"generic: {route} {field} binding skipped only at {scope}; both ends still check elsewhere"))
                elif field == 'destination_host_id':
                    old = old_attach_dest if route == 'attach' else old_logs_dest
                    prefix = old.split(':')[0]
                    new = prefix.replace('if ', 'if (', 1) + f") and not ({guard_both}):"
                    result.append(dict(id=f"gen-{route}-both-{scope}-{field}-generic", level='generic', row=row, old=old, new=new, witness=witness,
                                       narrowing=f"generic: {route} {field} binding skipped only at {scope}; both ends still check elsewhere"))
                else:
                    raise ValueError('both-side rows bind only action/destination: ' + str(row))
                continue
            guard = self._phase_guard(route, side, scope)
            if field == 'action':
                old = old_attach_action if route == 'attach' else old_logs_action
                want = f"'{route}'"
                if side == 'initiator':
                    new = old.replace(f"facts['initiator']['plan']['action'] != {want}",
                                      f"(facts['initiator']['plan']['action'] != {want} and not ({guard}))", 1)
                else:
                    new = old.replace(f"facts['receiver']['plan']['action'] != {want}",
                                      f"(facts['receiver']['plan']['action'] != {want} and not ({guard}))", 1)
                assert new != old, 'action narrowing failed: ' + str(row)
                result.append(dict(id=f"gen-{route}-{side}-{scope}-{field}-caller", level='caller', row=row, old=old, new=new, witness=witness,
                                   narrowing=f"caller: {route} {side} {field} binding skipped only at {scope}; other end and phases still check"))
            elif field == 'destination_host_id':
                if route == 'attach':
                    if side == 'initiator':
                        new = old_attach_dest.replace("facts['initiator']['plan']['destination_host_id'] is not None",
                                                      f"(facts['initiator']['plan']['destination_host_id'] is not None and not ({guard}))", 1)
                    else:
                        new = old_attach_dest.replace("facts['receiver']['plan']['destination_host_id'] is not None",
                                                      f"(facts['receiver']['plan']['destination_host_id'] is not None and not ({guard}))", 1)
                    old = old_attach_dest
                else:
                    if side == 'initiator':
                        new = old_logs_dest.replace("facts['initiator']['plan']['destination_host_id'] != facts['peer_host']",
                                                    f"(facts['initiator']['plan']['destination_host_id'] != facts['peer_host'] and not ({guard}))", 1)
                    else:
                        new = old_logs_dest.replace("facts['receiver']['plan']['destination_host_id'] != facts['peer_host']",
                                                    f"(facts['receiver']['plan']['destination_host_id'] != facts['peer_host'] and not ({guard}))", 1)
                    old = old_logs_dest
                assert new != old, 'destination narrowing failed: ' + str(row)
                result.append(dict(id=f"gen-{route}-{side}-{scope}-{field}-caller", level='caller', row=row, old=old, new=new, witness=witness,
                                   narrowing=f"caller: {route} {side} {field} binding skipped only at {scope}; other end and phases still check"))
            elif field in ('selector', 'source_alias'):
                old = old_attach_sel_head if route == 'attach' else old_logs_sel_head
                if field == 'selector':
                    new = old.replace("facts['initiator']['plan']['selector'] != facts['selection']['selector']",
                                      f"(facts['initiator']['plan']['selector'] != facts['selection']['selector'] and not ({guard}))", 1)
                else:
                    new = old.replace("facts['initiator']['plan']['source_alias'] != actual_alias",
                                      f"(facts['initiator']['plan']['source_alias'] != actual_alias and not ({guard}))", 1)
                assert new != old, 'selector narrowing failed: ' + str(row)
                result.append(dict(id=f"gen-{route}-{side}-{scope}-{field}-caller", level='caller', row=row, old=old, new=new, witness=witness,
                                   narrowing=f"caller: {route} {side} {field} binding skipped only at {scope}; paired clause and phases still check"))
            elif field in ('session_id', 'session_record_id', 'source_host_id'):
                if route == 'attach':
                    # Attach initiator session/record rows are isolated by
                    # coupled downstream witnesses (see coupled_downstream):
                    # receiver plan/current and the owner record follow the
                    # diverged plan value, so downstream admission passes and
                    # only the designated single-clause check can refuse. A
                    # single-phase skip therefore yields a forbidden success,
                    # and each row needs its own control like every other row.
                    old = old_attach_triple
                    clause = {'session_id': "selected['session_id'] != local['plan']['session_id']", 'session_record_id': "selected['record_id'] != local['plan']['session_record_id']", 'source_host_id': "selected['source_host_id'] != local['plan']['source_host_id']"}[field]
                    new = old.replace(clause, f"({clause} and not ({guard}))", 1)
                elif side == 'initiator':
                    old = old_logs_init_triple
                    clause = {'session_id': "selected['session_id'] != facts['initiator']['plan']['session_id']", 'session_record_id': "selected['record_id'] != facts['initiator']['plan']['session_record_id']", 'source_host_id': "selected['source_host_id'] != facts['initiator']['plan']['source_host_id']"}[field]
                    new = old.replace(clause, f"({clause} and not ({guard}))", 1)
                else:
                    old = old_logs_recv_double
                    clause = {'session_id': "facts['receiver']['plan']['session_id'] != selected['session_id']", 'session_record_id': "facts['receiver']['plan']['session_record_id'] != selected['record_id']"}[field]
                    if field == 'source_host_id':
                        raise ValueError('logs receiver never binds source_host_id: ' + str(row))
                    new = old.replace(clause, f"({clause} and not ({guard}))", 1)
                assert new != old, 'selection narrowing failed: ' + str(row)
                result.append(dict(id=f"gen-{route}-{side}-{scope}-{field}-caller", level='caller', row=row, old=old, new=new, witness=witness,
                                   narrowing=f"caller: {route} {side} {field} binding skipped only at {scope}; sibling clauses and phases still check"))
            else:
                raise ValueError('unreviewed bound field for control generation: ' + field)
        # Every binding row has its own single-phase control; no exclusions.
        # Adding or removing a binding row changes this population or fails
        # closed here. A redundant obligation may only be excluded with a
        # valid implication argument over admitted facts plus executable drift
        # protection, never by failed seed mutations.
        assert len(result) == len(self.binding), 'generated control population must track the binding relation exactly: ' + str(len(result))
        assert len({m['witness'] for m in result}) == len(self.binding), 'each binding witness needs its own single-phase control'
        return result

    def binding_audit(self, cases):
        # Every relation row needs its committed divergence witness: the right
        # composed kind, the stale refusal, plan/current in agreement on the
        # bound field, and that agreed value actually diverging from the
        # required invocation value in the witnessed scope.
        by_id = {c['id']: c for c in cases}
        cells = []
        for row in self.binding:
            kind = 'remote_' + row['route']
            seed = copy.deepcopy(self.seeds[kind])
            if 'cursor' in row['scope']:
                seed['facts']['cursor'] = copy.deepcopy(self.cursor)
            else:
                seed['facts'].pop('cursor', None)
            sides_all = ['initiator', 'receiver'] if row['side'] == 'both' else [row['side']]
            for side in sides_all:
                if 'pre-effect' in row['scope']:
                    seed['facts'][side]['boundary'] = 'pre-effect'
                elif 'fencing' in row['scope']:
                    seed['facts'][side]['boundary'] = 'fencing'
                elif 'projection' in row['scope']:
                    seed['facts'][side]['boundary'] = 'projection'
                elif 'retry' in row['scope']:
                    seed['facts'][side]['boundary'] = 'retry'
                elif 'resume' in row['scope']:
                    seed['facts'][side]['boundary'] = 'transport-resume'
            detail = dict(row=row, ok=False, reason='')
            case = by_id.get(row['witness'])
            if case is None or case['kind'] != kind:
                detail['reason'] = 'witness absent or wrong composed kind'
            elif case['expected'] != self.error('selector_plan_stale'):
                detail['reason'] = 'witness must refuse selector_plan_stale'
            else:
                facts, seed_facts = case['facts'], seed['facts']
                if ('cursor' in row['scope']) != (facts.get('cursor') is not None):
                    detail['reason'] = 'witness cursor scope mismatch'
                else:
                    problems = []
                    for side in sides_all:
                        if 'pre-effect' in row['scope']:
                            expected_boundary = 'pre-effect'
                        elif 'fencing' in row['scope']:
                            expected_boundary = 'fencing'
                        elif 'projection' in row['scope']:
                            expected_boundary = 'projection'
                        elif 'retry' in row['scope']:
                            expected_boundary = 'retry'
                        elif 'resume' in row['scope']:
                            expected_boundary = 'transport-resume'
                        else:
                            expected_boundary = seed_facts[side]['boundary']
                        # Seed boundary for dispatch/admission scopes is the dispatch/admission point.
                        base = copy.deepcopy(self.seeds[kind])
                        base_boundary = base['facts'][side]['boundary']
                        if expected_boundary == base_boundary and facts[side]['boundary'] != base_boundary:
                            problems.append(side + ': scope boundary drifted from seed')
                            continue
                        if facts[side]['boundary'] != expected_boundary:
                            problems.append(side + f': scope must run at {expected_boundary}')
                            continue
                        try:
                            required = self.required_value(row, facts, seed_facts, side)
                        except (ValueError, LookupError, StopIteration) as exc:
                            problems.append(side + ': ' + str(exc))
                            continue
                        plan_value = facts[side]['plan'].get(row['field'])
                        current_value = facts[side]['current'].get(row['field'])
                        if seed_facts[side]['plan'].get(row['field']) != required:
                            problems.append(side + ': seed itself violates the relation')
                        elif plan_value == required:
                            problems.append(side + ': plan agrees with invocation, no divergence')
                        elif plan_value != current_value:
                            problems.append(side + ': plan/current disagree; revalidation already covers this')
                    if not problems:
                        detail['ok'] = True
                    else:
                        detail['reason'] = '; '.join(problems)
            cells.append(detail)
        covered = sum(1 for cell in cells if cell['ok'])
        return dict(required_bindings=len(self.binding), covered_bindings=covered,
                    missing=[cell['row']['witness'] + ': ' + cell['reason'] for cell in cells if not cell['ok']],
                    bounds='Plan/current-agree divergence from the actual invocation, per endpoint and context (initial/cursor/pre-effect/fencing/projection/retry/resume). Cross-endpoint equality never counts.')

    def divergence_witness(self, row):
        # Source-derived vector constructor for the binding relation. Starts
        # from the route positive seed, applies the witnessed scope, then moves
        # plan and current together to a well-formed value that disagrees with
        # the actual invocation. Well-formedness matters: an ill-typed value
        # would be refused for the wrong reason.
        route = 'remote_' + row['route']
        seeds = {'remote_attach': 'SEL-CASE-remote-durable-collision',
                 'remote_logs-initial': 'SEL-CASE-logs-durable-collision',
                 'remote_logs-cursor': 'SEL-CASE-logs-cursor'}
        key = route + ('-cursor' if 'cursor' in row['scope'] else '-initial' if row['route'] == 'logs' else '')
        seed = copy.deepcopy(next(c for c in self.data['cases'] if c['id'] == seeds[key]))
        facts = seed['facts']
        if 'cursor' in row['scope'] and facts.get('cursor') is None:
            facts['cursor'] = copy.deepcopy(self.cursor)
        if 'cursor' not in row['scope']:
            facts.pop('cursor', None)
        sides = ['initiator', 'receiver'] if row['side'] == 'both' else [row['side']]
        for side in sides:
            if 'pre-effect' in row['scope']:
                facts[side]['boundary'] = 'pre-effect'
            elif 'fencing' in row['scope']:
                facts[side]['boundary'] = 'fencing'
            elif 'projection' in row['scope']:
                facts[side]['boundary'] = 'projection'
            elif 'retry' in row['scope']:
                facts[side]['boundary'] = 'retry'
            elif 'resume' in row['scope']:
                facts[side]['boundary'] = 'transport-resume'
        divergent_map = {
            'action': 'status',
            'destination_host_id': '0198f4c8-7d40-7e55-8e6f-1234567890ad',
            'selector': 'other@local',
            'source_alias': 'ghost',
            'session_id': '0198f4c8-3e70-7a11-8a2b-1234567890ac',
            'session_record_id': 'sha256:' + 'f' * 64,
            'source_host_id': '0198f4c8-7d40-7e55-8e6f-1234567890ac',
        }
        if row['field'] not in divergent_map:
            raise ValueError('unreviewed divergent field: ' + row['field'])
        for side in sides:
            facts[side]['plan'][row['field']] = divergent_map[row['field']]
            facts[side]['current'][row['field']] = divergent_map[row['field']]
        return dict(id=row['witness'], kind=route, family='SEL-PLAN', facts=facts, expected=self.error('selector_plan_stale'))

    def case(self, row, shape):
        c = copy.deepcopy(self.seeds[row['route']])
        c['id'] = 'SEL-CASE-GATE-'+row['key']+'-'+shape
        f = c['facts']; target=f[row['side']]
        target['boundary'] = row['boundary']
        if row['scope']=='cursor': f['cursor']=copy.deepcopy(self.cursor)
        if shape=='revoked': target['allowed']=False
        elif shape=='forged': target['trusted_local_plan']=False
        elif shape.startswith(('failed-','partial-','malformed-')):
            target['read'],target['read_domain']=shape.split('-')
        elif shape.startswith('changed-'):
            field=shape.removeprefix('changed-'); value=target['current'][field]
            target['current'][field] = value+1 if type(value) is int else ['sha256:'+'f'*64] if isinstance(value,list) else 'changed' if value is None else str(value)+'-changed'
        elif shape.startswith('missing-'): del target['current'][shape.removeprefix('missing-')]
        if shape!='stable':
            error = 'peer_not_allowlisted' if shape=='revoked' else 'local_precondition_failed' if shape=='failed-local' else 'selector_source_read_failed' if shape=='failed-remote' else 'integrity_failure' if shape.startswith(('partial-','malformed-')) else 'selector_plan_stale'
            c['expected']=self.error(error)
        return c

    @staticmethod
    def error(error):
        # Independently bound diagnostics from 14.7.1/14.7.3, not policy guard output.
        exits={'peer_not_allowlisted':7,'local_precondition_failed':3,'selector_source_read_failed':8,'integrity_failure':9,'selector_plan_stale':16,'selector_source_not_found':4,'not_found':4,'invalid_arguments':2,'host_identity_mismatch':7}
        result=dict(error=error,exit_code=exits[error],error_version='1.4.0')
        if error.startswith('selector_'): result['retryable']=False
        return result

    def vectors(self):
        result=[self.case(row,shape) for row in self.rows for shape in self.shapes]
        # Exercise resolution read/absence and exact filter evidence through the
        # same public composed route, retaining real same-name collision seeds.
        for route in self.routes:
            for shape in ['source-missing','source-empty','source-failed','source-partial','source-malformed']:
                c=copy.deepcopy(self.seeds[route]);c['id']='SEL-CASE-GATE-'+route+'-'+shape
                f=c['facts'];s=f['selection']
                if shape=='source-missing': s['sources']=[]; error='selector_source_not_found'
                elif shape=='source-empty': s['sources'][0]['records']=[];error='not_found'
                else:
                    s['sources'][0]['read']=shape.removeprefix('source-')
                    error='local_precondition_failed' if shape=='source-failed' else 'integrity_failure'
                c['expected']=self.error(error);result.append(c)
        for row in [r for r in self.rows if r['route']=='remote_logs' and r['side']=='receiver']:
            for shape in ['wrong-emitter','forged-event']+(['cursor-host','cursor-session'] if row['scope']=='cursor' else []):
                c=self.case(row,'stable');c['id']='SEL-CASE-GATE-'+row['key']+'-'+shape;f=c['facts']
                other=f['initiator']['plan']['owner_host_id']
                if shape=='wrong-emitter': f['emitting_host_id']=other;error='host_identity_mismatch'
                elif shape=='forged-event': f['events'][0]['host_id']=other;error='integrity_failure'
                elif shape=='cursor-host': f['cursor']['host_id']=other;error='invalid_arguments'
                else: f['cursor']['session_id']=other;error='invalid_arguments'
                c['expected']=self.error(error);result.append(c)
        return result

    def audit(self, cases):
        # Ignore editorial IDs: compare full facts and expected semantics.
        observed={json.dumps({k:c[k] for k in ['kind','facts','expected']},sort_keys=True) for c in cases}
        cells=[]
        for row in self.rows:
            covered=[]
            for shape in self.shapes:
                c=self.case(row,shape)
                if json.dumps({k:c[k] for k in ['kind','facts','expected']},sort_keys=True) in observed: covered.append(shape)
            cells.append(dict(**row,covered=covered,missing=sorted(set(self.shapes)-set(covered))))
        phase_keys={(c['kind'],side,c['facts'][side]['boundary'],'cursor' if c['facts'].get('cursor') else 'initial') for c in cases if c['kind'] in self.routes for side in ['initiator','receiver']}
        return dict(required_rows=len(self.rows),present_phase_rows=sum((r['route'],r['side'],r['boundary'],r['scope']) in phase_keys for r in self.rows),covered_rows=sum(not c['missing'] for c in cells),required_witnesses=len(self.rows)*len(self.shapes),covered_witnesses=sum(len(c['covered']) for c in cells),cells=cells,exclusions=self.exclusions,generic_pairs=len(self.pairs),generic_recovery_pairs=[p for p in self.pairs if p[1]=='recovery'],bounds='Exact synthetic fact-model equivalence, not runtime trace. Matching expectations alone never means mutation coverage.')

    def condition(self, row, shape, target, generic=False):
        terms=[f"{target}.get('boundary') == {row['boundary']!r}"]
        if not generic and row['scope']=='cursor': terms.append("facts.get('cursor') is not None")
        elif not generic and row['route']=='remote_logs' and row['scope']=='initial': terms.append("facts.get('cursor') is None")
        if shape=='revoked': terms.append(f"{target}.get('allowed') is False")
        elif shape=='forged': terms.append(f"{target}.get('trusted_local_plan') is False")
        elif shape=='failed-remote': terms.extend([f"{target}.get('read') == 'failed'",f"{target}.get('read_domain') == 'remote'"])
        elif shape=='changed-source_index_digest': terms.append(f"{target}['current'].get('source_index_digest') != {target}['plan'].get('source_index_digest')")
        elif shape=='missing-source_alias': terms.append(f"'source_alias' not in {target}['current']")
        elif shape!='broad': raise AssertionError(shape)
        return ' and '.join(terms)

    def mutants(self):
        result=[]
        # Five independent causal refusal shapes per scoped caller, including
        # narrower read-domain/cursor conditions, plus broad phase skips.
        shapes=['broad','revoked','forged','failed-remote','changed-source_index_digest','missing-source_alias']
        for row in self.rows:
            for level in ['caller','generic']:
                if level=='generic' and row['scope']=='cursor': continue
                for shape in shapes:
                    result.append(dict(id=level+'.'+row['key']+'.'+shape,level=level,row=row,shape=shape,witness=self.case(row,'revoked' if shape=='broad' else shape)['id']))
        # Adjacent generic action/recovery coverage stays a separate denominator.
        for action,boundary in self.pairs:
            result.append(dict(id='adjacent.'+action+'.'+boundary,level='adjacent',action=action,boundary=boundary,witness='SEL-CASE-boundary-'+action+'-'+boundary+'-revoked'))
        return result

    def mutate(self, root, mutant):
        code=self.code
        if mutant['level']=='adjacent':
            condition=f"facts['plan'].get('action') == {mutant['action']!r} and facts.get('boundary') == {mutant['boundary']!r}"
            code=code.replace('def revalidate(facts, policy):\n','def revalidate(facts, policy):\n    if '+condition+':\n        return\n',1)
        else:
            row=mutant['row']
            if mutant['level']=='generic':
                condition=self.condition(row,mutant['shape'],'facts',generic=True)
                source_id=self.seeds[row['route']]['facts'][row['side']]['plan']['source_host_id']
                condition += f" and facts['plan'].get('action') == {row['action']!r} and facts['plan'].get('source_host_id') == {source_id!r}"
                code=code.replace('def revalidate(facts, policy):\n','def revalidate(facts, policy):\n    if '+condition+':\n        return\n',1)
            else:
                call=self.calls[row['route']][row['side']];lines=code.splitlines(keepends=True);old=lines[call['line']-1];indent=old[:len(old)-len(old.lstrip())]
                assert old.strip()==call['call'], 'AST call must be standalone'
                condition=self.condition(row,mutant['shape'],f"facts[{row['side']!r}]")
                lines[call['line']-1]=indent+'if not ('+condition+'):\n'+indent+'    '+old.lstrip()
                code=''.join(lines)
        (root/CODE).write_text(code)
        ast.parse(code)
