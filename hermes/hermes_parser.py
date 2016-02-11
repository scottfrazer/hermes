
import sys
import os
import re
import base64
import argparse
from collections import OrderedDict
# Common Code #
def parse_tree_string(parsetree, indent=None, b64_source=True, indent_level=0, debug=False):
    indent_str = (' ' * indent * indent_level) if indent else ''
    if isinstance(parsetree, ParseTree):
        children = [parse_tree_string(child, indent, b64_source, indent_level+1, debug) for child in parsetree.children]
        debug_str = parsetree.debug_str() if debug else ''
        if indent is None or len(children) == 0:
            return '{0}({1}: {2}{3})'.format(indent_str, parsetree.nonterminal, debug_str, ', '.join(children))
        else:
            return '{0}({1}:{2}\n{3}\n{4})'.format(
                indent_str,
                parsetree.nonterminal,
                debug_str,
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
  def dumps(self, b64_source=True, **kwargs):
      source_string = base64.b64encode(self.source_string.encode('utf-8')).decode('utf-8') if b64_source else self.source_string
      return '<{resource}:{line}:{col} {terminal} "{source}">'.format(
          resource=self.resource,
          line=self.line,
          col=self.col,
          terminal=self.str,
          source=source_string
      )
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
      self.list_separator_id = None
      self.list = False
  def debug_str(self):
      from copy import deepcopy
      def h(v):
          if v == False or v is None:
              return str(v)
          from xtermcolor import colorize
          return colorize(str(v), ansi=190)
      d = deepcopy(self.__dict__)
      for key in ['self', 'nonterminal', 'children']:
          del d[key]
      f = {k: v for k, v in d.items() if v != False and v is not None}
      return ' [{}]'.format(', '.join(['{}={}'.format(k,h(v)) for k,v in f.items()]))
  def add(self, tree):
      self.children.append( tree )
  def ast(self):
      if self.list == True:
          r = AstList()
          if len(self.children) == 0:
              return r
          for child in self.children:
              if isinstance(child, Terminal) and self.list_separator_id is not None and child.id == self.list_separator_id:
                  continue
              r.append(child.ast())
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
  def dumps(self, indent=None, b64_source=True, debug=False):
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
        super(TokenStream, self).__init__(arg)
        self.index = 0
    def advance(self):
        self.index += 1
        return self.current()
    def last(self):
        return self[-1]
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
    def missing_list_items(self, method, required, found, last):
        return self._error("List for {} requires {} items but only {} were found.".format(method, required, found))
    def missing_terminator(self, method, terminator, last):
        return self._error("List for "+method+" is missing a terminator")
class ParserContext:
  def __init__(self, tokens, errors):
    self.__dict__.update(locals())
    self.nonterminal_string = None
    self.rule_string = None
# Parser Code #
terminals = {
    0: 'regex_enum',
    1: 'dash',
    2: 'lbrace',
    3: 'arrow',
    4: 'unary',
    5: 'rsquare',
    6: 'infix_rule_hint',
    7: 'equals',
    8: 'stack_push',
    9: 'code_start',
    10: 'langle',
    11: 'no_group',
    12: 'expr_rule_hint',
    13: 'partials',
    14: 'regex',
    15: 'rbrace',
    16: 'code',
    17: 'identifier',
    18: 'regex_partial',
    19: 'rangle',
    20: 'language',
    21: 'integer',
    22: 'left',
    23: 'rparen',
    24: 'right',
    25: 'mixfix_rule_hint',
    26: 'colon',
    27: 'expression_divider',
    28: 'prefix_rule_hint',
    29: 'asterisk',
    30: 'll1_rule_hint',
    31: 'string',
    32: 'lexer',
    33: 'grammar',
    34: 'terminal',
    35: 'lsquare',
    36: 'parser',
    37: 'lparen',
    38: 'comma',
    39: 'action',
    40: 'pipe',
    41: 'parser_expression',
    42: 'nonterminal',
    43: 'mode',
    44: 'nonterminal_reference',
    45: 'null',
    'regex_enum': 0,
    'dash': 1,
    'lbrace': 2,
    'arrow': 3,
    'unary': 4,
    'rsquare': 5,
    'infix_rule_hint': 6,
    'equals': 7,
    'stack_push': 8,
    'code_start': 9,
    'langle': 10,
    'no_group': 11,
    'expr_rule_hint': 12,
    'partials': 13,
    'regex': 14,
    'rbrace': 15,
    'code': 16,
    'identifier': 17,
    'regex_partial': 18,
    'rangle': 19,
    'language': 20,
    'integer': 21,
    'left': 22,
    'rparen': 23,
    'right': 24,
    'mixfix_rule_hint': 25,
    'colon': 26,
    'expression_divider': 27,
    'prefix_rule_hint': 28,
    'asterisk': 29,
    'll1_rule_hint': 30,
    'string': 31,
    'lexer': 32,
    'grammar': 33,
    'terminal': 34,
    'lsquare': 35,
    'parser': 36,
    'lparen': 37,
    'comma': 38,
    'action': 39,
    'pipe': 40,
    'parser_expression': 41,
    'nonterminal': 42,
    'mode': 43,
    'nonterminal_reference': 44,
    'null': 45,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, 16, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, 84, -1, -1, -1, -1, -1, -1, -1, 83, -1, -1, 87],
    [-1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, 50, -1, -1, -1, -1, -1, -1, 50, -1, -1, 50, -1, -1, -1, -1, -1],
    [-1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1],
    [7, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, 9, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1],
    [-1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, 64, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, 64, -1, -1, -1, -1, 64, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1],
    [21, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, 4, -1, -1, -1, -1, 4, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, 51, -1, -1, -1, -1, -1, 51, -1, 51, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, 2, -1, -1, -1, -1, 2, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, 47, -1, 53, -1, -1, -1, -1, 53, 47, -1, -1, 52],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [35, -1, -1, -1, -1, -1, -1, -1, 35, 35, -1, 34, -1, 35, 35, 35, -1, 35, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, 34, -1, -1, -1, 35, -1, -1, -1, 35, -1, 35],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, 42, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, 39],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    46: [2, -1],
    47: [24, 4, 22],
    48: [34, -1],
    49: [36],
    50: [34, 42, 17],
    51: [34, 42, 21, 31, 45],
    52: [3, -1],
    53: [27, -1],
    54: [0, 13, 43, 14, 9],
    55: [43],
    56: [34, 42, -1, 17],
    57: [44, 17],
    58: [0],
    59: [32, 36, 41],
    60: [37, -1],
    61: [0, 13, 14, -1, 43, 9],
    62: [36, -1, 41, 32],
    63: [14, -1],
    64: [37],
    65: [34],
    66: [12, 37],
    67: [29, 1],
    68: [30],
    69: [37, 12, -1],
    70: [9],
    71: [28, 25, 6],
    72: [34, -1, 3, 42, 17],
    73: [17],
    74: [32, 36, 41],
    75: [-1, 17],
    76: [35, 11],
    77: [3, 34, -1, 42, 17],
    78: [37],
    79: [17],
    80: [3, 34, 36, -1, 41, 42, 17, 45],
    81: [34, -1, 39, 8, 17, 45],
    82: [34, -1, 42, 17],
    83: [-1, 17],
    84: [2],
    85: [14],
    86: [27],
    87: [29, 1],
    88: [41],
    89: [32],
    90: [17],
    91: [14, 0],
    92: [35, 11, -1],
    93: [-1, 17],
    94: [36, 41],
    95: [34, 39, 8, 17, 45],
    96: [30, -1],
    97: [33],
    98: [13],
    99: [3],
    100: [34, -1, 31, 42, 21, 45],
    101: [37, -1],
}
nonterminal_follow = {
    46: [3],
    47: [23],
    48: [23],
    49: [30, 32, 15, 36, 41],
    50: [12, 30, 3, 34, 15, 37, 40, 42, 17],
    51: [23, 38],
    52: [27, 12, 30, 15, 37, 40],
    53: [15, 12, 37, 3],
    54: [0, 13, 14, 15, 43, 9],
    55: [0, 13, 14, 15, 43, 9],
    56: [15, 12, 37, 3],
    57: [27, 12, 30, 15, 37, 40],
    58: [0, 13, 14, 15, 43, 9],
    59: [15, 36, 41, 32],
    60: [15, 17],
    61: [15],
    62: [15],
    63: [15],
    64: [15, 17],
    65: [0, 23, 8, 9, 13, 14, 34, 15, 39, 43, 17, 45],
    66: [15, 12, 37],
    67: [26],
    68: [15, 30],
    69: [15],
    70: [0, 13, 14, 15, 43, 9],
    71: [15, 12, 37],
    72: [15, 30, 40],
    73: [23, 38],
    74: [15, 36, 41, 32],
    75: [15],
    76: [0, 23, 8, 9, 13, 14, 34, 15, 39, 43, 17, 45],
    77: [15, 30],
    78: [12],
    79: [15, 17],
    80: [15, 30],
    81: [0, 13, 14, 15, 43, 9],
    82: [12, 30, 3, 15, 37, 40],
    83: [15, 23],
    84: [3],
    85: [15, 14],
    86: [15, 12, 37, 3],
    87: [23],
    88: [30, 32, 15, 36, 41],
    89: [15, 36, 41, 32],
    90: [3, 12, 30, 34, 15, 37, 40, 42, 17],
    91: [0, 13, 14, 15, 43, 9],
    92: [0, 23, 8, 9, 13, 14, 34, 15, 39, 43, 17, 45],
    93: [23],
    94: [30, 32, 15, 36, 41],
    95: [0, 13, 14, 34, 15, 39, 43, 8, 9, 17, 45],
    96: [15],
    97: [-1],
    98: [0, 13, 14, 15, 43, 9],
    99: [27, 12, 30, 15, 37, 40],
    100: [23],
    101: [12],
}
rule_first = {
    0: [32, 36, -1, 41],
    1: [33],
    2: [32, 36, 41],
    3: [32],
    4: [36, 41],
    5: [0, 13, 14, -1, 43, 9],
    6: [32],
    7: [14, 0],
    8: [43],
    9: [13],
    10: [9],
    11: [9],
    12: [14, -1],
    13: [13],
    14: [14],
    15: [0],
    16: [2],
    17: [-1],
    18: [34, -1, 39, 8, 17, 45],
    19: [14],
    20: [-1, 17],
    21: [0],
    22: [37],
    23: [-1],
    24: [17],
    25: [-1, 17],
    26: [37],
    27: [2],
    28: [34],
    29: [34],
    30: [-1],
    31: [17],
    32: [8],
    33: [39],
    34: [35, 11],
    35: [-1],
    36: [34],
    37: [35],
    38: [11],
    39: [45],
    40: [43],
    41: [36],
    42: [41],
    43: [30, -1],
    44: [36],
    45: [30],
    46: [34, 3, -1, 17, 42],
    47: [3, 42, 34, 17, -1],
    48: [34, 42, -1, 17],
    49: [3],
    50: [-1],
    51: [34, 42, -1, 3, 17],
    52: [45],
    53: [36, 41],
    54: [12, 37, -1],
    55: [41],
    56: [37],
    57: [-1],
    58: [12, 37],
    59: [27],
    60: [-1],
    61: [25],
    62: [28],
    63: [6],
    64: [34, 42, -1, 17],
    65: [27],
    66: [37],
    67: [29, 1],
    68: [29],
    69: [1],
    70: [22],
    71: [24],
    72: [4],
    73: [34],
    74: [42],
    75: [17],
    76: [3],
    77: [-1, 17],
    78: [17],
    79: [44],
    80: [17],
    81: [31, 21, 34, -1, 42, 45],
    82: [17],
    83: [42],
    84: [34],
    85: [31],
    86: [21],
    87: [45],
}
nonterminal_rules = {
    46: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    47: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    48: [
        "$_gen8 = $terminal",
        "$_gen8 = :_empty",
    ],
    49: [
        "$parser_ll1 = :parser :lbrace $_gen10 :rbrace -> Parser( rules=$2 )",
    ],
    50: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    51: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
        "$macro_parameter = :null",
    ],
    52: [
        "$_gen13 = $ast_transform",
        "$_gen13 = :_empty",
    ],
    53: [
        "$_gen16 = $led",
        "$_gen16 = :_empty",
    ],
    54: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
        "$lexer_atom = $lexer_code",
    ],
    55: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    56: [
        "$nud = $_gen12",
    ],
    57: [
        "$ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    58: [
        "$enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )",
    ],
    59: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    60: [
        "$_gen6 = $regex_enumeration_options",
        "$_gen6 = :_empty",
    ],
    61: [
        "$_gen1 = list($lexer_atom)",
    ],
    62: [
        "$_gen0 = list($body_element)",
    ],
    63: [
        "$_gen2 = list($regex_partial)",
    ],
    64: [
        "$regex_enumeration_options = :lparen $_gen7 :rparen -> $1",
    ],
    65: [
        "$terminal = :terminal $_gen9 -> Terminal( name=$0, group=$1 )",
    ],
    66: [
        "$expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    67: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    68: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    69: [
        "$_gen14 = list($expression_rule)",
    ],
    70: [
        "$lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )",
    ],
    71: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    72: [
        "$rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )",
    ],
    73: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    74: [
        "$body_element = $body_element_sub",
    ],
    75: [
        "$_gen5 = list($regex_enumeration)",
    ],
    76: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    77: [
        "$_gen11 = list($rule,:pipe)",
    ],
    78: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    79: [
        "$regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )",
    ],
    80: [
        "$ll1_rule_rhs = $_gen11",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    81: [
        "$_gen4 = list($lexer_target)",
    ],
    82: [
        "$_gen12 = list($morpheme)",
    ],
    83: [
        "$_gen7 = list(:identifier,:comma)",
    ],
    84: [
        "$regex_options = :lbrace $_gen7 :rbrace -> $1",
    ],
    85: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    86: [
        "$led = :expression_divider $_gen12 -> $1",
    ],
    87: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    88: [
        "$parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    89: [
        "$lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )",
    ],
    90: [
        "$macro = :identifier :lparen $_gen18 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    91: [
        "$lexer_regex = $enumerated_regex",
        "$lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    92: [
        "$_gen9 = $match_group",
        "$_gen9 = :_empty",
    ],
    93: [
        "$_gen17 = list($ast_parameter,:comma)",
    ],
    94: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    95: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen8 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :stack_push",
        "$lexer_target = :action",
        "$lexer_target = :null -> Null(  )",
    ],
    96: [
        "$_gen10 = list($ll1_rule)",
    ],
    97: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    98: [
        "$lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )",
    ],
    99: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    100: [
        "$_gen18 = list($macro_parameter,:comma)",
    ],
    101: [
        "$_gen15 = $binding_power",
        "$_gen15 = :_empty",
    ],
}
rules = {
    0: "$_gen0 = list($body_element)",
    1: "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    2: "$body_element = $body_element_sub",
    3: "$body_element_sub = $lexer",
    4: "$body_element_sub = $parser",
    5: "$_gen1 = list($lexer_atom)",
    6: "$lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )",
    7: "$lexer_atom = $lexer_regex",
    8: "$lexer_atom = $lexer_mode",
    9: "$lexer_atom = $lexer_partials",
    10: "$lexer_atom = $lexer_code",
    11: "$lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )",
    12: "$_gen2 = list($regex_partial)",
    13: "$lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )",
    14: "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    15: "$lexer_regex = $enumerated_regex",
    16: "$_gen3 = $regex_options",
    17: "$_gen3 = :_empty",
    18: "$_gen4 = list($lexer_target)",
    19: "$lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    20: "$_gen5 = list($regex_enumeration)",
    21: "$enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )",
    22: "$_gen6 = $regex_enumeration_options",
    23: "$_gen6 = :_empty",
    24: "$regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )",
    25: "$_gen7 = list(:identifier,:comma)",
    26: "$regex_enumeration_options = :lparen $_gen7 :rparen -> $1",
    27: "$regex_options = :lbrace $_gen7 :rbrace -> $1",
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
    43: "$_gen10 = list($ll1_rule)",
    44: "$parser_ll1 = :parser :lbrace $_gen10 :rbrace -> Parser( rules=$2 )",
    45: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    46: "$_gen11 = list($rule,:pipe)",
    47: "$ll1_rule_rhs = $_gen11",
    48: "$_gen12 = list($morpheme)",
    49: "$_gen13 = $ast_transform",
    50: "$_gen13 = :_empty",
    51: "$rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )",
    52: "$ll1_rule_rhs = :null -> NullProduction(  )",
    53: "$ll1_rule_rhs = $parser",
    54: "$_gen14 = list($expression_rule)",
    55: "$parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )",
    56: "$_gen15 = $binding_power",
    57: "$_gen15 = :_empty",
    58: "$expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    59: "$_gen16 = $led",
    60: "$_gen16 = :_empty",
    61: "$expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    62: "$expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )",
    63: "$expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )",
    64: "$nud = $_gen12",
    65: "$led = :expression_divider $_gen12 -> $1",
    66: "$binding_power = :lparen $precedence :rparen -> $1",
    67: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    68: "$binding_power_marker = :asterisk",
    69: "$binding_power_marker = :dash",
    70: "$associativity = :left",
    71: "$associativity = :right",
    72: "$associativity = :unary",
    73: "$morpheme = :terminal",
    74: "$morpheme = :nonterminal",
    75: "$morpheme = $macro",
    76: "$ast_transform = :arrow $ast_transform_sub -> $1",
    77: "$_gen17 = list($ast_parameter,:comma)",
    78: "$ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    79: "$ast_transform_sub = :nonterminal_reference",
    80: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    81: "$_gen18 = list($macro_parameter,:comma)",
    82: "$macro = :identifier :lparen $_gen18 :rparen -> Macro( name=$0, parameters=$2 )",
    83: "$macro_parameter = :nonterminal",
    84: "$macro_parameter = :terminal",
    85: "$macro_parameter = :string",
    86: "$macro_parameter = :integer",
    87: "$macro_parameter = :null",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 45
