import os
import re
import hermes.test.functions

base_dir = os.path.join(os.path.dirname(__file__), 'cases/parsing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            yield python_parse_tree, test_dir
            yield python_ast, test_dir
            yield c_parse_tree, test_dir
            yield c_ast, test_dir
            yield java_parse_tree, test_dir
            yield java_ast, test_dir
            yield javascript_parse_tree, test_dir
            yield javascript_ast, test_dir

def python_parse_tree(test_dir):
    actual = hermes.test.functions.python_parsetree(test_dir)
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    if not os.path.isfile(parse_tree_file):
        with open(parse_tree_file, 'w') as fp:
            fp.write(actual)
    with open(parse_tree_file) as fp:
        expected = fp.read()
    assert expected == actual

def python_ast(test_dir):
    actual = hermes.test.functions.python_ast(test_dir)
    ast_file = os.path.join(test_dir, 'ast')
    if not os.path.isfile(ast_file):
        with open(ast_file, 'w') as fp:
            fp.write(actual)
    with open(ast_file) as fp:
        expected = fp.read()
    assert expected == actual

def c_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.c_parsetree(test_dir)
    assert expected == actual

def c_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.c_ast(test_dir)
    assert expected == actual

def java_parse_tree(test_dir):
    ast_file = os.path.join(test_dir, 'parsetree')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.java_parsetree(test_dir)
    assert expected == actual

def java_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.java_ast(test_dir)
    assert expected == actual

def javascript_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.javascript_parsetree(test_dir)
    assert expected == actual

def javascript_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.javascript_ast(test_dir)
    assert expected == actual
