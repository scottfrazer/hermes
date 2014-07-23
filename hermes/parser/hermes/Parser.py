import sys
from collections import OrderedDict
from ..Common import *
terminals = {
    0: 'expression_divider',
    1: 'll1_rule_hint',
    2: 'arrow',
    3: 'langle',
    4: 'grammar',
    5: 'pipe',
    6: 'equals',
    7: 'rbrace',
    8: 'expr_rule_hint',
    9: 'infix_rule_hint',
    10: 'identifier',
    11: 'lexer',
    12: 'null',
    13: 'lparen',
    14: 'prefix_rule_hint',
    15: 'string',
    16: 'asterisk',
    17: 'right',
    18: 'parser_ll1',
    19: 'integer',
    20: 'rparen',
    21: 'rangle',
    22: 'comma',
    23: 'colon',
    24: 'lbrace',
    25: 'dash',
    26: 'mixfix_rule_hint',
    27: 'mode',
    28: 'nonterminal',
    29: 'parser_expression',
    30: 'terminal',
    31: 'code',
    32: 'left',
    33: 'nonterminal_reference',
    34: 'unary',
    35: 'regex',
    'expression_divider': 0,
    'll1_rule_hint': 1,
    'arrow': 2,
    'langle': 3,
    'grammar': 4,
    'pipe': 5,
    'equals': 6,
    'rbrace': 7,
    'expr_rule_hint': 8,
    'infix_rule_hint': 9,
    'identifier': 10,
    'lexer': 11,
    'null': 12,
    'lparen': 13,
    'prefix_rule_hint': 14,
    'string': 15,
    'asterisk': 16,
    'right': 17,
    'parser_ll1': 18,
    'integer': 19,
    'rparen': 20,
    'rangle': 21,
    'comma': 22,
    'colon': 23,
    'lbrace': 24,
    'dash': 25,
    'mixfix_rule_hint': 26,
    'mode': 27,
    'nonterminal': 28,
    'parser_expression': 29,
    'terminal': 30,
    'code': 31,
    'left': 32,
    'nonterminal_reference': 33,
    'unary': 34,
    'regex': 35,
}
# table[nonterminal][terminal] = rule
table = [
    [-1, 37, 37, -1, -1, 37, -1, 37, 37, -1, 36, -1, -1, 37, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 36, -1, 36, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 47, -1, -1, -1, -1, 46, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 3, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 15],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 22, -1, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 73, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 35, 35, -1, -1, 35, -1, 35, -1, -1, 35, -1, 41, -1, -1, -1, -1, -1, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, 35, 42, 35, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 65, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 64, -1, 63, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 81, -1, -1, -1, 82, -1, -1, -1, -1, -1, -1, -1, -1, 79, -1, 80, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, -1, -1, -1, -1, -1, -1, -1, 59, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, 48, -1, -1, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 45, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 5, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 6, -1, -1, -1, 7, -1, -1, -1, 6],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, -1, -1, -1, -1, -1, -1],
    [-1, 27, -1, -1, -1, -1, -1, 28, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, 53, -1, -1, -1, -1, 52, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 14, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 69, -1, 68, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 78, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [55, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 29, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [49, -1, 50, -1, -1, -1, -1, 50, 50, -1, -1, -1, -1, 50, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 21, -1, -1, -1, -1, -1, -1, -1, -1, -1, 20, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 12, -1, -1, -1, -1, -1, -1, -1, 11],
    [-1, 40, 40, -1, -1, 40, -1, 40, -1, -1, 40, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 40, -1, 40, -1, -1, -1, -1, -1],
    [-1, 33, -1, -1, -1, 32, -1, 33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, 54, -1, -1, -1, -1, 54, 54, -1, 54, -1, -1, 54, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 54, -1, 54, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 44, 43, -1, -1, -1, -1, 43, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 17, -1, -1, 16, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 56, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 67, -1, -1, -1, -1, -1, -1, -1, -1, -1, 70, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [39, 39, 38, -1, -1, 39, -1, 39, 39, -1, -1, -1, -1, 39, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, 57, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 76, -1, 75, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 74, -1, -1, -1, 74, 77, -1, -1, -1, -1, -1, -1, -1, 74, -1, 74, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, -1, -1, -1, -1],
    [-1, -1, 66, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, 31, 31, -1, -1, 31, -1, 31, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 31, -1, 31, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 61, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 60, -1, 62, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 71, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 72, -1, -1],
]
nonterminal_first = {
    36: [30, 10, -1, 28],
    37: [-1, 13],
    38: [18, 29, 11],
    39: [35],
    40: [12, 30, 10],
    41: [10],
    42: [29, 30, 10, 12, 2, 5, -1, 28, 18],
    43: [27],
    44: [28, 30, 10],
    45: [28, 30, 15, 19],
    46: [25, 16],
    47: [8, 13],
    48: [29],
    49: [18, 29, 11],
    50: [-1, 35, 27],
    51: [18, 29],
    52: [-1, 1],
    53: [26, 9, 14],
    54: [-1, 24],
    55: [24],
    56: [22, -1],
    57: [10],
    58: [1],
    59: [0],
    60: [18],
    61: [0, -1],
    62: [-1, 30],
    63: [35, 27],
    64: [30, 10, -1, 2, 28],
    65: [-1, 5],
    66: [4],
    67: [-1, 28, 30, 10],
    68: [-1, 8, 13],
    69: [-1, 10],
    70: [-1, 18, 29, 11],
    71: [13],
    72: [-1, 10],
    73: [-1, 2],
    74: [11],
    75: [25, 16],
    76: [22, -1],
    77: [-1, 28, 30, 15, 19],
    78: [31, -1],
    79: [2],
    80: [30, 10, 5, 2, -1, 28],
    81: [32, 34, 17],
    82: [33, 10],
}
nonterminal_follow = {
    36: [1, 2, 13, 5, 7, 8],
    37: [8],
    38: [18, 29, 7, 11],
    39: [31, 35, 27, 7],
    40: [31, 35, 27, 7],
    41: [22, 20],
    42: [1, 7],
    43: [31, 35, 27, 7],
    44: [1, 30, 10, 2, 13, 5, 28, 7, 8],
    45: [22, 20],
    46: [23],
    47: [7, 8, 13],
    48: [1, 29, 11, 18, 7],
    49: [29, 11, 18, 7],
    50: [31, 7],
    51: [1, 29, 11, 18, 7],
    52: [7],
    53: [7, 8, 13],
    54: [2],
    55: [2],
    56: [20],
    57: [1, 2, 5, 28, 7, 8, 30, 10, 13],
    58: [1, 7],
    59: [2, 7, 8, 13],
    60: [1, 29, 11, 18, 7],
    61: [2, 7, 8, 13],
    62: [20],
    63: [31, 35, 27, 7],
    64: [1, 7, 5],
    65: [1, 7],
    66: [-1],
    67: [2, 7, 8, 13],
    68: [7],
    69: [7],
    70: [7],
    71: [8],
    72: [20],
    73: [0, 1, 13, 5, 7, 8],
    74: [29, 11, 18, 7],
    75: [20],
    76: [20],
    77: [20],
    78: [7],
    79: [0, 1, 13, 5, 7, 8],
    80: [1, 7],
    81: [20],
    82: [0, 1, 13, 5, 7, 8],
}
rule_first = {
    0: [18, 29, 11],
    1: [-1],
    2: [4],
    3: [18, 29, 11],
    4: [11],
    5: [18, 29],
    6: [35, 27],
    7: [-1],
    8: [31],
    9: [-1],
    10: [11],
    11: [35],
    12: [27],
    13: [24],
    14: [-1],
    15: [35],
    16: [10],
    17: [-1],
    18: [24],
    19: [30],
    20: [30],
    21: [-1],
    22: [10],
    23: [12],
    24: [27],
    25: [18],
    26: [29],
    27: [1],
    28: [-1],
    29: [18],
    30: [1],
    31: [30, 10, 2, 5, -1, 28],
    32: [5],
    33: [-1],
    34: [-1],
    35: [30, 10, 2, 5, -1, 28],
    36: [28, 30, 10],
    37: [-1],
    38: [2],
    39: [-1],
    40: [2, -1, 28, 30, 10],
    41: [12],
    42: [18, 29],
    43: [8, 13],
    44: [-1],
    45: [29],
    46: [13],
    47: [-1],
    48: [8, 13],
    49: [0],
    50: [-1],
    51: [26],
    52: [14],
    53: [9],
    54: [-1, 28, 30, 10],
    55: [0],
    56: [13],
    57: [25, 16],
    58: [16],
    59: [25],
    60: [32],
    61: [17],
    62: [34],
    63: [30],
    64: [28],
    65: [10],
    66: [2],
    67: [10],
    68: [22],
    69: [-1],
    70: [-1],
    71: [10],
    72: [33],
    73: [10],
    74: [28, 30, 15, 19],
    75: [22],
    76: [-1],
    77: [-1],
    78: [10],
    79: [28],
    80: [30],
    81: [15],
    82: [19],
}
nonterminal_rules = {
    36: [
        "$_gen9 = $morpheme $_gen9",
        "$_gen9 = :_empty",
    ],
    37: [
        "$_gen12 = $binding_power",
        "$_gen12 = :_empty",
    ],
    38: [
        "$body_element = $body_element_sub",
    ],
    39: [
        "$lexer_regex = :regex $_gen3 :arrow $lexer_target -> Regex( regex=$0, options=$1, onmatch=$3 )",
    ],
    40: [
        "$lexer_target = :terminal",
        "$lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )",
        "$lexer_target = :null -> Null(  )",
    ],
    41: [
        "$ast_parameter = :identifier :equals :nonterminal_reference -> AstParameter( name=$0, index=$2 )",
    ],
    42: [
        "$ll1_rule_rhs = $_gen7",
        "$ll1_rule_rhs = :null -> NullProduction(  )",
        "$ll1_rule_rhs = $parser",
    ],
    43: [
        "$lexer_mode = :mode :langle :identifier :rangle :lbrace $_gen1 :rbrace -> Mode( name=$2, atoms=$5 )",
    ],
    44: [
        "$morpheme = :terminal",
        "$morpheme = :nonterminal",
        "$morpheme = $macro",
    ],
    45: [
        "$macro_parameter = :nonterminal",
        "$macro_parameter = :terminal",
        "$macro_parameter = :string",
        "$macro_parameter = :integer",
    ],
    46: [
        "$binding_power_marker = :asterisk",
        "$binding_power_marker = :dash",
    ],
    47: [
        "$expression_rule = $_gen12 :expr_rule_hint :nonterminal :equals $expression_rule_production -> ExpressionRule( precedence=$0, nonterminal=$2, production=$4 )",
    ],
    48: [
        "$parser_expression = :parser_expression :lbrace $_gen11 :rbrace -> ExpressionParser( rules=$2 )",
    ],
    49: [
        "$body_element_sub = $lexer",
        "$body_element_sub = $parser",
    ],
    50: [
        "$_gen1 = $lexer_atom $_gen1",
        "$_gen1 = :_empty",
    ],
    51: [
        "$parser = $parser_ll1",
        "$parser = $parser_expression",
    ],
    52: [
        "$_gen6 = $ll1_rule $_gen6",
        "$_gen6 = :_empty",
    ],
    53: [
        "$expression_rule_production = :mixfix_rule_hint $nud $_gen10 $_gen13 $_gen10 -> MixfixProduction( nud=$1, nud_ast=$2, led=$3, ast=$4 )",
        "$expression_rule_production = :prefix_rule_hint $_gen9 $_gen10 -> PrefixProduction( morphemes=$1, ast=$2 )",
        "$expression_rule_production = :infix_rule_hint $_gen9 $_gen10 -> InfixProduction( morphemes=$1, ast=$2 )",
    ],
    54: [
        "$_gen3 = $regex_options",
        "$_gen3 = :_empty",
    ],
    55: [
        "$regex_options = :lbrace $_gen4 :rbrace -> $1",
    ],
    56: [
        "$_gen15 = :comma $ast_parameter $_gen15",
        "$_gen15 = :_empty",
    ],
    57: [
        "$macro = :identifier :lparen $_gen16 :rparen -> Macro( name=$0, parameters=$2 )",
    ],
    58: [
        "$ll1_rule = :ll1_rule_hint :nonterminal :equals $ll1_rule_rhs -> Rule( nonterminal=$1, production=$3 )",
    ],
    59: [
        "$led = :expression_divider $_gen9 -> $1",
    ],
    60: [
        "$parser_ll1 = :parser_ll1 :lbrace $_gen6 :rbrace -> Parser( rules=$2 )",
    ],
    61: [
        "$_gen13 = $led",
        "$_gen13 = :_empty",
    ],
    62: [
        "$_gen5 = :terminal",
        "$_gen5 = :_empty",
    ],
    63: [
        "$lexer_atom = $lexer_regex",
        "$lexer_atom = $lexer_mode",
    ],
    64: [
        "$rule = $_gen9 $_gen10 -> Production( morphemes=$0, ast=$1 )",
    ],
    65: [
        "$_gen8 = :pipe $rule $_gen8",
        "$_gen8 = :_empty",
    ],
    66: [
        "$grammar = :grammar :lbrace $_gen0 :rbrace -> Grammar( body=$2 )",
    ],
    67: [
        "$nud = $_gen9",
    ],
    68: [
        "$_gen11 = $expression_rule $_gen11",
        "$_gen11 = :_empty",
    ],
    69: [
        "$_gen4 = :identifier $_gen4",
        "$_gen4 = :_empty",
    ],
    70: [
        "$_gen0 = $body_element $_gen0",
        "$_gen0 = :_empty",
    ],
    71: [
        "$binding_power = :lparen $precedence :rparen -> $1",
    ],
    72: [
        "$_gen14 = $ast_parameter $_gen15",
        "$_gen14 = :_empty",
    ],
    73: [
        "$_gen10 = $ast_transform",
        "$_gen10 = :_empty",
    ],
    74: [
        "$lexer = :lexer :langle :identifier :rangle :lbrace $_gen1 $_gen2 :rbrace -> Lexer( language=$2, atoms=$5, code=$6 )",
    ],
    75: [
        "$precedence = $binding_power_marker :colon $associativity -> Precedence( marker=$0, associativity=$2 )",
    ],
    76: [
        "$_gen17 = :comma $macro_parameter $_gen17",
        "$_gen17 = :_empty",
    ],
    77: [
        "$_gen16 = $macro_parameter $_gen17",
        "$_gen16 = :_empty",
    ],
    78: [
        "$_gen2 = :code",
        "$_gen2 = :_empty",
    ],
    79: [
        "$ast_transform = :arrow $ast_transform_sub -> $1",
    ],
    80: [
        "$_gen7 = $rule $_gen8",
        "$_gen7 = :_empty",
    ],
    81: [
        "$associativity = :left",
        "$associativity = :right",
        "$associativity = :unary",
    ],
    82: [
        "$ast_transform_sub = :identifier :lparen $_gen14 :rparen -> AstTransformation( name=$0, parameters=$2 )",
        "$ast_transform_sub = :nonterminal_reference",
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
def parse__gen9(ctx):
    current = ctx.tokens.current()
    rule = table[0][current.id] if current else -1
    tree = ParseTree(NonTerminal(36, '_gen9'))
    ctx.nonterminal = "_gen9"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[36] and current.id not in nonterminal_first[36]:
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
def parse__gen12(ctx):
    current = ctx.tokens.current()
    rule = table[1][current.id] if current else -1
    tree = ParseTree(NonTerminal(37, '_gen12'))
    ctx.nonterminal = "_gen12"
    tree.list = False
    if current != None and current.id in nonterminal_follow[37] and current.id not in nonterminal_first[37]:
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
def parse_body_element(ctx):
    current = ctx.tokens.current()
    rule = table[2][current.id] if current else -1
    tree = ParseTree(NonTerminal(38, 'body_element'))
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
      [terminals[x] for x in nonterminal_first[38]],
      rules[3]
    ))
def parse_lexer_regex(ctx):
    current = ctx.tokens.current()
    rule = table[3][current.id] if current else -1
    tree = ParseTree(NonTerminal(39, 'lexer_regex'))
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
        t = expect(ctx, 35) # :regex
        tree.add(t)
        subtree = parse__gen3(ctx)
        tree.add(subtree)
        t = expect(ctx, 2) # :arrow
        tree.add(t)
        subtree = parse_lexer_target(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[39]],
      rules[15]
    ))
