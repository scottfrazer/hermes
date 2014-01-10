import sys, inspect
from collections import OrderedDict
from hermes.parser.ParserCommon import *
def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]
def parse( iterator, entry ):
  p = grammar_Parser()
  return p.parse(iterator, entry)
class grammar_Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
    0: 'dash',
    1: 'nonterminal',
    2: 'rparen',
    3: 'rbrace',
    4: 'arrow',
    5: 'lexer',
    6: 'grammar',
    7: 'expression_divider',
    8: 'comma',
    9: 'right',
    10: 'mode',
    11: 'parser_expression',
    12: 'equals',
    13: 'unary',
    14: 'langle',
    15: 'lbrace',
    16: 'rangle',
    17: 'lparen',
    18: 'code',
    19: 'nonterminal_reference',
    20: 'identifier',
    21: 'colon',
    22: 'll1_rule_hint',
    23: 'null',
    24: 'terminal',
    25: 'regex',
    26: 'parser_ll1',
    27: 'asterisk',
    28: 'expr_rule_hint',
    29: 'left',
    30: 'pipe',
    'dash': 0,
    'nonterminal': 1,
    'rparen': 2,
    'rbrace': 3,
    'arrow': 4,
    'lexer': 5,
    'grammar': 6,
    'expression_divider': 7,
    'comma': 8,
    'right': 9,
    'mode': 10,
    'parser_expression': 11,
    'equals': 12,
    'unary': 13,
    'langle': 14,
    'lbrace': 15,
    'rangle': 16,
    'lparen': 17,
    'code': 18,
    'nonterminal_reference': 19,
    'identifier': 20,
    'colon': 21,
    'll1_rule_hint': 22,
    'null': 23,
    'terminal': 24,
    'regex': 25,
    'parser_ll1': 26,
    'asterisk': 27,
    'expr_rule_hint': 28,
    'left': 29,
    'pipe': 30,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    31: 'parser',
    32: 'expression_rule',
    33: '_gen16',
    34: '_gen17',
    35: '_gen1',
    36: '_gen5',
    37: 'expression_rule_rhs',
    38: '_gen12',
    39: '_gen6',
    40: '_gen14',
    41: '_gen15',
    42: '_gen8',
    43: 'lexer_target',
    44: '_gen9',
    45: 'lexer_atom',
    46: 'ast_transform',
    47: '_gen2',
    48: '_gen3',
    49: '_gen7',
    50: 'morpheme',
    51: '_gen13',
    52: 'precedence',
    53: '_gen4',
    54: '_gen0',
    55: 'binding_power_marker',
    56: 'lexer_regex',
    57: 'parser_expression',
    58: 'nud_expression',
    59: 'll1_rule',
    60: 'body_element_sub',
    61: 'rule',
    62: 'macro',
    63: 'll1_rule_rhs',
    64: 'led_expression',
    65: '_gen10',
    66: 'grammar',
    67: 'ast_parameter',
    68: 'ast_transform_sub',
    69: 'lexer_mode',
    70: '_gen11',
    71: 'binding_power',
    72: 'parser_ll1',
    73: 'lexer',
    74: 'body_element',
    75: 'regex_options',
    76: 'macro_parameter',
    77: 'associativity',
    'parser': 31,
    'expression_rule': 32,
    '_gen16': 33,
    '_gen17': 34,
    '_gen1': 35,
    '_gen5': 36,
    'expression_rule_rhs': 37,
    '_gen12': 38,
    '_gen6': 39,
    '_gen14': 40,
    '_gen15': 41,
    '_gen8': 42,
    'lexer_target': 43,
    '_gen9': 44,
    'lexer_atom': 45,
    'ast_transform': 46,
    '_gen2': 47,
    '_gen3': 48,
    '_gen7': 49,
    'morpheme': 50,
    '_gen13': 51,
    'precedence': 52,
    '_gen4': 53,
    '_gen0': 54,
    'binding_power_marker': 55,
    'lexer_regex': 56,
    'parser_expression': 57,
    'nud_expression': 58,
    'll1_rule': 59,
    'body_element_sub': 60,
    'rule': 61,
    'macro': 62,
    'll1_rule_rhs': 63,
    'led_expression': 64,
    '_gen10': 65,
    'grammar': 66,
    'ast_parameter': 67,
    'ast_transform_sub': 68,
    'lexer_mode': 69,
    '_gen11': 70,
    'binding_power': 71,
    'parser_ll1': 72,
    'lexer': 73,
    'body_element': 74,
    'regex_options': 75,
    'macro_parameter': 76,
    'associativity': 77,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1],
    [-1, 3, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1],
    [-1, -1, 76, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 77, -1, 77, 77, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, 77, -1, -1, -1, 77, -1, -1, -1, 77, -1, 77],
    [-1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, 73],
    [-1, 67, -1, 4, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, 4, -1, 67, -1, -1, -1, -1, -1, 67],
    [-1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 55, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 21, -1, 23, 23, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, 21, -1, 23, -1, 21, -1, -1, -1, 23, -1, 23],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, 0, 27, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 35, 32, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, 35, -1, 35],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 61, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, 50],
    [-1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 60, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, 60],
    [13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1],
    [-1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 24, -1, 2, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1],
    [30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 37, -1, 37, 37, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, 37, -1, -1, -1, 37, -1, -1, -1, 37, -1, 37],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1],
    [-1, 53, -1, 53, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, 53, -1, 53, -1, -1, -1, -1, -1, 53],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 42, -1, 42, 42, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, 42, 48, 42, -1, 45, -1, -1, -1, 42],
    [-1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1],
    [-1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 7, -1, 7, 7, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, 7, -1, -1, -1, 7, -1, -1, -1, 7, -1, 7],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1],
  ]
  TERMINAL_DASH = 0
  TERMINAL_NONTERMINAL = 1
  TERMINAL_RPAREN = 2
  TERMINAL_RBRACE = 3
  TERMINAL_ARROW = 4
  TERMINAL_LEXER = 5
  TERMINAL_GRAMMAR = 6
  TERMINAL_EXPRESSION_DIVIDER = 7
  TERMINAL_COMMA = 8
  TERMINAL_RIGHT = 9
  TERMINAL_MODE = 10
  TERMINAL_PARSER_EXPRESSION = 11
  TERMINAL_EQUALS = 12
  TERMINAL_UNARY = 13
  TERMINAL_LANGLE = 14
  TERMINAL_LBRACE = 15
  TERMINAL_RANGLE = 16
  TERMINAL_LPAREN = 17
  TERMINAL_CODE = 18
  TERMINAL_NONTERMINAL_REFERENCE = 19
  TERMINAL_IDENTIFIER = 20
  TERMINAL_COLON = 21
  TERMINAL_LL1_RULE_HINT = 22
  TERMINAL_NULL = 23
  TERMINAL_TERMINAL = 24
  TERMINAL_REGEX = 25
  TERMINAL_PARSER_LL1 = 26
  TERMINAL_ASTERISK = 27
  TERMINAL_EXPR_RULE_HINT = 28
  TERMINAL_LEFT = 29
  TERMINAL_PIPE = 30
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 30
  def isNonTerminal(self, id):
    return 31 <= id <= 77
  def parse(self, tokens):
    self.tokens = tokens
    self.start = 'GRAMMAR'
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
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(31, self.nonterminals[31]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 5:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    elif rule == 78:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(32, self.nonterminals[32]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 47:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      t = self.expect(28) # expr_rule_hint
      tree.add(t)
      t = self.expect(1) # nonterminal
      tree.add(t)
      t = self.expect(12) # equals
      tree.add(t)
      subtree = self.parse__gen11()
      tree.add( subtree )
      return tree
    elif rule == 71:
      astParameters = OrderedDict([
        ('precedence', 0),
        ('nonterminal', 2),
        ('morphemes', 4),
        ('ast', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionOperatorRule', astParameters)
      subtree = self.parse_binding_power()
      tree.add( subtree )
      t = self.expect(28) # expr_rule_hint
      tree.add(t)
      t = self.expect(1) # nonterminal
      tree.add(t)
      t = self.expect(12) # equals
      tree.add(t)
      subtree = self.parse__gen8()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen16(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(33, self.nonterminals[33]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2]):
      return tree
    if current == None:
      return tree
    if rule == 3:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen17(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(34, self.nonterminals[34]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2]):
      return tree
    if current == None:
      return tree
    if rule == 6:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # comma
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
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(35, self.nonterminals[35]))
    tree.list = False
    if current != None and (current.getId() in [-1]):
      return tree
    if current == None:
      return tree
    if rule == 20:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(18) # code
      tree.add(t)
      return tree
    return tree
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 40:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen5()
      tree.add( subtree )
      return tree
    return tree
  def parse_expression_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = False
    if current == None:
      return tree
    if rule == 77:
      astParameters = OrderedDict([
        ('nud', 0),
        ('led', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionProduction', astParameters)
      subtree = self.parse_nud_expression()
      tree.add( subtree )
      subtree = self.parse__gen13()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = 'slist'
    if current != None and (current.getId() in [28, 17, 3]):
      return tree
    if current == None:
      return tree
    if rule == 73:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(30) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_expression_rule_rhs()
      tree.add( subtree )
      subtree = self.parse__gen12()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = 'slist'
    if current != None and (current.getId() in [3, 22]):
      return tree
    if current == None:
      return tree
    if rule == 67:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2]):
      return tree
    if current == None:
      return tree
    if rule == 52:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen15(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2]):
      return tree
    if current == None:
      return tree
    if rule == 54:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3, 22, 17, 4, 28, 7, 30]):
      return tree
    if current == None:
      return tree
    if rule == 21:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(23) # null
      tree.add(t)
      return tree
    elif rule == 27:
      astParameters = OrderedDict([
        ('name', 0),
      ])
      tree.astTransform = AstTransformNodeCreator('Terminal', astParameters)
      t = self.expect(24) # terminal
      tree.add(t)
      return tree
    elif rule == 44:
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(20) # identifier
      tree.add(t)
      t = self.expect(17) # lparen
      tree.add(t)
      t = self.expect(24) # terminal
      tree.add(t)
      t = self.expect(2) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = False
    if current != None and (current.getId() in [17, 3, 30, 28, 7, 22]):
      return tree
    if current == None:
      return tree
    if rule == 32:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 31:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    elif rule == 56:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 38:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(4) # arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 57:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen2()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = False
    if current != None and (current.getId() in [4]):
      return tree
    if current == None:
      return tree
    if rule == 1:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = 'slist'
    if current != None and (current.getId() in [3, 22]):
      return tree
    if current == None:
      return tree
    if rule == 50:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(30) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    return tree
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 8:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(1) # nonterminal
      tree.add(t)
      return tree
    elif rule == 59:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    elif rule == 69:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(24) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current != None and (current.getId() in [17, 28, 30, 3]):
      return tree
    if current == None:
      return tree
    if rule == 46:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_led_expression()
      tree.add( subtree )
      return tree
    return tree
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 13:
      astParameters = OrderedDict([
        ('marker', 0),
        ('associativity', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Precedence', astParameters)
      subtree = self.parse_binding_power_marker()
      tree.add( subtree )
      t = self.expect(21) # colon
      tree.add(t)
      subtree = self.parse_associativity()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 22:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(20) # identifier
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 2:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 28:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # asterisk
      tree.add(t)
      return tree
    elif rule == 30:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(0) # dash
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 36:
      astParameters = OrderedDict([
        ('regex', 0),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(25) # regex
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(4) # arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 58:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(11) # parser_expression
      tree.add(t)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen10()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_nud_expression(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = False
    if current == None:
      return tree
    if rule == 37:
      astParameters = OrderedDict([
        ('morphemes', 0),
        ('ast', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('NudExpression', astParameters)
      subtree = self.parse__gen8()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 26:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(22) # ll1_rule_hint
      tree.add(t)
      t = self.expect(1) # nonterminal
      tree.add(t)
      t = self.expect(12) # equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 19:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 41:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = False
    if current == None:
      return tree
    if rule == 53:
      astParameters = OrderedDict([
        ('morphemes', 0),
        ('ast', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('Production', astParameters)
      subtree = self.parse__gen8()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 15:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(20) # identifier
      tree.add(t)
      t = self.expect(17) # lparen
      tree.add(t)
      subtree = self.parse__gen16()
      tree.add( subtree )
      t = self.expect(2) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = False
    if current == None:
      return tree
    if rule == 42:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    elif rule == 45:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 48:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(23) # null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_led_expression(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 63:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LedExpression', astParameters)
      t = self.expect(7) # expression_divider
      tree.add(t)
      subtree = self.parse__gen8()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 68:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    return tree
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 39:
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(6) # grammar
      tree.add(t)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 49:
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(20) # identifier
      tree.add(t)
      t = self.expect(12) # equals
      tree.add(t)
      t = self.expect(19) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 66:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(20) # identifier
      tree.add(t)
      t = self.expect(17) # lparen
      tree.add(t)
      subtree = self.parse__gen14()
      tree.add( subtree )
      t = self.expect(2) # rparen
      tree.add(t)
      return tree
    elif rule == 70:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(19) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 62:
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(10) # mode
      tree.add(t)
      t = self.expect(14) # langle
      tree.add(t)
      t = self.expect(20) # identifier
      tree.add(t)
      t = self.expect(16) # rangle
      tree.add(t)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = 'slist'
    if current != None and (current.getId() in [28, 17, 3]):
      return tree
    if current == None:
      return tree
    if rule == 7:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule_rhs()
      tree.add( subtree )
      subtree = self.parse__gen12()
      tree.add( subtree )
      return tree
    return tree
  def parse_binding_power(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(71, self.nonterminals[71]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 65:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(17) # lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(2) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[41][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(72, self.nonterminals[72]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 9:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(26) # parser_ll1
      tree.add(t)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen5()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[42][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(73, self.nonterminals[73]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 33:
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(5) # lexer
      tree.add(t)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[43][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(74, self.nonterminals[74]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 16:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[44][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(75, self.nonterminals[75]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 17:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(15) # lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[45][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(76, self.nonterminals[76]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 64:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(1) # nonterminal
      tree.add(t)
      return tree
    elif rule == 74:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(24) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[46][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(77, self.nonterminals[77]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 29:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # left
      tree.add(t)
      return tree
    elif rule == 43:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(13) # unary
      tree.add(t)
      return tree
    elif rule == 72:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(9) # right
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
