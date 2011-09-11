import sys

{% from hermes.Grammar import AstTranslation, AstSpecification %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import ExprListMacro, SeparatedListMacro, NonterminalListMacro, TerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}
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
    self.list = False
  def add( self, tree ):
    self.children.append( tree )
  def toAst( self ):
    if self.list == 'slist' or self.list == 'nlist':
      if len(self.children) == 0:
        return AstList()
      offset = 1 if not isinstance(self.children[0], ParseTree) else 0
      r = AstList([self.children[offset].toAst()])
      r.extend(self.children[offset+1].toAst())
      return r
    elif self.list == 'tlist':
      if len(self.children) == 0:
        return []
      r = AstList([self.children[0].toAst()])
      r.extend(self.children[2].toAst())
      return r
    elif self.isExpr:
      if isinstance(self.astTransform, AstTransformSubstitution):
        return self.children[self.astTransform.idx].toAst()
      elif isinstance(self.astTransform, AstTransformNodeCreator):
        parameters = {}
        for name, idx in self.astTransform.parameters.items():
          if isinstance(self.children[idx], ParseTree):
            parameters[name] = self.children[idx].toAst()
          elif isinstance(self.children[idx], list):
            parameters[name] = [x.toAst() for x in self.children[idx]]
          else:
            parameters[name] = self.children[idx]
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

class SyntaxError(Exception):
  def __init__(self, message, tracer = None):
    self.__dict__.update(locals())
  def __str__(self):
    return self.message

class TokenRecorder:
  def __init__(self):
    self.stack = []
    self.awake = False
  def wake(self):
    self.awake = True
    self.stack = []
    return self
  def sleep(self):
    self.awake = False
    return self
  def record(self, s):
    self.stack.append(s)
    return self
  def tokens(self):
    return self.stack

