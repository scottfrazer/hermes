import sys

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

import inspect
def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]

def parse( iterator, entry ):
  p = Parser()
  return p.parse(iterator, entry)
class DebugTracer:
  def __init__(self, func, symbol, rule, callDepth ):
    self.__dict__.update(locals())
    self.children = []
  
  def add(self, child):
    self.children.append(child)
  
  def __str__(self):
    s = '%s[%s, symbol: %s, rule: %s]\n' % (' '.join(['' for i in range(self.callDepth)]), self.func, self.symbol, str(self.rule))
    for child in self.children:
      s += str(child)
    return s
  
class Terminal:
  def __init__(self, id):
    self.id=id
    self.str=Parser.terminal_str[id]
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
  def __init__(self, nonterminal, tracer = None):
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
          else:
            child = self.children[idx]

          if isinstance(child, ParseTree):
            parameters[name] = child.toAst()
          elif isinstance(child, list):
            parameters[name] = [x.toAst() for x in child]
          else:
            parameters[name] = child
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
      string = '%s(%s:\n' % (indentStr, parsetree.nonterminal)
      string += ',\n'.join([ \
        '%s  %s' % (indentStr, self._prettyPrint(value, indent + 2).lstrip()) for value in parsetree.children \
      ])
      string += '\n%s)' % (indentStr)
      return string
    elif isinstance(parsetree, Terminal):
      return '%s%s' % (indentStr, parsetree.toString(self.tokenFormat))
    else:
      return '%s%s' % (indentStr, parsetree)

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
        return '%s[]' % (indentStr)
      string = '%s[\n' % (indentStr)
      string += ',\n'.join([self._prettyPrint(element, indent + 2) for element in ast])
      string += '\n%s]' % (indentStr)
      return string
    elif isinstance(ast, Terminal):
      return '%s%s' % (indentStr, ast.toString(self.tokenFormat))
    else:
      return '%s%s' % (indentStr, ast)

class SyntaxError(Exception):
  def __init__(self, message, tracer = None):
    self.__dict__.update(locals())
  def __str__(self):
    return self.message

