import os
import re
import hermes.test.functions

base_dir = os.path.join(os.path.dirname(__file__), 'cases/parsing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            with hermes.test.functions.python_code_context(test_dir) as python_ctx:
                yield python_parse_tree, python_ctx
                yield python_ast, python_ctx
            with hermes.test.functions.python_code_context(test_dir) as c_ctx:
                yield c_parse_tree, c_ctx
                yield c_ast, c_ctx
            with hermes.test.functions.python_code_context(test_dir) as java_ctx:
                yield java_parse_tree, java_ctx
                yield java_ast, java_ctx
            with hermes.test.functions.python_code_context(test_dir) as javascript_ctx:
                yield javascript_parse_tree, javascript_ctx
                yield javascript_ast, javascript_ctx

def python_parse_tree(python_ctx):
    actual = python_ctx.parsetree()
    parse_tree_file = os.path.join(python_ctx.test_dir, 'parsetree')
    if not os.path.isfile(parse_tree_file):
        with open(parse_tree_file, 'w') as fp:
            fp.write(actual)
    with open(parse_tree_file) as fp:
        expected = fp.read()
    assert expected == actual

def python_ast(python_ctx):
    actual = python_ctx.ast()
    ast_file = os.path.join(python_ctx.test_dir, 'ast')
    if not os.path.isfile(ast_file):
        with open(ast_file, 'w') as fp:
            fp.write(actual)
    with open(ast_file) as fp:
        expected = fp.read()
    assert expected == actual

def c_parse_tree(c_ctx):
    parse_tree_file = os.path.join(c_ctx.test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = c_ctx.parsetree()
    assert expected == actual

def c_ast(c_ctx):
    ast_file = os.path.join(c_ctx.test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = c_ctx.ast()
    assert expected == actual

def java_parse_tree(java_ctx):
    ast_file = os.path.join(java_ctx.test_dir, 'parsetree')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = java_ctx.parsetree()
    assert expected == actual

def java_ast(java_ctx):
    ast_file = os.path.join(java_ctx.test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = java_ctx.ast()
    assert expected == actual

def javascript_parse_tree(javascript_ctx):
    parse_tree_file = os.path.join(javascript_ctx.test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = javascript_ctx.parsetree()
    assert expected == actual

def javascript_ast(javascript_ctx):
    ast_file = os.path.join(javascript_ctx.test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = javascript_ctx.ast()
    assert expected == actual
