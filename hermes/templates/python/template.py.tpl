{% if len(header)%}
{{'\n'.join(['# ' + s for s in header.split('\n')])}}
{% endif %}
import sys
import os
import re
import base64
import argparse
from collections import OrderedDict

{% import re %}
{% from hermes.grammar import * %}

###############
# Common Code #
###############

def parse_tree_string(parsetree, indent=None, b64_source=True, indent_level=0, debug=False):
    indent_str = (' ' * indent * indent_level) if indent else ''
    if isinstance(parsetree, ParseTree):
        children = [parse_tree_string(child, indent, b64_source, indent_level+1, debug) for child in parsetree.children]
        debug_str = parsetree.debug_str() if debug else ''
        if indent is None or len(children) == 0:
            return '{0}({1}: {2}{3})'.format(indent_str, parsetree.nonterminal, debug_str, ', '.join(children))
        else:
            return '{0}({1}:{2}\n{3}\n{4})'.format(
                indent_str,
                parsetree.nonterminal,
                debug_str,
                ',\n'.join(children),
                indent_str
            )
    elif isinstance(parsetree, Terminal):
        return indent_str + parsetree.dumps(b64_source=b64_source)

def ast_string(ast, indent=None, b64_source=True, indent_level=0):
    indent_str = (' ' * indent * indent_level) if indent else ''
    next_indent_str = (' ' * indent * (indent_level+1)) if indent else ''
    if isinstance(ast, Ast):
        children = OrderedDict([(k, ast_string(v, indent, b64_source, indent_level+1)) for k, v in ast.attributes.items()])
        if indent is None:
            return '({0}: {1})'.format(
                ast.name,
                ', '.join('{0}={1}'.format(k, v) for k, v in children.items())
            )
        else:
            return '({0}:\n{1}\n{2})'.format(
                ast.name,
                ',\n'.join(['{0}{1}={2}'.format(next_indent_str, k, v) for k, v in children.items()]),
                indent_str
            )
    elif isinstance(ast, list):
        children = [ast_string(element, indent, b64_source, indent_level+1) for element in ast]
        if indent is None or len(children) == 0:
            return '[{0}]'.format(', '.join(children))
        else:
            return '[\n{1}\n{0}]'.format(
                indent_str,
                ',\n'.join(['{0}{1}'.format(next_indent_str, child) for child in children]),
            )
    elif isinstance(ast, Terminal):
        return ast.dumps(b64_source=b64_source)

class Terminal:
  def __init__(self, id, str, source_string, resource, line, col):
      self.__dict__.update(locals())
  def getId(self):
      return self.id
  def ast(self):
      return self
  def dumps(self, b64_source=True, **kwargs):
      source_string = base64.b64encode(self.source_string.encode('utf-8')).decode('utf-8') if b64_source else self.source_string
      return '<{resource}:{line}:{col} {terminal} "{source}">'.format(
          resource=self.resource,
          line=self.line,
          col=self.col,
          terminal=self.str,
          source=source_string
      )
  def __str__(self):
      return self.dumps()

class NonTerminal():
  def __init__(self, id, str):
    self.__dict__.update(locals())
    self.list = False
  def __str__(self):
    return self.str

class AstTransform:
  pass

class AstTransformSubstitution(AstTransform):
  def __init__(self, idx):
    self.__dict__.update(locals())
  def __repr__(self):
    return '$' + str(self.idx)
  def __str__(self):
    return self.__repr__()

class AstTransformNodeCreator(AstTransform):
  def __init__( self, name, parameters ):
    self.__dict__.update(locals())
  def __repr__( self ):
    return self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )'
  def __str__(self):
    return self.__repr__()

class AstList(list):
  def ast(self):
      retval = []
      for ast in self:
          retval.append(ast.ast())
      return retval
  def dumps(self, indent=None, b64_source=True):
      args = locals()
      del args['self']
      return ast_string(self, **args)

