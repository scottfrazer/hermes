import sys
import os
import re
import base64
import argparse
import json
from collections import OrderedDict
# Common Code #
def no_color(string, color):
  return string
def term_color(string, intcolor):
  return "\033[38;5;{0}m{1}\033[0m".format(intcolor, string)
def parse_tree_string(parsetree, indent=None, color=no_color, b64_source=False, indent_level=0):
    indent_str = (' ' * indent * indent_level) if indent else ''
    if isinstance(parsetree, ParseTree):
        children = [parse_tree_string(child, indent, color, b64_source, indent_level+1) for child in parsetree.children]
        if indent is None or len(children) == 0:
            return '{0}({1}: {2})'.format(indent_str, color(parsetree.nonterminal, 10), ', '.join(children))
        else:
            return '{0}({1}:\n{2}\n{3})'.format(
                indent_str,
                color(parsetree.nonterminal, 10),
                ',\n'.join(children),
                indent_str
            )
    elif isinstance(parsetree, Terminal):
        return indent_str + color(parsetree.dumps(b64_source=b64_source), 6)
def ast_string(ast, indent=None, color=no_color, b64_source=False, indent_level=0):
    indent_str = (' ' * indent * indent_level) if indent else ''
    next_indent_str = (' ' * indent * (indent_level+1)) if indent else ''
    if isinstance(ast, Ast):
        children = OrderedDict([(k, ast_string(v, indent, color, b64_source, indent_level+1)) for k, v in ast.attributes.items()])
        if indent is None:
            return '({0}: {1})'.format(
                color(ast.name, 9),
                ', '.join('{0}={1}'.format(color(k, 2), v) for k, v in children.items())
            )
        else:
            return '({0}:\n{1}\n{2})'.format(
                color(ast.name, 9),
                ',\n'.join(['{0}{1}={2}'.format(next_indent_str, color(k, 2), v) for k, v in children.items()]),
                indent_str
            )
    elif isinstance(ast, list):
        children = [ast_string(element, indent, color, b64_source, indent_level+1) for element in ast]
        if indent is None or len(children) == 0:
            return '[{0}]'.format(', '.join(children))
        else:
            return '[\n{1}\n{0}]'.format(
                indent_str,
                ',\n'.join(['{0}{1}'.format(next_indent_str, child) for child in children]),
            )
    elif isinstance(ast, Terminal):
        return color(ast.dumps(b64_source=b64_source), 6)
class Terminal:
  def __init__(self, id, str, source_string, resource, line, col):
    self.__dict__.update(locals())
  def getId(self):
    return self.id
  def toAst(self):
    return self
  def dumps(self, b64_source=False, **kwargs):
    source_string = base64.b64encode(self.source_string.encode('utf-8')).decode('utf-8') if b64_source else self.source_string
    return '<{} (line {} col {}) `{}`>'.format(self.str, self.line, self.col, source_string)
  def __str__(self):
    return self.dumps()
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
  def dumps(self, indent=None, color=no_color, b64_source=False):
      args = locals()
      del args['self']
      return ast_string(self, **args)
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
  def dumps(self, indent=None, color=no_color, b64_source=False):
      args = locals()
      del args['self']
      return parse_tree_string(self, **args)