def parse_lexer_target(ctx):
    current = ctx.tokens.current()
    rule = table[4][current.id] if current else -1
    tree = ParseTree(NonTerminal(40, 'lexer_target'))
    ctx.nonterminal = "lexer_target"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 19: # $lexer_target = :terminal
        ctx.rule = rules[19]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :terminal
        tree.add(t)
        return tree
    elif rule == 22: # $lexer_target = :identifier :lparen $_gen5 :rparen -> LexerFunctionCall( name=$0, terminal=$2 )
        ctx.rule = rules[22]
        ast_parameters = OrderedDict([
            ('name', 0),
            ('terminal', 2),
        ])
        tree.astTransform = AstTransformNodeCreator('LexerFunctionCall', ast_parameters)
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen5(ctx)
        tree.add(subtree)
        t = expect(ctx, 20) # :rparen
        tree.add(t)
        return tree
    elif rule == 23: # $lexer_target = :null -> Null(  )
        ctx.rule = rules[23]
        ast_parameters = OrderedDict([
        ])
        tree.astTransform = AstTransformNodeCreator('Null', ast_parameters)
        t = expect(ctx, 12) # :null
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[40]],
      rules[23]
    ))
def parse_ast_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[5][current.id] if current else -1
    tree = ParseTree(NonTerminal(41, 'ast_parameter'))
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
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 6) # :equals
        tree.add(t)
        t = expect(ctx, 33) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[41]],
      rules[73]
    ))
