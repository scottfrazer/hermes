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
    1: 'infix_rule_hint',
    2: 'left',
    3: 'rbrace',
    4: 'expr_rule_hint',
    5: 'right',
    6: 'lexer',
    7: 'comma',
    8: 'grammar',
    9: 'expression_divider',
    10: 'pipe',
    11: 'terminal',
    12: 'unary',
    13: 'parser_ll1',
    14: 'mixfix_rule_hint',
    15: 'prefix_rule_hint',
    16: 'arrow',
    17: 'nonterminal_reference',
    18: 'code',
    19: 'langle',
    20: 'regex',
    21: 'rparen',
    22: 'parser_expression',
    23: 'll1_rule_hint',
    24: 'mode',
    25: 'identifier',
    26: 'lbrace',
    27: 'nonterminal',
    28: 'null',
    29: 'equals',
    30: 'lparen',
    31: 'asterisk',
    32: 'rangle',
    33: 'colon',
    'dash': 0,
    'infix_rule_hint': 1,
    'left': 2,
    'rbrace': 3,
    'expr_rule_hint': 4,
    'right': 5,
    'lexer': 6,
    'comma': 7,
    'grammar': 8,
    'expression_divider': 9,
    'pipe': 10,
    'terminal': 11,
    'unary': 12,
    'parser_ll1': 13,
    'mixfix_rule_hint': 14,
    'prefix_rule_hint': 15,
    'arrow': 16,
    'nonterminal_reference': 17,
    'code': 18,
    'langle': 19,
    'regex': 20,
    'rparen': 21,
    'parser_expression': 22,
    'll1_rule_hint': 23,
    'mode': 24,
    'identifier': 25,
    'lbrace': 26,
    'nonterminal': 27,
    'null': 28,
    'equals': 29,
    'lparen': 30,
    'asterisk': 31,
    'rangle': 32,
    'colon': 33,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    34: 'lexer_mode',
    35: 'grammar',
    36: '_gen17',
    37: 'expression_rule_production',
    38: 'lexer_regex',
    39: 'ast_parameter',
    40: 'body_element_sub',
    41: '_gen14',
    42: '_gen3',
    43: 'regex_options',
    44: 'rule',
    45: '_gen15',
    46: 'parser',
    47: '_gen16',
    48: '_gen1',
    49: 'll1_rule',
    50: 'lexer_atom',
    51: 'macro_parameter',
    52: '_gen6',
    53: 'nud',
    54: 'expression_rule',
    55: '_gen10',
    56: '_gen13',
    57: 'body_element',
    58: 'precedence',
    59: 'parser_ll1',
    60: 'morpheme',
    61: 'binding_power_marker',
    62: '_gen2',
    63: '_gen11',
    64: 'parser_expression',
    65: '_gen0',
    66: '_gen9',
    67: 'macro',
    68: 'ast_transform',
    69: '_gen4',
    70: 'ast_transform_sub',
    71: 'lexer',
    72: 'll1_rule_rhs',
    73: '_gen12',
    74: 'lexer_target',
    75: 'binding_power',
    76: '_gen5',
    77: '_gen7',
    78: 'led',
    79: '_gen8',
    80: 'associativity',
    'lexer_mode': 34,
    'grammar': 35,
    '_gen17': 36,
    'expression_rule_production': 37,
    'lexer_regex': 38,
    'ast_parameter': 39,
    'body_element_sub': 40,
    '_gen14': 41,
    '_gen3': 42,
    'regex_options': 43,
    'rule': 44,
    '_gen15': 45,
    'parser': 46,
    '_gen16': 47,
    '_gen1': 48,
    'll1_rule': 49,
    'lexer_atom': 50,
    'macro_parameter': 51,
    '_gen6': 52,
    'nud': 53,
    'expression_rule': 54,
    '_gen10': 55,
    '_gen13': 56,
    'body_element': 57,
    'precedence': 58,
    'parser_ll1': 59,
    'morpheme': 60,
    'binding_power_marker': 61,
    '_gen2': 62,
    '_gen11': 63,
    'parser_expression': 64,
    '_gen0': 65,
    '_gen9': 66,
    'macro': 67,
    'ast_transform': 68,
    '_gen4': 69,
    'ast_transform_sub': 70,
    'lexer': 71,
    'll1_rule_rhs': 72,
    '_gen12': 73,
    'lexer_target': 74,
    'binding_power': 75,
    '_gen5': 76,
    '_gen7': 77,
    'led': 78,
    '_gen8': 79,
    'associativity': 80,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 80, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, 72, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 69, -1, -1, -1, -1, -1, -1, 69, 69, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, 69, -1, 69, -1, 69, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 21, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 76, 76, -1, -1, -1, -1, 76, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, 76, -1, -1, 76, -1, -1, -1],
    [-1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1],
    [-1, -1, -1, 79, 79, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, 74, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1, -1, -1, -1, 79, -1, -1, -1],
    [-1, -1, -1, 63, 63, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, 37, -1, -1, -1, -1, -1, -1],
    [10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1],
    [-1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 28, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 27, -1, -1, 9, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 67, 67, -1, -1, -1, -1, 67, 67, 64, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, 67, -1, 64, -1, 64, -1, -1, 67, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 62, -1, -1, -1, -1, -1, -1, 62, 62, -1, 14, -1, -1, 62, -1, -1, -1, -1, -1, 14, 62, -1, 62, -1, 62, 1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, 61, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 7, -1, -1, -1, -1, -1, -1, 7, 7, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, 7, -1, 7, -1, 7, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 45, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 51, -1, -1, 11, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
  ]
  TERMINAL_DASH = 0
  TERMINAL_INFIX_RULE_HINT = 1
  TERMINAL_LEFT = 2
  TERMINAL_RBRACE = 3
  TERMINAL_EXPR_RULE_HINT = 4
  TERMINAL_RIGHT = 5
  TERMINAL_LEXER = 6
  TERMINAL_COMMA = 7
  TERMINAL_GRAMMAR = 8
  TERMINAL_EXPRESSION_DIVIDER = 9
  TERMINAL_PIPE = 10
  TERMINAL_TERMINAL = 11
  TERMINAL_UNARY = 12
  TERMINAL_PARSER_LL1 = 13
  TERMINAL_MIXFIX_RULE_HINT = 14
  TERMINAL_PREFIX_RULE_HINT = 15
  TERMINAL_ARROW = 16
  TERMINAL_NONTERMINAL_REFERENCE = 17
  TERMINAL_CODE = 18
  TERMINAL_LANGLE = 19
  TERMINAL_REGEX = 20
  TERMINAL_RPAREN = 21
  TERMINAL_PARSER_EXPRESSION = 22
  TERMINAL_LL1_RULE_HINT = 23
  TERMINAL_MODE = 24
  TERMINAL_IDENTIFIER = 25
  TERMINAL_LBRACE = 26
  TERMINAL_NONTERMINAL = 27
  TERMINAL_NULL = 28
  TERMINAL_EQUALS = 29
  TERMINAL_LPAREN = 30
  TERMINAL_ASTERISK = 31
  TERMINAL_RANGLE = 32
  TERMINAL_COLON = 33
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
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(34, self.nonterminals[34]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 4:
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(24) # mode
      tree.add(t)
      t = self.expect(19) # langle
      tree.add(t)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(32) # rangle
      tree.add(t)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(35, self.nonterminals[35]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 3:
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(8) # grammar
      tree.add(t)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen17(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 44:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(7) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse_expression_rule_production(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 39:
      astParameters = OrderedDict([
        ('nud', 1),
        ('led', 2),
        ('ast', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('MixfixProduction', astParameters)
      t = self.expect(14) # mixfix_rule_hint
      tree.add(t)
      subtree = self.parse_nud()
      tree.add( subtree )
      subtree = self.parse__gen13()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    elif rule == 72:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('PrefixProduction', astParameters)
      t = self.expect(15) # prefix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    elif rule == 80:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('InfixProduction', astParameters)
      t = self.expect(1) # infix_rule_hint
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 32:
      astParameters = OrderedDict([
        ('regex', 0),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(20) # regex
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(16) # arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 50:
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(29) # equals
      tree.add(t)
      t = self.expect(17) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 30:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 77:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 75:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = False
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 78:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 55:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = False
    if current == None:
      return tree
    if rule == 69:
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
  def parse__gen15(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 12:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(7) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      return tree
    return tree
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 34:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    elif rule == 42:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen16(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 40:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen17()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = False
    if current != None and (current.getId() in [-1]):
      return tree
    if current == None:
      return tree
    if rule == 70:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(18) # code
      tree.add(t)
      return tree
    return tree
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 49:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(23) # ll1_rule_hint
      tree.add(t)
      t = self.expect(27) # nonterminal
      tree.add(t)
      t = self.expect(29) # equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 2:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    elif rule == 59:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 24:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # nonterminal
      tree.add(t)
      return tree
    elif rule == 29:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(11) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 18:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse_nud(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = False
    if current == None:
      return tree
    if rule == 76:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 35:
      astParameters = OrderedDict([
        ('precedence', 0),
        ('nonterminal', 2),
        ('production', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      subtree = self.parse__gen12()
      tree.add( subtree )
      t = self.expect(4) # expr_rule_hint
      tree.add(t)
      t = self.expect(27) # nonterminal
      tree.add(t)
      t = self.expect(29) # equals
      tree.add(t)
      subtree = self.parse_expression_rule_production()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = False
    if current != None and (current.getId() in [30, 4, 10, 23, 3]):
      return tree
    if current == None:
      return tree
    if rule == 74:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = False
    if current != None and (current.getId() in [30, 16, 3, 4]):
      return tree
    if current == None:
      return tree
    if rule == 54:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_led()
      tree.add( subtree )
      return tree
    return tree
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 71:
      astParameters = OrderedDict([
        ('marker', 0),
        ('associativity', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Precedence', astParameters)
      subtree = self.parse_binding_power_marker()
      tree.add( subtree )
      t = self.expect(33) # colon
      tree.add(t)
      subtree = self.parse_associativity()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 53:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(13) # parser_ll1
      tree.add(t)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen6()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 16:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(11) # terminal
      tree.add(t)
      return tree
    elif rule == 37:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # nonterminal
      tree.add(t)
      return tree
    elif rule == 66:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 10:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(0) # dash
      tree.add(t)
      return tree
    elif rule == 56:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(31) # asterisk
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 5:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen2()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 25:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen11()
      tree.add( subtree )
      return tree
    return tree
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 41:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(22) # parser_expression
      tree.add(t)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen11()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 9:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [4, 10, 16, 30, 23, 3, 9]):
      return tree
    if current == None:
      return tree
    if rule == 64:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 65:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(30) # lparen
      tree.add(t)
      subtree = self.parse__gen16()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 6:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(16) # arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 43:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # identifier
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 19:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(17) # nonterminal_reference
      tree.add(t)
      return tree
    elif rule == 68:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(30) # lparen
      tree.add(t)
      subtree = self.parse__gen14()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(71, self.nonterminals[71]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 13:
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(6) # lexer
      tree.add(t)
      t = self.expect(26) # lbrace
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(3) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(72, self.nonterminals[72]))
    tree.list = False
    if current == None:
      return tree
    if rule == 1:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(28) # null
      tree.add(t)
      return tree
    elif rule == 14:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 62:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(73, self.nonterminals[73]))
    tree.list = False
    if current != None and (current.getId() in [4]):
      return tree
    if current == None:
      return tree
    if rule == 36:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_binding_power()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(74, self.nonterminals[74]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 31:
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(30) # lparen
      tree.add(t)
      subtree = self.parse__gen5()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    elif rule == 48:
      astParameters = OrderedDict([
        ('name', 0),
      ])
      tree.astTransform = AstTransformNodeCreator('Terminal', astParameters)
      t = self.expect(11) # terminal
      tree.add(t)
      return tree
    elif rule == 61:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(28) # null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power(self):
    current = self.tokens.current()
    rule = self.table[41][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(75, self.nonterminals[75]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 26:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(30) # lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[42][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(76, self.nonterminals[76]))
    tree.list = False
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 20:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(11) # terminal
      tree.add(t)
      return tree
    return tree
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[43][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(77, self.nonterminals[77]))
    tree.list = 'slist'
    if current != None and (current.getId() in [23, 3]):
      return tree
    if current == None:
      return tree
    if rule == 7:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_led(self):
    current = self.tokens.current()
    rule = self.table[44][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(78, self.nonterminals[78]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 8:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(9) # expression_divider
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[45][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(79, self.nonterminals[79]))
    tree.list = 'slist'
    if current != None and (current.getId() in [23, 3]):
      return tree
    if current == None:
      return tree
    if rule == 23:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(10) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    return tree
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[46][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(80, self.nonterminals[80]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 11:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(5) # right
      tree.add(t)
      return tree
    elif rule == 17:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(12) # unary
      tree.add(t)
      return tree
    elif rule == 51:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(2) # left
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
