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
  def ast(self):
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
  def ast(self):
      retval = []
      for ast in self:
          retval.append(ast.ast())
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
  def ast( self ):
      if self.list == 'slist' or self.list == 'nlist':
          if len(self.children) == 0:
              return AstList()
          offset = 1 if self.children[0] == self.listSeparator else 0
          first = self.children[offset].ast()
          r = AstList()
          if first is not None:
              r.append(first)
          r.extend(self.children[offset+1].ast())
          return r
      elif self.list == 'otlist':
          if len(self.children) == 0:
              return AstList()
          r = AstList()
          if self.children[0] != self.listSeparator:
              r.append(self.children[0].ast())
          r.extend(self.children[1].ast())
          return r
      elif self.list == 'tlist':
          if len(self.children) == 0:
              return AstList()
          r = AstList([self.children[0].ast()])
          r.extend(self.children[2].ast())
          return r
      elif self.list == 'mlist':
          r = AstList()
          if len(self.children) == 0:
              return r
          lastElement = len(self.children) - 1
          for i in range(lastElement):
              r.append(self.children[i].ast())
          r.extend(self.children[lastElement].ast())
          return r
      elif self.isExpr:
          if isinstance(self.astTransform, AstTransformSubstitution):
              return self.children[self.astTransform.idx].ast()
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
                  parameters[name] = child.ast()
              return Ast(self.astTransform.name, parameters)
      else:
          if isinstance(self.astTransform, AstTransformSubstitution):
              return self.children[self.astTransform.idx].ast()
          elif isinstance(self.astTransform, AstTransformNodeCreator):
              parameters = OrderedDict()
              for name, idx in self.astTransform.parameters.items():
                  parameters[name] = self.children[idx].ast()
              return Ast(self.astTransform.name, parameters)
          elif len(self.children):
              return self.children[0].ast()
          else:
              return None
  def dumps(self, indent=None, b64_source=True):
      args = locals()
      del args['self']
      return parse_tree_string(self, **args)