def parse_ll1_rule_rhs(ctx):
    current = ctx.tokens.current()
    rule = table[6][current.id] if current else -1
    tree = ParseTree(NonTerminal(42, 'll1_rule_rhs'))
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
        t = expect(ctx, 12) # :null
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
      [terminals[x] for x in nonterminal_first[42]],
      rules[42]
    ))
def parse_lexer_mode(ctx):
    current = ctx.tokens.current()
    rule = table[7][current.id] if current else -1
    tree = ParseTree(NonTerminal(43, 'lexer_mode'))
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
        t = expect(ctx, 27) # :mode
        tree.add(t)
        t = expect(ctx, 3) # :langle
        tree.add(t)
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 21) # :rangle
        tree.add(t)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[43]],
      rules[24]
    ))
def parse_morpheme(ctx):
    current = ctx.tokens.current()
    rule = table[8][current.id] if current else -1
    tree = ParseTree(NonTerminal(44, 'morpheme'))
    ctx.nonterminal = "morpheme"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 63: # $morpheme = :terminal
        ctx.rule = rules[63]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :terminal
        tree.add(t)
        return tree
    elif rule == 64: # $morpheme = :nonterminal
        ctx.rule = rules[64]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 28) # :nonterminal
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
      [terminals[x] for x in nonterminal_first[44]],
      rules[65]
    ))
