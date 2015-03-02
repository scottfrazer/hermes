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
    0: 'mixfix_rule_hint',
    1: 'lparen',
    2: 'integer',
    3: 'colon',
    4: 'expression_divider',
    5: 'dash',
    6: 'grammar',
    7: 'arrow',
    8: 'null',
    9: 'prefix_rule_hint',
    10: 'expr_rule_hint',
    11: 'partials',
    12: 'pipe',
    13: 'string',
    14: 'll1_rule_hint',
    15: 'asterisk',
    16: 'rsquare',
    17: 'lexer',
    18: 'comma',
    19: 'rbrace',
    20: 'parser_ll1',
    21: 'parser_expression',
    22: 'langle',
    23: 'regex',
    24: 'identifier',
    25: 'right',
    26: 'left',
    27: 'regex_partial',
    28: 'unary',
    29: 'terminal',
    30: 'nonterminal',
    31: 'lbrace',
    32: 'mode',
    33: 'code',
    34: 'lsquare',
    35: 'infix_rule_hint',
    36: 'nonterminal_reference',
    37: 'rparen',
    38: 'equals',
    39: 'rangle',
    40: 'no_group',
    'mixfix_rule_hint': 0,
    'lparen': 1,
    'integer': 2,
    'colon': 3,
    'expression_divider': 4,
    'dash': 5,
    'grammar': 6,
    'arrow': 7,
    'null': 8,
    'prefix_rule_hint': 9,
    'expr_rule_hint': 10,
    'partials': 11,
    'pipe': 12,
    'string': 13,
    'll1_rule_hint': 14,
    'asterisk': 15,
    'rsquare': 16,
    'lexer': 17,
    'comma': 18,
    'rbrace': 19,
    'parser_ll1': 20,
    'parser_expression': 21,
    'langle': 22,
    'regex': 23,
    'identifier': 24,
    'right': 25,
    'left': 26,
    'regex_partial': 27,
    'unary': 28,
    'terminal': 29,
    'nonterminal': 30,
    'lbrace': 31,
    'mode': 32,
    'code': 33,
    'lsquare': 34,
    'infix_rule_hint': 35,
    'nonterminal_reference': 36,
    'rparen': 37,
    'equals': 38,
    'rangle': 39,
    'no_group': 40,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, 94, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 92, 91, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, 31, 31, -1, -1, -1, -1, 31, -1, -1, 31, 31, 30, -1, -1, 31, -1, -1, 30],
    [-1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 51, -1, -1, 51, -1, -1, 50, -1, -1, 51, -1, 51, -1, 51, -1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 55, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 49, -1, -1, -1, -1, -1, 49, -1, -1, 49, -1, 49, -1, 49, -1, -1, -1, -1, 49, -1, -1, -1, -1, 48, -1, -1, -1, -1, 48, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 58, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, 21, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, 21, 20, -1, -1, -1, -1, 20, -1, -1, 21, 21, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, 52, -1, 52, -1, -1, -1, -1, 52, -1, -1, -1, -1, 52, -1, -1, -1, -1, 52, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [63, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 47, 53, -1, -1, -1, 47, -1, 47, -1, -1, -1, -1, 47, 54, 54, -1, -1, 47, -1, -1, -1, -1, 47, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, 45, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, 34],
    [-1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, 43, -1, 43, -1, -1, -1, -1, 43, -1, -1, -1, -1, 43, -1, -1, -1, -1, 43, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 66, -1, -1, -1, -1, -1, 66, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, 66, -1, -1, -1, -1, 66, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, -1, -1, -1],
    [-1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, 72, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 60, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, 1, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 62, -1, -1, 61, -1, -1, 62, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, 75, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, 3, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, 86, -1, -1, -1, -1, -1, -1, 89, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, 6, 7, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, -1, -1],
]
nonterminal_first = {
    41: [13, 29, 2, 30],
    42: [23, 32, 11],
    43: [23],
    44: [34, 40, -1],
    45: [7],
    46: [-1, 7],
    47: [17],
    48: [24],
    49: [10, -1, 1],
    50: [-1, 24, 29, 30],
    51: [14, -1],
    52: [4],
    53: [23],
    54: [18, -1],
    55: [17, 20, 21],
    56: [-1, 1],
    57: [6],
    58: [33, -1],
    59: [29, -1],
    60: [32],
    61: [11],
    62: [-1, 24, 29, 8],
    63: [20],
    64: [-1, 24, 29, 7, 30],
    65: [9, 35, 0],
    66: [24, -1],
    67: [30, 21, -1, 12, 24, 29, 20, 7, 8],
    68: [24, -1],
    69: [-1, 12],
    70: [34, 40],
    71: [-1, 12, 24, 29, 7, 30],
    72: [24, 29, -1, 30],
    73: [18, -1],
    74: [5, 15],
    75: [23, -1],
    76: [26, 25, 28],
    77: [14],
    78: [31, -1],
    79: [10, 1],
    80: [17, 20, 21, -1],
    81: [1],
    82: [4, -1],
    83: [20, 21],
    84: [24, 29, 30],
    85: [29],
    86: [17, 20, 21],
    87: [5, 15],
    88: [24],
    89: [13, 29, 2, -1, 30],
    90: [31],
    91: [23, 32, -1, 11],
    92: [24, 29, 8],
    93: [21],
    94: [24, 36],
}
nonterminal_follow = {
    41: [18, 37],
    42: [23, 32, 19, 33, 11],
    43: [11, 23, 32, 33, 19],
    44: [23, 24, 29, 8, 11, 32, 33, 37, 19],
    45: [10, 12, 1, 14, 4, 19],
    46: [10, 12, 1, 14, 4, 19],
    47: [21, 17, 20, 19],
    48: [18, 37],
    49: [19],
    50: [10, 12, 1, 14, 19, 7],
    51: [19],
    52: [10, 1, 19, 7],
    53: [23, 19],
    54: [37],
    55: [21, 17, 20, 19],
    56: [10],
    57: [-1],
    58: [19],
    59: [37],
    60: [11, 23, 32, 33, 19],
    61: [11, 23, 32, 33, 19],
    62: [11, 23, 32, 33, 19],
    63: [21, 14, 17, 20, 19],
    64: [14, 19, 12],
    65: [10, 19, 1],
    66: [37],
    67: [14, 19],
    68: [19],
    69: [14, 19],
    70: [23, 24, 29, 8, 11, 32, 33, 37, 19],
    71: [14, 19],
    72: [10, 1, 19, 7],
    73: [37],
    74: [37],
    75: [19],
    76: [37],
    77: [14, 19],
    78: [7],
    79: [10, 19, 1],
    80: [19],
    81: [10],
    82: [10, 1, 19, 7],
    83: [21, 14, 17, 20, 19],
    84: [10, 12, 1, 24, 14, 29, 19, 7, 30],
    85: [11, 23, 24, 32, 33, 37, 29, 19, 8],
    86: [17, 20, 21, 19],
    87: [3],
    88: [1, 24, 29, 7, 30, 10, 12, 14, 19],
    89: [37],
    90: [7],
    91: [19, 33],
    92: [11, 23, 24, 32, 33, 29, 19, 8],
    93: [21, 14, 17, 20, 19],
    94: [10, 12, 1, 14, 4, 19],
}
rule_first = {
    0: [17, 20, 21],
    1: [-1],
    2: [6],
    3: [17, 20, 21],
    4: [17],
    5: [20, 21],
    6: [23, 32, 11],
    7: [-1],
    8: [33],
    9: [-1],
    10: [17],
    11: [23],
    12: [32],
    13: [11],
    14: [23],
    15: [-1],
    16: [11],
    17: [23],
    18: [31],
    19: [-1],
    20: [24, 29, 8],
    21: [-1],
    22: [23],
    23: [24],
    24: [-1],
    25: [31],
    26: [29],
    27: [29],
    28: [-1],
    29: [24],
    30: [34, 40],
    31: [-1],
    32: [29],
    33: [34],
    34: [40],
    35: [8],
    36: [32],
    37: [20],
    38: [21],
    39: [14],
    40: [-1],
    41: [20],
    42: [14],
    43: [-1, 12, 24, 29, 7, 30],
    44: [12],
    45: [-1],
    46: [-1],
    47: [-1, 12, 24, 29, 7, 30],
    48: [24, 29, 30],
    49: [-1],
    50: [7],
    51: [-1],
    52: [24, 29, 7, -1, 30],
    53: [8],
    54: [20, 21],
    55: [10, 1],
    56: [-1],
    57: [21],
    58: [1],
    59: [-1],
    60: [10, 1],
    61: [4],
    62: [-1],
    63: [0],
    64: [9],
    65: [35],
    66: [24, 29, -1, 30],
    67: [4],
    68: [1],
    69: [5, 15],
    70: [15],
    71: [5],
    72: [26],
    73: [25],
    74: [28],
    75: [29],
    76: [30],
    77: [24],
    78: [7],
    79: [24],
    80: [18],
    81: [-1],
    82: [-1],
    83: [24],
    84: [36],
    85: [24],
    86: [13, 29, 2, 30],
    87: [18],
    88: [-1],
    89: [-1],
    90: [24],
    91: [30],
    92: [29],
    93: [13],
    94: [2],
}
nonterminal_rules = {
    41: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    42: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
    ],
    43: [
        "$lexer_regex = :regex $_gen4 :arrow $_gen5 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    44: [
        "$_gen8 = $match_group",
        "$_gen8 = :_empty",
    ],
    45: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    46: [
        "$_gen13 = $ast_transform",
        "$_gen13 = :_empty",
    ],
    47: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    48: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    49: [
        "$_gen14 = $expression_rule $_gen14",
        "$_gen14 = :_empty",
    ],
    50: [
        "$_gen12 = $morpheme $_gen12",
        "$_gen12 = :_empty",
    ],
    51: [
        "$_gen9 = $ll1_rule $_gen9",
        "$_gen9 = :_empty",
    ],
    52: [
        "$led = :expression_divider $_gen12 -> $1",
    ],
    53: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    54: [
        "$_gen18 = :comma $ast_parameter $_gen18",
        "$_gen18 = :_empty",
    ],
    55: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    56: [
        "$_gen15 = $binding_power",
        "$_gen15 = :_empty",
    ],
    57: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    58: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    59: [
        "$_gen7 = $terminal",
        "$_gen7 = :_empty",
    ],
    60: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    61: [
        "$lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )",
    ],
    62: [
        "$_gen5 = $lexer_target $_gen5",
        "$_gen5 = :_empty",
    ],
    63: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen9 :rbrace -> Parser( rules=$2 )",
    ],
    64: [
        "$rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )",
    ],
    65: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    66: [
        "$_gen17 = $ast_parameter $_gen18",
        "$_gen17 = :_empty",
    ],
    67: [
        "$ll1_rule_rhs = $_gen10",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    68: [
        "$_gen6 = :identifier $_gen6",
        "$_gen6 = :_empty",
    ],
    69: [
        "$_gen11 = :pipe $rule $_gen11",
        "$_gen11 = :_empty",
    ],
    70: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    71: [
        "$_gen10 = $rule $_gen11",
        "$_gen10 = :_empty",
    ],
    72: [
        "$nud = $_gen12",
    ],
    73: [
        "$_gen20 = :comma $macro_parameter $_gen20",
        "$_gen20 = :_empty",
    ],
    74: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    75: [
        "$_gen3 = $regex_partial $_gen3",
        "$_gen3 = :_empty",
    ],
    76: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    77: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    78: [
        "$_gen4 = $regex_options",
        "$_gen4 = :_empty",
    ],
    79: [
        "$expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    80: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    81: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    82: [
        "$_gen16 = $led",
        "$_gen16 = :_empty",
    ],
    83: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    84: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    85: [
        "$terminal = :terminal $_gen8 -> Terminal( name=$0, group=$1 )",
    ],
    86: [
        "$body_element = $body_element_sub",
    ],
    87: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    88: [
        "$macro = :identifier :lparen $_gen19 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    89: [
        "$_gen19 = $macro_parameter $_gen20",
        "$_gen19 = :_empty",
    ],
    90: [
        "$regex_options = :lbrace $_gen6 :rbrace -> $1",
    ],
    91: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    92: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen7 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    93: [
        "$parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    94: [
        "$ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
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
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 91: # $macro_parameter = :nonterminal
        ctx.rule = rules[91]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 92: # $macro_parameter = :terminal
        ctx.rule = rules[92]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        return tree
    elif rule == 93: # $macro_parameter = :string
        ctx.rule = rules[93]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :string
        tree.add(t)
        return tree
    elif rule == 94: # $macro_parameter = :integer
        ctx.rule = rules[94]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 2) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[41]],
      rules[94]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, 'lexer_atom'))
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
      [terminals[x] for x in nonterminal_first[42]],
      rules[13]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, 'lexer_regex'))
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
        t = expect(ctx, 23) # :regex
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :arrow
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[43]],
      rules[22]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = False
    if current != None and current.id in nonterminal_follow[44] and current.id not in nonterminal_first[44]:
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
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 7) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[45]],
      rules[78]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[46] and current.id not in nonterminal_first[46]:
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
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'lexer'))
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
        t = expect(ctx, 17) # :lexer
        tree.add(t)
        t = expect(ctx, 22) # :langle
        tree.add(t)
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 39) # :rangle
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[47]],
      rules[10]
    ))
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'ast_parameter'))
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
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 38) # :equals
        tree.add(t)
        t = expect(ctx, 36) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[85]
    ))
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[49] and current.id not in nonterminal_first[49]:
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
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[50] and current.id not in nonterminal_first[50]:
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
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[51] and current.id not in nonterminal_first[51]:
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
        t = expect(ctx, 4) # :expression_divider
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
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'regex_partial'))
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
        t = expect(ctx, 23) # :regex
        tree.add(t)
        t = expect(ctx, 7) # :arrow
        tree.add(t)
        t = expect(ctx, 27) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[17]
    ))
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
        return tree
    if current == None:
        return tree
    if rule == 80: # $_gen18 = :comma $ast_parameter $_gen18
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[55]],
      rules[5]
    ))
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
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
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'grammar'))
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
        t = expect(ctx, 6) # :grammar
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[2]
    ))
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[58] and current.id not in nonterminal_first[58]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :code
        tree.add(t)
        return tree
    return tree
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = False
    if current != None and current.id in nonterminal_follow[59] and current.id not in nonterminal_first[59]:
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
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'lexer_mode'))
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
        t = expect(ctx, 32) # :mode
        tree.add(t)
        t = expect(ctx, 22) # :langle
        tree.add(t)
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 39) # :rangle
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[36]
    ))
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, 'lexer_partials'))
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
        t = expect(ctx, 11) # :partials
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[61]],
      rules[16]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[62] and current.id not in nonterminal_first[62]:
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
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'parser_ll1'))
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
        t = expect(ctx, 20) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[63]],
      rules[41]
    ))
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'rule'))
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
      [terminals[x] for x in nonterminal_first[64]],
      rules[52]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'expression_rule_production'))
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
        t = expect(ctx, 0) # :mixfix_rule_hint
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
        t = expect(ctx, 9) # :prefix_rule_hint
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
        t = expect(ctx, 35) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[65]],
      rules[65]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
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
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'll1_rule_rhs'))
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
        t = expect(ctx, 8) # :null
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
      [terminals[x] for x in nonterminal_first[67]],
      rules[54]
    ))
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[68] and current.id not in nonterminal_first[68]:
        return tree
    if current == None:
        return tree
    if rule == 23: # $_gen6 = :identifier $_gen6
        ctx.rule = rules[23]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[69] and current.id not in nonterminal_first[69]:
        return tree
    if current == None:
        return tree
    if rule == 44: # $_gen11 = :pipe $rule $_gen11
        ctx.rule = rules[44]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 12) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 33: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[33]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 34) # :lsquare
        tree.add(t)
        t = expect(ctx, 2) # :integer
        tree.add(t)
        t = expect(ctx, 16) # :rsquare
        tree.add(t)
        return tree
    elif rule == 34: # $match_group = :no_group
        ctx.rule = rules[34]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 40) # :no_group
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[34]
    ))
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[71] and current.id not in nonterminal_first[71]:
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
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'nud'))
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
      [terminals[x] for x in nonterminal_first[72]],
      rules[66]
    ))
