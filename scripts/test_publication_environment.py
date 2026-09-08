#!/usr/bin/env python3
"""Real JVM/public-entrypoint portability controls; no fake renderer or AX runtime.

The bootstrap sets Python's platform default search path to a fixture containing
real Java 11. This models the hosted fallback without modifying the host system.
Every case enters test_host_channel.main -> run_validation.sh -> validate_spec.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts/publication_gate'))
from inventory import derive
from execution import finalize, control_passed, read_evidence


def classify_publication(case, repo, expected_identity, result, control):
    """Forward both success and failure through the shared typed decision.

    Expected failure never credits an exception or an absent/unreadable result.
    Preflight controls use the same evidence reader but require no launches.
    """
    try:
        gate = finalize(case, derive(repo), expected_identity, result.returncode)
        persisted = read_evidence(case/'result.json')
        if persisted['state'] != 'valid' or persisted['value'] != gate:
            return False, dict(refusal='result_error', result_read_state=persisted['state'])
        log = read_evidence(case/'public.log', 'text')
        private = read_evidence(case/'private.jsonl', 'jsonl')
        accepted = control_passed(control, gate['gate_exit'], gate,
                                  log['value'] or '', private['value'] or [])
        return accepted, gate
    except Exception as error:
        return False, dict(refusal='driver_error', error_type=type(error).__name__, detail=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java11', type=Path, required=True)
    parser.add_argument('--pinned-java', type=Path, required=True)
    parser.add_argument('--structurizr', type=Path, required=True)
    parser.add_argument('--plantuml-jar', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--mutants', action='store_true')
    parser.add_argument('--compatible-java', type=Path, required=True)
    parser.add_argument('--section', choices=['all', 'controls', 'legacy-mutants', 'identity-mutants'], default='all')
    args = parser.parse_args()
    rows = []
    workflow = (ROOT/'.github/workflows/validate.yml').read_text()
    pinned = re.search(r"java-version: '([^']+)'", workflow)[1]
    for major, home in [('11.', args.java11), (pinned, args.pinned_java)]:
        version = subprocess.run([str(home/'bin/java'), '-version'], capture_output=True, text=True)
        print(f'java{major}-version: exit={version.returncode}\n{version.stderr}', flush=True)
        required_version = f'version "{major}' + ('"' if home == args.pinned_java else '')
        if version.returncode or required_version not in version.stderr:
            return 1
        if home == args.pinned_java and 'Temurin' not in version.stderr:
            print('pinned runtime must use the workflow Temurin distribution', flush=True)
            return 1
    compatible = subprocess.run([str(args.compatible_java/'bin/java'), '-version'], capture_output=True, text=True)
    print(f'compatible-java-version: exit={compatible.returncode}\n{compatible.stderr}', flush=True)
    if compatible.returncode or 'version "25.0.1"' not in compatible.stderr or 'Temurin' not in compatible.stderr:
        return 1
    dot = shutil.which('dot')
    if not dot or not args.structurizr.is_file() or not args.plantuml_jar.is_file():
        parser.error('real Graphviz and pinned Structurizr launcher/PlantUML JAR are required')
    expected_jar_sha = re.search(r'PLANTUML_SHA256="([0-9a-f]+)"', workflow)[1]
    if hashlib.sha256(args.plantuml_jar.read_bytes()).hexdigest() != expected_jar_sha:
        print('PlantUML jar differs from workflow pin', flush=True)
        return 1
    expected_plantuml = {str(args.plantuml_jar.resolve()): expected_jar_sha}
    expected_structurizr = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (args.structurizr.parent/'lib').glob('*.jar')}
    if not expected_structurizr:
        parser.error('complete Structurizr distribution is required')
    with tempfile.TemporaryDirectory(prefix='publication-env-') as temporary:
        base = Path(temporary)
        template = base/'template'
        shutil.copytree(ROOT, template, ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', '__pycache__'))

        def run(name, expected, marker, setup=None, mutation=None, control=None):
            if control is None:
                control = 'ambient-dot' if expected == 0 else 'publication-failure'
            case = base/name
            case.mkdir()
            repo = case/'repo'
            shutil.copytree(template, repo)
            selected = case/'selected'
            selected.mkdir()
            system = case/'system'
            system.mkdir()
            (system/'java').symlink_to(args.java11/'bin/java')
            for command, target in [('python3', sys.executable), ('java', args.pinned_java/'bin/java'), ('dot', dot)]:
                (selected/command).symlink_to(target)
            (selected/'structurizr-cli').write_text('#!/bin/bash\nexec '+shlex.quote(str(args.structurizr))+' "$@"\n')
            (selected/'plantuml').write_text('#!/bin/bash\nexec java -Djava.awt.headless=true -jar '+shlex.quote(str(args.plantuml_jar))+' "$@"\n')
            for command in ['structurizr-cli', 'plantuml']:
                (selected/command).chmod(0o755)
            for tool in ['python3', 'structurizr-cli', 'plantuml', 'dot']:
                alternate = selected/('alternate-'+tool)
                alternate.write_text('#!/bin/sh\nexec '+shlex.quote(str(selected/tool))+' "$@"\n')
                alternate.chmod(0o755)
            environment = dict(os.environ, PATH=str(selected)+os.pathsep+os.defpath)
            environment.pop('JAVA_HOME', None)
            default = str(system)+os.pathsep+os.defpath
            if setup:
                default = setup(repo, selected, system, environment, default) or default
            expected_tools = {}
            for tool in ['python3', 'java', 'structurizr-cli', 'plantuml', 'dot']:
                target = args.pinned_java/'bin/java' if tool == 'java' else selected/tool
                if expected == 0 and target.is_file():
                    target = target.resolve()
                    expected_tools[tool] = (str(target), hashlib.sha256(target.read_bytes()).hexdigest())
            if mutation:
                path, before, after = mutation
                source = (repo/path).read_text()
                if source.count(before) != 1:
                    raise RuntimeError(name+': mutation site cardinality mismatch')
                (repo/path).write_text(source.replace(before, after, 1))
            expected_identity = {t:dict(target=i[0],sha256=i[1]) for t,i in expected_tools.items()}
            expected_identity.update(structurizr_jars=expected_structurizr,plantuml_jars=expected_plantuml)
            config=case/'config.json'
            config.write_text(json.dumps(dict(repo=str(repo),ledger=str(case/'private.jsonl'),
                                             counter=str(case/'counter.json'),default_path=default)))
            # Accepted controller observes the actual public no-AX entrypoint;
            # the source-derived census, not a generic main-class token, owns
            # completeness for validate/export/render/comparison separately.
            bootstrap = ('import sys; sys.path.insert(0,'+repr(str(repo/'scripts/publication_gate'))+'); '
                         'from drive import child; raise SystemExit(child('+repr(str(config))+'))')
            result = subprocess.run([sys.executable, '-B', '-c', bootstrap], cwd=repo,
                                    env=environment, text=True, capture_output=True)
            (case/'public.log').write_text(result.stdout+result.stderr)
            accepted, gate = classify_publication(case, repo, expected_identity, result, control)
            identity_errors = [] if accepted else gate.get('errors', [gate.get('refusal')])
            matched = result.returncode == expected and marker in result.stdout+result.stderr and accepted
            row = dict(test=name, exit=result.returncode, expected_exit=expected,
                       marker=marker, passed=matched, control=control, gate=gate,
                       identity_errors=identity_errors, stdout=result.stdout, stderr=result.stderr)
            rows.append(row)
            print(f'{name}: exit={result.returncode}; assertion={"PASS" if matched else "FAIL"}', flush=True)
            if not matched:
                print('identity errors:', identity_errors, flush=True)
                if not name.startswith('mutant-'):
                    print(result.stdout, result.stderr, flush=True)
            return matched

        def pin_current(repo, selected, system, environment, default):
            environment['JAVA_HOME'] = str(args.pinned_java)
            (selected/'java').unlink()
            (selected/'java').symlink_to(args.java11/'bin/java')

        def hosted_pin(repo, selected, system, environment, default):
            environment['JAVA_HOME'] = str(args.pinned_java)

        def wrong(repo, selected, system, environment, default):
            environment['JAVA_HOME'] = str(args.java11)

        def absent(repo, selected, system, environment, default):
            environment['JAVA_HOME'] = str(system/'absent')

        def unreadable(repo, selected, system, environment, default):
            home = system/'unreadable'
            (home/'bin').mkdir(parents=True)
            (home/'bin/java').symlink_to(args.pinned_java/'bin/java')
            (home/'bin').chmod(0)
            environment['JAVA_HOME'] = str(home)

        def missing_doc(repo, selected, system, environment, default):
            (selected/'structurizr-cli').unlink()

        def wrong_doc(repo, selected, system, environment, default):
            (selected/'structurizr-cli').unlink()
            (selected/'structurizr-cli').symlink_to('/usr/bin/false')

        def broken_doc(repo, selected, system, environment, default):
            (selected/'plantuml').unlink()
            (selected/'plantuml').symlink_to(system/'missing-jar-wrapper')

        def absent_dot(repo, selected, system, environment, default):
            (selected/'dot').unlink()

        def wrong_dot(repo, selected, system, environment, default):
            (selected/'dot').unlink()
            (selected/'dot').symlink_to('/usr/bin/false')

        def unreadable_dot(repo, selected, system, environment, default):
            folder = system/'unreadable-dot'
            folder.mkdir()
            (folder/'dot').symlink_to(dot)
            folder.chmod(0)
            (selected/'dot').unlink()
            (selected/'dot').symlink_to(folder/'dot')

        def ambient_graphviz(repo, selected, system, environment, default):
            environment['GRAPHVIZ_DOT'] = '/usr/bin/false'

        def ax_at(where):
            def setup(repo, selected, system, environment, default):
                folder = {'repo':repo, 'ambient':selected, 'default':system}[where]
                (folder/'ax').write_text('#!/bin/sh\nexit 99\n')
                (folder/'ax').chmod(0o755)
            return setup

        def search_error(repo, selected, system, environment, default):
            path = system/'not-directory'
            path.write_text('not a directory')
            environment['PATH'] = str(path)+os.pathsep+environment['PATH']

        def ax_read_error(repo, selected, system, environment, default):
            path = system/'not-directory'
            path.write_text('not a directory')
            return str(path)+os.pathsep+default

        positive = 'publication-no-ax-full-entrypoint: exit=0'
        cases = [
            ('pinned-path-java26', 0, positive, None),
            ('pinned-home-java26', 0, positive, pin_current),
            ('ambient-ax-excluded', 0, positive, ax_at('ambient')),
            ('ambient-graphviz-overridden', 0, positive, ambient_graphviz),
            ('absent-graphviz', 1, 'missing publication prerequisite: dot', absent_dot),
            ('unusable-graphviz-render', 1, 'SVG contains a PlantUML render failure', wrong_dot),
            ('unreadable-graphviz', 1, 'Permission denied', unreadable_dot),
            ('wrong-java11', 1, 'class file version 61.0', wrong),
            ('absent-java-pin', 1, 'missing publication prerequisite: java', absent),
            ('unreadable-java-pin', 1, 'Permission denied', unreadable),
            ('absent-documentation-tool', 1, 'missing publication prerequisite: structurizr-cli', missing_doc),
            ('wrong-documentation-tool', 1, 'publication-no-ax-full-entrypoint: exit=1', wrong_doc),
            ('broken-documentation-tool', 1, 'unreadable publication tool:', broken_doc),
            ('forbidden-default-ax', 1, 'no-AX control is invalid: ax is present', ax_at('default')),
            ('forbidden-repo-ax', 1, 'no-AX control is invalid: ax is present', ax_at('repo')),
            ('tool-search-read-error', 1, 'Not a directory', search_error),
            ('ax-search-read-error', 1, 'Not a directory', ax_read_error),
        ]
        for case in cases:
            if args.section in {'all', 'controls'}:
                name, expected, marker, setup = case
                control = ('ambient-dot' if expected == 0 else
                           'f1' if name == 'unusable-graphviz-render' else
                           'java11' if name == 'wrong-java11' else
                           'publication-failure' if name == 'wrong-documentation-tool' else 'preflight')
                run(*case, control=control)
        # The old control's exact omission: real fallback Java11 executes the
        # same Structurizr classes (61 versus55), through the full public shell.
        script = 'scripts/test_host_channel.py'
        if args.section in {'all', 'controls'}:
            # The deliberate historical omission also removes Java observation.
            # Its real failed launch is diagnostic evidence, not a JVM census.
            run('original-java-omission-reproduction', 1, 'class file version 61.0', hosted_pin, control='publication-failure', mutation=(
                script, "'plantuml', 'java', 'dot'", "'plantuml', 'dot'"))
            # Source-token-preserving workflow attack reaches the public validator.
            run('automatic-push-with-manual-token', 1, 'local-only CI requires', control='baseline-refusal', mutation=(
                '.github/workflows/validate.yml', 'on: workflow_dispatch',
                'on:\n  workflow_dispatch:\n  push:\n    branches: [ main ]'))
            run('quoted-automatic-trigger', 1, 'local-only CI requires', control='baseline-refusal', mutation=(
                '.github/workflows/validate.yml', 'on: workflow_dispatch',
                'on: workflow_dispatch\n"on": [push]'))
        if args.mutants and args.section != 'controls':
            mutants = [
                ('java-path-pin-only-with-home', 'pinned-path-java26', (
                    script, 'executable = find_tool(command, search)',
                    "executable = find_tool(command, os.defpath if command == 'java' and 'JAVA_HOME' not in environment else search)")),
                ('public-failure-only-non-one', 'wrong-documentation-tool', (
                    script, 'if result.returncode or coverage_marker not in result.stdout:',
                    'if result.returncode not in (0, 1) or coverage_marker not in result.stdout:')),
                ('pin-home-narrowed-to-absent-path', 'pinned-home-java26', (
                    script, "command == 'java' and 'JAVA_HOME' in environment",
                    "command == 'java' and 'JAVA_HOME' in environment and not shutil.which('java')")),
                ('ax-only-repo', 'forbidden-default-ax', (
                    script, "find_tool('ax', environment['PATH']) or os.path.lexists(repo / 'ax')",
                    "os.path.lexists(repo / 'ax')")),
                ('ax-only-path', 'forbidden-repo-ax', (
                    script, "find_tool('ax', environment['PATH']) or os.path.lexists(repo / 'ax')",
                    "find_tool('ax', environment['PATH'])")),
                ('read-error-as-absence', 'ax-search-read-error', (
                    script, 'except FileNotFoundError:\n            continue',
                    'except (FileNotFoundError, NotADirectoryError):\n            continue')),
                ('broken-pin-fallback', 'absent-java-pin', (
                    script, 'executable = find_tool(command, search)',
                    "executable = find_tool(command, search) or (shutil.which(command) if command == 'java' else None)")),
                ('workflow-quoted-key-exemption', 'quoted-automatic-trigger', (
                    'scripts/validate_spec.py',
                    "top_level_keys != ['name', 'on', 'jobs']",
                    "top_level_keys not in (['name', 'on', 'jobs'], ['name', 'on', '\"on\"', 'jobs'])")),
                ('workflow-token-only', 'automatic-push-with-manual-token', (
                    'scripts/validate_spec.py',
                    "len(trigger_blocks) != 1 or trigger_blocks[0].strip() != 'on: workflow_dispatch'",
                    "'workflow_dispatch' not in text")),
            ]
            legacy_count = len(mutants)
            for branch, condition, witness in [
                ('path', "'JAVA_HOME' not in environment", 'pinned-path-java26'),
                ('home', "'JAVA_HOME' in environment", 'pinned-home-java26'),
            ]:
                mutants.append(('compatible-java25-'+branch, witness, (
                    script, 'executable = find_tool(command, search)',
                    "executable = find_tool(command, search)\n        if command == 'java' and " + condition + ":\n            executable = " + repr(str(args.compatible_java/'bin/java')))))
            mutants.extend([
                ('missing-dot-admits-false', 'absent-graphviz', (
                    script, 'executable = find_tool(command, search)',
                    "executable = find_tool(command, search) or ('/usr/bin/false' if command == 'dot' else None)")),
                ('render-error-only-handwritten', 'unusable-graphviz-render', (
                    'scripts/validate_spec.py',
                    'errors.append(f"{label} SVG contains a PlantUML render failure")',
                    'if not committed.name.startswith("structurizr-"): errors.append(f"{label} SVG contains a PlantUML render failure")')),
                ('render-error-only-error-type', 'unusable-graphviz-render', (
                    'scripts/validate_spec.py',
                    'errors.append(f"{label} SVG contains a PlantUML render failure")',
                    'if svg.get("data-diagram-type") == "ERROR": errors.append(f"{label} SVG contains a PlantUML render failure")')),
                ('ambient-graphviz-bypass', 'ambient-graphviz-overridden', (
                    script, "environment['GRAPHVIZ_DOT'] = str(bin_dir / 'dot')",
                    "environment.setdefault('GRAPHVIZ_DOT', str(bin_dir / 'dot'))")),
                ('omit-execution-evidence', 'pinned-path-java26', (
                    script, "json.dumps(records), flush=True)", "json.dumps([]), flush=True)")),
                ('forge-java-identity', 'pinned-path-java26', (
                    script, "json.dumps(records), flush=True)",
                    "json.dumps([dict(r, sha256='0'*64) if r['tool'] == 'java' else r for r in records]), flush=True)")),
                ('forge-jar-identity', 'pinned-path-java26', (
                    script, "json.dumps(records), flush=True)",
                    "json.dumps([dict(r, artifacts={}) if r['tool'] == 'java' else r for r in records]), flush=True)")),
                ('omit-dot-execution', 'pinned-path-java26', (
                    script, "json.dumps(records), flush=True)",
                    "json.dumps([r for r in records if r['tool'] != 'dot']), flush=True)")),
            ])
            for tool in ['python3', 'structurizr-cli', 'plantuml', 'dot']:
                mutants.append(('compatible-substitute-'+tool, 'pinned-path-java26', (
                    script, 'executable = find_tool(command, search)',
                    "executable = find_tool(command, search)\n        if command == " + repr(tool) + ": executable = str(pathlib.Path(executable).with_name('alternate-' + command))")))
            if args.section == 'legacy-mutants':
                mutants = mutants[:legacy_count]
            elif args.section == 'identity-mutants':
                mutants = mutants[legacy_count:]
            for name, witness, mutation in mutants:
                if witness in {'automatic-push-with-manual-token', 'quoted-automatic-trigger'}:
                    def setup(repo, selected, system, environment, default):
                        p = repo/'.github/workflows/validate.yml'
                        replacement = 'on:\n  workflow_dispatch:\n  push:\n    branches: [ main ]' if witness == 'automatic-push-with-manual-token' else 'on: workflow_dispatch\n"on": [push]'
                        p.write_text(p.read_text().replace('on: workflow_dispatch', replacement))
                    expected, marker = 1, 'local-only CI requires'
                else:
                    _, expected, marker, setup = next(c for c in cases if c[0] == witness)
                control = ('baseline-refusal' if witness in {'automatic-push-with-manual-token', 'quoted-automatic-trigger'} else
                           'ambient-dot' if expected == 0 else
                           'f1' if witness == 'unusable-graphviz-render' else
                           'publication-failure' if witness == 'wrong-documentation-tool' else 'preflight')
                run('mutant-'+name, expected, marker, setup, mutation, control)
                rows[-1]['mutant'] = name
                row = rows[-1]
                killed = (not row['passed'] and 'baseline-public-validator: exit=0' in row['stdout']
                          and 'Traceback' not in row['stdout'] + row['stderr'])
                if name.startswith(('compatible-', 'omit-', 'forge-')):
                    killed = killed and row['exit'] == 0 and bool(row['identity_errors'])
                row['named_failing_test'] = witness if killed else None
                row['killed'] = killed
                if name == 'render-error-only-handwritten' and not killed:
                    row['survivor_bound'] = ('The full gate still rejects a handwritten diagram crash; '
                                             'this witness cannot isolate C4 rejection. '
                                             'test_svg_rendering.py real-crash-tokens-retained '
                                             'isolates the C4 comparator and kills this narrowing.')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(rows, indent=2)+'\n')
        normal = [r for r in rows if 'mutant' not in r]
        mutants = [r for r in rows if 'mutant' in r]
        print(f'Controls: {sum(r["passed"] for r in normal)}/{len(normal)}; '
              f'mutants killed: {sum(r["killed"] for r in mutants)}/{len(mutants)}', flush=True)
        return 0 if rows and all(r['passed'] for r in normal) and all(
            r['killed'] or r.get('survivor_bound') for r in mutants) else 1


if __name__ == '__main__':
    raise SystemExit(main())