def parse_macro_parameter(ctx):
    current = ctx.tokens.current()
    rule = table[9][current.id] if current else -1
    tree = ParseTree(NonTerminal(45, 'macro_parameter'))
    ctx.nonterminal = "macro_parameter"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 79: # $macro_parameter = :nonterminal
        ctx.rule = rules[79]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 28) # :nonterminal
        tree.add(t)
        return tree
    elif rule == 80: # $macro_parameter = :terminal
        ctx.rule = rules[80]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :terminal
        tree.add(t)
        return tree
    elif rule == 81: # $macro_parameter = :string
        ctx.rule = rules[81]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 15) # :string
        tree.add(t)
        return tree
    elif rule == 82: # $macro_parameter = :integer
        ctx.rule = rules[82]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 19) # :integer
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[45]],
      rules[82]
    ))
def parse_binding_power_marker(ctx):
    current = ctx.tokens.current()
    rule = table[10][current.id] if current else -1
    tree = ParseTree(NonTerminal(46, 'binding_power_marker'))
    ctx.nonterminal = "binding_power_marker"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 58: # $binding_power_marker = :asterisk
        ctx.rule = rules[58]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 16) # :asterisk
        tree.add(t)
        return tree
    elif rule == 59: # $binding_power_marker = :dash
        ctx.rule = rules[59]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 25) # :dash
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[46]],
      rules[59]
    ))
