import re
import sys
import base64
import argparse
import os
from ..Common import Terminal, SyntaxError, TokenStream
from .Parser import terminals

{% import re %}

terminals = {
{% for terminal in lexer.terminals %}
    {{terminal.id}}: '{{terminal.string}}',
{% endfor %}

{% for terminal in lexer.terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

# START USER CODE
{{lexer.code}}
# END USER CODE

{% if re.search(r'def\s+default_action', lexer.code) is None %}
def default_action(context, mode, match, terminal, resource, line, col):
    tokens = [Terminal(terminals[terminal], terminal, match, resource, line, col)] if terminal else []
    return (tokens, mode, context)
{% endif %}

{% if re.search(r'def\s+init', lexer.code) is None %}
def init():
    return {}
{% endif %}

{% if re.search(r'def\s+destroy', lexer.code) is None %}
def destroy(context):
    pass
{% endif %}

class HermesLexer:
    regex = {
      {% for mode, regex_list in lexer.items() %}
        '{{mode}}': [
          {% for regex in regex_list %}
          (re.compile({{regex.regex}}{{", "+' | '.join(['re.'+x for x in regex.options]) if regex.options else ''}}), {{"'" + regex.terminal.string.lower() + "'" if regex.terminal else 'None'}}, {{regex.function}}),
          {% endfor %}
        ],
      {% endfor %}
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
