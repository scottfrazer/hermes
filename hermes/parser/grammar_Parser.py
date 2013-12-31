import sys, inspect
from collections import OrderedDict
from ParserCommon import *
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
    0: 'equals',
    1: 'asterisk',
    2: 'lbrace',
    3: 'mode',
    4: 'langle',
    5: 'expression_divider',
    6: 'nonterminal',
    7: 'identifier',
    8: 'left',
    9: 'pipe',
    10: 'rangle',
    11: 'dash',
    12: 'right',
    13: 'comma',
    14: 'unary',
    15: 'terminal',
    16: 'rbrace',
    17: 'regex',
    18: 'grammar',
    19: 'code',
    20: 'lparen',
    21: 'rparen',
    22: 'lexer',
    23: 'parser_expression',
    24: 'null',
    25: 'colon',
    26: 'arrow',
    27: 'parser_ll1',
    28: 'nonterminal_reference',
    29: 'll1_rule_hint',
    'equals': 0,
    'asterisk': 1,
    'lbrace': 2,
    'mode': 3,
    'langle': 4,
    'expression_divider': 5,
    'nonterminal': 6,
    'identifier': 7,
    'left': 8,
    'pipe': 9,
    'rangle': 10,
    'dash': 11,
    'right': 12,
    'comma': 13,
    'unary': 14,
    'terminal': 15,
    'rbrace': 16,
    'regex': 17,
    'grammar': 18,
    'code': 19,
    'lparen': 20,
    'rparen': 21,
    'lexer': 22,
    'parser_expression': 23,
    'null': 24,
    'colon': 25,
    'arrow': 26,
    'parser_ll1': 27,
    'nonterminal_reference': 28,
    'll1_rule_hint': 29,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    30: 'morpheme',
    31: 'lexer_target',
    32: 'body_element_sub',
    33: '_gen7',
    34: 'lexer_atom',
    35: 'body_element',
    36: 'macro',
    37: '_gen0',
    38: 'expression_rule',
    39: 'parser_ll1',
    40: 'll1_rule_rhs',
    41: 'rule',
    42: '_gen3',
    43: 'lexer_regex',
    44: 'macro_parameter',
    45: '_gen13',
    46: '_gen10',
    47: '_gen5',
    48: 'grammar',
    49: 'binding_power_marker',
    50: 'lexer_mode',
    51: 'lexer',
    52: 'ast_transform',
    53: 'ast_parameter',
    54: '_gen9',
    55: '_gen11',
    56: '_gen12',
    57: 'precedence',
    58: 'ast_transform_sub',
    59: 'regex_options',
    60: '_gen8',
    61: '_gen2',
    62: 'll1_rule',
    63: 'expression_morpheme',
    64: 'parser',
    65: 'parser_expression',
    66: '_gen4',
    67: '_gen14',
    68: 'associativity',
    69: '_gen6',
    70: '_gen1',
    'morpheme': 30,
    'lexer_target': 31,
    'body_element_sub': 32,
    '_gen7': 33,
    'lexer_atom': 34,
    'body_element': 35,
    'macro': 36,
    '_gen0': 37,
    'expression_rule': 38,
    'parser_ll1': 39,
    'll1_rule_rhs': 40,
    'rule': 41,
    '_gen3': 42,
    'lexer_regex': 43,
    'macro_parameter': 44,
    '_gen13': 45,
    '_gen10': 46,
    '_gen5': 47,
    'grammar': 48,
    'binding_power_marker': 49,
    'lexer_mode': 50,
    'lexer': 51,
    'ast_transform': 52,
    'ast_parameter': 53,
    '_gen9': 54,
    '_gen11': 55,
    '_gen12': 56,
    'precedence': 57,
    'ast_transform_sub': 58,
    'regex_options': 59,
    '_gen8': 60,
    '_gen2': 61,
    'll1_rule': 62,
    'expression_morpheme': 63,
    'parser': 64,
    'parser_expression': 65,
    '_gen4': 66,
    '_gen14': 67,
    'associativity': 68,
    '_gen6': 69,
    '_gen1': 70,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, -1, -1, 22, 20, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, 1, -1, -1, -1, 1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 46, 46, -1, 40, -1, -1, -1, -1, -1, 46, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, 40],
    [-1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, 41, -1, -1, -1, 41, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, 10, 10, -1, -1, -1, 10, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 39, -1, -1],
    [-1, -1, -1, -1, -1, -1, 45, 45, -1, 45, -1, -1, -1, -1, -1, 45, 45, -1, -1, -1, -1, -1, -1, 4, 69, -1, 45, 4, -1, 45],
    [-1, -1, -1, -1, -1, -1, 49, 49, -1, 49, -1, -1, -1, -1, -1, 49, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, 49],
    [-1, -1, -1, -1, -1, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 24, 24, 24, -1, -1, -1, -1, -1, -1, -1, 24, 21, -1, -1, -1, 21, -1, -1, -1, -1, -1, 21, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 18, 18, -1, 18, -1, -1, -1, -1, -1, 18, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, 18],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1],
    [-1, -1, 32, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, 60, -1, -1, -1, -1, -1, 47, -1, -1, 60],
    [-1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 38],
    [-1, -1, -1, -1, -1, 29, 52, 52, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, 23, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, 6, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62],
    [-1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
  ]
  TERMINAL_EQUALS = 0
  TERMINAL_ASTERISK = 1
  TERMINAL_LBRACE = 2
  TERMINAL_MODE = 3
  TERMINAL_LANGLE = 4
  TERMINAL_EXPRESSION_DIVIDER = 5
  TERMINAL_NONTERMINAL = 6
  TERMINAL_IDENTIFIER = 7
  TERMINAL_LEFT = 8
  TERMINAL_PIPE = 9
  TERMINAL_RANGLE = 10
  TERMINAL_DASH = 11
  TERMINAL_RIGHT = 12
  TERMINAL_COMMA = 13
  TERMINAL_UNARY = 14
  TERMINAL_TERMINAL = 15
  TERMINAL_RBRACE = 16
  TERMINAL_REGEX = 17
  TERMINAL_GRAMMAR = 18
  TERMINAL_CODE = 19
  TERMINAL_LPAREN = 20
  TERMINAL_RPAREN = 21
  TERMINAL_LEXER = 22
  TERMINAL_PARSER_EXPRESSION = 23
  TERMINAL_NULL = 24
  TERMINAL_COLON = 25
  TERMINAL_ARROW = 26
  TERMINAL_PARSER_LL1 = 27
  TERMINAL_NONTERMINAL_REFERENCE = 28
  TERMINAL_LL1_RULE_HINT = 29
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 29
  def isNonTerminal(self, id):
    return 30 <= id <= 70
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
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(30, self.nonterminals[30]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 14:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(15) # terminal
      tree.add(t)
      return tree
    elif rule == 20:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    elif rule == 22:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(6) # nonterminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(31, self.nonterminals[31]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 13:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(24) # null
      tree.add(t)
      return tree
    elif rule == 58:
      astParameters = OrderedDict([
        ('name', 0),
      ])
      tree.astTransform = AstTransformNodeCreator('Terminal', astParameters)
      t = self.expect(15) # terminal
      tree.add(t)
      return tree
    elif rule == 66:
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(7) # identifier
      tree.add(t)
      t = self.expect(20) # lparen
      tree.add(t)
      t = self.expect(15) # terminal
      tree.add(t)
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(32, self.nonterminals[32]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 1:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 61:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(33, self.nonterminals[33]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [26, 29, 9, 16]):
      return tree
    if current == None:
      return tree
    if rule == 46:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(34, self.nonterminals[34]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 3:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    elif rule == 37:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(35, self.nonterminals[35]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 41:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 54:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(7) # identifier
      tree.add(t)
      t = self.expect(20) # lparen
      tree.add(t)
      subtree = self.parse__gen13()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 10:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 12:
      astParameters = OrderedDict([
        ('precedence', 1),
        ('nonterminal', 3),
        ('production', 5),
        ('ast', 6),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      t = self.expect(20) # lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      t = self.expect(6) # nonterminal
      tree.add(t)
      t = self.expect(0) # equals
      tree.add(t)
      subtree = self.parse__gen10()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 39:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(27) # parser_ll1
      tree.add(t)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = False
    if current == None:
      return tree
    if rule == 4:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 45:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen5()
      tree.add( subtree )
      return tree
    elif rule == 69:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(24) # null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = False
    if current == None:
      return tree
    if rule == 49:
      astParameters = OrderedDict([
        ('morphemes', 0),
        ('ast', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('Production', astParameters)
      subtree = self.parse__gen7()
      tree.add( subtree )
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 17:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(7) # identifier
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 56:
      astParameters = OrderedDict([
        ('regex', 0),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(17) # regex
      tree.add(t)
      subtree = self.parse__gen2()
      tree.add( subtree )
      t = self.expect(26) # arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 11:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(6) # nonterminal
      tree.add(t)
      return tree
    elif rule == 42:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(15) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 43:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen14()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [26, 16, 20]):
      return tree
    if current == None:
      return tree
    if rule == 24:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen10()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = 'slist'
    if current != None and (current.getId() in [29, 16]):
      return tree
    if current == None:
      return tree
    if rule == 18:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 2:
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(18) # grammar
      tree.add(t)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      t = self.expect(19) # code
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 9:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(1) # asterisk
      tree.add(t)
      return tree
    elif rule == 50:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(11) # dash
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 7:
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(3) # mode
      tree.add(t)
      t = self.expect(4) # langle
      tree.add(t)
      t = self.expect(7) # identifier
      tree.add(t)
      t = self.expect(10) # rangle
      tree.add(t)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 8:
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(22) # lexer
      tree.add(t)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 30:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(26) # arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 53:
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(7) # identifier
      tree.add(t)
      t = self.expect(0) # equals
      tree.add(t)
      t = self.expect(28) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 5:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 26:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen12()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 28:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(13) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen12()
      tree.add( subtree )
      return tree
    return tree
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 36:
      astParameters = OrderedDict([
        ('marker', 0),
        ('associativity', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Precedence', astParameters)
      subtree = self.parse_binding_power_marker()
      tree.add( subtree )
      t = self.expect(25) # colon
      tree.add(t)
      subtree = self.parse_associativity()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(28) # nonterminal_reference
      tree.add(t)
      return tree
    elif rule == 35:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(7) # identifier
      tree.add(t)
      t = self.expect(20) # lparen
      tree.add(t)
      subtree = self.parse__gen11()
      tree.add( subtree )
      t = self.expect(21) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 32:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = False
    if current != None and (current.getId() in [29, 20, 9, 16]):
      return tree
    if current == None:
      return tree
    if rule == 47:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = False
    if current != None and (current.getId() in [26]):
      return tree
    if current == None:
      return tree
    if rule == 63:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 38:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(29) # ll1_rule_hint
      tree.add(t)
      t = self.expect(6) # nonterminal
      tree.add(t)
      t = self.expect(0) # equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_expression_morpheme(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 29:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(5) # expression_divider
      tree.add(t)
      return tree
    elif rule == 52:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 23:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    elif rule == 34:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 68:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(23) # parser_expression
      tree.add(t)
      t = self.expect(2) # lbrace
      tree.add(t)
      subtree = self.parse__gen9()
      tree.add( subtree )
      t = self.expect(16) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 67:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = 'slist'
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 57:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(13) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen14()
      tree.add( subtree )
      return tree
    return tree
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 6:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(12) # right
      tree.add(t)
      return tree
    elif rule == 27:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # left
      tree.add(t)
      return tree
    elif rule == 55:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(14) # unary
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = 'slist'
    if current != None and (current.getId() in [29, 16]):
      return tree
    if current == None:
      return tree
    if rule == 19:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(9) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [16]):
      return tree
    if current == None:
      return tree
    if rule == 51:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    return tree