class ParseTree():
  def __init__(self, nonterminal):
      self.__dict__.update(locals())
      self.children = []
      self.astTransform = None
      self.isExpr = False
      self.isNud = False
      self.isPrefix = False
      self.isInfix = False
      self.nudMorphemeCount = 0
      self.isExprNud = False # true for rules like _expr := {_expr} + {...}
      self.listSeparator = None
      self.list = False
  def debug_str(self):
      from copy import deepcopy
      def h(v):
          if v == False or v is None:
              return str(v)
          from xtermcolor import colorize
          return colorize(str(v), ansi=190)
      d = deepcopy(self.__dict__)
      for key in ['self', 'nonterminal', 'children']:
          del d[key]
      f = {k: v for k, v in d.items() if v != False and v is not None}
      return '[{}]'.format(', '.join(['{}={}'.format(k,h(v)) for k,v in f.items()]))
  def add(self, tree):
      self.children.append( tree )
  def ast(self):
      if self.list == True:
          r = AstList()
          if len(self.children) == 0:
              return r
          end = max(0, len(self.children) - 1)
          for child in self.children[:end]:
              if isinstance(child, Terminal) and self.listSeparator is not None and child.id == self.listSeparator.id:
                  continue
              r.append(child.ast())
          r.extend(self.children[end].ast())
          return r
      elif self.isExpr:
          if isinstance(self.astTransform, AstTransformSubstitution):
              return self.children[self.astTransform.idx].ast()
          elif isinstance(self.astTransform, AstTransformNodeCreator):
              parameters = OrderedDict()
              for name, idx in self.astTransform.parameters.items():
                  if idx == '$':
                      child = self.children[0]
                  elif isinstance(self.children[0], ParseTree) and \
                       self.children[0].isNud and \
                       not self.children[0].isPrefix and \
                       not self.isExprNud and \
                       not self.isInfix:
                      if idx < self.children[0].nudMorphemeCount:
                          child = self.children[0].children[idx]
                      else:
                          index = idx - self.children[0].nudMorphemeCount + 1
                          child = self.children[index]
                  elif len(self.children) == 1 and not isinstance(self.children[0], ParseTree) and not isinstance(self.children[0], list):
                      return self.children[0]
                  else:
                      child = self.children[idx]
                  parameters[name] = child.ast()
              return Ast(self.astTransform.name, parameters)
      else:
          if isinstance(self.astTransform, AstTransformSubstitution):
              return self.children[self.astTransform.idx].ast()
          elif isinstance(self.astTransform, AstTransformNodeCreator):
              parameters = OrderedDict()
              for name, idx in self.astTransform.parameters.items():
                  parameters[name] = self.children[idx].ast()
              return Ast(self.astTransform.name, parameters)
          elif len(self.children):
              return self.children[0].ast()
          else:
              return None

  def dumps(self, indent=None, b64_source=True, debug=False):
      args = locals()
      del args['self']
      return parse_tree_string(self, **args)

class Ast():
    def __init__(self, name, attributes):
        self.__dict__.update(locals())
    def attr(self, attr):
        return self.attributes[attr]
    def dumps(self, indent=None, b64_source=True):
        args = locals()
        del args['self']
        return ast_string(self, **args)

class SyntaxError(Exception):
    def __init__(self, message):
        self.__dict__.update(locals())
    def __str__(self):
        return self.message

class TokenStream(list):
    def __init__(self, arg=[]):
        super(TokenStream, self).__init__(arg)
        self.index = 0
    def advance(self):
        self.index += 1
        return self.current()
    def last(self):
        return self[-1]
    def current(self):
        try:
            return self[self.index]
        except IndexError:
            return None

class DefaultSyntaxErrorHandler:
    def __init__(self):
        self.errors = []
    def _error(self, string):
        error = SyntaxError(string)
        self.errors.append(error)
        return error
    def unexpected_eof(self):
        return self._error("Error: unexpected end of file")
    def excess_tokens(self):
        return self._error("Finished parsing without consuming all tokens.")
    def unexpected_symbol(self, nonterminal, actual_terminal, expected_terminals, rule):
        return self._error("Unexpected symbol (line {line}, col {col}) when parsing parse_{nt}.  Expected {expected}, got {actual}.".format(
            line=actual_terminal.line,
            col=actual_terminal.col,
            nt=nonterminal,
            expected=', '.join(expected_terminals),
            actual=actual_terminal
        ))
    def no_more_tokens(self, nonterminal, expected_terminal, last_terminal):
        return self._error("No more tokens.  Expecting " + expected_terminal)
    def invalid_terminal(self, nonterminal, invalid_terminal):
        return self._error("Invalid symbol ID: {} ({})".format(invalid_terminal.id, invalid_terminal.string))
    def unrecognized_token(self, string, line, col):
        lines = string.split('\n')
        bad_line = lines[line-1]
        return self._error('Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
            line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
        ))

class ParserContext:
  def __init__(self, tokens, errors):
    self.__dict__.update(locals())
    self.nonterminal_string = None
    self.rule_string = None

