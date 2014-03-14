import os, json
from nose.plugins.skip import SkipTest
from hermes.GrammarParser import GrammarParser
from hermes.Morpheme import NonTerminal
from hermes.parser.hermes import parse, lex
from hermes.parser.Common import ParseTreePrettyPrintable, AstPrettyPrintable

base_dir = os.path.join(os.path.dirname(__file__), 'cases/grammar')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        grammar_path = os.path.join(test_dir, 'grammar.zgr')
        if os.path.isfile(grammar_path):
            if os.path.isdir(test_dir):
                yield tokens, test_dir
                yield parse_tree, test_dir
                yield ast, test_dir
            
            grammar = GrammarParser().parse('grammar', open(grammar_path))
            if grammar.conflicts:
                conflicts_path = os.path.join(test_dir, 'conflicts')
                if not os.path.exists(conflicts_path):
                    with open(conflicts_path, 'w') as fp:
                        fp.write(conflicts_to_string(grammar.conflicts))
                yield conflicts, test_dir
            else:
                first_sets_path = os.path.join(test_dir, 'first.json')
                follow_sets_path = os.path.join(test_dir, 'follow.json')
                if not os.path.isfile(first_sets_path):
                    write_sets(grammar.first, first_sets_path)
                if not os.path.isfile(follow_sets_path):
                    write_sets(grammar.follow, follow_sets_path)
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
      print("Generated: " + expected_file)
    with open(expected_file) as fp:
      expected = fp.read()
    assert expected == actual

def tokens(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    actual = '\n'.join([str(token) for token in lex(grammar_file)])
    compare(test_dir, 'tokens', actual)

def parse_tree(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    tree = parse(lex(grammar_file))
    actual = str(ParseTreePrettyPrintable(tree))
    compare(test_dir, 'parse_tree', actual)

def ast(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    tree = parse(lex(grammar_file))
    actual = str(AstPrettyPrintable(tree.toAst()))
    compare(test_dir, 'ast', actual)

def first_sets(test_dir, nonterminal, terminals):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    grammar = GrammarParser().parse('grammar', open(grammar_file))
    grammar_first_sets = {str(k): [str(v1) for v1 in v] for k, v in grammar.first.items()}
    assert len(grammar_first_sets[nonterminal]) == len(terminals)
    for terminal in terminals:
        assert str(terminal) in grammar_first_sets[nonterminal]

def follow_sets(test_dir, nonterminal, terminals):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    grammar = GrammarParser().parse('grammar', open(grammar_file))
    grammar_follow_sets = {str(k): [str(v1) for v1 in v] for k, v in grammar.follow.items()}
    assert len(grammar_follow_sets[nonterminal]) == len(terminals)
    for terminal in terminals:
        assert str(terminal) in grammar_follow_sets[nonterminal]

def conflicts(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    conflicts_file = os.path.join(test_dir, 'conflicts')
    grammar = GrammarParser().parse('grammar', open(grammar_file))
    with open(conflicts_file) as fp:
        expected = fp.read()
    assert expected == conflicts_to_string(grammar.conflicts)

