import sys

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

import inspect
def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]

def parse( iterator, entry ):
  p = Parser()
  return p.parse(iterator, entry)
  
class Terminal:
  def __init__(self, id):
    self.id=id
    self.str=Parser.terminals[id]
  def getId(self):
    return self.id
  def toAst(self):
    return self
  def toString(self, format):
    if format == 'type':
      return self.str
  def __str__(self):
    return self.str

class NonTerminal():
  def __init__(self, id, string):
    self.id = id
    self.string = string
    self.list = False
  def __str__(self):
    return self.string

class AstTransform:
  pass

class AstTransformSubstitution(AstTransform):
  def __init__( self, idx ):
    self.idx = idx
  def __repr__( self ):
    return '$' + str(self.idx)
class AstTransformNodeCreator(AstTransform):
  def __init__( self, name, parameters ):
    self.name = name
    self.parameters = parameters
  def __repr__( self ):
    return self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )' 
class AstList(list):
  def toAst(self):
    retval = []
    for ast in self:
      retval.append(ast.toAst())
    return retval
class ParseTree():
  def __init__(self, nonterminal):
    self.__dict__.update(locals())
    self.children = []
    self.astTransform = None
    self.isExpr = False
    self.isNud = False
    self.isPrefix = False
    self.isInfix = False
    self.nudMorphemeCount = 0
    self.isExprNud = False # true for rules like _expr := {_expr} + {...}
    self.listSeparator = None
    self.list = False
  def add( self, tree ):
    self.children.append( tree )
  def toAst( self ):
    if self.list == 'slist' or self.list == 'nlist':
      if len(self.children) == 0:
        return AstList()
      offset = 1 if self.children[0] == self.listSeparator else 0
      r = AstList([self.children[offset].toAst()])
      r.extend(self.children[offset+1].toAst())
      return r
    elif self.list == 'tlist':
      if len(self.children) == 0:
        return AstList()
      r = AstList([self.children[0].toAst()])
      r.extend(self.children[2].toAst())
      return r
    elif self.list == 'mlist':
      r = AstList()
      if len(self.children) == 0:
        return r
      lastElement = len(self.children) - 1
      for i in range(lastElement):
        r.append(self.children[i].toAst())
      r.extend(self.children[lastElement].toAst())
      return r
    elif self.isExpr:
      if isinstance(self.astTransform, AstTransformSubstitution):
        return self.children[self.astTransform.idx].toAst()
      elif isinstance(self.astTransform, AstTransformNodeCreator):
        parameters = {}
        for name, idx in self.astTransform.parameters.items():
          if idx == '$':
            child = self.children[0]
          elif isinstance(self.children[0], ParseTree) and \
               self.children[0].isNud and \
               not self.children[0].isPrefix and \
               not self.isExprNud and \
               not self.isInfix:
            if idx < self.children[0].nudMorphemeCount:
              child = self.children[0].children[idx]
            else:
              index = idx - self.children[0].nudMorphemeCount + 1
              child = self.children[index]
          elif len(self.children) == 1 and not isinstance(self.children[0], ParseTree) and not isinstance(self.children[0], list):
            return self.children[0]
          else:
            child = self.children[idx]

          parameters[name] = child.toAst()
        return Ast(self.astTransform.name, parameters)
    else:
      if isinstance(self.astTransform, AstTransformSubstitution):
        return self.children[self.astTransform.idx].toAst()
      elif isinstance(self.astTransform, AstTransformNodeCreator):
        parameters = {name: self.children[idx].toAst() for name, idx in self.astTransform.parameters.items()}
        return Ast(self.astTransform.name, parameters)
      elif len(self.children):
        return self.children[0].toAst()
      else:
        return None
  def __str__( self ):
    children = []
    for child in self.children:
      if isinstance(child, list):
        children.append('[' + ', '.join([str(a) for a in child]) + ']')
      else:
        children.append(str(child))
    return '(' + str(self.nonterminal) + ': ' + ', '.join(children) + ')'

class Ast():
  def __init__(self, name, attributes):
    self.name = name
    self.attributes = attributes
  def getAttr(self, attr):
    return self.attributes[attr]
  def __str__(self):
    return '(%s: %s)' % (self.name, ', '.join('%s=%s'%(str(k), '[' + ', '.join([str(x) for x in v]) + ']' if isinstance(v, list) else str(v) ) for k,v in self.attributes.items()))

class ParseTreePrettyPrintable:
  def __init__(self, ast, tokenFormat='type'):
    self.__dict__.update(locals())
  def __str__(self):
    return self._prettyPrint(self.ast, 0)
  def _prettyPrint(self, parsetree, indent = 0):
    indentStr = ''.join([' ' for x in range(indent)])
    if isinstance(parsetree, ParseTree):
      if len(parsetree.children) == 0:
        return '(%s: )' % (parsetree.nonterminal)
      string = '%s(%s:\n' % ('', parsetree.nonterminal)
      string += ',\n'.join([ \
        '%s  %s' % (indentStr, self._prettyPrint(value, indent + 2)) for value in parsetree.children \
      ])
      string += '\n%s)' % (indentStr)
      return string
    elif isinstance(parsetree, Terminal):
      return parsetree.toString(self.tokenFormat)

