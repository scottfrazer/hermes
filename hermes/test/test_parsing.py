import os
import tempfile
import shutil
import re
import subprocess

import hermes.code
import hermes.factory

base_dir = os.path.join(os.path.dirname(__file__), 'cases/parsing')

def get_grammar(directory, name='grammar.zgr'):
    with open(os.path.join(directory, name)) as fp:
        return hermes.factory.parse(fp.read(), 'grammar')

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

def parse_python(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp()

    try:
      hermes.code.generate(grammar, 'python', directory=tmp_dir, add_main=True)
      command = 'python grammar_parser.py {0} {1} 2>&1'.format(out, os.path.abspath(tokens_file))
      return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmp_dir)

def parser_c(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = get_grammar(test_dir)

    tmp_dir = tempfile.mkdtemp()
    try:
        shutil.copy(tokens_file, tmp_dir)
        hermes.code.generate(grammar, 'c', directory=tmp_dir, add_main=True)
        c_files = list(filter(lambda x: x.endswith('.c'), os.listdir(tmp_dir)))
        command = 'gcc -o parser {sources} -g -Wall -pedantic -ansi -std=c99 2>/dev/null'.format(sources=' '.join(c_files))
        subprocess.check_call(command, cwd=tmp_dir, shell=True, stderr=None)
        command = './parser {type} tokens'.format(type=out)
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def parser_java(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = get_grammar(test_dir)

    tmp_dir = tempfile.mkdtemp()
    try:
        shutil.copy(tokens_file, tmp_dir)
        java_sources = list(filter(lambda filename: filename.endswith('.java'), os.listdir(tmp_dir)))
        hermes.code.generate(grammar, 'java', directory=tmp_dir, add_main=True)
        compile_command = 'javac *.java 2>/dev/null'
        subprocess.check_call(compile_command, cwd=tmp_dir, shell=True, stderr=None)
    except subprocess.CalledProcessError as error:
        shutil.rmtree(tmp_dir)

    try:
        run_command = 'java GrammarParser {type} tokens 2>&1'.format(type=out)
        return subprocess.check_output(run_command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
        return exception.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def parse_javascript(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp()

    try:
      hermes.code.generate(grammar, 'javascript', directory=tmp_dir, nodejs=True, add_main=True)
      command = 'node grammar_parser.js {0} {1} 2>&1'.format(out, os.path.abspath(tokens_file))
      return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmp_dir)

# Tests

def python_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    if not os.path.isfile(parse_tree_file):
        with open(parse_tree_file, 'w') as fp:
            fp.write(parse_python(test_dir, 'parsetree'))
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = parse_python(test_dir, 'parsetree')
    assert expected == actual

def python_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    if not os.path.isfile(ast_file):
        with open(ast_file, 'w') as fp:
            fp.write(parse_python(test_dir, 'ast'))
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parse_python(test_dir, 'ast')
    assert expected == actual

def c_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = parser_c(test_dir, 'parsetree')
    assert expected == actual

def c_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parser_c(test_dir, 'ast')
    assert expected == actual

def java_parse_tree(test_dir):
    ast_file = os.path.join(test_dir, 'parsetree')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parser_java(test_dir, 'parsetree')
    assert expected == actual

def java_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parser_java(test_dir, 'ast')
    assert expected == actual

def javascript_parse_tree(test_dir):
    parse_tree_file = os.path.join(test_dir, 'parsetree')
    with open(parse_tree_file) as fp:
        expected = fp.read()
    actual = parse_javascript(test_dir, 'parsetree')
    assert expected == actual

def javascript_ast(test_dir):
    ast_file = os.path.join(test_dir, 'ast')
    with open(ast_file) as fp:
        expected = fp.read()
    actual = parse_javascript(test_dir, 'ast')
    assert expected == actual
