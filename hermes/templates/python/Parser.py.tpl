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

nonterminals = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: '{{nonterminal.string}}',
{% endfor %}

{% for nonterminal in grammar.nonterminals %}
    '{{nonterminal.string.lower()}}': {{nonterminal.id}},
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

def get_nonterminal_str(id): return nonterminals[id]
def get_terminal_str(id): return terminals[id]
def get_nonterminal_id(str): return nonterminals[str]
def get_terminal_str(str): return terminals[str]
def is_terminal(id): return isinstance(id, int) and id in terminals
def is_nonterminal(id): return isinstance(id, int) and id in nonterminals

def parse(tokens):
    #return Parser().parse(tokens)
    tree = parse_{{grammar.start.string.lower()}}(tokens)
    if tokens.current() != None:
        raise SyntaxError('Finished parsing without consuming all tokens.')
    return tree

def expect(tokens, terminal_id):
    current = tokens.current()
    if not current:
        raise SyntaxError('No more tokens.  Expecting {}'.format(terminals[terminal_id]))
    if current.id != terminal_id:
        raise SyntaxError('Unexpected symbol (line {}, col {}) when parsing {}.  Expected {}, got {}.'.format(
            current.line,
            current.col,
            inspect.stack()[2][3],
            terminals[terminal_id],
            current
        ))

    next = tokens.advance()
    if next and not is_terminal(next.id):
        raise SyntaxError('Invalid symbol ID: {} ({})'.format(next.id, next))

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

def parse_{{name}}(tokens):
    return parse_{{name}}_internal(tokens, rbp=0)

def parse_{{name}}_internal(tokens, rbp=0):
    left = nud_{{name}}(tokens)
    if isinstance(left, ParseTree):
        left.isExpr = True
        left.isNud = True
    while tokens.current() and rbp < get_infix_binding_power_{{name}}(tokens.current().id):
        left = led_{{name}}(left, tokens)
    if left:
        left.isExpr = True
    return left

def nud_{{name}}(tokens):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = tokens.current()

    if not current:
        return tree

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
    {{'if' if i == 0 else 'elif'}} current.id in rule_first[{{rule.id}}]:
        # {{rule}}
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
        tree.add(expect(tokens, {{morpheme.id}}))
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add(parse_{{name}}_internal(tokens, get_prefix_binding_power_{{name}}({{rule.operator.operator.id}})))
        tree.isPrefix = True
            {% else %}
        tree.add(parse_{{rule.nonterminal.string.lower()}}(tokens))
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(tokens))
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

def led_{{name}}(left, tokens):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = tokens.current()

    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) %}

    if current.id == {{led[0].id}}: # {{led[0]}}

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
        tree.add(expect(tokens, {{morpheme.id}})) # {{morpheme}}
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
            {% if isinstance(rule.operator, InfixOperator) %}
        tree.isInfix = True
            {% endif %}
        tree.add(parse_{{name}}_internal(tokens, get_infix_binding_power_{{name}}({{rule.operator.operator.id}}) - modifier))
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(tokens))
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

# END definitions for expression parser `{{name}}`
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
def parse_{{name}}(tokens):
    current = tokens.current()
    rule = table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] if current else -1
    tree = ParseTree(NonTerminal({{nonterminal.id}}, '{{name}}'))

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
        t = expect(tokens, {{morpheme.id}}) # {{morpheme}}
        tree.add(t)
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
        tree.listSeparator = t
            {% endif %}
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
        subtree = parse_{{morpheme.string.lower()}}(tokens)
        tree.add(subtree)
        {% endif %}

      {% endfor %}
        return tree
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
    raise SyntaxError('Error: Unexpected symbol ({}) on line {}, column {} when parsing {}'.format(
      current,
      current.line,
      current.col,
      inspect.stack()[1][3]
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
