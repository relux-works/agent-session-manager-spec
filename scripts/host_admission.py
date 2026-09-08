"""Interpreter and renderer for the normative policy embedded in SPEC.md.

No TLS implementation and no independently stored admission predicates.
"""
from __future__ import annotations
import json
import re

POLICY = re.compile(r'<!-- host-admission-policy -->\n~~~json\n(.*?)\n~~~\n<!-- /host-admission-policy -->', re.S)
TABLE = re.compile(r'(?<=<!-- host-admission-table -->\n).*?(?=\n<!-- /host-admission-table -->)', re.S)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate member {key}')
        result[key] = value
    return result


def exact(a, b):
    return type(a) is type(b) and (set(a) == set(b) and all(exact(a[k], b[k]) for k in b)
        if isinstance(b, dict) else len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
        if isinstance(b, list) else a == b)


def check_predicate(p, fields):
    if not isinstance(p, dict) or len(p) != 1:
        raise ValueError('predicate must have exactly one operator')
    op, arg = next(iter(p.items()))
    if op == 'eq':
        return
    if op == 'range' and isinstance(arg, list) and len(arg) == 2 and all(type(v) is int for v in arg) and arg[0] <= arg[1]:
        return
    if op == 'in' and isinstance(arg, list) and arg:
        return
    if op in {'equal_field', 'singleton_field'} and isinstance(arg, str) and arg in fields:
        return
    if op == 'uuid7' and arg is True:
        return
    if op == 'all' and isinstance(arg, list) and arg:
        for child in arg:
            check_predicate(child, fields)
        return
    if op == 'when' and isinstance(arg, dict) and set(arg) == {'field', 'in', 'require'} and isinstance(arg['field'], str) and arg['field'] in fields and isinstance(arg['in'], list) and arg['in']:
        check_predicate(arg['require'], fields)
        return
    raise ValueError(f'unsupported or malformed operator {op}')


def read_policy(spec):
    matches = POLICY.findall(spec)
    if len(matches) != 1:
        raise ValueError('exactly one fenced host admission policy required')
    policy = json.loads(matches[0], object_pairs_hook=unique_pairs)
    if not isinstance(policy, dict) or set(policy) != {'format', 'gates'} or policy['format'] != 'ax-host-admission-1' or not isinstance(policy['gates'], dict) or not policy['gates']:
        raise ValueError('closed policy root mismatch')
    for gate, rules in policy['gates'].items():
        if not isinstance(rules, dict) or not rules:
            raise ValueError(f'{gate}: nonempty field predicates required')
        for field, predicate in rules.items():
            if not re.fullmatch('[a-z][a-z_]*', field):
                raise ValueError(f'{gate}: invalid field name')
            check_predicate(predicate, rules)
    return policy


def holds(predicate, value, facts):
    op, arg = next(iter(predicate.items()))
    if op == 'eq':
        return exact(value, arg)
    if op == 'range':
        return type(value) is int and arg[0] <= value <= arg[1]
    if op == 'in':
        return any(exact(value, item) for item in arg)
    if op == 'equal_field':
        return arg in facts and exact(value, facts[arg])
    if op == 'singleton_field':
        return arg in facts and exact(value, [facts[arg]])
    if op == 'uuid7':
        return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value) is not None
    if op == 'all':
        return all(holds(child, value, facts) for child in arg)
    if op == 'when':
        return arg['field'] in facts and (not any(exact(facts[arg['field']], item) for item in arg['in']) or holds(arg['require'], value, facts))
    raise ValueError(f'unsupported operator {op}')


def failures(policy, gate, facts):
    rules = policy['gates'][gate]
    if not isinstance(facts, dict) or set(facts) != set(rules):
        return {'closed-shape'}
    return {field for field, predicate in rules.items() if not holds(predicate, facts[field], facts)}


def admits(policy, gate, facts):
    return not failures(policy, gate, facts)


def describe(p):
    op, arg = next(iter(p.items()))
    literal = lambda v: json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    if op == 'eq': return 'equals ' + literal(arg)
    if op == 'range': return f'is an integer in [{arg[0]}, {arg[1]}]'
    if op == 'in': return 'is one of ' + literal(arg)
    if op == 'equal_field': return 'equals field ' + arg
    if op == 'singleton_field': return 'is exactly [field ' + arg + ']'
    if op == 'uuid7': return 'is a canonical lowercase UUIDv7'
    if op == 'all': return ' AND '.join(describe(child) for child in arg)
    if op == 'when': return f"only when {arg['field']} is in {literal(arg['in'])}: {describe(arg['require'])}"
    raise ValueError(op)


def render_table(policy):
    lines = ['| Obligation | Required on every invocation |', '| --- | --- |']
    for gate, rules in policy['gates'].items():
        for field, predicate in rules.items():
            lines.append(f'| {gate}.{field} | {describe(predicate)} |')
    return '\n'.join(lines)


def replace_policy(spec, policy):
    replacement = '<!-- host-admission-policy -->\n~~~json\n' + json.dumps(policy, indent=2, ensure_ascii=False) + '\n~~~\n<!-- /host-admission-policy -->'
    spec, count = POLICY.subn(lambda _: replacement, spec)
    if count != 1: raise ValueError('missing/duplicate policy')
    return TABLE.sub(lambda _: render_table(policy), spec)
