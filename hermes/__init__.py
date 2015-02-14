from hermes.GrammarParser import GrammarParser
from hermes.CodeGenerator import CodeGenerator
import imp, io, uuid

def get_grammar(str_or_fp):
    if isinstance(str_or_fp, str):
        code = str_or_fp
    else:
        code = str_or_fp.read()
    return GrammarParser().parse("internal", code)

def compile(str_or_fp, module=None):
    grammar = get_grammar(str_or_fp)
    code = CodeGenerator().generate_internal(grammar)
    #compile(code, '<string>', 'exec')
    return imp.load_module(module if module else str(uuid.uuid1()), io.StringIO(code), '<string>', ('.py', 'r', 1))
