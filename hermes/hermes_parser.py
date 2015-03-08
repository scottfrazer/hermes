import sys
import os
import re
import base64
import argparse
import json
from collections import OrderedDict
# Common Code #
def parse_tree_string(parsetree, indent=None, b64_source=True, indent_level=0):
    indent_str = (' ' * indent * indent_level) if indent else ''
    if isinstance(parsetree, ParseTree):
        children = [parse_tree_string(child, indent, b64_source, indent_level+1) for child in parsetree.children]
        if indent is None or len(children) == 0:
            return '{0}({1}: {2})'.format(indent_str, parsetree.nonterminal, ', '.join(children))
        else:
            return '{0}({1}:\n{2}\n{3})'.format(
                indent_str,
                parsetree.nonterminal,
                ',\n'.join(children),
                indent_str
            )
    elif isinstance(parsetree, Terminal):
        return indent_str + parsetree.dumps(b64_source=b64_source)
def ast_string(ast, indent=None, b64_source=True, indent_level=0):
    indent_str = (' ' * indent * indent_level) if indent else ''
    next_indent_str = (' ' * indent * (indent_level+1)) if indent else ''
    if isinstance(ast, Ast):
        children = OrderedDict([(k, ast_string(v, indent, b64_source, indent_level+1)) for k, v in ast.attributes.items()])
        if indent is None:
            return '({0}: {1})'.format(
                ast.name,
                ', '.join('{0}={1}'.format(k, v) for k, v in children.items())
            )
        else:
            return '({0}:\n{1}\n{2})'.format(
                ast.name,
                ',\n'.join(['{0}{1}={2}'.format(next_indent_str, k, v) for k, v in children.items()]),
                indent_str
            )
    elif isinstance(ast, list):
        children = [ast_string(element, indent, b64_source, indent_level+1) for element in ast]
        if indent is None or len(children) == 0:
            return '[{0}]'.format(', '.join(children))
        else:
            return '[\n{1}\n{0}]'.format(
                indent_str,
                ',\n'.join(['{0}{1}'.format(next_indent_str, child) for child in children]),
            )
    elif isinstance(ast, Terminal):
        return ast.dumps(b64_source=b64_source)
class Terminal:
  def __init__(self, id, str, source_string, resource, line, col):
      self.__dict__.update(locals())
  def getId(self):
      return self.id
  def toAst(self):
      return self
  def dumps(self, b64_source=True, json=False, **kwargs):
      if not b64_source and json:
          raise Exception('b64_source must be set to True if json=True')
      source_string = base64.b64encode(self.source_string.encode('utf-8')).decode('utf-8') if b64_source else self.source_string
      if json:
          json_fmt = '"terminal": "{0}", "resource": "{1}", "line": {2}, "col": {3}, "source_string": "{4}"'
          return '{' + json_fmt.format(self.str, self.resource, self.line, self.col, source_string) + '}'
      else:
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
  def dumps(self, indent=None, b64_source=True):
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
  def dumps(self, indent=None, b64_source=True):
      args = locals()
      del args['self']
      return parse_tree_string(self, **args)