class Ast():
    def __init__(self, name, attributes):
        self.__dict__.update(locals())
    def attr(self, attr):
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
class DefaultSyntaxErrorHandler:
    def __init__(self):
        self.errors = []
    def _error(self, string):
        error = SyntaxError(string)
        self.errors.append(error)
        return error
    def unexpected_eof(self):
        return self._error("Error: unexpected end of file")
    def excess_tokens(self):
        return self._error("Finished parsing without consuming all tokens.")
    def unexpected_symbol(self, nonterminal, actual_terminal, expected_terminals, rule):
        return self._error("Unexpected symbol (line {line}, col {col}) when parsing parse_{nt}.  Expected {expected}, got {actual}.".format(
            line=actual_terminal.line,
            col=actual_terminal.col,
            nt=nonterminal,
            expected=', '.join(expected_terminals),
            actual=actual_terminal
        ))
    def no_more_tokens(self, nonterminal, expected_terminal, last_terminal):
        return self._error("No more tokens.  Expecting " + expected_terminal)
    def invalid_terminal(self, nonterminal, invalid_terminal):
        return self._error("Invalid symbol ID: {} ({})".format(invalid_terminal.id, invalid_terminal.string))
    def unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        return self._error('Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        ))
class ParserContext:
  def __init__(self, tokens, errors):
    self.__dict__.update(locals())
    self.nonterminal_string = None
    self.rule_string = None
# Parser Code #
terminals = {
    0: 'unary',
    1: 'code',
    2: 'colon',
    3: 'grammar',
    4: 'arrow',
    5: 'pipe',
    6: 'lparen',
    7: 'nonterminal_reference',
    8: 'langle',
    9: 'terminal',
    10: 'rparen',
    11: 'left',
    12: 'lexer',
    13: 'null',
    14: 'parser_expression',
    15: 'prefix_rule_hint',
    16: 'asterisk',
    17: 'rbrace',
    18: 'regex',
    19: 'mode',
    20: 'nonterminal',
    21: 'equals',
    22: 'lsquare',
    23: 'rsquare',
    24: 'regex_enum',
    25: 'identifier',
    26: 'regex_partial',
    27: 'right',
    28: 'no_group',
    29: 'expression_divider',
    30: 'expr_rule_hint',
    31: 'lbrace',
    32: 'code_start',
    33: 'rangle',
    34: 'parser',
    35: 'mixfix_rule_hint',
    36: 'string',
    37: 'comma',
    38: 'dash',
    39: 'stack_push',
    40: 'language',
    41: 'infix_rule_hint',
    42: 'action',
    43: 'integer',
    44: 'll1_rule_hint',
    45: 'partials',
    'unary': 0,
    'code': 1,
    'colon': 2,
    'grammar': 3,
    'arrow': 4,
    'pipe': 5,
    'lparen': 6,
    'nonterminal_reference': 7,
    'langle': 8,
    'terminal': 9,
    'rparen': 10,
    'left': 11,
    'lexer': 12,
    'null': 13,
    'parser_expression': 14,
    'prefix_rule_hint': 15,
    'asterisk': 16,
    'rbrace': 17,
    'regex': 18,
    'mode': 19,
    'nonterminal': 20,
    'equals': 21,
    'lsquare': 22,
    'rsquare': 23,
    'regex_enum': 24,
    'identifier': 25,
    'regex_partial': 26,
    'right': 27,
    'no_group': 28,
    'expression_divider': 29,
    'expr_rule_hint': 30,
    'lbrace': 31,
    'code_start': 32,
    'rangle': 33,
    'parser': 34,
    'mixfix_rule_hint': 35,
    'string': 36,
    'comma': 37,
    'dash': 38,
    'stack_push': 39,
    'language': 40,
    'infix_rule_hint': 41,
    'action': 42,
    'integer': 43,
    'll1_rule_hint': 44,
    'partials': 45,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, 41, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 104, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 103, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 105, -1, -1, -1, -1, -1, -1, 106, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 37, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 43, 43, -1, -1, 43, -1, -1, -1, 43, 43, 43, -1, -1, 42, -1, 43, 43, -1, -1, 42, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, 43, -1, -1, 43, -1, -1, 43],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, 0, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 96, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 95, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 59, 59, -1, -1, -1, 59, -1, -1, -1, 65, 66, -1, -1, 59, -1, -1, 59, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1],
    [-1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 75, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1],
    [-1, -1, -1, -1, 78, -1, 78, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, 78, -1, -1, -1, -1, 78, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 74, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 100, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 99, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, 10, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1],
    [-1, -1, -1, -1, 55, 55, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, 55, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, 21, -1, -1, -1, 22, 22, 22, -1, -1, -1, -1, 22, 21, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, 21, -1, -1, 21, -1, -1, 22],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 62, 63, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1],
    [-1, -1, -1, -1, 61, 61, 61, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, 60, -1, -1, -1, -1, 60, -1, -1, -1, -1, 61, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, 6, 6, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6],
    [-1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 98, 101, -1, -1, -1, -1, -1, -1, -1, -1, -1, 98, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 98, -1, -1, -1, -1, -1, -1, 98, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 64, 64, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, 64, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 92, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, -1, -1, -1, -1, 89, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 94, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 90, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 102, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    46: [34],
    47: [25, 13, 39, 9, 42],
    48: [38, 16],
    49: [31],
    50: [20, 9, 36, 43],
    51: [-1, 9],
    52: [-1, 25],
    53: [19],
    54: [-1, 28, 22],
    55: [-1, 12, 34, 14],
    56: [25, 7],
    57: [25, -1],
    58: [34, 13, 14, 25, 4, 5, 20, -1, 9],
    59: [5, -1],
    60: [14],
    61: [-1, 18],
    62: [15, 41, 35],
    63: [25, 20, -1, 9],
    64: [-1, 29],
    65: [38, 16],
    66: [-1, 37],
    67: [19, 32, 24, 18, 45],
    68: [24],
    69: [45],
    70: [44],
    71: [25, 5, 20, -1, 9, 4],
    72: [25, 13, 39, 42, -1, 9],
    73: [24, 18],
    74: [12, 34, 14],
    75: [29],
    76: [-1, 4],
    77: [25, 20, -1, 9],
    78: [32],
    79: [18, 19, -1, 32, 24, 45],
    80: [6],
    81: [25],
    82: [-1, 20, 9, 36, 43],
    83: [9],
    84: [0, 27, 11],
    85: [25, 20, -1, 9, 4],
    86: [18],
    87: [34, 14],
    88: [3],
    89: [-1, 31],
    90: [25],
    91: [-1, 6],
    92: [6],
    93: [28, 22],
    94: [30, 6],
    95: [12, 34, 14],
    96: [-1, 44],
    97: [-1, 37],
    98: [-1, 37],
    99: [25, 20, 9],
    100: [-1, 25],
    101: [-1, 6],
    102: [12],
    103: [-1, 30, 6],
    104: [4],
    105: [25],
}
nonterminal_follow = {
    46: [12, 34, 14, 17, 44],
    47: [25, 13, 17, 39, 18, 19, 42, 32, 9, 24, 45],
    48: [2],
    49: [4],
    50: [10, 37],
    51: [10],
    52: [17],
    53: [17, 18, 19, 32, 24, 45],
    54: [25, 32, 9, 10, 13, 17, 39, 18, 19, 42, 24, 45],
    55: [17],
    56: [17, 29, 5, 30, 6, 44],
    57: [10, 17],
    58: [44, 17],
    59: [44, 17],
    60: [12, 34, 14, 17, 44],
    61: [17],
    62: [30, 6, 17],
    63: [30, 6, 17, 4],
    64: [30, 6, 17, 4],
    65: [10],
    66: [10],
    67: [19, 17, 32, 24, 18, 45],
    68: [17, 18, 19, 32, 24, 45],
    69: [17, 18, 19, 32, 24, 45],
    70: [44, 17],
    71: [44, 17],
    72: [17, 18, 19, 32, 24, 45],
    73: [17, 18, 19, 32, 24, 45],
    74: [12, 34, 14, 17],
    75: [30, 6, 17, 4],
    76: [17, 29, 5, 30, 6, 44],
    77: [17, 4, 5, 30, 6, 44],
    78: [17, 18, 19, 32, 24, 45],
    79: [17],
    80: [30],
    81: [10, 37],
    82: [10],
    83: [25, 32, 9, 10, 13, 17, 39, 18, 19, 42, 24, 45],
    84: [10],
    85: [5, 44, 17],
    86: [17, 18],
    87: [12, 34, 14, 17, 44],
    88: [-1],
    89: [4],
    90: [25, 17],
    91: [25, 17],
    92: [25, 17],
    93: [25, 32, 9, 10, 13, 17, 39, 18, 19, 42, 24, 45],
    94: [30, 6, 17],
    95: [12, 34, 14, 17],
    96: [17],
    97: [10],
    98: [10, 17],
    99: [25, 17, 4, 5, 20, 30, 6, 44, 9],
    100: [10],
    101: [30],
    102: [12, 34, 14, 17],
    103: [17],
    104: [17, 29, 5, 30, 6, 44],
    105: [25, 4, 5, 30, 6, 9, 17, 20, 44],
}
rule_first = {
    0: [12, 34, 14],
    1: [-1],
    2: [3],
    3: [12, 34, 14],
    4: [12],
    5: [34, 14],
    6: [19, 32, 24, 18, 45],
    7: [-1],
    8: [12],
    9: [24, 18],
    10: [19],
    11: [45],
    12: [32],
    13: [32],
    14: [18],
    15: [-1],
    16: [45],
    17: [18],
    18: [24],
    19: [31],
    20: [-1],
    21: [25, 13, 39, 9, 42],
    22: [-1],
    23: [18],
    24: [25],
    25: [-1],
    26: [24],
    27: [6],
    28: [-1],
    29: [25],
    30: [25],
    31: [37],
    32: [-1],
    33: [-1],
    34: [6],
    35: [31],
    36: [9],
    37: [9],
    38: [-1],
    39: [25],
    40: [39],
    41: [42],
    42: [28, 22],
    43: [-1],
    44: [9],
    45: [22],
    46: [28],
    47: [13],
    48: [19],
    49: [34],
    50: [14],
    51: [44],
    52: [-1],
    53: [34],
    54: [44],
    55: [25, 4, 5, 20, -1, 9],
    56: [5],
    57: [-1],
    58: [-1],
    59: [25, 4, 5, 20, -1, 9],
    60: [25, 20, 9],
    61: [-1],
    62: [4],
    63: [-1],
    64: [25, 20, -1, 9, 4],
    65: [13],
    66: [34, 14],
    67: [30, 6],
    68: [-1],
    69: [14],
    70: [6],
    71: [-1],
    72: [6, 30],
    73: [29],
    74: [-1],
    75: [35],
    76: [15],
    77: [41],
    78: [25, 20, -1, 9],
    79: [29],
    80: [6],
    81: [38, 16],
    82: [16],
    83: [38],
    84: [11],
    85: [27],
    86: [0],
    87: [9],
    88: [20],
    89: [25],
    90: [4],
    91: [25],
    92: [37],
    93: [-1],
    94: [-1],
    95: [25],
    96: [7],
    97: [25],
    98: [20, 9, 36, 43],
    99: [37],
    100: [-1],
    101: [-1],
    102: [25],
    103: [20],
    104: [9],
    105: [36],
    106: [43],
}
nonterminal_rules = {
    46: [
        "$parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )",
    ],
    47: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :stack_push",
        "$lexer_target = :action",
        "$lexer_target = :null -> Null(  )",
    ],
    48: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    49: [
        "$regex_options = :lbrace $_gen7 :rbrace -> $1",
    ],
    50: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    51: [
        "$_gen9 = $terminal",
        "$_gen9 = :_empty",
    ],
    52: [
        "$_gen5 = $regex_enumeration $_gen5",
        "$_gen5 = :_empty",
    ],
    53: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    54: [
        "$_gen10 = $match_group",
        "$_gen10 = :_empty",
    ],
    55: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    56: [
        "$ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    57: [
        "$_gen7 = :identifier $_gen8",
        "$_gen7 = :_empty",
    ],
    58: [
        "$ll1_rule_rhs = $_gen12",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    59: [
        "$_gen13 = :pipe $rule $_gen13",
        "$_gen13 = :_empty",
    ],
    60: [
        "$parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    61: [
        "$_gen2 = $regex_partial $_gen2",
        "$_gen2 = :_empty",
    ],
    62: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    63: [
        "$nud = $_gen14",
    ],
    64: [
        "$_gen18 = $led",
        "$_gen18 = :_empty",
    ],
    65: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    66: [
        "$_gen22 = :comma $macro_parameter $_gen22",
        "$_gen22 = :_empty",
    ],
    67: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
        "$lexer_atom = $lexer_code",
    ],
    68: [
        "$enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )",
    ],
    69: [
        "$lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )",
    ],
    70: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    71: [
        "$_gen12 = $rule $_gen13",
        "$_gen12 = :_empty",
    ],
    72: [
        "$_gen4 = $lexer_target $_gen4",
        "$_gen4 = :_empty",
    ],
    73: [
        "$lexer_regex = $enumerated_regex",
        "$lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    74: [
        "$body_element = $body_element_sub",
    ],
    75: [
        "$led = :expression_divider $_gen14 -> $1",
    ],
    76: [
        "$_gen15 = $ast_transform",
        "$_gen15 = :_empty",
    ],
    77: [
        "$_gen14 = $morpheme $_gen14",
        "$_gen14 = :_empty",
    ],
    78: [
        "$lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )",
    ],
    79: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    80: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    81: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    82: [
        "$_gen21 = $macro_parameter $_gen22",
        "$_gen21 = :_empty",
    ],
    83: [
        "$terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )",
    ],
    84: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    85: [
        "$rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )",
    ],
    86: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    87: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    88: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    89: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    90: [
        "$regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )",
    ],
    91: [
        "$_gen6 = $regex_enumeration_options",
        "$_gen6 = :_empty",
    ],
    92: [
        "$regex_enumeration_options = :lparen $_gen7 :rparen -> $1",
    ],
    93: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    94: [
        "$expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    95: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    96: [
        "$_gen11 = $ll1_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    97: [
        "$_gen20 = :comma $ast_parameter $_gen20",
        "$_gen20 = :_empty",
    ],
    98: [
        "$_gen8 = :comma :identifier $_gen8",
        "$_gen8 = :_empty",
    ],
    99: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    100: [
        "$_gen19 = $ast_parameter $_gen20",
        "$_gen19 = :_empty",
    ],
    101: [
        "$_gen17 = $binding_power",
        "$_gen17 = :_empty",
    ],
    102: [
        "$lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )",
    ],
    103: [
        "$_gen16 = $expression_rule $_gen16",
        "$_gen16 = :_empty",
    ],
    104: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    105: [
        "$macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )",
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
    8: "$lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )",
    9: "$lexer_atom = $lexer_regex",
    10: "$lexer_atom = $lexer_mode",
    11: "$lexer_atom = $lexer_partials",
    12: "$lexer_atom = $lexer_code",
    13: "$lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )",
    14: "$_gen2 = $regex_partial $_gen2",
    15: "$_gen2 = :_empty",
    16: "$lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )",
    17: "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    18: "$lexer_regex = $enumerated_regex",
    19: "$_gen3 = $regex_options",
    20: "$_gen3 = :_empty",
    21: "$_gen4 = $lexer_target $_gen4",
    22: "$_gen4 = :_empty",
    23: "$lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    24: "$_gen5 = $regex_enumeration $_gen5",
    25: "$_gen5 = :_empty",
    26: "$enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )",
    27: "$_gen6 = $regex_enumeration_options",
    28: "$_gen6 = :_empty",
    29: "$regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )",
    30: "$_gen7 = :identifier $_gen8",
    31: "$_gen8 = :comma :identifier $_gen8",
    32: "$_gen8 = :_empty",
    33: "$_gen7 = :_empty",
    34: "$regex_enumeration_options = :lparen $_gen7 :rparen -> $1",
    35: "$regex_options = :lbrace $_gen7 :rbrace -> $1",
    36: "$lexer_target = $terminal",
    37: "$_gen9 = $terminal",
    38: "$_gen9 = :_empty",
    39: "$lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    40: "$lexer_target = :stack_push",
    41: "$lexer_target = :action",
    42: "$_gen10 = $match_group",
    43: "$_gen10 = :_empty",
    44: "$terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )",
    45: "$match_group = :lsquare :integer :rsquare -> $1",
    46: "$match_group = :no_group",
    47: "$lexer_target = :null -> Null(  )",
    48: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    49: "$parser = $parser_ll1",
    50: "$parser = $parser_expression",
    51: "$_gen11 = $ll1_rule $_gen11",
    52: "$_gen11 = :_empty",
    53: "$parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )",
    54: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    55: "$_gen12 = $rule $_gen13",
    56: "$_gen13 = :pipe $rule $_gen13",
    57: "$_gen13 = :_empty",
    58: "$_gen12 = :_empty",
    59: "$ll1_rule_rhs = $_gen12",
    60: "$_gen14 = $morpheme $_gen14",
    61: "$_gen14 = :_empty",
    62: "$_gen15 = $ast_transform",
    63: "$_gen15 = :_empty",
    64: "$rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )",
    65: "$ll1_rule_rhs = :null -> NullProduction(  )",
    66: "$ll1_rule_rhs = $parser",
    67: "$_gen16 = $expression_rule $_gen16",
    68: "$_gen16 = :_empty",
    69: "$parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )",
    70: "$_gen17 = $binding_power",
    71: "$_gen17 = :_empty",
    72: "$expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    73: "$_gen18 = $led",
    74: "$_gen18 = :_empty",
    75: "$expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    76: "$expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )",
    77: "$expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )",
    78: "$nud = $_gen14",
    79: "$led = :expression_divider $_gen14 -> $1",
    80: "$binding_power = :lparen $precedence :rparen -> $1",
    81: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    82: "$binding_power_marker = :asterisk",
    83: "$binding_power_marker = :dash",
    84: "$associativity = :left",
    85: "$associativity = :right",
    86: "$associativity = :unary",
    87: "$morpheme = :terminal",
    88: "$morpheme = :nonterminal",
    89: "$morpheme = $macro",
    90: "$ast_transform = :arrow $ast_transform_sub -> $1",
    91: "$_gen19 = $ast_parameter $_gen20",
    92: "$_gen20 = :comma $ast_parameter $_gen20",
    93: "$_gen20 = :_empty",
    94: "$_gen19 = :_empty",
    95: "$ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    96: "$ast_transform_sub = :nonterminal_reference",
    97: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    98: "$_gen21 = $macro_parameter $_gen22",
    99: "$_gen22 = :comma $macro_parameter $_gen22",
    100: "$_gen22 = :_empty",
    101: "$_gen21 = :_empty",
    102: "$macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )",
    103: "$macro_parameter = :nonterminal",
    104: "$macro_parameter = :terminal",
    105: "$macro_parameter = :string",
    106: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 45
