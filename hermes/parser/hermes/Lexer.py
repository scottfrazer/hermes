import re
import sys
import base64
import argparse
from ..Common import Terminal, SyntaxError, TokenStream
from .Parser import terminals
terminals = {
    8: 'parser_expression',
    35: 'dash',
    15: 'regex',
    16: 'infix_rule_hint',
    23: 'unary',
    1: 'integer',
    3: 'nonterminal',
    0: 'langle',
    18: 'mixfix_rule_hint',
    26: 'mode',
    25: 'pipe',
    13: 'identifier',
    4: 'code',
    34: 'rparen',
    27: 'string',
    29: 'colon',
    20: 'rangle',
    10: 'nonterminal_reference',
    11: 'lexer',
    7: 'll1_rule_hint',
    6: 'right',
    24: 'left',
    28: 'asterisk',
    19: 'expression_divider',
    14: 'lbrace',
    5: 'grammar',
    12: 'prefix_rule_hint',
    33: 'arrow',
    22: 'equals',
    17: 'null',
    9: 'expr_rule_hint',
    21: 'rbrace',
    32: 'terminal',
    31: 'lparen',
    -1: '_empty',
    2: 'parser_ll1',
    30: 'comma',
    'parser_expression': 8,
    'dash': 35,
    'regex': 15,
    'infix_rule_hint': 16,
    'unary': 23,
    'integer': 1,
    'nonterminal': 3,
    'langle': 0,
    'mixfix_rule_hint': 18,
    'mode': 26,
    'pipe': 25,
    'identifier': 13,
    'code': 4,
    'rparen': 34,
    'string': 27,
    'colon': 29,
    'rangle': 20,
    'nonterminal_reference': 10,
    'lexer': 11,
    'll1_rule_hint': 7,
    'right': 6,
    'left': 24,
    'asterisk': 28,
    'expression_divider': 19,
    'lbrace': 14,
    'grammar': 5,
    'prefix_rule_hint': 12,
    'arrow': 33,
    'equals': 22,
    'null': 17,
    'expr_rule_hint': 9,
    'rbrace': 21,
    'terminal': 32,
    'lparen': 31,
    '_empty': -1,
    'parser_ll1': 2,
    'comma': 30,
}
# START USER CODE
def normalize_morpheme(morpheme):
    if morpheme == '$$': return '$'
    return morpheme.lstrip(':').lstrip('$')
def binding_power(context, mode, match, terminal, line, col):
    (precedence, associativity) = match[1:-1].split(':')
    marker = 'asterisk' if precedence == '*' else 'dash'
    tokens = [
        Terminal(terminals['lparen'], 'lparen', '(', 'lparen', line, col),
        Terminal(terminals[marker], marker, precedence, marker, line, col),
        Terminal(terminals['colon'], 'colon', ':', 'colon', line, col),
        Terminal(terminals[associativity], associativity, associativity, associativity, line, col),
        Terminal(terminals['rparen'], 'rparen', ')', 'rparen', line, col)
    ]
    return (tokens, mode, context)
def morpheme(context, mode, match, terminal, line, col):
    return default_action(context, mode, normalize_morpheme(match), terminal, line, col)
def grammar_start(context, mode, match, terminal, line, col):
    return default_action(context, 'grammar', match, terminal, line, col)
def lexer_start(context, mode, match, terminal, line, col):
    identifier = match.replace('lexer', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(terminals['lexer'], 'lexer', 'lexer', 'lexer', line, col),
        Terminal(terminals['langle'], 'langle', '<', 'langle', line, col),
        Terminal(terminals['identifier'], 'identifier', identifier, 'identifier', line, col),
        Terminal(terminals['rangle'], 'rangle', '>', 'rangle', line, col),
    ]
    return (tokens, 'lexer', context)
def parser_ll1_start(context, mode, match, terminal, line, col):
    return default_action(context, 'parser_ll1', match, terminal, line, col)
def parser_expr_start(context, mode, match, terminal, line, col):
    return default_action(context, 'parser_expr', match, terminal, line, col)
def parse_mode(context, mode, match, terminal, line, col):
    identifier = match.replace('mode', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Terminal(terminals['mode'], 'mode', 'mode', 'mode', line, col),
        Terminal(terminals['langle'], 'langle', '<', 'langle', line, col),
        Terminal(terminals['identifier'], 'identifier', identifier, 'identifier', line, col),
        Terminal(terminals['rangle'], 'rangle', '>', 'rangle', line, col),
    ]
    return (tokens, mode, context)
def lexer_code(context, mode, match, terminal, line, col):
    code = match[6:-7].strip()
    tokens = [Terminal(terminals[terminal], terminal, code, 'resource', line, col)]
    return (tokens, mode, context)
