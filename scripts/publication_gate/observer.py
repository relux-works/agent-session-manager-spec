"""Trusted local launch observer. Private ledger is owned by the controller.

Not an authenticator for attacker-owned executables, kernel, or concurrent writes.
"""
import fcntl, glob, hashlib, json, os, pathlib, subprocess, sys

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def main(config, tool, executable, sink):
    cfg=json.loads(pathlib.Path(config).read_text()); args=sys.argv[1:]
    scope=os.environ.get('INVOCATION_SCOPE','')
    if tool=='python3':
        scope='compare:'+pathlib.Path(args[args.index('--compare-svg')+1]).name if '--compare-svg' in args else 'contracts'
    elif tool=='structurizr-cli': scope='structurizr:'+args[0]
    elif tool=='plantuml':
        names=[pathlib.Path(a).name for a in args if a.endswith('.puml')]
        scope='render:c4' if all(n.startswith('structurizr-') for n in names) else 'render:handwritten'
    key=scope+'/'+tool
    if tool=='dot': key+=':'+('probe' if args==['-V'] else 'render')
    with open(cfg['counter'],'a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX); f.seek(0); counts=json.loads(f.read() or '{}')
        n=counts.get(key,0)+1; counts[key]=n
        f.seek(0); f.truncate(); json.dump(counts,f)
    key+=f'#{n}'
    target=pathlib.Path(executable).resolve(strict=True)
    mutation=cfg.get('mutation',{})
    applied=mutation.get('id')==key
    if applied and mutation['kind']=='substitute': target=pathlib.Path(mutation['target']).resolve(strict=True)
    if applied and mutation['kind']=='jar-substitute':
        if '-jar' in args: args[args.index('-jar')+1]=mutation['target']
        else:
            i=args.index('-cp')+1
            expanded=[]
            for entry in args[i].split(os.pathsep): expanded.extend(sorted(glob.glob(entry)) if '*' in entry else [entry])
            index=next(i for i,p in enumerate(expanded) if p.endswith('.jar'))
            expanded[index]=mutation['target']; args[i]=os.pathsep.join(expanded)
    paths=[]
    if tool=='java':
        if '-jar' in args: paths=[args[args.index('-jar')+1]]
        elif '-cp' in args:
            for entry in args[args.index('-cp')+1].split(os.pathsep): paths.extend(p for p in sorted(glob.glob(entry)) if p.endswith('.jar'))
    artifacts={str(pathlib.Path(p).resolve(strict=True)):sha(p) for p in paths}
    env=dict(os.environ,INVOCATION_SCOPE=scope)
    p=subprocess.Popen([str(target),*args],env=env)
    result=p.wait()
    record=dict(id=key,tool=tool,scope=scope,target=str(target),sha256=sha(target),argv=args,artifacts=artifacts,pid=p.pid,exit=result,applied=applied)
    # Controller-owned private evidence and publication-facing receipt are separate.
    for path in [cfg['ledger'],sink]:
        with open(path,'a') as f:
            fcntl.flock(f,fcntl.LOCK_EX); f.write(json.dumps(record)+'\n')
    sys.exit(result)
