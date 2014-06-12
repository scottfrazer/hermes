import sys
import inspect
from collections import OrderedDict
from ..Common import *

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro, OptionallyTerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

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

def parse(tokens, error_formatter=None, start=None):
    if error_formatter is None:
        error_formatter = DefaultSyntaxErrorFormatter()
    ctx = ParserContext(tokens, error_formatter)
    tree = parse_{{grammar.start.string.lower()}}(ctx)
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

{% for expression_nonterminal in grammar.expression_nonterminals %}
    {% py name = expression_nonterminal.string %}

# START definitions for expression parser `{{name}}`
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
        {% if isinstance(rule.nudAst, AstSpecification) %}
        ast_parameters = OrderedDict([
          {% for k,v in rule.nudAst.parameters.items() %}
            ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{rule.nudAst.name}}', ast_parameters)
        {% elif isinstance(rule.nudAst, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{rule.nudAst.idx}})
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

# END definitions for expression parser `{{name}}`
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
def parse_{{name}}(ctx):
    current = ctx.tokens.current()
    rule = table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] if current else -1
    tree = ParseTree(NonTerminal({{nonterminal.id}}, '{{name}}'))
    ctx.nonterminal = "{{name}}"

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist'
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
    tree.list = 'nlist'
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist'
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist'
    {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
    tree.list = 'otlist'
    {% else %}
    tree.list = False
    {% endif %}

    {% if not grammar.must_consume_tokens(nonterminal) %}
    if current != None and current.id in nonterminal_follow[{{nonterminal.id}}] and current.id not in nonterminal_first[{{nonterminal.id}}]:
        return tree
    {% endif %}

    if current == None:
    {% if grammar.must_consume_tokens(nonterminal) %}
        raise SyntaxError('Error: unexpected end of file')
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
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
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
    raise SyntaxError(ctx.error_formatter.unexpected_symbol(
      ctx.nonterminal,
      ctx.tokens.current(),
      nonterminal_first({{nonterminal.id}}),
      rule[{{rule.id}}]
    ))
    {% else %}
    return tree
    {% endif %}

{% endfor %}

if __name__ == '__main__':
    import json
    import os

    if len(sys.argv) != 3 or sys.argv[1] not in ['parsetree', 'ast']:
        sys.exit("Usage: Parser.py <parsetree|ast> <tokens_file>")

    tokens = TokenStream()
    with open(os.path.expanduser(sys.argv[2])) as fp:
        json_tokens = json.loads(fp.read())
        for json_token in json_tokens:
            tokens.append(Terminal(
                terminals[json_token['terminal']],
                json_token['terminal'],
                json_token['source_string'],
                json_token['resource'],
                json_token['line'],
                json_token['col']
            ))

    try:
        tree = parse(tokens)
        if sys.argv[1] == 'parsetree':
            print(ParseTreePrettyPrintable(tree))
        else:
            print(AstPrettyPrintable(tree.toAst()))
    except SyntaxError as error:
        print(error)