class Ast():
    def __init__(self, name, attributes):
        self.__dict__.update(locals())
    def getAttr(self, attr):
        return self.attributes[attr]
    def dumps(self, indent=None, b64_source=True):
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
            tokens_json.append(token.dumps(json=True, b64_source=True))
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
    0: 'lexer',
    1: 'nonterminal',
    2: 'langle',
    3: 'lbrace',
    4: 'lparen',
    5: 'mixfix_rule_hint',
    6: 'parser_expression',
    7: 'asterisk',
    8: 'integer',
    9: 'partials',
    10: 'parser',
    11: 'll1_rule_hint',
    12: 'right',
    13: 'action',
    14: 'unary',
    15: 'identifier',
    16: 'rparen',
    17: 'stack_push',
    18: 'terminal',
    19: 'no_group',
    20: 'pipe',
    21: 'nonterminal_reference',
    22: 'string',
    23: 'infix_rule_hint',
    24: 'grammar',
    25: 'equals',
    26: 'expr_rule_hint',
    27: 'expression_divider',
    28: 'mode',
    29: 'left',
    30: 'lsquare',
    31: 'arrow',
    32: 'colon',
    33: 'code',
    34: 'rangle',
    35: 'regex_partial',
    36: 'prefix_rule_hint',
    37: 'comma',
    38: 'rbrace',
    39: 'regex',
    40: 'rsquare',
    41: 'null',
    42: 'dash',
    'lexer': 0,
    'nonterminal': 1,
    'langle': 2,
    'lbrace': 3,
    'lparen': 4,
    'mixfix_rule_hint': 5,
    'parser_expression': 6,
    'asterisk': 7,
    'integer': 8,
    'partials': 9,
    'parser': 10,
    'll1_rule_hint': 11,
    'right': 12,
    'action': 13,
    'unary': 14,
    'identifier': 15,
    'rparen': 16,
    'stack_push': 17,
    'terminal': 18,
    'no_group': 19,
    'pipe': 20,
    'nonterminal_reference': 21,
    'string': 22,
    'infix_rule_hint': 23,
    'grammar': 24,
    'equals': 25,
    'expr_rule_hint': 26,
    'expression_divider': 27,
    'mode': 28,
    'left': 29,
    'lsquare': 30,
    'arrow': 31,
    'colon': 32,
    'code': 33,
    'rangle': 34,
    'regex_partial': 35,
    'prefix_rule_hint': 36,
    'comma': 37,
    'rbrace': 38,
    'regex': 39,
    'rsquare': 40,
    'null': 41,
    'dash': 42,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, 83, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, 34, -1, 35, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, 16, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 98, -1, -1, -1, -1, -1, -1, 101, -1, -1, -1, -1, -1, -1, -1, -1, -1, 99, -1, -1, -1, 100, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, 89, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78],
    [-1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, 50, -1, -1, 50, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1],
    [-1, 55, -1, -1, 56, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, 55, -1, -1, 55, -1, 56, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, 11, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, 21, -1, -1, -1],
    [-1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, 68, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76],
    [-1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, 9, -1, -1, -1, -1, 9, 8, -1, -1, -1],
    [-1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, 59, -1, -1, 59, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 95, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 94, -1, -1, -1, -1, -1],
    [-1, 93, -1, -1, -1, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, 96, -1, 93, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1],
    [3, -1, -1, -1, -1, -1, 3, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 38, -1, -1, -1, 38, -1, 38, 38, 38, 38, 37, -1, -1, -1, -1, -1, -1, -1, -1, 38, -1, 37, -1, -1, 38, -1, -1, -1, -1, 38, 38, -1, 38, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 45, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 73, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, -1, -1, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1],
    [4, -1, -1, -1, -1, -1, 5, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, 27, -1, 27, -1, 27, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, 28, -1, -1, -1, -1, 28, 28, -1, 27, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1],
    [-1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, 58, 58, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1],
    [-1, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 6, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 54, -1, -1, -1, -1, 61, -1, -1, -1, 61, 54, -1, -1, -1, 54, -1, -1, 54, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, 54, -1, -1, 60, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, 14, 15, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 92, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    43: [15, 18, 1],
    44: [15, 13, 41, 18, 17],
    45: [15, 21],
    46: [28],
    47: [15, -1],
    48: [11],
    49: [0],
    50: [-1, 18],
    51: [22, 8, 18, 1],
    52: [24],
    53: [26, 4],
    54: [-1, 11],
    55: [15],
    56: [-1, 3],
    57: [37, -1],
    58: [15, -1],
    59: [7, 42],
    60: [31, 15, 1, 20, -1, 18],
    61: [15, 1, -1, 18],
    62: [31],
    63: [6],
    64: [27],
    65: [33, -1],
    66: [-1, 39],
    67: [-1, 4],
    68: [27, -1],
    69: [7, 42],
    70: [3],
    71: [28, 9, -1, 39],
    72: [31, 15, 1, -1, 18],
    73: [37, -1],
    74: [22, 8, -1, 18, 1],
    75: [39],
    76: [6, 0, 10],
    77: [5, 36, 23],
    78: [28, 9, 39],
    79: [30, -1, 19],
    80: [29, 12, 14],
    81: [-1, 26, 4],
    82: [6, 10],
    83: [15, -1, 18, 1],
    84: [10],
    85: [6, 0, -1, 10],
    86: [6, 0, 10],
    87: [13, 15, 17, 41, -1, 18],
    88: [20, -1],
    89: [39],
    90: [31, -1],
    91: [4],
    92: [30, 19],
    93: [2],
    94: [2, -1],
    95: [31, 10, 1, 20, 15, 6, 41, -1, 18],
    96: [18],
    97: [37, -1],
    98: [15],
    99: [9],
}
nonterminal_follow = {
    43: [31, 11, 1, 20, 4, 15, 26, 38, 18],
    44: [9, 33, 13, 15, 38, 17, 39, 28, 41, 18],
    45: [11, 20, 4, 26, 38, 27],
    46: [9, 33, 38, 39, 28],
    47: [38, 34],
    48: [11, 38],
    49: [0, 10, 38, 6],
    50: [16],
    51: [37, 16],
    52: [-1],
    53: [38, 26, 4],
    54: [38],
    55: [1, 20, 4, 26, 31, 11, 15, 38, 18],
    56: [31],
    57: [16],
    58: [16],
    59: [32],
    60: [11, 38],
    61: [31, 11, 20, 4, 26, 38],
    62: [11, 20, 4, 26, 38, 27],
    63: [0, 10, 11, 38, 6],
    64: [31, 26, 38, 4],
    65: [38],
    66: [38],
    67: [26],
    68: [31, 26, 38, 4],
    69: [16],
    70: [31],
    71: [33, 38],
    72: [20, 11, 38],
    73: [16],
    74: [16],
    75: [9, 33, 38, 39, 28],
    76: [6, 0, 10, 38],
    77: [38, 26, 4],
    78: [28, 9, 33, 38, 39],
    79: [9, 33, 13, 15, 16, 38, 17, 39, 28, 41, 18],
    80: [16],
    81: [38],
    82: [0, 10, 11, 38, 6],
    83: [31, 26, 38, 4],
    84: [0, 10, 11, 38, 6],
    85: [38],
    86: [0, 10, 38, 6],
    87: [9, 33, 38, 39, 28],
    88: [11, 38],
    89: [38, 39],
    90: [11, 20, 4, 26, 38, 27],
    91: [26],
    92: [9, 33, 13, 15, 16, 38, 17, 39, 28, 41, 18],
    93: [3],
    94: [3],
    95: [11, 38],
    96: [9, 33, 13, 15, 16, 38, 17, 39, 28, 41, 18],
    97: [38, 34],
    98: [37, 16],
    99: [9, 33, 38, 39, 28],
}
rule_first = {
    0: [6, 0, 10],
    1: [-1],
    2: [24],
    3: [6, 0, 10],
    4: [0],
    5: [6, 10],
    6: [2],
    7: [-1],
    8: [28, 9, 39],
    9: [-1],
    10: [33],
    11: [-1],
    12: [0],
    13: [15],
    14: [37],
    15: [-1],
    16: [-1],
    17: [2],
    18: [39],
    19: [28],
    20: [9],
    21: [39],
    22: [-1],
    23: [9],
    24: [39],
    25: [3],
    26: [-1],
    27: [15, 13, 41, 18, 17],
    28: [-1],
    29: [39],
    30: [3],
    31: [18],
    32: [18],
    33: [-1],
    34: [15],
    35: [17],
    36: [13],
    37: [30, 19],
    38: [-1],
    39: [18],
    40: [30],
    41: [19],
    42: [41],
    43: [28],
    44: [10],
    45: [6],
    46: [11],
    47: [-1],
    48: [10],
    49: [11],
    50: [31, 1, 20, 15, -1, 18],
    51: [20],
    52: [-1],
    53: [-1],
    54: [31, 1, 20, 15, -1, 18],
    55: [15, 18, 1],
    56: [-1],
    57: [31],
    58: [-1],
    59: [31, 15, -1, 18, 1],
    60: [41],
    61: [6, 10],
    62: [26, 4],
    63: [-1],
    64: [6],
    65: [4],
    66: [-1],
    67: [4, 26],
    68: [27],
    69: [-1],
    70: [5],
    71: [36],
    72: [23],
    73: [15, -1, 18, 1],
    74: [27],
    75: [4],
    76: [7, 42],
    77: [7],
    78: [42],
    79: [29],
    80: [12],
    81: [14],
    82: [18],
    83: [1],
    84: [15],
    85: [31],
    86: [15],
    87: [37],
    88: [-1],
    89: [-1],
    90: [15],
    91: [21],
    92: [15],
    93: [22, 8, 18, 1],
    94: [37],
    95: [-1],
    96: [-1],
    97: [15],
    98: [1],
    99: [18],
    100: [22],
    101: [8],
}
nonterminal_rules = {
    43: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    44: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :stack_push",
        "$lexer_target = :action",
        "$lexer_target = :null -> Null(  )",
    ],
    45: [
        "$ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    46: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen2 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    47: [
        "$_gen4 = :identifier $_gen5",
        "$_gen4 = :_empty",
    ],
    48: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    49: [
        "$lexer = :lexer $_gen1 :lbrace $_gen2 $_gen3 :rbrace -> Lexer( languages=$1, atoms=$3, code=$4 )",
    ],
    50: [
        "$_gen9 = $terminal",
        "$_gen9 = :_empty",
    ],
    51: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    52: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    53: [
        "$expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    54: [
        "$_gen11 = $ll1_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    55: [
        "$macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    56: [
        "$_gen7 = $regex_options",
        "$_gen7 = :_empty",
    ],
    57: [
        "$_gen20 = :comma $ast_parameter $_gen20",
        "$_gen20 = :_empty",
    ],
    58: [
        "$_gen19 = $ast_parameter $_gen20",
        "$_gen19 = :_empty",
    ],
    59: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    60: [
        "$_gen12 = $rule $_gen13",
        "$_gen12 = :_empty",
    ],
    61: [
        "$_gen14 = $morpheme $_gen14",
        "$_gen14 = :_empty",
    ],
    62: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    63: [
        "$parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    64: [
        "$led = :expression_divider $_gen14 -> $1",
    ],
    65: [
        "$_gen3 = :code",
        "$_gen3 = :_empty",
    ],
    66: [
        "$_gen6 = $regex_partial $_gen6",
        "$_gen6 = :_empty",
    ],
    67: [
        "$_gen17 = $binding_power",
        "$_gen17 = :_empty",
    ],
    68: [
        "$_gen18 = $led",
        "$_gen18 = :_empty",
    ],
    69: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    70: [
        "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    ],
    71: [
        "$_gen2 = $lexer_atom $_gen2",
        "$_gen2 = :_empty",
    ],
    72: [
        "$rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )",
    ],
    73: [
        "$_gen22 = :comma $macro_parameter $_gen22",
        "$_gen22 = :_empty",
    ],
    74: [
        "$_gen21 = $macro_parameter $_gen22",
        "$_gen21 = :_empty",
    ],
    75: [
        "$lexer_regex = :regex $_gen7 :arrow $_gen8 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    76: [
        "$body_element = $body_element_sub",
    ],
    77: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    78: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
    ],
    79: [
        "$_gen10 = $match_group",
        "$_gen10 = :_empty",
    ],
    80: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    81: [
        "$_gen16 = $expression_rule $_gen16",
        "$_gen16 = :_empty",
    ],
    82: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    83: [
        "$nud = $_gen14",
    ],
    84: [
        "$parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )",
    ],
    85: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    86: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    87: [
        "$_gen8 = $lexer_target $_gen8",
        "$_gen8 = :_empty",
    ],
    88: [
        "$_gen13 = :pipe $rule $_gen13",
        "$_gen13 = :_empty",
    ],
    89: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    90: [
        "$_gen15 = $ast_transform",
        "$_gen15 = :_empty",
    ],
    91: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    92: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    93: [
        "$lexer_languages = :langle $_gen4 :rangle -> $1",
    ],
    94: [
        "$_gen1 = $lexer_languages",
        "$_gen1 = :_empty",
    ],
    95: [
        "$ll1_rule_rhs = $_gen12",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    96: [
        "$terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )",
    ],
    97: [
        "$_gen5 = :comma :identifier $_gen5",
        "$_gen5 = :_empty",
    ],
    98: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    99: [
        "$lexer_partials = :partials :lbrace $_gen6 :rbrace -> RegexPartials( list=$2 )",
    ],
}
rules = {
    0: "$_gen0 = $body_element $_gen0",
    1: "$_gen0 = :_empty",
    2: "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    3: "$body_element = $body_element_sub",
    4: "$body_element_sub = $lexer",
    5: "$body_element_sub = $parser",
    6: "$_gen1 = $lexer_languages",
    7: "$_gen1 = :_empty",
    8: "$_gen2 = $lexer_atom $_gen2",
    9: "$_gen2 = :_empty",
    10: "$_gen3 = :code",
    11: "$_gen3 = :_empty",
    12: "$lexer = :lexer $_gen1 :lbrace $_gen2 $_gen3 :rbrace -> Lexer( languages=$1, atoms=$3, code=$4 )",
    13: "$_gen4 = :identifier $_gen5",
    14: "$_gen5 = :comma :identifier $_gen5",
    15: "$_gen5 = :_empty",
    16: "$_gen4 = :_empty",
    17: "$lexer_languages = :langle $_gen4 :rangle -> $1",
    18: "$lexer_atom = $lexer_regex",
    19: "$lexer_atom = $lexer_mode",
    20: "$lexer_atom = $lexer_partials",
    21: "$_gen6 = $regex_partial $_gen6",
    22: "$_gen6 = :_empty",
    23: "$lexer_partials = :partials :lbrace $_gen6 :rbrace -> RegexPartials( list=$2 )",
    24: "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    25: "$_gen7 = $regex_options",
    26: "$_gen7 = :_empty",
    27: "$_gen8 = $lexer_target $_gen8",
    28: "$_gen8 = :_empty",
    29: "$lexer_regex = :regex $_gen7 :arrow $_gen8 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    30: "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    31: "$lexer_target = $terminal",
    32: "$_gen9 = $terminal",
    33: "$_gen9 = :_empty",
    34: "$lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    35: "$lexer_target = :stack_push",
    36: "$lexer_target = :action",
    37: "$_gen10 = $match_group",
    38: "$_gen10 = :_empty",
    39: "$terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )",
    40: "$match_group = :lsquare :integer :rsquare -> $1",
    41: "$match_group = :no_group",
    42: "$lexer_target = :null -> Null(  )",
    43: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen2 :rbrace -> Mode( name=$2, atoms=$5 )",
    44: "$parser = $parser_ll1",
    45: "$parser = $parser_expression",
    46: "$_gen11 = $ll1_rule $_gen11",
    47: "$_gen11 = :_empty",
    48: "$parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )",
    49: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    50: "$_gen12 = $rule $_gen13",
    51: "$_gen13 = :pipe $rule $_gen13",
    52: "$_gen13 = :_empty",
    53: "$_gen12 = :_empty",
    54: "$ll1_rule_rhs = $_gen12",
    55: "$_gen14 = $morpheme $_gen14",
    56: "$_gen14 = :_empty",
    57: "$_gen15 = $ast_transform",
    58: "$_gen15 = :_empty",
    59: "$rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )",
    60: "$ll1_rule_rhs = :null -> NullProduction(  )",
    61: "$ll1_rule_rhs = $parser",
    62: "$_gen16 = $expression_rule $_gen16",
    63: "$_gen16 = :_empty",
    64: "$parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )",
    65: "$_gen17 = $binding_power",
    66: "$_gen17 = :_empty",
    67: "$expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    68: "$_gen18 = $led",
    69: "$_gen18 = :_empty",
    70: "$expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    71: "$expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )",
    72: "$expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )",
    73: "$nud = $_gen14",
    74: "$led = :expression_divider $_gen14 -> $1",
    75: "$binding_power = :lparen $precedence :rparen -> $1",
    76: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    77: "$binding_power_marker = :asterisk",
    78: "$binding_power_marker = :dash",
    79: "$associativity = :left",
    80: "$associativity = :right",
    81: "$associativity = :unary",
    82: "$morpheme = :terminal",
    83: "$morpheme = :nonterminal",
    84: "$morpheme = $macro",
    85: "$ast_transform = :arrow $ast_transform_sub -> $1",
    86: "$_gen19 = $ast_parameter $_gen20",
    87: "$_gen20 = :comma $ast_parameter $_gen20",
    88: "$_gen20 = :_empty",
    89: "$_gen19 = :_empty",
    90: "$ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    91: "$ast_transform_sub = :nonterminal_reference",
    92: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    93: "$_gen21 = $macro_parameter $_gen22",
    94: "$_gen22 = :comma $macro_parameter $_gen22",
    95: "$_gen22 = :_empty",
    96: "$_gen21 = :_empty",
    97: "$macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )",
    98: "$macro_parameter = :nonterminal",
    99: "$macro_parameter = :terminal",
    100: "$macro_parameter = :string",
    101: "$macro_parameter = :integer",
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
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 82: # $morpheme = :terminal
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :terminal
        tree.add(t)
        return tree
    elif rule == 83: # $morpheme = :nonterminal
        ctx.rule = rules[83]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 84: # $morpheme = $macro
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[43]],
      rules[84]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 31: # $lexer_target = $terminal
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    elif rule == 34: # $lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[34]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        t = expect(ctx, 4) # :lparen
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        t = expect(ctx, 16) # :rparen
        tree.add(t)
        return tree
    elif rule == 35: # $lexer_target = :stack_push
        ctx.rule = rules[35]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 17) # :stack_push
        tree.add(t)
        return tree
    elif rule == 36: # $lexer_target = :action
        ctx.rule = rules[36]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :action
        tree.add(t)
        return tree
    elif rule == 42: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[42]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 41) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[44]],
      rules[42]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 90: # $ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[90]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        t = expect(ctx, 4) # :lparen
        tree.add(t)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        t = expect(ctx, 16) # :rparen
        tree.add(t)
        return tree
    elif rule == 91: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[91]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 21) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[45]],
      rules[91]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 43: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen2 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[43]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 28) # :mode
        tree.add(t)
        t = expect(ctx, 2) # :langle
        tree.add(t)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        t = expect(ctx, 34) # :rangle
        tree.add(t)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[43]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[47] and current.id not in nonterminal_first[47]:
        return tree
    if current == None:
        return tree
    if rule == 13: # $_gen4 = :identifier $_gen5
        ctx.rule = rules[13]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 49: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[49]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 11) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 1) # :nonterminal
        tree.add(t)
        t = expect(ctx, 25) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[49]
    ))
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'lexer'))
    ctx.nonterminal = "lexer"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 12: # $lexer = :lexer $_gen1 :lbrace $_gen2 $_gen3 :rbrace -> Lexer( languages=$1, atoms=$3, code=$4 )
        ctx.rule = rules[12]
        ast_parameters = OrderedDict([
            ('languages', 1),
            ('atoms', 3),
            ('code', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 0) # :lexer
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49]],
      rules[12]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = False
    if current != None and current.id in nonterminal_follow[50] and current.id not in nonterminal_first[50]:
        return tree
    if current == None:
        return tree
    if rule == 32: # $_gen9 = $terminal
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 98: # $macro_parameter = :nonterminal
        ctx.rule = rules[98]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 99: # $macro_parameter = :terminal
        ctx.rule = rules[99]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :terminal
        tree.add(t)
        return tree
    elif rule == 100: # $macro_parameter = :string
        ctx.rule = rules[100]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 22) # :string
        tree.add(t)
        return tree
    elif rule == 101: # $macro_parameter = :integer
        ctx.rule = rules[101]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 8) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[51]],
      rules[101]
    ))
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'grammar'))
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
        t = expect(ctx, 24) # :grammar
        tree.add(t)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[2]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 67: # $expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[67]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 1) # :nonterminal
        tree.add(t)
        t = expect(ctx, 25) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[67]
    ))
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
        return tree
    if current == None:
        return tree
    if rule == 46: # $_gen11 = $ll1_rule $_gen11
        ctx.rule = rules[46]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 97: # $macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[97]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        t = expect(ctx, 4) # :lparen
        tree.add(t)
        subtree = parse__gen21(ctx)
        tree.add(subtree)
        t = expect(ctx, 16) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[97]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 25: # $_gen7 = $regex_options
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen20(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, '_gen20'))
    ctx.nonterminal = "_gen20"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[57] and current.id not in nonterminal_first[57]:
        return tree
    if current == None:
        return tree
    if rule == 87: # $_gen20 = :comma $ast_parameter $_gen20
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 37) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[58] and current.id not in nonterminal_first[58]:
        return tree
    if current == None:
        return tree
    if rule == 86: # $_gen19 = $ast_parameter $_gen20
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 77: # $binding_power_marker = :asterisk
        ctx.rule = rules[77]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 7) # :asterisk
        tree.add(t)
        return tree
    elif rule == 78: # $binding_power_marker = :dash
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 42) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59]],
      rules[78]
    ))
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[60] and current.id not in nonterminal_first[60]:
        return tree
    if current == None:
        return tree
    if rule == 50: # $_gen12 = $rule $_gen13
        ctx.rule = rules[50]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
        return tree
    if current == None:
        return tree
    if rule == 55: # $_gen14 = $morpheme $_gen14
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 85: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[85]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 31) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[62]],
      rules[85]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 64: # $parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[64]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 6) # :parser_expression
        tree.add(t)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[63]],
      rules[64]
    ))
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 74: # $led = :expression_divider $_gen14 -> $1
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 27) # :expression_divider
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[64]],
      rules[74]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = False
    if current != None and current.id in nonterminal_follow[65] and current.id not in nonterminal_first[65]:
        return tree
    if current == None:
        return tree
    if rule == 10: # $_gen3 = :code
        ctx.rule = rules[10]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :code
        tree.add(t)
        return tree
    return tree
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
        return tree
    if current == None:
        return tree
    if rule == 21: # $_gen6 = $regex_partial $_gen6
        ctx.rule = rules[21]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_partial(ctx)
        tree.add(subtree)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = False
    if current != None and current.id in nonterminal_follow[67] and current.id not in nonterminal_first[67]:
        return tree
    if current == None:
        return tree
    if rule == 65: # $_gen17 = $binding_power
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = False
    if current != None and current.id in nonterminal_follow[68] and current.id not in nonterminal_first[68]:
        return tree
    if current == None:
        return tree
    if rule == 68: # $_gen18 = $led
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 76: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[76]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 32) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[69]],
      rules[76]
    ))
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 30: # $regex_options = :lbrace $_gen4 :rbrace -> $1
        ctx.rule = rules[30]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[30]
    ))
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[71] and current.id not in nonterminal_first[71]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = $lexer_atom $_gen2
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_atom(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 59: # $rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[59]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[72]],
      rules[59]
    ))
