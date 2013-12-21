import re
from xtermcolor import colorize

def default_action(context, mode, match, terminal):
    tokens = [Token(match, terminal)] if terminal else []
    return (tokens, mode, context)
def grammar_start(context, mode, match, terminal):
    return default_action(context, 'grammar', match, terminal)
def lexer_start(context, mode, match, terminal):
    return default_action(context, 'lexer', match, terminal)
def parser_ll1_start(context, mode, match, terminal):
    return default_action(context, 'parser_ll1', match, terminal)
def parser_expr_start(context, mode, match, terminal):
    return default_action(context, 'parser_expr', match, terminal)
def parse_mode(context, mode, match, terminal):
    identifier = match.replace('mode', '').replace('<', '').replace('>', '').strip()
    tokens = [
        Token('mode', 'mode'),
        Token('<', 'langle'),
        Token(identifier, 'identifier'),
        Token('>', 'rangle'),
    ]
    return (tokens, mode, context)
def lexer_lbrace(context, mode, match, terminal):
    context['lexer_brace'] += 1
    return default_action(context, mode, match, terminal)
def lexer_rbrace(context, mode, match, terminal):
    context['lexer_brace'] -= 1
    mode = 'grammar' if context['lexer_brace'] == 0 else mode
    return default_action(context, mode, match, terminal)
def parser_lbrace(context, mode, match, terminal):
    context['parser_brace'] += 1
    return default_action(context, mode, match, terminal)
def parser_rbrace(context, mode, match, terminal):
    context['parser_brace'] -= 1
    mode = 'grammar' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal)
def grammar_lbrace(context, mode, match, terminal):
    context['grammar_brace'] += 1
    return default_action(context, mode, match, terminal)
def grammar_rbrace(context, mode, match, terminal):
    context['grammar_brace'] -= 1
    mode = 'default' if context['parser_brace'] == 0 else mode
    return default_action(context, mode, match, terminal)

class Token:
    def __init__(self, match, terminal):
        self.__dict__.update(locals())

class HermesLexer:
    regex = {
        'default': [
            (re.compile(r'\grammar'), "grammar", grammar_start),
            (re.compile(r'\s+'), None, None),
            (re.compile(r'.*', re.DOTALL), "code", None)
        ],
        'grammar': [
            (re.compile(r'\s+'), None, None),
            (re.compile(r'{'), "lbrace", grammar_lbrace),
            (re.compile(r'}'), "lbrace", grammar_rbrace),
            (re.compile(r'lexer'), "lexer", lexer_start),
            (re.compile(r'parser\s*<\s*ll1\s*>'), "parser_ll1", parser_ll1_start),
        ],
        'lexer': [
            (re.compile(r'\s+'), None, None),
            (re.compile(r'{'), "lbrace", lexer_lbrace),
            (re.compile(r'}'), "lbrace", lexer_rbrace),
            (re.compile(r'\('), "lparen", None),
            (re.compile(r'\)'), "rparen", None),
            (re.compile(r"r'(\\\'|[^\'])*'"), "regex", None),
            (re.compile(r"->"), "arrow", None),
            (re.compile(r":[a-zA-Z][a-zA-Z0-9_]+"), "terminal", None),
            (re.compile(r"mode<[a-zA-Z0-9_]+>"), "mode", parse_mode),
            (re.compile(r'[a-zA-Z_]+'), "identifier", None),
        ],
        'parser_ll1': [
            (re.compile(r'\s+'), None, None),
            (re.compile(r'{'), "lbrace", parser_lbrace),
            (re.compile(r'}'), "lbrace", parser_rbrace),
            (re.compile(r'\|'), "pipe", None),
            (re.compile(r'='), "equals", None),
            (re.compile(r'list'), "list", None),
            (re.compile(r'\('), "lparen", None),
            (re.compile(r'\)'), "rparen", None),
            (re.compile(r','), "comma", None),
            (re.compile(r'->'), "arrow", None),
            (re.compile(r'parser\s*<\s*expression\s*>'), "parser_expr", parser_expr_start),
            (re.compile(r":[a-zA-Z][a-zA-Z0-9_]+"), "terminal", None),
            (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]+'), "nonterminal", None),
            (re.compile(r'\$[0-9]+'), "nonterminal_reference", None),
            (re.compile(r'[a-zA-Z][a-zA-Z0-9_]+'), "identifier", None),
        ],
        'parser_expr': [
            (re.compile(r'\s+'), None, None),
            (re.compile(r'\([\*-]:(left|right|unary)\)'), "binding", None),
            (re.compile(r'='), "equals", None),
            (re.compile(r'{'), "lbrace", parser_lbrace),
            (re.compile(r'}'), "lbrace", parser_rbrace),
            (re.compile(r'\('), "lparen", None),
            (re.compile(r'\)'), "rparen", None),
            (re.compile(r','), "comma", None),
            (re.compile(r'->'), "arrow", None),
            (re.compile(r":[a-zA-Z][a-zA-Z0-9_]+"), "terminal", None),
            (re.compile(r'\$[a-zA-Z][a-zA-Z0-9_]+'), "nonterminal", None),
            (re.compile(r'\$[0-9]+'), "nonterminal_reference", None),
            (re.compile(r'[a-zA-Z_]+'), "identifier", None),
        ]
    }

    def update_line_col(self, match, line, col):
        match_lines = match.split('\n')
        line += len(match_lines) - 1
        if len(match_lines) == 1:
            col += len(match_lines[0])
        else:
            col = len(match_lines[-1]) + 1
        return (line, col)

    def parse(self, string):
      (mode, line, col) = ('default', 1, 1)
      context = {'lexer_brace': 0, 'grammar_brace': 0, 'parser_brace': 0}
      while len(string):
          (tokens, match, mode) = self.next(string, mode, context)
          string = string[len(match):]
          if tokens is not None:
              for token in tokens:
                  token.line = line
                  token.col = col
                  print('token --> [{}] [{}, {}] [{}] [{}] [{}]'.format(
                      colorize(token.terminal, ansi=9), colorize(str(token.line), ansi=5), colorize(str(token.col), ansi=5),
                      colorize(token.match, ansi=3), colorize(mode, ansi=4), colorize(str(context), ansi=13)
                  ))
              (line, col) = self.update_line_col(match, line, col)
          else:
              print('No match found')
              return

    def next(self, string, mode, context):
        for (regex, terminal, function) in self.regex[mode]:
            match = regex.match(string)
            if match:
                function = function if function else default_action
                (tokens, mode, context) = function(context, mode, match.group(0), terminal)
                return (tokens, match.group(0), mode)
        return (None, None, mode)

lexer = HermesLexer()
with open('hermes.zgr') as fp:
    lexer.parse(fp.read())
