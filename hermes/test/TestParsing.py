import os
from nose.plugins.skip import SkipTest

base_dir = os.path.join(os.path.dirname(__file__), 'cases/parsing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir):
            yield python_parse_tree, test_dir
            yield python_ast, test_dir
            yield c_parse_tree, test_dir
            yield c_ast, test_dir
            yield java_parse_tree, test_dir
            yield java_ast, test_dir

def python_parse_tree(test_dir):
    raise SkipTest()

def python_ast(test_dir):
    raise SkipTest()

def c_parse_tree(test_dir):
    raise SkipTest()

def c_ast(test_dir):
    raise SkipTest()

def java_parse_tree(test_dir):
    raise SkipTest()

def java_ast(test_dir):
    raise SkipTest()