def parse__gen22(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen22'))
    ctx.nonterminal = "_gen22"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
        return tree
    if current == None:
        return tree
    if rule == 94: # $_gen22 = :comma $macro_parameter $_gen22
        ctx.rule = rules[94]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 37) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen22(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen21(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, '_gen21'))
    ctx.nonterminal = "_gen21"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[74] and current.id not in nonterminal_first[74]:
        return tree
    if current == None:
        return tree
    if rule == 93: # $_gen21 = $macro_parameter $_gen22
        ctx.rule = rules[93]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen22(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $lexer_regex = :regex $_gen7 :arrow $_gen8 -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 39) # :regex
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 31) # :arrow
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75]],
      rules[29]
    ))
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[76]],
      rules[3]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 70: # $expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[70]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 5) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    elif rule == 71: # $expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[71]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 36) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    elif rule == 72: # $expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[72]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 23) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[72]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 18: # $lexer_atom = $lexer_regex
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 19: # $lexer_atom = $lexer_mode
        ctx.rule = rules[19]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_mode(ctx)
        tree.add(subtree)
        return tree
    elif rule == 20: # $lexer_atom = $lexer_partials
        ctx.rule = rules[20]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_partials(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[20]
    ))
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[79] and current.id not in nonterminal_first[79]:
        return tree
    if current == None:
        return tree
    if rule == 37: # $_gen10 = $match_group
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_match_group(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $associativity = :left
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :left
        tree.add(t)
        return tree
    elif rule == 80: # $associativity = :right
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 12) # :right
        tree.add(t)
        return tree
    elif rule == 81: # $associativity = :unary
        ctx.rule = rules[81]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 14) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[80]],
      rules[81]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[81] and current.id not in nonterminal_first[81]:
        return tree
    if current == None:
        return tree
    if rule == 62: # $_gen16 = $expression_rule $_gen16
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 44: # $parser = $parser_ll1
        ctx.rule = rules[44]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 45: # $parser = $parser_expression
        ctx.rule = rules[45]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[82]],
      rules[45]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 73: # $nud = $_gen14
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[83]],
      rules[73]
    ))
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 48: # $parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[48]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 10) # :parser
        tree.add(t)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84]],
      rules[48]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[85] and current.id not in nonterminal_first[85]:
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
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[86]],
      rules[5]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[87] and current.id not in nonterminal_first[87]:
        return tree
    if current == None:
        return tree
    if rule == 27: # $_gen8 = $lexer_target $_gen8
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[88] and current.id not in nonterminal_first[88]:
        return tree
    if current == None:
        return tree
    if rule == 51: # $_gen13 = :pipe $rule $_gen13
        ctx.rule = rules[51]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 20) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
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
    if rule == 24: # $regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )
        ctx.rule = rules[24]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('name', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartial', ast_parameters)
        t = expect(ctx, 39) # :regex
        tree.add(t)
        t = expect(ctx, 31) # :arrow
        tree.add(t)
        t = expect(ctx, 35) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[89]],
      rules[24]
    ))
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = False
    if current != None and current.id in nonterminal_follow[90] and current.id not in nonterminal_first[90]:
        return tree
    if current == None:
        return tree
    if rule == 57: # $_gen15 = $ast_transform
        ctx.rule = rules[57]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 75: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 4) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 16) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[91]],
      rules[75]
    ))
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[40]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 30) # :lsquare
        tree.add(t)
        t = expect(ctx, 8) # :integer
        tree.add(t)
        t = expect(ctx, 40) # :rsquare
        tree.add(t)
        return tree
    elif rule == 41: # $match_group = :no_group
        ctx.rule = rules[41]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 19) # :no_group
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92]],
      rules[41]
    ))
