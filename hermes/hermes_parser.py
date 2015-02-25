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
    0: 'regex_partial',
    1: 'rbrace',
    2: 'expr_rule_hint',
    3: 'langle',
    4: 'parser_ll1',
    5: 'mode',
    6: 'grammar',
    7: 'null',
    8: 'unary',
    9: 'equals',
    10: 'rparen',
    11: 'right',
    12: 'infix_rule_hint',
    13: 'prefix_rule_hint',
    14: 'partials',
    15: 'terminal',
    16: 'left',
    17: 'arrow',
    18: 'asterisk',
    19: 'regex',
    20: 'expression_divider',
    21: 'lbrace',
    22: 'lexer',
    23: 'pipe',
    24: 'comma',
    25: 'integer',
    26: 'nonterminal_reference',
    27: 'mixfix_rule_hint',
    28: 'parser_expression',
    29: 'dash',
    30: 'code',
    31: 'rangle',
    32: 'string',
    33: 'nonterminal',
    34: 'identifier',
    35: 'lparen',
    36: 'll1_rule_hint',
    37: 'colon',
    'regex_partial': 0,
    'rbrace': 1,
    'expr_rule_hint': 2,
    'langle': 3,
    'parser_ll1': 4,
    'mode': 5,
    'grammar': 6,
    'null': 7,
    'unary': 8,
    'equals': 9,
    'rparen': 10,
    'right': 11,
    'infix_rule_hint': 12,
    'prefix_rule_hint': 13,
    'partials': 14,
    'terminal': 15,
    'left': 16,
    'arrow': 17,
    'asterisk': 18,
    'regex': 19,
    'expression_divider': 20,
    'lbrace': 21,
    'lexer': 22,
    'pipe': 23,
    'comma': 24,
    'integer': 25,
    'nonterminal_reference': 26,
    'mixfix_rule_hint': 27,
    'parser_expression': 28,
    'dash': 29,
    'code': 30,
    'rangle': 31,
    'string': 32,
    'nonterminal': 33,
    'identifier': 34,
    'lparen': 35,
    'll1_rule_hint': 36,
    'colon': 37,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1],
    [-1, 42, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, 42, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, 41, 42, 42, -1],
    [-1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, 45, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, 45, -1, 45, -1],
    [-1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1, -1, -1, 86, 84, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1],
    [-1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1],
    [-1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 59, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, 59, 59, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, 79, 79, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1],
    [-1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 38, -1],
    [-1, 55, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1],
    [-1, 7, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 40, -1, -1, 47, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, 40, -1, 40, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, 47, -1, -1, -1, -1, 40, 40, -1, 40, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, 36, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, 36, -1, 36, -1],
    [-1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, 70, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 44, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, 44, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, 44, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, 66, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 49, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1],
]
nonterminal_first = {
    38: [34, -1],
    39: [17],
    40: [22, 4, 28],
    41: [35, -1],
    42: [33, 34, 15, -1],
    43: [17, 34, 33, 15, -1],
    44: [6],
    45: [28],
    46: [25, 15, 32, 33],
    47: [24, -1],
    48: [34],
    49: [4, 28],
    50: [34, 26],
    51: [19, -1],
    52: [36],
    53: [29, 18],
    54: [4],
    55: [35, 2],
    56: [21, -1],
    57: [5],
    58: [36, -1],
    59: [19],
    60: [14],
    61: [34, 33, 15, -1],
    62: [33, 25, 15, 32, -1],
    63: [34, 15, 7],
    64: [23, -1],
    65: [20, -1],
    66: [14, 5, 19, -1],
    67: [15, -1],
    68: [22],
    69: [22, 4, 28, -1],
    70: [19],
    71: [23, 15, 33, 17, 34, 4, 28, 7, -1],
    72: [27, 12, 13],
    73: [14, 5, 19],
    74: [17, 34, 33, 23, 15, -1],
    75: [34, -1],
    76: [29, 18],
    77: [34, 15, 33],
    78: [21],
    79: [22, 4, 28],
    80: [17, -1],
    81: [20],
    82: [24, -1],
    83: [30, -1],
    84: [35],
    85: [34],
    86: [11, 8, 16],
    87: [35, 2, -1],
}
nonterminal_follow = {
    38: [10],
    39: [20, 23, 2, 1, 35, 36],
    40: [22, 4, 1, 28],
    41: [2],
    42: [23, 2, 1, 17, 35, 36],
    43: [23, 36, 1],
    44: [-1],
    45: [22, 1, 36, 4, 28],
    46: [10, 24],
    47: [10],
    48: [10, 24],
    49: [22, 1, 36, 4, 28],
    50: [20, 23, 2, 1, 35, 36],
    51: [1],
    52: [36, 1],
    53: [37],
    54: [22, 1, 36, 4, 28],
    55: [35, 2, 1],
    56: [17],
    57: [19, 14, 1, 5, 30],
    58: [1],
    59: [19, 14, 1, 5, 30],
    60: [19, 14, 1, 5, 30],
    61: [17, 35, 2, 1],
    62: [10],
    63: [19, 14, 1, 5, 30],
    64: [36, 1],
    65: [17, 35, 2, 1],
    66: [30, 1],
    67: [10],
    68: [4, 28, 22, 1],
    69: [1],
    70: [1, 19],
    71: [36, 1],
    72: [35, 2, 1],
    73: [14, 30, 5, 1, 19],
    74: [36, 1],
    75: [1],
    76: [10],
    77: [23, 2, 1, 15, 33, 34, 17, 35, 36],
    78: [17],
    79: [4, 28, 22, 1],
    80: [20, 23, 2, 1, 35, 36],
    81: [17, 35, 2, 1],
    82: [10],
    83: [1],
    84: [2],
    85: [23, 2, 1, 15, 33, 34, 17, 35, 36],
    86: [10],
    87: [1],
}
rule_first = {
    0: [22, 4, 28],
    1: [-1],
    2: [6],
    3: [22, 4, 28],
    4: [22],
    5: [4, 28],
    6: [14, 5, 19],
    7: [-1],
    8: [30],
    9: [-1],
    10: [22],
    11: [19],
    12: [5],
    13: [14],
    14: [19],
    15: [-1],
    16: [14],
    17: [19],
    18: [21],
    19: [-1],
    20: [19],
    21: [34],
    22: [-1],
    23: [21],
    24: [15],
    25: [15],
    26: [-1],
    27: [34],
    28: [7],
    29: [5],
    30: [4],
    31: [28],
    32: [36],
    33: [-1],
    34: [4],
    35: [36],
    36: [23, 15, 33, 17, 34, -1],
    37: [23],
    38: [-1],
    39: [-1],
    40: [23, 15, 33, 17, 34, -1],
    41: [34, 15, 33],
    42: [-1],
    43: [17],
    44: [-1],
    45: [34, 17, -1, 15, 33],
    46: [7],
    47: [4, 28],
    48: [35, 2],
    49: [-1],
    50: [28],
    51: [35],
    52: [-1],
    53: [35, 2],
    54: [20],
    55: [-1],
    56: [27],
    57: [13],
    58: [12],
    59: [34, -1, 15, 33],
    60: [20],
    61: [35],
    62: [29, 18],
    63: [18],
    64: [29],
    65: [16],
    66: [11],
    67: [8],
    68: [15],
    69: [33],
    70: [34],
    71: [17],
    72: [34],
    73: [24],
    74: [-1],
    75: [-1],
    76: [34],
    77: [26],
    78: [34],
    79: [25, 15, 32, 33],
    80: [24],
    81: [-1],
    82: [-1],
    83: [34],
    84: [33],
    85: [15],
    86: [32],
    87: [25],
}
nonterminal_rules = {
    38: [
        "$_gen15 = $ast_parameter $_gen16",
        "$_gen15 = :_empty",
    ],
    39: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    40: [
        "$body_element = $body_element_sub",
    ],
    41: [
        "$_gen13 = $binding_power",
        "$_gen13 = :_empty",
    ],
    42: [
        "$_gen10 = $morpheme $_gen10",
        "$_gen10 = :_empty",
    ],
    43: [
        "$rule = $_gen10 $_gen11 -> Production( morphemes=$0, ast=$1 )",
    ],
    44: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    45: [
        "$parser_expression = :parser_expression :lbrace $_gen12 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    46: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    47: [
        "$_gen16 = :comma $ast_parameter $_gen16",
        "$_gen16 = :_empty",
    ],
    48: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    49: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    50: [
        "$ast_transform_sub = :identifier :lparen $_gen15 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    51: [
        "$_gen3 = $regex_partial $_gen3",
        "$_gen3 = :_empty",
    ],
    52: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    53: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    54: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen7 :rbrace -> Parser( rules=$2 )",
    ],
    55: [
        "$expression_rule = $_gen13 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    56: [
        "$_gen4 = $regex_options",
        "$_gen4 = :_empty",
    ],
    57: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    58: [
        "$_gen7 = $ll1_rule $_gen7",
        "$_gen7 = :_empty",
    ],
    59: [
        "$lexer_regex = :regex $_gen4 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    60: [
        "$lexer_partials = :partials :lbrace $_gen3 :rbrace -> RegexPartials( list=$2 )",
    ],
    61: [
        "$nud = $_gen10",
    ],
    62: [
        "$_gen17 = $macro_parameter $_gen18",
        "$_gen17 = :_empty",
    ],
    63: [
        "$lexer_target = :terminal",
        "$lexer_target = :identifier :lparen $_gen6 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    64: [
        "$_gen9 = :pipe $rule $_gen9",
        "$_gen9 = :_empty",
    ],
    65: [
        "$_gen14 = $led",
        "$_gen14 = :_empty",
    ],
    66: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    67: [
        "$_gen6 = :terminal",
        "$_gen6 = :_empty",
    ],
    68: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    69: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    70: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    71: [
        "$ll1_rule_rhs = $_gen8",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    72: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen11 $_gen14 $_gen11 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen10 $_gen11 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen10 $_gen11 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    73: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
    ],
    74: [
        "$_gen8 = $rule $_gen9",
        "$_gen8 = :_empty",
    ],
    75: [
        "$_gen5 = :identifier $_gen5",
        "$_gen5 = :_empty",
    ],
    76: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    77: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    78: [
        "$regex_options = :lbrace $_gen5 :rbrace -> $1",
    ],
    79: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    80: [
        "$_gen11 = $ast_transform",
        "$_gen11 = :_empty",
    ],
    81: [
        "$led = :expression_divider $_gen10 -> $1",
    ],
    82: [
        "$_gen18 = :comma $macro_parameter $_gen18",
        "$_gen18 = :_empty",
    ],
    83: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    84: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    85: [
        "$macro = :identifier :lparen $_gen17 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    86: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    87: [
        "$_gen12 = $expression_rule $_gen12",
        "$_gen12 = :_empty",
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
    20: "$lexer_regex = :regex $_gen4 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    21: "$_gen5 = :identifier $_gen5",
    22: "$_gen5 = :_empty",
    23: "$regex_options = :lbrace $_gen5 :rbrace -> $1",
    24: "$lexer_target = :terminal",
    25: "$_gen6 = :terminal",
    26: "$_gen6 = :_empty",
    27: "$lexer_target = :identifier :lparen $_gen6 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    28: "$lexer_target = :null -> Null(  )",
    29: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    30: "$parser = $parser_ll1",
    31: "$parser = $parser_expression",
    32: "$_gen7 = $ll1_rule $_gen7",
    33: "$_gen7 = :_empty",
    34: "$parser_ll1 = :parser_ll1 :lbrace $_gen7 :rbrace -> Parser( rules=$2 )",
    35: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    36: "$_gen8 = $rule $_gen9",
    37: "$_gen9 = :pipe $rule $_gen9",
    38: "$_gen9 = :_empty",
    39: "$_gen8 = :_empty",
    40: "$ll1_rule_rhs = $_gen8",
    41: "$_gen10 = $morpheme $_gen10",
    42: "$_gen10 = :_empty",
    43: "$_gen11 = $ast_transform",
    44: "$_gen11 = :_empty",
    45: "$rule = $_gen10 $_gen11 -> Production( morphemes=$0, ast=$1 )",
    46: "$ll1_rule_rhs = :null -> NullProduction(  )",
    47: "$ll1_rule_rhs = $parser",
    48: "$_gen12 = $expression_rule $_gen12",
    49: "$_gen12 = :_empty",
    50: "$parser_expression = :parser_expression :lbrace $_gen12 :rbrace -> ExpressionParser( rules=$2 )",
    51: "$_gen13 = $binding_power",
    52: "$_gen13 = :_empty",
    53: "$expression_rule = $_gen13 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    54: "$_gen14 = $led",
    55: "$_gen14 = :_empty",
    56: "$expression_rule_production = :mixfix_rule_hint $nud $_gen11 $_gen14 $_gen11 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    57: "$expression_rule_production = :prefix_rule_hint $_gen10 $_gen11 -> PrefixProduction( morphemes=$1, ast=$2 )",
    58: "$expression_rule_production = :infix_rule_hint $_gen10 $_gen11 -> InfixProduction( morphemes=$1, ast=$2 )",
    59: "$nud = $_gen10",
    60: "$led = :expression_divider $_gen10 -> $1",
    61: "$binding_power = :lparen $precedence :rparen -> $1",
    62: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    63: "$binding_power_marker = :asterisk",
    64: "$binding_power_marker = :dash",
    65: "$associativity = :left",
    66: "$associativity = :right",
    67: "$associativity = :unary",
    68: "$morpheme = :terminal",
    69: "$morpheme = :nonterminal",
    70: "$morpheme = $macro",
    71: "$ast_transform = :arrow $ast_transform_sub -> $1",
    72: "$_gen15 = $ast_parameter $_gen16",
    73: "$_gen16 = :comma $ast_parameter $_gen16",
    74: "$_gen16 = :_empty",
    75: "$_gen15 = :_empty",
    76: "$ast_transform_sub = :identifier :lparen $_gen15 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    77: "$ast_transform_sub = :nonterminal_reference",
    78: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    79: "$_gen17 = $macro_parameter $_gen18",
    80: "$_gen18 = :comma $macro_parameter $_gen18",
    81: "$_gen18 = :_empty",
    82: "$_gen17 = :_empty",
    83: "$macro = :identifier :lparen $_gen17 :rparen -> Macro( name=$0, parameters=$2 )",
    84: "$macro_parameter = :nonterminal",
    85: "$macro_parameter = :terminal",
    86: "$macro_parameter = :string",
    87: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 37
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
    tree = ParseTree(NonTerminal(38, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[38] and current.id not in nonterminal_first[38]:
        return tree
    if current == None:
        return tree
    if rule == 72: # $_gen15 = $ast_parameter $_gen16
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(39, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 71: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[71]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 17) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[39]],
      rules[71]
    ))
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(40, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[40]],
      rules[3]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[41] and current.id not in nonterminal_first[41]:
        return tree
    if current == None:
        return tree
    if rule == 51: # $_gen13 = $binding_power
        ctx.rule = rules[51]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[42] and current.id not in nonterminal_first[42]:
        return tree
    if current == None:
        return tree
    if rule == 41: # $_gen10 = $morpheme $_gen10
        ctx.rule = rules[41]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $rule = $_gen10 $_gen11 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[45]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[43]],
      rules[45]
    ))
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, 'grammar'))
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
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[44]],
      rules[2]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 50: # $parser_expression = :parser_expression :lbrace $_gen12 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[50]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 28) # :parser_expression
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[45]],
      rules[50]
    ))
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 84: # $macro_parameter = :nonterminal
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 85: # $macro_parameter = :terminal
        ctx.rule = rules[85]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :terminal
        tree.add(t)
        return tree
    elif rule == 86: # $macro_parameter = :string
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 32) # :string
        tree.add(t)
        return tree
    elif rule == 87: # $macro_parameter = :integer
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[87]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[47] and current.id not in nonterminal_first[47]:
        return tree
    if current == None:
        return tree
    if rule == 73: # $_gen16 = :comma $ast_parameter $_gen16
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[78]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 9) # :equals
        tree.add(t)
        t = expect(ctx, 26) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[78]
    ))
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 30: # $parser = $parser_ll1
        ctx.rule = rules[30]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 31: # $parser = $parser_expression
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49]],
      rules[31]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 76: # $ast_transform_sub = :identifier :lparen $_gen15 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[76]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 35) # :lparen
        tree.add(t)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    elif rule == 77: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[77]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 26) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50]],
      rules[77]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[51] and current.id not in nonterminal_first[51]:
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
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 35: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[35]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 36) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 33) # :nonterminal
        tree.add(t)
        t = expect(ctx, 9) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[35]
    ))
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $binding_power_marker = :asterisk
        ctx.rule = rules[63]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :asterisk
        tree.add(t)
        return tree
    elif rule == 64: # $binding_power_marker = :dash
        ctx.rule = rules[64]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[64]
    ))
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 34: # $parser_ll1 = :parser_ll1 :lbrace $_gen7 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[34]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 4) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[54]],
      rules[34]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 53: # $expression_rule = $_gen13 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        t = expect(ctx, 2) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 33) # :nonterminal
        tree.add(t)
        t = expect(ctx, 9) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[53]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
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
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 5) # :mode
        tree.add(t)
        t = expect(ctx, 3) # :langle
        tree.add(t)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 31) # :rangle
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[29]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[58] and current.id not in nonterminal_first[58]:
        return tree
    if current == None:
        return tree
    if rule == 32: # $_gen7 = $ll1_rule $_gen7
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 20: # $lexer_regex = :regex $_gen4 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[20]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 19) # :regex
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :arrow
        tree.add(t)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59]],
      rules[20]
    ))
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'lexer_partials'))
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
        t = expect(ctx, 14) # :partials
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[16]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 59: # $nud = $_gen10
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[61]],
      rules[59]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[62] and current.id not in nonterminal_first[62]:
        return tree
    if current == None:
        return tree
    if rule == 79: # $_gen17 = $macro_parameter $_gen18
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 24: # $lexer_target = :terminal
        ctx.rule = rules[24]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :terminal
        tree.add(t)
        return tree
    elif rule == 27: # $lexer_target = :identifier :lparen $_gen6 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[27]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 35) # :lparen
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    elif rule == 28: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[28]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 7) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[63]],
      rules[28]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[64] and current.id not in nonterminal_first[64]:
        return tree
    if current == None:
        return tree
    if rule == 37: # $_gen9 = :pipe $rule $_gen9
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 23) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = False
    if current != None and current.id in nonterminal_follow[65] and current.id not in nonterminal_first[65]:
        return tree
    if current == None:
        return tree
    if rule == 54: # $_gen14 = $led
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
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
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = False
    if current != None and current.id in nonterminal_follow[67] and current.id not in nonterminal_first[67]:
        return tree
    if current == None:
        return tree
    if rule == 25: # $_gen6 = :terminal
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :terminal
        tree.add(t)
        return tree
    return tree
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'lexer'))
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
        t = expect(ctx, 22) # :lexer
        tree.add(t)
        t = expect(ctx, 3) # :langle
        tree.add(t)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 31) # :rangle
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68]],
      rules[10]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[69] and current.id not in nonterminal_first[69]:
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
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'regex_partial'))
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
        t = expect(ctx, 19) # :regex
        tree.add(t)
        t = expect(ctx, 17) # :arrow
        tree.add(t)
        t = expect(ctx, 0) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[17]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $ll1_rule_rhs = $_gen8
        ctx.rule = rules[40]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    elif rule == 46: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[46]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 7) # :null
        tree.add(t)
        return tree
    elif rule == 47: # $ll1_rule_rhs = $parser
        ctx.rule = rules[47]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71]],
      rules[47]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $expression_rule_production = :mixfix_rule_hint $nud $_gen11 $_gen14 $_gen11 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[56]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 27) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    elif rule == 57: # $expression_rule_production = :prefix_rule_hint $_gen10 $_gen11 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[57]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 13) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    elif rule == 58: # $expression_rule_production = :infix_rule_hint $_gen10 $_gen11 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[58]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 12) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[72]],
      rules[58]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, 'lexer_atom'))
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
      [terminals[x] for x in nonterminal_first[73]],
      rules[13]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[74] and current.id not in nonterminal_first[74]:
        return tree
    if current == None:
        return tree
    if rule == 36: # $_gen8 = $rule $_gen9
        ctx.rule = rules[36]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[75] and current.id not in nonterminal_first[75]:
        return tree
    if current == None:
        return tree
    if rule == 21: # $_gen5 = :identifier $_gen5
        ctx.rule = rules[21]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 62: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[62]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76]],
      rules[62]
    ))
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 68: # $morpheme = :terminal
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :terminal
        tree.add(t)
        return tree
    elif rule == 69: # $morpheme = :nonterminal
        ctx.rule = rules[69]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 70: # $morpheme = $macro
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[70]
    ))
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 23: # $regex_options = :lbrace $_gen5 :rbrace -> $1
        ctx.rule = rules[23]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 1) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[23]
    ))
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[79]],
      rules[5]
    ))
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = False
    if current != None and current.id in nonterminal_follow[80] and current.id not in nonterminal_first[80]:
        return tree
    if current == None:
        return tree
    if rule == 43: # $_gen11 = $ast_transform
        ctx.rule = rules[43]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $led = :expression_divider $_gen10 -> $1
        ctx.rule = rules[60]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 20) # :expression_divider
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[60]
    ))
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
        return tree
    if current == None:
        return tree
    if rule == 80: # $_gen18 = :comma $macro_parameter $_gen18
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[83] and current.id not in nonterminal_first[83]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :code
        tree.add(t)
        return tree
    return tree
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 61: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 35) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84]],
      rules[61]
    ))
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 83: # $macro = :identifier :lparen $_gen17 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[83]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 35) # :lparen
        tree.add(t)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[85]],
      rules[83]
    ))
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 65: # $associativity = :left
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :left
        tree.add(t)
        return tree
    elif rule == 66: # $associativity = :right
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 11) # :right
        tree.add(t)
        return tree
    elif rule == 67: # $associativity = :unary
        ctx.rule = rules[67]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 8) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[86]],
      rules[67]
    ))
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[87] and current.id not in nonterminal_first[87]:
        return tree
    if current == None:
        return tree
    if rule == 48: # $_gen12 = $expression_rule $_gen12
        ctx.rule = rules[48]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    return tree
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
          (re.compile(r'r\'(\\\'|[^\'])*\''), 'regex', None),
          (re.compile(r'"(\\\"|[^\"])*"'), 'regex', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'mode<[a-zA-Z0-9_]+>'), 'mode', parse_mode),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'partials'), 'partials', parse_partials),
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
    def _next(self, string, mode, context, resource, line, col):
        for (regex, terminal, function) in self.regex[mode]:
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), match.groups(), terminal, resource, line, col)
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