def parse(tokens, errors=None, start=None):
    if errors is None:
        errors = DefaultSyntaxErrorHandler()
    if isinstance(tokens, str):
        tokens = lex(tokens, 'string', errors)
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
def parse__gen18(ctx):
    tree = ParseTree(NonTerminal(100, '_gen18'))
    tree.list = True;
    tree.list_separator_id = 38
    ctx.nonterminal = "_gen18"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[100]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(100)):
        tree.add(parse_macro_parameter(ctx))
        ctx.nonterminal = "_gen18" # Horrible -- because parse_* can reset this
        if ctx.tokens.current() is not None and ctx.tokens.current().id == 38:
            tree.add(expect(ctx, 38));
        else:
          break
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen5(ctx):
    tree = ParseTree(NonTerminal(75, '_gen5'))
    tree.list = True;
    ctx.nonterminal = "_gen5"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[75]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(75)):
        tree.add(parse_regex_enumeration(ctx))
        ctx.nonterminal = "_gen5" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen11(ctx):
    tree = ParseTree(NonTerminal(77, '_gen11'))
    tree.list = True;
    tree.list_separator_id = 40
    ctx.nonterminal = "_gen11"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[77]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(77)):
        tree.add(parse_rule(ctx))
        ctx.nonterminal = "_gen11" # Horrible -- because parse_* can reset this
        if ctx.tokens.current() is not None and ctx.tokens.current().id == 40:
            tree.add(expect(ctx, 40));
        else:
          break
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen17(ctx):
    tree = ParseTree(NonTerminal(93, '_gen17'))
    tree.list = True;
    tree.list_separator_id = 38
    ctx.nonterminal = "_gen17"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[93]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(93)):
        tree.add(parse_ast_parameter(ctx))
        ctx.nonterminal = "_gen17" # Horrible -- because parse_* can reset this
        if ctx.tokens.current() is not None and ctx.tokens.current().id == 38:
            tree.add(expect(ctx, 38));
        else:
          break
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen1(ctx):
    tree = ParseTree(NonTerminal(61, '_gen1'))
    tree.list = True;
    ctx.nonterminal = "_gen1"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[61]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(61)):
        tree.add(parse_lexer_atom(ctx))
        ctx.nonterminal = "_gen1" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen10(ctx):
    tree = ParseTree(NonTerminal(96, '_gen10'))
    tree.list = True;
    ctx.nonterminal = "_gen10"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[96]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(96)):
        tree.add(parse_ll1_rule(ctx))
        ctx.nonterminal = "_gen10" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen0(ctx):
    tree = ParseTree(NonTerminal(62, '_gen0'))
    tree.list = True;
    ctx.nonterminal = "_gen0"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[62]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(62)):
        tree.add(parse_body_element(ctx))
        ctx.nonterminal = "_gen0" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen4(ctx):
    tree = ParseTree(NonTerminal(81, '_gen4'))
    tree.list = True;
    ctx.nonterminal = "_gen4"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[81]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(81)):
        tree.add(parse_lexer_target(ctx))
        ctx.nonterminal = "_gen4" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen2(ctx):
    tree = ParseTree(NonTerminal(63, '_gen2'))
    tree.list = True;
    ctx.nonterminal = "_gen2"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[63]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(63)):
        tree.add(parse_regex_partial(ctx))
        ctx.nonterminal = "_gen2" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen12(ctx):
    tree = ParseTree(NonTerminal(82, '_gen12'))
    tree.list = True;
    ctx.nonterminal = "_gen12"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[82]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(82)):
        tree.add(parse_morpheme(ctx))
        ctx.nonterminal = "_gen12" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen7(ctx):
    tree = ParseTree(NonTerminal(83, '_gen7'))
    tree.list = True;
    tree.list_separator_id = 38
    ctx.nonterminal = "_gen7"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[83]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(83)):
        tree.add(expect(ctx, 17))
        if ctx.tokens.current() is not None and ctx.tokens.current().id == 38:
            tree.add(expect(ctx, 38));
        else:
          break
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen14(ctx):
    tree = ParseTree(NonTerminal(69, '_gen14'))
    tree.list = True;
    ctx.nonterminal = "_gen14"
    if ctx.tokens.current() is not None and \
       ctx.tokens.current().id not in nonterminal_first[101] and \
       ctx.tokens.current().id in nonterminal_follow[69]:
        return tree;
    if ctx.tokens.current() is None:
        return tree
    minimum = 0;
    while minimum > 0 or \
           (ctx.tokens.current() is not None and \
            ctx.tokens.current().id in nonterminal_first.get(69)):
        tree.add(parse_expression_rule(ctx))
        ctx.nonterminal = "_gen14" # Horrible -- because parse_* can reset this
        minimum = max(minimum - 1, 0)
    return tree
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, '_gen3'))
    ctx.nonterminal = "_gen3"
    if current != None and current.id in nonterminal_follow[46] and current.id not in nonterminal_first[46]:
        return tree
    if current == None:
        return tree
    if rule == 16: # $_gen3 = $regex_options
        ctx.rule = rules[16]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'associativity'))
    ctx.nonterminal = "associativity"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 70: # $associativity = :left
        ctx.rule = rules[70]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 22) # :left
        tree.add(t)
        return tree
    elif rule == 71: # $associativity = :right
        ctx.rule = rules[71]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :right
        tree.add(t)
        return tree
    elif rule == 72: # $associativity = :unary
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 4) # :unary
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[47] if x >=0],
      rules[72]
    )
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, '_gen8'))
    ctx.nonterminal = "_gen8"
    if current != None and current.id in nonterminal_follow[48] and current.id not in nonterminal_first[48]:
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
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 44: # $parser_ll1 = :parser :lbrace $_gen10 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[44]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 36) # :parser
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49] if x >=0],
      rules[44]
    )
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'morpheme'))
    ctx.nonterminal = "morpheme"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 73: # $morpheme = :terminal
        ctx.rule = rules[73]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :terminal
        tree.add(t)
        return tree
    elif rule == 74: # $morpheme = :nonterminal
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 42) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 75: # $morpheme = $macro
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50] if x >=0],
      rules[75]
    )
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 83: # $macro_parameter = :nonterminal
        ctx.rule = rules[83]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 42) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 84: # $macro_parameter = :terminal
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :terminal
        tree.add(t)
        return tree
    elif rule == 85: # $macro_parameter = :string
        ctx.rule = rules[85]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :string
        tree.add(t)
        return tree
    elif rule == 86: # $macro_parameter = :integer
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 21) # :integer
        tree.add(t)
        return tree
    elif rule == 87: # $macro_parameter = :null
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 45) # :null
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[51] if x >=0],
      rules[87]
    )
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, '_gen13'))
    ctx.nonterminal = "_gen13"
    if current != None and current.id in nonterminal_follow[52] and current.id not in nonterminal_first[52]:
        return tree
    if current == None:
        return tree
    if rule == 49: # $_gen13 = $ast_transform
        ctx.rule = rules[49]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, '_gen16'))
    ctx.nonterminal = "_gen16"
    if current != None and current.id in nonterminal_follow[53] and current.id not in nonterminal_first[53]:
        return tree
    if current == None:
        return tree
    if rule == 59: # $_gen16 = $led
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 7: # $lexer_atom = $lexer_regex
        ctx.rule = rules[7]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 8: # $lexer_atom = $lexer_mode
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_mode(ctx)
        tree.add(subtree)
        return tree
    elif rule == 9: # $lexer_atom = $lexer_partials
        ctx.rule = rules[9]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_partials(ctx)
        tree.add(subtree)
        return tree
    elif rule == 10: # $lexer_atom = $lexer_code
        ctx.rule = rules[10]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_code(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[54] if x >=0],
      rules[10]
    )
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 40: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[40]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 43) # :mode
        tree.add(t)
        t = expect(ctx, 10) # :langle
        tree.add(t)
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 19) # :rangle
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55] if x >=0],
      rules[40]
    )
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, 'nud'))
    ctx.nonterminal = "nud"
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 64: # $nud = $_gen12
        ctx.rule = rules[64]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 78: # $ast_transform_sub = :identifier :lparen $_gen17 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[78]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 37) # :lparen
        tree.add(t)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        t = expect(ctx, 23) # :rparen
        tree.add(t)
        return tree
    elif rule == 79: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 44) # :nonterminal_reference
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57] if x >=0],
      rules[79]
    )