def parse_lexer_languages(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, 'lexer_languages'))
    ctx.nonterminal = "lexer_languages"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 17: # $lexer_languages = :langle $_gen4 :rangle -> $1
        ctx.rule = rules[17]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 2) # :langle
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 34) # :rangle
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[93]],
      rules[17]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = False
    if current != None and current.id in nonterminal_follow[94] and current.id not in nonterminal_first[94]:
        return tree
    if current == None:
        return tree
    if rule == 6: # $_gen1 = $lexer_languages
        ctx.rule = rules[6]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_languages(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(95, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 54: # $ll1_rule_rhs = $_gen12
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    elif rule == 60: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[60]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 41) # :null
        tree.add(t)
        return tree
    elif rule == 61: # $ll1_rule_rhs = $parser
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[95]],
      rules[61]
    ))
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(96, 'terminal'))
    ctx.nonterminal = "terminal"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 39: # $terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[39]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 18) # :terminal
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[96]],
      rules[39]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[54][current.id] if current else -1
    tree = ParseTree(NonTerminal(97, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[97] and current.id not in nonterminal_first[97]:
        return tree
    if current == None:
        return tree
    if rule == 14: # $_gen5 = :comma :identifier $_gen5
        ctx.rule = rules[14]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 37) # :comma
        tree.add(t)
        tree.listSeparator = t
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[55][current.id] if current else -1
    tree = ParseTree(NonTerminal(98, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 92: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[92]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 15) # :identifier
        tree.add(t)
        t = expect(ctx, 25) # :equals
        tree.add(t)
        t = expect(ctx, 21) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[98]],
      rules[92]
    ))
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[56][current.id] if current else -1
    tree = ParseTree(NonTerminal(99, 'lexer_partials'))
    ctx.nonterminal = "lexer_partials"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 23: # $lexer_partials = :partials :lbrace $_gen6 :rbrace -> RegexPartials( list=$2 )
        ctx.rule = rules[23]
        ast_parameters = OrderedDict([
            ('list', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartials', ast_parameters)
        t = expect(ctx, 9) # :partials
        tree.add(t)
        t = expect(ctx, 3) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 38) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[99]],
      rules[23]
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
          (re.compile(r'lexer'), [
              # (terminal, group, function)
              ('lexer', 0, None),
              LexerStackPush('lexer'),
          ]),
          (re.compile(r'parser'), [
              # (terminal, group, function)
              ('parser', 0, None),
              LexerStackPush('parser'),
          ]),
        ]),
        'lexer': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), [
              # (terminal, group, function)
              ('code', 1, None),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
              LexerAction('pop'),
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
          ]),
          (re.compile(r'<'), [
              # (terminal, group, function)
              ('langle', 0, None),
          ]),
          (re.compile(r'>'), [
              # (terminal, group, function)
              ('rangle', 0, None),
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
              LexerStackPush('regex_options'),
          ]),
          (re.compile(r'"(\\\"|[^\"])*"'), [
              # (terminal, group, function)
              ('regex', 0, None),
              LexerStackPush('regex_options'),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
          ]),
          (re.compile(r','), [
              # (terminal, group, function)
              ('comma', 0, None),
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
          (re.compile(r'_[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('regex_partial', 0, None),
          ]),
          (re.compile(r'null'), [
              # (terminal, group, function)
              ('null', 0, None),
          ]),
          (re.compile(r'mode'), [
              # (terminal, group, function)
              ('mode', 0, None),
              LexerStackPush('lexer'),
          ]),
          (re.compile(r'partials'), [
              # (terminal, group, function)
              ('partials', 0, None),
              LexerStackPush('lexer'),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
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
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
          ]),
          (re.compile(r'}'), [
              # (terminal, group, function)
              ('rbrace', 0, None),
          ]),
          (re.compile(r'->'), [
              # (terminal, group, function)
              ('arrow', 0, None),
              LexerAction('pop'),
          ]),
        ]),
        'parser': OrderedDict([
          (re.compile(r'\s+'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'\#.*'), [
              # (terminal, group, function)
          ]),
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
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
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
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
                from xtermcolor import colorize
                token_count = len(ctx.tokens)
                print('{1} ({2}, {3}) regex: {0}'.format(
                    colorize(regex.pattern, ansi=40), colorize(ctx.string[:20].replace('\n', '\\n'), ansi=15), ctx.line, ctx.col)
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
                            print('    matched: {}'.format(colorize(match.group(0).replace('\n', '\\n'), ansi=3)))
                            for token in ctx.tokens[token_count:]:
                                print('    emit: [{}] [{}, {}] [{}] stack:{} context:{}'.format(
                                    colorize(token.str, ansi=9),
                                    colorize(str(token.line), ansi=5),
                                    colorize(str(token.col), ansi=5),
                                    colorize(token.source_string, ansi=3),
                                    colorize(str(ctx.stack), ansi=4),
                                    colorize(str(ctx.user_context), ansi=13)
                                ))
                            token_count = len(ctx.tokens)
                    if isinstance(output, LexerStackPush):
                        ctx.stack.append(output.mode)
                        if debug:
                            print('    push on stack: {}'.format(colorize(output.mode, ansi=4)))
                    if isinstance(output, LexerAction):
                        if output.action == 'pop':
                            mode = ctx.stack.pop()
                            if debug:
                                print('    pop off stack: {}'.format(colorize(mode, ansi=4)))
                self._advance_string(ctx, match.group(0))
                return len(match.group(0)) > 0
        return False
    def lex(self, string, resource, debug=False):
        string_copy = string
        user_context = init()
        ctx = LexerContext(string, resource, user_context)
        while len(ctx.string):
            matched = self._next(ctx, debug)
            if matched == False:
                self._unrecognized_token(string_copy, ctx.line, ctx.col)
        destroy(ctx.user_context)
        return ctx.tokens
def lex(source, resource, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, debug))
