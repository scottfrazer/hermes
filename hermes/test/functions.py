import os
import tempfile
import shutil
import subprocess

import hermes.code
import hermes.factory

def python_tokens(test_dir): return _lex_python(test_dir)
def python_parsetree(test_dir): return _parse_python(test_dir, 'parsetree')
def python_ast(test_dir): return _parse_python(test_dir, 'ast')
def c_tokens(test_dir): return _lex_c(test_dir)
def c_parsetree(test_dir): return _parse_c(test_dir, 'parsetree')
def c_ast(test_dir): return _parse_c(test_dir, 'ast')
def java_tokens(test_dir): return _lex_java(test_dir)
def java_parsetree(test_dir): return _parse_java(test_dir, 'parsetree')
def java_ast(test_dir): return _parse_java(test_dir, 'ast')
def javascript_tokens(test_dir): return _lex_javascript(test_dir)
def javascript_parsetree(test_dir): return _parse_javascript(test_dir, 'parsetree')
def javascript_ast(test_dir): return _parse_javascript(test_dir, 'ast')

def _get_grammar(directory, name='grammar.zgr'):
    with open(os.path.join(directory, name)) as fp:
        return hermes.factory.parse(fp.read(), 'grammar')

def _parse_python(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp()

    try:
      hermes.code.generate(grammar, 'python', directory=tmp_dir, add_main=True)
      command = 'python grammar_parser.py {0} {1} 2>&1'.format(out, os.path.abspath(tokens_file))
      return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmp_dir)

def _parse_c(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = _get_grammar(test_dir)

    tmp_dir = tempfile.mkdtemp()
    try:
        shutil.copy(tokens_file, tmp_dir)
        hermes.code.generate(grammar, 'c', directory=tmp_dir, add_main=True)
        c_files = list(filter(lambda x: x.endswith('.c'), os.listdir(tmp_dir)))
        command = 'gcc -o parser {sources} -g -Wall -pedantic -ansi -std=c99 -lpcre 2>/dev/null'.format(sources=' '.join(c_files))
        subprocess.check_call(command, cwd=tmp_dir, shell=True, stderr=None)
        command = './parser {type} tokens 2>&1'.format(type=out)
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def _parse_java(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = _get_grammar(test_dir)

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

def _parse_javascript(test_dir, out):
    tokens_file = os.path.join(test_dir, 'tokens')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp()

    try:
      hermes.code.generate(grammar, 'javascript', directory=tmp_dir, nodejs=True, add_main=True)
      command = 'node grammar_parser.js {0} {1} 2>&1'.format(out, os.path.abspath(tokens_file))
      return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmp_dir)

def _lex_python(test_dir):
    source_file = os.path.join(test_dir, 'source')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        hermes.code.generate(grammar, 'python', directory=tmp_dir, add_main=True)
        command = 'python grammar_parser.py tokens {0} 2>&1'.format(os.path.abspath(source_file))
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
        return exception.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def _lex_c(test_dir):
    source_file = os.path.join(test_dir, 'source')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        shutil.copy(source_file, tmp_dir)
        hermes.code.generate(grammar, 'c', directory=tmp_dir, add_main=True)
        c_files = list(filter(lambda x: x.endswith('.c'), os.listdir(tmp_dir)))
        command = 'gcc -o lexer {sources} -g -Wall -pedantic -std=c99 -lpcre 2>/dev/null'.format(sources=' '.join(c_files))
        subprocess.check_call(command, cwd=tmp_dir, shell=True, stderr=None)
        command = './lexer tokens source'
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        print(error)
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def _lex_java(test_dir):
    source_file = os.path.join(test_dir, 'source')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        shutil.copy(source_file, tmp_dir)
        java_sources = list(filter(lambda filename: filename.endswith('.java'), os.listdir(tmp_dir)))
        hermes.code.generate(grammar, 'java', directory=tmp_dir, add_main=True)
        compile_command = 'javac *.java 2>/dev/null'
        subprocess.check_call(compile_command, cwd=tmp_dir, shell=True, stderr=None)
        run_command = 'java GrammarParser tokens source 2>&1'
        return subprocess.check_output(run_command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def _lex_javascript(test_dir):
    source_file = os.path.join(test_dir, 'source')
    grammar = _get_grammar(test_dir)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        hermes.code.generate(grammar, 'javascript', directory=tmp_dir, nodejs=True, add_main=True)
        command = 'node grammar_parser.js tokens {0} 2>&1'.format(os.path.abspath(source_file))
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
        return exception.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)