class AstPrettyPrintable(Ast):
  def __init__(self, ast, tokenFormat='type'):
    self.__dict__.update(locals())
  def getAttr(self, attr):
    return self.ast.getAttr(attr)
  def __str__(self):
    return self._prettyPrint(self.ast, 0)
  def _prettyPrint(self, ast, indent = 0):
    indentStr = ''.join([' ' for x in range(indent)])
    if isinstance(ast, Ast):
      string = '%s(%s:\n' % (indentStr, ast.name)
      string += ',\n'.join([ \
        '%s  %s=%s' % (indentStr, name, self._prettyPrint(value, indent + 2).lstrip()) for name, value in ast.attributes.items() \
      ])
      string += '\n%s)' % (indentStr)
      return string
    elif isinstance(ast, list):
      if len(ast) == 0:
        return '[]'
      string = '[\n'
      string += ',\n'.join([self._prettyPrint(element, indent + 2) for element in ast])
      string += '\n%s]' % (indentStr)
      return string
    elif isinstance(ast, Terminal):
      return '%s%s' % (indentStr, ast.toString(self.tokenFormat))
    return 'None'
class SyntaxError(Exception):
  def __init__(self, message):
    self.__dict__.update(locals())
  def __str__(self):
    return self.message

{% for exprGrammar in grammar.exprgrammars %}

class ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}:
  def __init__(self, parent):
    self.__dict__.update(locals())

    self.infixBp = {
      {% for terminal_id, binding_power in exprGrammar.infix.items() %}
      {{terminal_id}}: {{binding_power}},
      {% endfor %}
    }

    self.prefixBp = {
      {% for terminal_id, binding_power in exprGrammar.prefix.items() %}
      {{terminal_id}}: {{binding_power}},
      {% endfor %}
    }

  def getInfixBp(self, tokenId):
    try:
      return self.infixBp[tokenId]
    except:
      return 0

  def getPrefixBp(self, tokenId):
    try:
      return self.prefixBp[tokenId]
    except:
      return 0
  
  def getCurrentToken(self):
    return self.parent.tokens.current()

  def expect(self, token):
    return self.parent.expect(token)

  def parse(self, rbp = 0):
    left = self.nud()
    if isinstance(left, ParseTree):
      left.isExpr = True
      left.isNud = True
    while self.getCurrentToken() and rbp < self.getInfixBp(self.getCurrentToken().getId()):
      left = self.led(left)
    if left:
      left.isExpr = True
    return left

  def nud(self):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    if not current:
      return tree

    {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
      {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

      {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

      {% if len(ruleFirstSet) and not isOptional %}
    {{'if' if i == 0 else 'elif'}} current.getId() in [{{', '.join([str(x.id) for x in exprGrammar.ruleFirst(rule)])}}]:

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

      tree.nudMorphemeCount = {{len(rule.nudProduction)}}

        {% for morpheme in rule.nudProduction.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}( self.getPrefixBp({{rule.operator.operator.id}}) ) )
      tree.isPrefix = True
            {% else %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}() )
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self.parent.parse_{{morpheme.string.lower()}}() )
          {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self.parent.parse_{{morpheme.start_nt.string.lower()}}() )
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

  def led(self, left):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    {% py seen = list() %}
    {% for rule in exprGrammar.rules %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) and led[0] not in seen %}
    {{'if' if len(seen)==0 else 'elif'}} current.getId() == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

      {% py morpheme = rule.nudProduction.morphemes[0] if len(rule.nudProduction) else None %}
      {% if morpheme == rule.nonterminal or (isinstance(morpheme, NonTerminal) and morpheme.macro and morpheme.macro.nonterminal == rule.nonterminal) %}
      tree.isExprNud = True
      {% endif %}

      tree.add(left)

        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
      modifier = {{1 if rule.operator.operator.id in exprGrammar.precedence and exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}}
            {% if isinstance(rule.operator, InfixOperator) %}
      tree.isInfix = True
            {% endif %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}( self.getInfixBp({{rule.operator.operator.id}}) - modifier ) )
          {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self.parent.parse_{{morpheme.string.lower()}}() )
          {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self.parent.parse_{{morpheme.start_nt.string.lower()}}() )
          {% endif %}
        {% endfor %}
        {% py seen.append(led[0]) %}
      {% endif %}
    {% endfor %}

    return tree
{% endfor %}

class TokenStream:
  def __init__(self, iterable):
    self.iterable = iter(iterable)
    self.advance()
  def advance(self):
    try:
      self.token = next(self.iterable)
    except StopIteration:
      self.token = None
    return self.token
  def current(self):
    return self.token

class Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
  {% for terminal in nonAbstractTerminals %}
    {{terminal.id}}: '{{terminal.string}}',
  {% endfor %}

  {% for terminal in nonAbstractTerminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
  {% endfor %}
  }

  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
  {% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: '{{nonterminal.string}}',
  {% endfor %}

  {% for nonterminal in grammar.nonterminals %}
    '{{nonterminal.string.lower()}}': {{nonterminal.id}},
  {% endfor %}
  }

  # table[nonterminal][terminal] = rule
  table = [
    {% py parseTable = grammar.getParseTable() %}
    {% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}}],
    {% endfor %}
  ]

  {% for terminal in nonAbstractTerminals %}
  TERMINAL_{{terminal.string.upper()}} = {{terminal.id}}
  {% endfor %}

  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()

  def isTerminal(self, id):
    return 0 <= id <= {{len(nonAbstractTerminals) - 1}}

  def isNonTerminal(self, id):
    return {{len(nonAbstractTerminals)}} <= id <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}}

  def parse(self, tokens):
    self.tokens = tokens
    self.start = '{{str(grammar.start).upper()}}'
    tree = self.parse_{{str(grammar.start).lower()}}()
    if self.tokens.current() != None:
      raise SyntaxError( 'Finished parsing without consuming all tokens.' )
    return tree

  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError( 'No more tokens.  Expecting %s' % (self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError( 'Unexpected symbol when parsing %s.  Expected %s, got %s.' %(whosdaddy(), self.terminals[terminalId], currentToken if currentToken else 'None') )

    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) )

    return currentToken
 
  {% for nonterminal in LL1Nonterminals %}

  def parse_{{nonterminal.string.lower()}}(self):
    current = self.tokens.current()
    rule = self.table[{{nonterminal.id - len(nonAbstractTerminals)}}][current.getId()] if current else -1
    tree = ParseTree( NonTerminal({{nonterminal.id}}, self.nonterminals[{{nonterminal.id}}]))

      {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist'
      {% elif isinstance(nonterminal.macro, NonterminalListMacro) %}
    tree.list = 'nlist'
      {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist'
      {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist'
      {% else %}
    tree.list = False
      {% endif %}

      {% if nonterminal.empty %}
    if current != None and (current.getId() in [{{', '.join([str(a.id) for a in grammar.follow[nonterminal]])}}]):
      return tree
      {% endif %}

    if current == None:
      {% if nonterminal.empty or grammar.ε in grammar.first[nonterminal] %}
      return tree
      {% else %}
      raise SyntaxError('Error: unexpected end of file')
      {% endif %}
    
      {% for index, rule in enumerate(nonterminal.rules) %}

        {% if index == 0 %}
    if rule == {{rule.id}}:
        {% else %}
    elif rule == {{rule.id}}:
        {% endif %}

        {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% elif isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% else %}
      tree.astTransform = AstTransformSubstitution(0)
        {% endif %}

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
      t = self.expect({{morpheme.id}}) # {{morpheme.string}}
      tree.add(t)
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
      tree.listSeparator = t
            {% endif %}
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
      subtree = self.parse_{{morpheme.string.lower()}}()
      tree.add( subtree )
          {% endif %}

        {% endfor %}

      return tree

      {% endfor %}

      {% for exprGrammar in grammar.exprgrammars %}
        {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
          {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}

    elif current.getId() in [{{', '.join([str(x.id) for x in grammar.first[exprGrammar.nonterminal]])}}]:
          {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
          {% elif isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
          {% else %}
      tree.astTransform = AstTransformSubstitution(0)
          {% endif %}

          {% for morpheme in rule.production.morphemes %}

            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) ) # {{morpheme.string}}
            {% endif %}

            {% if isinstance(morpheme, NonTerminal) %}
      subtree = self.parse_{{morpheme.string.lower()}}()
      tree.add( subtree )
            {% endif %}
          {% endfor %}
        {% endif %}
      {% endfor %}

      {% if not nonterminal.empty %}
    raise SyntaxError('Error: Unexpected symbol (%s) when parsing %s' % (current, whoami()))
      {% else %}
    return tree
      {% endif %}

  {% endfor %}

  {% for exprGrammar in grammar.exprgrammars %}
  def parse_{{exprGrammar.nonterminal.string.lower()}}( self, rbp = 0):
    name = '{{exprGrammar.nonterminal.string.lower()}}'
    if name not in self.expressionParsers:
      self.expressionParsers[name] = ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}(self)
    return self.expressionParsers[name].parse(rbp)
  {% endfor %}

{% if addMain %}
if __name__ == '__main__':
  parser = Parser()

  try:
    tokens = TokenStream([
      {% for terminal in initialTerminals %}
      Terminal( parser.TERMINAL_{{terminal.upper()}} ),
      {% endfor %}
    ])
  except AttributeError as e:
    sys.stderr.write( str(e) + "\n" )
    sys.exit(-1)

  try:
    parsetree = parser.parse( tokens )
    if not parsetree or len(sys.argv) <= 1 or (len(sys.argv) > 1 and sys.argv[1] == 'parsetree'):
      print(ParseTreePrettyPrintable(parsetree))
    elif len(sys.argv) > 1 and sys.argv[1] == 'ast':
      ast = parsetree.toAst()
      print(AstPrettyPrintable(ast))
  except SyntaxError as e:
    print(e)
{% endif %}
