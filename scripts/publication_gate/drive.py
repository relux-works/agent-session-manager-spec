#!/usr/bin/env python3
"""Run the source public harness in a disposable copy, attach trusted observer.

Usage: python3 drive.py --source ../source --out ../runs/path --branch path
"""
import argparse,hashlib,importlib.util,json,os,re,shlex,shutil,subprocess,sys
from pathlib import Path
from inventory import derive,digest,bind_census
from execution import finalize
HERE=Path(__file__).resolve().parent
JAVA26=Path(os.environ.get('PUBLICATION_JAVA', os.environ.get('JAVA_HOME', '/missing-pinned-java')))
JAVA11=Path(os.environ.get('PUBLICATION_JAVA11', '/missing-java11'))
JAVA25=Path(os.environ.get('PUBLICATION_JAVA25', '/missing-compatible-java25'))
STRUCT=Path(os.environ.get('PUBLICATION_STRUCTURIZR', '/opt/structurizr-cli-2025.11.09/structurizr.sh'))
PLANT=Path(os.environ.get('PUBLICATION_PLANTUML', '/opt/plantuml-1.2026.6.jar'))
DOT=Path(os.environ.get('PUBLICATION_DOT', shutil.which('dot') or '/missing-dot')).resolve()

def child(config):
    cfg=json.loads(Path(config).read_text()); source=Path(cfg['repo'])
    sys.path.insert(0,str(source/'scripts'))
    spec=importlib.util.spec_from_file_location('public_host',source/'scripts/test_host_channel.py'); host=importlib.util.module_from_spec(spec); spec.loader.exec_module(host)
    def traced(bin_dir,command,executable):
        wrapper=bin_dir/command
        wrapper.write_text('#!'+sys.executable+'\nimport sys\nsys.path.insert(0,'+repr(str(HERE))+')\nfrom observer import main\nmain('+repr(str(config))+','+repr(command)+','+repr(executable)+','+repr(str(bin_dir/'executions.jsonl'))+')\n')
        wrapper.chmod(0o755)
    host.traced_tool=traced
    # Default PATH deliberately exposes actual Java11, as original reviewer.
    os.defpath=cfg['default_path']
    sys.argv=['scripts/test_host_channel.py','--group','environment']
    os.chdir(source)
    return host.main()

