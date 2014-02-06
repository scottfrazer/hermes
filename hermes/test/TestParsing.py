import os
import tempfile
import shutil
import re
import subprocess

from hermes.GrammarCodeGenerator import FactoryFactory as TemplateFactoryFactory
from hermes.GrammarCodeGenerator import TemplateWriter
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from nose.plugins.skip import SkipTest

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

# Utility

def parse(test_dir, out):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = GrammarFileParser(HermesParserFactory().create()).parse_new('grammar', open(grammar_file))
    tmp_dir = tempfile.mkdtemp()
    
    try:
      template = TemplateWriter(TemplateFactoryFactory().create('python'))
      template.write([grammar], tmp_dir)
      command = 'python -m {0}.grammar.Parser --file={1} --out={2} 2>&1'.format(os.path.basename(tmp_dir), os.path.abspath(tokens_file), out)
      return subprocess.check_output(command, shell=True, stderr=None, cwd=os.path.dirname(tmp_dir)).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmp_dir)

# Tests

def python_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parse_tree')
    if not os.path.isfile(parse_tree_file):
        with open(parse_tree_file, 'w') as fp:
            fp.write(parse(test_dir, 'parsetree'))
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = parse(test_dir, 'parsetree')
    assert expected == actual

def python_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    if not os.path.isfile(ast_file):
        with open(ast_file, 'w') as fp:
            fp.write(parse(test_dir, 'ast'))
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parse(test_dir, 'ast')
    assert expected == actual

def c_parse_tree(test_dir):
    raise SkipTest()

def c_ast(test_dir):
    raise SkipTest()

def java_parse_tree(test_dir):
    raise SkipTest()

def java_ast(test_dir):
    raise SkipTest()
