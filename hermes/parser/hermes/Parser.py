import sys
from collections import OrderedDict
from ..Common import *
terminals = {
    0: 'dash',
    1: 'lbrace',
    2: 'comma',
    3: 'expr_rule_hint',
    4: 'pipe',
    5: 'unary',
    6: 'grammar',
    7: 'regex',
    8: 'code',
    9: 'identifier',
    10: 'expression_divider',
    11: 'mode',
    12: 'rbrace',
    13: 'right',
    14: 'arrow',
    15: 'equals',
    16: 'langle',
    17: 'lparen',
    18: 'rangle',
    19: 'rparen',
    20: 'prefix_rule_hint',
    21: 'lexer',
    22: 'colon',
    23: 'll1_rule_hint',
    24: 'null',
    25: 'infix_rule_hint',
    26: 'parser_ll1',
    27: 'left',
    28: 'nonterminal_reference',
    29: 'nonterminal',
    30: 'parser_expression',
    31: 'terminal',
    32: 'integer',
    33: 'asterisk',
    34: 'mixfix_rule_hint',
    35: 'string',
    'dash': 0,
    'lbrace': 1,
    'comma': 2,
    'expr_rule_hint': 3,
    'pipe': 4,
    'unary': 5,
    'grammar': 6,
    'regex': 7,
    'code': 8,
    'identifier': 9,
    'expression_divider': 10,
    'mode': 11,
    'rbrace': 12,
    'right': 13,
    'arrow': 14,
    'equals': 15,
    'langle': 16,
    'lparen': 17,
    'rangle': 18,
    'rparen': 19,
    'prefix_rule_hint': 20,
    'lexer': 21,
    'colon': 22,
    'll1_rule_hint': 23,
    'null': 24,
    'infix_rule_hint': 25,
    'parser_ll1': 26,
    'left': 27,
    'nonterminal_reference': 28,
    'nonterminal': 29,
    'parser_expression': 30,
    'terminal': 31,
    'integer': 32,
    'asterisk': 33,
    'mixfix_rule_hint': 34,
    'string': 35,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 52, -1, -1, -1, -1, 53, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1],
    [-1, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 50, -1, -1, -1, -1, -1, -1, 49, -1, 50, -1, 50, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 6, 7, -1, -1, 6, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 16, -1, -1, 17, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, 44, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, 80, 82, -1, -1, 81],
    [-1, -1, -1, 37, 37, -1, -1, -1, -1, 36, -1, -1, 37, -1, 37, -1, -1, 37, -1, -1, -1, -1, -1, 37, -1, -1, -1, -1, -1, 36, -1, 36, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, 3, -1, -1, -1, 3, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 35, -1, -1, -1, -1, 35, -1, -1, 35, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, 35, 41, -1, 42, -1, -1, 35, 42, 35, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 27, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 54, -1, -1, -1, -1, -1, 54, -1, -1, 54, -1, 54, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, 54, -1, -1, -1, -1],
    [-1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 77, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, 74, 74, -1, -1, 74],
    [-1, -1, -1, -1, 40, -1, -1, -1, -1, 40, -1, -1, 40, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, -1, -1, -1, -1, 40, -1, 40, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, -1, -1],
    [59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, 63, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 11, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 39, 39, -1, -1, -1, -1, -1, 39, -1, 39, -1, 38, -1, -1, 39, -1, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 31, -1, -1, -1, -1, 31, -1, -1, 31, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, -1, -1, -1, -1, 31, -1, 31, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, 62, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, 5, -1, -1, -1, 5, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, 26, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 23, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1],
]
nonterminal_first = {
    36: [30],
    37: [20, 25, 34],
    38: [-1, 2],
    39: [26],
    40: [10, -1],
    41: [21],
    42: [11],
    43: [7, 11, -1],
    44: [9, -1],
    45: [17, 3, -1],
    46: [32, 29, 31, 35],
    47: [29, 9, -1, 31],
    48: [26, 30, 21],
    49: [26, 30, 29, 9, 4, 31, 24, -1, 14],
    50: [14],
    51: [17, 3],
    52: [23],
    53: [0, 33],
    54: [9],
    55: [-1, 23],
    56: [17, -1],
    57: [9, -1],
    58: [29, 9, -1, 31],
    59: [1],
    60: [17],
    61: [31, 29, -1, 32, 35],
    62: [29, 9, -1, 31, 14],
    63: [26, 30, 21, -1],
    64: [0, 33],
    65: [29, 9, 31],
    66: [7, 11],
    67: [7],
    68: [-1, 14],
    69: [8, -1],
    70: [-1, 2],
    71: [10],
    72: [14, 29, 9, -1, 31, 4],
    73: [27, 5, 13],
    74: [6],
    75: [26, 30, 21],
    76: [26, 30],
    77: [4, -1],
    78: [9, 28],
    79: [9],
    80: [-1, 1],
    81: [24, 9, 31],
    82: [-1, 31],
}
nonterminal_follow = {
    36: [26, 30, 21, 23, 12],
    37: [17, 3, 12],
    38: [19],
    39: [26, 30, 21, 23, 12],
    40: [17, 3, 12, 14],
    41: [26, 21, 30, 12],
    42: [7, 8, 11, 12],
    43: [12, 8],
    44: [12],
    45: [12],
    46: [19, 2],
    47: [17, 3, 4, 23, 12, 14],
    48: [26, 30, 12, 21],
    49: [12, 23],
    50: [17, 3, 4, 10, 23, 12],
    51: [17, 3, 12],
    52: [12, 23],
    53: [19],
    54: [19, 2],
    55: [12],
    56: [3],
    57: [19],
    58: [17, 3, 12, 14],
    59: [14],
    60: [3],
    61: [19],
    62: [12, 4, 23],
    63: [12],
    64: [22],
    65: [17, 29, 3, 9, 4, 31, 23, 12, 14],
    66: [7, 11, 12, 8],
    67: [7, 8, 11, 12],
    68: [17, 3, 4, 10, 23, 12],
    69: [12],
    70: [19],
    71: [17, 3, 12, 14],
    72: [12, 23],
    73: [19],
    74: [-1],
    75: [26, 21, 30, 12],
    76: [26, 30, 21, 23, 12],
    77: [12, 23],
    78: [17, 3, 4, 10, 23, 12],
    79: [17, 3, 4, 23, 29, 9, 31, 12, 14],
    80: [14],
    81: [7, 8, 11, 12],
    82: [19],
}
rule_first = {
    0: [26, 30, 21],
    1: [-1],
    2: [6],
    3: [26, 30, 21],
    4: [21],
    5: [26, 30],
    6: [7, 11],
    7: [-1],
    8: [8],
    9: [-1],
    10: [21],
    11: [7],
    12: [11],
    13: [1],
    14: [-1],
    15: [7],
    16: [9],
    17: [-1],
    18: [1],
    19: [31],
    20: [31],
    21: [-1],
    22: [9],
    23: [24],
    24: [11],
    25: [26],
    26: [30],
    27: [23],
    28: [-1],
    29: [26],
    30: [23],
    31: [29, 9, 4, 31, -1, 14],
    32: [4],
    33: [-1],
    34: [-1],
    35: [29, 9, 4, 31, -1, 14],
    36: [29, 9, 31],
    37: [-1],
    38: [14],
    39: [-1],
    40: [29, 9, -1, 31, 14],
    41: [24],
    42: [26, 30],
    43: [17, 3],
    44: [-1],
    45: [30],
    46: [17],
    47: [-1],
    48: [17, 3],
    49: [10],
    50: [-1],
    51: [34],
    52: [20],
    53: [25],
    54: [29, 9, -1, 31],
    55: [10],
    56: [17],
    57: [0, 33],
    58: [33],
    59: [0],
    60: [27],
    61: [13],
    62: [5],
    63: [31],
    64: [29],
    65: [9],
    66: [14],
    67: [9],
    68: [2],
    69: [-1],
    70: [-1],
    71: [9],
    72: [28],
    73: [9],
    74: [31, 29, 32, 35],
    75: [2],
    76: [-1],
    77: [-1],
    78: [9],
    79: [29],
    80: [31],
    81: [35],
    82: [32],
}
nonterminal_rules = {
    36: [
        "$parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    37: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    38: [
        "$_gen15 = :comma $ast_parameter $_gen15",
        "$_gen15 = :_empty",
    ],
    39: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )",
    ],
    40: [
        "$_gen13 = $led",
        "$_gen13 = :_empty",
    ],
    41: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    42: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    43: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    44: [
        "$_gen4 = :identifier $_gen4",
        "$_gen4 = :_empty",
    ],
    45: [
        "$_gen11 = $expression_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    46: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    47: [
        "$_gen9 = $morpheme $_gen9",
        "$_gen9 = :_empty",
    ],
    48: [
        "$body_element = $body_element_sub",
    ],
    49: [
        "$ll1_rule_rhs = $_gen7",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    50: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    51: [
        "$expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    52: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    53: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    54: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    55: [
        "$_gen6 = $ll1_rule $_gen6",
        "$_gen6 = :_empty",
    ],
    56: [
        "$_gen12 = $binding_power",
        "$_gen12 = :_empty",
    ],
    57: [
        "$_gen14 = $ast_parameter $_gen15",
        "$_gen14 = :_empty",
    ],
    58: [
        "$nud = $_gen9",
    ],
    59: [
        "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    ],
    60: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    61: [
        "$_gen16 = $macro_parameter $_gen17",
        "$_gen16 = :_empty",
    ],
    62: [
        "$rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )",
    ],
    63: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    64: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    65: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    66: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
    ],
    67: [
        "$lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    68: [
        "$_gen10 = $ast_transform",
        "$_gen10 = :_empty",
    ],
    69: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    70: [
        "$_gen17 = :comma $macro_parameter $_gen17",
        "$_gen17 = :_empty",
    ],
    71: [
        "$led = :expression_divider $_gen9 -> $1",
    ],
    72: [
        "$_gen7 = $rule $_gen8",
        "$_gen7 = :_empty",
    ],
    73: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    74: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    75: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    76: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    77: [
        "$_gen8 = :pipe $rule $_gen8",
        "$_gen8 = :_empty",
    ],
    78: [
        "$ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
    ],
    79: [
        "$macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    80: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    81: [
        "$lexer_target = :terminal",
        "$lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    82: [
        "$_gen5 = :terminal",
        "$_gen5 = :_empty",
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
    8: "$_gen2 = :code",
    9: "$_gen2 = :_empty",
    10: "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    11: "$lexer_atom = $lexer_regex",
    12: "$lexer_atom = $lexer_mode",
    13: "$_gen3 = $regex_options",
    14: "$_gen3 = :_empty",
    15: "$lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    16: "$_gen4 = :identifier $_gen4",
    17: "$_gen4 = :_empty",
    18: "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    19: "$lexer_target = :terminal",
    20: "$_gen5 = :terminal",
    21: "$_gen5 = :_empty",
    22: "$lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
    23: "$lexer_target = :null -> Null(  )",
    24: "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    25: "$parser = $parser_ll1",
    26: "$parser = $parser_expression",
    27: "$_gen6 = $ll1_rule $_gen6",
    28: "$_gen6 = :_empty",
    29: "$parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )",
    30: "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    31: "$_gen7 = $rule $_gen8",
    32: "$_gen8 = :pipe $rule $_gen8",
    33: "$_gen8 = :_empty",
    34: "$_gen7 = :_empty",
    35: "$ll1_rule_rhs = $_gen7",
    36: "$_gen9 = $morpheme $_gen9",
    37: "$_gen9 = :_empty",
    38: "$_gen10 = $ast_transform",
    39: "$_gen10 = :_empty",
    40: "$rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )",
    41: "$ll1_rule_rhs = :null -> NullProduction(  )",
    42: "$ll1_rule_rhs = $parser",
    43: "$_gen11 = $expression_rule $_gen11",
    44: "$_gen11 = :_empty",
    45: "$parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )",
    46: "$_gen12 = $binding_power",
    47: "$_gen12 = :_empty",
    48: "$expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    49: "$_gen13 = $led",
    50: "$_gen13 = :_empty",
    51: "$expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
    52: "$expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )",
    53: "$expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )",
    54: "$nud = $_gen9",
    55: "$led = :expression_divider $_gen9 -> $1",
    56: "$binding_power = :lparen $precedence :rparen -> $1",
    57: "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    58: "$binding_power_marker = :asterisk",
    59: "$binding_power_marker = :dash",
    60: "$associativity = :left",
    61: "$associativity = :right",
    62: "$associativity = :unary",
    63: "$morpheme = :terminal",
    64: "$morpheme = :nonterminal",
    65: "$morpheme = $macro",
    66: "$ast_transform = :arrow $ast_transform_sub -> $1",
    67: "$_gen14 = $ast_parameter $_gen15",
    68: "$_gen15 = :comma $ast_parameter $_gen15",
    69: "$_gen15 = :_empty",
    70: "$_gen14 = :_empty",
    71: "$ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )",
    72: "$ast_transform_sub = :nonterminal_reference",
    73: "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    74: "$_gen16 = $macro_parameter $_gen17",
    75: "$_gen17 = :comma $macro_parameter $_gen17",
    76: "$_gen17 = :_empty",
    77: "$_gen16 = :_empty",
    78: "$macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )",
    79: "$macro_parameter = :nonterminal",
    80: "$macro_parameter = :terminal",
    81: "$macro_parameter = :string",
    82: "$macro_parameter = :integer",
}
def is_terminal(id): return isinstance(id, int) and 0 <= id <= 35
def parse(tokens, error_formatter=None, start=None):
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
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(36, 'parser_expression'))
    ctx.nonterminal = "parser_expression"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 45: # $parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )
        ctx.rule = rules[45]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionParser', ast_parameters)
        t = expect(ctx, 30) # :parser_expression
        tree.add(t)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[36]],
      rules[45]
    ))
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(37, 'expression_rule_production'))
    ctx.nonterminal = "expression_rule_production"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 51: # $expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )
        ctx.rule = rules[51]
        ast_parameters = OrderedDict([
            ('nud', 1),
            ('nud_ast', 2),
            ('led', 3),
            ('ast', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('MixfixProduction', ast_parameters)
        t = expect(ctx, 34) # :mixfix_rule_hint
        tree.add(t)
        subtree = parse_nud(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        subtree = parse__gen13(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    elif rule == 52: # $expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[52]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('PrefixProduction', ast_parameters)
        t = expect(ctx, 20) # :prefix_rule_hint
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    elif rule == 53: # $expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )
        ctx.rule = rules[53]
        ast_parameters = OrderedDict([
            ('morphemes', 1),
            ('ast', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('InfixProduction', ast_parameters)
        t = expect(ctx, 25) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[37]],
      rules[53]
    ))
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(38, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[38] and current.id not in nonterminal_first[38]:
        return tree
    if current == None:
        return tree
    if rule == 68: # $_gen15 = :comma $ast_parameter $_gen15
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 2) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(39, 'parser_ll1'))
    ctx.nonterminal = "parser_ll1"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 29: # $parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )
        ctx.rule = rules[29]
        ast_parameters = OrderedDict([
            ('rules', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Parser', ast_parameters)
        t = expect(ctx, 26) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[39]],
      rules[29]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(40, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[40] and current.id not in nonterminal_first[40]:
        return tree
    if current == None:
        return tree
    if rule == 49: # $_gen13 = $led
        ctx.rule = rules[49]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_led(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, 'lexer'))
    ctx.nonterminal = "lexer"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 10: # $lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )
        ctx.rule = rules[10]
        ast_parameters = OrderedDict([
            ('language', 2),
            ('atoms', 5),
            ('code', 6),
        ])
        tree.astTransform = AstTransformNodeCreator('Lexer', ast_parameters)
        t = expect(ctx, 21) # :lexer
        tree.add(t)
        t = expect(ctx, 16) # :langle
        tree.add(t)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 18) # :rangle
        tree.add(t)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[41]],
      rules[10]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, 'lexer_mode'))
    ctx.nonterminal = "lexer_mode"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 24: # $lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )
        ctx.rule = rules[24]
        ast_parameters = OrderedDict([
            ('name', 2),
            ('atoms', 5),
        ])
        tree.astTransform = AstTransformNodeCreator('Mode', ast_parameters)
        t = expect(ctx, 11) # :mode
        tree.add(t)
        t = expect(ctx, 16) # :langle
        tree.add(t)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 18) # :rangle
        tree.add(t)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[42]],
      rules[24]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[43] and current.id not in nonterminal_first[43]:
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
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[44] and current.id not in nonterminal_first[44]:
        return tree
    if current == None:
        return tree
    if rule == 16: # $_gen4 = :identifier $_gen4
        ctx.rule = rules[16]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[45] and current.id not in nonterminal_first[45]:
        return tree
    if current == None:
        return tree
    if rule == 43: # $_gen11 = $expression_rule $_gen11
        ctx.rule = rules[43]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_expression_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $macro_parameter = :nonterminal
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 80: # $macro_parameter = :terminal
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :terminal
        tree.add(t)
        return tree
    elif rule == 81: # $macro_parameter = :string
        ctx.rule = rules[81]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 35) # :string
        tree.add(t)
        return tree
    elif rule == 82: # $macro_parameter = :integer
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 32) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[82]
    ))
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[47] and current.id not in nonterminal_first[47]:
        return tree
    if current == None:
        return tree
    if rule == 36: # $_gen9 = $morpheme $_gen9
        ctx.rule = rules[36]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_morpheme(ctx)
        tree.add(subtree)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[48]],
      rules[3]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'll1_rule_rhs'))
    ctx.nonterminal = "ll1_rule_rhs"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 35: # $ll1_rule_rhs = $_gen7
        ctx.rule = rules[35]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen7(ctx)
        tree.add(subtree)
        return tree
    elif rule == 41: # $ll1_rule_rhs = :null -> NullProduction(  )
        ctx.rule = rules[41]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('NullProduction', ast_parameters)
        t = expect(ctx, 24) # :null
        tree.add(t)
        return tree
    elif rule == 42: # $ll1_rule_rhs = $parser
        ctx.rule = rules[42]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[49]],
      rules[42]
    ))
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 66: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 14) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[50]],
      rules[66]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'expression_rule'))
    ctx.nonterminal = "expression_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 48: # $expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )
        ctx.rule = rules[48]
        ast_parameters = OrderedDict([
            ('precedence', 0),
            ('nonterminal', 2),
            ('production', 4),
        ])
        tree.astTransform = AstTransformNodeCreator('ExpressionRule', ast_parameters)
        subtree = parse__gen12(ctx)
        tree.add(subtree)
        t = expect(ctx, 3) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 29) # :nonterminal
        tree.add(t)
        t = expect(ctx, 15) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[51]],
      rules[48]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, 'll1_rule'))
    ctx.nonterminal = "ll1_rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 30: # $ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )
        ctx.rule = rules[30]
        ast_parameters = OrderedDict([
            ('nonterminal', 1),
            ('production', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Rule', ast_parameters)
        t = expect(ctx, 23) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 29) # :nonterminal
        tree.add(t)
        t = expect(ctx, 15) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[52]],
      rules[30]
    ))
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'precedence'))
    ctx.nonterminal = "precedence"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 57: # $precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )
        ctx.rule = rules[57]
        ast_parameters = OrderedDict([
            ('marker', 0),
            ('associativity', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Precedence', ast_parameters)
        subtree = parse_binding_power_marker(ctx)
        tree.add(subtree)
        t = expect(ctx, 22) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[57]
    ))
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, 'ast_parameter'))
    ctx.nonterminal = "ast_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 73: # $ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )
        ctx.rule = rules[73]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('index', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstParameter', ast_parameters)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 15) # :equals
        tree.add(t)
        t = expect(ctx, 28) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[54]],
      rules[73]
    ))
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[55] and current.id not in nonterminal_first[55]:
        return tree
    if current == None:
        return tree
    if rule == 27: # $_gen6 = $ll1_rule $_gen6
        ctx.rule = rules[27]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ll1_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = False
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 46: # $_gen12 = $binding_power
        ctx.rule = rules[46]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_binding_power(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[57] and current.id not in nonterminal_first[57]:
        return tree
    if current == None:
        return tree
    if rule == 67: # $_gen14 = $ast_parameter $_gen15
        ctx.rule = rules[67]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'nud'))
    ctx.nonterminal = "nud"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 54: # $nud = $_gen9
        ctx.rule = rules[54]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58]],
      rules[54]
    ))
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 18: # $regex_options = :lbrace $_gen4 :rbrace -> $1
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59]],
      rules[18]
    ))
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 17) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[56]
    ))
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
        return tree
    if current == None:
        return tree
    if rule == 74: # $_gen16 = $macro_parameter $_gen17
        ctx.rule = rules[74]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, 'rule'))
    ctx.nonterminal = "rule"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 40: # $rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )
        ctx.rule = rules[40]
        ast_parameters = OrderedDict([
            ('morphemes', 0),
            ('ast', 1),
        ])
        tree.astTransform = AstTransformNodeCreator('Production', ast_parameters)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[62]],
      rules[40]
    ))
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[63] and current.id not in nonterminal_first[63]:
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
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 58: # $binding_power_marker = :asterisk
        ctx.rule = rules[58]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :asterisk
        tree.add(t)
        return tree
    elif rule == 59: # $binding_power_marker = :dash
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 0) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[64]],
      rules[59]
    ))
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $morpheme = :terminal
        ctx.rule = rules[63]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :terminal
        tree.add(t)
        return tree
    elif rule == 64: # $morpheme = :nonterminal
        ctx.rule = rules[64]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 29) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 65: # $morpheme = $macro
        ctx.rule = rules[65]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_macro(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[65]],
      rules[65]
    ))
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, 'lexer_atom'))
    ctx.nonterminal = "lexer_atom"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 11: # $lexer_atom = $lexer_regex
        ctx.rule = rules[11]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_regex(ctx)
        tree.add(subtree)
        return tree
    elif rule == 12: # $lexer_atom = $lexer_mode
        ctx.rule = rules[12]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_lexer_mode(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[66]],
      rules[12]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'lexer_regex'))
    ctx.nonterminal = "lexer_regex"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 15: # $lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )
        ctx.rule = rules[15]
        ast_parameters = OrderedDict([
            ('regex', 0),
            ('options', 1),
            ('onmatch', 3),
        ])
        tree.astTransform = AstTransformNodeCreator('Regex', ast_parameters)
        t = expect(ctx, 7) # :regex
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 14) # :arrow
        tree.add(t)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[67]],
      rules[15]
    ))
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[68] and current.id not in nonterminal_first[68]:
        return tree
    if current == None:
        return tree
    if rule == 38: # $_gen10 = $ast_transform
        ctx.rule = rules[38]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_ast_transform(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[69] and current.id not in nonterminal_first[69]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 8) # :code
        tree.add(t)
        return tree
    return tree
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[70] and current.id not in nonterminal_first[70]:
        return tree
    if current == None:
        return tree
    if rule == 75: # $_gen17 = :comma $macro_parameter $_gen17
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 2) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 55: # $led = :expression_divider $_gen9 -> $1
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 10) # :expression_divider
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71]],
      rules[55]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[72] and current.id not in nonterminal_first[72]:
        return tree
    if current == None:
        return tree
    if rule == 31: # $_gen7 = $rule $_gen8
        ctx.rule = rules[31]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_associativity(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $associativity = :left
        ctx.rule = rules[60]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 27) # :left
        tree.add(t)
        return tree
    elif rule == 61: # $associativity = :right
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 13) # :right
        tree.add(t)
        return tree
    elif rule == 62: # $associativity = :unary
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 5) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[73]],
      rules[62]
    ))
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'grammar'))
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
        t = expect(ctx, 6) # :grammar
        tree.add(t)
        t = expect(ctx, 1) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 12) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[74]],
      rules[2]
    ))
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[75]],
      rules[5]
    ))
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, 'parser'))
    ctx.nonterminal = "parser"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 25: # $parser = $parser_ll1
        ctx.rule = rules[25]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_ll1(ctx)
        tree.add(subtree)
        return tree
    elif rule == 26: # $parser = $parser_expression
        ctx.rule = rules[26]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_parser_expression(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[76]],
      rules[26]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[77] and current.id not in nonterminal_first[77]:
        return tree
    if current == None:
        return tree
    if rule == 32: # $_gen8 = :pipe $rule $_gen8
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 4) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, 'ast_transform_sub'))
    ctx.nonterminal = "ast_transform_sub"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 71: # $ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )
        ctx.rule = rules[71]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('AstTransformation', ast_parameters)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 17) # :lparen
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rparen
        tree.add(t)
        return tree
    elif rule == 72: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 28) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[78]],
      rules[72]
    ))
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'macro'))
    ctx.nonterminal = "macro"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 78: # $macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )
        ctx.rule = rules[78]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('parameters', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('Macro', ast_parameters)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 17) # :lparen
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[79]],
      rules[78]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = False
    if current != None and current.id in nonterminal_follow[80] and current.id not in nonterminal_first[80]:
        return tree
    if current == None:
        return tree
    if rule == 13: # $_gen3 = $regex_options
        ctx.rule = rules[13]
        tree.astTransform = AstTransformSubstitution(0)
        subtree = parse_regex_options(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 19: # $lexer_target = :terminal
        ctx.rule = rules[19]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :terminal
        tree.add(t)
        return tree
    elif rule == 22: # $lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[22]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 9) # :identifier
        tree.add(t)
        t = expect(ctx, 17) # :lparen
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 19) # :rparen
        tree.add(t)
        return tree
    elif rule == 23: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[23]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 24) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[23]
    ))
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = False
    if current != None and current.id in nonterminal_follow[82] and current.id not in nonterminal_first[82]:
        return tree
    if current == None:
        return tree
    if rule == 20: # $_gen5 = :terminal
        ctx.rule = rules[20]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :terminal
        tree.add(t)
        return tree
    return tree
