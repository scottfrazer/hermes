import hermes.factory
import hermes.code
import imp, io, uuid

def get_grammar(str_or_fp):
    if isinstance(str_or_fp, str):
        code = str_or_fp
    else:
        code = str_or_fp.read()
    return hermes.factory.parse(code, "internal")

def compile(str_or_fp, module=None, debug=False):
    grammar = get_grammar(str_or_fp)
    module = module if module else str(uuid.uuid1())
    code = hermes.code.generate_internal(grammar)
    if debug:
        filename = module if module.endswith('.py') else module+'.py'
        with open(filename, 'w') as fp:
            fp.write(code)
    return imp.load_module(module, io.StringIO(code), '<hermes {}>'.format(module), ('.py', 'r', 1))