def parse(tokens, errors=None, start=None):
    if errors is None:
        errors = DefaultSyntaxErrorHandler()
    if isinstance(tokens, str):
        tokens = lex(tokens, '<string>', errors)
    ctx = ParserContext(tokens, errors)
    tree = parse_grammar(ctx)
    if tokens.current() != None:
        raise ctx.errors.excess_tokens()
    return tree
def expect(ctx, terminal_id):
    current = ctx.tokens.current()
    if not current:
        raise ctx.errors.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last())
    if current.id != terminal_id:
        raise ctx.errors.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule)
    next = ctx.tokens.advance()
    if next and not is_terminal(next.id):
        raise ctx.errors.invalid_terminal(ctx.nonterminal, next)
    return current
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 53: # $parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 34) # :parser
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46] if x >=0],
      rules[53]
    )
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 36: # $lexer_target = $terminal
        ctx.rule = rules[36]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    elif rule == 39: # $lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[39]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :lparen
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    elif rule == 40: # $lexer_target = :stack_push
        ctx.rule = rules[40]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 39) # :stack_push
        tree.add(t)
        return tree
    elif rule == 41: # $lexer_target = :action
        ctx.rule = rules[41]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 42) # :action
        tree.add(t)
        return tree
    elif rule == 47: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[47]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 13) # :null
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[47] if x >=0],
      rules[47]
    )
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 82: # $binding_power_marker = :asterisk
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :asterisk
        tree.add(t)
        return tree
    elif rule == 83: # $binding_power_marker = :dash
        ctx.rule = rules[83]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 38) # :dash
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48] if x >=0],
      rules[83]
    )
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 35: # $regex_options = :lbrace $_gen7 :rbrace -> $1
        ctx.rule = rules[35]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49] if x >=0],
      rules[35]
    )
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 103: # $macro_parameter = :nonterminal
        ctx.rule = rules[103]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 20) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 104: # $macro_parameter = :terminal
        ctx.rule = rules[104]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 9) # :terminal
        tree.add(t)
        return tree
    elif rule == 105: # $macro_parameter = :string
        ctx.rule = rules[105]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 36) # :string
        tree.add(t)
        return tree
    elif rule == 106: # $macro_parameter = :integer
        ctx.rule = rules[106]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 43) # :integer
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50] if x >=0],
      rules[106]
    )
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = False
    if current != None and current.id in nonterminal_follow[51] and current.id not in nonterminal_first[51]:
        return tree
    if current == None:
        return tree
    if rule == 37: # $_gen9 = $terminal
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_terminal(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[52] and current.id not in nonterminal_first[52]:
        return tree
    if current == None:
        return tree
    if rule == 24: # $_gen5 = $regex_enumeration $_gen5
        ctx.rule = rules[24]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_enumeration(ctx)
        tree.add(subtree)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 48: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[48]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 19) # :mode
        tree.add(t)
        t = expect(ctx, 8) # :langle
        tree.add(t)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 33) # :rangle
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53] if x >=0],
      rules[48]
    )
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
        return tree
    if current == None:
        return tree
    if rule == 42: # $_gen10 = $match_group
        ctx.rule = rules[42]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_match_group(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[55] and current.id not in nonterminal_first[55]:
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
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 95: # $ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[95]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :lparen
        tree.add(t)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    elif rule == 96: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[96]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 7) # :nonterminal_reference
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[56] if x >=0],
      rules[96]
    )
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[57] and current.id not in nonterminal_first[57]:
        return tree
    if current == None:
        return tree
    if rule == 30: # $_gen7 = :identifier $_gen8
        ctx.rule = rules[30]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 59: # $ll1_rule_rhs = $_gen12
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    elif rule == 65: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[65]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 13) # :null
        tree.add(t)
        return tree
    elif rule == 66: # $ll1_rule_rhs = $parser
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58] if x >=0],
      rules[66]
    )
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[59] and current.id not in nonterminal_first[59]:
        return tree
    if current == None:
        return tree
    if rule == 56: # $_gen13 = :pipe $rule $_gen13
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 5) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 69: # $parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[69]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 14) # :parser_expression
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60] if x >=0],
      rules[69]
    )
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
        return tree
    if current == None:
        return tree
    if rule == 14: # $_gen2 = $regex_partial $_gen2
        ctx.rule = rules[14]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_partial(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 75: # $expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[75]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 35) # :mixfix_rule_hint
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
    elif rule == 76: # $expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[76]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 15) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    elif rule == 77: # $expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[77]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 41) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[62] if x >=0],
      rules[77]
    )
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 78: # $nud = $_gen14
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[63] if x >=0],
      rules[78]
    )
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = False
    if current != None and current.id in nonterminal_follow[64] and current.id not in nonterminal_first[64]:
        return tree
    if current == None:
        return tree
    if rule == 73: # $_gen18 = $led
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 81: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[81]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 2) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[65] if x >=0],
      rules[81]
    )
