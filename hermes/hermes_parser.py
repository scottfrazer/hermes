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
    0: 'colon',
    1: 'code_start',
    2: 'rangle',
    3: 'parser',
    4: 'll1_rule_hint',
    5: 'lsquare',
    6: 'comma',
    7: 'integer',
    8: 'infix_rule_hint',
    9: 'nonterminal_reference',
    10: 'left',
    11: 'pipe',
    12: 'partials',
    13: 'lparen',
    14: 'expr_rule_hint',
    15: 'parser_expression',
    16: 'action',
    17: 'expression_divider',
    18: 'stack_push',
    19: 'nonterminal',
    20: 'string',
    21: 'lbrace',
    22: 'grammar',
    23: 'rsquare',
    24: 'right',
    25: 'langle',
    26: 'rbrace',
    27: 'regex_partial',
    28: 'code',
    29: 'terminal',
    30: 'unary',
    31: 'asterisk',
    32: 'regex',
    33: 'regex_enum',
    34: 'identifier',
    35: 'null',
    36: 'mode',
    37: 'rparen',
    38: 'lexer',
    39: 'mixfix_rule_hint',
    40: 'equals',
    41: 'language',
    42: 'arrow',
    43: 'no_group',
    44: 'prefix_rule_hint',
    45: 'dash',
    'colon': 0,
    'code_start': 1,
    'rangle': 2,
    'parser': 3,
    'll1_rule_hint': 4,
    'lsquare': 5,
    'comma': 6,
    'integer': 7,
    'infix_rule_hint': 8,
    'nonterminal_reference': 9,
    'left': 10,
    'pipe': 11,
    'partials': 12,
    'lparen': 13,
    'expr_rule_hint': 14,
    'parser_expression': 15,
    'action': 16,
    'expression_divider': 17,
    'stack_push': 18,
    'nonterminal': 19,
    'string': 20,
    'lbrace': 21,
    'grammar': 22,
    'rsquare': 23,
    'right': 24,
    'langle': 25,
    'rbrace': 26,
    'regex_partial': 27,
    'code': 28,
    'terminal': 29,
    'unary': 30,
    'asterisk': 31,
    'regex': 32,
    'regex_enum': 33,
    'identifier': 34,
    'null': 35,
    'mode': 36,
    'rparen': 37,
    'lexer': 38,
    'mixfix_rule_hint': 39,
    'equals': 40,
    'language': 41,
    'arrow': 42,
    'no_group': 43,
    'prefix_rule_hint': 44,
    'dash': 45,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, 43, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, 43, -1, 43, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, 43, -1, -1, 43, 43, 43, 43, 43, 43, -1, -1, -1, -1, -1, 42, -1, -1],
    [-1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, 55, -1, -1, 55, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 85, -1, -1, -1, -1, -1, 86, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 98, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 98, 98, -1, -1, -1, -1, -1, -1, -1, -1, 98, -1, -1, -1, -1, -1, -1, -1, 101, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, 21, -1, 21, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, 21, -1, -1, 22, 22, 21, 21, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 102, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 61, -1, -1, -1, -1, -1, -1, 61, -1, 61, 61, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, 61, -1, -1, 60, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 83],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, 64, -1, -1, 64, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1],
    [-1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 106, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 103, 105, -1, -1, -1, -1, -1, -1, -1, -1, 104, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, 39, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 75, -1, -1, -1, -1, 76, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81],
    [-1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, 6, 6, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, 63, -1, 63, 63, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 99, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 100, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1],
    [-1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, -1, -1, -1, -1, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1, 89, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, 9, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 96, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 95, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 66, 59, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, 66, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, 59, -1, -1, 59, -1, -1, -1, -1, 59, 65, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, 78, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, 78, -1, -1, 78, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 92, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 93, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, 74, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 91, -1, -1, 94, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
]
nonterminal_first = {
    46: [-1, 43, 5],
    47: [34, 11, 19, -1, 29, 42],
    48: [38],
    49: [4],
    50: [30, 10, 24],
    51: [-1, 29, 20, 19, 7],
    52: [34],
    53: [29],
    54: [43, 5],
    55: [22],
    56: [34, 35, 16, 18, -1, 29],
    57: [32],
    58: [-1, 29],
    59: [-1, 4],
    60: [34],
    61: [-1, 13, 14],
    62: [17],
    63: [13, 14],
    64: [34, 19, -1, 29],
    65: [45, 31],
    66: [-1, 34],
    67: [-1, 32],
    68: [3],
    69: [1],
    70: [13],
    71: [21],
    72: [34, 19, -1, 29, 42],
    73: [-1, 11],
    74: [3, 15, 38],
    75: [33, 32],
    76: [-1, 34],
    77: [29, 20, 19, 7],
    78: [15],
    79: [33],
    80: [34],
    81: [29, 34, 35, 16, 18],
    82: [44, 39, 8],
    83: [45, 31],
    84: [12, 1, 32, 33, 36, -1],
    85: [-1, 42],
    86: [6, -1],
    87: [13],
    88: [6, -1],
    89: [-1, 21],
    90: [42],
    91: [-1, 3, 15, 38],
    92: [29, 34, 19],
    93: [33, 36, 12, 1, 32],
    94: [34, 9],
    95: [11, 3, 34, 35, 15, 19, -1, 29, 42],
    96: [-1, 34, 29, 19],
    97: [6, -1],
    98: [3, 15, 38],
    99: [36],
    100: [12],
    101: [-1, 13],
    102: [-1, 17],
    103: [-1, 13],
    104: [-1, 34],
    105: [3, 15],
}
nonterminal_follow = {
    46: [1, 26, 29, 12, 32, 33, 34, 35, 16, 36, 18, 37],
    47: [4, 26],
    48: [15, 26, 38, 3],
    49: [4, 26],
    50: [37],
    51: [37],
    52: [34, 26],
    53: [1, 26, 29, 12, 32, 33, 34, 35, 16, 36, 18, 37],
    54: [1, 26, 29, 12, 32, 33, 34, 35, 16, 36, 18, 37],
    55: [-1],
    56: [12, 1, 32, 33, 26, 36],
    57: [26, 32],
    58: [37],
    59: [26],
    60: [4, 26, 29, 11, 13, 14, 34, 19, 42],
    61: [26],
    62: [26, 13, 42, 14],
    63: [13, 26, 14],
    64: [11, 13, 4, 14, 26, 42],
    65: [0],
    66: [26, 37],
    67: [26],
    68: [3, 4, 15, 26, 38],
    69: [12, 1, 32, 33, 26, 36],
    70: [34, 26],
    71: [42],
    72: [11, 4, 26],
    73: [4, 26],
    74: [3, 15, 26, 38],
    75: [12, 1, 32, 33, 26, 36],
    76: [26],
    77: [6, 37],
    78: [3, 4, 15, 26, 38],
    79: [12, 1, 32, 33, 26, 36],
    80: [6, 37],
    81: [12, 1, 32, 33, 34, 35, 16, 36, 18, 26, 29],
    82: [13, 26, 14],
    83: [37],
    84: [26],
    85: [11, 13, 4, 14, 26, 17],
    86: [26, 37],
    87: [14],
    88: [37],
    89: [42],
    90: [11, 13, 4, 14, 26, 17],
    91: [26],
    92: [11, 13, 4, 14, 34, 26, 19, 29, 42],
    93: [33, 26, 12, 36, 1, 32],
    94: [11, 13, 4, 14, 26, 17],
    95: [4, 26],
    96: [26, 13, 42, 14],
    97: [37],
    98: [15, 26, 38, 3],
    99: [12, 1, 32, 33, 26, 36],
    100: [12, 1, 32, 33, 26, 36],
    101: [14],
    102: [26, 13, 42, 14],
    103: [34, 26],
    104: [37],
    105: [3, 4, 15, 26, 38],
}
rule_first = {
    0: [3, 15, 38],
    1: [-1],
    2: [22],
    3: [3, 15, 38],
    4: [38],
    5: [3, 15],
    6: [33, 1, 36, 12, 32],
    7: [-1],
    8: [38],
    9: [33, 32],
    10: [36],
    11: [12],
    12: [1],
    13: [1],
    14: [32],
    15: [-1],
    16: [12],
    17: [32],
    18: [33],
    19: [21],
    20: [-1],
    21: [29, 34, 35, 16, 18],
    22: [-1],
    23: [32],
    24: [34],
    25: [-1],
    26: [33],
    27: [13],
    28: [-1],
    29: [34],
    30: [34],
    31: [6],
    32: [-1],
    33: [-1],
    34: [13],
    35: [21],
    36: [29],
    37: [29],
    38: [-1],
    39: [34],
    40: [18],
    41: [16],
    42: [43, 5],
    43: [-1],
    44: [29],
    45: [5],
    46: [43],
    47: [35],
    48: [36],
    49: [3],
    50: [15],
    51: [4],
    52: [-1],
    53: [3],
    54: [4],
    55: [11, 34, 19, 29, -1, 42],
    56: [11],
    57: [-1],
    58: [-1],
    59: [11, 34, 19, 29, -1, 42],
    60: [29, 34, 19],
    61: [-1],
    62: [42],
    63: [-1],
    64: [29, 34, 42, -1, 19],
    65: [35],
    66: [3, 15],
    67: [13, 14],
    68: [-1],
    69: [15],
    70: [13],
    71: [-1],
    72: [13, 14],
    73: [17],
    74: [-1],
    75: [39],
    76: [44],
    77: [8],
    78: [29, 34, -1, 19],
    79: [17],
    80: [13],
    81: [45, 31],
    82: [31],
    83: [45],
    84: [10],
    85: [24],
    86: [30],
    87: [29],
    88: [19],
    89: [34],
    90: [42],
    91: [34],
    92: [6],
    93: [-1],
    94: [-1],
    95: [34],
    96: [9],
    97: [34],
    98: [29, 20, 19, 7],
    99: [6],
    100: [-1],
    101: [-1],
    102: [34],
    103: [19],
    104: [29],
    105: [20],
    106: [7],
}
nonterminal_rules = {
    46: [
        "$_gen10 = $match_group",
        "$_gen10 = :_empty",
    ],
    47: [
        "$_gen12 = $rule $_gen13",
        "$_gen12 = :_empty",
    ],
    48: [
        "$lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )",
    ],
    49: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    50: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    51: [
        "$_gen21 = $macro_parameter $_gen22",
        "$_gen21 = :_empty",
    ],
    52: [
        "$regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )",
    ],
    53: [
        "$terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )",
    ],
    54: [
        "$match_group = :lsquare :integer :rsquare -> $1",
        "$match_group = :no_group",
    ],
    55: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    56: [
        "$_gen4 = $lexer_target $_gen4",
        "$_gen4 = :_empty",
    ],
    57: [
        "$regex_partial = :regex :arrow :regex_partial -> RegexPartial( regex=$0, name=$2 )",
    ],
    58: [
        "$_gen9 = $terminal",
        "$_gen9 = :_empty",
    ],
    59: [
        "$_gen11 = $ll1_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    60: [
        "$macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    61: [
        "$_gen16 = $expression_rule $_gen16",
        "$_gen16 = :_empty",
    ],
    62: [
        "$led = :expression_divider $_gen14 -> $1",
    ],
    63: [
        "$expression_rule = $_gen17 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    64: [
        "$_gen14 = $morpheme $_gen14",
        "$_gen14 = :_empty",
    ],
    65: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    66: [
        "$_gen7 = :identifier $_gen8",
        "$_gen7 = :_empty",
    ],
    67: [
        "$_gen2 = $regex_partial $_gen2",
        "$_gen2 = :_empty",
    ],
    68: [
        "$parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )",
    ],
    69: [
        "$lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )",
    ],
    70: [
        "$regex_enumeration_options = :lparen $_gen7 :rparen -> $1",
    ],
    71: [
        "$regex_options = :lbrace $_gen7 :rbrace -> $1",
    ],
    72: [
        "$rule = $_gen14 $_gen15 -> Production( morphemes=$0, ast=$1 )",
    ],
    73: [
        "$_gen13 = :pipe $rule $_gen13",
        "$_gen13 = :_empty",
    ],
    74: [
        "$body_element = $body_element_sub",
    ],
    75: [
        "$lexer_regex = $enumerated_regex",
        "$lexer_regex = :regex $_gen3 :arrow $_gen4 -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    76: [
        "$_gen5 = $regex_enumeration $_gen5",
        "$_gen5 = :_empty",
    ],
    77: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    78: [
        "$parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    79: [
        "$enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )",
    ],
    80: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    81: [
        "$lexer_target = $terminal",
        "$lexer_target = :identifier :lparen $_gen9 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :stack_push",
        "$lexer_target = :action",
        "$lexer_target = :null -> Null(  )",
    ],
    82: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen14 $_gen15 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen14 $_gen15 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    83: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    84: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    85: [
        "$_gen15 = $ast_transform",
        "$_gen15 = :_empty",
    ],
    86: [
        "$_gen8 = :comma :identifier $_gen8",
        "$_gen8 = :_empty",
    ],
    87: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    88: [
        "$_gen22 = :comma $macro_parameter $_gen22",
        "$_gen22 = :_empty",
    ],
    89: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    90: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    91: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    92: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    93: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
        "$lexer_atom = $lexer_partials",
        "$lexer_atom = $lexer_code",
    ],
    94: [
        "$ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    95: [
        "$ll1_rule_rhs = $_gen12",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    96: [
        "$nud = $_gen14",
    ],
    97: [
        "$_gen20 = :comma $ast_parameter $_gen20",
        "$_gen20 = :_empty",
    ],
    98: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    99: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    100: [
        "$lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )",
    ],
    101: [
        "$_gen17 = $binding_power",
        "$_gen17 = :_empty",
    ],
    102: [
        "$_gen18 = $led",
        "$_gen18 = :_empty",
    ],
    103: [
        "$_gen6 = $regex_enumeration_options",
        "$_gen6 = :_empty",
    ],
    104: [
        "$_gen19 = $ast_parameter $_gen20",
        "$_gen19 = :_empty",
    ],
    105: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
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
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[46] and current.id not in nonterminal_first[46]:
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
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[47] and current.id not in nonterminal_first[47]:
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
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'lexer'))
    ctx.nonterminal = "lexer"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 8: # $lexer = :lexer :lbrace $_gen1 :rbrace -> Lexer( atoms=$2 )
        ctx.rule = rules[8]
        ast_parameters = OrderedDict([
            ('atoms', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 38) # :lexer
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[8]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 54: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[54]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 4) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 19) # :nonterminal
        tree.add(t)
        t = expect(ctx, 40) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49]],
      rules[54]
    ))
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 84: # $associativity = :left
        ctx.rule = rules[84]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 10) # :left
        tree.add(t)
        return tree
    elif rule == 85: # $associativity = :right
        ctx.rule = rules[85]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 24) # :right
        tree.add(t)
        return tree
    elif rule == 86: # $associativity = :unary
        ctx.rule = rules[86]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50]],
      rules[86]
    ))
