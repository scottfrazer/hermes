import re
import sys
import base64
import argparse
import os
from ..Common import Terminal, SyntaxError, TokenStream
lexer_terminals = {
    29: 'identifier',
    25: 'colon',
    32: 'null',
    24: 'arrow',
    -1: '_empty',
    20: 'langle',
    12: 'll1_rule_hint',
    17: 'string',
    13: 'code',
    1: 'terminal',
    6: 'infix_rule_hint',
    19: 'nonterminal_reference',
    10: 'left',
    3: 'lbrace',
    23: 'unary',
    0: 'expression_divider',
    27: 'integer',
    16: 'comma',
    28: 'expr_rule_hint',
    2: 'parser_ll1',
    26: 'lparen',
    4: 'mixfix_rule_hint',
    35: 'mode',
    21: 'lexer',
    11: 'nonterminal',
    15: 'grammar',
    18: 'rparen',
    31: 'regex',
    30: 'asterisk',
    8: 'dash',
    14: 'equals',
    9: 'rangle',
    7: 'prefix_rule_hint',
    22: 'rbrace',
    34: 'parser_expression',
    5: 'right',
    33: 'pipe',
    'identifier': 29,
    'colon': 25,
    'null': 32,
    'arrow': 24,
    '_empty': -1,
    'langle': 20,
    'll1_rule_hint': 12,
    'string': 17,
    'code': 13,
    'terminal': 1,
    'infix_rule_hint': 6,
    'nonterminal_reference': 19,
    'left': 10,
    'lbrace': 3,
    'unary': 23,
    'expression_divider': 0,
    'integer': 27,
    'comma': 16,
    'expr_rule_hint': 28,
    'parser_ll1': 2,
    'lparen': 26,
    'mixfix_rule_hint': 4,
    'mode': 35,
    'lexer': 21,
    'nonterminal': 11,
    'grammar': 15,
    'rparen': 18,
    'regex': 31,
    'asterisk': 30,
    'dash': 8,
    'equals': 14,
    'rangle': 9,
    'prefix_rule_hint': 7,
    'rbrace': 22,
    'parser_expression': 34,
    'right': 5,
    'pipe': 33,
}
# START USER CODE
def init():
    return {'lexer_brace': 0, 'grammar_brace': 0, 'parser_brace': 0}
def normalize_morpheme(morpheme):
    if morpheme == '$$': return '$'
    return morpheme.lstrip(':').lstrip('$')
def binding_power(context, mode, match, terminal, resource, line, col):
    (precedence, associativity) = match[1:-1].split(':')
    marker = 'asterisk' if precedence == '*' else 'dash'
    tokens = [
        Terminal(lexer_terminals['lparen'], 'lparen', '(', resource, line, col),
        Terminal(lexer_terminals[marker], marker, precedence, resource, line, col),
        Terminal(lexer_terminals['colon'], 'colon', ':', resource, line, col),
        Terminal(lexer_terminals[associativity], associativity, associativity, resource, line, col),
        Terminal(lexer_terminals['rparen'], 'rparen', ')', resource, line, col)
    ]
    return (tokens, mode, context)
def morpheme(context, mode, match, terminal, resource, line, col):
    return default_action(context, mode, normalize_morpheme(match), terminal, resource, line, col)
