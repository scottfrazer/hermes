import os
import json
import re

import hermes.factory
from hermes.grammar import NonTerminal
from hermes.hermes_parser import parse, lex

base_dir = os.path.join(os.path.dirname(__file__), 'cases/grammar/')
grammars_dir = os.path.join(os.path.dirname(__file__), 'grammars/')

def get_grammar(directory, name='grammar.hgr'):
    with open(os.path.join(directory, name)) as fp:
        return hermes.factory.parse(fp.read(), 'grammar')

def test_all():
    for root, _, files in os.walk(grammars_dir):
        for filename in files:
            if filename.endswith('.hgr'):
                subdir = os.path.join(base_dir, root.replace(grammars_dir, ''), re.match(r'(.*?)\.hgr$', filename).group(1))
                if not os.path.exists(subdir):
                    os.makedirs(subdir)
                grammar_symlink = os.path.join(subdir, 'grammar.hgr')
                if not os.path.exists(grammar_symlink):
                    os.symlink(os.path.relpath(os.path.join(root, filename), subdir), grammar_symlink)
    for test_dir, dirs, files in os.walk(base_dir):
        if 'grammar.hgr' not in files:
            continue
        grammar_path = os.path.join(test_dir, 'grammar.hgr')
        first_sets_path = os.path.join(test_dir, 'first.json')
        follow_sets_path = os.path.join(test_dir, 'follow.json')
        conflicts_path = os.path.join(test_dir, 'conflicts')

        if os.path.isfile(grammar_path):
            if os.path.isdir(test_dir):
                yield tokens, test_dir
                yield parse_tree, test_dir
                yield ast, test_dir

            with open(grammar_path) as fp:
                grammar = hermes.factory.parse(fp.read(), 'grammar')

            if grammar.conflicts:
                if not os.path.exists(conflicts_path) and (not os.path.exists(first_sets_path) or not os.path.exists(follow_sets_path)):
                    with open(conflicts_path, 'w') as fp:
                        fp.write(conflicts_to_string(grammar.conflicts))
                yield conflicts, test_dir
            else:
                if not os.path.isfile(first_sets_path):
                    write_sets(grammar.first_sets, first_sets_path)
                if not os.path.isfile(follow_sets_path):
                    write_sets(grammar.follow_sets, follow_sets_path)
                with open(first_sets_path) as fp:
                    expected_first_sets = string2sets(fp.read())
                    for nonterminal, terminals in expected_first_sets.items():
                        yield first_sets, test_dir, nonterminal, terminals
                with open(follow_sets_path) as fp:
                    expected_follow_sets = string2sets(fp.read())
                    for nonterminal, terminals in expected_follow_sets.items():
                        yield follow_sets, test_dir, nonterminal, terminals

def conflicts_to_string(conflicts):
    return '\n'.join(sorted(map(str, conflicts)))

def sets2string(sets):
    string = ''
    for k in sorted(sets.keys(), key=str):
        string += '{} -> {}\n'.format(k, ', '.join([str(x) for x in sorted(sets[k], key=str)]))
    return string

def string2sets(string):
    d = dict()
    for line in string.split('\n'):
        if len(line) == 0: continue
        (nt, terminals) = line.split(' -> ')
        terminals = terminals.split(', ')
        d[nt] = [t for t in terminals if len(t)]
    return d

def write_sets(sets, output_path):
    with open(output_path, 'w') as fp:
        fp.write(sets2string(sets))

def compare(test_dir, filename, actual):
    grammar_file = os.path.join(test_dir, 'grammar.hgr')
    expected_file = os.path.join(test_dir, filename)
    if not os.path.isfile(expected_file):
      with open(expected_file, 'w') as fp:
        fp.write(actual)
    with open(expected_file) as fp:
      expected = fp.read()
    assert expected == actual

def tokens(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.hgr')
    with open(grammar_file) as fp:
        actual = '\n'.join([str(t) for t in lex(fp.read(), 'grammar.hgr')])
    compare(test_dir, 'tokens', actual)

def parse_tree(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.hgr')
    with open(grammar_file) as fp:
        tree = parse(lex(fp.read(), 'grammar.hgr'))
    actual = str(tree.dumps(indent=2))
    compare(test_dir, 'parse_tree', actual)

def ast(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.hgr')
    with open(grammar_file) as fp:
        tree = parse(lex(fp.read(), 'grammar.hgr'))
    actual = str(tree.ast().dumps(indent=2))
    compare(test_dir, 'ast', actual)

def first_sets(test_dir, nonterminal, expected_terminals):
    grammar = get_grammar(test_dir)
    actual_first_set = None
    for k, v in grammar.first_sets.items():
        if str(k) == str(nonterminal):
            actual_first_set = [str(v1) for v1 in v]
    assert actual_first_set is not None
    assert len(actual_first_set) == len(expected_terminals)
    for terminal in expected_terminals:
        assert str(terminal) in actual_first_set

def follow_sets(test_dir, nonterminal, expected_terminals):
    grammar = get_grammar(test_dir)
    actual_follow_set = None
    for k, v in grammar.follow_sets.items():
        if str(k) == str(nonterminal):
            actual_follow_set = [str(v1) for v1 in v]
    assert actual_follow_set is not None
    assert len(actual_follow_set) == len(expected_terminals)
    for terminal in expected_terminals:
        assert str(terminal) in actual_follow_set

def conflicts(test_dir):
    conflicts_file = os.path.join(test_dir, 'conflicts')
    grammar = get_grammar(test_dir)
    assert os.path.exists(conflicts_file)
    with open(conflicts_file, encoding='utf-8') as fp:
        expected = fp.read()
    assert expected == conflicts_to_string(grammar.conflicts)