def parse__gen21(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, '_gen21'))
    ctx.nonterminal = "_gen21"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[51] and current.id not in nonterminal_first[51]:
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
def parse_regex_enumeration(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'regex_enumeration'))
    ctx.nonterminal = "regex_enumeration"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $regex_enumeration = :identifier :colon :regex $_gen6 -> RegexEnum( language=$0, regex=$2, options=$3 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('language', 0),
            ('regex', 2),
            ('options', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexEnum', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 0) # :colon
        tree.add(t)
        t = expect(ctx, 32) # :regex
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[29]
    ))
def parse_terminal(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'terminal'))
    ctx.nonterminal = "terminal"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 44: # $terminal = :terminal $_gen10 -> Terminal( name=$0, group=$1 )
        ctx.rule = rules[44]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('group', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Terminal', ast_parameters)
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[44]
    ))
def parse_match_group(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, 'match_group'))
    ctx.nonterminal = "match_group"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $match_group = :lsquare :integer :rsquare -> $1
        ctx.rule = rules[45]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 5) # :lsquare
        tree.add(t)
        t = expect(ctx, 7) # :integer
        tree.add(t)
        t = expect(ctx, 23) # :rsquare
        tree.add(t)
        return tree
    elif rule == 46: # $match_group = :no_group
        ctx.rule = rules[46]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 43) # :no_group
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[54]],
      rules[46]
    ))
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'grammar'))
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
        t = expect(ctx, 22) # :grammar
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[2]
    ))
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
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
def parse_regex_partial(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'regex_partial'))
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
        t = expect(ctx, 32) # :regex
        tree.add(t)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        t = expect(ctx, 27) # :regex_partial
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[17]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = False
    if current != None and current.id in nonterminal_follow[58] and current.id not in nonterminal_first[58]:
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
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[59] and current.id not in nonterminal_first[59]:
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
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 102: # $macro = :identifier :lparen $_gen21 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[102]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen21(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[102]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
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
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $led = :expression_divider $_gen14 -> $1
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 17) # :expression_divider
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[62]],
      rules[79]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
        t = expect(ctx, 14) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 19) # :nonterminal
        tree.add(t)
        t = expect(ctx, 40) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[63]],
      rules[72]
    ))
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[64] and current.id not in nonterminal_first[64]:
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
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 82: # $binding_power_marker = :asterisk
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :asterisk
        tree.add(t)
        return tree
    elif rule == 83: # $binding_power_marker = :dash
        ctx.rule = rules[83]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 45) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[65]],
      rules[83]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[66] and current.id not in nonterminal_first[66]:
        return tree
    if current == None:
        return tree
    if rule == 30: # $_gen7 = :identifier $_gen8
        ctx.rule = rules[30]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[67] and current.id not in nonterminal_first[67]:
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
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 53: # $parser_ll1 = :parser :lbrace $_gen11 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 3) # :parser
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[68]],
      rules[53]
    ))
