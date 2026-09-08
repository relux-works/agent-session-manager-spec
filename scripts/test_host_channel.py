#!/usr/bin/env python3
"""Attack source-derived obligations through validate_spec.main (and run_validation).

Mutants are disposable. Behavioral kills require an incorrect vector decision,
not a prose digest or projection mismatch. Projection attacks are reported as
integrity evidence separately. This is not AX TLS/runtime testing.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from host_admission import read_policy, replace_policy, POLICY
from validate_host_channel import CLAUSES

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', choices=['all','source','model','fixture','obligations','publication'], default='all')
    parser.add_argument('--dimension', choices=['entrypoint','carrier'], default='entrypoint')
    parser.add_argument('--report', type=pathlib.Path)
    args = parser.parse_args()
    report = []
    with tempfile.TemporaryDirectory(prefix='ax-host-mutations-') as temp:
        repo = pathlib.Path(temp) / 'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git','.temp','.task-board','__pycache__'))
        paths = ['SPEC.md','CONTRIBUTING.md','scripts/validate_spec.py','scripts/validate_host_channel.py','scripts/host_admission.py','fixtures/host_channel_conformance.json']
        originals = {p:(repo/p).read_bytes() for p in paths}
        original_spec = originals['SPEC.md'].decode()
        policy = read_policy(original_spec)
        obligation_count = sum(len(rules) for rules in policy['gates'].values())
        coverage_marker = f'Host Channel executable obligations: {obligation_count}/{obligation_count}'
        mutants = []
        def add(name, bound, kind, payload, gate):
            mutants.append((name,bound,kind,payload,gate))
        if args.group in {'all','source'}:
            for gate, clauses in CLAUSES.items():
                for n, clause in enumerate(clauses,1):
                    add(f'source-token-absence-{gate}-{n}', 'literal clause removed (retained presence control)', 'remove-clause', clause, gate)
                    add(f'source-token-preserving-{gate}-{n}', 'explanation obligation applies only to initial initiator requests', 'qualify-clause', clause, 'source-projection')
            add('review-generation-narrowing','effect recheck applies only to initial requests','prose-replace',
                ('under the authorization lock immediately before each externally visible\nside-effect boundary.',
                 'under the authorization lock immediately before each externally visible\nside-effect boundary only for initial requests; resumed transfers, retries, queued work and recovery bypass this recheck.'),'source-projection')
            add('review-mtls-narrowing','only server verifies certificates; clients disable verification','prose-replace',
                ('<code>InsecureSkipVerify=false</code>,','<code>InsecureSkipVerify=false</code> only on the server; clients may use <code>InsecureSkipVerify=true</code>,'),'source-projection')
            add('publication-manual-commands','restores superseded per-command approval','contributing',
                ('Explicit delivery authorization permits automation to stage the reviewed scope, create signed commits, and push a feature branch/PR after validation.',
                 'Automation MUST stop and obtain manual approval before every stage, commit and push command.'),'publication-authority')
            add('publication-manual-checklist','checklist requires superseded manual-command approval','contributing',
                ('and was created under explicit signed-delivery authorization after validation.',
                 'and was created only after explicit human review of the handed commands.'),'publication-authority')
        if args.group in {'all','obligations'}:
            dimensions = ['entrypoint', 'carrier'] if args.group == 'all' else [args.dimension]
            for dim in dimensions:
              for gate, rules in policy['gates'].items():
                  for field, predicate in rules.items():
                      if field in {'entrypoint','carrier'}:
                          changed = {'in':predicate['in']+['unknown']}
                          bound = f'accepts undeclared {field} context'
                      else:
                          changed = {'when':{'field':dim,'in':[rules[dim]['in'][0]],'require':predicate}}
                          bound = f'{field} enforced only for {dim}={rules[dim]["in"][0]}; other contexts bypass it'
                      add(f'scope-{dim}-{gate}-{field}',bound,'policy',(gate,field,changed),gate)
        if args.group in {'all','model'}:
            variants = [
                ('tls-client-direction','HC-TLS','client_version',{'in':['1.3','1.2']}),
                ('tls-server-direction','HC-TLS','server_version',{'in':['1.3','1.2']}),
                ('cert-client-direction','HC-CERT','client_chain',{'in':[True,False]}),
                ('cert-server-direction','HC-CERT','server_chain',{'in':[True,False]}),
                ('map-spki-bypass','HC-MAP','spki_match',{'in':[True,False]}),
                ('hello-client-direction','HC-HELLO','client_hello',{'uuid7':True}),
                ('hello-server-direction','HC-HELLO','server_hello',{'uuid7':True}),
                ('dispatch-client-direction','HC-DISPATCH','client_tls',{'in':[True,False]}),
                ('dispatch-server-direction','HC-DISPATCH','server_tls',{'in':[True,False]}),
                ('migration-launch-bypass','HC-MIGRATE','launch',{'in':['--host-channel 1.0.0','']}),
                ('revoked-admission','HC-LIFECYCLE','credential_state',{'in':['active','retiring','revoked']}),
                ('tls-byte-plus-one','HC-TLS','incoming_handshake_bytes',{'range':[1,1048577]}),
                ('tls-time-plus-one','HC-TLS','handshake_ms',{'range':[1,10001]}),
                ('rotation-plus-one','HC-LIFECYCLE','overlap_seconds',{'range':[0,86401]}),
                ('idle-close-plus-one','HC-GENERATION','close_delay_ms',{'range':[0,1001]}),
                ('tls-empty-byte-bound','HC-TLS','incoming_handshake_bytes',{'range':[0,1048576]}),
            ]
            for name,gate,field,predicate in variants:
                add(name,f'{field}: '+json.dumps(predicate),'policy',(gate,field,predicate),gate)
            add('historical-registry-widening','rewrites historical Config1 version','prose-replace',
                ('| Configuration | <code>urn:ax:schema:config</code> | <code>1.0.0</code>',
                 '| Configuration | <code>urn:ax:schema:config</code> | <code>1.0.1</code>'),'HC-MIGRATE')
            add('public-call-disconnected','public main omits host validation','disconnect',None,'public_host_coverage')
            add('interpreter-range-narrowing','interpreter ignores maximum for retry','interpreter',
                ('return type(value) is int and arg[0] <= value <= arg[1]',
                 "return type(value) is int and arg[0] <= value and (facts.get('entrypoint') == 'retry' or value <= arg[1])"),'HC-TLS')
        if args.group in {'all','fixture'}:
            for gate in policy['gates']:
                add('fixture-missing-negative-'+gate,'no refusal vectors for family','remove-family',gate,'coverage')
            add('fixture-resume-context-missing','resume vectors omitted across every family','remove-context','resume','context-coverage')
            for kind in ['forged','malformed','missing','duplicate']:
                add('fixture-'+kind,'fixture '+kind,kind,None,'HC-CERT' if kind=='forged' else 'fixture')
            for kind in ['missing-policy','malformed-policy','unknown-operator','duplicate-policy']:
                add(kind,'policy '+kind,kind,None,'policy')
            add('whole-package-forged-vector','forged successful certificate fact via run_validation.sh','whole-package',None,'HC-CERT')
        if args.group in {'all','publication'}:
            for gate in policy['gates']:
                add('unknown-field-bypass-'+gate,
                    f'{gate} admits exactly the extra unsupported field on recovery/native_tailscale_ssh',
                    'interpreter', ("rules = policy['gates'][gate]",
                        "rules = policy['gates'][gate]\n"
                        f"    if gate == {gate!r} and isinstance(facts, dict) and facts.get('entrypoint') == 'recovery' and facts.get('carrier') == 'native_tailscale_ssh':\n"
                        "        facts = {k: v for k, v in facts.items() if k != 'unsupported'}"), gate)
                add('unknown-field-witness-missing-'+gate,
                    f'{gate} omits unknown-field refusal at recovery/native_tailscale_ssh',
                    'remove-unknown', gate, 'closed-coverage')
            add('publication-reached-failing-control',
                'well-shaped fixture falsely claims an unknown field is admitted',
                'unknown-admit', None, 'HC-TLS')
            add('closed-coverage-recovery-exemption',
                'coverage requirement omits only HC-TLS recovery/native_tailscale_ssh',
                'coverage-bypass', None, 'closed-coverage')

        def execute():
            return subprocess.run([sys.executable,'-B','scripts/validate_spec.py'],cwd=repo,text=True,capture_output=True)
        baseline=execute()
        print(f'baseline-public-validator: exit={baseline.returncode}',flush=True)
        if baseline.returncode or coverage_marker not in baseline.stdout:
            print(baseline.stdout,baseline.stderr);return 1
        if args.group in {'all', 'publication'}:
            # A clean public fixture with no AX on PATH, still using the real
            # installed documentation tools and full public shell entrypoint.
            bin_dir = pathlib.Path(temp) / 'bin'
            bin_dir.mkdir()
            for command in ['python3', 'structurizr-cli', 'plantuml']:
                executable = shutil.which(command)
                if not executable:
                    print('missing publication prerequisite: '+command);return 1
                (bin_dir / command).symlink_to(executable)
            environment = dict(os.environ, PATH=str(bin_dir)+os.pathsep+os.defpath)
            if shutil.which('ax', path=environment['PATH']) or (repo/'ax').exists():
                print('no-AX control is invalid: ax is present');return 1
            result = subprocess.run(['./run_validation.sh'],cwd=repo,env=environment,text=True,capture_output=True)
            print(f'publication-no-ax-full-entrypoint: exit={result.returncode}',flush=True)
            if result.returncode or coverage_marker not in result.stdout:
                print(result.stdout,result.stderr);return 1
            # Syntax failure is an invalid plant, never a behavioral kill.
            p = repo/'fixtures/host_channel_conformance.json'
            p.write_text('{')
            invalid = execute()
            diagnostic = 'host channel gate fixture: unreadable or malformed fixture:'
            print(f'publication-invalid-plant-control: exit={invalid.returncode}; class=invalid-plant',flush=True)
            if invalid.returncode != 1 or diagnostic not in invalid.stdout or 'Traceback' in invalid.stderr:
                print(invalid.stdout,invalid.stderr);return 1
            p.write_bytes(originals['fixtures/host_channel_conformance.json'])
        if args.group in {'all', 'model'}:
            equivalent = copy.deepcopy(policy)
            equivalent['gates']['HC-TLS']['client_version'] = {'in': ['1.3']}
            rendered = replace_policy(original_spec, equivalent)
            (repo/'SPEC.md').write_text(rendered)
            validator = originals['scripts/validate_spec.py'].decode().replace(
                hashlib.sha256(originals['SPEC.md']).hexdigest(), hashlib.sha256(rendered.encode()).hexdigest())
            (repo/'scripts/validate_spec.py').write_text(validator)
            result = execute()
            print(f'equivalent-source-policy-and-regenerated-table: exit={result.returncode}', flush=True)
            if result.returncode:
                print(result.stdout, result.stderr)
                return 1
        for name,bound,kind,payload,gate in mutants:
            for path,content in originals.items():(repo/path).write_bytes(content)
            spec = original_spec
            if kind == 'policy':
                changed=copy.deepcopy(policy);g,field,predicate=payload;changed['gates'][g][field]=predicate
                spec=replace_policy(spec,changed)  # regenerate projection too: behavioral evidence only
            elif kind in {'remove-clause','qualify-clause'}:
                pattern=r'\s+'.join(re.escape(word) for word in payload.split())
                match=re.search(pattern,spec)
                if not match:raise RuntimeError(name+' mutation site missing')
                replacement='' if kind=='remove-clause' else match[0]+' (only for initial initiator requests)'
                spec=spec[:match.start()]+replacement+spec[match.end():]
            elif kind in {'prose-replace','contributing','interpreter'}:
                target={'prose-replace':'SPEC.md','contributing':'CONTRIBUTING.md','interpreter':'scripts/host_admission.py'}[kind]
                text=(repo/target).read_text();before,after=payload
                if before not in text:raise RuntimeError(name+' mutation site missing')
                text=text.replace(before,after,1)
                if target=='SPEC.md':spec=text
                else:(repo/target).write_text(text)
            elif kind=='disconnect':
                p=repo/'scripts/validate_spec.py';p.write_text(p.read_text().replace('host_errors, host_ledger = validate_host_channel(ROOT, text)','host_errors, host_ledger = [], {}'))
            elif kind=='coverage-bypass':
                p=repo/'scripts/validate_host_channel.py'
                p.write_text(p.read_text().replace(
                    'missing_closed = expected_closed_contexts - unknown_field_contexts',
                    "missing_closed = expected_closed_contexts - unknown_field_contexts\n    missing_closed.discard(('HC-TLS', 'recovery', 'native_tailscale_ssh'))"))
                p=repo/'fixtures/host_channel_conformance.json';data=json.loads(p.read_text())
                data['cases']=[c for c in data['cases'] if c['id']!='HC-TLS-unknown-field-recovery-native_tailscale_ssh']
                p.write_text(json.dumps(data))
            elif kind in {'missing-policy','malformed-policy','duplicate-policy'}:
                if kind=='missing-policy':spec=spec.replace('<!-- host-admission-policy -->','<!-- missing-policy -->')
                elif kind=='malformed-policy':spec=spec.replace('"format": "ax-host-admission-1"','"format": null')
                else:spec=spec.replace('"format": "ax-host-admission-1",','"format": "ax-host-admission-1", "format": "ax-host-admission-1",')
            elif kind=='unknown-operator':
                changed=copy.deepcopy(policy);changed['gates']['HC-TLS']['client_version']={'maybe':'1.3'}
                # malformed policy cannot be passed to the renderer
                spec=POLICY.sub(lambda m: m[0].replace('"eq": "1.3"', '"maybe": "1.3"', 1), spec)
                if spec==original_spec:raise RuntimeError('unknown operator site missing')
            else:
                p=repo/'fixtures/host_channel_conformance.json';data=json.loads(p.read_text())
                if kind=='remove-context':data['cases']=[c for c in data['cases'] if c['facts'].get('entrypoint')!=payload]
                if kind=='remove-family':data['cases']=[c for c in data['cases'] if c['gate']!=payload or c['expected']!='refuse']
                if kind=='remove-unknown':data['cases']=[c for c in data['cases'] if c['id']!=payload+'-unknown-field-recovery-native_tailscale_ssh']
                if kind=='unknown-admit':next(c for c in data['cases'] if c['id']=='HC-TLS-unknown-field-recovery-native_tailscale_ssh')['expected']='admit'
                if kind in {'forged','whole-package'}:next(c for c in data['cases'] if c['id']=='HC-CERT-positive')['facts']['client_chain']=False
                if kind=='missing':p.unlink()
                elif kind=='malformed':p.write_text('{')
                elif kind=='duplicate':p.write_text('{"fixture":1,"fixture":2}')
                else:p.write_text(json.dumps(data))
            (repo/'SPEC.md').write_text(spec)
            # Defeat the caller-editable prose digest on EVERY source mutation.
            p=repo/'scripts/validate_spec.py';text=p.read_text()
            for target in ['SPEC.md','CONTRIBUTING.md']:
                text=text.replace(hashlib.sha256(originals[target]).hexdigest(),hashlib.sha256((repo/target).read_bytes()).hexdigest())
            p.write_text(text)
            result=(subprocess.run(['./run_validation.sh'],cwd=repo,text=True,capture_output=True) if kind=='whole-package' else execute())
            errors=[line for line in result.stdout.splitlines() if f'ERROR: host channel gate {gate}:' in line]
            if kind in {'policy','interpreter'}:
                errors=[line for line in errors if ': vector ' in line and 'observed' in line]
            if kind=='disconnect':
                killed=coverage_marker not in result.stdout
                failing='test_public_host_coverage' if killed else ''
            elif kind=='coverage-bypass':
                # This is the same consumer assertion exercised by the
                # unknown-field-witness-missing-HC-TLS test above. The mutant
                # must reach a successful validator before its false admission
                # can be evidence that the consumer test fails.
                killed=result.returncode == 0 and not errors
                failing='test_unknown_field_witness_required: expected closed-coverage refusal, got exit 0' if killed else ''
            else:
                killed=result.returncode!=0 and bool(errors)
                failing=errors[0] if killed else ''
            row=dict(mutant=name,narrows_to=bound,validator_exit=result.returncode,
                     named_failing_test=failing,survivor_bound='' if killed else 'Gate has not established refusal for '+bound,
                     evidence_class='behavior' if kind in {'policy','interpreter'} else 'public-wiring' if kind in {'disconnect','coverage-bypass'} else 'integrity/validation')
            report.append(row)
            print(f'{name}: exit={result.returncode}; '+('KILLED: '+failing if killed else 'SURVIVOR'),flush=True)
        killed=sum(bool(r['named_failing_test']) for r in report)
        print(f'Mutants detected by named tests: {killed}/{len(report)}; TLS/runtime coverage unknown',flush=True)
    if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if killed==len(report) else 1


if __name__=='__main__':raise SystemExit(main())
