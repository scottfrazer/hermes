import json
import os
import sys

from {{python_package}}.{{grammar.name}} import parse
{% if lexer %}
from {{python_package}}.{{grammar.name}} import lex
{% endif %}
from {{python_package}}.{{grammar.name}}.Parser import parser_terminals
from {{python_package}}.Common import *

if len(sys.argv) != 3 or (sys.argv[1] not in ['parsetree', 'ast']{% if lexer %} and sys.argv[1] != 'tokens'{% endif %}):
    sys.stderr.write("Usage: Main.py <parsetree|ast> <tokens_file>\n")
    {% if lexer %}
    sys.stderr.write("Usage: Main.py <tokens> <source_file>\n")
    {% endif %}
    sys.exit(-1)

if sys.argv[1] in ['parsetree', 'ast']:
    tokens = TokenStream()
    with open(os.path.expanduser(sys.argv[2])) as fp:
        json_tokens = json.loads(fp.read())
        for json_token in json_tokens:
            tokens.append(Terminal(
                parser_terminals[json_token['terminal']],
                json_token['terminal'],
                json_token['source_string'],
                json_token['resource'],
                json_token['line'],
                json_token['col']
            ))

    try:
        tree = parse(tokens)
        if sys.argv[1] == 'parsetree':
            print(tree.dumps(indent=2))
        else:
            print(AstPrettyPrintable(tree.toAst()))
    except SyntaxError as error:
        print(error)

if sys.argv[1] == 'tokens':
    try:
        with open(sys.argv[2]) as fp:
            tokens = lex(fp.read(), os.path.basename(sys.argv[2]))
        print(tokens.json())
    except SyntaxError as error:
        sys.exit(error)