def parse_enumerated_regex(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'enumerated_regex'))
    ctx.nonterminal = "enumerated_regex"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 21: # $enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )
        ctx.rule = rules[21]
        ast_parameters = OrderedDict([
            ('enums', 2),
            ('onmatch', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('EnumeratedRegex', ast_parameters)
        t = expect(ctx, 0) # :regex_enum
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        t = expect(ctx, 3) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58] if x >=0],
      rules[21]
    )
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'body_element_sub'))
    ctx.nonterminal = "body_element_sub"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 3: # $body_element_sub = $lexer
        ctx.rule = rules[3]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer(ctx)
        tree.add(subtree)
        return tree
    elif rule == 4: # $body_element_sub = $parser
        ctx.rule = rules[4]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59] if x >=0],
      rules[4]
    )
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, '_gen6'))
    ctx.nonterminal = "_gen6"
    if current != None and current.id in nonterminal_follow[60] and current.id not in nonterminal_first[60]:
        return tree
    if current == None:
        return tree
    if rule == 22: # $_gen6 = $regex_enumeration_options
        ctx.rule = rules[22]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_enumeration_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_enumeration_options(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'regex_enumeration_options'))
    ctx.nonterminal = "regex_enumeration_options"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 26: # $regex_enumeration_options = :lparen $_gen7 :rparen -> $1
        ctx.rule = rules[26]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 37) # :lparen
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 23) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[64] if x >=0],
      rules[26]
    )
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'terminal'))
    ctx.nonterminal = "terminal"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 36: # $terminal = :terminal $_gen9 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[36]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 34) # :terminal
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[65] if x >=0],
      rules[36]
    )
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 58: # $expression_rule = $_gen15 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[58]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 42) # :nonterminal
        tree.add(t)
        t = expect(ctx, 7) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[66] if x >=0],
      rules[58]
    )
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 68: # $binding_power_marker = :asterisk
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :asterisk
        tree.add(t)
        return tree
    elif rule == 69: # $binding_power_marker = :dash
        ctx.rule = rules[69]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 1) # :dash
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[67] if x >=0],
      rules[69]
    )
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 45: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[45]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 30) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 42) # :nonterminal
        tree.add(t)
        t = expect(ctx, 7) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68] if x >=0],
      rules[45]
    )
