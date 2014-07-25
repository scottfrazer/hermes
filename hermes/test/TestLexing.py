import os
import tempfile
import shutil
import re
import subprocess

from hermes.CodeGenerator import CodeGenerator
from hermes.GrammarParser import GrammarParser

base_dir = os.path.join(os.path.dirname(__file__), 'cases/lexing')

def test_all():
    for directory in os.listdir(base_dir):
        test_dir = os.path.join(base_dir, directory)
        if os.path.isdir(test_dir) and re.match(r'^\d+$', directory):
            yield python_tokens, test_dir
            yield c_tokens, test_dir
            yield java_tokens, test_dir
            yield javascript_tokens, test_dir

def lex_python(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    source_file = os.path.join(test_dir, 'source')
    grammar = GrammarParser().parse('grammar', grammar_file)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        CodeGenerator().generate(grammar, 'python', directory=tmp_dir, python_package='parsers', add_main=True)
        command = 'python grammar_main.py tokens {0} 2>&1'.format(os.path.abspath(source_file))
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
        return exception.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def lex_c(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    source_file = os.path.join(test_dir, 'source')
    grammar = GrammarParser().parse('grammar', grammar_file)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        shutil.copy(source_file, tmp_dir)
        CodeGenerator().generate(grammar, 'c', directory=tmp_dir, add_main=True)
        c_files = list(filter(lambda x: x.endswith('.c'), os.listdir(tmp_dir)))
        command = 'gcc -o lexer -I/usr/local/include -I/usr/include -L/usr/local/lib -L/usr/lib -lpcre {sources} -g -Wall -pedantic -ansi -std=c99 2>&1'.format(sources=' '.join(c_files))
        subprocess.check_call(command, cwd=tmp_dir, shell=True, stderr=None)
        command = './lexer tokens source'
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        print(error)
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def lex_java(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    source_file = os.path.join(test_dir, 'source')
    grammar = GrammarParser().parse('grammar', grammar_file)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        shutil.copy(source_file, tmp_dir)
        shutil.copytree(os.path.join(test_dir, '..', '..', 'javacp', 'org'), os.path.join(tmp_dir, 'org'))
        java_sources = list(filter(lambda filename: filename.endswith('.java'), os.listdir(tmp_dir)))
        CodeGenerator().generate(grammar, 'java', directory=tmp_dir, add_main=True)
        compile_command = 'javac *.java 2>/dev/null'
        subprocess.check_call(compile_command, cwd=tmp_dir, shell=True, stderr=None)
        run_command = 'java ParserMain tokens source 2>&1'
        return subprocess.check_output(run_command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

def lex_javascript(test_dir):
    grammar_file = os.path.join(test_dir, 'grammar.zgr')
    source_file = os.path.join(test_dir, 'tokens')
    grammar = GrammarParser().parse('grammar', grammar_file)
    tmp_dir = tempfile.mkdtemp(prefix='hermes-')

    try:
        CodeGenerator().generate(grammar, 'javascript', directory=tmp_dir, nodejs=True, add_main=True)
        command = 'node main.js tokens {0} 2>&1'.format(os.path.abspath(source_file))
        return subprocess.check_output(command, shell=True, stderr=None, cwd=tmp_dir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
        return exception.output.decode('utf-8').strip()
    finally:
        shutil.rmtree(tmp_dir)

# Tests

def python_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    if not os.path.isfile(source_file):
        with open(source_file, 'w') as fp:
            fp.write(lex_python(test_dir))
    with open(source_file) as fp:
        expected = fp.read()
    actual = lex_python(test_dir)
    assert expected == actual

def c_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = lex_c(test_dir)
    assert expected == actual

def java_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = lex_java(test_dir)
    assert expected == actual

def javascript_tokens(test_dir):
    source_file = os.path.join(test_dir, 'tokens')
    with open(source_file) as fp:
        expected = fp.read()
    actual = lex_javascript(test_dir)
    assert expected == actual
