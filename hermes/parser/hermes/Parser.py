import sys
import inspect
from collections import OrderedDict
from ..Common import *
def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]
def parse(tokens):
  return Parser().parse(tokens)
class Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
    0: 'regex',
    1: 'mode',
    2: 'unary',
    3: 'null',
    4: 'lparen',
    5: 'string',
    6: 'parser_expression',
    7: 'integer',
    8: 'comma',
    9: 'colon',
    10: 'dash',
    11: 'grammar',
    12: 'nonterminal',
    13: 'lexer',
    14: 'code',
    15: 'rparen',
    16: 'equals',
    17: 'expr_rule_hint',
    18: 'mixfix_rule_hint',
    19: 'arrow',
    20: 'prefix_rule_hint',
    21: 'rangle',
    22: 'terminal',
    23: 'parser_ll1',
    24: 'infix_rule_hint',
    25: 'll1_rule_hint',
    26: 'lbrace',
    27: 'left',
    28: 'pipe',
    29: 'right',
    30: 'nonterminal_reference',
    31: 'asterisk',
    32: 'expression_divider',
    33: 'langle',
    34: 'rbrace',
    35: 'identifier',
    'regex': 0,
    'mode': 1,
    'unary': 2,
    'null': 3,
    'lparen': 4,
    'string': 5,
    'parser_expression': 6,
    'integer': 7,
    'comma': 8,
    'colon': 9,
    'dash': 10,
    'grammar': 11,
    'nonterminal': 12,
    'lexer': 13,
    'code': 14,
    'rparen': 15,
    'equals': 16,
    'expr_rule_hint': 17,
    'mixfix_rule_hint': 18,
    'arrow': 19,
    'prefix_rule_hint': 20,
    'rangle': 21,
    'terminal': 22,
    'parser_ll1': 23,
    'infix_rule_hint': 24,
    'll1_rule_hint': 25,
    'lbrace': 26,
    'left': 27,
    'pipe': 28,
    'right': 29,
    'nonterminal_reference': 30,
    'asterisk': 31,
    'expression_divider': 32,
    'langle': 33,
    'rbrace': 34,
    'identifier': 35,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    36: '_gen9',
    37: '_gen11',
    38: 'lexer_target',
    39: 'grammar',
    40: 'lexer_mode',
    41: 'led',
    42: '_gen6',
    43: 'associativity',
    44: '_gen10',
    45: '_gen3',
    46: 'parser_ll1',
    47: 'binding_power_marker',
    48: 'binding_power',
    49: 'nud',
    50: 'll1_rule',
    51: 'macro_parameter',
    52: 'lexer_atom',
    53: '_gen15',
    54: 'ast_transform',
    55: 'body_element_sub',
    56: 'lexer_regex',
    57: 'expression_rule_production',
    58: '_gen17',
    59: '_gen1',
    60: 'expression_rule',
    61: 'parser_expression',
    62: '_gen13',
    63: '_gen0',
    64: 'ast_transform_sub',
    65: '_gen2',
    66: 'ast_parameter',
    67: '_gen12',
    68: 'body_element',
    69: 'parser',
    70: 'macro',
    71: '_gen4',
    72: '_gen5',
    73: '_gen14',
    74: 'll1_rule_rhs',
    75: 'rule',
    76: '_gen8',
    77: 'lexer',
    78: 'morpheme',
    79: '_gen16',
    80: '_gen7',
    81: 'regex_options',
    82: 'precedence',
    '_gen9': 36,
    '_gen11': 37,
    'lexer_target': 38,
    'grammar': 39,
    'lexer_mode': 40,
    'led': 41,
    '_gen6': 42,
    'associativity': 43,
    '_gen10': 44,
    '_gen3': 45,
    'parser_ll1': 46,
    'binding_power_marker': 47,
    'binding_power': 48,
    'nud': 49,
    'll1_rule': 50,
    'macro_parameter': 51,
    'lexer_atom': 52,
    '_gen15': 53,
    'ast_transform': 54,
    'body_element_sub': 55,
    'lexer_regex': 56,
    'expression_rule_production': 57,
    '_gen17': 58,
    '_gen1': 59,
    'expression_rule': 60,
    'parser_expression': 61,
    '_gen13': 62,
    '_gen0': 63,
    'ast_transform_sub': 64,
    '_gen2': 65,
    'ast_parameter': 66,
    '_gen12': 67,
    'body_element': 68,
    'parser': 69,
    'macro': 70,
    '_gen4': 71,
    '_gen5': 72,
    '_gen14': 73,
    'll1_rule_rhs': 74,
    'rule': 75,
    '_gen8': 76,
    'lexer': 77,
    'morpheme': 78,
    '_gen16': 79,
    '_gen7': 80,
    'regex_options': 81,
    'precedence': 82,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, 37, -1, 37, -1, -1, 36, -1, -1, 37, -1, -1, 37, -1, -1, -1, -1, -1, 37, 36],
    [-1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1],
    [-1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1],
    [-1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, 61, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, 38, -1, -1, -1, -1, -1, 39, -1, -1, 39, -1, -1, -1, 39, -1, 39, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1],
    [-1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, 54, -1, 54, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, 54],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 81, -1, 82, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [11, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, 52, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, 50, -1],
    [-1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, 71],
    [8, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73],
    [-1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, 16],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67],
    [-1, -1, -1, 41, -1, -1, 42, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, 35, -1, -1, 35, 42, -1, 35, -1, -1, 35, -1, -1, -1, -1, -1, 35, 35],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, 40, -1, -1, 40, -1, -1, 40, -1, -1, 40, -1, -1, -1, -1, -1, 40, 40],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, 32, -1, -1, -1, -1, -1, 33, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65],
    [-1, -1, -1, -1, -1, 74, -1, 74, -1, -1, -1, -1, 74, -1, -1, 77, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, 31, -1, -1, 31, -1, -1, 31, -1, -1, 31, -1, -1, -1, -1, -1, 31, 31],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1],
  ]
  TERMINAL_REGEX = 0
  TERMINAL_MODE = 1
  TERMINAL_UNARY = 2
  TERMINAL_NULL = 3
  TERMINAL_LPAREN = 4
  TERMINAL_STRING = 5
  TERMINAL_PARSER_EXPRESSION = 6
  TERMINAL_INTEGER = 7
  TERMINAL_COMMA = 8
  TERMINAL_COLON = 9
  TERMINAL_DASH = 10
  TERMINAL_GRAMMAR = 11
  TERMINAL_NONTERMINAL = 12
  TERMINAL_LEXER = 13
  TERMINAL_CODE = 14
  TERMINAL_RPAREN = 15
  TERMINAL_EQUALS = 16
  TERMINAL_EXPR_RULE_HINT = 17
  TERMINAL_MIXFIX_RULE_HINT = 18
  TERMINAL_ARROW = 19
  TERMINAL_PREFIX_RULE_HINT = 20
  TERMINAL_RANGLE = 21
  TERMINAL_TERMINAL = 22
  TERMINAL_PARSER_LL1 = 23
  TERMINAL_INFIX_RULE_HINT = 24
  TERMINAL_LL1_RULE_HINT = 25
  TERMINAL_LBRACE = 26
  TERMINAL_LEFT = 27
  TERMINAL_PIPE = 28
  TERMINAL_RIGHT = 29
  TERMINAL_NONTERMINAL_REFERENCE = 30
  TERMINAL_ASTERISK = 31
  TERMINAL_EXPRESSION_DIVIDER = 32
  TERMINAL_LANGLE = 33
  TERMINAL_RBRACE = 34
  TERMINAL_IDENTIFIER = 35
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 35
  def isNonTerminal(self, id):
    return 36 <= id <= 82
  def parse(self, tokens):
    self.tokens = tokens
    tree = self.parse_grammar()
    if self.tokens.current() != None:
      raise SyntaxError( 'Finished parsing without consuming all tokens.' )
    return tree
  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError( 'No more tokens.  Expecting %s' % (self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError( 'Unexpected symbol (line %d, col %d) when parsing %s.  Expected %s, got %s.' %(currentToken.line, currentToken.col, whosdaddy(), self.terminals[terminalId], currentToken) )
    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) )
    return currentToken
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [17, 28, 19, 4, 34, 25]) and \
       (current.getId() not in [-1, 12, 22, 35]):
      return tree
    if current == None:
      return tree
    if rule == 36: # $_gen9 = $morpheme $_gen9
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [34]) and \
       (current.getId() not in [4, 17, -1]):
      return tree
    if current == None:
      return tree
    if rule == 43: # $_gen11 = $expression_rule $_gen11
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen11()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 19: # $lexer_target = :terminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # :terminal
      tree.add(t)
      return tree
    elif rule == 22: # $lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(35) # :identifier
      tree.add(t)
      t = self.expect(4) # :lparen
      tree.add(t)
      subtree = self.parse__gen5()
      tree.add( subtree )
      t = self.expect(15) # :rparen
      tree.add(t)
      return tree
    elif rule == 23: # $lexer_target = :null -> Null(  )
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(3) # :null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 4: # $grammar = :grammar :lbrace $_gen0 :rbrace $_gen1 -> Grammar( body=$2, code=$4 )
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(11) # :grammar
      tree.add(t)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 24: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen2 :rbrace -> Mode( name=$2, atoms=$5 )
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(1) # :mode
      tree.add(t)
      t = self.expect(33) # :langle
      tree.add(t)
      t = self.expect(35) # :identifier
      tree.add(t)
      t = self.expect(21) # :rangle
      tree.add(t)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_led(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 55: # $led = :expression_divider $_gen9 -> $1
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(32) # :expression_divider
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [34]) and \
       (current.getId() not in [-1, 25]):
      return tree
    if current == None:
      return tree
    if rule == 27: # $_gen6 = $ll1_rule $_gen6
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $associativity = :left
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # :left
      tree.add(t)
      return tree
    elif rule == 61: # $associativity = :right
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # :right
      tree.add(t)
      return tree
    elif rule == 62: # $associativity = :unary
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(2) # :unary
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = False
    if current != None and \
       (current.getId() in [17, 28, 32, 4, 34, 25]) and \
       (current.getId() not in [-1, 19]):
      return tree
    if current == None:
      return tree
    if rule == 38: # $_gen10 = $ast_transform
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = False
    if current != None and \
       (current.getId() in [19]) and \
       (current.getId() not in [26, -1]):
      return tree
    if current == None:
      return tree
    if rule == 13: # $_gen3 = $regex_options
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(23) # :parser_ll1
      tree.add(t)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen6()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 58: # $binding_power_marker = :asterisk
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(31) # :asterisk
      tree.add(t)
      return tree
    elif rule == 59: # $binding_power_marker = :dash
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(10) # :dash
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $binding_power = :lparen $precedence :rparen -> $1
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(4) # :lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(15) # :rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_nud(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 54: # $nud = $_gen9
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 30: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(25) # :ll1_rule_hint
      tree.add(t)
      t = self.expect(12) # :nonterminal
      tree.add(t)
      t = self.expect(16) # :equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $macro_parameter = :nonterminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(12) # :nonterminal
      tree.add(t)
      return tree
    elif rule == 80: # $macro_parameter = :terminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # :terminal
      tree.add(t)
      return tree
    elif rule == 81: # $macro_parameter = :string
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(5) # :string
      tree.add(t)
      return tree
    elif rule == 82: # $macro_parameter = :integer
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(7) # :integer
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 11: # $lexer_atom = $lexer_regex
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    elif rule == 12: # $lexer_atom = $lexer_mode
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen15(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [15]) and \
       (current.getId() not in [8, -1]):
      return tree
    if current == None:
      return tree
    if rule == 68: # $_gen15 = :comma $ast_parameter $_gen15
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # :comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 66: # $ast_transform = :arrow $ast_transform_sub -> $1
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(19) # :arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 6: # $body_element_sub = $lexer
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    elif rule == 7: # $body_element_sub = $parser
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 15: # $lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )
      astParameters = OrderedDict([
        ('regex', 0),
        ('options', 1),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(0) # :regex
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(19) # :arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_expression_rule_production(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 51: # $expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
      astParameters = OrderedDict([
        ('nud', 1),
        ('nud_ast', 2),
        ('led', 3),
        ('ast', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('MixfixProduction', astParameters)
      t = self.expect(18) # :mixfix_rule_hint
      tree.add(t)
      subtree = self.parse_nud()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      subtree = self.parse__gen13()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    elif rule == 52: # $expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('PrefixProduction', astParameters)
      t = self.expect(20) # :prefix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    elif rule == 53: # $expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('InfixProduction', astParameters)
      t = self.expect(24) # :infix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen17(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [15]) and \
       (current.getId() not in [8, -1]):
      return tree
    if current == None:
      return tree
    if rule == 75: # $_gen17 = :comma $macro_parameter $_gen17
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # :comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current != None and \
       (current.getId() in [-1]) and \
       (current.getId() not in [14, -1]):
      return tree
    if current == None:
      return tree
    if rule == 2: # $_gen1 = :code
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(14) # :code
      tree.add(t)
      return tree
    return tree
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 48: # $expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
      astParameters = OrderedDict([
        ('precedence', 0),
        ('nonterminal', 2),
        ('production', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      subtree = self.parse__gen12()
      tree.add( subtree )
      t = self.expect(17) # :expr_rule_hint
      tree.add(t)
      t = self.expect(12) # :nonterminal
      tree.add(t)
      t = self.expect(16) # :equals
      tree.add(t)
      subtree = self.parse_expression_rule_production()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(6) # :parser_expression
      tree.add(t)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen11()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = False
    if current != None and \
       (current.getId() in [4, 17, 19, 34]) and \
       (current.getId() not in [32, -1]):
      return tree
    if current == None:
      return tree
    if rule == 49: # $_gen13 = $led
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_led()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [34]) and \
       (current.getId() not in [6, -1, 13, 23]):
      return tree
    if current == None:
      return tree
    if rule == 0: # $_gen0 = $body_element $_gen0
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 71: # $ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(35) # :identifier
      tree.add(t)
      t = self.expect(4) # :lparen
      tree.add(t)
      subtree = self.parse__gen14()
      tree.add( subtree )
      t = self.expect(15) # :rparen
      tree.add(t)
      return tree
    elif rule == 72: # $ast_transform_sub = :nonterminal_reference
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(30) # :nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [34]) and \
       (current.getId() not in [-1, 0, 1]):
      return tree
    if current == None:
      return tree
    if rule == 8: # $_gen2 = $lexer_atom $_gen2
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen2()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 73: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(35) # :identifier
      tree.add(t)
      t = self.expect(16) # :equals
      tree.add(t)
      t = self.expect(30) # :nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = False
    if current != None and \
       (current.getId() in [17]) and \
       (current.getId() not in [4, -1]):
      return tree
    if current == None:
      return tree
    if rule == 46: # $_gen12 = $binding_power
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_binding_power()
      tree.add( subtree )
      return tree
    return tree
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 5: # $body_element = $body_element_sub
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 25: # $parser = $parser_ll1
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    elif rule == 26: # $parser = $parser_expression
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(35) # :identifier
      tree.add(t)
      t = self.expect(4) # :lparen
      tree.add(t)
      subtree = self.parse__gen16()
      tree.add( subtree )
      t = self.expect(15) # :rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(71, self.nonterminals[71]))
    tree.list = 'nlist'
    if current != None and \
       (current.getId() in [34]) and \
       (current.getId() not in [-1, 35]):
      return tree
    if current == None:
      return tree
    if rule == 16: # $_gen4 = :identifier $_gen4
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(35) # :identifier
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(72, self.nonterminals[72]))
    tree.list = False
    if current != None and \
       (current.getId() in [15]) and \
       (current.getId() not in [22, -1]):
      return tree
    if current == None:
      return tree
    if rule == 20: # $_gen5 = :terminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # :terminal
      tree.add(t)
      return tree
    return tree
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(73, self.nonterminals[73]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [15]) and \
       (current.getId() not in [-1, 35]):
      return tree
    if current == None:
      return tree
    if rule == 67: # $_gen14 = $ast_parameter $_gen15
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(74, self.nonterminals[74]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 35: # $ll1_rule_rhs = $_gen7
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    elif rule == 41: # $ll1_rule_rhs = :null -> NullProduction(  )
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(3) # :null
      tree.add(t)
      return tree
    elif rule == 42: # $ll1_rule_rhs = $parser
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(75, self.nonterminals[75]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )
      astParameters = OrderedDict([
        ('morphemes', 0),
        ('ast', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('Production', astParameters)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(76, self.nonterminals[76]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [34, 25]) and \
       (current.getId() not in [-1, 28]):
      return tree
    if current == None:
      return tree
    if rule == 32: # $_gen8 = :pipe $rule $_gen8
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(28) # :pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[41][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(77, self.nonterminals[77]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 10: # $lexer = :lexer :lbrace $_gen2 :rbrace -> Lexer( atoms=$2 )
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(13) # :lexer
      tree.add(t)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[42][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(78, self.nonterminals[78]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $morpheme = :terminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # :terminal
      tree.add(t)
      return tree
    elif rule == 64: # $morpheme = :nonterminal
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(12) # :nonterminal
      tree.add(t)
      return tree
    elif rule == 65: # $morpheme = $macro
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen16(self):
    current = self.tokens.current()
    rule = self.table[43][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(79, self.nonterminals[79]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [15]) and \
       (current.getId() not in [5, -1, 12, 22, 7]):
      return tree
    if current == None:
      return tree
    if rule == 74: # $_gen16 = $macro_parameter $_gen17
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[44][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(80, self.nonterminals[80]))
    tree.list = 'slist'
    if current != None and \
       (current.getId() in [34, 25]) and \
       (current.getId() not in [28, -1, 12, 22, 19, 35]):
      return tree
    if current == None:
      return tree
    if rule == 31: # $_gen7 = $rule $_gen8
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[45][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(81, self.nonterminals[81]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 18: # $regex_options = :lbrace $_gen4 :rbrace -> $1
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(26) # :lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(34) # :rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[46][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(82, self.nonterminals[82]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 57: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
      astParameters = OrderedDict([
        ('marker', 0),
        ('associativity', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Precedence', astParameters)
      subtree = self.parse_binding_power_marker()
      tree.add( subtree )
      t = self.expect(9) # :colon
      tree.add(t)
      subtree = self.parse_associativity()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
if __name__ == '__main__':
    import argparse
    import json
    cli_parser = argparse.ArgumentParser(description='Grammar Parser')
    cli_parser.add_argument('--color', action='store_true', help="Print output in terminal colors")
    cli_parser.add_argument('--file')
    cli_parser.add_argument('--out', default='ast', choices=['ast', 'parsetree'])
    cli_parser.add_argument('--stdin', action='store_true')
    cli = cli_parser.parse_args()
    if (not cli.file and not cli.stdin) or (cli.file and cli.stdin):
      sys.exit('Either --file=<path> or --stdin required, but not both')
    cli.file = open(cli.file) if cli.file else sys.stdin
    json_tokens = json.loads(cli.file.read())
    cli.file.close()
    tokens = TokenStream()
    for json_token in json_tokens:
        tokens.append(Terminal(
            Parser.terminals[json_token['terminal']],
            json_token['terminal'],
            json_token['source_string'],
            json_token['resource'],
            json_token['line'],
            json_token['col']
        ))
    try:
        tree = parse(tokens)
        if cli.out == 'parsetree':
          print(ParseTreePrettyPrintable(tree, color=cli.color))
        else:
          print(AstPrettyPrintable(tree.toAst(), color=cli.color))
    except SyntaxError as error:
        print(error)
