import json
import os
import sys
import base64

from {{python_package}}.{{grammar.name}} import parse
{% if lexer %}
from {{python_package}}.{{grammar.name}} import lex
{% endif %}
from {{python_package}}.{{grammar.name}}.Parser import terminals
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
                terminals[json_token['terminal']],
                json_token['terminal'],
                json_token['source_string'],
                json_token['resource'],
                json_token['line'],
                json_token['col']
            ))

    try:
        tree = parse(tokens)
        if sys.argv[1] == 'parsetree':
            print(ParseTreePrettyPrintable(tree))
        else:
            print(AstPrettyPrintable(tree.toAst()))
    except SyntaxError as error:
        print(error)

if sys.argv[1] == 'tokens':
    try:
        tokens = lex(sys.argv[2])
    except SyntaxError as error:
        sys.exit(error)

    if len(tokens) == 0:
        print('[]')
        sys.exit(0)

    tokens_json = []
    json_fmt = '"terminal": "{terminal}", "resource": "{resource}", "line": {line}, "col": {col}, "source_string": "{source_string}"'
    for token in tokens:
        tokens_json.append(
            '{' +
            json_fmt.format(
              terminal=token.str,
              resource=token.resource,
              line=token.line,
              col=token.col,
              source_string=base64.b64encode(token.source_string.encode('utf-8')).decode('utf-8')
            ) +
            '}'
        )
    sys.stdout.write('[\n    ')
    sys.stdout.write(',\n    '.join(tokens_json))
    sys.stdout.write('\n]\n')