def run(args):
    out=args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    source=args.source.resolve(); repo=out/'repo'; shutil.copytree(source,repo,ignore=shutil.ignore_patterns('.git','.temp','.task-board','__pycache__'))
    workflow=(source/'.github/workflows/validate.yml').read_text()
    pin=re.search(r"java-version: '([^']+)'",workflow)[1]
    version=subprocess.run([str(JAVA26/'bin/java'),'-version'],capture_output=True,text=True)
    (out/'java-version.json').write_text(json.dumps(dict(argv=[str(JAVA26/'bin/java'),'-version'],exit=version.returncode,stdout=version.stdout,stderr=version.stderr),indent=2))
    if version.returncode or 'version "'+pin+'"' not in version.stderr or 'Temurin' not in version.stderr:
        raise ValueError('selected Java does not match workflow Temurin pin')
    if digest(PLANT)!=re.search(r'PLANTUML_SHA256="([0-9a-f]+)"',workflow)[1]:
        raise ValueError('selected PlantUML differs from workflow digest')
    inventory=derive(source)
    (out/'inventory.json').write_text(json.dumps(inventory,indent=2))
    selected=out/'selected'; selected.mkdir(); fallback=out/'fallback'; fallback.mkdir()
    (fallback/'java').symlink_to((JAVA11 if JAVA11.is_dir() else JAVA26)/'bin/java')
    for tool,target in [('python3',Path(sys.executable)),('java',JAVA26/'bin/java'),('dot',DOT)]: (selected/tool).symlink_to(target)
    for tool,text in [('structurizr-cli','exec '+shlex.quote(str(STRUCT))+' "$@"'),('plantuml','exec java -Djava.awt.headless=true -jar '+shlex.quote(str(PLANT))+' "$@"')]:
        if tool=='plantuml' and args.control=='serial-render': text=text.replace(' \"$@\"',' -nbthread 1 \"$@\"')
        p=selected/tool; p.write_text('#!/bin/bash\n'+text+'\n'); p.chmod(0o755)
    expected={t:dict(target=str((selected/t).resolve()),sha256=digest((selected/t).resolve())) for t in ['python3','java','dot','structurizr-cli','plantuml']}
    expected['structurizr_jars']={str(p.resolve()):digest(p) for p in sorted((STRUCT.parent/'lib').glob('*.jar'))}
    expected['plantuml_jars']={str(PLANT.resolve()):digest(PLANT)}
    cfg=dict(repo=str(repo),ledger=str(out/'private.jsonl'),counter=str(out/'counter.json'),default_path=str(fallback)+':/usr/bin:/bin')
    if args.kind:
        assert args.target_id in {r['id'] for r in inventory['invocations']}
        role=next(r for r in inventory['invocations'] if r['id']==args.target_id)
        cfg['mutation']=dict(id=args.target_id,kind=args.kind)
        if args.kind=='substitute':
            if role['tool']=='java': target=JAVA25/'bin/java'
            else:
                target=out/'compatible-alternate'; target.write_text('#!/bin/bash\nexec '+shlex.quote(expected[role['tool']]['target'])+' "$@"\n'); target.chmod(0o755)
            cfg['mutation']['target']=str(target)
        elif args.kind=='jar-substitute':
            assert role['tool']=='java'
            original=next(iter(expected['structurizr_jars'])) if role['scope'].startswith('structurizr:') else str(PLANT)
            target=out/Path(original).name; shutil.copyfile(original,target); cfg['mutation']['target']=str(target)
    if args.control=='mixed-export':
        observer=out/'export-observer'; observer.mkdir()
        java=observer/'java'
        java.write_text('#!'+sys.executable+'\nimport os,sys,json,hashlib\nfrom pathlib import Path\ntarget=Path('+repr(str(JAVA25/'bin/java'))+').resolve()\nr=dict(target=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),argv=sys.argv[1:])\nwith open('+repr(str(out/'independent-export.jsonl'))+',"a") as f:f.write(json.dumps(r)+"\\n")\nos.execv(str(target),[str(target),*sys.argv[1:]])\n')
        java.chmod(0o755)
        path=repo/'run_validation.sh'; text=path.read_text(); anchor='structurizr-cli export -w'; assert text.count(anchor)==1
        path.write_text(text.replace(anchor,'PATH='+shlex.quote(str(observer))+':$PATH '+anchor))
    if args.control=='absent-caller':
        p=repo/'scripts/test_host_channel.py'; s=p.read_text(); old="subprocess.run(['./run_validation.sh'],cwd=repo,env=environment,"; assert s.count(old)==1
        p.write_text(s.replace(old,"subprocess.run(['/usr/bin/true'],cwd=repo,env=environment,"))
    env={k:v for k,v in os.environ.items() if k not in ('JAVA_HOME','GRAPHVIZ_DOT','INVOCATION_SCOPE')}
    env['PATH']=str(selected)+':/usr/bin:/bin'
    if args.branch=='home':
        env['JAVA_HOME']=str(JAVA26); (selected/'java').unlink(); (selected/'java').symlink_to((JAVA11 if JAVA11.is_dir() else JAVA26)/'bin/java')
    if args.control=='java11': env['JAVA_HOME']=str(JAVA11)
    if args.control=='f1':
        (selected/'dot').unlink(); (selected/'dot').symlink_to('/usr/bin/false')
    if args.control=='ambient-ax':
        p=selected/'ax'; p.write_text('#!/bin/sh\nexit 99\n'); p.chmod(0o755)
    if args.control=='ambient-dot': env['GRAPHVIZ_DOT']='/usr/bin/false'
    if args.control=='forbidden-ax':
        p=repo/'ax'; p.write_text('#!/bin/sh\nexit 99\n'); p.chmod(0o755)
    (out/'expected.json').write_text(json.dumps(expected,indent=2))
    config=out/'config.json'; config.write_text(json.dumps(cfg,indent=2))
    argv=[sys.executable,'-B',str(HERE/'drive.py'),'--child',str(config)]
    with (out/'public.log').open('w') as f:
        proc=subprocess.run(argv,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150)
    result=finalize(out,inventory,expected,proc.returncode)
    result.update(argv=argv,environment={k:env[k] for k in ['PATH','JAVA_HOME','GRAPHVIZ_DOT'] if k in env},branch=args.branch,kind=args.kind,target_id=args.target_id,control=args.control)
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    return result['gate_exit']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--pinned-java',type=Path,default=JAVA26); p.add_argument('--structurizr',type=Path,default=STRUCT); p.add_argument('--plantuml-jar',type=Path,default=PLANT); p.add_argument('--child',type=Path); p.add_argument('--source',type=Path); p.add_argument('--out',type=Path); p.add_argument('--branch',choices=['path','home'],default='path'); p.add_argument('--kind',choices=['substitute','jar-substitute']); p.add_argument('--target-id'); p.add_argument('--control',choices=['absent-caller','java11','f1','ambient-ax','ambient-dot','forbidden-ax','mixed-export','serial-render'])
    args=p.parse_args()
    JAVA26=args.pinned_java.resolve(); STRUCT=args.structurizr.resolve(); PLANT=args.plantuml_jar.resolve()
    if args.child:sys.exit(child(args.child))
    try:
        code=run(args)
    except Exception as e:
        # A typed refusal preserves failures; it is never a passing control.
        result=dict(schema=2,execution=dict(state='driver_error',error_type=type(e).__name__,detail=str(e)),census=dict(state='not_evaluated',complete_publication=False),refusal='driver_error',gate_exit=1,errors=[type(e).__name__+': '+str(e)])
        if args.out and args.out.is_dir() and not isinstance(e,FileExistsError):
            (args.out/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True);code=1
    sys.exit(code)
