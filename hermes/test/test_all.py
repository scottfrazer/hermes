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
            with hermes.test.functions.python_code_context(test_dir) as python_ctx:
                yield python_tokens, python_ctx
                yield python_parse_tree, python_ctx
                yield python_ast, python_ctx
            with hermes.test.functions.python_code_context(test_dir) as c_ctx:
                yield c_tokens, c_ctx
                yield c_parse_tree, c_ctx
                yield c_ast, c_ctx
            with hermes.test.functions.python_code_context(test_dir) as java_ctx:
                yield java_tokens, java_ctx
                yield java_parse_tree, java_ctx
                yield java_ast, java_ctx
            with hermes.test.functions.python_code_context(test_dir) as javascript_ctx:
                yield javascript_tokens, javascript_ctx
                yield javascript_parse_tree, javascript_ctx
                yield javascript_ast, javascript_ctx
