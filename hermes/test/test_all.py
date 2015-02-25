import os
import re
import hermes.test.functions
from hermes.test.test_lexing import *
from hermes.test.test_parsing import *

base_dir = os.path.join(os.path.dirname(__file__), 'cases/all')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            yield python_tokens, test_dir
            yield python_parse_tree, test_dir
            yield python_ast, test_dir
            yield c_tokens, test_dir
            yield c_parse_tree, test_dir
            yield c_ast, test_dir
            yield java_tokens, test_dir
            yield java_parse_tree, test_dir
            yield java_ast, test_dir
            yield javascript_tokens, test_dir
            yield javascript_parse_tree, test_dir
            yield javascript_ast, test_dir