class Ast():
    def __init__(self, name, attributes):
        self.__dict__.update(locals())
    def getAttr(self, attr):
        return self.attributes[attr]
    def dumps(self, indent=None, color=no_color, b64_source=False):
        args = locals()
        del args['self']
        return ast_string(self, **args)
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
# Parser Code #
terminals = {
    0: 'partials',
    1: 'right',
    2: 'terminal',
    3: 'grammar',
    4: 'rbrace',
    5: 'parser_expression',
    6: 'infix_rule_hint',
    7: 'mixfix_rule_hint',
    8: 'colon',
    9: 'unary',
    10: 'expr_rule_hint',
    11: 'lexer',
    12: 'string',
    13: 'no_group',
    14: 'arrow',
    15: 'dash',
    16: 'code',
    17: 'null',
    18: 'left',
    19: 'regex_partial',
    20: 'lsquare',
    21: 'rangle',
    22: 'equals',
    23: 'parser_ll1',
    24: 'comma',
    25: 'rparen',
    26: 'nonterminal',
    27: 'll1_rule_hint',
    28: 'mode',
    29: 'regex',
    30: 'pipe',
    31: 'langle',
    32: 'rsquare',
    33: 'lparen',
    34: 'prefix_rule_hint',
    35: 'expression_divider',
    36: 'identifier',
    37: 'lbrace',
    38: 'asterisk',
    39: 'nonterminal_reference',
    40: 'integer',
    'partials': 0,
    'right': 1,
    'terminal': 2,
    'grammar': 3,
    'rbrace': 4,
    'parser_expression': 5,
    'infix_rule_hint': 6,
    'mixfix_rule_hint': 7,
    'colon': 8,
    'unary': 9,
    'expr_rule_hint': 10,
    'lexer': 11,
    'string': 12,
    'no_group': 13,
    'arrow': 14,
    'dash': 15,
    'code': 16,
    'null': 17,
    'left': 18,
    'regex_partial': 19,
    'lsquare': 20,
    'rangle': 21,
    'equals': 22,
    'parser_ll1': 23,
    'comma': 24,
    'rparen': 25,
    'nonterminal': 26,
    'll1_rule_hint': 27,
    'mode': 28,
    'regex': 29,
    'pipe': 30,
    'langle': 31,
    'rsquare': 32,
    'lparen': 33,
    'prefix_rule_hint': 34,
    'expression_divider': 35,
    'identifier': 36,
    'lbrace': 37,
    'asterisk': 38,
    'nonterminal_reference': 39,
    'integer': 40,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 89, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86],
    [-1, -1, 43, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, 43, -1, -1, 43, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 52, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, 52, -1, -1, 52, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1],
    [-1, -1, 66, -1, 66, -1, -1, -1, -1, -1, 66, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, 66, -1, -1, 66, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 62, -1, -1, -1, -1, -1, 62, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, 61, -1, -1, -1, -1, -1],
    [-1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [31, -1, 31, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, 31, 31, -1, -1, 30, -1, -1, -1, -1, 31, -1, -1, 31, 31, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1],
    [-1, -1, -1, -1, 56, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1],
    [16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1],
    [-1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 92, -1, -1, -1, -1, -1, -1, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 94],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 51, -1, -1, -1, -1, -1, 51, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, 51, -1, -1, 51, -1, 51, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, -1],
    [6, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1],
    [-1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 48, -1, 49, -1, -1, -1, -1, -1, 49, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, 49, -1, -1, 49, -1, -1, 49, -1, -1, 48, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 65, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1],
    [-1, -1, 47, -1, 47, 54, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, 53, -1, -1, -1, -1, -1, 54, -1, -1, 47, 47, -1, -1, 47, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1],
    [21, -1, 20, -1, 21, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, 21, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1],
    [-1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 87, 88, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1],
    [-1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 1, 0, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, 84, -1],
    [-1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 73, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    41: [2, -1, 26, 40, 12],
    42: [2, 36, 26, -1, 14, 30],
    43: [-1, 33],
    44: [2, 36, 26, -1, 14],
    45: [2, 36, -1, 26],
    46: [14],
    47: [35, -1],
    48: [3],
    49: [20, 13, -1],
    50: [10, -1, 33],
    51: [0],
    52: [35],
    53: [23],
    54: [36, -1],
    55: [38, 15],
    56: [2],
    57: [2, 26, 40, 12],
    58: [20, 13],
    59: [-1, 14],
    60: [36],
    61: [0, 28, -1, 29],
    62: [23, 11, 5],
    63: [-1, 27],
    64: [2, 36, 26],
    65: [-1, 29],
    66: [2, 36, 26, -1],
    67: [24, -1],
    68: [23, 11, 5],
    69: [7, 34, 6],
    70: [26, -1, 14, 30, 17, 2, 36, 5, 23],
    71: [38, 15],
    72: [17, 2, 36, -1],
    73: [2, -1],
    74: [24, -1],
    75: [37],
    76: [5],
    77: [36],
    78: [28],
    79: [37, -1],
    80: [27],
    81: [17, 2, 36],
    82: [33],
    83: [10, 33],
    84: [29],
    85: [-1, 16],
    86: [23, 5],
    87: [-1, 23, 11, 5],
    88: [0, 28, 29],
    89: [11],
    90: [29],
    91: [36, -1],
    92: [39, 36],
    93: [-1, 30],
    94: [1, 18, 9],
}
nonterminal_follow = {
    41: [25],
    42: [4, 27],
    43: [10],
    44: [4, 30, 27],
    45: [10, 4, 14, 33],
    46: [10, 27, 35, 30, 4, 33],
    47: [10, 4, 14, 33],
    48: [-1],
    49: [0, 28, 29, 2, 4, 16, 17, 36, 25],
    50: [4],
    51: [0, 28, 29, 16, 4],
    52: [10, 4, 14, 33],
    53: [11, 27, 5, 4, 23],
    54: [25],
    55: [25],
    56: [0, 28, 29, 16, 17, 2, 36, 4, 25],
    57: [24, 25],
    58: [0, 28, 29, 2, 4, 16, 17, 36, 25],
    59: [10, 27, 35, 30, 4, 33],
    60: [26, 27, 30, 2, 4, 33, 10, 14, 36],
    61: [16, 4],
    62: [11, 5, 4, 23],
    63: [4],
    64: [10, 26, 27, 14, 30, 2, 36, 4, 33],
    65: [4],
    66: [10, 27, 14, 30, 4, 33],
    67: [25],
    68: [4, 23, 11, 5],
    69: [10, 33, 4],
    70: [4, 27],
    71: [8],
    72: [0, 28, 29, 16, 4],
    73: [25],
    74: [25],
    75: [14],
    76: [11, 27, 5, 4, 23],
    77: [24, 25],
    78: [0, 28, 29, 16, 4],
    79: [14],
    80: [4, 27],
    81: [0, 28, 29, 16, 17, 2, 36, 4],
    82: [10],
    83: [10, 33, 4],
    84: [29, 4],
    85: [4],
    86: [11, 27, 5, 4, 23],
    87: [4],
    88: [0, 28, 29, 16, 4],
    89: [11, 5, 4, 23],
    90: [0, 28, 29, 16, 4],
    91: [4],
    92: [10, 27, 35, 30, 4, 33],
    93: [4, 27],
    94: [25],
}
rule_first = {
    0: [23, 11, 5],
    1: [-1],
    2: [3],
    3: [23, 11, 5],
    4: [11],
    5: [23, 5],
    6: [0, 28, 29],
    7: [-1],
    8: [16],
    9: [-1],
    10: [11],
    11: [29],
    12: [28],
    13: [0],
    14: [29],
    15: [-1],
    16: [0],
    17: [29],
    18: [37],
    19: [-1],
    20: [17, 2, 36],
    21: [-1],
    22: [29],
    23: [36],
    24: [-1],
    25: [37],
    26: [2],
    27: [2],
    28: [-1],
    29: [36],
    30: [20, 13],
    31: [-1],
    32: [2],
    33: [20],
    34: [13],
    35: [17],
    36: [28],
    37: [23],
    38: [5],
    39: [27],
    40: [-1],
    41: [23],
    42: [27],
    43: [26, 14, -1, 30, 2, 36],
    44: [30],
    45: [-1],
    46: [-1],
    47: [26, 14, -1, 30, 2, 36],
    48: [2, 36, 26],
    49: [-1],
    50: [14],
    51: [-1],
    52: [2, 36, 14, 26, -1],
    53: [17],
    54: [23, 5],
    55: [10, 33],
    56: [-1],
    57: [5],
    58: [33],
    59: [-1],
    60: [10, 33],
    61: [35],
    62: [-1],
    63: [7],
    64: [34],
    65: [6],
    66: [2, 36, -1, 26],
    67: [35],
    68: [33],
    69: [38, 15],
    70: [38],
    71: [15],
    72: [18],
    73: [1],
    74: [9],
    75: [2],
    76: [26],
    77: [36],
    78: [14],
    79: [36],
    80: [24],
    81: [-1],
    82: [-1],
    83: [36],
    84: [39],
    85: [36],
    86: [2, 26, 40, 12],
    87: [24],
    88: [-1],
    89: [-1],
    90: [36],
    91: [26],
    92: [2],
    93: [12],
    94: [40],
}
nonterminal_rules = {
    41: [
        "$_gen19 = $macro_parameter $_gen20",
        "$_gen19 = :_empty",
    ],
    42: [
        "$_gen10 = $rule $_gen11",
        "$_gen10 = :_empty",
    ],
    43: [
        "$_gen15 = $binding_power",
        "$_gen15 = :_empty",
    ],
    44: [
        "$rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )",
    ],
    45: [
        "$nud = $_gen12",
    ],
    46: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    47: [
        "$_gen16 = $led",
        "$_gen16 = :_empty",
    ],
    48: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    49: [
        "$_gen8 = $match_group",
        "$_gen8 = :_empty",
    ],
    50: [
        "$_gen14 = $expression_rule $_gen14",
        "$_gen14 = :_empty",
    ],
    51: [
        "$lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )",
    ],
    52: [
        "$led = :expression_divider $_gen12 -> $1",
    ],
    53: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen9 :rbrace -> Parser( rules=$2 )",
    ],
    54: [
        "$_gen17 = $ast_parameter $_gen18",
        "$_gen17 = :_empty",
    ],
    55: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    56: [
        "$terminal = :terminal $_gen8 -> Terminal( name=$0, group=$1 )",
    ],
    57: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    58: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    59: [
        "$_gen13 = $ast_transform",
        "$_gen13 = :_empty",
    ],
    60: [
        "$macro = :identifier :lparen $_gen19 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    61: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    62: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    63: [
        "$_gen9 = $ll1_rule $_gen9",
        "$_gen9 = :_empty",
    ],
    64: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    65: [
        "$_gen3 = $regex_partial $_gen3",
        "$_gen3 = :_empty",
    ],
    66: [
        "$_gen12 = $morpheme $_gen12",
        "$_gen12 = :_empty",
    ],
    67: [
        "$_gen18 = :comma $ast_parameter $_gen18",
        "$_gen18 = :_empty",
    ],
    68: [
        "$body_element = $body_element_sub",
    ],
    69: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    70: [
        "$ll1_rule_rhs = $_gen10",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    71: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    72: [
        "$_gen5 = $lexer_target $_gen5",
        "$_gen5 = :_empty",
    ],
    73: [
        "$_gen7 = $terminal",
        "$_gen7 = :_empty",
    ],
    74: [
        "$_gen20 = :comma $macro_parameter $_gen20",
        "$_gen20 = :_empty",
    ],
    75: [
        "$regex_options = :lbrace $_gen6 :rbrace -> $1",
    ],
    76: [
        "$parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    77: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    78: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    79: [
        "$_gen4 = $regex_options",
        "$_gen4 = :_empty",
    ],
    80: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    81: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen7 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    82: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    83: [
        "$expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    84: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    85: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    86: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    87: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    88: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
    ],
    89: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    90: [
        "$lexer_regex = :regex $_gen4 :arrow $_gen5 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    91: [
        "$_gen6 = :identifier $_gen6",
        "$_gen6 = :_empty",
    ],
    92: [
        "$ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    93: [
        "$_gen11 = :pipe $rule $_gen11",
        "$_gen11 = :_empty",
    ],
    94: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
}
rules = {
    0: "$_gen0 = $body_element $_gen0",
    1: "$_gen0 = :_empty",
    2: "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    3: "$body_element = $body_element_sub",
    4: "$body_element_sub = $lexer",
    5: "$body_element_sub = $parser",
    6: "$_gen1 = $lexer_atom $_gen1",
    7: "$_gen1 = :_empty",
    8: "$_gen2 = :code",
    9: "$_gen2 = :_empty",
    10: "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    11: "$lexer_atom = $lexer_regex",
    12: "$lexer_atom = $lexer_mode",
    13: "$lexer_atom = $lexer_partials",
    14: "$_gen3 = $regex_partial $_gen3",
    15: "$_gen3 = :_empty",
    16: "$lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )",
    17: "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    18: "$_gen4 = $regex_options",
    19: "$_gen4 = :_empty",
    20: "$_gen5 = $lexer_target $_gen5",
    21: "$_gen5 = :_empty",
    22: "$lexer_regex = :regex $_gen4 :arrow $_gen5 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    23: "$_gen6 = :identifier $_gen6",
    24: "$_gen6 = :_empty",
    25: "$regex_options = :lbrace $_gen6 :rbrace -> $1",
    26: "$lexer_target = $terminal",
    27: "$_gen7 = $terminal",
    28: "$_gen7 = :_empty",
    29: "$lexer_target = :identifier :lparen $_gen7 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    30: "$_gen8 = $match_group",
    31: "$_gen8 = :_empty",
    32: "$terminal = :terminal $_gen8 -> Terminal( name=$0, group=$1 )",
    33: "$match_group = :lsquare :integer :rsquare -> $1",
    34: "$match_group = :no_group",
    35: "$lexer_target = :null -> Null(  )",
    36: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    37: "$parser = $parser_ll1",
    38: "$parser = $parser_expression",
    39: "$_gen9 = $ll1_rule $_gen9",
    40: "$_gen9 = :_empty",
    41: "$parser_ll1 = :parser_ll1 :lbrace $_gen9 :rbrace -> Parser( rules=$2 )",
    42: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    43: "$_gen10 = $rule $_gen11",
    44: "$_gen11 = :pipe $rule $_gen11",
    45: "$_gen11 = :_empty",
    46: "$_gen10 = :_empty",
    47: "$ll1_rule_rhs = $_gen10",
    48: "$_gen12 = $morpheme $_gen12",
    49: "$_gen12 = :_empty",
    50: "$_gen13 = $ast_transform",
    51: "$_gen13 = :_empty",
    52: "$rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )",
    53: "$ll1_rule_rhs = :null -> NullProduction(  )",
    54: "$ll1_rule_rhs = $parser",
    55: "$_gen14 = $expression_rule $_gen14",
    56: "$_gen14 = :_empty",
    57: "$parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )",
    58: "$_gen15 = $binding_power",
    59: "$_gen15 = :_empty",
    60: "$expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    61: "$_gen16 = $led",
    62: "$_gen16 = :_empty",
    63: "$expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    64: "$expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )",
    65: "$expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )",
    66: "$nud = $_gen12",
    67: "$led = :expression_divider $_gen12 -> $1",
    68: "$binding_power = :lparen $precedence :rparen -> $1",
    69: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    70: "$binding_power_marker = :asterisk",
    71: "$binding_power_marker = :dash",
    72: "$associativity = :left",
    73: "$associativity = :right",
    74: "$associativity = :unary",
    75: "$morpheme = :terminal",
    76: "$morpheme = :nonterminal",
    77: "$morpheme = $macro",
    78: "$ast_transform = :arrow $ast_transform_sub -> $1",
    79: "$_gen17 = $ast_parameter $_gen18",
    80: "$_gen18 = :comma $ast_parameter $_gen18",
    81: "$_gen18 = :_empty",
    82: "$_gen17 = :_empty",
    83: "$ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    84: "$ast_transform_sub = :nonterminal_reference",
    85: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    86: "$_gen19 = $macro_parameter $_gen20",
    87: "$_gen20 = :comma $macro_parameter $_gen20",
    88: "$_gen20 = :_empty",
    89: "$_gen19 = :_empty",
    90: "$macro = :identifier :lparen $_gen19 :rparen -> Macro( name=$0, parameters=$2 )",
    91: "$macro_parameter = :nonterminal",
    92: "$macro_parameter = :terminal",
    93: "$macro_parameter = :string",
    94: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 40
