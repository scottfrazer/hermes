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
parser_terminals = {
    0: 'lexer',
    1: 'asterisk',
    2: 'mixfix_rule_hint',
    3: 'll1_rule_hint',
    4: 'null',
    5: 'parser_ll1',
    6: 'parser_expression',
    7: 'unary',
    8: 'grammar',
    9: 'rparen',
    10: 'prefix_rule_hint',
    11: 'nonterminal_reference',
    12: 'equals',
    13: 'comma',
    14: 'regex',
    15: 'infix_rule_hint',
    16: 'terminal',
    17: 'dash',
    18: 'mode',
    19: 'rangle',
    20: 'langle',
    21: 'arrow',
    22: 'expr_rule_hint',
    23: 'lbrace',
    24: 'lparen',
    25: 'colon',
    26: 'left',
    27: 'pipe',
    28: 'rbrace',
    29: 'identifier',
    30: 'string',
    31: 'integer',
    32: 'right',
    33: 'code',
    34: 'nonterminal',
    35: 'expression_divider',
    'lexer': 0,
    'asterisk': 1,
    'mixfix_rule_hint': 2,
    'll1_rule_hint': 3,
    'null': 4,
    'parser_ll1': 5,
    'parser_expression': 6,
    'unary': 7,
    'grammar': 8,
    'rparen': 9,
    'prefix_rule_hint': 10,
    'nonterminal_reference': 11,
    'equals': 12,
    'comma': 13,
    'regex': 14,
    'infix_rule_hint': 15,
    'terminal': 16,
    'dash': 17,
    'mode': 18,
    'rangle': 19,
    'langle': 20,
    'arrow': 21,
    'expr_rule_hint': 22,
    'lbrace': 23,
    'lparen': 24,
    'colon': 25,
    'left': 26,
    'pipe': 27,
    'rbrace': 28,
    'identifier': 29,
    'string': 30,
    'integer': 31,
    'right': 32,
    'code': 33,
    'nonterminal': 34,
    'expression_divider': 35,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, 43, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, 33, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, 74, -1, -1, 74, -1],
    [-1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, 40, 40, 40, -1, -1, -1, -1, 40, -1],
    [10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 51, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, -1, -1, -1, -1, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, 16, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 25, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55],
    [-1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, 7, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, 37, 37, -1, 37, -1, -1, 37, 37, 36, -1, -1, -1, -1, 36, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, 54, 54, -1, 54, -1, -1, -1, 54, 54, -1, -1, -1, -1, 54, -1],
    [-1, -1, -1, 35, 41, 42, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, 35, 35, 35, -1, -1, -1, -1, 35, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, 50, -1, 50, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, 49],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, 64, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 38, 39, -1, 39, -1, -1, 39, 39, -1, -1, -1, -1, -1, -1, 39],
    [-1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, 31, 31, 31, -1, -1, -1, -1, 31, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, 61, -1, -1, -1],
    [3, -1, -1, -1, -1, 3, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, 82, -1, -1, 79, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, -1, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, 8, -1, -1],
]
nonterminal_first = {
    36: [13, -1],
    37: [5],
    38: [-1, 29],
    39: [-1, 22, 24],
    40: [-1, 23],
    41: [-1, 27],
    42: [29],
    43: [18, 14],
    44: [4, 29, 16],
    45: [11, 29],
    46: [30, 34, 31, -1, 16],
    47: [21, 16, 34, -1, 29],
    48: [0],
    49: [24],
    50: [2, 10, 15],
    51: [0, 5, 6],
    52: [-1, 29],
    53: [5, 6],
    54: [21],
    55: [-1, 24],
    56: [-1, 16],
    57: [35],
    58: [1, 17],
    59: [1, 17],
    60: [18, 14, -1],
    61: [14],
    62: [3],
    63: [16, 34, -1, 29],
    64: [23],
    65: [34, -1, 29, 16],
    66: [27, 4, 5, 6, -1, 29, 21, 16, 34],
    67: [-1, 35],
    68: [34, 29, 16],
    69: [29],
    70: [21, -1],
    71: [-1, 3],
    72: [18],
    73: [21, 27, 16, 34, -1, 29],
    74: [8],
    75: [22, 24],
    76: [7, 32, 26],
    77: [0, 5, 6],
    78: [30, 34, 31, 16],
    79: [13, -1],
    80: [0, 5, 6, -1],
    81: [6],
    82: [33, -1],
}
nonterminal_follow = {
    36: [9],
    37: [0, 3, 5, 6, 28],
    38: [9],
    39: [28],
    40: [21],
    41: [28, 3],
    42: [9, 13],
    43: [18, 14, 33, 28],
    44: [14, 33, 18, 28],
    45: [27, 3, 28, 22, 24, 35],
    46: [9],
    47: [27, 28, 3],
    48: [0, 5, 6, 28],
    49: [22],
    50: [22, 28, 24],
    51: [0, 5, 6, 28],
    52: [28],
    53: [0, 3, 5, 6, 28],
    54: [27, 3, 28, 22, 24, 35],
    55: [22],
    56: [9],
    57: [21, 22, 24, 28],
    58: [9],
    59: [25],
    60: [33, 28],
    61: [14, 33, 18, 28],
    62: [28, 3],
    63: [3, 27, 28, 21, 22, 24],
    64: [21],
    65: [21, 22, 24, 28],
    66: [28, 3],
    67: [21, 22, 24, 28],
    68: [27, 3, 28, 29, 21, 22, 16, 24, 34],
    69: [3, 21, 22, 24, 27, 28, 29, 16, 34],
    70: [27, 3, 28, 22, 24, 35],
    71: [28],
    72: [14, 33, 18, 28],
    73: [28, 3],
    74: [-1],
    75: [22, 28, 24],
    76: [9],
    77: [0, 5, 6, 28],
    78: [9, 13],
    79: [9],
    80: [28],
    81: [0, 3, 5, 6, 28],
    82: [28],
}
rule_first = {
    0: [0, 5, 6],
    1: [-1],
    2: [8],
    3: [0, 5, 6],
    4: [0],
    5: [5, 6],
    6: [18, 14],
    7: [-1],
    8: [33],
    9: [-1],
    10: [0],
    11: [14],
    12: [18],
    13: [23],
    14: [-1],
    15: [14],
    16: [29],
    17: [-1],
    18: [23],
    19: [16],
    20: [16],
    21: [-1],
    22: [29],
    23: [4],
    24: [18],
    25: [5],
    26: [6],
    27: [3],
    28: [-1],
    29: [5],
    30: [3],
    31: [27, -1, 29, 21, 16, 34],
    32: [27],
    33: [-1],
    34: [-1],
    35: [27, -1, 29, 21, 16, 34],
    36: [34, 29, 16],
    37: [-1],
    38: [21],
    39: [-1],
    40: [34, 21, -1, 29, 16],
    41: [4],
    42: [5, 6],
    43: [22, 24],
    44: [-1],
    45: [6],
    46: [24],
    47: [-1],
    48: [22, 24],
    49: [35],
    50: [-1],
    51: [2],
    52: [10],
    53: [15],
    54: [34, -1, 29, 16],
    55: [35],
    56: [24],
    57: [1, 17],
    58: [1],
    59: [17],
    60: [26],
    61: [32],
    62: [7],
    63: [16],
    64: [34],
    65: [29],
    66: [21],
    67: [29],
    68: [13],
    69: [-1],
    70: [-1],
    71: [29],
    72: [11],
    73: [29],
    74: [30, 34, 31, 16],
    75: [13],
    76: [-1],
    77: [-1],
    78: [29],
    79: [34],
    80: [16],
    81: [30],
    82: [31],
}
nonterminal_rules = {
    36: [
        "$_gen15 = :comma $ast_parameter $_gen15",
        "$_gen15 = :_empty",
    ],
    37: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )",
    ],
    38: [
        "$_gen14 = $ast_parameter $_gen15",
        "$_gen14 = :_empty",
    ],
    39: [
        "$_gen11 = $expression_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    40: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    41: [
        "$_gen8 = :pipe $rule $_gen8",
        "$_gen8 = :_empty",
    ],
    42: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    43: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
    ],
    44: [
        "$lexer_target = :terminal",
        "$lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    45: [
        "$ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    46: [
        "$_gen16 = $macro_parameter $_gen17",
        "$_gen16 = :_empty",
    ],
    47: [
        "$rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )",
    ],
    48: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    49: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    50: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    51: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    52: [
        "$_gen4 = :identifier $_gen4",
        "$_gen4 = :_empty",
    ],
    53: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    54: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    55: [
        "$_gen12 = $binding_power",
        "$_gen12 = :_empty",
    ],
    56: [
        "$_gen5 = :terminal",
        "$_gen5 = :_empty",
    ],
    57: [
        "$led = :expression_divider $_gen9 -> $1",
    ],
    58: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    59: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    60: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    61: [
        "$lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    62: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    63: [
        "$_gen9 = $morpheme $_gen9",
        "$_gen9 = :_empty",
    ],
    64: [
        "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    ],
    65: [
        "$nud = $_gen9",
    ],
    66: [
        "$ll1_rule_rhs = $_gen7",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    67: [
        "$_gen13 = $led",
        "$_gen13 = :_empty",
    ],
    68: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    69: [
        "$macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    70: [
        "$_gen10 = $ast_transform",
        "$_gen10 = :_empty",
    ],
    71: [
        "$_gen6 = $ll1_rule $_gen6",
        "$_gen6 = :_empty",
    ],
    72: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    73: [
        "$_gen7 = $rule $_gen8",
        "$_gen7 = :_empty",
    ],
    74: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    75: [
        "$expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    76: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    77: [
        "$body_element = $body_element_sub",
    ],
    78: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    79: [
        "$_gen17 = :comma $macro_parameter $_gen17",
        "$_gen17 = :_empty",
    ],
    80: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    81: [
        "$parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    82: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
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
    13: "$_gen3 = $regex_options",
    14: "$_gen3 = :_empty",
    15: "$lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    16: "$_gen4 = :identifier $_gen4",
    17: "$_gen4 = :_empty",
    18: "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    19: "$lexer_target = :terminal",
    20: "$_gen5 = :terminal",
    21: "$_gen5 = :_empty",
    22: "$lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    23: "$lexer_target = :null -> Null(  )",
    24: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    25: "$parser = $parser_ll1",
    26: "$parser = $parser_expression",
    27: "$_gen6 = $ll1_rule $_gen6",
    28: "$_gen6 = :_empty",
    29: "$parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )",
    30: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    31: "$_gen7 = $rule $_gen8",
    32: "$_gen8 = :pipe $rule $_gen8",
    33: "$_gen8 = :_empty",
    34: "$_gen7 = :_empty",
    35: "$ll1_rule_rhs = $_gen7",
    36: "$_gen9 = $morpheme $_gen9",
    37: "$_gen9 = :_empty",
    38: "$_gen10 = $ast_transform",
    39: "$_gen10 = :_empty",
    40: "$rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )",
    41: "$ll1_rule_rhs = :null -> NullProduction(  )",
    42: "$ll1_rule_rhs = $parser",
    43: "$_gen11 = $expression_rule $_gen11",
    44: "$_gen11 = :_empty",
    45: "$parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )",
    46: "$_gen12 = $binding_power",
    47: "$_gen12 = :_empty",
    48: "$expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    49: "$_gen13 = $led",
    50: "$_gen13 = :_empty",
    51: "$expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    52: "$expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )",
    53: "$expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )",
    54: "$nud = $_gen9",
    55: "$led = :expression_divider $_gen9 -> $1",
    56: "$binding_power = :lparen $precedence :rparen -> $1",
    57: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    58: "$binding_power_marker = :asterisk",
    59: "$binding_power_marker = :dash",
    60: "$associativity = :left",
    61: "$associativity = :right",
    62: "$associativity = :unary",
    63: "$morpheme = :terminal",
    64: "$morpheme = :nonterminal",
    65: "$morpheme = $macro",
    66: "$ast_transform = :arrow $ast_transform_sub -> $1",
    67: "$_gen14 = $ast_parameter $_gen15",
    68: "$_gen15 = :comma $ast_parameter $_gen15",
    69: "$_gen15 = :_empty",
    70: "$_gen14 = :_empty",
    71: "$ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    72: "$ast_transform_sub = :nonterminal_reference",
    73: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    74: "$_gen16 = $macro_parameter $_gen17",
    75: "$_gen17 = :comma $macro_parameter $_gen17",
    76: "$_gen17 = :_empty",
    77: "$_gen16 = :_empty",
    78: "$macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )",
    79: "$macro_parameter = :nonterminal",
    80: "$macro_parameter = :terminal",
    81: "$macro_parameter = :string",
    82: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 35
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
        raise SyntaxError(ctx.error_formatter.no_more_tokens(ctx.nonterminal, parser_terminals[terminal_id], ctx.tokens.last()))
    if current.id != terminal_id:
        raise SyntaxError(ctx.error_formatter.unexpected_symbol(ctx.nonterminal, current, [parser_terminals[terminal_id]], ctx.rule))
    next = ctx.tokens.advance()
    if next and not is_terminal(next.id):
        raise SyntaxError(ctx.error_formatter.invalid_terminal(ctx.nonterminal, next))
    return current
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(36, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[36] and current.id not in nonterminal_first[36]:
        return tree
    if current == None:
        return tree
    if rule == 68: # $_gen15 = :comma $ast_parameter $_gen15
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(37, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 5) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[37]],
      rules[29]
    ))
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(38, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[38] and current.id not in nonterminal_first[38]:
        return tree
    if current == None:
        return tree
    if rule == 67: # $_gen14 = $ast_parameter $_gen15
        ctx.rule = rules[67]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(39, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[39] and current.id not in nonterminal_first[39]:
        return tree
    if current == None:
        return tree
    if rule == 43: # $_gen11 = $expression_rule $_gen11
        ctx.rule = rules[43]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(40, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = False
    if current != None and current.id in nonterminal_follow[40] and current.id not in nonterminal_first[40]:
        return tree
    if current == None:
        return tree
    if rule == 13: # $_gen3 = $regex_options
        ctx.rule = rules[13]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[41] and current.id not in nonterminal_first[41]:
        return tree
    if current == None:
        return tree
    if rule == 32: # $_gen8 = :pipe $rule $_gen8
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 27) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 73: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[73]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 12) # :equals
        tree.add(t)
        t = expect(ctx, 11) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[42]],
      rules[73]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, 'lexer_atom'))
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
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[43]],
      rules[12]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 19: # $lexer_target = :terminal
        ctx.rule = rules[19]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :terminal
        tree.add(t)
        return tree
    elif rule == 22: # $lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[22]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 24) # :lparen
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 9) # :rparen
        tree.add(t)
        return tree
    elif rule == 23: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[23]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 4) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[44]],
      rules[23]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 71: # $ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[71]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 24) # :lparen
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 9) # :rparen
        tree.add(t)
        return tree
    elif rule == 72: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 11) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[45]],
      rules[72]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[46] and current.id not in nonterminal_first[46]:
        return tree
    if current == None:
        return tree
    if rule == 74: # $_gen16 = $macro_parameter $_gen17
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[40]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[47]],
      rules[40]
    ))
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'lexer'))
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
        t = expect(ctx, 0) # :lexer
        tree.add(t)
        t = expect(ctx, 20) # :langle
        tree.add(t)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 19) # :rangle
        tree.add(t)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[48]],
      rules[10]
    ))
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 24) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 9) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[49]],
      rules[56]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 51: # $expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[51]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 2) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    elif rule == 52: # $expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[52]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 10) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    elif rule == 53: # $expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 15) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[50]],
      rules[53]
    ))
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'body_element_sub'))
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
      [parser_terminals[x] for x in nonterminal_first[51]],
      rules[5]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[52] and current.id not in nonterminal_first[52]:
        return tree
    if current == None:
        return tree
    if rule == 16: # $_gen4 = :identifier $_gen4
        ctx.rule = rules[16]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 25: # $parser = $parser_ll1
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 26: # $parser = $parser_expression
        ctx.rule = rules[26]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[53]],
      rules[26]
    ))
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 66: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 21) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[54]],
      rules[66]
    ))
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = False
    if current != None and current.id in nonterminal_follow[55] and current.id not in nonterminal_first[55]:
        return tree
    if current == None:
        return tree
    if rule == 46: # $_gen12 = $binding_power
        ctx.rule = rules[46]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 20: # $_gen5 = :terminal
        ctx.rule = rules[20]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :terminal
        tree.add(t)
        return tree
    return tree
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 55: # $led = :expression_divider $_gen9 -> $1
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 35) # :expression_divider
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[57]],
      rules[55]
    ))
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 57: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[57]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 25) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[58]],
      rules[57]
    ))
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 58: # $binding_power_marker = :asterisk
        ctx.rule = rules[58]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :asterisk
        tree.add(t)
        return tree
    elif rule == 59: # $binding_power_marker = :dash
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 17) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[59]],
      rules[59]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[60] and current.id not in nonterminal_first[60]:
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
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 15: # $lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[15]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 14) # :regex
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 21) # :arrow
        tree.add(t)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[61]],
      rules[15]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 30: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[30]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 3) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 34) # :nonterminal
        tree.add(t)
        t = expect(ctx, 12) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[62]],
      rules[30]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[63] and current.id not in nonterminal_first[63]:
        return tree
    if current == None:
        return tree
    if rule == 36: # $_gen9 = $morpheme $_gen9
        ctx.rule = rules[36]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 18: # $regex_options = :lbrace $_gen4 :rbrace -> $1
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[64]],
      rules[18]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 54: # $nud = $_gen9
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[65]],
      rules[54]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 35: # $ll1_rule_rhs = $_gen7
        ctx.rule = rules[35]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        return tree
    elif rule == 41: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[41]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 4) # :null
        tree.add(t)
        return tree
    elif rule == 42: # $ll1_rule_rhs = $parser
        ctx.rule = rules[42]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[66]],
      rules[42]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[67] and current.id not in nonterminal_first[67]:
        return tree
    if current == None:
        return tree
    if rule == 49: # $_gen13 = $led
        ctx.rule = rules[49]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $morpheme = :terminal
        ctx.rule = rules[63]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :terminal
        tree.add(t)
        return tree
    elif rule == 64: # $morpheme = :nonterminal
        ctx.rule = rules[64]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 65: # $morpheme = $macro
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[68]],
      rules[65]
    ))
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[78]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 24) # :lparen
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 9) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[69]],
      rules[78]
    ))
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[70] and current.id not in nonterminal_first[70]:
        return tree
    if current == None:
        return tree
    if rule == 38: # $_gen10 = $ast_transform
        ctx.rule = rules[38]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[71] and current.id not in nonterminal_first[71]:
        return tree
    if current == None:
        return tree
    if rule == 27: # $_gen6 = $ll1_rule $_gen6
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 24: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[24]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 18) # :mode
        tree.add(t)
        t = expect(ctx, 20) # :langle
        tree.add(t)
        t = expect(ctx, 29) # :identifier
        tree.add(t)
        t = expect(ctx, 19) # :rangle
        tree.add(t)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[72]],
      rules[24]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
        return tree
    if current == None:
        return tree
    if rule == 31: # $_gen7 = $rule $_gen8
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'grammar'))
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
        t = expect(ctx, 8) # :grammar
        tree.add(t)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[74]],
      rules[2]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 48: # $expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[48]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        t = expect(ctx, 22) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 34) # :nonterminal
        tree.add(t)
        t = expect(ctx, 12) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[75]],
      rules[48]
    ))
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $associativity = :left
        ctx.rule = rules[60]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :left
        tree.add(t)
        return tree
    elif rule == 61: # $associativity = :right
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 32) # :right
        tree.add(t)
        return tree
    elif rule == 62: # $associativity = :unary
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 7) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[76]],
      rules[62]
    ))
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'body_element'))
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
      [parser_terminals[x] for x in nonterminal_first[77]],
      rules[3]
    ))
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $macro_parameter = :nonterminal
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 80: # $macro_parameter = :terminal
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :terminal
        tree.add(t)
        return tree
    elif rule == 81: # $macro_parameter = :string
        ctx.rule = rules[81]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :string
        tree.add(t)
        return tree
    elif rule == 82: # $macro_parameter = :integer
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[78]],
      rules[82]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[79] and current.id not in nonterminal_first[79]:
        return tree
    if current == None:
        return tree
    if rule == 75: # $_gen17 = :comma $macro_parameter $_gen17
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
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
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[45]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 6) # :parser_expression
        tree.add(t)
        t = expect(ctx, 23) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 28) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [parser_terminals[x] for x in nonterminal_first[81]],
      rules[45]
    ))
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
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
# Lexer Code #
lexer_terminals = {
    8: 'grammar',
    5: 'parser_ll1',
    6: 'parser_expression',
    12: 'equals',
    24: 'lparen',
    17: 'dash',
    29: 'identifier',
    2: 'mixfix_rule_hint',
    3: 'll1_rule_hint',
    28: 'rbrace',
    31: 'integer',
    35: 'expression_divider',
    15: 'infix_rule_hint',
    27: 'pipe',
    18: 'mode',
    22: 'expr_rule_hint',
    33: 'code',
    11: 'nonterminal_reference',
    19: 'rangle',
    1: 'asterisk',
    10: 'prefix_rule_hint',
    13: 'comma',
    34: 'nonterminal',
    14: 'regex',
    -1: '_empty',
    9: 'rparen',
    4: 'null',
    20: 'langle',
    32: 'right',
    30: 'string',
    23: 'lbrace',
    7: 'unary',
    21: 'arrow',
    25: 'colon',
    16: 'terminal',
    26: 'left',
    0: 'lexer',
    'grammar': 8,
    'parser_ll1': 5,
    'parser_expression': 6,
    'equals': 12,
    'lparen': 24,
    'dash': 17,
    'identifier': 29,
    'mixfix_rule_hint': 2,
    'll1_rule_hint': 3,
    'rbrace': 28,
    'integer': 31,
    'expression_divider': 35,
    'infix_rule_hint': 15,
    'pipe': 27,
    'mode': 18,
    'expr_rule_hint': 22,
    'code': 33,
    'nonterminal_reference': 11,
    'rangle': 19,
    'asterisk': 1,
    'prefix_rule_hint': 10,
    'comma': 13,
    'nonterminal': 34,
    'regex': 14,
    '_empty': -1,
    'rparen': 9,
    'null': 4,
    'langle': 20,
    'right': 32,
    'string': 30,
    'lbrace': 23,
    'unary': 7,
    'arrow': 21,
    'colon': 25,
    'terminal': 16,
    'left': 26,
    'lexer': 0,
}
# START USER CODE
def init():
    return {'lexer_brace': 0, 'grammar_brace': 0, 'parser_brace': 0}
