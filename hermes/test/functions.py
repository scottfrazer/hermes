import os
import tempfile
import shutil
import subprocess

import hermes.code
import hermes.factory

def c_tokens(test_dir): return _lex_c(test_dir)
def c_parsetree(test_dir): return _parse_c(test_dir, 'parsetree')
def c_ast(test_dir): return _parse_c(test_dir, 'ast')
def java_tokens(test_dir): return _lex_java(test_dir)
def java_parsetree(test_dir): return _parse_java(test_dir, 'parsetree')
def java_ast(test_dir): return _parse_java(test_dir, 'ast')
def javascript_tokens(test_dir): return _lex_javascript(test_dir)
def javascript_parsetree(test_dir): return _parse_javascript(test_dir, 'parsetree')
def javascript_ast(test_dir): return _parse_javascript(test_dir, 'ast')

def _get_grammar(directory, name='grammar.hgr'):
    with open(os.path.join(directory, name)) as fp:
        return hermes.factory.parse(fp.read(), 'grammar')

def _run_command(command, tmp_dir, action, input):
    try:
        return subprocess.check_output(
            command.format(action=action, input=input),
            shell=True, stderr=None, cwd=tmp_dir
        ).decode('utf-8').strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode('utf-8').strip()

class python_code_context:
    def __init__(self, test_dir):
        self.test_dir = test_dir
        self.tokens_file = os.path.join(self.test_dir, 'tokens')
        self.source_file = os.path.join(self.test_dir, 'source')
        self.grammar = _get_grammar(self.test_dir)
        self.command = 'python grammar_parser.py {action} {input} 2>&1'
    def __enter__(self):
        self.tmp_dir = tempfile.mkdtemp('hermes-')
        if os.path.isfile(self.source_file):
            shutil.copy(self.source_file, self.tmp_dir)
        if os.path.isfile(self.tokens_file):
            shutil.copy(self.tokens_file, self.tmp_dir)
        hermes.code.generate(self.grammar, 'python', directory=self.tmp_dir, add_main=True)
        return self
    def tokens(self):
        return _run_command(self.command, self.tmp_dir, 'tokens', os.path.abspath(self.source_file))
    def parsetree(self):
        return _run_command(self.command, self.tmp_dir, 'parsetree', os.path.abspath(self.tokens_file))
    def ast(self):
        return _run_command(self.command, self.tmp_dir, 'ast', os.path.abspath(self.tokens_file))
    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)
    def __repr__(self):
        return '<{} dir={}>'.format(self.__class__.__name__, self.test_dir)

class c_code_context:
    def __init__(self, test_dir):
        self.test_dir = test_dir
        self.tokens_file = os.path.join(self.test_dir, 'tokens')
        self.source_file = os.path.join(self.test_dir, 'source')
        self.grammar = _get_grammar(self.test_dir)
        self.command = './parser {action} {input} 2>&1'
    def __enter__(self):
        self.tmp_dir = tempfile.mkdtemp('hermes-')
        hermes.code.generate(self.grammar, 'c', directory=self.tmp_dir, add_main=True)
        c_files = [f for f in os.listdir(self.tmp_dir) if f.endswith('.c')]
        compile_command = 'gcc -o parser {sources} -g -Wall -pedantic -ansi -std=c99 -lpcre 2>/dev/null'.format(sources=' '.join(c_files))
        if os.path.isfile(self.source_file):
            shutil.copy(self.source_file, self.tmp_dir)
        if os.path.isfile(self.tokens_file):
            shutil.copy(self.tokens_file, self.tmp_dir)
        subprocess.check_call(compile_command, cwd=self.tmp_dir, shell=True, stderr=None)
        return self
    def tokens(self):
        return _run_command(self.command, self.tmp_dir, 'tokens', 'source')
    def parsetree(self):
        return _run_command(self.command, self.tmp_dir, 'parsetree', os.path.abspath(self.tokens_file))
    def ast(self):
        return _run_command(self.command, self.tmp_dir, 'ast', os.path.abspath(self.tokens_file))
    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)
    def __repr__(self):
        return '<{} dir={}>'.format(self.__class__.__name__, self.test_dir)

class java_code_context:
    def __init__(self, test_dir):
        self.test_dir = test_dir
        self.tokens_file = os.path.join(self.test_dir, 'tokens')
        self.source_file = os.path.join(self.test_dir, 'source')
        self.grammar = _get_grammar(self.test_dir)
        self.command = 'java GrammarParser {action} {input} 2>&1'
    def __enter__(self):
        self.tmp_dir = tempfile.mkdtemp('hermes-')
        hermes.code.generate(self.grammar, 'java', directory=self.tmp_dir, add_main=True)
        compile_command = 'javac *.java 2>/dev/null'
        subprocess.check_call(compile_command, cwd=self.tmp_dir, shell=True, stderr=None)
        if os.path.isfile(self.source_file):
            shutil.copy(self.source_file, self.tmp_dir)
        if os.path.isfile(self.tokens_file):
            shutil.copy(self.tokens_file, self.tmp_dir)
        return self
    def tokens(self):
        return _run_command(self.command, self.tmp_dir, 'tokens', 'source')
    def parsetree(self):
        return _run_command(self.command, self.tmp_dir, 'parsetree', os.path.abspath(self.tokens_file))
    def ast(self):
        return _run_command(self.command, self.tmp_dir, 'ast', os.path.abspath(self.tokens_file))
    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)
    def __repr__(self):
        return '<{} dir={}>'.format(self.__class__.__name__, self.test_dir)

class javascript_code_context:
    def __init__(self, test_dir):
        self.test_dir = test_dir
        self.tokens_file = os.path.join(self.test_dir, 'tokens')
        self.source_file = os.path.join(self.test_dir, 'source')
        self.grammar = _get_grammar(self.test_dir)
        with open('/dev/null', 'w') as null:
            node_exe = 'nodejs' if subprocess.call(["which", "nodejs"], stdout=null) == 0 else 'node'
        self.command = node_exe + ' grammar_parser.js {action} {input} 2>&1'
    def __enter__(self):
        self.tmp_dir = tempfile.mkdtemp('hermes-')
        hermes.code.generate(self.grammar, 'javascript', directory=self.tmp_dir, add_main=True)
        if os.path.isfile(self.source_file):
            shutil.copy(self.source_file, self.tmp_dir)
        if os.path.isfile(self.tokens_file):
            shutil.copy(self.tokens_file, self.tmp_dir)
        return self
    def tokens(self):
        return _run_command(self.command, self.tmp_dir, 'tokens', 'source')
    def parsetree(self):
        return _run_command(self.command, self.tmp_dir, 'parsetree', os.path.abspath(self.tokens_file))
    def ast(self):
        return _run_command(self.command, self.tmp_dir, 'ast', os.path.abspath(self.tokens_file))
    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)
    def __repr__(self):
        return '<{} dir={}>'.format(self.__class__.__name__, self.test_dir)