class Parser:
  def __init__(self):
    self.iterator = None
    self.sym = None
    self.recorder = TokenRecorder()
    self.entry_points = {
      {% for s,f in entry_points.items() %}
      '{{s}}': self.{{f}},
      {% endfor %}
    }

  {% for i,var in init['terminal_var'].items() %}
  {{var}} = {{i}}
  {% endfor %}

  terminal_str = {
  {% for i,string in init['terminal_str'].items() %}
    {{i}}: '{{string}}',
  {% endfor %}
  }

  nonterminal_str = {
  {% for i,string in init['nonterminal_str'].items() %}
    {{i}}: '{{string}}',
  {% endfor %}
  }
  
  str_terminal = {
  {% for i,string in init['terminal_str'].items() %}
    '{{string.lower()}}': {{i}},
  {% endfor %}
  }

  str_nonterminal = {
  {% for i,string in init['nonterminal_str'].items() %}
    '{{string.lower()}}': {{i}},
  {% endfor %}
  }

  terminal_count = {{init['terminal_count']}}
  nonterminal_count = {{init['nonterminal_count']}}
  parse_table = [
    {{init['parse_table']}}
  ]

  def terminal(self, str):
    return self.str_terminal[str]
  
  def terminalNames(self):
    return list(self.str_terminal.keys())
  
  def isTerminal(self, id):
    return {{init['terminal_start']}} <= id <= {{init['terminal_end']}}

  def isNonTerminal(self, id):
    return {{init['nonterminal_start']}} <= id <= {{init['nonterminal_end']}}

  def rewind(self, recorder):
    global tokens
    tokens = recorder.tokens().append(tokens)

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

  def parse(self, iterator, entry):
    self.iterator = iter(iterator)
    self.sym = self.getsym()
    tree = self.entry_points[entry]()
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

    if self.recorder.awake and self.sym is not None:
      self.recorder.record(self.sym)

    return self.sym

  def expect(self, s, tracer):
    if self.sym and s == self.sym.getId():
      symbol = self.sym
      self.sym = self.next()
      return symbol
    else:
      raise SyntaxError('Unexpected symbol.  Expected %s, got %s.' %(self.terminal_str[s], self.sym if self.sym else 'None'), tracer)

  def rule(self, n):
    if self.sym == None: return -1
    return self.parse_table[n - {{init['nonterminal_start']}}][self.sym.getId()]

  def call(self, nt_str):
    return getattr(self, nt_str)()
  

  {% for n in nt %}
  def _{{n['nt_obj'].string.upper()}}(self, depth = 0):
    rule = self.rule({{n['nt_obj'].id}})
    if depth is not False:
      tracer = DebugTracer("_{{n['nt_obj'].string.upper()}}", str(self.sym), rule, depth)
      depth = depth + 1
    else:
      tracer = None
    tree = ParseTree( NonTerminal({{n['nt_obj'].id}}, self.getAtomString({{n['nt_obj'].id}})), tracer )
    {% if isinstance(n['nt_obj'].macro, SeparatedListMacro) %}
    tree.list = 'slist'
    {% elif isinstance(n['nt_obj'].macro, NonterminalListMacro) %}
    tree.list = 'nlist'
    {% elif isinstance(n['nt_obj'].macro, TerminatedListMacro) %}
    tree.list = 'tlist'
    {% else %}
    tree.list = False
    {% endif %}

    {% if n['empty'] and len(n['follow']) %}
      {% for f in n['follow']%}
    if self.sym != None and ({{' or '.join(['self.sym.getId() == ' + str(a.id) for a in n['follow']])}}):
      return tree
      {% endfor %}
    {% endif %}

    if self.sym == None or self.sym.getId() in [{{', '.join(str(e.id) for e in n['escape_terminals'])}}]:
    {% if n['empty'] %}
      return tree
    {% else %}
      raise SyntaxError('Error: unexpected end of file', tracer)
    {% endif %}
  
    {% for index, rule in enumerate(n['rules']) %}

      {% if index == 0 %}
    if rule == {{rule['obj'].id}}:
      {% else %}
    elif rule == {{rule['obj'].id}}:
      {% endif %}
      {% if isinstance(rule['obj'].ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule['obj'].ast.idx}})
      {% elif isinstance(rule['obj'].ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule['obj'].ast.name}}', {{rule['obj'].ast.parameters}})
      {% else %}
      tree.astTransform = AstTransformSubstitution(0)
      {% endif %}
      {% for atom in rule['atoms'] %}

        {% if isinstance(atom, Terminal) %}
      tree.add( self.expect({{atom.id}}, tracer) ) # {{atom.string}}
        {% endif %}

        {% if isinstance(atom, NonTerminal) %}
      subtree = self._{{atom.string.upper()}}(depth)
      tree.add( subtree )
      if tracer and isinstance(subtree, ParseTree):
        tracer.add( subtree.tracer )
        {% endif %}

      {% endfor %}

      return tree

    {% endfor %}

    {% if n['lambda_path'] %}
    else:
      try:
        if not self.recorder.awake:
          self.recorder.wake()
        self.recorder.record(self.sym)
        {% if isinstance(n['lambda_path'].ast, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{n['lambda_path'].ast.idx}})
        {% elif isinstance(n['lambda_path'].ast, AstSpecification) %}
        tree.astTransform = AstTransformNodeCreator('{{n['lambda_path'].ast.name}}', {{n['lambda_path'].ast.parameters}})
        {% else %}
        tree.astTransform = AstTransformSubstitution(0)
        {% endif %}
        {% for atom in n['lambda_path_atoms'] %}

        {% if isinstance(atom, Terminal) %}
        tree.add( self.expect({{atom.id}}, tracer) ) # {{atom.string}}
        {% endif %}

        {% if isinstance(atom, NonTerminal) %}
        subtree = self._{{atom.string.upper()}}(depth)
        tree.add( subtree )
        if tracer and isinstance(subtree, ParseTree):
          tracer.add( subtree.tracer )
        {% endif %}
      {% endfor %}
      except SyntaxError as e:
        if self.recorder.awake:
          self.recorder.sleep()
          self.rewind(self.recorder)
        raise e
      return tree
    {% endif %}

    {% if not n['empty'] %}
    raise SyntaxError('Error: Unexpected symbol', tracer)
    {% else %}
    return tree
    {% endif %}

  {% endfor %}

  {% for index, exprParser in enumerate(nudled) %}

  infixBp{{index}} = {
    {% for terminal_id, binding_power in exprParser['infixPrecedence'].items() %}
    {{terminal_id}}: {{binding_power}},
    {% endfor %}
  }

  prefixBp{{index}} = {
    {% for terminal_id, binding_power in exprParser['prefixPrecedence'].items() %}
    {{terminal_id}}: {{binding_power}},
    {% endfor %}
  }

  def {{exprParser['grammar'].nonterminal.string.lower().strip('_')}}(self):
    return self._{{exprParser['grammar'].nonterminal.string.upper()}}()
  def _{{exprParser['grammar'].nonterminal.string.upper()}}( self, rbp = 0, depth = 0 ):
    t = self.sym
    if depth is not False:
      tracer = DebugTracer("(expr) _{{exprParser['grammar'].nonterminal.string.upper()}}", str(self.sym), 'N/A', depth)
      depth = depth + 1
    else:
      tracer = None
    left = self.nud{{index}}(depth)
    if isinstance(left, ParseTree):
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
    tree = ParseTree( NonTerminal({{exprParser['grammar'].nonterminal.id}}, '{{exprParser['grammar'].nonterminal.string.lower()}}') )

    {% py seen = list() %}
    {% for rule in exprParser['grammar'].rules %}
      {% py nud = rule.nudProduction.morphemes %}
      {% if len(nud) and nud[0] not in seen %}
    {{'if' if len(seen)==0 else 'elif'}} self.sym.getId() == {{nud[0].id}}: # {{nud[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

        {% if len(nud) == 1 %}
      return self.expect( {{nud[0].id}}, tracer )
        {% else %}
          {% for morpheme in nud %}
            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}, tracer) )
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
              {% if isinstance(rule.operator, PrefixOperator) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}( self.prefixBp{{index}}[{{rule.operator.operator.id}}] ) )
              {% else %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
              {% endif %}
            {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
            {% elif isinstance(morpheme, ExprListMacro) %}
      ls = AstList()
      if self.sym.getId() not in [{{', '.join([str(x.id) for x in morpheme.follow])}}]:
        while 1:
          ls.append( self._{{morpheme.nonterminal.string.upper()}}() )
          if self.sym.getId() != {{morpheme.separator.id}}:
            break
          self.expect({{morpheme.separator.id}}, tracer)
      tree.add( ls )
            {% endif %}
          {% endfor %}
        {% endif %}
        {% py seen.append(nud[0]) %}
      {% endif %}
    {% endfor %}

    return tree

  def led{{index}}(self, left, tracer):
    tree = ParseTree( NonTerminal({{exprParser['grammar'].nonterminal.id}}, '{{exprParser['grammar'].nonterminal.string.lower()}}') )

    {% py seen = list() %}
    {% for rule in exprParser['grammar'].rules %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) and led[0] not in seen %}
    {{'if' if len(seen)==0 else 'elif'}}  self.sym.getId() == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

      if left:
        tree.add(left)

        {% if len(led) == 1 %}
      return self.expect( {{led[0].id}}, tracer )
        {% else %}
          {% for morpheme in led %}
            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}, tracer) )
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
              {% if isinstance(rule.operator, InfixOperator) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}( self.infixBp{{index}}[{{rule.operator.operator.id}}] ) )
              {% else %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
              {% endif %}
            {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self._{{rule.nonterminal.string.upper()}}() )
            {% elif isinstance(morpheme, ExprListMacro) %}
      ls = AstList()
      if self.sym.getId() not in [{{', '.join([str(x.id) for x in morpheme.follow])}}]:
        while 1:
          ls.append( self._{{morpheme.nonterminal.string.upper()}}() )
          if self.sym.getId() != {{morpheme.separator.id}}:
            break
          self.expect({{morpheme.separator.id}}, tracer)
      tree.add( ls )
            {% endif %}
          {% endfor %}
        {% endif %}
        {% py seen.append(led[0]) %}
      {% endif %}
    {% endfor %}

    return tree
{% endfor %}

{% if add_main %}
if __name__ == '__main__':
  p = Parser()

  try:
    tokens = [
      {% for t in tokens %}
      Terminal( p.TERMINAL_{{t.upper()}} ),
      {% endfor %}
    ]
  except AttributeError as e:
    sys.stderr.write( str(e) + "\n" )
    sys.exit(-1)

  try:
    parsetree = p.parse( tokens, '{{entry}}' )
    if not parsetree or len(sys.argv) <= 1 or (len(sys.argv) > 1 and sys.argv[1] == 'parsetree'):
      print(parsetree)
    elif len(sys.argv) > 1 and sys.argv[1] == 'ast':
      print(parsetree.toAst())
  except SyntaxError as e:
    print(e)
{% endif %}