def parse(tokens, error_formatter=None, start=None):
    if isinstance(tokens, str):
        tokens = lex(tokens, '<string>')
    if error_formatter is None:
        error_formatter = DefaultSyntaxErrorFormatter()
    ctx = ParserContext(tokens, error_formatter)
    tree = parse_grammar(ctx)
    if tokens.current() != None:
        raise SyntaxError('Finished parsing without consuming all tokens.')
    return tree
def expect(ctx, terminal_id):
    current = ctx.tokens.current()
    if not current:
        raise SyntaxError(ctx.error_formatter.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last()))
    if current.id != terminal_id:
        raise SyntaxError(ctx.error_formatter.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule))
    next = ctx.tokens.advance()
    if next and not is_terminal(next.id):
        raise SyntaxError(ctx.error_formatter.invalid_terminal(ctx.nonterminal, next))
    return current
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[41] and current.id not in nonterminal_first[41]:
        return tree
    if current == None:
        return tree
    if rule == 86: # $_gen19 = $macro_parameter $_gen20
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[42] and current.id not in nonterminal_first[42]:
        return tree
    if current == None:
        return tree
    if rule == 43: # $_gen10 = $rule $_gen11
        ctx.rule = rules[43]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = False
    if current != None and current.id in nonterminal_follow[43] and current.id not in nonterminal_first[43]:
        return tree
    if current == None:
        return tree
    if rule == 58: # $_gen15 = $binding_power
        ctx.rule = rules[58]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 52: # $rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[52]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[44]],
      rules[52]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 66: # $nud = $_gen12
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[45]],
      rules[66]
    ))
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 14) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[78]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = False
    if current != None and current.id in nonterminal_follow[47] and current.id not in nonterminal_first[47]:
        return tree
    if current == None:
        return tree
    if rule == 61: # $_gen16 = $led
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'grammar'))
    ctx.nonterminal = "grammar"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 2: # $grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )
        ctx.rule = rules[2]
        ast_parameters = OrderedDict([
            ('body', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Grammar', ast_parameters)
        t = expect(ctx, 3) # :grammar
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[2]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = False
    if current != None and current.id in nonterminal_follow[49] and current.id not in nonterminal_first[49]:
        return tree
    if current == None:
        return tree
    if rule == 30: # $_gen8 = $match_group
        ctx.rule = rules[30]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_match_group(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[50] and current.id not in nonterminal_first[50]:
        return tree
    if current == None:
        return tree
    if rule == 55: # $_gen14 = $expression_rule $_gen14
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'lexer_partials'))
    ctx.nonterminal = "lexer_partials"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 16: # $lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )
        ctx.rule = rules[16]
        ast_parameters = OrderedDict([
            ('list', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartials', ast_parameters)
        t = expect(ctx, 0) # :partials
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[51]],
      rules[16]
    ))
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 67: # $led = :expression_divider $_gen12 -> $1
        ctx.rule = rules[67]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 35) # :expression_divider
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[67]
    ))
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 41: # $parser_ll1 = :parser_ll1 :lbrace $_gen9 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[41]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 23) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[41]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
        return tree
    if current == None:
        return tree
    if rule == 79: # $_gen17 = $ast_parameter $_gen18
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 69: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[69]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 8) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[69]
    ))
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, 'terminal'))
    ctx.nonterminal = "terminal"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 32: # $terminal = :terminal $_gen8 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[32]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 2) # :terminal
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[56]],
      rules[32]
    ))
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 91: # $macro_parameter = :nonterminal
        ctx.rule = rules[91]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 92: # $macro_parameter = :terminal
        ctx.rule = rules[92]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 2) # :terminal
        tree.add(t)
        return tree
    elif rule == 93: # $macro_parameter = :string
        ctx.rule = rules[93]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 12) # :string
        tree.add(t)
        return tree
    elif rule == 94: # $macro_parameter = :integer
        ctx.rule = rules[94]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 40) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[94]
    ))
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 33: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[33]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 20) # :lsquare
        tree.add(t)
        t = expect(ctx, 40) # :integer
        tree.add(t)
        t = expect(ctx, 32) # :rsquare
        tree.add(t)
        return tree
    elif rule == 34: # $match_group = :no_group
        ctx.rule = rules[34]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :no_group
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58]],
      rules[34]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[59] and current.id not in nonterminal_first[59]:
        return tree
    if current == None:
        return tree
    if rule == 50: # $_gen13 = $ast_transform
        ctx.rule = rules[50]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 90: # $macro = :identifier :lparen $_gen19 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[90]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        t = expect(ctx, 25) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[90]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
        return tree
    if current == None:
        return tree
    if rule == 6: # $_gen1 = $lexer_atom $_gen1
        ctx.rule = rules[6]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_atom(ctx)
        tree.add(subtree)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'body_element_sub'))
    ctx.nonterminal = "body_element_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 4: # $body_element_sub = $lexer
        ctx.rule = rules[4]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer(ctx)
        tree.add(subtree)
        return tree
    elif rule == 5: # $body_element_sub = $parser
        ctx.rule = rules[5]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[62]],
      rules[5]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[63] and current.id not in nonterminal_first[63]:
        return tree
    if current == None:
        return tree
    if rule == 39: # $_gen9 = $ll1_rule $_gen9
        ctx.rule = rules[39]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 75: # $morpheme = :terminal
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 2) # :terminal
        tree.add(t)
        return tree
    elif rule == 76: # $morpheme = :nonterminal
        ctx.rule = rules[76]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 77: # $morpheme = $macro
        ctx.rule = rules[77]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[64]],
      rules[77]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[65] and current.id not in nonterminal_first[65]:
        return tree
    if current == None:
        return tree
    if rule == 14: # $_gen3 = $regex_partial $_gen3
        ctx.rule = rules[14]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_partial(ctx)
        tree.add(subtree)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
        return tree
    if current == None:
        return tree
    if rule == 48: # $_gen12 = $morpheme $_gen12
        ctx.rule = rules[48]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[67] and current.id not in nonterminal_first[67]:
        return tree
    if current == None:
        return tree
    if rule == 80: # $_gen18 = :comma $ast_parameter $_gen18
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'body_element'))
    ctx.nonterminal = "body_element"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 3: # $body_element = $body_element_sub
        ctx.rule = rules[3]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_body_element_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68]],
      rules[3]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[63]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 7) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    elif rule == 64: # $expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[64]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 34) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    elif rule == 65: # $expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[65]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 6) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[69]],
      rules[65]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 47: # $ll1_rule_rhs = $_gen10
        ctx.rule = rules[47]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    elif rule == 53: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 17) # :null
        tree.add(t)
        return tree
    elif rule == 54: # $ll1_rule_rhs = $parser
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[54]
    ))
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 70: # $binding_power_marker = :asterisk
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 38) # :asterisk
        tree.add(t)
        return tree
    elif rule == 71: # $binding_power_marker = :dash
        ctx.rule = rules[71]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71]],
      rules[71]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[72] and current.id not in nonterminal_first[72]:
        return tree
    if current == None:
        return tree
    if rule == 20: # $_gen5 = $lexer_target $_gen5
        ctx.rule = rules[20]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = False
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
        return tree
    if current == None:
        return tree
    if rule == 27: # $_gen7 = $terminal
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen20(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, '_gen20'))
    ctx.nonterminal = "_gen20"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[74] and current.id not in nonterminal_first[74]:
        return tree
    if current == None:
        return tree
    if rule == 87: # $_gen20 = :comma $macro_parameter $_gen20
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 25: # $regex_options = :lbrace $_gen6 :rbrace -> $1
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75]],
      rules[25]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 57: # $parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[57]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 5) # :parser_expression
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76]],
      rules[57]
    ))
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 85: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[85]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 22) # :equals
        tree.add(t)
        t = expect(ctx, 39) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[85]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 36: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[36]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 28) # :mode
        tree.add(t)
        t = expect(ctx, 31) # :langle
        tree.add(t)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 21) # :rangle
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[36]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = False
    if current != None and current.id in nonterminal_follow[79] and current.id not in nonterminal_first[79]:
        return tree
    if current == None:
        return tree
    if rule == 18: # $_gen4 = $regex_options
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 42: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[42]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 27) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 26) # :nonterminal
        tree.add(t)
        t = expect(ctx, 22) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[80]],
      rules[42]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 26: # $lexer_target = $terminal
        ctx.rule = rules[26]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    elif rule == 29: # $lexer_target = :identifier :lparen $_gen7 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 25) # :rparen
        tree.add(t)
        return tree
    elif rule == 35: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[35]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 17) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[35]
    ))
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 68: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 25) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[82]],
      rules[68]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[60]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 26) # :nonterminal
        tree.add(t)
        t = expect(ctx, 22) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[83]],
      rules[60]
    ))
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'regex_partial'))
    ctx.nonterminal = "regex_partial"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 17: # $regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )
        ctx.rule = rules[17]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('name', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartial', ast_parameters)
        t = expect(ctx, 29) # :regex
        tree.add(t)
        t = expect(ctx, 14) # :arrow
        tree.add(t)
        t = expect(ctx, 19) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84]],
      rules[17]
    ))
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[85] and current.id not in nonterminal_first[85]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :code
        tree.add(t)
        return tree
    return tree
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 37: # $parser = $parser_ll1
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 38: # $parser = $parser_expression
        ctx.rule = rules[38]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[86]],
      rules[38]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[87] and current.id not in nonterminal_first[87]:
        return tree
    if current == None:
        return tree
    if rule == 0: # $_gen0 = $body_element $_gen0
        ctx.rule = rules[0]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_body_element(ctx)
        tree.add(subtree)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 11: # $lexer_atom = $lexer_regex
        ctx.rule = rules[11]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 12: # $lexer_atom = $lexer_mode
        ctx.rule = rules[12]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_mode(ctx)
        tree.add(subtree)
        return tree
    elif rule == 13: # $lexer_atom = $lexer_partials
        ctx.rule = rules[13]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_partials(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[88]],
      rules[13]
    ))
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(89, 'lexer'))
    ctx.nonterminal = "lexer"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 10: # $lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )
        ctx.rule = rules[10]
        ast_parameters = OrderedDict([
            ('language', 2),
            ('atoms', 5),
            ('code', 6),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 11) # :lexer
        tree.add(t)
        t = expect(ctx, 31) # :langle
        tree.add(t)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 21) # :rangle
        tree.add(t)
        t = expect(ctx, 37) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[89]],
      rules[10]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 22: # $lexer_regex = :regex $_gen4 :arrow $_gen5 -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[22]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 29) # :regex
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 14) # :arrow
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[90]],
      rules[22]
    ))
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[91] and current.id not in nonterminal_first[91]:
        return tree
    if current == None:
        return tree
    if rule == 23: # $_gen6 = :identifier $_gen6
        ctx.rule = rules[23]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 83: # $ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[83]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 36) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 25) # :rparen
        tree.add(t)
        return tree
    elif rule == 84: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 39) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92]],
      rules[84]
    ))
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[93] and current.id not in nonterminal_first[93]:
        return tree
    if current == None:
        return tree
    if rule == 44: # $_gen11 = :pipe $rule $_gen11
        ctx.rule = rules[44]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 72: # $associativity = :left
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :left
        tree.add(t)
        return tree
    elif rule == 73: # $associativity = :right
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :right
        tree.add(t)
        return tree
    elif rule == 74: # $associativity = :unary
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 9) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94]],
      rules[74]
    ))
