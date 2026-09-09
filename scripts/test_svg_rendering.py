#!/usr/bin/env python3
"""Exercise the public SVG comparator with real pinned renderer error output.

The crash case invokes the pinned PlantUML JAR directly through an
explicitly resolved Java runtime instead of the ambient ``plantuml``
wrapper: distributor wrappers (e.g. Homebrew) assign their own
``GRAPHVIZ_DOT`` before Java starts, so a ``GRAPHVIZ_DOT`` failure
injection exported only to the wrapper child never reaches PlantUML and
the "crash" SVG is silently a successful render. Direct JAR invocation
uses the same pinned bytes (workflow SHA) and preserves the injection
at the real renderer boundary.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CRASH_MARKERS = ('has crashed.', 'An error has occurred!')


def workflow_pin(name):
    """Read a pinned literal from the local-only CI workflow."""
    workflow = (ROOT / '.github/workflows/validate.yml').read_text()
    match = re.search(r'%s="([^"]+)"' % re.escape(name), workflow)
    if not match:
        raise SystemExit(f'cannot resolve {name} from .github/workflows/validate.yml')
    return match.group(1)


def resolve_plantuml_jar(expected_sha):
    """Resolve the pinned PlantUML JAR without executing a wrapper.

    Order follows the repository publication-gate convention: an explicit
    PUBLICATION_PLANTUML override, then the CI pin location, then the
    ``-jar`` target parsed out of the installed ``plantuml`` wrapper text
    (derived, never a hardcoded distributor cellar path). Fails clearly
    when no pinned-bytes candidate exists.
    """
    candidates = []
    override = os.environ.get('PUBLICATION_PLANTUML')
    if override:
        candidates.append(Path(override))
    candidates.append(Path(f'/opt/plantuml-{workflow_pin("PLANTUML_VERSION")}.jar'))
    wrapper = shutil.which('plantuml')
    if wrapper:
        try:
            text = Path(wrapper).read_text()
        except OSError:
            text = ''
        match = re.search(r'-jar\s+(\S+)', text)
        if match:
            candidates.append(Path(match.group(1).strip('"\'')))
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != expected_sha:
                raise SystemExit(
                    f'pinned PlantUML mismatch: {candidate} sha256:{digest} '
                    f'differs from workflow pin sha256:{expected_sha}')
            return candidate
    searched = ', '.join(str(c) for c in candidates) or '(no candidates)'
    raise SystemExit(f'cannot resolve pinned PlantUML JAR; searched: {searched}')


def resolve_java():
    """Resolve an explicit Java executable (JAVA_HOME pin wins)."""
    pinned = os.environ.get('JAVA_HOME')
    if pinned:
        candidate = Path(pinned) / 'bin/java'
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise SystemExit(f'JAVA_HOME does not resolve to an executable java: {candidate}')
    found = shutil.which('java')
    if found:
        return Path(found)
    raise SystemExit('cannot resolve a java runtime for the pinned PlantUML JAR')


def inspect_wrapper():
    """Record whether the ambient plantuml wrapper overrides GRAPHVIZ_DOT.

    Diagnostic evidence only: it explains why failure injection must cross
    the real renderer boundary instead of the wrapper. Never gates.
    """
    wrapper = shutil.which('plantuml')
    if not wrapper:
        return dict(wrapper=None, overrides_graphviz_dot=None)
    try:
        text = Path(wrapper).read_text()
    except OSError as error:
        return dict(wrapper=wrapper, overrides_graphviz_dot=None, read_error=str(error))
    match = re.search(r'GRAPHVIZ_DOT="([^"]*)"', text) or re.search(r"GRAPHVIZ_DOT='([^']*)'", text)
    if not match:
        match = re.search(r'GRAPHVIZ_DOT=(\S+)', text)
    return dict(wrapper=wrapper,
                overrides_graphviz_dot=match.group(1) if match else None)


def render(jar, java, source, graphviz_dot):
    """Render one diagram through the real pinned renderer."""
    return subprocess.run([str(java), '-Djava.awt.headless=true',
                           '-jar', str(jar), '-tsvg', str(source)],
                          env=dict(os.environ, GRAPHVIZ_DOT=graphviz_dot),
                          capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    expected_sha = workflow_pin('PLANTUML_SHA256')
    expected_version = workflow_pin('PLANTUML_VERSION')
    jar = resolve_plantuml_jar(expected_sha)
    java = resolve_java()
    java_version = subprocess.run([str(java), '-version'], capture_output=True, text=True)
    renderer = dict(jar=str(jar), sha256=expected_sha,
                    plantuml_version=expected_version,
                    java=str(java), java_version_stderr=java_version.stderr.strip())
    failing_dot = shutil.which('false')
    if not failing_dot:
        raise SystemExit('cannot resolve a failing dot for crash injection (no false on PATH)')
    real_dot = shutil.which('dot')
    if not real_dot:
        raise SystemExit('missing publication prerequisite: dot')
    wrapper = inspect_wrapper()
    rows = []

    def write_report():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(rows, indent=2)+'\n')

    with tempfile.TemporaryDirectory(prefix='svg-render-controls-') as temporary:
        base = Path(temporary)
        repo = base/'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', '__pycache__'))
        original = (repo/'scripts/validate_spec.py').read_text()
        source = base/'structurizr-SystemContext.puml'
        shutil.copyfile(ROOT/'diagrams/c4'/source.name, source)
        crashed = render(jar, java, source, failing_dot)
        svg = source.with_suffix('.svg')
        try:
            text = svg.read_text()
        except OSError as error:
            rows.append(dict(test='real-graphviz-crash-render', exit=crashed.returncode,
                             passed=False, stdout=crashed.stdout, stderr=crashed.stderr,
                             renderer=renderer, wrapper=wrapper, failing_dot=failing_dot,
                             setup_error=f'rendered SVG unreadable: {error}',
                             bound='Malformed setup must never count as a behavioral kill'))
            args.report.parent.mkdir(parents=True, exist_ok=True)
            write_report()
            print(f'Controls: 0/{len(rows)} (renderer setup failure; evidence preserved)')
            return 1
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.with_suffix('.crash.svg').write_text(text)
        committed = repo/'diagrams/artefacts/structurizr-SystemContext.svg'
        baseline = committed.read_text()
        crash_ok = (crashed.returncode == 0 and all(marker in text for marker in CRASH_MARKERS))
        metadata_ok = True
        for token in [r'<\?plantuml-src [^?]+\?>', r'<\?plantuml [^?]+\?>']:
            rendered = re.search(token, text)
            committed_token = re.search(token, baseline)
            if not rendered or not committed_token or rendered[0] != committed_token[0]:
                metadata_ok = False
        rows.append(dict(test='real-graphviz-crash-render', exit=crashed.returncode,
                         passed=crash_ok and metadata_ok,
                         stdout=crashed.stdout, stderr=crashed.stderr,
                         renderer=renderer, wrapper=wrapper, failing_dot=failing_dot,
                         crash_markers_present={m: (m in text) for m in CRASH_MARKERS},
                         metadata_preserved=metadata_ok,
                         bound='Actual renderer exits zero with an error image; this is not successful rendering'))
        if not (crash_ok and metadata_ok):
            rows.append(dict(test='crash-precondition', passed=False,
                             renderer=renderer, wrapper=wrapper,
                             detail='real renderer crash injection did not produce crash markers '
                                    'with preserved source metadata; dependent cases not constructed '
                                    'so malformed setup cannot count as a behavioral kill'))
            write_report()
            print(f'Controls: {sum(r["passed"] for r in rows)}/{len(rows)} (crash precondition failed; evidence preserved)')
            return 1
        legit_source = base/'legit-SystemContext.puml'
        shutil.copyfile(source, legit_source)
        legit = render(jar, java, legit_source, real_dot)
        legit_svg = legit_source.with_suffix('.svg')
        try:
            legit_text = legit_svg.read_text()
        except OSError as error:
            rows.append(dict(test='legitimate-direct-render-succeeds', passed=False,
                             renderer=renderer, real_dot=real_dot,
                             setup_error=f'rendered SVG unreadable: {error}'))
            write_report()
            print(f'Controls: {sum(r["passed"] for r in rows)}/{len(rows)} (legitimate render setup failure)')
            return 1
        legit_ok = (legit.returncode == 0
                    and not re.search(r'PlantUML \(.*?\) has crashed\.', legit_text)
                    and 'An error has occurred!' not in legit_text
                    and 'data-diagram-type="ERROR"' not in legit_text
                    and bool(legit_text))
        legit_metadata = True
        for token in [r'<\?plantuml-src [^?]+\?>', r'<\?plantuml [^?]+\?>']:
            rendered = re.search(token, legit_text)
            committed_token = re.search(token, baseline)
            if not rendered or not committed_token or rendered[0] != committed_token[0]:
                legit_metadata = False
        rows.append(dict(test='legitimate-direct-render-succeeds', exit=legit.returncode,
                         passed=legit_ok and legit_metadata,
                         stdout=legit.stdout, stderr=legit.stderr,
                         renderer=renderer, real_dot=real_dot,
                         bound='The real renderer without injection must succeed with '
                               'unmodified embedded source metadata; a fake error image would fail here'))

        def run(name, content, expected, marker, mutant=None):
            svg.write_text(content)
            result = subprocess.run([sys.executable, '-B', 'scripts/validate_spec.py',
                                     '--compare-svg', str(committed), str(svg)],
                                    cwd=repo, capture_output=True, text=True)
            passed = result.returncode == expected and marker in result.stdout
            row = dict(test=name, exit=result.returncode, expected_exit=expected,
                       passed=passed, stdout=result.stdout, stderr=result.stderr)
            if mutant:
                row.update(mutant=mutant, killed=not passed,
                           named_failing_test=name if not passed else None)
            rows.append(row)
            print(f'{name}: exit={result.returncode}; assertion={passed}; mutant={mutant}', flush=True)

        cases = [
            ('fresh-svg', baseline, 0, 'embedded source metadata fresh'),
            ('real-crash-tokens-retained', text, 1, 'PlantUML render failure'),
            ('malformed-svg-tokens-retained', baseline.replace('</svg>', ''), 1, 'SVG is malformed'),
            ('error-type-tokens-retained', baseline.replace('data-diagram-type="DESCRIPTION"', 'data-diagram-type="ERROR"'), 1, 'PlantUML render failure'),
            ('crash-message-only', re.sub(r'<text[^>]*>An error has occurred!</text>', '', text), 1, 'PlantUML render failure'),
            ('error-message-only', re.sub(r'<text[^>]*>PlantUML .*? has crashed.</text>', '', text), 1, 'PlantUML render failure'),
            ('missing-source', re.sub(r'<\?plantuml-src [^?]+\?>', '', baseline), 1, 'missing PlantUML source'),
            ('missing-version', re.sub(r'<\?plantuml [^?]+\?>', '', baseline), 1, 'missing PlantUML renderer'),
            ('wrong-version', baseline.replace('<?plantuml 1.2026.6?>', '<?plantuml 1.2026.5?>'), 1, 'renderer version mismatch'),
            ('stale-source', re.sub(r'<\?plantuml-src [^?]+\?>', '<?plantuml-src changed?>', baseline), 1, 'embedded PlantUML source metadata differs'),
        ]
        for case in cases:
            run(*case)
        mutants = [
            ('crash-only-handwritten', 'real-crash-tokens-retained',
             'errors.append(f"{label} SVG contains a PlantUML render failure")',
             'if not committed.name.startswith("structurizr-"): errors.append(f"{label} SVG contains a PlantUML render failure")'),
            ('malformed-only-committed', 'malformed-svg-tokens-retained',
             'errors.append(f"{label} SVG is malformed: {error}")',
             'if label == "committed": errors.append(f"{label} SVG is malformed: {error}")'),
            ('error-type-description-exemption', 'error-type-tokens-retained',
             "svg.get('data-diagram-type') == 'ERROR'", "svg.get('data-diagram-type') == 'ERROR' and 'SystemContext' not in committed.name"),
            ('crash-message-exemption', 'crash-message-only',
             "re.search(r'PlantUML \\(.*?\\) has crashed\\.', rendered_text)",
             "re.search(r'PlantUML \\(.*?\\) has crashed\\.', rendered_text) and 'SystemContext' not in committed.name"),
            ('error-message-exemption', 'error-message-only',
             "'An error has occurred!' in rendered_text", "'An error has occurred!' in rendered_text and 'SystemContext' not in committed.name"),
        ]
        for name, witness, before, after in mutants:
            assert original.count(before) == 1, name
            (repo/'scripts/validate_spec.py').write_text(original.replace(before, after))
            run(*next(c for c in cases if c[0] == witness), mutant=name)
            (repo/'scripts/validate_spec.py').write_text(original)
    write_report()
    controls = [r for r in rows if 'mutant' not in r]
    mutants = [r for r in rows if 'mutant' in r]
    print(f'Controls: {sum(r["passed"] for r in controls)}/{len(controls)}; mutants: {sum(r["killed"] for r in mutants)}/{len(mutants)}')
    return 0 if all(r['passed'] for r in controls) and all(r['killed'] for r in mutants) else 1


if __name__ == '__main__':
    raise SystemExit(main())