def parse_expression_rule(ctx):
    current = ctx.tokens.current()
    rule = table[11][current.id] if current else -1
    tree = ParseTree(NonTerminal(47, 'expression_rule'))
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
        t = expect(ctx, 8) # :expr_rule_hint
        tree.add(t)
        t = expect(ctx, 28) # :nonterminal
        tree.add(t)
        t = expect(ctx, 6) # :equals
        tree.add(t)
        subtree = parse_expression_rule_production(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[47]],
      rules[48]
    ))
def parse_parser_expression(ctx):
    current = ctx.tokens.current()
    rule = table[12][current.id] if current else -1
    tree = ParseTree(NonTerminal(48, 'parser_expression'))
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
        t = expect(ctx, 29) # :parser_expression
        tree.add(t)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen11(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[48]],
      rules[45]
    ))
def parse_body_element_sub(ctx):
    current = ctx.tokens.current()
    rule = table[13][current.id] if current else -1
    tree = ParseTree(NonTerminal(49, 'body_element_sub'))
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
      [terminals[x] for x in nonterminal_first[49]],
      rules[5]
    ))
def parse__gen1(ctx):
    current = ctx.tokens.current()
    rule = table[14][current.id] if current else -1
    tree = ParseTree(NonTerminal(50, '_gen1'))
    ctx.nonterminal = "_gen1"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[50] and current.id not in nonterminal_first[50]:
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
def parse_parser(ctx):
    current = ctx.tokens.current()
    rule = table[15][current.id] if current else -1
    tree = ParseTree(NonTerminal(51, 'parser'))
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
      [terminals[x] for x in nonterminal_first[51]],
      rules[26]
    ))
