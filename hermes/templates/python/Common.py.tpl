from collections import OrderedDict
import base64

def no_color(string, color):
  return string

def term_color(string, intcolor):
  return "\033[38;5;%dm%s\033[0m" % (intcolor, string)

class Terminal:
  def __init__(self, id, str, source_string, resource, line, col):
    self.__dict__.update(locals())
  def getId(self):
    return self.id
  def toAst(self):
    return self
  def __str__(self):
    return '<{} (line {} col {}) `{}`>'.format(self.str, self.line, self.col, self.source_string)

class NonTerminal():
  def __init__(self, id, str):
    self.__dict__.update(locals())
    self.list = False
  def __str__(self):
    return self.str

class AstTransform:
  pass

class AstTransformSubstitution(AstTransform):
  def __init__(self, idx):
    self.__dict__.update(locals())
  def __repr__(self):
    return '$' + str(self.idx)
  def __str__(self):
    return self.__repr__()

class AstTransformNodeCreator(AstTransform):
  def __init__( self, name, parameters ):
    self.__dict__.update(locals())
  def __repr__( self ):
    return self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )'
  def __str__(self):
    return self.__repr__()

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
      first = self.children[offset].toAst()
      r = AstList()
      if first is not None:
        r.append(first)
      r.extend(self.children[offset+1].toAst())
      return r
    elif self.list == 'otlist':
      if len(self.children) == 0:
        return AstList()
      r = AstList()
      if self.children[0] != self.listSeparator:
        r.append(self.children[0].toAst())
      r.extend(self.children[1].toAst())
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
        parameters = OrderedDict()
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
        parameters = OrderedDict()
        for name, idx in self.astTransform.parameters.items():
          parameters[name] = self.children[idx].toAst()
        return Ast(self.astTransform.name, parameters)
      elif len(self.children):
        return self.children[0].toAst()
      else:
        return None

  def dumps(self, indent=None, color=False):
    if indent is None:
      return self._to_string(color)
    else:
      return self._to_string_indented(indent, color)

  def _to_string(self, color):
    colored = term_color if color else no_color
    children = []
    for child in self.children:
      if isinstance(child, list):
        children.append('[' + ', '.join([str(a) for a in child]) + ']')
      else:
        children.append(str(child))
    return '({0}: {1})'.format(colored(self.nonterminal, 10), ', '.join(children))

  def _to_string_indented(self, indent, color):
    colored = term_color if color else no_color
    indent_str = ''.join([' ' for x in range(indent)])
    if isinstance(parsetree, ParseTree):
      if len(parsetree.children) == 0:
        return '(%s: )' % (colored(parsetree.nonterminal, 10))
      string = '%s(%s:\n' % (indent_str, colored(parsetree.nonterminal, 10))
      string += ',\n'.join([ \
        '%s  %s' % (indent_str, self._prettyPrint(value, indent + 2).lstrip()) for value in parsetree.children \
      ])
      string += '\n%s)' % (indent_str)
      return string
    elif isinstance(parsetree, Terminal):
      return '%s%s' % (indent_str, colored(str(parsetree), 9))
    else:
      return '%s%s' % (indent_str, colored(parsetree, 9))

class ParseTreePrettyPrintable:
  def __init__(self, ast, color=False):
    self.__dict__.update(locals())
  def __str__(self):
    return self._prettyPrint(self.ast, 0)
  def _prettyPrint(self, parsetree, indent = 0):
    colored = term_color if self.color else no_color
    indentStr = ''.join([' ' for x in range(indent)])
    if isinstance(parsetree, ParseTree):
      if len(parsetree.children) == 0:
        return '(%s: )' % (colored(parsetree.nonterminal, 10))
      string = '%s(%s:\n' % (indentStr, colored(parsetree.nonterminal, 10))
      string += ',\n'.join([ \
        '%s  %s' % (indentStr, self._prettyPrint(value, indent + 2).lstrip()) for value in parsetree.children \
      ])
      string += '\n%s)' % (indentStr)
      return string
    elif isinstance(parsetree, Terminal):
      return '%s%s' % (indentStr, colored(str(parsetree), 9))
    else:
      return '%s%s' % (indentStr, colored(parsetree, 9))