# Lexer Code #
# START USER CODE
def init():
    return {'lexer_brace': 0, 'grammar_brace': 0, 'parser_brace': 0}
def normalize_morpheme(morpheme):
    if morpheme == '$$': return '$'
    return morpheme.lstrip(':').lstrip('$')
def binding_power(context, mode, match, groups, terminal, resource, line, col):
    (precedence, associativity) = match[1:-1].split(':')
    marker = 'asterisk' if precedence == '*' else 'dash'
    tokens = [
        Terminal(terminals['lparen'], 'lparen', '(', resource, line, col),
        Terminal(terminals[marker], marker, precedence, resource, line, col),
        Terminal(terminals['colon'], 'colon', ':', resource, line, col),
        Terminal(terminals[associativity], associativity, associativity, resource, line, col),
        Terminal(terminals['rparen'], 'rparen', ')', resource, line, col)
    ]
    return (tokens, mode, context)
def morpheme(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, mode, normalize_morpheme(match), groups, terminal, resource, line, col)
def grammar_start(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, 'grammar', match, groups, terminal, resource, line, col)
def lexer_start(context, mode, match, groups, terminal, resource, line, col):
    identifier = match.replace('lexer', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(terminals['lexer'], 'lexer', 'lexer', resource, line, col),
        Terminal(terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, 'lexer', context)
def parser_ll1_start(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, 'parser_ll1', match, groups, terminal, resource, line, col)
def parser_expr_start(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, 'parser_expr', match, groups, terminal, resource, line, col)
def parse_mode(context, mode, match, groups, terminal, resource, line, col):
    identifier = match.replace('mode', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(terminals['mode'], 'mode', 'mode', resource, line, col),
        Terminal(terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, mode, context)
def parse_partials(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, 'partials', match, groups, terminal, resource, line, col)
def partials_rbrace(context, mode, match, groups, terminal, resource, line, col):
    return default_action(context, 'lexer', match, groups, terminal, resource, line, col)
def lexer_code(context, mode, match, groups, terminal, resource, line, col):
    code = match[6:-7].strip()
    tokens = [Terminal(terminals[terminal], terminal, code, resource, line, col)]
    return (tokens, mode, context)
def lexer_lbrace(context, mode, match, groups, terminal, resource, line, col):
    context['lexer_brace'] += 1
    return default_action(context, mode, match, groups, terminal, resource, line, col)
def lexer_rbrace(context, mode, match, groups, terminal, resource, line, col):
    context['lexer_brace'] -= 1
    mode = 'grammar' if context['lexer_brace'] == 0 else mode
    return default_action(context, mode, match, groups, terminal, resource, line, col)
def parser_lbrace(context, mode, match, groups, terminal, resource, line, col):
    context['parser_brace'] += 1
    return default_action(context, mode, match, groups, terminal, resource, line, col)
def parser_rbrace(context, mode, match, groups, terminal, resource, line, col):
    context['parser_brace'] -= 1
    mode = 'grammar' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, groups, terminal, resource, line, col)
def parser_rule_start(context, mode, match, groups, terminal, resource, line, col):
    tokens = [
        Terminal(terminals['ll1_rule_hint'], 'll1_rule_hint', '', resource, line, col),
        Terminal(terminals[terminal], terminal, normalize_morpheme(match), resource, line, col)
    ]
    return (tokens, mode, context)
def infix_rule_start(context, mode, match, groups, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(terminals['infix_rule_hint'], 'infix_rule_hint', '', resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def prefix_rule_start(context, mode, match, groups, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(terminals['prefix_rule_hint'], 'prefix_rule_hint', '', resource, line, col),
        Terminal(terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def expr_rule_start(context, mode, match, groups, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(terminals['mixfix_rule_hint'], 'mixfix_rule_hint', '',resource, line, col),
    ]
    return (tokens, mode, context)
def grammar_lbrace(context, mode, match, groups, terminal, resource, line, col):
    context['grammar_brace'] += 1
    return default_action(context, mode, match, groups, terminal, resource, line, col)
def grammar_rbrace(context, mode, match, groups, terminal, resource, line, col):
    context['grammar_brace'] -= 1
    mode = 'default' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, groups, terminal, resource, line, col)
# END USER CODE
def default_action(context, mode, match, groups, terminal, resource, line, col):
    tokens = [Terminal(terminals[terminal], terminal, match, resource, line, col)] if terminal else []
    return (tokens, mode, context)
def destroy(context):
    pass
class HermesLexer:
    regex = {
        'default': [
          (re.compile(r'\grammar'), 'grammar', grammar_start),
          (re.compile(r'\s+'), None, None),
        ],
        'grammar': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', grammar_lbrace),
          (re.compile(r'}'), 'rbrace', grammar_rbrace),
          (re.compile(r'lexer\s*<\s*[a-zA-Z]+\s*>'), 'lexer', lexer_start),
          (re.compile(r'parser\s*<\s*ll1\s*>'), 'parser_ll1', parser_ll1_start),
        ],
        'lexer': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', lexer_lbrace),
          (re.compile(r'}'), 'rbrace', lexer_rbrace),
          (re.compile(r'null'), 'null', None),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r'\[\]'), 'no_group', None),
          (re.compile(r'\['), 'lsquare', None),
          (re.compile(r'\]'), 'rsquare', None),
          (re.compile(r'[0-9]+'), 'integer', None),
          (re.compile(r'r\'(\\\'|[^\'])*\''), 'regex', None),
          (re.compile(r'"(\\\"|[^\"])*"'), 'regex', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'mode<[a-zA-Z0-9_]+>'), 'mode', parse_mode),
          (re.compile(r'partials(?=[\{\s])'), 'partials', parse_partials),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), 'code', lexer_code),
        ],
        'partials': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'r\'(\\\'|[^\'])*\''), 'regex', None),
          (re.compile(r'"(\\\"|[^\"])*"'), 'regex', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r'_([a-zA-Z][a-zA-Z0-9_]*)'), 'regex_partial', None),
          (re.compile(r'{'), 'lbrace', None),
          (re.compile(r'}'), 'rbrace', partials_rbrace),
        ],
        'parser_ll1': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', parser_lbrace),
          (re.compile(r'}'), 'rbrace', parser_rbrace),
          (re.compile(r'\|'), 'pipe', None),
          (re.compile(r'='), 'equals', None),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r','), 'comma', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r'parser\s*<\s*expression\s*>'), 'parser_expression', parser_expr_start),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*(?=\s*\=)'), 'nonterminal', parser_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*'), 'nonterminal', morpheme),
          (re.compile(r'\$([0-9]+|\$)'), 'nonterminal_reference', morpheme),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'"[^"]+"'), 'string', None),
          (re.compile(r'[0-9]+'), 'integer', None),
        ],
        'parser_expr': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'\([\*-]:(left|right|unary)\)'), None, binding_power),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r'<=>'), 'expression_divider', None),
          (re.compile(r'\|'), 'pipe', None),
          (re.compile(r'='), 'equals', None),
          (re.compile(r'{'), 'lbrace', parser_lbrace),
          (re.compile(r'}'), 'rbrace', parser_rbrace),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r','), 'comma', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'(\$[a-zA-Z][a-zA-Z0-9_]*)[ \t]*=[ \t]*\1[ \t]+:[a-zA-Z][a-zA-Z0-9_]*[ \t]+\1(?![ \t]+(:|\$))'), 'nonterminal', infix_rule_start),
          (re.compile(r'(\$[a-zA-Z][a-zA-Z0-9_]*)[ \t]*=[ \t]*:[a-zA-Z][a-zA-Z0-9_]*[ \t]+\1(?![ \t](:|\$))'), 'nonterminal', prefix_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*\s*='), 'nonterminal', expr_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*'), 'nonterminal', morpheme),
          (re.compile(r'\$([0-9]+|\$)'), 'nonterminal_reference', morpheme),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'"[^"]+"'), 'string', None),
          (re.compile(r'[0-9]+'), 'integer', None),
        ],
    }
    def _update_line_col(self, match, line, col):
        match_lines = match.split('\n')
        line += len(match_lines) - 1
        if len(match_lines) == 1:
            col += len(match_lines[0])
        else:
            col = len(match_lines[-1]) + 1
        return (line, col)
    def _unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        message = 'Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        )
        raise SyntaxError(message)
    def _next(self, string, mode, context, resource, line, col, debug=False):
        for (regex, terminal, function) in self.regex[mode]:
            if debug: print('trying: `{1}` ({2}, {3}) against {0}'.format(regex, string[:20].replace('\n', '\\n'), line, col))
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), match.groups(), terminal, resource, line, col)
                if debug:
                    print('    match: mode={} string={}'.format(mode, match.group(0), tokens))
                    for token in tokens:
                        print('           token: {}'.format(token))
                return (tokens, match.group(0), mode)
        return ([], '', mode)
    def lex(self, string, resource, debug=False):
        (mode, line, col) = ('default', 1, 1)
        context = init()
        string_copy = string
        parsed_tokens = []
        while len(string):
            (tokens, match, mode) = self._next(string, mode, context, resource, line, col, debug)
            if len(match) == 0:
                self._unrecognized_token(string_copy, line, col)
            string = string[len(match):]
            if tokens is None:
                self._unrecognized_token(string_copy, line, col)
            parsed_tokens.extend(tokens)
            (line, col) = self._update_line_col(match, line, col)
            if debug:
                from xtermcolor import colorize
                for token in tokens:
                    print('token --> [{}] [{}, {}] [{}] [{}] [{}]'.format(
                        colorize(token.str, ansi=9),
                        colorize(str(token.line), ansi=5),
                        colorize(str(token.col), ansi=5),
                        colorize(token.source_string, ansi=3),
                        colorize(mode, ansi=4),
                        colorize(str(context), ansi=13)
                    ))
        destroy(context)
        return parsed_tokens
def lex(source, resource, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, debug))
