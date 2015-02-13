from hermes.GrammarParser import GrammarParser
from hermes.CodeGenerator import CodeGenerator
import imp, io, uuid

def get_grammar(str_or_fp):
    if isinstance(str_or_fp, str):
        code = str_or_fp
    else:
        code = str_or_fp.read()
    return GrammarParser().parse("internal", str_or_fp)

def load(str_or_fp):
    grammar = get_grammar(str_or_fp)
    code = CodeGenerator().generate_internal(grammar)
    m = imp.load_module(str(uuid.uuid1()), io.StringIO(code), '', ('.py', 'r', 1))
    return m