###############
# Parser Code #
###############

terminals = {
{% for terminal in grammar.standard_terminals %}
    {{terminal.id}}: '{{terminal.string}}',
{% endfor %}

{% for terminal in grammar.standard_terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

# table[nonterminal][terminal] = rule
table = [
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}}],
{% endfor %}
]

nonterminal_first = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.first(nonterminal)])}}],
{% endfor %}
}

nonterminal_follow = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.follow(nonterminal)])}}],
{% endfor %}
}

rule_first = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: [{{', '.join([str(t.id) for t in grammar.first(rule.production)])}}],
{% endfor %}
}

nonterminal_rules = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [
  {% for rule in grammar.get_expanded_rules() %}
    {% if rule.nonterminal.id == nonterminal.id %}
        "{{rule}}",
    {% endif %}
  {% endfor %}
    ],
{% endfor %}
}

rules = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: "{{rule}}",
{% endfor %}
}

def is_terminal(id): return isinstance(id, int) and 0 <= id <= {{len(grammar.standard_terminals) - 1}}

def parse(tokens, errors=None, start=None):
    if errors is None:
        errors = DefaultSyntaxErrorHandler()
    if isinstance(tokens, str):
        tokens = lex(tokens, 'string', errors)
    ctx = ParserContext(tokens, errors)
    tree = parse_{{grammar.start.string.lower()}}(ctx)
    if tokens.current() != None:
        raise ctx.errors.excess_tokens()
    return tree

def expect(ctx, terminal_id):
    current = ctx.tokens.current()
    if not current:
        raise ctx.errors.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last())
    if current.id != terminal_id:
        raise ctx.errors.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule)
    next = ctx.tokens.advance()
    if next and not is_terminal(next.id):
        raise ctx.errors.invalid_terminal(ctx.nonterminal, next)
    return current

{% for expression_nonterminal in grammar.expression_nonterminals %}
    {% py name = expression_nonterminal.string %}

# START definitions for expression parser: {{name}}
infix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
    {% endfor %}
}

prefix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['unary'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
    {% endfor %}
}

def get_infix_binding_power_{{name}}(terminal_id):
    try:
        return infix_binding_power_{{name}}[terminal_id]
    except:
        return 0

def get_prefix_binding_power_{{name}}(terminal_id):
    try:
        return prefix_binding_power_{{name}}[terminal_id]
    except:
        return 0

def parse_{{name}}(ctx):
    return parse_{{name}}_internal(ctx, rbp=0)

def parse_{{name}}_internal(ctx, rbp=0):
    left = nud_{{name}}(ctx)
    if isinstance(left, ParseTree):
        left.isExpr = True
        left.isNud = True
    while ctx.tokens.current() and rbp < get_infix_binding_power_{{name}}(ctx.tokens.current().id):
        left = led_{{name}}(left, ctx)
    if left:
        left.isExpr = True
    return left

def nud_{{name}}(ctx):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = ctx.tokens.current()
    ctx.nonterminal = "{{name}}"

    if not current:
        return tree

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
    {{'if' if i == 0 else 'elif'}} current.id in rule_first[{{rule.id}}]:
        # {{rule}}
        ctx.rule = rules[{{rule.id}}]
        {% py ast = rule.nudAst if not isinstance(rule.operator, PrefixOperator) else rule.ast %}
        {% if isinstance(ast, AstSpecification) %}
        ast_parameters = OrderedDict([
          {% for k,v in ast.parameters.items() %}
            ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{ast.name}}', ast_parameters)
        {% elif isinstance(ast, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{ast.idx}})
        {% endif %}

        tree.nudMorphemeCount = {{len(rule.nud_production)}}

        {% for morpheme in rule.nud_production.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}}))
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add(parse_{{name}}_internal(ctx, get_prefix_binding_power_{{name}}({{rule.operator.operator.id}})))
        tree.isPrefix = True
            {% else %}
        tree.add(parse_{{rule.nonterminal.string.lower()}}(ctx))
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx))
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