def lexer_lbrace(context, mode, match, terminal, line, col):
    context['lexer_brace'] += 1
    return default_action(context, mode, match, terminal, line, col)
def lexer_rbrace(context, mode, match, terminal, line, col):
    context['lexer_brace'] -= 1
    mode = 'grammar' if context['lexer_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, line, col)
def parser_lbrace(context, mode, match, terminal, line, col):
    context['parser_brace'] += 1
    return default_action(context, mode, match, terminal, line, col)
def parser_rbrace(context, mode, match, terminal, line, col):
    context['parser_brace'] -= 1
    mode = 'grammar' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, line, col)
def parser_rule_start(context, mode, match, terminal, line, col):
    tokens = [
        Terminal(terminals['ll1_rule_hint'], 'll1_rule_hint', '', 'll1_rule_hint', line, col),
        Terminal(terminals[terminal], terminal, normalize_morpheme(match), terminal, line, col)
    ]
    return (tokens, mode, context)
def infix_rule_start(context, mode, match, terminal, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', 'expr_rule_hint', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
        Terminal(terminals['equals'], 'equals', '=', 'equals', line, col),
        Terminal(terminals['infix_rule_hint'], 'infix_rule_hint', '', 'infix_rule_hint', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
        Terminal(terminals['terminal'], 'terminal', operator, 'terminal', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
    ]
    return (tokens, mode, context)
def prefix_rule_start(context, mode, match, terminal, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    operator = normalize_morpheme(re.search(':[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', 'expr_rule_hint', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
        Terminal(terminals['equals'], 'equals', '=', 'equals', line, col),
        Terminal(terminals['prefix_rule_hint'], 'prefix_rule_hint', '', 'prefix_rule_hint', line, col),
        Terminal(terminals['terminal'], 'terminal', operator, 'terminal', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
    ]
    return (tokens, mode, context)
def expr_rule_start(context, mode, match, terminal, line, col):
    nonterminal = normalize_morpheme(re.search('\$[a-zA-Z][a-zA-Z0-9_]*', match).group(0))
    tokens = [
        Terminal(terminals['expr_rule_hint'], 'expr_rule_hint', '', 'expr_rule_hint', line, col),
        Terminal(terminals['nonterminal'], 'nonterminal', nonterminal, 'nonterminal', line, col),
        Terminal(terminals['equals'], 'equals', '=', 'equals', line, col),
        Terminal(terminals['mixfix_rule_hint'], 'mixfix_rule_hint', '', 'mixfix_rule_hint', line, col),
    ]
    return (tokens, mode, context)
def grammar_lbrace(context, mode, match, terminal, line, col):
    context['grammar_brace'] += 1
    return default_action(context, mode, match, terminal, line, col)
def grammar_rbrace(context, mode, match, terminal, line, col):
    context['grammar_brace'] -= 1
    mode = 'default' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal, line, col)
# END USER CODE
def default_action(context, mode, match, terminal, line, col):
    tokens = [Terminal(terminals[terminal], terminal, match, 'resource', line, col)] if terminal else []
    return (tokens, mode, context)
class HermesLexer:
    regex = {
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
        'grammar': [
          (re.compile(r'\s+'), None, None),
          (re.compile(r'{'), 'lbrace', grammar_lbrace),
          (re.compile(r'}'), 'rbrace', grammar_rbrace),
          (re.compile(r'lexer\s*<\s*[a-zA-Z]+\s*>'), 'lexer', lexer_start),
          (re.compile(r'parser\s*<\s*ll1\s*>'), 'parser_ll1', parser_ll1_start),
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
        'default': [
          (re.compile(r'\grammar'), 'grammar', grammar_start),
          (re.compile(r'\s+'), None, None),
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
    def _next(self, string, mode, context, line, col):
        for (regex, terminal, function) in self.regex[mode]:
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), terminal, line, col)
                return (tokens, match.group(0), mode)
        return ([], '', mode)
    def lex(self, string, debug=False):
        (mode, line, col) = ('default', 1, 1)
        context = {'lexer_brace': 0, 'grammar_brace': 0, 'parser_brace': 0}
        string_copy = string
        parsed_tokens = []
        while len(string):
            (tokens, match, mode) = self._next(string, mode, context, line, col)
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
        return parsed_tokens
def lex(file_or_path, debug=False):
    if isinstance(file_or_path, str):
        try:
            with open(file_or_path) as fp:
                contents = fp.read()
        except FileNotFoundError:
            contents = file_or_path
    elif hasattr(file_or_path, 'read') and hasattr(file_or_path, 'close'):
        contents = file_or_path.read()
        file_or_path.close()
    lexer = HermesLexer()
    return TokenStream(lexer.lex(contents, debug))
