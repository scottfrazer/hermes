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
    0: 'asterisk',
    1: 'rparen',
    2: 'rangle',
    3: 'dash',
    4: 'identifier',
    5: 'infix_rule_hint',
    6: 'left',
    7: 'grammar',
    8: 'regex',
    9: 'parser_expression',
    10: 'expr_rule_hint',
    11: 'langle',
    12: 'right',
    13: 'expression_divider',
    14: 'lbrace',
    15: 'unary',
    16: 'mixfix_rule_hint',
    17: 'arrow',
    18: 'lexer',
    19: 'lparen',
    20: 'null',
    21: 'colon',
    22: 'equals',
    23: 'll1_rule_hint',
    24: 'mode',
    25: 'terminal',
    26: 'code',
    27: 'nonterminal',
    28: 'prefix_rule_hint',
    29: 'comma',
    30: 'nonterminal_reference',
    31: 'parser_ll1',
    32: 'rbrace',
    33: 'pipe',
    'asterisk': 0,
    'rparen': 1,
    'rangle': 2,
    'dash': 3,
    'identifier': 4,
    'infix_rule_hint': 5,
    'left': 6,
    'grammar': 7,
    'regex': 8,
    'parser_expression': 9,
    'expr_rule_hint': 10,
    'langle': 11,
    'right': 12,
    'expression_divider': 13,
    'lbrace': 14,
    'unary': 15,
    'mixfix_rule_hint': 16,
    'arrow': 17,
    'lexer': 18,
    'lparen': 19,
    'null': 20,
    'colon': 21,
    'equals': 22,
    'll1_rule_hint': 23,
    'mode': 24,
    'terminal': 25,
    'code': 26,
    'nonterminal': 27,
    'prefix_rule_hint': 28,
    'comma': 29,
    'nonterminal_reference': 30,
    'parser_ll1': 31,
    'rbrace': 32,
    'pipe': 33,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    34: 'rule',
    35: '_gen7',
    36: 'macro_parameter',
    37: 'body_element_sub',
    38: 'lexer_mode',
    39: 'grammar',
    40: 'lexer_atom',
    41: 'expression_rule_production',
    42: 'ast_parameter',
    43: '_gen10',
    44: '_gen14',
    45: '_gen3',
    46: 'ast_transform_sub',
    47: '_gen15',
    48: 'lexer_regex',
    49: 'parser',
    50: '_gen8',
    51: '_gen1',
    52: '_gen5',
    53: 'expression_rule',
    54: 'nud',
    55: 'body_element',
    56: 'lexer',
    57: 'parser_expression',
    58: '_gen4',
    59: 'lexer_target',
    60: '_gen17',
    61: 'morpheme',
    62: 'led',
    63: '_gen9',
    64: 'll1_rule',
    65: '_gen11',
    66: '_gen13',
    67: '_gen2',
    68: 'associativity',
    69: '_gen0',
    70: 'macro',
    71: 'parser_ll1',
    72: 'precedence',
    73: '_gen6',
    74: 'ast_transform',
    75: 'll1_rule_rhs',
    76: 'binding_power',
    77: 'regex_options',
    78: '_gen12',
    79: '_gen16',
    80: 'binding_power_marker',
    'rule': 34,
    '_gen7': 35,
    'macro_parameter': 36,
    'body_element_sub': 37,
    'lexer_mode': 38,
    'grammar': 39,
    'lexer_atom': 40,
    'expression_rule_production': 41,
    'ast_parameter': 42,
    '_gen10': 43,
    '_gen14': 44,
    '_gen3': 45,
    'ast_transform_sub': 46,
    '_gen15': 47,
    'lexer_regex': 48,
    'parser': 49,
    '_gen8': 50,
    '_gen1': 51,
    '_gen5': 52,
    'expression_rule': 53,
    'nud': 54,
    'body_element': 55,
    'lexer': 56,
    'parser_expression': 57,
    '_gen4': 58,
    'lexer_target': 59,
    '_gen17': 60,
    'morpheme': 61,
    'led': 62,
    '_gen9': 63,
    'll1_rule': 64,
    '_gen11': 65,
    '_gen13': 66,
    '_gen2': 67,
    'associativity': 68,
    '_gen0': 69,
    'macro': 70,
    'parser_ll1': 71,
    'precedence': 72,
    '_gen6': 73,
    'ast_transform': 74,
    'll1_rule_rhs': 75,
    'binding_power': 76,
    'regex_options': 77,
    '_gen12': 78,
    '_gen16': 79,
    'binding_power_marker': 80,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, 32, -1, 32, -1, 32, -1, -1, -1, -1, 32, 32],
    [-1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, 42, -1, 42, -1, 42, -1, -1, -1, -1, 42, 42],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, 5, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 61, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, 1, -1, -1, -1, 66, -1, 1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, 1, 1],
    [-1, 55, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1],
    [-1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, 47, 45],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1],
    [-1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 64, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, 64, -1, 64, -1, -1, -1, -1, -1, 64, -1, 64, -1, -1, -1, -1, 64, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1],
    [-1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, -1],
    [-1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, 62, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 72, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, 35, -1, 35, -1, -1, -1, 35, -1, 72, -1, 72, -1, -1, -1, -1, 35, 35],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, 80, -1, -1, -1, 12, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, 31, -1],
    [-1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, 20, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, 73, -1],
    [-1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1],
    [59, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 10, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, 17, -1, -1, 10, -1, 10, -1, 10, -1, -1, -1, 24, 10, 10],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, 37, -1, -1, -1, -1, -1, -1],
    [56, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
  ]
  TERMINAL_ASTERISK = 0
  TERMINAL_RPAREN = 1
  TERMINAL_RANGLE = 2
  TERMINAL_DASH = 3
  TERMINAL_IDENTIFIER = 4
  TERMINAL_INFIX_RULE_HINT = 5
  TERMINAL_LEFT = 6
  TERMINAL_GRAMMAR = 7
  TERMINAL_REGEX = 8
  TERMINAL_PARSER_EXPRESSION = 9
  TERMINAL_EXPR_RULE_HINT = 10
  TERMINAL_LANGLE = 11
  TERMINAL_RIGHT = 12
  TERMINAL_EXPRESSION_DIVIDER = 13
  TERMINAL_LBRACE = 14
  TERMINAL_UNARY = 15
  TERMINAL_MIXFIX_RULE_HINT = 16
  TERMINAL_ARROW = 17
  TERMINAL_LEXER = 18
  TERMINAL_LPAREN = 19
  TERMINAL_NULL = 20
  TERMINAL_COLON = 21
  TERMINAL_EQUALS = 22
  TERMINAL_LL1_RULE_HINT = 23
  TERMINAL_MODE = 24
  TERMINAL_TERMINAL = 25
  TERMINAL_CODE = 26
  TERMINAL_NONTERMINAL = 27
  TERMINAL_PREFIX_RULE_HINT = 28
  TERMINAL_COMMA = 29
  TERMINAL_NONTERMINAL_REFERENCE = 30
  TERMINAL_PARSER_LL1 = 31
  TERMINAL_RBRACE = 32
  TERMINAL_PIPE = 33
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 33
  def isNonTerminal(self, id):
    return 34 <= id <= 80
  def parse(self, tokens):
    self.tokens = tokens
    self.start = '$GRAMMAR'
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
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(34, self.nonterminals[34]))
    tree.list = False
    if current == None:
      return tree
    if rule == 32:
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
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(35, self.nonterminals[35]))
    tree.list = 'slist'
    if current != None and (current.getId() in [23, 32]):
      return tree
    if current == None:
      return tree
    if rule == 42:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 5:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # nonterminal
      tree.add(t)
      return tree
    elif rule == 40:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 11:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    elif rule == 34:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 8:
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(24) # mode
      tree.add(t)
      t = self.expect(11) # langle
      tree.add(t)
      t = self.expect(4) # identifier
      tree.add(t)
      t = self.expect(2) # rangle
      tree.add(t)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 14:
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(7) # grammar
      tree.add(t)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 7:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    elif rule == 65:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_expression_rule_production(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 48:
      astParameters = OrderedDict([
        ('nud', 1),
        ('nud_ast', 2),
        ('led', 3),
        ('ast', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('MixfixProduction', astParameters)
      t = self.expect(16) # mixfix_rule_hint
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
    elif rule == 61:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('InfixProduction', astParameters)
      t = self.expect(5) # infix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    elif rule == 67:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('PrefixProduction', astParameters)
      t = self.expect(28) # prefix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 70:
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(4) # identifier
      tree.add(t)
      t = self.expect(22) # equals
      tree.add(t)
      t = self.expect(30) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current != None and (current.getId() in [10, 23, 19, 32, 13, 33]):
      return tree
    if current == None:
      return tree
    if rule == 66:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = 'slist'
    if current != None and (current.getId() in [1]):
      return tree
    if current == None:
      return tree
    if rule == 9:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = False
    if current != None and (current.getId() in [17]):
      return tree
    if current == None:
      return tree
    if rule == 53:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 46:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(30) # nonterminal_reference
      tree.add(t)
      return tree
    elif rule == 69:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(4) # identifier
      tree.add(t)
      t = self.expect(19) # lparen
      tree.add(t)
      subtree = self.parse__gen14()
      tree.add( subtree )
      t = self.expect(1) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen15(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = 'slist'
    if current != None and (current.getId() in [1]):
      return tree
    if current == None:
      return tree
    if rule == 16:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 60:
      astParameters = OrderedDict([
        ('regex', 0),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(8) # regex
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(17) # arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 13:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    elif rule == 74:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = 'slist'
    if current != None and (current.getId() in [23, 32]):
      return tree
    if current == None:
      return tree
    if rule == 45:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(33) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current != None and (current.getId() in [-1]):
      return tree
    if current == None:
      return tree
    if rule == 77:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(26) # code
      tree.add(t)
      return tree
    return tree
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = False
    if current != None and (current.getId() in [1]):
      return tree
    if current == None:
      return tree
    if rule == 43:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # terminal
      tree.add(t)
      return tree
    return tree
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 44:
      astParameters = OrderedDict([
        ('precedence', 0),
        ('nonterminal', 2),
        ('production', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      subtree = self.parse__gen12()
      tree.add( subtree )
      t = self.expect(10) # expr_rule_hint
      tree.add(t)
      t = self.expect(27) # nonterminal
      tree.add(t)
      t = self.expect(22) # equals
      tree.add(t)
      subtree = self.parse_expression_rule_production()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_nud(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = False
    if current == None:
      return tree
    if rule == 64:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 26:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 63:
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(18) # lexer
      tree.add(t)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 38:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(9) # parser_expression
      tree.add(t)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen11()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [32]):
      return tree
    if current == None:
      return tree
    if rule == 52:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(4) # identifier
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # terminal
      tree.add(t)
      return tree
    elif rule == 19:
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(4) # identifier
      tree.add(t)
      t = self.expect(19) # lparen
      tree.add(t)
      subtree = self.parse__gen5()
      tree.add( subtree )
      t = self.expect(1) # rparen
      tree.add(t)
      return tree
    elif rule == 25:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(20) # null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen17(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = 'slist'
    if current != None and (current.getId() in [1]):
      return tree
    if current == None:
      return tree
    if rule == 51:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 49:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # terminal
      tree.add(t)
      return tree
    elif rule == 62:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # nonterminal
      tree.add(t)
      return tree
    elif rule == 79:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_led(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 6:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(13) # expression_divider
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10, 17, 19, 32, 33, 23]):
      return tree
    if current == None:
      return tree
    if rule == 72:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 23:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(23) # ll1_rule_hint
      tree.add(t)
      t = self.expect(27) # nonterminal
      tree.add(t)
      t = self.expect(22) # equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [32]):
      return tree
    if current == None:
      return tree
    if rule == 27:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen11()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = False
    if current != None and (current.getId() in [10, 17, 19, 32]):
      return tree
    if current == None:
      return tree
    if rule == 80:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_led()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [32]):
      return tree
    if current == None:
      return tree
    if rule == 30:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen2()
      tree.add( subtree )
      return tree
    return tree
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 2:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(6) # left
      tree.add(t)
      return tree
    elif rule == 20:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(12) # right
      tree.add(t)
      return tree
    elif rule == 36:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(15) # unary
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [32]):
      return tree
    if current == None:
      return tree
    if rule == 68:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 3:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(4) # identifier
      tree.add(t)
      t = self.expect(19) # lparen
      tree.add(t)
      subtree = self.parse__gen16()
      tree.add( subtree )
      t = self.expect(1) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(71, self.nonterminals[71]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 41:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(31) # parser_ll1
      tree.add(t)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen6()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(72, self.nonterminals[72]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 59:
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
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(73, self.nonterminals[73]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [32]):
      return tree
    if current == None:
      return tree
    if rule == 54:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(74, self.nonterminals[74]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 57:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(17) # arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[41][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(75, self.nonterminals[75]))
    tree.list = False
    if current == None:
      return tree
    if rule == 10:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    elif rule == 17:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(20) # null
      tree.add(t)
      return tree
    elif rule == 24:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power(self):
    current = self.tokens.current()
    rule = self.table[42][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(76, self.nonterminals[76]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 4:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(19) # lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(1) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[43][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(77, self.nonterminals[77]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 21:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(14) # lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(32) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[44][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(78, self.nonterminals[78]))
    tree.list = False
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 39:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_binding_power()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen16(self):
    current = self.tokens.current()
    rule = self.table[45][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(79, self.nonterminals[79]))
    tree.list = 'slist'
    if current != None and (current.getId() in [1]):
      return tree
    if current == None:
      return tree
    if rule == 37:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[46][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(80, self.nonterminals[80]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 56:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(0) # asterisk
      tree.add(t)
      return tree
    elif rule == 75:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(3) # dash
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
