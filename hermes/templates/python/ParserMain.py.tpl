import sys, re, json
from ParserCommon import *

{% for grammar in grammars %}
from {{grammar.name}}_Parser import {{grammar.name}}_Parser
{% endfor %}

def getParser(name):
  {% for grammar in grammars %}
  if name == '{{grammar.name}}':
    return {{grammar.name}}_Parser()
  {% endfor %}
  raise Exception('Invalid grammar name: {}'.format(name))

if __name__ == '__main__':
  
  grammars = "{{','.join([grammar.name for grammar in grammars])}}"
  if len(sys.argv) < 2:
    print("Usage: {} <{}> <parsetree,ast>".format(sys.argv[0], grammars))
    sys.exit(-1)
  grammar = sys.argv[1].lower()
  parser = getParser(grammar)

  in_tokens = json.loads(sys.stdin.read())
  tokens = []
  for token in in_tokens:

    for key in ["terminal", "line", "col", "resource", "source_string"]:
      if key not in token.keys():
        raise Exception('Malformed token (missing key {0}): {1}'.format(key, json.dumps(token)))

    try:
      tokens.append(Terminal(
        parser.terminals[token['terminal']],
        token['terminal'],
        token['source_string'],
        token['resource'],
        token['line'],
        token['col']
      ))
    except AttributeError as error:
      sys.stderr.write( str(error) + "\n" )
      sys.exit(-1)

  tokens = TokenStream(tokens)

  try:
    parsetree = parser.parse( tokens )
    if len(sys.argv) > 2 and sys.argv[2] == 'ast':
      ast = parsetree.toAst()
      print(AstPrettyPrintable(ast))
    else:
      print(ParseTreePrettyPrintable(parsetree))
    
  except SyntaxError as error:
    sys.stderr.write( str(error) + "\n" )
    sys.exit(-1)
