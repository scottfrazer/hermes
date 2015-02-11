{% import re %}

var common = require('./common.js');

var terminals = {
{% for terminal in lexer.terminals %}
    '{{terminal.id}}': '{{terminal.string}}',
{% endfor %}

{% for terminal in lexer.terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

// START USER CODE
{{lexer.code}}
// END USER CODE

{% if re.search(r'function\s+default_action', lexer.code) is None %}
function default_action(context, mode, match, terminal, resource, line, col) {
    var tokens = []
    if (terminal) {
        tokens = [new common.Terminal(terminals[terminal], terminal, match, resource, line, col)]
    }
    return {tokens: tokens, mode: mode, context: context}
}

{% endif %}

{% if re.search(r'function\s+init', lexer.code) is None %}
function init() {
    return {}
}
{% endif %}

{% if re.search(r'function\s+destroy', lexer.code) is None %}
function destroy(context) {
    return 0;
}
{% endif %}

var regex = {
  {% for mode, regex_list in lexer.items() %}
    '{{mode}}': [
      {% for regex in regex_list %}
      [new RegExp({{regex.regex}}{{", "+' | '.join(['re.'+x for x in regex.options]) if regex.options else ''}}), {{"'" + regex.terminal.string.lower() + "'" if regex.terminal else 'null'}}, {{regex.function if regex.function else 'null'}}],
      {% endfor %}
    ],
  {% endfor %}
}

function _update_line_col(string, lexer_context) {
    var match_lines = string.split("\n")
    lexer_context.line += match_lines.length - 1
    if (match_lines.length == 1) {
        lexer_context.col += match_lines[0].length
    } else {
        lexer_context.col = match_lines[match_lines.length-1].length + 1
    }
}

function _unrecognized_token(self, string, line, col) {
    var lines = string.split('\n')
    var bad_line = lines[line-1]
    var message = 'Unrecognized token on line {0}, column {1}:\n\n{2}\n{3}'.format(
        line, col, bad_line, Array(col-1).join(' ') + '^'
    )
    throw new common.SyntaxError(message)
}

function _next(string, mode, context, resource, line, col) {
    for (i = 0; i < regex[mode].length; i++) {
        regexp = regex[mode][i][0];
        terminal = regex[mode][i][1];
        func = regex[mode][i][2];

        match = regexp.exec(string);

        if (match != null && match.index == 0) {
            if (func == null) {
                func = default_action;
            }

            lexer_match = func(context, mode, match[0], terminal, resource, line, col)
            tokens = lexer_match.tokens
            mode = lexer_match.mode
            context = lexer_match.context

            return {tokens: tokens, string: match[0], mode: mode}
        }
    }
    return {tokens: [], string: '', mode: mode}
}

function lex(string, resource) {
    lexer_context = {
        mode: 'default',
        line: 1,
        col: 1
    }
    user_context = init()

    string_copy = string
    parsed_tokens = []
    while (string.length) {
        lexer_match = _next(string, lexer_context.mode, user_context, resource, lexer_context.line, lexer_context.col)

        if (lexer_match.string.length == 0) {
            _unrecognized_token(string_copy, lexer_context.line, lexer_context.col)
        }

        string = string.substring(match.length)

        if (lexer_match.tokens == null) {
            _unrecognized_token(string_copy, lexer_context.line, lexer_context.col)
        }

        parsed_tokens.push.apply(parsed_tokens, lexer_match.tokens)

        lexer_context.mode = lexer_match.mode
        _update_line_col(lexer_match.string, lexer_context)

        if (false) {
            for (j=0; j<tokens.length; j++) {
                var token = tokens[j];
                console.log('token --> [{0}] [{1}, {2}] [{3}] [{4}] [{5}]'.format(
                    token.str,
                    token.line,
                    token.col,
                    token.source_string,
                    lexer_context.mode,
                    user_context
                ))
            }
        }
    }
    destroy(user_context)
    return new common.TokenStream(parsed_tokens)
}

{% if nodejs %}
module.exports = {
  lex: lex
}
{% endif %}