def parse_lexer_code(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, 'lexer_code'))
    ctx.nonterminal = "lexer_code"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 13: # $lexer_code = :code_start :language :code -> LexerCode( language=$1, code=$2 )
        ctx.rule = rules[13]
        ast_parameters = OrderedDict([
            ('language', 1),
            ('code', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerCode', ast_parameters)
        t = expect(ctx, 1) # :code_start
        tree.add(t)
        t = expect(ctx, 41) # :language
        tree.add(t)
        t = expect(ctx, 28) # :code
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[69]],
      rules[13]
    ))
def parse_regex_enumeration_options(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, 'regex_enumeration_options'))
    ctx.nonterminal = "regex_enumeration_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 34: # $regex_enumeration_options = :lparen $_gen7 :rparen -> $1
        ctx.rule = rules[34]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[70]],
      rules[34]
    ))
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 35: # $regex_options = :lbrace $_gen7 :rbrace -> $1
        ctx.rule = rules[35]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71]],
      rules[35]
    ))
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[72]],
      rules[64]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
        return tree
    if current == None:
        return tree
    if rule == 56: # $_gen13 = :pipe $rule $_gen13
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 11) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[74]],
      rules[3]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
        t = expect(ctx, 32) # :regex
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75]],
      rules[23]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[76] and current.id not in nonterminal_first[76]:
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
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 103: # $macro_parameter = :nonterminal
        ctx.rule = rules[103]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 19) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 104: # $macro_parameter = :terminal
        ctx.rule = rules[104]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        return tree
    elif rule == 105: # $macro_parameter = :string
        ctx.rule = rules[105]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 20) # :string
        tree.add(t)
        return tree
    elif rule == 106: # $macro_parameter = :integer
        ctx.rule = rules[106]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 7) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[77]],
      rules[106]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 69: # $parser_expression = :parser_expression :lbrace $_gen16 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[69]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 15) # :parser_expression
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[69]
    ))