def normalize_morpheme(morpheme):
    if morpheme == '$$': return '$'
    return morpheme.lstrip(':').lstrip('$')
def binding_power(context, mode, match, terminal, resource, line, col):
    (precedence, associativity) = match[1:-1].split(':')
    marker = 'asterisk' if precedence == '*' else 'dash'
    tokens = [
        Terminal(lexer_terminals['lparen'], 'lparen', '(', resource, line, col),
        Terminal(lexer_terminals[marker], marker, precedence, resource, line, col),
        Terminal(lexer_terminals['colon'], 'colon', ':', resource, line, col),
        Terminal(lexer_terminals[associativity], associativity, associativity, resource, line, col),
        Terminal(lexer_terminals['rparen'], 'rparen', ')', resource, line, col)
    ]
    return (tokens, mode, context)
def morpheme(context, mode, match, terminal, resource, line, col):
    return default_action(context, mode, normalize_morpheme(match), terminal, resource, line, col)
def grammar_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'grammar', match, terminal, resource, line, col)
def lexer_start(context, mode, match, terminal, resource, line, col):
    identifier = match.replace('lexer', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(lexer_terminals['lexer'], 'lexer', 'lexer', resource, line, col),
        Terminal(lexer_terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(lexer_terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(lexer_terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, 'lexer', context)
def parser_ll1_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'parser_ll1', match, terminal, resource, line, col)
def parser_expr_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'parser_expr', match, terminal, resource, line, col)
def parse_mode(context, mode, match, terminal, resource, line, col):
    identifier = match.replace('mode', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(lexer_terminals['mode'], 'mode', 'mode', resource, line, col),
        Terminal(lexer_terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(lexer_terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(lexer_terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, mode, context)
def lexer_code(context, mode, match, terminal, resource, line, col):
    code = match[6:-7].strip()
    tokens = [Terminal(lexer_terminals[terminal], terminal, code, resource, line, col)]
    return (tokens, mode, context)
def lexer_lbrace(context, mode, match, terminal, resource, line, col):
    context['lexer_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def lexer_rbrace(context, mode, match, terminal, resource, line, col):
    context['lexer_brace'] -= 1
    mode = 'grammar' if context['lexer_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_lbrace(context, mode, match, terminal, resource, line, col):
    context['parser_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_rbrace(context, mode, match, terminal, resource, line, col):
    context['parser_brace'] -= 1
    mode = 'grammar' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_rule_start(context, mode, match, terminal, resource, line, col):
    tokens = [
        Terminal(lexer_terminals['ll1_rule_hint'], 'll1_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals[terminal], terminal, normalize_morpheme(match), resource, line, col)
    ]
    return (tokens, mode, context)
def infix_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['infix_rule_hint'], 'infix_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def prefix_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['prefix_rule_hint'], 'prefix_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def expr_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['mixfix_rule_hint'], 'mixfix_rule_hint', '',resource, line, col),
    ]
    return (tokens, mode, context)
def grammar_lbrace(context, mode, match, terminal, resource, line, col):
    context['grammar_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def grammar_rbrace(context, mode, match, terminal, resource, line, col):
    context['grammar_brace'] -= 1
    mode = 'default' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
# END USER CODE
def default_action(context, mode, match, terminal, resource, line, col):
    tokens = [Terminal(lexer_terminals[terminal], terminal, match, resource, line, col)] if terminal else []
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
          (re.compile(r'r\'(\\\'|[^\'])*\''), 'regex', None),
          (re.compile(r'"(\\\"|[^\"])*"'), 'regex', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'mode<[a-zA-Z0-9_]+>'), 'mode', parse_mode),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), 'code', lexer_code),
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
    def _next(self, string, mode, context, resource, line, col):
        for (regex, terminal, function) in self.regex[mode]:
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), terminal, resource, line, col)
                return (tokens, match.group(0), mode)
        return ([], '', mode)
    def lex(self, string, resource, debug=False):
        (mode, line, col) = ('default', 1, 1)
        context = init()
        string_copy = string
        parsed_tokens = []
        while len(string):
            (tokens, match, mode) = self._next(string, mode, context, resource, line, col)
            if len(match) == 0:
                self._unrecognized_token(string_copy, line, col)
            string = string[len(match):]
            if tokens is None:
                self._unrecognized_token(string_copy, line, col)
            parsed_tokens.extend(tokens)
            (line, col) = self._update_line_col(match, line, col)
            if debug:
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
