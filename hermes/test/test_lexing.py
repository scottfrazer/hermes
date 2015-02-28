import os
import re
import hermes.test.functions

base_dir = os.path.join(os.path.dirname(__file__), 'cases/lexing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            with hermes.test.functions.python_code_context(test_dir) as python_ctx:
                yield python_tokens, python_ctx
            with hermes.test.functions.c_code_context(test_dir) as c_ctx:
                yield c_tokens, c_ctx
            with hermes.test.functions.java_code_context(test_dir) as java_ctx:
                yield java_tokens, java_ctx
            with hermes.test.functions.javascript_code_context(test_dir) as javascript_ctx:
                yield javascript_tokens, javascript_ctx

def python_tokens(python_ctx):
    actual = python_ctx.tokens()
    tokens_file = os.path.join(python_ctx.test_dir, 'tokens')
    if not os.path.isfile(tokens_file):
        with open(tokens_file, 'w') as fp:
            fp.write(actual)
    with open(tokens_file) as fp:
        expected = fp.read()
    assert expected == actual

def c_tokens(c_ctx):
    tokens_file = os.path.join(c_ctx.test_dir, 'tokens')
    with open(tokens_file) as fp:
        expected = fp.read()
    actual = c_ctx.tokens()
    assert expected == actual

def java_tokens(java_ctx):
    tokens_file = os.path.join(java_ctx.test_dir, 'tokens')
    with open(tokens_file) as fp:
        expected = fp.read()
    actual = java_ctx.tokens()
    assert expected == actual

def javascript_tokens(javascript_ctx):
    tokens_file = os.path.join(javascript_ctx.test_dir, 'tokens')
    with open(tokens_file) as fp:
        expected = fp.read()
    actual = javascript_ctx.tokens()
    assert expected == actual