def parse_enumerated_regex(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'enumerated_regex'))
    ctx.nonterminal = "enumerated_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 26: # $enumerated_regex = :regex_enum :lbrace $_gen5 :rbrace :arrow $_gen4 -> EnumeratedRegex( enums=$2, onmatch=$5 )
        ctx.rule = rules[26]
        ast_parameters = OrderedDict([
            ('enums', 2),
            ('onmatch', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('EnumeratedRegex', ast_parameters)
        t = expect(ctx, 33) # :regex_enum
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[79]],
      rules[26]
    ))
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 97: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[97]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 40) # :equals
        tree.add(t)
        t = expect(ctx, 9) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[80]],
      rules[97]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    elif rule == 40: # $lexer_target = :stack_push
        ctx.rule = rules[40]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 18) # :stack_push
        tree.add(t)
        return tree
    elif rule == 41: # $lexer_target = :action
        ctx.rule = rules[41]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :action
        tree.add(t)
        return tree
    elif rule == 47: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[47]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 35) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[47]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 75: # $expression_rule_production = :mixfix_rule_hint $nud $_gen15 $_gen18 $_gen15 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[75]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 39) # :mixfix_rule_hint
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
        t = expect(ctx, 44) # :prefix_rule_hint
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
        t = expect(ctx, 8) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[82]],
      rules[77]
    ))
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(83, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 81: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[81]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 0) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[83]],
      rules[81]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(84, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[84] and current.id not in nonterminal_first[84]:
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
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(85, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = False
    if current != None and current.id in nonterminal_follow[85] and current.id not in nonterminal_first[85]:
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
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(86, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[86] and current.id not in nonterminal_first[86]:
        return tree
    if current == None:
        return tree
    if rule == 31: # $_gen8 = :comma :identifier $_gen8
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 6) # :comma
        tree.add(t)
        tree.listSeparator = t
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(87, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 80: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[87]],
      rules[80]
    ))