def parse__gen22(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen22'))
    ctx.nonterminal = "_gen22"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
        return tree
    if current == None:
        return tree
    if rule == 99: # $_gen22 = :comma $macro_parameter $_gen22
        ctx.rule = rules[99]
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
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 9: # $lexer_atom = $lexer_regex
        ctx.rule = rules[9]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 10: # $lexer_atom = $lexer_mode
        ctx.rule = rules[10]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_mode(ctx)
        tree.add(subtree)
        return tree
    elif rule == 11: # $lexer_atom = $lexer_partials
        ctx.rule = rules[11]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_partials(ctx)
        tree.add(subtree)
        return tree
    elif rule == 12: # $lexer_atom = $lexer_code
        ctx.rule = rules[12]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_code(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[67] if x >=0],
      rules[12]
    )
def parse_enumerated_regex(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'enumerated_regex'))
    ctx.nonterminal = "enumerated_regex"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 26: # $enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )
        ctx.rule = rules[26]
        ast_parameters = OrderedDict([
            ('enums', 2),
            ('onmatch', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('EnumeratedRegex', ast_parameters)
        t = expect(ctx, 24) # :regex_enum
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        t = expect(ctx, 4) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68] if x >=0],
      rules[26]
    )
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, 'lexer_partials'))
    ctx.nonterminal = "lexer_partials"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 16: # $lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )
        ctx.rule = rules[16]
        ast_parameters = OrderedDict([
            ('list', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartials', ast_parameters)
        t = expect(ctx, 45) # :partials
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[69] if x >=0],
      rules[16]
    )
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 54: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[54]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 44) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 20) # :nonterminal
        tree.add(t)
        t = expect(ctx, 21) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70] if x >=0],
      rules[54]
    )
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[71] and current.id not in nonterminal_first[71]:
        return tree
    if current == None:
        return tree
    if rule == 55: # $_gen12 = $rule $_gen13
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[72] and current.id not in nonterminal_first[72]:
        return tree
    if current == None:
        return tree
    if rule == 21: # $_gen4 = $lexer_target $_gen4
        ctx.rule = rules[21]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 18: # $lexer_regex = $enumerated_regex
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_enumerated_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 23: # $lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[23]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 18) # :regex
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 4) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[73] if x >=0],
      rules[23]
    )
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'body_element'))
    ctx.nonterminal = "body_element"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 3: # $body_element = $body_element_sub
        ctx.rule = rules[3]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_body_element_sub(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[74] if x >=0],
      rules[3]
    )
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 79: # $led = :expression_divider $_gen14 -> $1
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 29) # :expression_divider
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75] if x >=0],
      rules[79]
    )
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = False
    if current != None and current.id in nonterminal_follow[76] and current.id not in nonterminal_first[76]:
        return tree
    if current == None:
        return tree
    if rule == 62: # $_gen15 = $ast_transform
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[77] and current.id not in nonterminal_first[77]:
        return tree
    if current == None:
        return tree
    if rule == 60: # $_gen14 = $morpheme $_gen14
        ctx.rule = rules[60]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_code(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'lexer_code'))
    ctx.nonterminal = "lexer_code"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 13: # $lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )
        ctx.rule = rules[13]
        ast_parameters = OrderedDict([
            ('language', 1),
            ('code', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerCode', ast_parameters)
        t = expect(ctx, 32) # :code_start
        tree.add(t)
        t = expect(ctx, 40) # :language
        tree.add(t)
        t = expect(ctx, 1) # :code
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78] if x >=0],
      rules[13]
    )
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[79] and current.id not in nonterminal_first[79]:
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
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 80: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 6) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[80] if x >=0],
      rules[80]
    )
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 97: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[97]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 21) # :equals
        tree.add(t)
        t = expect(ctx, 7) # :nonterminal_reference
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81] if x >=0],
      rules[97]
    )