def parse__gen6(ctx):
    current = ctx.tokens.current()
    rule = table[16][current.id] if current else -1
    tree = ParseTree(NonTerminal(52, '_gen6'))
    ctx.nonterminal = "_gen6"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[52] and current.id not in nonterminal_first[52]:
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
def parse_expression_rule_production(ctx):
    current = ctx.tokens.current()
    rule = table[17][current.id] if current else -1
    tree = ParseTree(NonTerminal(53, 'expression_rule_production'))
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
        t = expect(ctx, 26) # :mixfix_rule_hint
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
        t = expect(ctx, 14) # :prefix_rule_hint
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
        t = expect(ctx, 9) # :infix_rule_hint
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        subtree = parse__gen10(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[53]],
      rules[53]
    ))
def parse__gen3(ctx):
    current = ctx.tokens.current()
    rule = table[18][current.id] if current else -1
    tree = ParseTree(NonTerminal(54, '_gen3'))
    ctx.nonterminal = "_gen3"
    tree.list = False
    if current != None and current.id in nonterminal_follow[54] and current.id not in nonterminal_first[54]:
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
def parse_regex_options(ctx):
    current = ctx.tokens.current()
    rule = table[19][current.id] if current else -1
    tree = ParseTree(NonTerminal(55, 'regex_options'))
    ctx.nonterminal = "regex_options"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 18: # $regex_options = :lbrace $_gen4 :rbrace -> $1
        ctx.rule = rules[18]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[55]],
      rules[18]
    ))
def parse__gen15(ctx):
    current = ctx.tokens.current()
    rule = table[20][current.id] if current else -1
    tree = ParseTree(NonTerminal(56, '_gen15'))
    ctx.nonterminal = "_gen15"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[56] and current.id not in nonterminal_first[56]:
        return tree
    if current == None:
        return tree
    if rule == 68: # $_gen15 = :comma $ast_parameter $_gen15
        ctx.rule = rules[68]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 22) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_ast_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen15(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_macro(ctx):
    current = ctx.tokens.current()
    rule = table[21][current.id] if current else -1
    tree = ParseTree(NonTerminal(57, 'macro'))
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
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen16(ctx)
        tree.add(subtree)
        t = expect(ctx, 20) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[57]],
      rules[78]
    ))
def parse_ll1_rule(ctx):
    current = ctx.tokens.current()
    rule = table[22][current.id] if current else -1
    tree = ParseTree(NonTerminal(58, 'll1_rule'))
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
        t = expect(ctx, 1) # :ll1_rule_hint
        tree.add(t)
        t = expect(ctx, 28) # :nonterminal
        tree.add(t)
        t = expect(ctx, 6) # :equals
        tree.add(t)
        subtree = parse_ll1_rule_rhs(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[58]],
      rules[30]
    ))
def parse_led(ctx):
    current = ctx.tokens.current()
    rule = table[23][current.id] if current else -1
    tree = ParseTree(NonTerminal(59, 'led'))
    ctx.nonterminal = "led"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 55: # $led = :expression_divider $_gen9 -> $1
        ctx.rule = rules[55]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 0) # :expression_divider
        tree.add(t)
        subtree = parse__gen9(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[59]],
      rules[55]
    ))
def parse_parser_ll1(ctx):
    current = ctx.tokens.current()
    rule = table[24][current.id] if current else -1
    tree = ParseTree(NonTerminal(60, 'parser_ll1'))
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
        t = expect(ctx, 18) # :parser_ll1
        tree.add(t)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen6(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[60]],
      rules[29]
    ))
def parse__gen13(ctx):
    current = ctx.tokens.current()
    rule = table[25][current.id] if current else -1
    tree = ParseTree(NonTerminal(61, '_gen13'))
    ctx.nonterminal = "_gen13"
    tree.list = False
    if current != None and current.id in nonterminal_follow[61] and current.id not in nonterminal_first[61]:
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
def parse__gen5(ctx):
    current = ctx.tokens.current()
    rule = table[26][current.id] if current else -1
    tree = ParseTree(NonTerminal(62, '_gen5'))
    ctx.nonterminal = "_gen5"
    tree.list = False
    if current != None and current.id in nonterminal_follow[62] and current.id not in nonterminal_first[62]:
        return tree
    if current == None:
        return tree
    if rule == 20: # $_gen5 = :terminal
        ctx.rule = rules[20]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 30) # :terminal
        tree.add(t)
        return tree
    return tree
