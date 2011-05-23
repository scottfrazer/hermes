import sys

{% from hermes.Grammar import AstTranslation, AstSpecification %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro %}

def parse( iterator, entry ):
  p = Parser()
  return p.parse(iterator, entry)
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
class ParseTree():
  def __init__(self, nonterminal):
    self.children = []
    self.nonterminal = nonterminal
    self.astTransform = None
    self.isExpr = False
    self.list = False
  def add( self, tree ):
    self.children.append( tree )
  def toAst( self ):
    if self.list == 'slist' or self.list == 'nlist':
      if len(self.children) == 0:
        return []
      offset = 1 if not isinstance(self.children[0], ParseTree) else 0
      r = [self.children[offset].toAst()]
      r.extend(self.children[offset+1].toAst())
      return r
    elif self.list == 'tlist':
      if len(self.children) == 0:
        return []
      r = [self.children[0].toAst()]
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
  def __init__(self, message):
    self.message = message
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
      raise SyntaxError('Syntax Error: Finished parsing without consuming all tokens.')
    self.iterator = None
    self.sym = None
    return tree

  def next(self):
    self.sym = self.getsym()

    if self.sym is not None and not self.isTerminal(self.sym.getId()):
      self.sym = None
      raise SyntaxError('Invalid symbol ID: %d (%s)'%(self.sym.getId(), self.sym))

    if self.recorder.awake and self.sym is not None:
      self.recorder.record(self.sym)

    return self.sym

  def expect(self, s):
    if self.sym and s == self.sym.getId():
      symbol = self.sym
      self.sym = self.next()
      return symbol
    else:
      raise SyntaxError('Unexpected symbol.  Expected %s, got %s.' %(self.terminal_str[s], self.sym if self.sym else 'None'))

  def rule(self, n):
    if self.sym == None: return -1
    return self.parse_table[n - {{init['nonterminal_start']}}][self.sym.getId()]

  {% for n in nt %}
  def {{n['func_name']}}(self):
    rule = self.rule({{n['id']}})
    tree = ParseTree( NonTerminal({{n['id']}}, self.getAtomString({{n['id']}})) )
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

    if self.sym == None{% for e in n['escape_terminals'] %} or self.sym.getId() == self.{{e}}{%endfor%}:
    {% if n['empty'] %}
      return tree
    {% else %}
      raise SyntaxError('Error: unexpected end of file')
    {% endif %}
  
    {% for rule in n['rules'] %}

      {% if rule['idx'] == 0 %}
    if rule == {{rule['id']}}:
      {% else %}
    elif rule == {{rule['id']}}:
      {% endif %}
      {% if isinstance(rule['obj'].ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule['obj'].ast.idx}})
      {% elif isinstance(rule['obj'].ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule['obj'].ast.name}}', {{rule['obj'].ast.parameters}})
      {% else %}
      tree.astTransform = AstTransformSubstitution(0)
      {% endif %}
      {% for atom in rule['atoms'] %}

        {% if atom['type'] == 'terminal' %}
      tree.add( self.expect(self.{{atom['terminal_var_name']}}) )
        {% endif %}

        {% if atom['type'] == 'nonterminal' %}
      tree.add( self.{{atom['nonterminal_func_name']}}() )
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

        {% if atom['type'] == 'terminal' %}
        tree.add( self.expect(self.{{atom['terminal_var_name']}}) )
        {% endif %}

        {% if atom['type'] == 'nonterminal' %}
        tree.add( self.{{atom['nonterminal_func_name']}}() )
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
    raise SyntaxError('Error: Unexpected symbol')
    {% else %}
    return tree
    {% endif %}

  {% endfor %}

  {% for index, exprParser in enumerate(nudled) %}
  bp{{index}} = {
    {% for nonterminal_id, binding_power in exprParser['precedence'].items() %}
    {{nonterminal_id}}: {{binding_power}},
    {% endfor %}
  }
  def _{{exprParser['nonterminal'].upper()}}( self, rbp = 0 ):
    t = self.sym
    left = self.nud()
    while rbp < self.binding_power(self.sym, self.bp{{index}}):
      left = self.led(left)
    left.isExpr = True
    return left

  def nud(self):
    tree = ParseTree( NonTerminal(self.str_nonterminal['_expr'], '_expr') )
    {% for sym, actions in exprParser['nud'].items() %}
    if self.sym.getId() == {{sym}}:
      {% for action in actions %}

        {% if action['type'] == 'symbol' and len(actions) == 1 %}
      return self.expect({{action['sym']}})

        {% elif action['type'] == 'symbol' %}
      tree.add( self.expect({{action['sym']}}) )
      
        {% elif action['type'] == 'symbol-append' %}
      tree.add( self.expect({{action['sym']}}) ) #here?

        {% elif action['type'] == 'infix' %}
      pass # infix noop

        {% elif action['type'] == 'prefix' %}
      tree.add( self.expect(self.sym.getId()) )
      tree.add( self.__EXPR({{action['binding_power']}}) )

        {% elif action['type'] == 'list' %}
      ls = []
      tree.add( self.expect({{action['open_sym']}}) )
      if self.sym.getId() != {{action['close_sym']}}:
        while 1:
          ls.append( self.{{action['nonterminal_func']}}() )
          if self.sym.getId() != {{action['separator']}}:
            break
          self.expect({{action['separator']}})
      tree.add( ls )
      tree.add( self.expect({{action['close_sym']}}) )

        {% elif action['type'] == 'nonterminal' %}
      
      tree.add(self.{{action['nonterminal_func']}}())

        {% endif %}

        {% if isinstance(action['rule'].ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{action['rule'].ast.name}}', {{action['rule'].ast.parameters}})
        {% elif isinstance(action['rule'].ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{action['rule'].ast.idx}})
        {% endif %}

      {% endfor %}
      return tree
    {% endfor %}

    {% if len(exprParser['nud']) == 0 %}
    pass
    {% endif %}

  def led(self, left):
    tree = ParseTree( NonTerminal(self.str_nonterminal['_expr'], '_expr') )
    {% for sym, actions in exprParser['led'].items() %}
    if self.sym.getId() == {{sym}}:
      if left:
        tree.add( left )
      {% for action in actions %}
        {% if action['type'] == 'symbol' and len(actions) == 1 %}
      return self.expect({{action['sym']}})
        {% elif action['type'] == 'symbol' %}
      tree.add( self.expect({{action['sym']}}) )
        {% elif action['type'] == 'symbol-append' %}
      tree.add( self.expect({{action['sym']}}) )
        {% elif action['type'] == 'infix' %}
      tree.add( self.expect(self.sym.getId()) )
      tree.add( self.__EXPR({{action['binding_power']}}) )
        {% elif action['type'] == 'prefix' %}
      pass # prefix noop
        {% elif action['type'] == 'list' %}
      ls = []
      tree.add( self.expect({{action['open_sym']}}) )
      if self.sym.getId() != {{action['close_sym']}}:
        while 1:
          ls.append( self.{{action['nonterminal_func']}}() )
          if self.sym.getId() != {{action['separator']}}:
            break
          self.expect({{action['separator']}})
      tree.add( ls )
      tree.add( self.expect({{action['close_sym']}}) )
        {% elif action['type'] == 'nonterminal' %}
          {% if action['nonterminal_func'] == '__EXPR' %}
      tree.add(self.{{action['nonterminal_func']}}({{action['binding_power']}}))
          {% else %}
      tree.add(self.{{action['nonterminal_func']}}())
          {% endif %}
        {% endif %}

        {% if isinstance(action['rule'].ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{action['rule'].ast.name}}', {{action['rule'].ast.parameters}})
        {% elif isinstance(action['rule'].ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{action['rule'].ast.idx}})
        {% endif %}

      {% endfor %}
      return tree
    {% endfor %}

    {% if len(exprParser['led']) == 0 %}
    pass
    {% endif %}
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
