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
    0: 'rparen',
    1: 'action',
    2: 'langle',
    3: 'no_group',
    4: 'rbrace',
    5: 'pipe',
    6: 'rangle',
    7: 'string',
    8: 'identifier',
    9: 'regex_partial',
    10: 'nonterminal_reference',
    11: 'equals',
    12: 'left',
    13: 'lexer',
    14: 'prefix_rule_hint',
    15: 'parser_ll1',
    16: 'right',
    17: 'regex',
    18: 'lsquare',
    19: 'expression_divider',
    20: 'asterisk',
    21: 'code',
    22: 'unary',
    23: 'terminal',
    24: 'dash',
    25: 'comma',
    26: 'stack_push',
    27: 'nonterminal',
    28: 'infix_rule_hint',
    29: 'lbrace',
    30: 'mode',
    31: 'grammar',
    32: 'integer',
    33: 'lparen',
    34: 'colon',
    35: 'expr_rule_hint',
    36: 'll1_rule_hint',
    37: 'null',
    38: 'parser_expression',
    39: 'partials',
    40: 'mixfix_rule_hint',
    41: 'rsquare',
    42: 'arrow',
    'rparen': 0,
    'action': 1,
    'langle': 2,
    'no_group': 3,
    'rbrace': 4,
    'pipe': 5,
    'rangle': 6,
    'string': 7,
    'identifier': 8,
    'regex_partial': 9,
    'nonterminal_reference': 10,
    'equals': 11,
    'left': 12,
    'lexer': 13,
    'prefix_rule_hint': 14,
    'parser_ll1': 15,
    'right': 16,
    'regex': 17,
    'lsquare': 18,
    'expression_divider': 19,
    'asterisk': 20,
    'code': 21,
    'unary': 22,
    'terminal': 23,
    'dash': 24,
    'comma': 25,
    'stack_push': 26,
    'nonterminal': 27,
    'infix_rule_hint': 28,
    'lbrace': 29,
    'mode': 30,
    'grammar': 31,
    'integer': 32,
    'lparen': 33,
    'colon': 34,
    'expr_rule_hint': 35,
    'll1_rule_hint': 36,
    'null': 37,
    'parser_expression': 38,
    'partials': 39,
    'mixfix_rule_hint': 40,
    'rsquare': 41,
    'arrow': 42,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, 59, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1],
    [-1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, 64, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 33, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, 63, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, 66, -1, -1, -1, -1, -1, -1, 66],
    [-1, -1, -1, -1, -1, -1, -1, -1, 87, -1, 88, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 51, 51, -1, -1, 51, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, 51, 57, 58, -1, -1, -1, 51],
    [-1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 89, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [85, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 55, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, 55, 55, -1, -1, -1, -1, -1, 54],
    [-1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1],
    [35, 35, -1, 34, 35, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, 35, 34, -1, -1, 35, -1, 35, -1, -1, 35, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, 35, -1, 35, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1],
    [-1, -1, -1, -1, 49, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 20, -1, -1, 21, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, 21, -1, 20, -1, -1, 20, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, 20, -1, 21, -1, -1, -1],
    [-1, -1, -1, -1, 70, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, 70, -1, -1, -1, -1, -1, 70, -1, 70, -1, -1, -1, -1, -1, -1, 70],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, 77, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [92, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 96, -1, -1, -1, 95, -1, -1, -1, -1, 98, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1],
    [-1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 56, 56, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, 56],
    [-1, -1, -1, -1, 47, 47, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1, -1, 47],
    [93, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, 90, -1, -1, -1, -1, 90, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [86, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 26, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 94, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 53, 53, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, 52, -1, -1, -1, -1, -1, 53, -1, 53, 53, -1, -1, -1, -1, -1, 53],
    [30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    43: [35, -1, 33],
    44: [39, 17, -1, 30],
    45: [-1, 17],
    46: [35, 33],
    47: [36],
    48: [38],
    49: [30],
    50: [8, 26, 23, 37, 1],
    51: [13, 15, 38],
    52: [17],
    53: [39, 17, 30],
    54: [33, -1],
    55: [24, 20],
    56: [19, -1],
    57: [8, 10],
    58: [23],
    59: [8, 15, 27, 37, 38, -1, 42, 5, 23],
    60: [21, -1],
    61: [8],
    62: [25, -1],
    63: [13],
    64: [25, -1],
    65: [42, -1],
    66: [13, 15, 38, -1],
    67: [14, 40, 28],
    68: [15, 38],
    69: [3, -1, 18],
    70: [39],
    71: [5, -1],
    72: [15],
    73: [29],
    74: [8, 1, 26, 37, -1, 23],
    75: [8, 27, 23, -1],
    76: [22, 12, 16],
    77: [42],
    78: [31],
    79: [25, -1],
    80: [27, 23, 7, 32],
    81: [13, 15, 38],
    82: [-1, 36],
    83: [33],
    84: [8, -1, 27, 23, 42],
    85: [8, -1, 27, 42, 5, 23],
    86: [27, 23, 7, 32, -1],
    87: [8, -1],
    88: [29, -1],
    89: [17],
    90: [8, -1],
    91: [19],
    92: [3, 18],
    93: [8],
    94: [8, 27, 23],
    95: [8, -1, 27, 23],
    96: [23, -1],
    97: [24, 20],
}
nonterminal_follow = {
    43: [4],
    44: [4, 21],
    45: [4],
    46: [4, 35, 33],
    47: [4, 36],
    48: [13, 15, 36, 38, 4],
    49: [17, 30, 39, 21, 4],
    50: [8, 1, 26, 17, 37, 30, 39, 21, 4, 23],
    51: [13, 4, 15, 38],
    52: [17, 30, 39, 21, 4],
    53: [39, 4, 21, 17, 30],
    54: [35],
    55: [34],
    56: [33, 4, 42, 35],
    57: [33, 35, 36, 19, 4, 5],
    58: [8, 0, 1, 26, 17, 37, 30, 39, 21, 4, 23],
    59: [4, 36],
    60: [4],
    61: [25, 0],
    62: [0],
    63: [38, 13, 4, 15],
    64: [4],
    65: [33, 35, 36, 19, 4, 5],
    66: [4],
    67: [4, 35, 33],
    68: [13, 15, 36, 38, 4],
    69: [8, 0, 1, 26, 17, 37, 30, 39, 21, 4, 23],
    70: [17, 30, 39, 21, 4],
    71: [4, 36],
    72: [13, 15, 36, 38, 4],
    73: [42],
    74: [17, 30, 39, 21, 4],
    75: [33, 4, 42, 35],
    76: [0],
    77: [33, 35, 36, 19, 4, 5],
    78: [-1],
    79: [0],
    80: [25, 0],
    81: [38, 13, 4, 15],
    82: [4],
    83: [35],
    84: [4, 5, 36],
    85: [4, 36],
    86: [0],
    87: [0],
    88: [42],
    89: [4, 17],
    90: [4],
    91: [33, 4, 42, 35],
    92: [8, 0, 1, 26, 17, 37, 30, 39, 21, 4, 23],
    93: [27, 4, 5, 8, 33, 35, 36, 42, 23],
    94: [8, 33, 27, 35, 36, 4, 42, 23, 5],
    95: [33, 35, 36, 4, 42, 5],
    96: [0],
    97: [0],
}
rule_first = {
    0: [13, 15, 38],
    1: [-1],
    2: [31],
    3: [13, 15, 38],
    4: [13],
    5: [15, 38],
    6: [17, 30, 39],
    7: [-1],
    8: [21],
    9: [-1],
    10: [13],
    11: [17],
    12: [30],
    13: [39],
    14: [17],
    15: [-1],
    16: [39],
    17: [17],
    18: [29],
    19: [-1],
    20: [8, 26, 23, 37, 1],
    21: [-1],
    22: [17],
    23: [8],
    24: [25],
    25: [-1],
    26: [-1],
    27: [29],
    28: [23],
    29: [23],
    30: [-1],
    31: [8],
    32: [26],
    33: [1],
    34: [3, 18],
    35: [-1],
    36: [23],
    37: [18],
    38: [3],
    39: [37],
    40: [30],
    41: [15],
    42: [38],
    43: [36],
    44: [-1],
    45: [15],
    46: [36],
    47: [8, 27, -1, 42, 23, 5],
    48: [5],
    49: [-1],
    50: [-1],
    51: [8, 27, -1, 42, 5, 23],
    52: [8, 27, 23],
    53: [-1],
    54: [42],
    55: [-1],
    56: [8, 27, 23, 42, -1],
    57: [37],
    58: [15, 38],
    59: [35, 33],
    60: [-1],
    61: [38],
    62: [33],
    63: [-1],
    64: [33, 35],
    65: [19],
    66: [-1],
    67: [40],
    68: [14],
    69: [28],
    70: [8, 27, 23, -1],
    71: [19],
    72: [33],
    73: [24, 20],
    74: [20],
    75: [24],
    76: [12],
    77: [16],
    78: [22],
    79: [23],
    80: [27],
    81: [8],
    82: [42],
    83: [8],
    84: [25],
    85: [-1],
    86: [-1],
    87: [8],
    88: [10],
    89: [8],
    90: [27, 23, 7, 32],
    91: [25],
    92: [-1],
    93: [-1],
    94: [8],
    95: [27],
    96: [23],
    97: [7],
    98: [32],
}
nonterminal_rules = {
    43: [
        "$_gen15 = $expression_rule $_gen15",
        "$_gen15 = :_empty",
    ],
    44: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    45: [
        "$_gen3 = $regex_partial $_gen3",
        "$_gen3 = :_empty",
    ],
    46: [
        "$expression_rule = $_gen16 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    47: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    48: [
        "$parser_expression = :parser_expression :lbrace $_gen15 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    49: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    50: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen8 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :stack_push",
        "$lexer_target = :action",
        "$lexer_target = :null -> Null(  )",
    ],
    51: [
        "$body_element = $body_element_sub",
    ],
    52: [
        "$lexer_regex = :regex $_gen4 :arrow $_gen5 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    53: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
    ],
    54: [
        "$_gen16 = $binding_power",
        "$_gen16 = :_empty",
    ],
    55: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    56: [
        "$_gen17 = $led",
        "$_gen17 = :_empty",
    ],
    57: [
        "$ast_transform_sub = :identifier :lparen $_gen18 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    58: [
        "$terminal = :terminal $_gen9 -> Terminal( name=$0, group=$1 )",
    ],
    59: [
        "$ll1_rule_rhs = $_gen11",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    60: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    61: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    62: [
        "$_gen19 = :comma $ast_parameter $_gen19",
        "$_gen19 = :_empty",
    ],
    63: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    64: [
        "$_gen7 = :comma :identifier $_gen7",
        "$_gen7 = :_empty",
    ],
    65: [
        "$_gen14 = $ast_transform",
        "$_gen14 = :_empty",
    ],
    66: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    67: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen14 $_gen17 $_gen14 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen13 $_gen14 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen13 $_gen14 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    68: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    69: [
        "$_gen9 = $match_group",
        "$_gen9 = :_empty",
    ],
    70: [
        "$lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )",
    ],
    71: [
        "$_gen12 = :pipe $rule $_gen12",
        "$_gen12 = :_empty",
    ],
    72: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen10 :rbrace -> Parser( rules=$2 )",
    ],
    73: [
        "$regex_options = :lbrace $_gen6 :rbrace -> $1",
    ],
    74: [
        "$_gen5 = $lexer_target $_gen5",
        "$_gen5 = :_empty",
    ],
    75: [
        "$nud = $_gen13",
    ],
    76: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    77: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    78: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    79: [
        "$_gen21 = :comma $macro_parameter $_gen21",
        "$_gen21 = :_empty",
    ],
    80: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    81: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    82: [
        "$_gen10 = $ll1_rule $_gen10",
        "$_gen10 = :_empty",
    ],
    83: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    84: [
        "$rule = $_gen13 $_gen14 -> Production( morphemes=$0, ast=$1 )",
    ],
    85: [
        "$_gen11 = $rule $_gen12",
        "$_gen11 = :_empty",
    ],
    86: [
        "$_gen20 = $macro_parameter $_gen21",
        "$_gen20 = :_empty",
    ],
    87: [
        "$_gen18 = $ast_parameter $_gen19",
        "$_gen18 = :_empty",
    ],
    88: [
        "$_gen4 = $regex_options",
        "$_gen4 = :_empty",
    ],
    89: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    90: [
        "$_gen6 = :identifier $_gen7",
        "$_gen6 = :_empty",
    ],
    91: [
        "$led = :expression_divider $_gen13 -> $1",
    ],
    92: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    93: [
        "$macro = :identifier :lparen $_gen20 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    94: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    95: [
        "$_gen13 = $morpheme $_gen13",
        "$_gen13 = :_empty",
    ],
    96: [
        "$_gen8 = $terminal",
        "$_gen8 = :_empty",
    ],
    97: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
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
    23: "$_gen6 = :identifier $_gen7",
    24: "$_gen7 = :comma :identifier $_gen7",
    25: "$_gen7 = :_empty",
    26: "$_gen6 = :_empty",
    27: "$regex_options = :lbrace $_gen6 :rbrace -> $1",
    28: "$lexer_target = $terminal",
    29: "$_gen8 = $terminal",
    30: "$_gen8 = :_empty",
    31: "$lexer_target = :identifier :lparen $_gen8 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    32: "$lexer_target = :stack_push",
    33: "$lexer_target = :action",
    34: "$_gen9 = $match_group",
    35: "$_gen9 = :_empty",
    36: "$terminal = :terminal $_gen9 -> Terminal( name=$0, group=$1 )",
    37: "$match_group = :lsquare :integer :rsquare -> $1",
    38: "$match_group = :no_group",
    39: "$lexer_target = :null -> Null(  )",
    40: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    41: "$parser = $parser_ll1",
    42: "$parser = $parser_expression",
    43: "$_gen10 = $ll1_rule $_gen10",
    44: "$_gen10 = :_empty",
    45: "$parser_ll1 = :parser_ll1 :lbrace $_gen10 :rbrace -> Parser( rules=$2 )",
    46: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    47: "$_gen11 = $rule $_gen12",
    48: "$_gen12 = :pipe $rule $_gen12",
    49: "$_gen12 = :_empty",
    50: "$_gen11 = :_empty",
    51: "$ll1_rule_rhs = $_gen11",
    52: "$_gen13 = $morpheme $_gen13",
    53: "$_gen13 = :_empty",
    54: "$_gen14 = $ast_transform",
    55: "$_gen14 = :_empty",
    56: "$rule = $_gen13 $_gen14 -> Production( morphemes=$0, ast=$1 )",
    57: "$ll1_rule_rhs = :null -> NullProduction(  )",
    58: "$ll1_rule_rhs = $parser",
    59: "$_gen15 = $expression_rule $_gen15",
    60: "$_gen15 = :_empty",
    61: "$parser_expression = :parser_expression :lbrace $_gen15 :rbrace -> ExpressionParser( rules=$2 )",
    62: "$_gen16 = $binding_power",
    63: "$_gen16 = :_empty",
    64: "$expression_rule = $_gen16 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    65: "$_gen17 = $led",
    66: "$_gen17 = :_empty",
    67: "$expression_rule_production = :mixfix_rule_hint $nud $_gen14 $_gen17 $_gen14 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    68: "$expression_rule_production = :prefix_rule_hint $_gen13 $_gen14 -> PrefixProduction( morphemes=$1, ast=$2 )",
    69: "$expression_rule_production = :infix_rule_hint $_gen13 $_gen14 -> InfixProduction( morphemes=$1, ast=$2 )",
    70: "$nud = $_gen13",
    71: "$led = :expression_divider $_gen13 -> $1",
    72: "$binding_power = :lparen $precedence :rparen -> $1",
    73: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    74: "$binding_power_marker = :asterisk",
    75: "$binding_power_marker = :dash",
    76: "$associativity = :left",
    77: "$associativity = :right",
    78: "$associativity = :unary",
    79: "$morpheme = :terminal",
    80: "$morpheme = :nonterminal",
    81: "$morpheme = $macro",
    82: "$ast_transform = :arrow $ast_transform_sub -> $1",
    83: "$_gen18 = $ast_parameter $_gen19",
    84: "$_gen19 = :comma $ast_parameter $_gen19",
    85: "$_gen19 = :_empty",
    86: "$_gen18 = :_empty",
    87: "$ast_transform_sub = :identifier :lparen $_gen18 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    88: "$ast_transform_sub = :nonterminal_reference",
    89: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    90: "$_gen20 = $macro_parameter $_gen21",
    91: "$_gen21 = :comma $macro_parameter $_gen21",
    92: "$_gen21 = :_empty",
    93: "$_gen20 = :_empty",
    94: "$macro = :identifier :lparen $_gen20 :rparen -> Macro( name=$0, parameters=$2 )",
    95: "$macro_parameter = :nonterminal",
    96: "$macro_parameter = :terminal",
    97: "$macro_parameter = :string",
    98: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 42
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
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[43] and current.id not in nonterminal_first[43]:
        return tree
    if current == None:
        return tree
    if rule == 59: # $_gen15 = $expression_rule $_gen15
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[44] and current.id not in nonterminal_first[44]:
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
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[45] and current.id not in nonterminal_first[45]:
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
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 64: # $expression_rule = $_gen16 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[64]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 35) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 27) # :nonterminal
        tree.add(t)
        t = expect(ctx, 11) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[64]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 46: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[46]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 36) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 27) # :nonterminal
        tree.add(t)
        t = expect(ctx, 11) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[47]],
      rules[46]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 61: # $parser_expression = :parser_expression :lbrace $_gen15 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[61]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 38) # :parser_expression
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[61]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[40]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 30) # :mode
        tree.add(t)
        t = expect(ctx, 2) # :langle
        tree.add(t)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :rangle
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49]],
      rules[40]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 28: # $lexer_target = $terminal
        ctx.rule = rules[28]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    elif rule == 31: # $lexer_target = :identifier :lparen $_gen8 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[31]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        t = expect(ctx, 0) # :rparen
        tree.add(t)
        return tree
    elif rule == 32: # $lexer_target = :stack_push
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :stack_push
        tree.add(t)
        return tree
    elif rule == 33: # $lexer_target = :action
        ctx.rule = rules[33]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :action
        tree.add(t)
        return tree
    elif rule == 39: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[39]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 37) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50]],
      rules[39]
    ))
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[51]],
      rules[3]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'lexer_regex'))
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
        t = expect(ctx, 17) # :regex
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[22]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'lexer_atom'))
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
      [terminals[x] for x in nonterminal_first[53]],
      rules[13]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = False
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
        return tree
    if current == None:
        return tree
    if rule == 62: # $_gen16 = $binding_power
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 74: # $binding_power_marker = :asterisk
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 20) # :asterisk
        tree.add(t)
        return tree
    elif rule == 75: # $binding_power_marker = :dash
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[75]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 65: # $_gen17 = $led
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 87: # $ast_transform_sub = :identifier :lparen $_gen18 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[87]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        t = expect(ctx, 0) # :rparen
        tree.add(t)
        return tree
    elif rule == 88: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[88]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 10) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[88]
    ))
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'terminal'))
    ctx.nonterminal = "terminal"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 36: # $terminal = :terminal $_gen9 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[36]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 23) # :terminal
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58]],
      rules[36]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 51: # $ll1_rule_rhs = $_gen11
        ctx.rule = rules[51]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    elif rule == 57: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[57]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 37) # :null
        tree.add(t)
        return tree
    elif rule == 58: # $ll1_rule_rhs = $parser
        ctx.rule = rules[58]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59]],
      rules[58]
    ))
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[60] and current.id not in nonterminal_first[60]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 21) # :code
        tree.add(t)
        return tree
    return tree
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 89: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[89]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 11) # :equals
        tree.add(t)
        t = expect(ctx, 10) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[61]],
      rules[89]
    ))
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[62] and current.id not in nonterminal_first[62]:
        return tree
    if current == None:
        return tree
    if rule == 84: # $_gen19 = :comma $ast_parameter $_gen19
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'lexer'))
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
        t = expect(ctx, 13) # :lexer
        tree.add(t)
        t = expect(ctx, 2) # :langle
        tree.add(t)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :rangle
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
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
      [terminals[x] for x in nonterminal_first[63]],
      rules[10]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[64] and current.id not in nonterminal_first[64]:
        return tree
    if current == None:
        return tree
    if rule == 24: # $_gen7 = :comma :identifier $_gen7
        ctx.rule = rules[24]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :comma
        tree.add(t)
        tree.listSeparator = t
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = False
    if current != None and current.id in nonterminal_follow[65] and current.id not in nonterminal_first[65]:
        return tree
    if current == None:
        return tree
    if rule == 54: # $_gen14 = $ast_transform
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
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
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 67: # $expression_rule_production = :mixfix_rule_hint $nud $_gen14 $_gen17 $_gen14 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[67]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 40) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    elif rule == 68: # $expression_rule_production = :prefix_rule_hint $_gen13 $_gen14 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[68]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 14) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    elif rule == 69: # $expression_rule_production = :infix_rule_hint $_gen13 $_gen14 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[69]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 28) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[67]],
      rules[69]
    ))
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 41: # $parser = $parser_ll1
        ctx.rule = rules[41]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 42: # $parser = $parser_expression
        ctx.rule = rules[42]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68]],
      rules[42]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = False
    if current != None and current.id in nonterminal_follow[69] and current.id not in nonterminal_first[69]:
        return tree
    if current == None:
        return tree
    if rule == 34: # $_gen9 = $match_group
        ctx.rule = rules[34]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_match_group(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'lexer_partials'))
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
        t = expect(ctx, 39) # :partials
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[16]
    ))
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[71] and current.id not in nonterminal_first[71]:
        return tree
    if current == None:
        return tree
    if rule == 48: # $_gen12 = :pipe $rule $_gen12
        ctx.rule = rules[48]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 5) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $parser_ll1 = :parser_ll1 :lbrace $_gen10 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[45]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 15) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[72]],
      rules[45]
    ))
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 27: # $regex_options = :lbrace $_gen6 :rbrace -> $1
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[73]],
      rules[27]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[74] and current.id not in nonterminal_first[74]:
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
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 70: # $nud = $_gen13
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75]],
      rules[70]
    ))
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 76: # $associativity = :left
        ctx.rule = rules[76]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 12) # :left
        tree.add(t)
        return tree
    elif rule == 77: # $associativity = :right
        ctx.rule = rules[77]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :right
        tree.add(t)
        return tree
    elif rule == 78: # $associativity = :unary
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 22) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76]],
      rules[78]
    ))
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 82: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[82]
    ))
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'grammar'))
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
        t = expect(ctx, 31) # :grammar
        tree.add(t)
        t = expect(ctx, 29) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[2]
    ))