class Parser:
  def __init__(self):
    self.iterator = None
    self.sym = None

  {% for terminal in nonAbstractTerminals %}
  {{terminal.varname}} = {{terminal.id}}
  {% endfor %}

  terminal_str = {
  {% for terminal in nonAbstractTerminals %}
    {{terminal.id}}: '{{terminal.string}}',
  {% endfor %}
  }

  nonterminal_str = {
  {% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: '{{nonterminal.string}}',
  {% endfor %}
  }
  
  str_terminal = {
  {% for terminal in nonAbstractTerminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
  {% endfor %}
  }

  str_nonterminal = {
  {% for nonterminal in grammar.nonterminals %}
    '{{nonterminal.string.lower()}}': {{nonterminal.id}},
  {% endfor %}
  }

  terminal_count = {{len(nonAbstractTerminals)}}
  nonterminal_count = {{len(grammar.nonterminals)}}

  parse_table = [
    {% py parseTable = grammar.getParseTable() %}
    {% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}}],
    {% endfor %}
  ]

  def terminal(self, str):
    return self.str_terminal[str]
  
  def terminalNames(self):
    return list(self.str_terminal.keys())
  
  def isTerminal(self, id):
    return 0 <= id <= {{len(nonAbstractTerminals) - 1}}

  def isNonTerminal(self, id):
    return {{len(nonAbstractTerminals)}} <= id <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}}

  def binding_power(self, sym, bp):
    try:
      return bp[sym.getId()]
    except KeyError:
      return 0
    except AttributeError:
      return 0

  def getAtomString(self, id):
    if self.isTerminal(id):
      return self.terminal_str[id]
    elif self.isNonTerminal(id):
      return self.nonterminal_str[id]
    return ''

  def getsym(self):
    try:
      return next( self.iterator )
    except StopIteration:
      return None

  def parse(self, iterator):
    self.iterator = iter(iterator)
    self.sym = self.getsym()
    self.start = '{{str(grammar.start).upper()}}'
    tree = self._{{str(grammar.start).upper()}}()
    if self.sym != None:
      raise SyntaxError('Syntax Error: Finished parsing without consuming all tokens.', tree.tracer)
    self.iterator = None
    self.sym = None
    return tree

  def next(self):
    self.sym = self.getsym()

    if self.sym is not None and not self.isTerminal(self.sym.getId()):
      self.sym = None
      raise SyntaxError('Invalid symbol ID: %d (%s)'%(self.sym.getId(), self.sym), None)

    return self.sym

  def expect(self, s, tracer):
    if self.sym and s == self.sym.getId():
      symbol = self.sym
      self.sym = self.next()
      return symbol
    else:
      raise SyntaxError('Unexpected symbol when parsing %s.  Expected %s, got %s.' %(whosdaddy(), self.terminal_str[s], self.sym if self.sym else 'None'), tracer)

  def rule(self, n):
    if self.sym == None: return -1
    return self.parse_table[n - {{len(nonAbstractTerminals)}}][self.sym.getId()]

  def call(self, nt_str):
    return getattr(self, nt_str)()
 
  {% for nonterminal in LL1Nonterminals %}

  def _{{nonterminal.string.upper()}}(self, depth=0, tracer=None):
    rule = self.rule({{nonterminal.id}})

    tree = ParseTree( NonTerminal({{nonterminal.id}}, self.getAtomString({{nonterminal.id}})), tracer )

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
    if self.sym != None and (self.sym.getId() in [{{', '.join([str(a.id) for a in grammar.follow[nonterminal]])}}]):
      return tree
      {% endif %}

    if self.sym == None:
      {% if nonterminal.empty or grammar.ε in grammar.first[nonterminal] %}
      return tree
      {% else %}
      raise SyntaxError('Error: unexpected end of file', tracer)
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
      t = self.expect({{morpheme.id}}, tracer) # {{morpheme.string}}
      tree.add(t)
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
      tree.listSeparator = t
            {% endif %}
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
      subtree = self._{{morpheme.string.upper()}}(depth)
      tree.add( subtree )
      if tracer and isinstance(subtree, ParseTree):
        tracer.add( subtree.tracer )
          {% endif %}

        {% endfor %}

      return tree

      {% endfor %}

      {% for exprGrammar in grammar.exprgrammars %}
        {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
          {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}

    elif self.sym.getId() in [{{', '.join([str(x.id) for x in grammar.first[exprGrammar.nonterminal]])}}]:
          {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
          {% elif isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
          {% else %}
      tree.astTransform = AstTransformSubstitution(0)
          {% endif %}

          {% for morpheme in rule.production.morphemes %}

            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}, tracer) ) # {{morpheme.string}}
            {% endif %}

            {% if isinstance(morpheme, NonTerminal) %}
      subtree = self._{{morpheme.string.upper()}}(depth)
      tree.add( subtree )
      if tracer and isinstance(subtree, ParseTree):
        tracer.add( subtree.tracer )
            {% endif %}
          {% endfor %}
        {% endif %}
      {% endfor %}

      {% if not nonterminal.empty %}
    raise SyntaxError('Error: Unexpected symbol (%s) when parsing %s' % (self.sym, whoami()), tracer)
      {% else %}
    return tree
      {% endif %}

  {% endfor %}

  {% for index, exprGrammar in enumerate(grammar.exprgrammars) %}

  infixBp{{index}} = {
    {% for terminal_id, binding_power in exprGrammar.infix.items() %}
    {{terminal_id}}: {{binding_power}},
    {% endfor %}
  }

  prefixBp{{index}} = {
    {% for terminal_id, binding_power in exprGrammar.prefix.items() %}
    {{terminal_id}}: {{binding_power}},
    {% endfor %}
  }

  def {{exprGrammar.nonterminal.string.lower().strip('_')}}(self):
    return self._{{exprGrammar.nonterminal.string.upper()}}()
  def _{{exprGrammar.nonterminal.string.upper()}}( self, rbp = 0, depth = 0 ):
    t = self.sym
    if depth is not False:
      tracer = DebugTracer("(expr) _{{exprGrammar.nonterminal.string.upper()}}", str(self.sym), 'N/A', depth)
      depth = depth + 1
    else:
      tracer = None
    left = self.nud{{index}}(depth)
    if isinstance(left, ParseTree):
      left.isExpr = True
      left.isNud = True
      tracer.add(left.tracer)
    while rbp < self.binding_power(self.sym, self.infixBp{{index}}):
      left = self.led{{index}}(left, depth)
      if isinstance(left, ParseTree):
        tracer.add(left.tracer)
    if left:
      left.isExpr = True
      left.tracer = tracer
    return left

  def nud{{index}}(self, tracer):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )

    if not self.sym:
      return tree

    {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
      {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}
      {% if len(ruleFirstSet) %}
    {{'if' if i == 0 else 'elif'}} self.sym.getId() in [{{', '.join([str(x.id) for x in exprGrammar.ruleFirst(rule)])}}]:

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

      tree.nudMorphemeCount = {{len(rule.nudProduction)}}

        {% if len(rule.nudProduction) == 1 and isinstance(rule.nudProduction.morphemes[0], Terminal) %}
      return self.expect( {{rule.nudProduction.morphemes[0].id}}, tracer )
        {% else %}
          {% for morpheme in rule.nudProduction.morphemes %}
            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}, tracer) )
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
              {% if isinstance(rule.operator, PrefixOperator) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}( self.prefixBp{{index}}[{{rule.operator.operator.id}}] ) )
      tree.isPrefix = True
              {% else %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
              {% endif %}
            {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self._{{morpheme.string.upper()}}() )
            {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self._{{morpheme.start_nt.string.upper()}}() )
            {% endif %}
          {% endfor %}
        {% endif %}
      {% endif %}
    {% endfor %}

    return tree

  def led{{index}}(self, left, tracer):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )

    {% py seen = list() %}
    {% for rule in exprGrammar.rules %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) and led[0] not in seen %}
    {{'if' if len(seen)==0 else 'elif'}}  self.sym.getId() == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

      {% if len(rule.nudProduction) == 1 and rule.nudProduction.morphemes[0] == rule.nonterminal%}
      tree.isExprNud = True
      {% endif %}

      if left:
        tree.add(left)

        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}, tracer) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, InfixOperator) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}( self.infixBp{{index}}[{{rule.operator.operator.id}}] ) )
      tree.isInfix = True
            {% else %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self._{{morpheme.string.upper()}}() )
          {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self._{{morpheme.start_nt.string.upper()}}() )
          {% endif %}
        {% endfor %}
        {% py seen.append(led[0]) %}
      {% endif %}
    {% endfor %}

    return tree
{% endfor %}

{% if addMain %}
if __name__ == '__main__':
  parser = Parser()

  try:
    tokens = [
      {% for terminal in initialTerminals %}
      Terminal( parser.TERMINAL_{{terminal.upper()}} ),
      {% endfor %}
    ]
  except AttributeError as e:
    sys.stderr.write( str(e) + "\n" )
    sys.exit(-1)

  try:
    parsetree = parser.parse( tokens )
    if not parsetree or len(sys.argv) <= 1 or (len(sys.argv) > 1 and sys.argv[1] == 'parsetree'):
      print(parsetree)
    elif len(sys.argv) > 1 and sys.argv[1] == 'ast':
      ast = parsetree.toAst()
      if isinstance(ast, list):
        print('[%s]' % (', '.join([str(x) for x in ast])))
      else:
        print(ast)
  except SyntaxError as e:
    print(e)
{% endif %}
