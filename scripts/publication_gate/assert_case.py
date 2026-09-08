#!/usr/bin/env python3
"""Named behavioral assertion; command exits one when its witness defeats a gate."""
import argparse,json,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--expected',type=int,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
r=subprocess.run(a.command,capture_output=True,text=True)
print(json.dumps(dict(test=a.name,gate_argv=a.command,gate_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,passed=r.returncode==a.expected)))
sys.exit(0 if r.returncode==a.expected else 1)
