import os
import json
import re

import hermes.factory
from hermes.grammar import NonTerminal
from hermes.hermes_parser import parse, lex

base_dir = os.path.join(os.path.dirname(__file__), 'cases/grammar/')
grammars_dir = os.path.join(os.path.dirname(__file__), 'grammars/')

def get_grammar(directory, name='grammar.zgr'):
    with open(os.path.join(directory, name)) as fp:
        return hermes.factory.parse(fp.read(), 'grammar')

def test_all():
    for root, _, files in os.walk(grammars_dir):
        for filename in files:
            if filename.endswith('.zgr'):
                subdir = os.path.join(base_dir, root.replace(grammars_dir, ''), re.match(r'(.*?)\.zgr$', filename).group(1))
                if not os.path.exists(subdir):
                    os.makedirs(subdir)
                grammar_symlink = os.path.join(subdir, 'grammar.zgr')
                if not os.path.exists(grammar_symlink):
                    os.symlink(os.path.relpath(os.path.join(root, filename), subdir), grammar_symlink)
    for test_dir, dirs, files in os.walk(base_dir):
        if 'grammar.zgr' not in files:
            continue
        grammar_path = os.path.join(test_dir, 'grammar.zgr')
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
                    grammar_first_sets = json.loads(fp.read())
                    for nonterminal, terminals in grammar_first_sets.items():
                        yield first_sets, test_dir, nonterminal, terminals
                with open(follow_sets_path) as fp:
                    grammar_follow_sets = json.loads(fp.read())
                    for nonterminal, terminals in grammar_follow_sets.items():
                        yield follow_sets, test_dir, nonterminal, terminals

def conflicts_to_string(conflicts):
    return '\n'.join(map(str, conflicts))

def write_sets(sets, output_path):
    json_sets = dict()
    for k,v in sets.items():
        if isinstance(k, NonTerminal):
            json_sets[str(k)] = list(map(lambda x: str(x), v))
    with open(output_path, 'w') as fp:
        fp.write(json.dumps(json_sets, indent=4))

def compare(test_dir, filename, actual):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    expected_file = os.path.join(test_dir, filename)
    if not os.path.isfile(expected_file):
      with open(expected_file, 'w') as fp:
        fp.write(actual)
    with open(expected_file) as fp:
      expected = fp.read()
    assert expected == actual

def tokens(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    with open(grammar_file) as fp:
        actual = lex(fp.read(), 'grammar.zgr').json()
    compare(test_dir, 'tokens', actual)

def parse_tree(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    with open(grammar_file) as fp:
        tree = parse(lex(fp.read(), 'grammar.zgr'))
    actual = str(tree.dumps(indent=2))
    compare(test_dir, 'parse_tree', actual)

def ast(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    with open(grammar_file) as fp:
        tree = parse(lex(fp.read(), 'grammar.zgr'))
    actual = str(tree.toAst().dumps(indent=2))
    compare(test_dir, 'ast', actual)

def first_sets(test_dir, nonterminal, terminals):
    grammar = get_grammar(test_dir)
    grammar_first_sets = {str(k): [str(v1) for v1 in v] for k, v in grammar.first_sets.items()}
    assert len(grammar_first_sets[nonterminal]) == len(terminals)
    for terminal in terminals:
        assert str(terminal) in grammar_first_sets[nonterminal]

def follow_sets(test_dir, nonterminal, terminals):
    grammar = get_grammar(test_dir)
    grammar_follow_sets = {str(k): [str(v1) for v1 in v] for k, v in grammar.follow_sets.items()}
    assert len(grammar_follow_sets[nonterminal]) == len(terminals)
    for terminal in terminals:
        assert str(terminal) in grammar_follow_sets[nonterminal]

def conflicts(test_dir):
    conflicts_file = os.path.join(test_dir, 'conflicts')
    grammar = get_grammar(test_dir)
    assert os.path.exists(conflicts_file)
    with open(conflicts_file, encoding='utf-8') as fp:
        expected = fp.read()
    assert expected == conflicts_to_string(grammar.conflicts)
