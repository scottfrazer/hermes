import os
import re
import hermes.test.functions

base_dir = os.path.join(os.path.dirname(__file__), 'cases/lexing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            yield python_tokens, test_dir
            yield c_tokens, test_dir
            yield java_tokens, test_dir
            yield javascript_tokens, test_dir

def python_tokens(test_dir):
    actual = hermes.test.functions.python_tokens(test_dir)
    source_file = os.path.join(test_dir, 'tokens')
    if not os.path.isfile(source_file):
        with open(source_file, 'w') as fp:
            fp.write(actual)
    with open(source_file) as fp:
        expected = fp.read()
    assert expected == actual

def c_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.c_tokens(test_dir)
    assert expected == actual

def java_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.java_tokens(test_dir)
    assert expected == actual

def javascript_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = hermes.test.functions.javascript_tokens(test_dir)
    assert expected == actual