class Ast():
  def __init__(self, name, attributes):
    self.__dict__.update(locals())
  def getAttr(self, attr):
    return self.attributes[attr]
  def __str__(self):
    return '(%s: %s)' % (self.name, ', '.join('%s=%s'%(str(k), '[' + ', '.join([str(x) for x in v]) + ']' if isinstance(v, list) else str(v) ) for k,v in self.attributes.items()))

class AstPrettyPrintable:
  def __init__(self, ast, color=False):
    self.__dict__.update(locals())
  def getAttr(self, attr):
    return self.ast.getAttr(attr)
  def __str__(self):
    return self._prettyPrint(self.ast, 0)
  def _prettyPrint(self, ast, indent = 0):
    indent_str = ''.join([' ' for x in range(indent)])
    colored = no_color
    if self.color:
      colored = term_color
    if isinstance(ast, Ast):
      string = '%s(%s:\n' % (indent_str, colored(ast.name, 12))
      string += ',\n'.join([ \
        '%s  %s=%s' % (indent_str, colored(name, 10), self._prettyPrint(value, indent + 2).lstrip()) for name, value in ast.attributes.items() \
      ])
      string += '\n%s)' % (indent_str)
      return string
    elif isinstance(ast, list):
      if len(ast) == 0:
        return '%s[]' % (indent_str)
      string = '%s[\n' % (indent_str)
      string += ',\n'.join([self._prettyPrint(element, indent + 2) for element in ast])
      string += '\n%s]' % (indent_str)
      return string
    elif isinstance(ast, Terminal):
      return '%s%s' % (indent_str, colored(str(ast), 9))
    else:
      return '%s%s' % (indent_str, colored(str(ast), 9))

class SyntaxError(Exception):
  def __init__(self, message):
    self.__dict__.update(locals())
  def __str__(self):
    return self.message

class TokenStream(list):
  def __init__(self, arg=[]):
    super().__init__(arg)
    self.index = 0
  def advance(self):
    self.index += 1
    return self.current()
  def last(self):
    return self[-1]
  def json(self):
    if len(self) == 0:
      return '[]'
    tokens_json = []
    json_fmt = '"terminal": "{terminal}", "resource": "{resource}", "line": {line}, "col": {col}, "source_string": "{source_string}"'
    for token in self:
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
    return '[\n    ' + ',\n    '.join(tokens_json) + '\n]'
  def current(self):
    try:
      return self[self.index]
    except IndexError:
      return None

class DefaultSyntaxErrorFormatter:
  def unexpected_eof(self, nonterminal, expected_terminals, nonterminal_rules):
    return "Error: unexpected end of file"
  def excess_tokens(self, nonterminal, terminal):
    return "Finished parsing without consuming all tokens."
  def unexpected_symbol(self, nonterminal, actual_terminal, expected_terminals, rule):
    return "Unexpected symbol (line {line}, col {col}) when parsing parse_{nt}.  Expected {expected}, got {actual}.".format(
      line=actual_terminal.line,
      col=actual_terminal.col,
      nt=nonterminal,
      expected=', '.join(expected_terminals),
      actual=actual_terminal
    )
  def no_more_tokens(self, nonterminal, expected_terminal, last_terminal):
    return "No more tokens.  Expecting " + expected_terminal
  def invalid_terminal(nonterminal, invalid_terminal):
    return "Invalid symbol ID: {} ({})".format(invalid_terminal.id, invalid_terminal.string)

class ParserContext:
  def __init__(self, tokens, error_formatter):
    self.__dict__.update(locals())
    self.nonterminal_string = None
    self.rule_string = None
