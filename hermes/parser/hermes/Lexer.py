import re
import sys
import base64
import argparse
import os
from ..Common import Terminal, SyntaxError, TokenStream
lexer_terminals = {
    15: 'parser_expression',
    -1: '_empty',
    10: 'lbrace',
    1: 'grammar',
    34: 'nonterminal_reference',
    13: 'langle',
    32: 'prefix_rule_hint',
    16: 'expression_divider',
    24: 'infix_rule_hint',
    12: 'pipe',
    17: 'null',
    5: 'mode',
    2: 'parser_ll1',
    28: 'string',
    31: 'asterisk',
    9: 'right',
    11: 'dash',
    3: 'equals',
    26: 'rparen',
    4: 'integer',
    7: 'lexer',
    27: 'comma',
    22: 'regex',
    18: 'rbrace',
    20: 'lparen',
    6: 'rangle',
    0: 'colon',
    19: 'll1_rule_hint',
    14: 'nonterminal',
    30: 'identifier',
    35: 'mixfix_rule_hint',
    33: 'terminal',
    8: 'expr_rule_hint',
    23: 'arrow',
    25: 'code',
    29: 'unary',
    21: 'left',
    'parser_expression': 15,
    '_empty': -1,
    'lbrace': 10,
    'grammar': 1,
    'nonterminal_reference': 34,
    'langle': 13,
    'prefix_rule_hint': 32,
    'expression_divider': 16,
    'infix_rule_hint': 24,
    'pipe': 12,
    'null': 17,
    'mode': 5,
    'parser_ll1': 2,
    'string': 28,
    'asterisk': 31,
    'right': 9,
    'dash': 11,
    'equals': 3,
    'rparen': 26,
    'integer': 4,
    'lexer': 7,
    'comma': 27,
    'regex': 22,
    'rbrace': 18,
    'lparen': 20,
    'rangle': 6,
    'colon': 0,
    'll1_rule_hint': 19,
    'nonterminal': 14,
    'identifier': 30,
    'mixfix_rule_hint': 35,
    'terminal': 33,
    'expr_rule_hint': 8,
    'arrow': 23,
    'code': 25,
    'unary': 29,
    'left': 21,
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
def lex(file_or_path, debug=False):
    if isinstance(file_or_path, str):
        try:
            with open(file_or_path) as fp:
                contents = fp.read()
                resource = os.path.basename(os.path.expanduser(file_or_path))
        except FileNotFoundError:
            contents = file_or_path
            resource = '<string>'
    lexer = HermesLexer()
    return TokenStream(lexer.lex(contents, resource, debug))