def parse_lexer_code(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'lexer_code'))
    ctx.nonterminal = "lexer_code"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 11: # $lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )
        ctx.rule = rules[11]
        ast_parameters = OrderedDict([
            ('language', 1),
            ('code', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerCode', ast_parameters)
        t = expect(ctx, 9) # :code_start
        tree.add(t)
        t = expect(ctx, 20) # :language
        tree.add(t)
        t = expect(ctx, 16) # :code
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70] if x >=0],
      rules[11]
    )
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 61: # $expression_rule_production = :mixfix_rule_hint $nud $_gen13 $_gen16 $_gen13 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[61]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 25) # :mixfix_rule_hint
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
    elif rule == 62: # $expression_rule_production = :prefix_rule_hint $_gen12 $_gen13 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[62]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 28) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    elif rule == 63: # $expression_rule_production = :infix_rule_hint $_gen12 $_gen13 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[63]
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
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71] if x >=0],
      rules[63]
    )
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'rule'))
    ctx.nonterminal = "rule"
    if current != None and current.id in nonterminal_follow[72] and current.id not in nonterminal_first[72]:
        return tree
    if current == None:
        return tree
    if rule == 51: # $rule = $_gen12 $_gen13 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[51]
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
    return tree
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 80: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[80]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 7) # :equals
        tree.add(t)
        t = expect(ctx, 44) # :nonterminal_reference
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[73] if x >=0],
      rules[80]
    )
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'body_element'))
    ctx.nonterminal = "body_element"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 2: # $body_element = $body_element_sub
        ctx.rule = rules[2]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_body_element_sub(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[74] if x >=0],
      rules[2]
    )
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'match_group'))
    ctx.nonterminal = "match_group"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 37: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[37]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 35) # :lsquare
        tree.add(t)
        t = expect(ctx, 21) # :integer
        tree.add(t)
        t = expect(ctx, 5) # :rsquare
        tree.add(t)
        return tree
    elif rule == 38: # $match_group = :no_group
        ctx.rule = rules[38]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 11) # :no_group
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76] if x >=0],
      rules[38]
    )
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'binding_power'))
    ctx.nonterminal = "binding_power"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 66: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 37) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 23) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78] if x >=0],
      rules[66]
    )