def parse__gen21(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, '_gen21'))
    ctx.nonterminal = "_gen21"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[79] and current.id not in nonterminal_first[79]:
        return tree
    if current == None:
        return tree
    if rule == 91: # $_gen21 = :comma $macro_parameter $_gen21
        ctx.rule = rules[91]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen21(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 95: # $macro_parameter = :nonterminal
        ctx.rule = rules[95]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 27) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 96: # $macro_parameter = :terminal
        ctx.rule = rules[96]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 23) # :terminal
        tree.add(t)
        return tree
    elif rule == 97: # $macro_parameter = :string
        ctx.rule = rules[97]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 7) # :string
        tree.add(t)
        return tree
    elif rule == 98: # $macro_parameter = :integer
        ctx.rule = rules[98]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 32) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[80]],
      rules[98]
    ))
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[81]],
      rules[5]
    ))
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
        return tree
    if current == None:
        return tree
    if rule == 43: # $_gen10 = $ll1_rule $_gen10
        ctx.rule = rules[43]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 72: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 0) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[83]],
      rules[72]
    ))
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $rule = $_gen13 $_gen14 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[56]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84]],
      rules[56]
    ))
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[85] and current.id not in nonterminal_first[85]:
        return tree
    if current == None:
        return tree
    if rule == 47: # $_gen11 = $rule $_gen12
        ctx.rule = rules[47]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen20(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, '_gen20'))
    ctx.nonterminal = "_gen20"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[86] and current.id not in nonterminal_first[86]:
        return tree
    if current == None:
        return tree
    if rule == 90: # $_gen20 = $macro_parameter $_gen21
        ctx.rule = rules[90]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen21(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[87] and current.id not in nonterminal_first[87]:
        return tree
    if current == None:
        return tree
    if rule == 83: # $_gen18 = $ast_parameter $_gen19
        ctx.rule = rules[83]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = False
    if current != None and current.id in nonterminal_follow[88] and current.id not in nonterminal_first[88]:
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
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(89, 'regex_partial'))
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
        t = expect(ctx, 17) # :regex
        tree.add(t)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        t = expect(ctx, 9) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[89]],
      rules[17]
    ))
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[90] and current.id not in nonterminal_first[90]:
        return tree
    if current == None:
        return tree
    if rule == 23: # $_gen6 = :identifier $_gen7
        ctx.rule = rules[23]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 71: # $led = :expression_divider $_gen13 -> $1
        ctx.rule = rules[71]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 19) # :expression_divider
        tree.add(t)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[91]],
      rules[71]
    ))
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 37: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 18) # :lsquare
        tree.add(t)
        t = expect(ctx, 32) # :integer
        tree.add(t)
        t = expect(ctx, 41) # :rsquare
        tree.add(t)
        return tree
    elif rule == 38: # $match_group = :no_group
        ctx.rule = rules[38]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 3) # :no_group
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92]],
      rules[38]
    ))
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 94: # $macro = :identifier :lparen $_gen20 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[94]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 8) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :lparen
        tree.add(t)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        t = expect(ctx, 0) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[93]],
      rules[94]
    ))
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $morpheme = :terminal
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 23) # :terminal
        tree.add(t)
        return tree
    elif rule == 80: # $morpheme = :nonterminal
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 27) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 81: # $morpheme = $macro
        ctx.rule = rules[81]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94]],
      rules[81]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(95, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[95] and current.id not in nonterminal_first[95]:
        return tree
    if current == None:
        return tree
    if rule == 52: # $_gen13 = $morpheme $_gen13
        ctx.rule = rules[52]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(96, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = False
    if current != None and current.id in nonterminal_follow[96] and current.id not in nonterminal_first[96]:
        return tree
    if current == None:
        return tree
    if rule == 29: # $_gen8 = $terminal
        ctx.rule = rules[29]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[54][current.id] if current else -1
    tree = ParseTree(NonTerminal(97, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 73: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[73]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 34) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[97]],
      rules[73]
    ))
