{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro, OptionallyTerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

var common = require('./common.js');

var terminals = {
{% for terminal in grammar.standard_terminals %}
    {{terminal.id}}: '{{terminal.string}}',
{% endfor %}

{% for terminal in grammar.standard_terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

// table[nonterminal][terminal] = rule
var table = [
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}}],
{% endfor %}
]

var nonterminal_first = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.first(nonterminal)])}}],
{% endfor %}
}

var nonterminal_follow = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.follow(nonterminal)])}}],
{% endfor %}
}

var rule_first = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: [{{', '.join([str(t.id) for t in grammar.first(rule.production)])}}],
{% endfor %}
}

var nonterminal_rules = {
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

var rules = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: "{{rule}}",
{% endfor %}
}

function is_terminal(id){
    return 0 <= id && id <= {{len(grammar.standard_terminals) - 1}};
}

function parse(tokens, error_formatter, start) {
    if (error_formatter === undefined) {
        error_formatter = new common.DefaultSyntaxErrorFormatter();
    }
    var ctx = new common.ParserContext(tokens, error_formatter);
    var tree = parse_{{grammar.start.string.lower()}}(ctx);
    if (tokens.current() != null) {
        throw new common.SyntaxError('Finished parsing without consuming all tokens.');
    }
    return tree;
}

function expect(ctx, terminal_id) {
    var current = ctx.tokens.current();
    if (current == null) {
        throw new common.SyntaxError(ctx.error_formatter.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last()));
    }
    if (current.id != terminal_id) {
        throw new common.SyntaxError(ctx.error_formatter.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule));
    }
    var next = ctx.tokens.advance();
    if (next && !is_terminal(next.id)) {
        throw new common.SyntaxError(ctx.error_formatter.invalid_terminal(ctx.nonterminal, next));
    }
    return current;
}

{% for expression_nonterminal in grammar.expression_nonterminals %}
    {% py name = expression_nonterminal.string %}

// START definitions for expression parser `{{name}}`
var infix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, // {{rule}}
        {% endif %}
    {% endfor %}
}

var prefix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['unary'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, // {{rule}}
        {% endif %}
    {% endfor %}
}

function get_infix_binding_power_{{name}}(terminal_id) {
    if (terminal_id in infix_binding_power_{{name}}) {
        return infix_binding_power_{{name}}[terminal_id];
    } else {
        return 0;
    }
}

function get_prefix_binding_power_{{name}}(terminal_id) {
    if (terminal_id in prefix_binding_power_{{name}}) {
        return prefix_binding_power_{{name}}[terminal_id];
    } else {
        return 0;
    }
}

function parse_{{name}}(ctx) {
    return parse_{{name}}_internal(ctx, 0);
}

function parse_{{name}}_internal(ctx, rbp) {
    left = nud_{{name}}(ctx);
    if (left instanceof common.ParseTree) {
        left.isExpr = true;
        left.isNud = true;
    }
    while (ctx.tokens.current() && rbp < get_infix_binding_power_{{name}}(ctx.tokens.current().id)) {
        left = led_{{name}}(left, ctx);
    }
    if (left) {
        left.isExpr = true;
    }
    return left;
}

function nud_{{name}}(ctx) {
    var tree = new common.ParseTree(new common.NonTerminal({{expression_nonterminal.id}}, '{{name}}'));
    var current = ctx.tokens.current();
    ctx.nonterminal = "{{name}}";

    if (!current) {
        return tree;
    }

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
    {{'if' if i == 0 else 'else if'}} (rule_first[{{rule.id}}].indexOf(current.id) != -1) {
        // {{rule}}
        ctx.rule = rules[{{rule.id}}];
        {% if isinstance(rule.nudAst, AstSpecification) %}
        ast_parameters = {
          {% for k,v in rule.nudAst.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
          {% endfor %}
        }
        tree.astTransform = new common.AstTransformNodeCreator('{{rule.nudAst.name}}', ast_parameters);
        {% elif isinstance(rule.nudAst, AstTranslation) %}
        tree.astTransform = new common.AstTransformSubstitution({{rule.nudAst.idx}});
        {% endif %}

        tree.nudMorphemeCount = {{len(rule.nud_production)}};

        {% for morpheme in rule.nud_production.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}}));
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add(parse_{{name}}_internal(ctx, get_prefix_binding_power_{{name}}({{rule.operator.operator.id}})));
        tree.isPrefix = true;
            {% else %}
        tree.add(parse_{{rule.nonterminal.string.lower()}}(ctx));
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx));
          {% endif %}
        {% endfor %}
    }
      {% endif %}
    {% endfor %}

    return tree;
}