def parse_regex_enumeration(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'regex_enumeration'))
    ctx.nonterminal = "regex_enumeration"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 24: # $regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )
        ctx.rule = rules[24]
        ast_parameters = OrderedDict([
            ('language', 0),
            ('regex', 2),
            ('options', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexEnum', ast_parameters)
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 26) # :colon
        tree.add(t)
        t = expect(ctx, 14) # :regex
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[79] if x >=0],
      rules[24]
    )
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    if current != None and current.id in nonterminal_follow[80] and current.id not in nonterminal_first[80]:
        return tree
    if current == None:
        return tree
    if rule == 47: # $ll1_rule_rhs = $_gen11
        ctx.rule = rules[47]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    elif rule == 52: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[52]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 45) # :null
        tree.add(t)
        return tree
    elif rule == 53: # $ll1_rule_rhs = $parser
        ctx.rule = rules[53]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, 'regex_options'))
    ctx.nonterminal = "regex_options"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 27: # $regex_options = :lbrace $_gen7 :rbrace -> $1
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[84] if x >=0],
      rules[27]
    )
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, 'regex_partial'))
    ctx.nonterminal = "regex_partial"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 14: # $regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )
        ctx.rule = rules[14]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('name', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartial', ast_parameters)
        t = expect(ctx, 14) # :regex
        tree.add(t)
        t = expect(ctx, 3) # :arrow
        tree.add(t)
        t = expect(ctx, 18) # :regex_partial
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[85] if x >=0],
      rules[14]
    )
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, 'led'))
    ctx.nonterminal = "led"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 65: # $led = :expression_divider $_gen12 -> $1
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 27) # :expression_divider
        tree.add(t)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[86] if x >=0],
      rules[65]
    )
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, 'precedence'))
    ctx.nonterminal = "precedence"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 67: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[67]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[87] if x >=0],
      rules[67]
    )
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 55: # $parser_expression = :parser_expression :lbrace $_gen14 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[55]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 41) # :parser_expression
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[88] if x >=0],
      rules[55]
    )
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(89, 'lexer'))
    ctx.nonterminal = "lexer"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 6: # $lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )
        ctx.rule = rules[6]
        ast_parameters = OrderedDict([
            ('atoms', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 32) # :lexer
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[89] if x >=0],
      rules[6]
    )
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, 'macro'))
    ctx.nonterminal = "macro"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 82: # $macro = :identifier :lparen $_gen18 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[82]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 37) # :lparen
        tree.add(t)
        subtree = parse__gen18(ctx)
        tree.add(subtree)
        t = expect(ctx, 23) # :rparen
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[90] if x >=0],
      rules[82]
    )
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 15: # $lexer_regex = $enumerated_regex
        ctx.rule = rules[15]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_enumerated_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 19: # $lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[19]
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
        t = expect(ctx, 3) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[91] if x >=0],
      rules[19]
    )
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, '_gen9'))
    ctx.nonterminal = "_gen9"
    if current != None and current.id in nonterminal_follow[92] and current.id not in nonterminal_first[92]:
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
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'parser'))
    ctx.nonterminal = "parser"
    if current == None:
        raise ctx.errors.unexpected_eof()
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
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94] if x >=0],
      rules[42]
    )
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(95, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    if current == None:
        raise ctx.errors.unexpected_eof()
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
        t = expect(ctx, 17) # :identifier
        tree.add(t)
        t = expect(ctx, 37) # :lparen
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        t = expect(ctx, 23) # :rparen
        tree.add(t)
        return tree
    elif rule == 32: # $lexer_target = :stack_push
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 8) # :stack_push
        tree.add(t)
        return tree
    elif rule == 33: # $lexer_target = :action
        ctx.rule = rules[33]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 39) # :action
        tree.add(t)
        return tree
    elif rule == 39: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[39]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 45) # :null
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[95] if x >=0],
      rules[39]
    )
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[51][current.id] if current else -1
    tree = ParseTree(NonTerminal(97, 'grammar'))
    ctx.nonterminal = "grammar"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 1: # $grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )
        ctx.rule = rules[1]
        ast_parameters = OrderedDict([
            ('body', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Grammar', ast_parameters)
        t = expect(ctx, 33) # :grammar
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[97] if x >=0],
      rules[1]
    )
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(98, 'lexer_partials'))
    ctx.nonterminal = "lexer_partials"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 13: # $lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )
        ctx.rule = rules[13]
        ast_parameters = OrderedDict([
            ('list', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartials', ast_parameters)
        t = expect(ctx, 13) # :partials
        tree.add(t)
        t = expect(ctx, 2) # :lbrace
        tree.add(t)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 15) # :rbrace
        tree.add(t)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[98] if x >=0],
      rules[13]
    )
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(99, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    if current == None:
        raise ctx.errors.unexpected_eof()
    if rule == 76: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[76]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 3) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[99] if x >=0],
      rules[76]
    )
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[55][current.id] if current else -1
    tree = ParseTree(NonTerminal(101, '_gen15'))
    ctx.nonterminal = "_gen15"
    if current != None and current.id in nonterminal_follow[101] and current.id not in nonterminal_first[101]:
        return tree
    if current == None:
        return tree
    if rule == 56: # $_gen15 = $binding_power
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
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
          (re.compile(r'null'), [
              # (terminal, group, function)
              ('null', 0, None),
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