def grammar_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'grammar', match, terminal, resource, line, col)
def lexer_start(context, mode, match, terminal, resource, line, col):
    identifier = match.replace('lexer', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(lexer_terminals['lexer'], 'lexer', 'lexer', resource, line, col),
        Terminal(lexer_terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(lexer_terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(lexer_terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, 'lexer', context)
def parser_ll1_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'parser_ll1', match, terminal, resource, line, col)
def parser_expr_start(context, mode, match, terminal, resource, line, col):
    return default_action(context, 'parser_expr', match, terminal, resource, line, col)
def parse_mode(context, mode, match, terminal, resource, line, col):
    identifier = match.replace('mode', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(lexer_terminals['mode'], 'mode', 'mode', resource, line, col),
        Terminal(lexer_terminals['langle'], 'langle', '<', resource, line, col),
        Terminal(lexer_terminals['identifier'], 'identifier', identifier, resource, line, col),
        Terminal(lexer_terminals['rangle'], 'rangle', '>', resource, line, col),
    ]
    return (tokens, mode, context)
def lexer_code(context, mode, match, terminal, resource, line, col):
    code = match[6:-7].strip()
    tokens = [Terminal(lexer_terminals[terminal], terminal, code, resource, line, col)]
    return (tokens, mode, context)
def lexer_lbrace(context, mode, match, terminal, resource, line, col):
    context['lexer_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def lexer_rbrace(context, mode, match, terminal, resource, line, col):
    context['lexer_brace'] -= 1
    mode = 'grammar' if context['lexer_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_lbrace(context, mode, match, terminal, resource, line, col):
    context['parser_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_rbrace(context, mode, match, terminal, resource, line, col):
    context['parser_brace'] -= 1
    mode = 'grammar' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
def parser_rule_start(context, mode, match, terminal, resource, line, col):
    tokens = [
        Terminal(lexer_terminals['ll1_rule_hint'], 'll1_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals[terminal], terminal, normalize_morpheme(match), resource, line, col)
    ]
    return (tokens, mode, context)
def infix_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['infix_rule_hint'], 'infix_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def prefix_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['prefix_rule_hint'], 'prefix_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['terminal'], 'terminal', operator, resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
    ]
    return (tokens, mode, context)
def expr_rule_start(context, mode, match, terminal, resource, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(lexer_terminals['expr_rule_hint'], 'expr_rule_hint', '', resource, line, col),
        Terminal(lexer_terminals['nonterminal'], 'nonterminal', nonterminal, resource, line, col),
        Terminal(lexer_terminals['equals'], 'equals', '=', resource, line, col),
        Terminal(lexer_terminals['mixfix_rule_hint'], 'mixfix_rule_hint', '',resource, line, col),
    ]
    return (tokens, mode, context)
def grammar_lbrace(context, mode, match, terminal, resource, line, col):
    context['grammar_brace'] += 1
    return default_action(context, mode, match, terminal, resource, line, col)
def grammar_rbrace(context, mode, match, terminal, resource, line, col):
    context['grammar_brace'] -= 1
    mode = 'default' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, resource, line, col)
# END USER CODE
def default_action(context, mode, match, terminal, resource, line, col):
    tokens = [Terminal(lexer_terminals[terminal], terminal, match, resource, line, col)] if terminal else []
    return (tokens, mode, context)
def destroy(context):
    pass
class HermesLexer:
    regex = {
        'default': [
          (re.compile(r'\grammar'), 'grammar', grammar_start),
          (re.compile(r'\s+'), None, None),
        ],
        'grammar': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', grammar_lbrace),
          (re.compile(r'}'), 'rbrace', grammar_rbrace),
          (re.compile(r'lexer\s*<\s*[a-zA-Z]+\s*>'), 'lexer', lexer_start),
          (re.compile(r'parser\s*<\s*ll1\s*>'), 'parser_ll1', parser_ll1_start),
        ],
        'lexer': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', lexer_lbrace),
          (re.compile(r'}'), 'rbrace', lexer_rbrace),
          (re.compile(r'null'), 'null', None),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r'r\'(\\\'|[^\'])*\''), 'regex', None),
          (re.compile(r'"(\\\"|[^\"])*"'), 'regex', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'mode<[a-zA-Z0-9_]+>'), 'mode', parse_mode),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'<code>(.*?)</code>', re.DOTALL), 'code', lexer_code),
        ],
        'parser_ll1': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', parser_lbrace),
          (re.compile(r'}'), 'rbrace', parser_rbrace),
          (re.compile(r'\|'), 'pipe', None),
          (re.compile(r'='), 'equals', None),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r','), 'comma', None),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r'parser\s*<\s*expression\s*>'), 'parser_expression', parser_expr_start),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*(?=\s*\=)'), 'nonterminal', parser_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*'), 'nonterminal', morpheme),
          (re.compile(r'\$([0-9]+|\$)'), 'nonterminal_reference', morpheme),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'"[^"]+"'), 'string', None),
          (re.compile(r'[0-9]+'), 'integer', None),
        ],
        'parser_expr': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'\([\*-]:(left|right|unary)\)'), None, binding_power),
          (re.compile(r'->'), 'arrow', None),
          (re.compile(r'<=>'), 'expression_divider', None),
          (re.compile(r'\|'), 'pipe', None),
          (re.compile(r'='), 'equals', None),
          (re.compile(r'{'), 'lbrace', parser_lbrace),
          (re.compile(r'}'), 'rbrace', parser_rbrace),
          (re.compile(r'\('), 'lparen', None),
          (re.compile(r'\)'), 'rparen', None),
          (re.compile(r','), 'comma', None),
          (re.compile(r':([a-zA-Z][a-zA-Z0-9_]*|_empty)'), 'terminal', morpheme),
          (re.compile(r'(\$[a-zA-Z][a-zA-Z0-9_]*)[ \t]*=[ \t]*\1[ \t]+:[a-zA-Z][a-zA-Z0-9_]*[ \t]+\1(?![ \t]+(:|\$))'), 'nonterminal', infix_rule_start),
          (re.compile(r'(\$[a-zA-Z][a-zA-Z0-9_]*)[ \t]*=[ \t]*:[a-zA-Z][a-zA-Z0-9_]*[ \t]+\1(?![ \t](:|\$))'), 'nonterminal', prefix_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*\s*='), 'nonterminal', expr_rule_start),
          (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]*'), 'nonterminal', morpheme),
          (re.compile(r'\$([0-9]+|\$)'), 'nonterminal_reference', morpheme),
          (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'), 'identifier', None),
          (re.compile(r'"[^"]+"'), 'string', None),
          (re.compile(r'[0-9]+'), 'integer', None),
        ],
    }
    def _update_line_col(self, match, line, col):
        match_lines = match.split('\n')
        line += len(match_lines) - 1
        if len(match_lines) == 1:
            col += len(match_lines[0])
        else:
            col = len(match_lines[-1]) + 1
        return (line, col)
    def _unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        message = 'Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        )
        raise SyntaxError(message)
    def _next(self, string, mode, context, resource, line, col):
        for (regex, terminal, function) in self.regex[mode]:
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), terminal, resource, line, col)
                return (tokens, match.group(0), mode)
        return ([], '', mode)
    def lex(self, string, resource, debug=False):
        (mode, line, col) = ('default', 1, 1)
        context = init()
        string_copy = string
        parsed_tokens = []
        while len(string):
            (tokens, match, mode) = self._next(string, mode, context, resource, line, col)
            if len(match) == 0:
                self._unrecognized_token(string_copy, line, col)
            string = string[len(match):]
            if tokens is None:
                self._unrecognized_token(string_copy, line, col)
            parsed_tokens.extend(tokens)
            (line, col) = self._update_line_col(match, line, col)
            if debug:
                for token in tokens:
                    print('token --> [{}] [{}, {}] [{}] [{}] [{}]'.format(
                        colorize(token.str, ansi=9),
                        colorize(str(token.line), ansi=5),
                        colorize(str(token.col), ansi=5),
                        colorize(token.source_string, ansi=3),
                        colorize(mode, ansi=4),
                        colorize(str(context), ansi=13)
                    ))
        destroy(context)
        return parsed_tokens
def lex(source, resource, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, debug))