def parse_lexer_atom(ctx):
    current = ctx.tokens.current()
    rule = table[27][current.id] if current else -1
    tree = ParseTree(NonTerminal(63, 'lexer_atom'))
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
      [terminals[x] for x in nonterminal_first[63]],
      rules[12]
    ))
def parse_rule(ctx):
    current = ctx.tokens.current()
    rule = table[28][current.id] if current else -1
    tree = ParseTree(NonTerminal(64, 'rule'))
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
      [terminals[x] for x in nonterminal_first[64]],
      rules[40]
    ))
def parse__gen8(ctx):
    current = ctx.tokens.current()
    rule = table[29][current.id] if current else -1
    tree = ParseTree(NonTerminal(65, '_gen8'))
    ctx.nonterminal = "_gen8"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[65] and current.id not in nonterminal_first[65]:
        return tree
    if current == None:
        return tree
    if rule == 32: # $_gen8 = :pipe $rule $_gen8
        ctx.rule = rules[32]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 5) # :pipe
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_rule(ctx)
        tree.add(subtree)
        subtree = parse__gen8(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse_grammar(ctx):
    current = ctx.tokens.current()
    rule = table[30][current.id] if current else -1
    tree = ParseTree(NonTerminal(66, 'grammar'))
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
        t = expect(ctx, 4) # :grammar
        tree.add(t)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen0(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[66]],
      rules[2]
    ))
def parse_nud(ctx):
    current = ctx.tokens.current()
    rule = table[31][current.id] if current else -1
    tree = ParseTree(NonTerminal(67, 'nud'))
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
      [terminals[x] for x in nonterminal_first[67]],
      rules[54]
    ))
def parse__gen11(ctx):
    current = ctx.tokens.current()
    rule = table[32][current.id] if current else -1
    tree = ParseTree(NonTerminal(68, '_gen11'))
    ctx.nonterminal = "_gen11"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[68] and current.id not in nonterminal_first[68]:
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
def parse__gen4(ctx):
    current = ctx.tokens.current()
    rule = table[33][current.id] if current else -1
    tree = ParseTree(NonTerminal(69, '_gen4'))
    ctx.nonterminal = "_gen4"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[69] and current.id not in nonterminal_first[69]:
        return tree
    if current == None:
        return tree
    if rule == 16: # $_gen4 = :identifier $_gen4
        ctx.rule = rules[16]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        subtree = parse__gen4(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen0(ctx):
    current = ctx.tokens.current()
    rule = table[34][current.id] if current else -1
    tree = ParseTree(NonTerminal(70, '_gen0'))
    ctx.nonterminal = "_gen0"
    tree.list = 'nlist'
    if current != None and current.id in nonterminal_follow[70] and current.id not in nonterminal_first[70]:
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
def parse_binding_power(ctx):
    current = ctx.tokens.current()
    rule = table[35][current.id] if current else -1
    tree = ParseTree(NonTerminal(71, 'binding_power'))
    ctx.nonterminal = "binding_power"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 56: # $binding_power = :lparen $precedence :rparen -> $1
        ctx.rule = rules[56]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse_precedence(ctx)
        tree.add(subtree)
        t = expect(ctx, 20) # :rparen
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[71]],
      rules[56]
    ))
def parse__gen14(ctx):
    current = ctx.tokens.current()
    rule = table[36][current.id] if current else -1
    tree = ParseTree(NonTerminal(72, '_gen14'))
    ctx.nonterminal = "_gen14"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[72] and current.id not in nonterminal_first[72]:
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
def parse__gen10(ctx):
    current = ctx.tokens.current()
    rule = table[37][current.id] if current else -1
    tree = ParseTree(NonTerminal(73, '_gen10'))
    ctx.nonterminal = "_gen10"
    tree.list = False
    if current != None and current.id in nonterminal_follow[73] and current.id not in nonterminal_first[73]:
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
def parse_lexer(ctx):
    current = ctx.tokens.current()
    rule = table[38][current.id] if current else -1
    tree = ParseTree(NonTerminal(74, 'lexer'))
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
        t = expect(ctx, 11) # :lexer
        tree.add(t)
        t = expect(ctx, 3) # :langle
        tree.add(t)
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 21) # :rangle
        tree.add(t)
        t = expect(ctx, 24) # :lbrace
        tree.add(t)
        subtree = parse__gen1(ctx)
        tree.add(subtree)
        subtree = parse__gen2(ctx)
        tree.add(subtree)
        t = expect(ctx, 7) # :rbrace
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[74]],
      rules[10]
    ))
