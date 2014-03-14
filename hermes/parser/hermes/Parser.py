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
    0: 'langle',
    1: 'rangle',
    2: 'll1_rule_hint',
    3: 'expr_rule_hint',
    4: 'right',
    5: 'mixfix_rule_hint',
    6: 'prefix_rule_hint',
    7: 'infix_rule_hint',
    8: 'asterisk',
    9: 'grammar',
    10: 'rbrace',
    11: 'left',
    12: 'lbrace',
    13: 'colon',
    14: 'unary',
    15: 'lexer',
    16: 'parser_ll1',
    17: 'null',
    18: 'lparen',
    19: 'rparen',
    20: 'regex',
    21: 'arrow',
    22: 'terminal',
    23: 'mode',
    24: 'integer',
    25: 'identifier',
    26: 'pipe',
    27: 'dash',
    28: 'equals',
    29: 'comma',
    30: 'parser_expression',
    31: 'nonterminal',
    32: 'nonterminal_reference',
    33: 'string',
    34: 'code',
    35: 'expression_divider',
    'langle': 0,
    'rangle': 1,
    'll1_rule_hint': 2,
    'expr_rule_hint': 3,
    'right': 4,
    'mixfix_rule_hint': 5,
    'prefix_rule_hint': 6,
    'infix_rule_hint': 7,
    'asterisk': 8,
    'grammar': 9,
    'rbrace': 10,
    'left': 11,
    'lbrace': 12,
    'colon': 13,
    'unary': 14,
    'lexer': 15,
    'parser_ll1': 16,
    'null': 17,
    'lparen': 18,
    'rparen': 19,
    'regex': 20,
    'arrow': 21,
    'terminal': 22,
    'mode': 23,
    'integer': 24,
    'identifier': 25,
    'pipe': 26,
    'dash': 27,
    'equals': 28,
    'comma': 29,
    'parser_expression': 30,
    'nonterminal': 31,
    'nonterminal_reference': 32,
    'string': 33,
    'code': 34,
    'expression_divider': 35,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    36: '_gen26',
    37: 'lexer_regex',
    38: '_gen9',
    39: 'expression_rule_production',
    40: 'lexer',
    41: 'nud',
    42: '_gen8',
    43: '_gen16',
    44: 'led',
    45: '_gen6',
    46: '_gen10',
    47: '_gen5',
    48: '_gen24',
    49: 'associativity',
    50: '_gen4',
    51: 'macro',
    52: '_gen7',
    53: '_gen22',
    54: 'ast_parameter',
    55: 'morpheme',
    56: 'macro_parameter',
    57: '_gen11',
    58: 'parser_ll1',
    59: '_gen1',
    60: 'grammar',
    61: '_gen25',
    62: '_gen0',
    63: '_gen23',
    64: 'ast_transform',
    65: '_gen17',
    66: 'rule',
    67: 'parser',
    68: 'ast_transform_sub',
    69: 'lexer_atom',
    70: '_gen2',
    71: '_gen15',
    72: 'lexer_mode',
    73: 'regex_options',
    74: '_gen12',
    75: 'body_element',
    76: 'lexer_target',
    77: '_gen13',
    78: 'body_element_sub',
    79: '_gen21',
    80: 'parser_expression',
    81: 'll1_rule',
    82: 'precedence',
    83: 'll1_rule_rhs',
    84: '_gen20',
    85: '_gen18',
    86: '_gen19',
    87: '_gen14',
    88: '_gen3',
    89: 'expression_rule',
    90: 'binding_power',
    91: 'binding_power_marker',
    '_gen26': 36,
    'lexer_regex': 37,
    '_gen9': 38,
    'expression_rule_production': 39,
    'lexer': 40,
    'nud': 41,
    '_gen8': 42,
    '_gen16': 43,
    'led': 44,
    '_gen6': 45,
    '_gen10': 46,
    '_gen5': 47,
    '_gen24': 48,
    'associativity': 49,
    '_gen4': 50,
    'macro': 51,
    '_gen7': 52,
    '_gen22': 53,
    'ast_parameter': 54,
    'morpheme': 55,
    'macro_parameter': 56,
    '_gen11': 57,
    'parser_ll1': 58,
    '_gen1': 59,
    'grammar': 60,
    '_gen25': 61,
    '_gen0': 62,
    '_gen23': 63,
    'ast_transform': 64,
    '_gen17': 65,
    'rule': 66,
    'parser': 67,
    'ast_transform_sub': 68,
    'lexer_atom': 69,
    '_gen2': 70,
    '_gen15': 71,
    'lexer_mode': 72,
    'regex_options': 73,
    '_gen12': 74,
    'body_element': 75,
    'lexer_target': 76,
    '_gen13': 77,
    'body_element_sub': 78,
    '_gen21': 79,
    'parser_expression': 80,
    'll1_rule': 81,
    'precedence': 82,
    'll1_rule_rhs': 83,
    '_gen20': 84,
    '_gen18': 85,
    '_gen19': 86,
    '_gen14': 87,
    '_gen3': 88,
    'expression_rule': 89,
    'binding_power': 90,
    'binding_power_marker': 91,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 4, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 98, 22, 83, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 49, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 91, -1, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1, -1, -1, -1, 91, -1, -1, 91, 91, -1, -1, 91, -1, -1, -1, -1, -1, 91, -1, -1, -1, -1],
    [-1, -1, 2, -1, -1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 2, 2, -1, -1, 2, 2, -1, -1, -1, -1, 2, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 34],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, -1, -1, -1, -1, -1, -1, -1, -1, 63, -1, -1, 63, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 37, -1, -1, 36, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, 1, -1, -1, 74, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 66, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 90, 90, -1, -1, -1, -1, -1, -1, 90, -1, -1, -1, -1, -1, -1, -1, 90, -1, -1, 90, 89, -1, -1, 89, 90, -1, -1, -1, -1, 89, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 86, -1, -1, 100, -1, -1, -1, -1, -1, 87, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, 85, -1, -1, -1, -1, -1, -1, 61, -1, 76, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, 52, -1, 52, -1, -1, -1, -1, -1, -1, 52, -1, 52, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 43, -1, -1, -1, -1, 42, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 16, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 16, 16, -1, -1, 16, 16, -1, -1, -1, -1, 16, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 95, -1, -1, -1, -1, -1, -1, 95, -1, -1, -1, -1, -1, -1, -1, 95, -1, -1, 95, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 94],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 71, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, 88, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 88, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, 39, -1, -1, 38, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 75, 41, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 41, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1],
    [-1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 6, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, -1, -1, 11, 35, -1, -1, -1, 6, 6, -1, -1, 6, 6, -1, -1, -1, 11, 6, -1, -1, -1, -1],
    [-1, -1, 97, 97, -1, -1, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, 97, -1, -1, 96, -1, -1, -1, -1, 97, -1, -1, -1, -1, -1, -1, -1, -1, 97],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 84, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 99, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1],
  ]
  TERMINAL_LANGLE = 0
  TERMINAL_RANGLE = 1
  TERMINAL_LL1_RULE_HINT = 2
  TERMINAL_EXPR_RULE_HINT = 3
  TERMINAL_RIGHT = 4
  TERMINAL_MIXFIX_RULE_HINT = 5
  TERMINAL_PREFIX_RULE_HINT = 6
  TERMINAL_INFIX_RULE_HINT = 7
  TERMINAL_ASTERISK = 8
  TERMINAL_GRAMMAR = 9
  TERMINAL_RBRACE = 10
  TERMINAL_LEFT = 11
  TERMINAL_LBRACE = 12
  TERMINAL_COLON = 13
  TERMINAL_UNARY = 14
  TERMINAL_LEXER = 15
  TERMINAL_PARSER_LL1 = 16
  TERMINAL_NULL = 17
  TERMINAL_LPAREN = 18
  TERMINAL_RPAREN = 19
  TERMINAL_REGEX = 20
  TERMINAL_ARROW = 21
  TERMINAL_TERMINAL = 22
  TERMINAL_MODE = 23
  TERMINAL_INTEGER = 24
  TERMINAL_IDENTIFIER = 25
  TERMINAL_PIPE = 26
  TERMINAL_DASH = 27
  TERMINAL_EQUALS = 28
  TERMINAL_COMMA = 29
  TERMINAL_PARSER_EXPRESSION = 30
  TERMINAL_NONTERMINAL = 31
  TERMINAL_NONTERMINAL_REFERENCE = 32
  TERMINAL_STRING = 33
  TERMINAL_CODE = 34
  TERMINAL_EXPRESSION_DIVIDER = 35
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 35
  def isNonTerminal(self, id):
    return 36 <= id <= 91
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
  def parse__gen26(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(36, self.nonterminals[36]))
    tree.list = 'slist'
    if current != None and (current.getId() in [19]):
      return tree
    if current == None:
      return tree
    if rule == 53:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen26()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_regex(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(37, self.nonterminals[37]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 9:
      astParameters = OrderedDict([
        ('regex', 0),
        ('options', 1),
        ('onmatch', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Regex', astParameters)
      t = self.expect(20) # regex
      tree.add(t)
      subtree = self.parse__gen3()
      tree.add( subtree )
      t = self.expect(21) # arrow
      tree.add(t)
      subtree = self.parse_lexer_target()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen9(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(38, self.nonterminals[38]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2, 10]):
      return tree
    if current == None:
      return tree
    if rule == 3:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(26) # pipe
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse_expression_rule_production(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(39, self.nonterminals[39]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 22:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('PrefixProduction', astParameters)
      t = self.expect(6) # prefix_rule_hint
      tree.add(t)
      subtree = self.parse__gen22()
      tree.add( subtree )
      subtree = self.parse__gen20()
      tree.add( subtree )
      return tree
    elif rule == 83:
      astParameters = OrderedDict([
        ('morphemes', 1),
        ('ast', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('InfixProduction', astParameters)
      t = self.expect(7) # infix_rule_hint
      tree.add(t)
      subtree = self.parse__gen22()
      tree.add( subtree )
      subtree = self.parse__gen20()
      tree.add( subtree )
      return tree
    elif rule == 98:
      astParameters = OrderedDict([
        ('nud', 1),
        ('nud_ast', 2),
        ('led', 3),
        ('ast', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('MixfixProduction', astParameters)
      t = self.expect(5) # mixfix_rule_hint
      tree.add(t)
      subtree = self.parse_nud()
      tree.add( subtree )
      subtree = self.parse__gen20()
      tree.add( subtree )
      subtree = self.parse__gen15()
      tree.add( subtree )
      subtree = self.parse__gen20()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer(self):
    current = self.tokens.current()
    rule = self.table[4][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(40, self.nonterminals[40]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 49:
      astParameters = OrderedDict([
        ('atoms', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Lexer', astParameters)
      t = self.expect(15) # lexer
      tree.add(t)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen6()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_nud(self):
    current = self.tokens.current()
    rule = self.table[5][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(41, self.nonterminals[41]))
    tree.list = False
    if current == None:
      return tree
    if rule == 91:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen8(self):
    current = self.tokens.current()
    rule = self.table[6][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(42, self.nonterminals[42]))
    tree.list = 'slist'
    if current != None and (current.getId() in [2, 10]):
      return tree
    if current == None:
      return tree
    if rule == 2:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_rule()
      tree.add( subtree )
      subtree = self.parse__gen9()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen16(self):
    current = self.tokens.current()
    rule = self.table[7][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(43, self.nonterminals[43]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_led(self):
    current = self.tokens.current()
    rule = self.table[8][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(44, self.nonterminals[44]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 34:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(35) # expression_divider
      tree.add(t)
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen6(self):
    current = self.tokens.current()
    rule = self.table[9][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(45, self.nonterminals[45]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 63:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    elif rule == 63:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_atom()
      tree.add( subtree )
      subtree = self.parse__gen6()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen10(self):
    current = self.tokens.current()
    rule = self.table[10][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(46, self.nonterminals[46]))
    tree.list = 'nlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen5(self):
    current = self.tokens.current()
    rule = self.table[11][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(47, self.nonterminals[47]))
    tree.list = False
    if current != None and (current.getId() in [19]):
      return tree
    if current == None:
      return tree
    if rule == 36:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # terminal
      tree.add(t)
      return tree
    return tree
  def parse__gen24(self):
    current = self.tokens.current()
    rule = self.table[12][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(48, self.nonterminals[48]))
    tree.list = 'slist'
    if current != None and (current.getId() in [19]):
      return tree
    if current == None:
      return tree
    if rule == 24:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(29) # comma
      tree.add(t)
      tree.listSeparator = t
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen24()
      tree.add( subtree )
      return tree
    return tree
  def parse_associativity(self):
    current = self.tokens.current()
    rule = self.table[13][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(49, self.nonterminals[49]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 1:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(11) # left
      tree.add(t)
      return tree
    elif rule == 69:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(4) # right
      tree.add(t)
      return tree
    elif rule == 74:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(14) # unary
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen4(self):
    current = self.tokens.current()
    rule = self.table[14][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(50, self.nonterminals[50]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 28:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(25) # identifier
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      return tree
    return tree
  def parse_macro(self):
    current = self.tokens.current()
    rule = self.table[15][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(51, self.nonterminals[51]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 56:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Macro', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(18) # lparen
      tree.add(t)
      subtree = self.parse__gen25()
      tree.add( subtree )
      t = self.expect(19) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen7(self):
    current = self.tokens.current()
    rule = self.table[16][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(52, self.nonterminals[52]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 66:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ll1_rule()
      tree.add( subtree )
      subtree = self.parse__gen7()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen22(self):
    current = self.tokens.current()
    rule = self.table[17][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(53, self.nonterminals[53]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [18, 10, 2, 26, 21, 3]):
      return tree
    if current == None:
      return tree
    if rule == 89:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    elif rule == 89:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    elif rule == 89:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    elif rule == 89:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    elif rule == 89:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_morpheme()
      tree.add( subtree )
      subtree = self.parse__gen22()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_parameter(self):
    current = self.tokens.current()
    rule = self.table[18][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(54, self.nonterminals[54]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 40:
      astParameters = OrderedDict([
        ('name', 0),
        ('index', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstParameter', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(28) # equals
      tree.add(t)
      t = self.expect(32) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_morpheme(self):
    current = self.tokens.current()
    rule = self.table[19][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(55, self.nonterminals[55]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 86:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # terminal
      tree.add(t)
      return tree
    elif rule == 87:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(31) # nonterminal
      tree.add(t)
      return tree
    elif rule == 100:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_macro_parameter(self):
    current = self.tokens.current()
    rule = self.table[20][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(56, self.nonterminals[56]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 61:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(31) # nonterminal
      tree.add(t)
      return tree
    elif rule == 70:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # terminal
      tree.add(t)
      return tree
    elif rule == 76:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(33) # string
      tree.add(t)
      return tree
    elif rule == 85:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(24) # integer
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen11(self):
    current = self.tokens.current()
    rule = self.table[21][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(57, self.nonterminals[57]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_ll1(self):
    current = self.tokens.current()
    rule = self.table[22][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(58, self.nonterminals[58]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 68:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Parser', astParameters)
      t = self.expect(16) # parser_ll1
      tree.add(t)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen7()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[23][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(59, self.nonterminals[59]))
    tree.list = False
    if current != None and (current.getId() in [-1]):
      return tree
    if current == None:
      return tree
    if rule == 44:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(34) # code
      tree.add(t)
      return tree
    return tree
  def parse_grammar(self):
    current = self.tokens.current()
    rule = self.table[24][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(60, self.nonterminals[60]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 46:
      astParameters = OrderedDict([
        ('body', 2),
        ('code', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('Grammar', astParameters)
      t = self.expect(9) # grammar
      tree.add(t)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen0()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen25(self):
    current = self.tokens.current()
    rule = self.table[25][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(61, self.nonterminals[61]))
    tree.list = 'slist'
    if current != None and (current.getId() in [19]):
      return tree
    if current == None:
      return tree
    if rule == 52:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_macro_parameter()
      tree.add( subtree )
      subtree = self.parse__gen26()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[26][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(62, self.nonterminals[62]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 42:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element()
      tree.add( subtree )
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen23(self):
    current = self.tokens.current()
    rule = self.table[27][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(63, self.nonterminals[63]))
    tree.list = 'slist'
    if current != None and (current.getId() in [19]):
      return tree
    if current == None:
      return tree
    if rule == 23:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_parameter()
      tree.add( subtree )
      subtree = self.parse__gen24()
      tree.add( subtree )
      return tree
    return tree
  def parse_ast_transform(self):
    current = self.tokens.current()
    rule = self.table[28][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(64, self.nonterminals[64]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 51:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(21) # arrow
      tree.add(t)
      subtree = self.parse_ast_transform_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen17(self):
    current = self.tokens.current()
    rule = self.table[29][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(65, self.nonterminals[65]))
    tree.list = 'nlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_rule(self):
    current = self.tokens.current()
    rule = self.table[30][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(66, self.nonterminals[66]))
    tree.list = False
    if current == None:
      return tree
    if rule == 16:
      astParameters = OrderedDict([
        ('morphemes', 0),
        ('ast', 1),
      ])
      tree.astTransform = AstTransformNodeCreator('Production', astParameters)
      subtree = self.parse__gen22()
      tree.add( subtree )
      subtree = self.parse__gen20()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser(self):
    current = self.tokens.current()
    rule = self.table[31][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(67, self.nonterminals[67]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 77:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_ll1()
      tree.add( subtree )
      return tree
    elif rule == 78:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser_expression()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ast_transform_sub(self):
    current = self.tokens.current()
    rule = self.table[32][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(68, self.nonterminals[68]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 27:
      astParameters = OrderedDict([
        ('name', 0),
        ('parameters', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('AstTransformation', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(18) # lparen
      tree.add(t)
      subtree = self.parse__gen23()
      tree.add( subtree )
      t = self.expect(19) # rparen
      tree.add(t)
      return tree
    elif rule == 62:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(32) # nonterminal_reference
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_atom(self):
    current = self.tokens.current()
    rule = self.table[33][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(69, self.nonterminals[69]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_mode()
      tree.add( subtree )
      return tree
    elif rule == 57:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer_regex()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen2(self):
    current = self.tokens.current()
    rule = self.table[34][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(70, self.nonterminals[70]))
    tree.list = 'nlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen15(self):
    current = self.tokens.current()
    rule = self.table[35][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(71, self.nonterminals[71]))
    tree.list = False
    if current != None and (current.getId() in [18, 10, 21, 3]):
      return tree
    if current == None:
      return tree
    if rule == 94:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_led()
      tree.add( subtree )
      return tree
    return tree
  def parse_lexer_mode(self):
    current = self.tokens.current()
    rule = self.table[36][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(72, self.nonterminals[72]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 65:
      astParameters = OrderedDict([
        ('name', 2),
        ('atoms', 5),
      ])
      tree.astTransform = AstTransformNodeCreator('Mode', astParameters)
      t = self.expect(23) # mode
      tree.add(t)
      t = self.expect(0) # langle
      tree.add(t)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(1) # rangle
      tree.add(t)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen6()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_regex_options(self):
    current = self.tokens.current()
    rule = self.table[37][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(73, self.nonterminals[73]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 30:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen4()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen12(self):
    current = self.tokens.current()
    rule = self.table[38][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(74, self.nonterminals[74]))
    tree.list = 'nlist'
    if current != None and (current.getId() in [10]):
      return tree
    if current == None:
      return tree
    if rule == 71:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_expression_rule()
      tree.add( subtree )
      subtree = self.parse__gen12()
      tree.add( subtree )
      return tree
    return tree
  def parse_body_element(self):
    current = self.tokens.current()
    rule = self.table[39][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(75, self.nonterminals[75]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 88:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_body_element_sub()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_lexer_target(self):
    current = self.tokens.current()
    rule = self.table[40][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(76, self.nonterminals[76]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 10:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('Null', astParameters)
      t = self.expect(17) # null
      tree.add(t)
      return tree
    elif rule == 38:
      astParameters = OrderedDict([
        ('name', 0),
        ('terminal', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', astParameters)
      t = self.expect(25) # identifier
      tree.add(t)
      t = self.expect(18) # lparen
      tree.add(t)
      subtree = self.parse__gen5()
      tree.add( subtree )
      t = self.expect(19) # rparen
      tree.add(t)
      return tree
    elif rule == 39:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(22) # terminal
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen13(self):
    current = self.tokens.current()
    rule = self.table[41][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(77, self.nonterminals[77]))
    tree.list = False
    if current != None and (current.getId() in [3]):
      return tree
    if current == None:
      return tree
    if rule == 58:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_binding_power()
      tree.add( subtree )
      return tree
    return tree
  def parse_body_element_sub(self):
    current = self.tokens.current()
    rule = self.table[42][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(78, self.nonterminals[78]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 41:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 75:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_lexer()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen21(self):
    current = self.tokens.current()
    rule = self.table[43][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(79, self.nonterminals[79]))
    tree.list = 'nlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_parser_expression(self):
    current = self.tokens.current()
    rule = self.table[44][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(80, self.nonterminals[80]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 73:
      astParameters = OrderedDict([
        ('rules', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionParser', astParameters)
      t = self.expect(30) # parser_expression
      tree.add(t)
      t = self.expect(12) # lbrace
      tree.add(t)
      subtree = self.parse__gen12()
      tree.add( subtree )
      t = self.expect(10) # rbrace
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule(self):
    current = self.tokens.current()
    rule = self.table[45][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(81, self.nonterminals[81]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 17:
      astParameters = OrderedDict([
        ('nonterminal', 1),
        ('production', 3),
      ])
      tree.astTransform = AstTransformNodeCreator('Rule', astParameters)
      t = self.expect(2) # ll1_rule_hint
      tree.add(t)
      t = self.expect(31) # nonterminal
      tree.add(t)
      t = self.expect(28) # equals
      tree.add(t)
      subtree = self.parse_ll1_rule_rhs()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_precedence(self):
    current = self.tokens.current()
    rule = self.table[46][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(82, self.nonterminals[82]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 31:
      astParameters = OrderedDict([
        ('marker', 0),
        ('associativity', 2),
      ])
      tree.astTransform = AstTransformNodeCreator('Precedence', astParameters)
      subtree = self.parse_binding_power_marker()
      tree.add( subtree )
      t = self.expect(13) # colon
      tree.add(t)
      subtree = self.parse_associativity()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_ll1_rule_rhs(self):
    current = self.tokens.current()
    rule = self.table[47][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(83, self.nonterminals[83]))
    tree.list = False
    if current == None:
      return tree
    if rule == 6:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen8()
      tree.add( subtree )
      return tree
    elif rule == 11:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_parser()
      tree.add( subtree )
      return tree
    elif rule == 35:
      astParameters = OrderedDict([
      ])
      tree.astTransform = AstTransformNodeCreator('NullProduction', astParameters)
      t = self.expect(17) # null
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen20(self):
    current = self.tokens.current()
    rule = self.table[48][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(84, self.nonterminals[84]))
    tree.list = False
    if current != None and (current.getId() in [18, 10, 2, 3, 26, 35]):
      return tree
    if current == None:
      return tree
    if rule == 96:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    elif rule == 96:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    elif rule == 96:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    elif rule == 96:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    elif rule == 96:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_ast_transform()
      tree.add( subtree )
      return tree
    return tree
  def parse__gen18(self):
    current = self.tokens.current()
    rule = self.table[49][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(85, self.nonterminals[85]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen19(self):
    current = self.tokens.current()
    rule = self.table[50][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(86, self.nonterminals[86]))
    tree.list = 'nlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen14(self):
    current = self.tokens.current()
    rule = self.table[51][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(87, self.nonterminals[87]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen3(self):
    current = self.tokens.current()
    rule = self.table[52][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(88, self.nonterminals[88]))
    tree.list = False
    if current != None and (current.getId() in [21]):
      return tree
    if current == None:
      return tree
    if rule == 7:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_regex_options()
      tree.add( subtree )
      return tree
    return tree
  def parse_expression_rule(self):
    current = self.tokens.current()
    rule = self.table[53][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(89, self.nonterminals[89]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 60:
      astParameters = OrderedDict([
        ('precedence', 0),
        ('nonterminal', 2),
        ('production', 4),
      ])
      tree.astTransform = AstTransformNodeCreator('ExpressionRule', astParameters)
      subtree = self.parse__gen13()
      tree.add( subtree )
      t = self.expect(3) # expr_rule_hint
      tree.add(t)
      t = self.expect(31) # nonterminal
      tree.add(t)
      t = self.expect(28) # equals
      tree.add(t)
      subtree = self.parse_expression_rule_production()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power(self):
    current = self.tokens.current()
    rule = self.table[54][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(90, self.nonterminals[90]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 84:
      tree.astTransform = AstTransformSubstitution(1)
      t = self.expect(18) # lparen
      tree.add(t)
      subtree = self.parse_precedence()
      tree.add( subtree )
      t = self.expect(19) # rparen
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_binding_power_marker(self):
    current = self.tokens.current()
    rule = self.table[55][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(91, self.nonterminals[91]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 50:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(27) # dash
      tree.add(t)
      return tree
    elif rule == 99:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(8) # asterisk
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
