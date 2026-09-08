"""Independent finite census from pinned shell call sites and diagram source.

Never derive expected members by reading evaluator code or observed records.
"""
import hashlib,json,re
from pathlib import Path

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def derive(root):
    root=Path(root); shell=(root/'run_validation.sh').read_text()
    operations=[]; rows=[]
    def add(scope,tool,line,arguments=None,count=1):
        for n in range(1,count+1):
            rows.append(dict(id=f'{scope}/{tool}#{n}',scope=scope,tool=tool.split(':')[0],site=f'run_validation.sh:{line}',arguments=arguments,conditional=tool=='dot:probe'))
    c4=sorted((root/'diagrams/c4').glob('structurizr-*.puml'))
    handwritten=sorted((root/'diagrams/plantuml').glob('*.puml'))
    svg=sorted((root/'diagrams/artefacts').glob('*.svg'))
    assert c4 and handwritten and svg
    assert {p.stem for p in c4+handwritten}=={p.stem for p in svg}, 'render/source scope mismatch'
    for ln,text in enumerate(shell.splitlines(),1):
        text=text.strip()
        if text=='./scripts/validate_spec.py':
            operations.append(dict(scope='contracts',site=ln)); add('contracts','python3',ln,['./scripts/validate_spec.py'])
        elif text.startswith('structurizr-cli '):
            operation=text.split()[1]; scope='structurizr:'+operation
            assert operation in ('validate','export'), 'unclassified Structurizr operation'
            operations.append(dict(scope=scope,site=ln)); add(scope,'structurizr-cli',ln); add(scope,'java',ln)
        elif text.startswith('plantuml '):
            scope='render:c4' if '"$TEMP_DIR/c4/"' in text else 'render:handwritten'
            inputs=c4 if scope=='render:c4' else handwritten
            operations.append(dict(scope=scope,site=ln,inputs=[str(p.relative_to(root)) for p in inputs]))
            add(scope,'plantuml',ln); add(scope,'java',ln)
            # Pinned source has standard Graphviz diagrams and native sequences.
            # Reject unclassified sources instead of silently excluding them.
            graph=[]; native=[]
            for p in inputs:
                content=p.read_text()
                if re.search(r'^participant\s',content,re.M): native.append(p.name)
                elif re.search(r'^(?:rectangle|component|node|package|state)\s',content,re.M): graph.append(p.name)
                else: raise ValueError('unknown renderer family: '+str(p))
            operations[-1].update(graphviz=graph,native_sequence=native)
            # Each Graphviz diagram requires -Tsvg. Version probes are conditional
            # (observed 4/5 for handwritten); bind their actual launch census.
            add(scope,'dot:probe',ln,['-V'],len(graph)); add(scope,'dot:render',ln,['-Tsvg'],len(graph))
        elif text.startswith('if ! ./scripts/validate_spec.py --compare-svg'):
            for p in svg:
                scope='compare:'+p.name; operations.append(dict(scope=scope,site=ln)); add(scope,'python3',ln)
    assert len(operations)==5+len(svg), 'shell operation census changed'
    assert len({r['id'] for r in rows})==len(rows)
    return dict(schema=1,source_hashes={str(p.relative_to(root)):digest(p) for p in sorted(root.rglob('*')) if p.is_file() and not {'.git', '.temp', '.task-board', '__pycache__'} & set(p.relative_to(root).parts)},operations=operations,invocations=rows,exclusions=['System support shell/env and file utilities (mktemp, mkdir, ls, cp, rm, basename, sort, diff, cat, tr); not selected documentation tool roles.', 'Workflow installation/download and version preflights; disabled hosted workflow is not executed.', 'Python imports, JVM class loading/native libraries: JAR evidence binds complete supplied classpath, not individual loaded classes.', 'Four native sequence diagrams do not invoke Graphviz; their PlantUML/Java render scope remains required.'])


def bind_census(inventory, census):
    """Required rendering is source-derived; optional probes are launch-derived.

    Counter events are controller-owned, recorded before execution, independently
    of receipt emission. Missing/malformed counter files are never absence.
    """
    import copy
    if not isinstance(census,dict) or any(type(n) is not int or n<0 for n in census.values()):
        raise ValueError('malformed launch census')
    valid={r['id'].rsplit('#',1)[0] for r in inventory['invocations']}
    if set(census)-valid: raise ValueError('unknown launch census scope')
    conditional=[r for r in inventory['invocations'] if r.get('conditional')]
    for key in {r['id'].rsplit('#',1)[0] for r in conditional}:
        limit=sum(r['id'].rsplit('#',1)[0]==key for r in conditional)
        if census.get(key,0)>limit: raise ValueError('probe census exceeds pinned source scope')
    result=copy.deepcopy(inventory)
    result['invocations']=[r for r in inventory['invocations'] if not r.get('conditional') or int(r['id'].rsplit('#',1)[1])<=census.get(r['id'].rsplit('#',1)[0],0)]
    result['required_executable_count']=sum(not r.get('conditional') for r in inventory['invocations'])
    result['conditional_probe_count']=len(result['invocations'])-result['required_executable_count']
    return result