def parse__gen20(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen20'))
    ctx.nonterminal = "_gen20"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
        return tree
    if current == None:
        return tree
    if rule == 87: # $_gen20 = :comma $macro_parameter $_gen20
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'precedence'))
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
        t = expect(ctx, 3) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[74]],
      rules[69]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[75] and current.id not in nonterminal_first[75]:
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
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 72: # $associativity = :left
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :left
        tree.add(t)
        return tree
    elif rule == 73: # $associativity = :right
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :right
        tree.add(t)
        return tree
    elif rule == 74: # $associativity = :unary
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 28) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76]],
      rules[74]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'll1_rule'))
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
        t = expect(ctx, 14) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 30) # :nonterminal
        tree.add(t)
        t = expect(ctx, 38) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[42]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = False
    if current != None and current.id in nonterminal_follow[78] and current.id not in nonterminal_first[78]:
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
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'expression_rule'))
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
        t = expect(ctx, 30) # :nonterminal
        tree.add(t)
        t = expect(ctx, 38) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[79]],
      rules[60]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[80] and current.id not in nonterminal_first[80]:
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
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 68: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 1) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[68]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = False
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
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
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'parser'))
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
      [terminals[x] for x in nonterminal_first[83]],
      rules[38]
    ))
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 75: # $morpheme = :terminal
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        return tree
    elif rule == 76: # $morpheme = :nonterminal
        ctx.rule = rules[76]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :nonterminal
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
      [terminals[x] for x in nonterminal_first[84]],
      rules[77]
    ))
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, 'terminal'))
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
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[85]],
      rules[32]
    ))
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[86]],
      rules[3]
    ))
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 70: # $binding_power_marker = :asterisk
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :asterisk
        tree.add(t)
        return tree
    elif rule == 71: # $binding_power_marker = :dash
        ctx.rule = rules[71]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 5) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[87]],
      rules[71]
    ))
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, 'macro'))
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
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 1) # :lparen
        tree.add(t)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[88]],
      rules[90]
    ))
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(89, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[89] and current.id not in nonterminal_first[89]:
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
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 25: # $regex_options = :lbrace $_gen6 :rbrace -> $1
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[90]],
      rules[25]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[91] and current.id not in nonterminal_first[91]:
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
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'lexer_target'))
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
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 1) # :lparen
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    elif rule == 35: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[35]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 8) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92]],
      rules[35]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, 'parser_expression'))
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
        t = expect(ctx, 21) # :parser_expression
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[93]],
      rules[57]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'ast_transform_sub'))
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
        t = expect(ctx, 24) # :identifier
        tree.add(t)
        t = expect(ctx, 1) # :lparen
        tree.add(t)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    elif rule == 84: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 36) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94]],
      rules[84]
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
        'default': OrderedDict([
          (re.compile(r'\grammar'), [
              # (terminal, group, function)
              ('grammar', 0, grammar_start),
          ]),
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
        ]),
        'grammar': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, grammar_lbrace),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, grammar_rbrace),
          ]),
          (re.compile(r'lexer\s*<\s*[a-zA-Z]+\s*>'), [
              # (terminal, group, function)
              ('lexer', 0, lexer_start),
          ]),
          (re.compile(r'parser\s*<\s*ll1\s*>'), [
              # (terminal, group, function)
              ('parser_ll1', 0, parser_ll1_start),
          ]),
        ]),
        'lexer': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, lexer_lbrace),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, lexer_rbrace),
          ]),
          (re.compile(r'null'), [
              # (terminal, group, function)
              ('null', 0, None),
          ]),
          (re.compile(r'\('), [
              # (terminal, group, function)
              ('lparen', 0, None),
          ]),
          (re.compile(r'\)'), [
              # (terminal, group, function)
              ('rparen', 0, None),
          ]),
          (re.compile(r'\[\]'), [
              # (terminal, group, function)
              ('no_group', 0, None),
          ]),
          (re.compile(r'\['), [
              # (terminal, group, function)
              ('lsquare', 0, None),
          ]),
          (re.compile(r'\]'), [
              # (terminal, group, function)
              ('rsquare', 0, None),
          ]),
          (re.compile(r'[0-9]+'), [
              # (terminal, group, function)
              ('integer', 0, None),
          ]),
          (re.compile(r'r\'(\\\'|[^\'])*\''), [
              # (terminal, group, function)
              ('regex', 0, None),
          ]),
          (re.compile(r'"(\\\"|[^\"])*"'), [
              # (terminal, group, function)
              ('regex', 0, None),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
          ]),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), [
              # (terminal, group, function)
              ('terminal', 1, None),
          ]),
          (re.compile(r'mode<[a-zA-Z0-9_]+>'), [
              # (terminal, group, function)
              ('mode', 0, parse_mode),
          ]),
          (re.compile(r'partials(?=[\{\s])'), [
              # (terminal, group, function)
              ('partials', 0, parse_partials),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), [
              # (terminal, group, function)
              ('code', 0, lexer_code),
          ]),
        ]),
        'partials': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'r\'(\\\'|[^\'])*\''), [
              # (terminal, group, function)
              ('regex', 0, None),
          ]),
          (re.compile(r'"(\\\"|[^\"])*"'), [
              # (terminal, group, function)
              ('regex', 0, None),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
          ]),
          (re.compile(r'_([a-zA-Z][a-zA-Z0-9_]*)'), [
              # (terminal, group, function)
              ('regex_partial', 0, None),
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, partials_rbrace),
          ]),
        ]),
        'parser_ll1': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, parser_lbrace),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, parser_rbrace),
          ]),
          (re.compile(r'\|'), [
              # (terminal, group, function)
              ('pipe', 0, None),
          ]),
          (re.compile(r'='), [
              # (terminal, group, function)
              ('equals', 0, None),
          ]),
          (re.compile(r'\('), [
              # (terminal, group, function)
              ('lparen', 0, None),
          ]),
          (re.compile(r'\)'), [
              # (terminal, group, function)
              ('rparen', 0, None),
          ]),
          (re.compile(r','), [
              # (terminal, group, function)
              ('comma', 0, None),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
          ]),
          (re.compile(r'parser\s*<\s*expression\s*>'), [
              # (terminal, group, function)
              ('parser_expression', 0, parser_expr_start),
          ]),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), [
              # (terminal, group, function)
              ('terminal', 1, None),
          ]),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*(?=\s*\=)'), [
              # (terminal, group, function)
              ('nonterminal', 0, parser_rule_start),
          ]),
          (re.compile(r'\$([a-zA-Z][a-zA-Z0-9_]*)'), [
              # (terminal, group, function)
              ('nonterminal', 1, None),
          ]),
          (re.compile(r'\$([0-9]+|\$)'), [
              # (terminal, group, function)
              ('nonterminal_reference', 1, None),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
          (re.compile(r'"[^"]+"'), [
              # (terminal, group, function)
              ('string', 0, None),
          ]),
          (re.compile(r'[0-9]+'), [
              # (terminal, group, function)
              ('integer', 0, None),
          ]),
        ]),
        'parser_expr': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\([\*-]:(left|right|unary)\)'), [
              # (terminal, group, function)
              (None, None, binding_power),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
          ]),
          (re.compile(r'<=>'), [
              # (terminal, group, function)
              ('expression_divider', 0, None),
          ]),
          (re.compile(r'\|'), [
              # (terminal, group, function)
              ('pipe', 0, None),
          ]),
          (re.compile(r'='), [
              # (terminal, group, function)
              ('equals', 0, None),
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, parser_lbrace),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, parser_rbrace),
          ]),
          (re.compile(r'\('), [
              # (terminal, group, function)
              ('lparen', 0, None),
          ]),
          (re.compile(r'\)'), [
              # (terminal, group, function)
              ('rparen', 0, None),
          ]),
          (re.compile(r','), [
              # (terminal, group, function)
              ('comma', 0, None),
          ]),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), [
              # (terminal, group, function)
              ('terminal', 1, None),
          ]),
          (re.compile(r'(\$([a-zA-Z][a-zA-Z0-9_]*))[ \t]*(=)[ \t]*\1[ \t]+:([a-zA-Z][a-zA-Z0-9_]*)[ \t]+\1(?![ \t]+(:|\$))'), [
              # (terminal, group, function)
              ('expr_rule_hint', None, None),
              ('nonterminal', 2, None),
              ('equals', 3, None),
              ('infix_rule_hint', None, None),
              ('nonterminal', 2, None),
              ('terminal', 4, None),
              ('nonterminal', 2, None),
          ]),
          (re.compile(r'(\$([a-zA-Z][a-zA-Z0-9_]*))[ \t]*(=)[ \t]*:([a-zA-Z][a-zA-Z0-9_]*)[ \t]+\1(?![ \t](:|\$))'), [
              # (terminal, group, function)
              ('expr_rule_hint', None, None),
              ('nonterminal', 2, None),
              ('equals', 3, None),
              ('prefix_rule_hint', None, None),
              ('terminal', 4, None),
              ('nonterminal', 2, None),
          ]),
          (re.compile(r'\$([a-zA-Z][a-zA-Z0-9_]*)\s*(=)'), [
              # (terminal, group, function)
              ('expr_rule_hint', None, None),
              ('nonterminal', 1, None),
              ('equals', 2, None),
              ('mixfix_rule_hint', None, None),
          ]),
          (re.compile(r'\$([a-zA-Z][a-zA-Z0-9_]*)'), [
              # (terminal, group, function)
              ('nonterminal', 1, None),
          ]),
          (re.compile(r'\$([0-9]+|\$)'), [
              # (terminal, group, function)
              ('nonterminal_reference', 1, None),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
          (re.compile(r'"[^"]+"'), [
              # (terminal, group, function)
              ('string', 0, None),
          ]),
          (re.compile(r'[0-9]+'), [
              # (terminal, group, function)
              ('integer', 0, None),
          ]),
        ]),
    }
    def _advance_line_col(self, string, length, line, col):
        for i in range(length):
            if string[i] == '\n':
                line += 1
                col = 1
            else:
                col += 1
        return (line, col)
    def _unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        message = 'Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        )
        raise SyntaxError(message)
    def _next(self, string, mode, context, resource, line, col, debug=False):
        for regex, outputs in self.regex[mode].items():
            if debug:
                print('trying: `{1}` ({2}, {3}) against {0}'.format(regex, string[:20].replace('\n', '\\n'), line, col))
            match = regex.match(string)
            if match:
                return_tokens = []
                return_mode = mode
                for (terminal, group, function) in outputs:
                    function = function if function else default_action
                    source_string = match.group(group) if group is not None else ''
                    if terminal is None and group is None and function != default_action:
                        source_string = match.group(0)
                    (group_line, group_col) = self._advance_line_col(string, match.start(group) if group else 0, line, col)
                    (tokens, return_mode, context) = function(
                        context,
                        mode,
                        source_string,
                        match.groups(),
                        terminal,
                        resource,
                        group_line, group_col
                    )
                    return_tokens.extend(tokens)
                    if debug:
                        print('    match: mode={} string={}'.format(mode, match.group(0), tokens))
                        for token in tokens:
                            print('           token: {}'.format(token))
                return (return_tokens, match.group(0), return_mode)
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
            (line, col) = self._advance_line_col(match, len(match), line, col)
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
