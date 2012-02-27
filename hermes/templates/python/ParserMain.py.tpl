import sys, re
from ParserCommon import *

{% for grammar in grammars %}
from {{grammar.name}}_Parser import {{grammar.name}}_Parser
{% endfor %}

def getParser(name):
  {% for grammar in grammars %}
  if name == {{grammar.name}}:
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
  
  tokens = []
  tokenRegex = re.compile(r'<(\S+) \[(\S+) line (\d+), col (\d+)\]>')
  for line in sys.stdin:
    match = tokenRegex.match(line)
    try:
      tokens.append(Terminal(
        parser.terminals[match.group(1)],
        match.group(1),
        match.group(2),
        int(match.group(3)),
        int(match.group(4))
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
    
  except SyntaxError as e:
    print(e)