def led_{{name}}(left, ctx):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = ctx.tokens.current()
    ctx.nonterminal = "{{name}}"

    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) %}

    if current.id == {{led[0].id}}: # {{led[0]}}
        # {{rule}}
        ctx.rule = rules[{{rule.id}}]
        {% if isinstance(rule.ast, AstSpecification) %}
        ast_parameters = OrderedDict([
          {% for k,v in rule.ast.parameters.items() %}
            ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters)
        {% elif isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

        {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
          {% py nt = rule.nud_production.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
        tree.isExprNud = True
          {% endif %}
        {% endif %}

        tree.add(left)

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}})) # {{morpheme}}
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
            {% if isinstance(rule.operator, InfixOperator) %}
        tree.isInfix = True
            {% endif %}
        tree.add(parse_{{name}}_internal(ctx, get_infix_binding_power_{{name}}({{rule.operator.operator.id}}) - modifier))
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx))
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

# END definitions for expression parser: {{name}}
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
def parse_{{name}}(ctx):
    current = ctx.tokens.current()
    rule = table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] if current else -1
    tree = ParseTree(NonTerminal({{nonterminal.id}}, '{{name}}'))
    ctx.nonterminal = "{{name}}"

    {% if isinstance(nonterminal.macro, LL1ListMacro) %}
    tree.list = True
    {% else %}
    tree.list = False
    {% endif %}

    {% if not grammar.must_consume_tokens(nonterminal) %}
    if current != None and current.id in nonterminal_follow[{{nonterminal.id}}] and current.id not in nonterminal_first[{{nonterminal.id}}]:
        return tree
    {% endif %}

    if current == None:
    {% if grammar.must_consume_tokens(nonterminal) %}
        raise ctx.errors.unexpected_eof()
    {% else %}
        return tree
    {% endif %}

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

      {% if index == 0 %}
    if rule == {{rule.id}}: # {{rule}}
      {% else %}
    elif rule == {{rule.id}}: # {{rule}}
      {% endif %}

        ctx.rule = rules[{{rule.id}}]

      {% if isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
      {% elif isinstance(rule.ast, AstSpecification) %}
        ast_parameters = OrderedDict([
        {% for k,v in rule.ast.parameters.items() %}
            ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
        {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters)
      {% else %}
        tree.astTransform = AstTransformSubstitution(0)
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
        t = expect(ctx, {{morpheme.id}}) # {{morpheme}}
        tree.add(t)
          {% if isinstance(nonterminal.macro, LL1ListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
        tree.listSeparator = t
            {% endif %}
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
        subtree = parse_{{morpheme.string.lower()}}(ctx)
        tree.add(subtree)
        {% endif %}

      {% endfor %}
        return tree
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
    raise ctx.errors.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      [terminals[x] for x in nonterminal_first[{{nonterminal.id}}] if x >=0],
      rules[{{rule.id}}]
    )
    {% else %}
    return tree
    {% endif %}

{% endfor %}

{% if lexer %}

##############
# Lexer Code #
##############

# START USER CODE
{{lexer.code}}
# END USER CODE

def emit(ctx, terminal, source_string, line, col):
    if terminal:
        ctx.tokens.append(Terminal(terminals[terminal], terminal, source_string, ctx.resource, line, col))

{% if re.search(r'def\s+default_action', lexer.code) is None %}
def default_action(ctx, terminal, source_string, line, col):
    emit(ctx, terminal, source_string, line, col)
{% endif %}

{% if re.search(r'def\s+init', lexer.code) is None %}
def init():
    return {}
{% endif %}

{% if re.search(r'def\s+destroy', lexer.code) is None %}
def destroy(context):
    pass
{% endif %}

class LexerStackPush:
    def __init__(self, mode):
        self.mode = mode

class LexerAction:
    def __init__(self, action):
        self.action = action

class LexerContext:
    def __init__(self, string, resource, errors, user_context):
        self.__dict__.update(locals())
        self.stack = ['default']
        self.line = 1
        self.col = 1
        self.tokens = []
        self.user_context = user_context
        self.re_match = None # https://docs.python.org/3/library/re.html#match-objects

class HermesLexer:
    regex = {
      {% for mode, regex_list in lexer.items() %}
        '{{mode}}': OrderedDict([
          {% for regex in regex_list %}
          (re.compile({{regex.regex}}{{", "+' | '.join(['re.'+x for x in regex.options]) if regex.options else ''}}), [
              # (terminal, group, function)
            {% for output in regex.outputs %}
              {% if isinstance(output, RegexOutput) %}
              ({{"'" + output.terminal.string.lower() + "'" if output.terminal else 'None'}}, {{output.group}}, {{output.function}}),
              {% elif isinstance(output, LexerStackPush) %}
              LexerStackPush('{{output.mode}}'),
              {% elif isinstance(output, LexerAction) %}
              LexerAction('{{output.action}}'),
              {% endif %}
            {% endfor %}
          ]),
          {% endfor %}
        ]),
      {% endfor %}
    }

    def _advance_line_col(self, string, length, line, col):
        for i in range(length):
            if string[i] == '\n':
                line += 1
                col = 1
            else:
                col += 1
        return (line, col)

    def _advance_string(self, ctx, string):
        (ctx.line, ctx.col) = self._advance_line_col(string, len(string), ctx.line, ctx.col)
        ctx.string = ctx.string[len(string):]

    def _next(self, ctx, debug=False):
        for regex, outputs in self.regex[ctx.stack[-1]].items():

            if debug:
                from xtermcolor import colorize
                token_count = len(ctx.tokens)
                print('{1} ({2}, {3}) regex: {0}'.format(
                    colorize(regex.pattern, ansi=40), colorize(ctx.string[:20].replace('\n', '\\n'), ansi=15), ctx.line, ctx.col)
                )

            match = regex.match(ctx.string)
            if match:
                ctx.re_match = match
                for output in outputs:
                    if isinstance(output, tuple):
                        (terminal, group, function) = output
                        function = function if function else default_action
                        source_string = match.group(group) if group is not None else ''
                        (group_line, group_col) = self._advance_line_col(ctx.string, match.start(group) if group else 0, ctx.line, ctx.col)
                        function(
                            ctx,
                            terminal,
                            source_string,
                            group_line,
                            group_col
                        )
                        if debug:
                            print('    matched: {}'.format(colorize(match.group(0).replace('\n', '\\n'), ansi=3)))
                            for token in ctx.tokens[token_count:]:
                                print('    emit: [{}] [{}, {}] [{}] stack:{} context:{}'.format(
                                    colorize(token.str, ansi=9),
                                    colorize(str(token.line), ansi=5),
                                    colorize(str(token.col), ansi=5),
                                    colorize(token.source_string, ansi=3),
                                    colorize(str(ctx.stack), ansi=4),
                                    colorize(str(ctx.user_context), ansi=13)
                                ))
                            token_count = len(ctx.tokens)
                    if isinstance(output, LexerStackPush):
                        ctx.stack.append(output.mode)
                        if debug:
                            print('    push on stack: {}'.format(colorize(output.mode, ansi=4)))
                    if isinstance(output, LexerAction):
                        if output.action == 'pop':
                            mode = ctx.stack.pop()
                            if debug:
                                print('    pop off stack: {}'.format(colorize(mode, ansi=4)))

                self._advance_string(ctx, match.group(0))
                return len(match.group(0)) > 0
        return False

    def lex(self, string, resource, errors=None, debug=False):
        if errors is None:
            errors = DefaultSyntaxErrorHandler()
        string_copy = string
        user_context = init()
        ctx = LexerContext(string, resource, errors, user_context)

        while len(ctx.string):
            matched = self._next(ctx, debug)
            if matched == False:
                raise ctx.errors.unrecognized_token(string_copy, ctx.line, ctx.col)

        destroy(ctx.user_context)
        return ctx.tokens

def lex(source, resource, errors=None, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, errors, debug))

{% endif %}

{% if add_main %}

########
# Main #
########

def cli():
    if len(sys.argv) != 3 or (sys.argv[1] not in ['parsetree', 'ast']{% if lexer %} and sys.argv[1] != 'tokens'{% endif %}):
        sys.stderr.write("Usage: {0} parsetree <source>\n".format(argv[0]))
        sys.stderr.write("Usage: {0} ast <source>\n".format(argv[0]))
        {% if lexer %}
        sys.stderr.write("Usage: {0} tokens <source>\n".format(argv[0]))
        {% endif %}
        sys.exit(-1)

    try:
        with open(sys.argv[2]) as fp:
            tokens = lex(fp.read(), os.path.basename(sys.argv[2]))
    except SyntaxError as error:
        sys.exit(error)

    if sys.argv[1] in ['parsetree', 'ast']:
        try:
            tree = parse(tokens)
            if sys.argv[1] == 'parsetree':
                print(tree.dumps(indent=2))
            else:
                ast = tree.ast()
                print(ast.dumps(indent=2) if ast else ast)
        except SyntaxError as error:
            print(error)

    if sys.argv[1] == 'tokens':
        for token in tokens:
            print(token)

if __name__ == '__main__':
    cli()
{% endif %}