def parse_precedence(ctx):
    current = ctx.tokens.current()
    rule = table[39][current.id] if current else -1
    tree = ParseTree(NonTerminal(75, 'precedence'))
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
        t = expect(ctx, 23) # :colon
        tree.add(t)
        subtree = parse_associativity(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[75]],
      rules[57]
    ))
def parse__gen17(ctx):
    current = ctx.tokens.current()
    rule = table[40][current.id] if current else -1
    tree = ParseTree(NonTerminal(76, '_gen17'))
    ctx.nonterminal = "_gen17"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[76] and current.id not in nonterminal_first[76]:
        return tree
    if current == None:
        return tree
    if rule == 75: # $_gen17 = :comma $macro_parameter $_gen17
        ctx.rule = rules[75]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 22) # :comma
        tree.add(t)
        tree.listSeparator = t
        subtree = parse_macro_parameter(ctx)
        tree.add(subtree)
        subtree = parse__gen17(ctx)
        tree.add(subtree)
        return tree
    return tree
def parse__gen16(ctx):
    current = ctx.tokens.current()
    rule = table[41][current.id] if current else -1
    tree = ParseTree(NonTerminal(77, '_gen16'))
    ctx.nonterminal = "_gen16"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[77] and current.id not in nonterminal_first[77]:
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
def parse__gen2(ctx):
    current = ctx.tokens.current()
    rule = table[42][current.id] if current else -1
    tree = ParseTree(NonTerminal(78, '_gen2'))
    ctx.nonterminal = "_gen2"
    tree.list = False
    if current != None and current.id in nonterminal_follow[78] and current.id not in nonterminal_first[78]:
        return tree
    if current == None:
        return tree
    if rule == 8: # $_gen2 = :code
        ctx.rule = rules[8]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 31) # :code
        tree.add(t)
        return tree
    return tree
def parse_ast_transform(ctx):
    current = ctx.tokens.current()
    rule = table[43][current.id] if current else -1
    tree = ParseTree(NonTerminal(79, 'ast_transform'))
    ctx.nonterminal = "ast_transform"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 66: # $ast_transform = :arrow $ast_transform_sub -> $1
        ctx.rule = rules[66]
        tree.astTransform = AstTransformSubstitution(1)
        t = expect(ctx, 2) # :arrow
        tree.add(t)
        subtree = parse_ast_transform_sub(ctx)
        tree.add(subtree)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[79]],
      rules[66]
    ))
def parse__gen7(ctx):
    current = ctx.tokens.current()
    rule = table[44][current.id] if current else -1
    tree = ParseTree(NonTerminal(80, '_gen7'))
    ctx.nonterminal = "_gen7"
    tree.list = 'slist'
    if current != None and current.id in nonterminal_follow[80] and current.id not in nonterminal_first[80]:
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
    rule = table[45][current.id] if current else -1
    tree = ParseTree(NonTerminal(81, 'associativity'))
    ctx.nonterminal = "associativity"
    tree.list = False
    if current == None:
        raise SyntaxError('Error: unexpected end of file')
    if rule == 60: # $associativity = :left
        ctx.rule = rules[60]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 32) # :left
        tree.add(t)
        return tree
    elif rule == 61: # $associativity = :right
        ctx.rule = rules[61]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 17) # :right
        tree.add(t)
        return tree
    elif rule == 62: # $associativity = :unary
        ctx.rule = rules[62]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 34) # :unary
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[81]],
      rules[62]
    ))
def parse_ast_transform_sub(ctx):
    current = ctx.tokens.current()
    rule = table[46][current.id] if current else -1
    tree = ParseTree(NonTerminal(82, 'ast_transform_sub'))
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
        t = expect(ctx, 10) # :identifier
        tree.add(t)
        t = expect(ctx, 13) # :lparen
        tree.add(t)
        subtree = parse__gen14(ctx)
        tree.add(subtree)
        t = expect(ctx, 20) # :rparen
        tree.add(t)
        return tree
    elif rule == 72: # $ast_transform_sub = :nonterminal_reference
        ctx.rule = rules[72]
        tree.astTransform = AstTransformSubstitution(0)
        t = expect(ctx, 33) # :nonterminal_reference
        tree.add(t)
        return tree
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[82]],
      rules[72]
    ))