# Lexer Code #
# START USER CODE
# END USER CODE
def emit(ctx, terminal, source_string, line, col):
    if terminal:
        ctx.tokens.append(Terminal(terminals[terminal], terminal, source_string, ctx.resource, line, col))
def default_action(ctx, terminal, source_string, line, col):
    emit(ctx, terminal, source_string, line, col)
def init():
    return {}
def destroy(context):
    pass
class LexerStackPush:
    def __init__(self, mode):
        self.mode = mode
class LexerAction:
    def __init__(self, action):
        self.action = action
class LexerContext:
    def __init__(self, string, resource, user_context):
        self.__dict__.update(locals())
        self.stack = ['default']
        self.line = 1
        self.col = 1
        self.tokens = []
        self.user_context = user_context
        self.re_match = None # https://docs.python.org/3/library/re.html#match-objects
class HermesLexer:
    regex = {
        'default': OrderedDict([
          (re.compile(r'(grammar)\s*({)'), [
              # (terminal, group, function)
              ('grammar', 1, None),
              ('lbrace', 2, None),
              LexerStackPush('grammar'),
          ]),
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
        ]),
        'grammar': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
          ]),
          (re.compile(r'(lexer)\s*(<)\s*([a-zA-Z][a-zA-Z0-9_]*)\s*(>)\s*({)'), [
              # (terminal, group, function)
              ('lexer', 1, None),
              ('langle', 2, None),
              ('identifier', 3, None),
              ('rangle', 4, None),
              ('lbrace', 5, None),
              LexerStackPush('lexer'),
          ]),
          (re.compile(r'(parser\s*<\s*ll1\s*>)\s*({)'), [
              # (terminal, group, function)
              ('parser_ll1', 1, None),
              ('lbrace', 2, None),
              LexerStackPush('parser_ll1'),
          ]),
        ]),
        'lexer': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
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
          (re.compile(r'@([a-zA-Z][a-zA-Z0-9_]*)'), [
              # (terminal, group, function)
              ('stack_push', 1, None),
          ]),
          (re.compile(r'%([a-zA-Z][a-zA-Z0-9_]*)'), [
              # (terminal, group, function)
              ('action', 1, None),
          ]),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), [
              # (terminal, group, function)
              ('terminal', 1, None),
          ]),
          (re.compile(r'(mode)\s*(<)\s*([a-zA-Z][a-zA-Z0-9_]*)\s*(>)\s*({)'), [
              # (terminal, group, function)
              ('mode', 1, None),
              ('langle', 2, None),
              ('identifier', 3, None),
              ('rangle', 4, None),
              ('lbrace', 5, None),
              LexerStackPush('lexer'),
          ]),
          (re.compile(r'(partials)\s*({)'), [
              # (terminal, group, function)
              ('partials', 1, None),
              ('lbrace', 2, None),
              LexerStackPush('partials'),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
              LexerStackPush('regex_options'),
          ]),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), [
              # (terminal, group, function)
              ('code', 1, None),
          ]),
        ]),
        'regex_options': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
          (re.compile(r','), [
              # (terminal, group, function)
              ('comma', 0, None),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
          ]),
        ]),
        'partials': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
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
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
          ]),
        ]),
        'parser_ll1': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
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
          (re.compile(r'parser\s*<\s*expression\s*>\s*({)'), [
              # (terminal, group, function)
              ('parser_expression', None, None),
              ('lbrace', 1, None),
              LexerStackPush('parser_expr'),
          ]),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), [
              # (terminal, group, function)
              ('terminal', 1, None),
          ]),
          (re.compile(r'\$([a-zA-Z][a-zA-Z0-9_]*)(?=\s*\=)'), [
              # (terminal, group, function)
              ('ll1_rule_hint', None, None),
              ('nonterminal', 1, None),
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
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'(\()(?=\s*[\*-])'), [
              # (terminal, group, function)
              ('lparen', 1, None),
              LexerStackPush('binding_power'),
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
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
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
        'binding_power': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\*'), [
              # (terminal, group, function)
              ('asterisk', 0, None),
          ]),
          (re.compile(r'-'), [
              # (terminal, group, function)
              ('dash', 0, None),
          ]),
          (re.compile(r':'), [
              # (terminal, group, function)
              ('colon', 0, None),
          ]),
          (re.compile(r'left'), [
              # (terminal, group, function)
              ('left', 0, None),
          ]),
          (re.compile(r'right'), [
              # (terminal, group, function)
              ('right', 0, None),
          ]),
          (re.compile(r'unary'), [
              # (terminal, group, function)
              ('unary', 0, None),
          ]),
          (re.compile(r'\)'), [
              # (terminal, group, function)
              ('rparen', 0, None),
              LexerAction('pop'),
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
    def _advance_string(self, ctx, string):
        (ctx.line, ctx.col) = self._advance_line_col(string, len(string), ctx.line, ctx.col)
        ctx.string = ctx.string[len(string):]
    def _unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        message = 'Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        )
        raise SyntaxError(message)
    def _next(self, ctx, debug=False):
        for regex, outputs in self.regex[ctx.stack[-1]].items():
            if debug:
                token_count = len(ctx.tokens)
                print('trying: `{1}` ({2}, {3}) against {0}'.format(
                    regex, ctx.string[:20].replace('\n', '\\n'), ctx.line, ctx.col)
                )
            match = regex.match(ctx.string)
            if match:
                ctx.re_match = match
                for output in outputs:
                    if isinstance(output, tuple):
                        (terminal, group, function) = output
                        function = function if function else default_action
                        source_string = match.group(group) if group is not None else ''
                        (group_line, group_col) = self._advance_line_col(ctx.string, match.start(group) if group else 0, ctx.line, ctx.col)
                        function(
                            ctx,
                            terminal,
                            source_string,
                            group_line,
                            group_col
                        )
                        if debug:
                            print('    match: string={}'.format(match.group(0).replace('\n', '\\n')))
                            for token in ctx.tokens[token_count:]:
                                print('           emit token: {}'.format(token))
                            token_count = len(ctx.tokens)
                    if isinstance(output, LexerStackPush):
                        ctx.stack.append(output.mode)
                    if isinstance(output, LexerAction):
                        if output.action == 'pop':
                            ctx.stack.pop()
                self._advance_string(ctx, match.group(0))
                return len(match.group(0)) > 0
        return False
    def lex(self, string, resource, debug=False):
        string_copy = string
        user_context = init()
        ctx = LexerContext(string, resource, user_context)
        while len(ctx.string):
            matched = self._next(ctx)
            if matched == False:
                self._unrecognized_token(string_copy, ctx.line, ctx.col)
            if debug:
                from xtermcolor import colorize
                for token in tokens:
                    print('token --> [{}] [{}, {}] [{}] [{}] [{}]'.format(
                        colorize(token.str, ansi=9),
                        colorize(str(token.line), ansi=5),
                        colorize(str(token.col), ansi=5),
                        colorize(token.source_string, ansi=3),
                        colorize(str(mode_stack), ansi=4),
                        colorize(str(context), ansi=13)
                    ))
        destroy(ctx.user_context)
        return ctx.tokens
def lex(source, resource, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, debug))