def parse__gen21(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen21'))
    ctx.nonterminal = "_gen21"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
        return tree
    if current == None:
        return tree
    if rule == 98: # $_gen21 = $macro_parameter $_gen22
        ctx.rule = rules[98]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen22(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'terminal'))
    ctx.nonterminal = "terminal"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 44: # $terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[44]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 9) # :terminal
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[83] if x >=0],
      rules[44]
    )
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 84: # $associativity = :left
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 11) # :left
        tree.add(t)
        return tree
    elif rule == 85: # $associativity = :right
        ctx.rule = rules[85]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 27) # :right
        tree.add(t)
        return tree
    elif rule == 86: # $associativity = :unary
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 0) # :unary
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84] if x >=0],
      rules[86]
    )
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 64: # $rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[64]
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
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[85] if x >=0],
      rules[64]
    )
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'regex_partial'))
    ctx.nonterminal = "regex_partial"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 17: # $regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )
        ctx.rule = rules[17]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('name', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartial', ast_parameters)
        t = expect(ctx, 18) # :regex
        tree.add(t)
        t = expect(ctx, 4) # :arrow
        tree.add(t)
        t = expect(ctx, 26) # :regex_partial
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[86] if x >=0],
      rules[17]
    )
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 49: # $parser = $parser_ll1
        ctx.rule = rules[49]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 50: # $parser = $parser_expression
        ctx.rule = rules[50]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[87] if x >=0],
      rules[50]
    )
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, 'grammar'))
    ctx.nonterminal = "grammar"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 2: # $grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )
        ctx.rule = rules[2]
        ast_parameters = OrderedDict([
            ('body', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Grammar', ast_parameters)
        t = expect(ctx, 3) # :grammar
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[88] if x >=0],
      rules[2]
    )
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(89, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = False
    if current != None and current.id in nonterminal_follow[89] and current.id not in nonterminal_first[89]:
        return tree
    if current == None:
        return tree
    if rule == 19: # $_gen3 = $regex_options
        ctx.rule = rules[19]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_enumeration(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, 'regex_enumeration'))
    ctx.nonterminal = "regex_enumeration"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 29: # $regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('language', 0),
            ('regex', 2),
            ('options', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexEnum', ast_parameters)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 2) # :colon
        tree.add(t)
        t = expect(ctx, 18) # :regex
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[90] if x >=0],
      rules[29]
    )
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = False
    if current != None and current.id in nonterminal_follow[91] and current.id not in nonterminal_first[91]:
        return tree
    if current == None:
        return tree
    if rule == 27: # $_gen6 = $regex_enumeration_options
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_enumeration_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_enumeration_options(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'regex_enumeration_options'))
    ctx.nonterminal = "regex_enumeration_options"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 34: # $regex_enumeration_options = :lparen $_gen7 :rparen -> $1
        ctx.rule = rules[34]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 6) # :lparen
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92] if x >=0],
      rules[34]
    )
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 45: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[45]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 22) # :lsquare
        tree.add(t)
        t = expect(ctx, 43) # :integer
        tree.add(t)
        t = expect(ctx, 23) # :rsquare
        tree.add(t)
        return tree
    elif rule == 46: # $match_group = :no_group
        ctx.rule = rules[46]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 28) # :no_group
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[93] if x >=0],
      rules[46]
    )
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 72: # $expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[72]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 30) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 20) # :nonterminal
        tree.add(t)
        t = expect(ctx, 21) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94] if x >=0],
      rules[72]
    )
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(95, 'body_element_sub'))
    ctx.nonterminal = "body_element_sub"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
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
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[95] if x >=0],
      rules[5]
    )
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(96, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[96] and current.id not in nonterminal_first[96]:
        return tree
    if current == None:
        return tree
    if rule == 51: # $_gen11 = $ll1_rule $_gen11
        ctx.rule = rules[51]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen20(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(97, '_gen20'))
    ctx.nonterminal = "_gen20"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[97] and current.id not in nonterminal_first[97]:
        return tree
    if current == None:
        return tree
    if rule == 92: # $_gen20 = :comma $ast_parameter $_gen20
        ctx.rule = rules[92]
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
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(98, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[98] and current.id not in nonterminal_first[98]:
        return tree
    if current == None:
        return tree
    if rule == 31: # $_gen8 = :comma :identifier $_gen8
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 37) # :comma
        tree.add(t)
        tree.listSeparator = t
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(99, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 87: # $morpheme = :terminal
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 9) # :terminal
        tree.add(t)
        return tree
    elif rule == 88: # $morpheme = :nonterminal
        ctx.rule = rules[88]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 20) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 89: # $morpheme = $macro
        ctx.rule = rules[89]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[99] if x >=0],
      rules[89]
    )
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[54][current.id] if current else -1
    tree = ParseTree(NonTerminal(100, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[100] and current.id not in nonterminal_first[100]:
        return tree
    if current == None:
        return tree
    if rule == 91: # $_gen19 = $ast_parameter $_gen20
        ctx.rule = rules[91]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[55][current.id] if current else -1
    tree = ParseTree(NonTerminal(101, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = False
    if current != None and current.id in nonterminal_follow[101] and current.id not in nonterminal_first[101]:
        return tree
    if current == None:
        return tree
    if rule == 70: # $_gen17 = $binding_power
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[56][current.id] if current else -1
    tree = ParseTree(NonTerminal(102, 'lexer'))
    ctx.nonterminal = "lexer"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 8: # $lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )
        ctx.rule = rules[8]
        ast_parameters = OrderedDict([
            ('atoms', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 12) # :lexer
        tree.add(t)
        t = expect(ctx, 31) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 17) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[102] if x >=0],
      rules[8]
    )
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[57][current.id] if current else -1
    tree = ParseTree(NonTerminal(103, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[103] and current.id not in nonterminal_first[103]:
        return tree
    if current == None:
        return tree
    if rule == 67: # $_gen16 = $expression_rule $_gen16
        ctx.rule = rules[67]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[58][current.id] if current else -1
    tree = ParseTree(NonTerminal(104, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 90: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[90]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 4) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[104] if x >=0],
      rules[90]
    )
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[59][current.id] if current else -1
    tree = ParseTree(NonTerminal(105, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 102: # $macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[102]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 25) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :lparen
        tree.add(t)
        subtree = parse__gen21(ctx)
        tree.add(subtree)
        t = expect(ctx, 10) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[105] if x >=0],
      rules[102]
    )
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
    def __init__(self, string, resource, errors, user_context):
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
          (re.compile(r'code<([a-z]+)>\s*<<\s*([a-zA-Z_]+)(?=\s)(.*?)(\2)', re.DOTALL), [
              # (terminal, group, function)
              ('code_start', 2, None),
              ('language', 1, None),
              ('code', 3, None),
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
          (re.compile(r'(r\'(\\\'|[^\'])*\'|"(\\\"|[^\"])*")'), [
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
          (re.compile(r'enum'), [
              # (terminal, group, function)
              ('regex_enum', 0, None),
              LexerStackPush('regex_enum'),
          ]),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), [
              # (terminal, group, function)
              ('identifier', 0, None),
          ]),
        ]),
        'regex_enum': OrderedDict([
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
          (re.compile(r'{'), [
              # (terminal, group, function)
              ('lbrace', 0, None),
          ]),
          (re.compile(r'\('), [
              # (terminal, group, function)
              ('lparen', 0, None),
          ]),
          (re.compile(r'\)'), [
              # (terminal, group, function)
              ('rparen', 0, None),
          ]),
          (re.compile(r':'), [
              # (terminal, group, function)
              ('colon', 0, None),
          ]),
          (re.compile(r','), [
              # (terminal, group, function)
              ('comma', 0, None),
          ]),
          (re.compile(r'(r\'(\\\'|[^\'])*\'|"(\\\"|[^\"])*")'), [
              # (terminal, group, function)
              ('regex', 0, None),
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
    def lex(self, string, resource, errors=None, debug=False):
        if errors is None:
            errors = DefaultSyntaxErrorHandler()
        string_copy = string
        user_context = init()
        ctx = LexerContext(string, resource, errors, user_context)
        while len(ctx.string):
            matched = self._next(ctx, debug)
            if matched == False:
                raise ctx.errors.unrecognized_token(string_copy, ctx.line, ctx.col)
        destroy(ctx.user_context)
        return ctx.tokens
def lex(source, resource, errors=None, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, errors, debug))