def parse__gen22(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(88, '_gen22'))
    ctx.nonterminal = "_gen22"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[88] and current.id not in nonterminal_first[88]:
        return tree
    if current == None:
        return tree
    if rule == 99: # $_gen22 = :comma $macro_parameter $_gen22
        ctx.rule = rules[99]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 6) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen22(ctx)
        tree.add(subtree)
        return tree
    return tree
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
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(90, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 90: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[90]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 42) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[90]],
      rules[90]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(91, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[91] and current.id not in nonterminal_first[91]:
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
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(92, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 87: # $morpheme = :terminal
        ctx.rule = rules[87]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :terminal
        tree.add(t)
        return tree
    elif rule == 88: # $morpheme = :nonterminal
        ctx.rule = rules[88]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 19) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 89: # $morpheme = $macro
        ctx.rule = rules[89]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[92]],
      rules[89]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[47][current.id] if current else -1
    tree = ParseTree(NonTerminal(93, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[93]],
      rules[12]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[48][current.id] if current else -1
    tree = ParseTree(NonTerminal(94, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 95: # $ast_transform_sub = :identifier :lparen $_gen19 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[95]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen19(ctx)
        tree.add(subtree)
        t = expect(ctx, 37) # :rparen
        tree.add(t)
        return tree
    elif rule == 96: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[96]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 9) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[94]],
      rules[96]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[49][current.id] if current else -1
    tree = ParseTree(NonTerminal(95, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
        t = expect(ctx, 35) # :null
        tree.add(t)
        return tree
    elif rule == 66: # $ll1_rule_rhs = $parser
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[95]],
      rules[66]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[50][current.id] if current else -1
    tree = ParseTree(NonTerminal(96, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $nud = $_gen14
        ctx.rule = rules[78]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[96]],
      rules[78]
    ))
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
        t = expect(ctx, 6) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen20(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[52][current.id] if current else -1
    tree = ParseTree(NonTerminal(98, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[98]],
      rules[5]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[53][current.id] if current else -1
    tree = ParseTree(NonTerminal(99, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 48: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[48]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 36) # :mode
        tree.add(t)
        t = expect(ctx, 25) # :langle
        tree.add(t)
        t = expect(ctx, 34) # :identifier
        tree.add(t)
        t = expect(ctx, 2) # :rangle
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[99]],
      rules[48]
    ))
def parse_lexer_partials(ctx):
    current = ctx.tokens.current()
    rule = table[54][current.id] if current else -1
    tree = ParseTree(NonTerminal(100, 'lexer_partials'))
    ctx.nonterminal = "lexer_partials"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 16: # $lexer_partials = :partials :lbrace $_gen2 :rbrace -> RegexPartials( list=$2 )
        ctx.rule = rules[16]
        ast_parameters = OrderedDict([
            ('list', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('RegexPartials', ast_parameters)
        t = expect(ctx, 12) # :partials
        tree.add(t)
        t = expect(ctx, 21) # :lbrace
        tree.add(t)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 26) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[100]],
      rules[16]
    ))
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
def parse__gen18(ctx):
    current = ctx.tokens.current()
    rule = table[56][current.id] if current else -1
    tree = ParseTree(NonTerminal(102, '_gen18'))
    ctx.nonterminal = "_gen18"
    tree.list = False
    if current != None and current.id in nonterminal_follow[102] and current.id not in nonterminal_first[102]:
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
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[57][current.id] if current else -1
    tree = ParseTree(NonTerminal(103, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = False
    if current != None and current.id in nonterminal_follow[103] and current.id not in nonterminal_first[103]:
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
def parse__gen19(ctx):
    current = ctx.tokens.current()
    rule = table[58][current.id] if current else -1
    tree = ParseTree(NonTerminal(104, '_gen19'))
    ctx.nonterminal = "_gen19"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[104] and current.id not in nonterminal_first[104]:
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
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[59][current.id] if current else -1
    tree = ParseTree(NonTerminal(105, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
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
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[105]],
      rules[50]
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