function led_{{name}}(left, ctx) {
    var tree = new common.ParseTree(new common.NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    var current = ctx.tokens.current()
    ctx.nonterminal = "{{name}}";

    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) %}
    if (current.id == {{led[0].id}}) { // {{led[0]}}
        // {{rule}}
        ctx.rule = rules[{{rule.id}}];
        {% if isinstance(rule.ast, AstSpecification) %}
        ast_parameters = {
          {% for k,v in rule.ast.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
          {% endfor %}
        }
        tree.astTransform = new common.AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters);
        {% elif isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = new common.AstTransformSubstitution({{rule.ast.idx}});
        {% endif %}

        {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
          {% py nt = rule.nud_production.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
        tree.isExprNud = true;
          {% endif %}
        {% endif %}

        tree.add(left);

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}})); // {{morpheme}}
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
            {% if isinstance(rule.operator, InfixOperator) %}
        tree.isInfix = true;
            {% endif %}
        tree.add(parse_{{name}}_internal(ctx, get_infix_binding_power_{{name}}({{rule.operator.operator.id}}) - modifier));
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx));
          {% endif %}
        {% endfor %}
    }
      {% endif %}
    {% endfor %}

    return tree;
}

// END definitions for expression parser `{{name}}`
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
function parse_{{name}}(ctx) {
    var current = ctx.tokens.current();
    var rule = current != null ? table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] : -1;
    var tree = new common.ParseTree(new common.NonTerminal({{nonterminal.id}}, '{{name}}'));
    ctx.nonterminal = "{{name}}";

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist';
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
    tree.list = 'nlist';
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist';
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist';
    {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
    tree.list = 'otlist';
    {% else %}
    tree.list = false;
    {% endif %}

    {% if not grammar.must_consume_tokens(nonterminal) %}
    if (current != null && nonterminal_follow[{{nonterminal.id}}].indexOf(current.id) != -1 && nonterminal_first[{{nonterminal.id}}].indexOf(current.id) == -1) {
        return tree;
    }
    {% endif %}

    if (current == null) {
    {% if grammar.must_consume_tokens(nonterminal) %}
        throw new common.SyntaxError('Error: unexpected end of file');
    {% else %}
        return tree
    {% endif %}
    }

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

      {% if index == 0 %}
    if (rule == {{rule.id}}) { // {{rule}}
      {% else %}
    else if (rule == {{rule.id}}) { // {{rule}}
      {% endif %}

        ctx.rule = rules[{{rule.id}}];

      {% if isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = new common.AstTransformSubstitution({{rule.ast.idx}});
      {% elif isinstance(rule.ast, AstSpecification) %}
        ast_parameters = {
        {% for k,v in rule.ast.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
        {% endfor %}
        }
        tree.astTransform = new common.AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters);
      {% else %}
        tree.astTransform = new common.AstTransformSubstitution(0);
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
        t = expect(ctx, {{morpheme.id}}); // {{morpheme}}
        tree.add(t);
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
        tree.listSeparator = t;
            {% endif %}
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
        subtree = parse_{{morpheme.string.lower()}}(ctx);
        tree.add(subtree);
        {% endif %}

      {% endfor %}
        return tree;
    }
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
    throw new common.SyntaxError(ctx.error_formatter.unexpected_symbol(
        ctx.nonterminal,
        ctx.tokens.current(),
        nonterminal_first[{{nonterminal.id}}],
        rules[{{rule.id}}]
    ));
    {% else %}
    return tree;
    {% endif %}
}
{% endfor %}

{% if nodejs %}
module.exports = {
  parse: parse,
  terminals: terminals
}
{% endif %}
