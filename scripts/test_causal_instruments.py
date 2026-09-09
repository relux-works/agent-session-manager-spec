#!/usr/bin/env python3
"""Substantive causal-success instrument controls through real public entries.

Every admitted restoration route (remote_attach, remote_logs) is attacked
with error-less instruments that the old missing-error check would accept as
success: denial, empty, malformed, wrong-typed and wrong-result payloads
(plus projection padding and owner/emitter substitution). Each instrument is
armed only on a poisoned restoration witness so legitimate fixtures never
trigger it; the fixed gate must refuse every armed run with exit 1 and the
named substantive diagnostic. Unarmed runs must stay green, proving the
instruments are targeted and the gate is not vacuous-refuse.

Exit 0 only when every control behaves as expected. No files are changed in
the candidate; every run executes in a disposable public-only copy.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from selector_inventory import Inventory  # noqa: E402

ENTRIES = ('./scripts/validate_spec.py', './run_validation.sh')
ATTACH_WITNESS = 'SEL-CASE-remote-resume-initiator-session-mismatch'
LOGS_WITNESS = 'SEL-CASE-logs-resume-initiator-session-mismatch'
WRONG_SESSION = '0198f4c8-3e70-7a11-8a2b-000000000000'

ATTACH_CONDITION = """    # Causal-instrument control (armed only on poisoned coupled restoration).
    if (facts['initiator'].get('boundary') == 'transport-resume'
            and facts['receiver']['plan']['action'] == 'status'
            and len({r['record'] for r in facts['owner_records']}) < len(facts['owner_records'])
            and facts['initiator']['plan']['session_id'] == resolve(facts['selection'], policy)['session_id']):"""

LOGS_CONDITION = """    # Causal-instrument control (armed only on poisoned restoration).
    if (facts['initiator'].get('boundary') == 'transport-resume'
            and facts['receiver']['plan']['action'] == 'attach'
            and facts['initiator']['plan']['session_id'] == resolve(facts['selection'], policy)['session_id']):"""

ATTACH_PAYLOADS = {
    'denial': ("{'session_id': facts['initiator']['plan']['session_id'],"
               " 'owner_host_id': facts['receiving_host'], 'input_allowed': False}",
               'lacks attach authorization'),
    'empty': ("{}", 'omits session_id'),
    'malformed': ("['session_id', 'owner_host_id', 'input_allowed']", 'non-mapping result'),
    'wrong-typed': ("{'session_id': [facts['initiator']['plan']['session_id']],"
                    " 'owner_host_id': facts['receiving_host'], 'input_allowed': True}",
                    'identity wrong-typed'),
    'wrong-result': ("{'session_id': '" + WRONG_SESSION + "',"
                     " 'owner_host_id': facts['receiving_host'], 'input_allowed': True}",
                     'session disagrees with resolved selection'),
    'wrong-owner': ("{'session_id': facts['initiator']['plan']['session_id'],"
                    " 'owner_host_id': facts['selection']['local_host'], 'input_allowed': True}",
                    'owner disagrees with the receiving endpoint fact'),
}

LOGS_PAYLOADS = {
    'denial': ("{'session_id': facts['initiator']['plan']['session_id'],"
               " 'emitting_host_id': facts['peer_host'], 'events': []}",
               'projection incomplete or padded'),
    'empty': ("{}", 'omits session_id'),
    'malformed': ("['session_id', 'emitting_host_id', 'events']", 'non-mapping result'),
    'wrong-typed': ("{'session_id': 12345,"
                    " 'emitting_host_id': facts['peer_host'], 'events': []}",
                    'identity wrong-typed'),
    'wrong-result': ("{'session_id': '" + WRONG_SESSION + "',"
                     " 'emitting_host_id': facts['peer_host'], 'events': []}",
                     'session disagrees with resolved selection'),
    'padded-projection': ("{'session_id': facts['initiator']['plan']['session_id'],"
                          " 'emitting_host_id': facts['peer_host'],"
                          " 'events': [e for e in facts['events'] if e['session_id'] == facts['initiator']['plan']['session_id']] +"
                          " [{'host_id': facts['peer_host'], 'name': 'forged', 'session_id': '" + WRONG_SESSION + "'}]}",
                          'carry wrong session/emitter identity'),
    'wrong-emitter': ("{'session_id': facts['initiator']['plan']['session_id'],"
                      " 'emitting_host_id': facts['selection']['local_host'],"
                      " 'events': [e for e in facts['events'] if e['session_id'] == facts['initiator']['plan']['session_id']]}",
                      'emitter disagrees with the peer endpoint fact'),
}


def poison_attach(data):
    victim = next(c for c in data['cases'] if c['id'] == ATTACH_WITNESS)
    for snapshot in ('plan', 'current'):
        victim['facts']['receiver'][snapshot]['action'] = 'status'


def poison_logs(data):
    victim = next(c for c in data['cases'] if c['id'] == LOGS_WITNESS)
    for snapshot in ('plan', 'current'):
        victim['facts']['receiver'][snapshot]['action'] = 'attach'


def check_armed_safety(data, route):
    # The instrument condition must be False on every committed fact set
    # except the armed restoration itself (which only exists transiently
    # inside causal_audit). The poisoned witness pre-restore must not match:
    # its initiator session still diverges from the resolved selection.
    from validate_selector import resolve  # noqa: E402
    import validate_spec as vs  # noqa: E402
    spec = (ROOT / 'SPEC.md').read_text()
    policy = json.loads(re.findall(r'~~~selector-policy\n(.*?)\n~~~', spec, re.S)[0])
    policy['_canonical'] = vs.canonical
    # Only cases of the instrumented route's kind can ever reach the
    # instrument: remote_attach instruments never see remote_logs facts.
    want_kind = 'remote_attach' if route == 'attach' else 'remote_logs'
    for case in data['cases']:
        if case['kind'] != want_kind:
            continue
        facts = case['facts']
        try:
            resolved = resolve(facts['selection'], policy)['session_id']
        except Exception:
            continue
        if route == 'attach':
            armed = (facts['initiator'].get('boundary') == 'transport-resume'
                     and facts['receiver']['plan']['action'] == 'status'
                     and len({r['record'] for r in facts.get('owner_records', [])}) < len(facts.get('owner_records', []))
                     and facts['initiator']['plan']['session_id'] == resolved)
        else:
            armed = (facts['initiator'].get('boundary') == 'transport-resume'
                     and facts['receiver']['plan']['action'] == 'attach'
                     and facts['initiator']['plan']['session_id'] == resolved)
        assert not armed, f'instrument would fire on committed case {case["id"]}'


def apply_instrument(code_path, route, payload):
    text = code_path.read_text()
    # A RAISE: payload raises instead of returning: an error-ful instrument
    # must still refuse the restoration, never launder it.
    action = 'raise ' + payload[len('RAISE:'):] if payload.startswith('RAISE:') else 'return ' + payload
    if route == 'attach':
        needle = 'def remote_attach(facts, policy):\n'
        insert = ATTACH_CONDITION + '\n        ' + action + '\n'
    else:
        needle = 'def remote_logs(facts, policy):\n'
        insert = LOGS_CONDITION + '\n        ' + action + '\n'
    assert text.count(needle) == 1, route
    text = text.replace(needle, needle + insert, 1)
    ast.parse(text)
    code_path.write_text(text)


def run_entry(entry, cwd):
    return subprocess.run([entry], cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=150)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=None)
    args = parser.parse_args()
    inv = Inventory(ROOT)
    assert len(inv.binding) == 159, len(inv.binding)
    data = json.loads((ROOT / 'fixtures/session_selector_conformance.json').read_text())
    by_id = {c['id']: c for c in data['cases']}
    assert by_id[ATTACH_WITNESS]['kind'] == 'remote_attach'
    assert by_id[LOGS_WITNESS]['kind'] == 'remote_logs'
    # Denial detectability: the logs witness must project a non-empty event
    # set for its selected session, otherwise dropping it proves nothing.
    logs_selected = by_id[LOGS_WITNESS]['facts']['initiator']['plan']['session_id']
    assert any(e['session_id'] == logs_selected for e in by_id[LOGS_WITNESS]['facts']['events']), 'logs witness projects no events'
    assert by_id[LOGS_WITNESS]['facts']['selection']['local_host'] != by_id[LOGS_WITNESS]['facts']['peer_host']
    assert by_id[ATTACH_WITNESS]['facts']['selection']['local_host'] != by_id[ATTACH_WITNESS]['facts']['receiving_host']

    controls = []
    for name, (payload, diagnostic) in ATTACH_PAYLOADS.items():
        controls.append((f'attach-{name}', 'attach', payload, diagnostic, True))
    for name, (payload, diagnostic) in LOGS_PAYLOADS.items():
        controls.append((f'logs-{name}', 'logs', payload, diagnostic, True))
    # Error-ful instruments: raising on the armed restoration must refuse too.
    controls.append(('attach-raise-refusal', 'attach', "RAISE:Refusal('selector_plan_stale')",
                     'causal restore still refuses', True))
    controls.append(('logs-raise-refusal', 'logs', "RAISE:Refusal('selector_plan_stale')",
                     'causal restore still refuses', True))
    # Targeting proofs: the denial instrument without poison never fires.
    controls.append(('attach-denial-unarmed', 'attach', ATTACH_PAYLOADS['denial'][0], '159/159 causal witnesses', False))
    controls.append(('logs-denial-unarmed', 'logs', LOGS_PAYLOADS['denial'][0], '159/159 causal witnesses', False))
    # Extra-defect preservation: poison without instrument still refuses.
    controls.append(('attach-poison-only', 'attach', None, 'causal restore still refuses', 'poison'))
    controls.append(('logs-poison-only', 'logs', None, 'causal restore still refuses', 'poison'))

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    # Fixture variants are built once per route: poison is identical for every
    # armed run, and each variant is safety-checked once (the instrument must
    # never fire on committed facts, armed or not).
    base_fixture = json.loads((ROOT / 'fixtures/session_selector_conformance.json').read_text())
    variants = {}
    for route in ('attach', 'logs'):
        for armed_state in (False, True):
            fixture = copy.deepcopy(base_fixture)
            if armed_state:
                (poison_attach if route == 'attach' else poison_logs)(fixture)
            check_armed_safety(fixture, route)
            variants[(route, armed_state)] = json.dumps(fixture, indent=2)
    manifest = []
    print('| Control | Route | Entry | Exit | Verdict |', flush=True)
    print('| --- | --- | --- | ---: | --- |', flush=True)
    failures = 0
    with tempfile.TemporaryDirectory(prefix='ax-causal-instruments-') as temp:
        for label, route, payload, diagnostic, armed in controls:
            witness = ATTACH_WITNESS if route == 'attach' else LOGS_WITNESS
            entries = ENTRIES if armed is True else ENTRIES if armed is False else ('./scripts/validate_spec.py',)
            for entry in entries:
                case_root = Path(temp) / f'{label}-{Path(entry).name}'
                shutil.copytree(ROOT, case_root,
                                ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', 'task-board.config.json', '__pycache__'))
                if armed in (True, 'poison'):
                    (case_root / 'fixtures/session_selector_conformance.json').write_text(variants[(route, True)])
                if payload is not None:
                    apply_instrument(case_root / 'scripts/validate_selector.py', route, payload)
                result = run_entry(entry, case_root)
                if armed is True:
                    ok = result.returncode == 1 and f'causal binding witness noncausal {witness}' in result.stdout and diagnostic in result.stdout
                    expect = f'exit 1 + noncausal {witness} + {diagnostic!r}'
                elif armed is False:
                    ok = result.returncode == 0 and diagnostic in result.stdout
                    expect = 'exit 0 + 159/159 (instrument never fires)'
                else:
                    ok = result.returncode == 1 and f'causal binding witness noncausal {witness}' in result.stdout and diagnostic in result.stdout
                    expect = f'exit 1 + poison refusal for {witness}'
                verdict = 'CONTROL HOLDS' if ok else f'CONTROL FAILED; expected {expect}'
                if not ok:
                    failures += 1
                print(f'| {label} | {route} | {entry} | {result.returncode} | {verdict} |', flush=True)
                if not ok:
                    print(result.stdout[-4000:], flush=True)
                if args.output_dir:
                    stem = f'{label}-' + ('spec' if entry.endswith('validate_spec.py') else 'run')
                    log_path = args.output_dir / (stem + '.log')
                    exit_path = args.output_dir / (stem + '.exit')
                    log_path.write_text(result.stdout)
                    exit_path.write_text(str(result.returncode) + '\n')
                    manifest.append(dict(control=label, route=route, entry=entry, witness=witness,
                                         expected=expect, log=log_path.name,
                                         log_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
                                         exit_file=exit_path.name, exit=result.returncode, ok=ok))
                shutil.rmtree(case_root, ignore_errors=True)
    if args.output_dir:
        (args.output_dir / 'instrument-manifest.json').write_text(json.dumps(manifest, indent=2))
        for row in manifest:
            assert (args.output_dir / row['log']).is_file(), row
            assert (args.output_dir / row['exit_file']).is_file(), row
    print(f'Instrument controls: {len(manifest) if args.output_dir else "ran"} invocations, {failures} failures.', flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
