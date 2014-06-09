{% if java_package %}
package {{java_package}};
{% endif %}

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro, OptionallyTerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

import java.util.*;

public class {{prefix}}Parser {

    private static Map<Integer, List<TerminalIdentifier>> nonterminal_first;
    private static Map<Integer, List<TerminalIdentifier>> nonterminal_follow;
    private static Map<Integer, List<TerminalIdentifier>> rule_first;
    private static Map<Integer, List<String>> nonterminal_rules;
    private static Map<Integer, String> rules;
    public static {{prefix}}TerminalMap terminal_map = new {{prefix}}TerminalMap({{prefix}}TerminalIdentifier.values());

    private static class ParserContext {
        public TokenStream tokens;
        public SyntaxErrorFormatter error_formatter;
        public String nonterminal;
        public String rule;

        public ParserContext(TokenStream tokens, SyntaxErrorFormatter error_formatter) {
            this.tokens = tokens;
            this.error_formatter = error_formatter;
        }
    }

    private static class DefaultSyntaxErrorFormatter implements SyntaxErrorFormatter {
        public String unexpected_eof(String method, List<TerminalIdentifier> expected, List<String> nt_rules) {
            return "Error: unexpected end of file";
        }

        public String excess_tokens(String method, Terminal terminal) {
            return "Finished parsing without consuming all tokens.";
        }

        public String unexpected_symbol(String method, Terminal actual, List<TerminalIdentifier> expected, String rule) {
            ArrayList<String> expected_terminals = new ArrayList<String>();
            for ( TerminalIdentifier e : expected ) {
                expected_terminals.add(e.string());
            }
            return String.format(
                "Unexpected symbol (line %d, col %d) when parsing parse_%s.  Expected %s, got %s.",
                actual.getLine(), actual.getColumn(), method, Utility.join(expected_terminals, ", "), actual.toPrettyString()
            );
        }

        public String no_more_tokens(String method, TerminalIdentifier expecting, Terminal last) {
            return "No more tokens.  Expecting " + expecting.string();
        }

        public String invalid_terminal(String method, Terminal invalid) {
            return "Invalid symbol ID: "+invalid.getId()+" ("+invalid.getTerminalStr()+")";
        }
    }

    public static class {{prefix}}TerminalMap implements TerminalMap {
        private Map<Integer, TerminalIdentifier> id_to_term;
        private Map<String, TerminalIdentifier> str_to_term;

        {{prefix}}TerminalMap({{prefix}}TerminalIdentifier[] terminals) {
            id_to_term = new HashMap<Integer, TerminalIdentifier>();
            str_to_term = new HashMap<String, TerminalIdentifier>();
            for( {{prefix}}TerminalIdentifier terminal : terminals ) {
                Integer id = new Integer(terminal.id());
                String str = terminal.string();
                id_to_term.put(id, terminal);
                str_to_term.put(str, terminal);
            }
        }

        public TerminalIdentifier get(String string) { return this.str_to_term.get(string); }
        public TerminalIdentifier get(int id) { return this.id_to_term.get(id); }
        public boolean isValid(String string) { return this.str_to_term.containsKey(string); }
        public boolean isValid(int id) { return this.id_to_term.containsKey(id); }
    }

    public enum {{prefix}}TerminalIdentifier implements TerminalIdentifier {
{% for index, terminal in enumerate(grammar.standard_terminals) %}
        TERMINAL_{{terminal.string.upper()}}({{terminal.id}}, "{{terminal.string}}"){{',' if index!=len(grammar.standard_terminals)-1 else ';'}}
{% endfor %}

        private final int id;
        private final String string;

        {{prefix}}TerminalIdentifier(int id, String string) {
            this.id = id;
            this.string = string;
        }

        public int id() {return id;}
        public String string() {return string;}
    }

    /* table[nonterminal][terminal] = rule */
    private static final int[][] table = {
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
        { {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} },
{% endfor %}
    };

    static {
        Map<Integer, List<TerminalIdentifier>> map = new HashMap<Integer, List<TerminalIdentifier>>();
{% for nonterminal in grammar.nonterminals %}
        map.put({{nonterminal.id}}, Arrays.asList(new TerminalIdentifier[] {
  {% for terminal in grammar.first(nonterminal) %}
    {% if terminal in grammar.standard_terminals %}
            {{prefix}}TerminalIdentifier.TERMINAL_{{terminal.string.upper()}},
    {% endif %}
  {% endfor %}
        }));
{% endfor %}
        nonterminal_first = Collections.unmodifiableMap(map);
    }

    static {
        Map<Integer, List<TerminalIdentifier>> map = new HashMap<Integer, List<TerminalIdentifier>>();
{% for nonterminal in grammar.nonterminals %}
        map.put({{nonterminal.id}}, Arrays.asList(new TerminalIdentifier[] {
  {% for terminal in grammar.follow(nonterminal) %}
    {% if terminal in grammar.standard_terminals %}
            {{prefix}}TerminalIdentifier.TERMINAL_{{terminal.string.upper()}},
    {% endif %}
  {% endfor %}
        }));
{% endfor %}
        nonterminal_follow = Collections.unmodifiableMap(map);
    }

    static {
        Map<Integer, List<TerminalIdentifier>> map = new HashMap<Integer, List<TerminalIdentifier>>();
{% for rule in grammar.get_expanded_rules() %}
        map.put({{rule.id}}, Arrays.asList(new TerminalIdentifier[] {
  {% for terminal in grammar.first(rule.production) %}
    {% if terminal in grammar.standard_terminals %}
            {{prefix}}TerminalIdentifier.TERMINAL_{{terminal.string.upper()}},
    {% endif %}
  {% endfor %}
        }));
{% endfor %}
        rule_first = Collections.unmodifiableMap(map);
    }

    static {
        Map<Integer, List<String>> map = new HashMap<Integer, List<String>>();
{% for nonterminal in grammar.nonterminals %}
        map.put({{nonterminal.id}}, new ArrayList<String>());
{% endfor %}
{% for rule in grammar.get_expanded_rules() %}
        map.get({{rule.nonterminal.id}}).add("{{rule}}");
{% endfor %}
        nonterminal_rules = Collections.unmodifiableMap(map);
    }

    static {
        Map<Integer, String> map = new HashMap<Integer, String>();
{% for rule in grammar.get_expanded_rules() %}
        map.put(new Integer({{rule.id}}), "{{rule}}");
{% endfor %}
        rules = Collections.unmodifiableMap(map);
    }

    public static boolean is_terminal(int id) {
        return 0 <= id && id <= {{len(grammar.standard_terminals) - 1}};
    }

    public static ParseTree parse(TokenStream tokens) throws SyntaxError {
        return parse(tokens, new DefaultSyntaxErrorFormatter());
    }

    public static ParseTree parse(TokenStream tokens, SyntaxErrorFormatter error_formatter) throws SyntaxError {
        ParserContext ctx = new ParserContext(tokens, error_formatter);
        ParseTree tree = parse_{{grammar.start.string.lower()}}(ctx);
        if (ctx.tokens.current() != null) {
            StackTraceElement[] stack = Thread.currentThread().getStackTrace();
            throw new SyntaxError(ctx.error_formatter.excess_tokens(stack[1].getMethodName(), ctx.tokens.current()));
        }
        return tree;
    }

    private static Terminal expect(ParserContext ctx, TerminalIdentifier expecting) throws SyntaxError {
        Terminal current = ctx.tokens.current();
        if (current == null) {
            throw new SyntaxError(ctx.error_formatter.no_more_tokens(ctx.nonterminal, expecting, ctx.tokens.last()));
        }
        if (current.getId() != expecting.id()) {
            ArrayList<TerminalIdentifier> expectedList = new ArrayList<TerminalIdentifier>();
            expectedList.add(expecting);
            throw new SyntaxError(ctx.error_formatter.unexpected_symbol(ctx.nonterminal, current, expectedList, ctx.rule));
        }
        Terminal next = ctx.tokens.advance();
        if ( next != null && !is_terminal(next.getId()) ) {
            throw new SyntaxError(ctx.error_formatter.invalid_terminal(ctx.nonterminal, next));
        }
        return current;
    }

{% for expression_nonterminal in grammar.expression_nonterminals %}
  {% py name = expression_nonterminal.string %}
    private static Map<Integer, Integer> infix_binding_power_{{name}};
    private static Map<Integer, Integer> prefix_binding_power_{{name}};

    static {
        Map<Integer, Integer> map = new HashMap<Integer, Integer>();
  {% for rule in grammar.get_rules(expression_nonterminal) %}
    {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
        map.put({{rule.operator.operator.id}}, {{rule.operator.binding_power}}); /* {{rule}} */
    {% endif %}
  {% endfor %}
        infix_binding_power_{{name}} = Collections.unmodifiableMap(map);
    }

    static {
        Map<Integer, Integer> map = new HashMap<Integer, Integer>();
  {% for rule in grammar.get_rules(expression_nonterminal) %}
    {% if rule.operator and rule.operator.associativity in ['unary'] %}
        map.put({{rule.operator.operator.id}}, {{rule.operator.binding_power}}); /* {{rule}} */
    {% endif %}
  {% endfor %}
        prefix_binding_power_{{name}} = Collections.unmodifiableMap(map);
    }

    static int get_infix_binding_power_{{name}}(int terminal_id) {
        if (infix_binding_power_{{name}}.containsKey(terminal_id)) {
            return infix_binding_power_{{name}}.get(terminal_id);
        }
        return 0;
    }

    static int get_prefix_binding_power_{{name}}(int terminal_id) {
        if (prefix_binding_power_{{name}}.containsKey(terminal_id)) {
            return prefix_binding_power_{{name}}.get(terminal_id);
        }
        return 0;
    }

    public static ParseTree parse_{{name}}(ParserContext ctx) throws SyntaxError {
        return parse_{{name}}_internal(ctx, 0);
    }

    public static ParseTree parse_{{name}}_internal(ParserContext ctx, int rbp) throws SyntaxError {
        ParseTree left = nud_{{name}}(ctx);
        if ( left instanceof ParseTree ) {
            left.setExpr(true);
            left.setNud(true);
        }
        while (ctx.tokens.current() != null && rbp < get_infix_binding_power_{{name}}(ctx.tokens.current().getId())) {
            left = led_{{name}}(left, ctx);
        }
        if (left != null) {
            left.setExpr(true);
        }
        return left;
    }

    private static ParseTree nud_{{name}}(ParserContext ctx) throws SyntaxError {
        ParseTree tree = new ParseTree( new NonTerminal({{expression_nonterminal.id}}, "{{name}}") );
        Terminal current = ctx.tokens.current();

        if (current == null) {
            return tree;
        }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py ruleFirstSet = grammar.first(rule.production) %}

    {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first(expression_nonterminal))%}
        {{'if' if i == 0 else 'else if'}} (rule_first.get({{rule.id}}).contains(terminal_map.get(current.getId()))) {

      {% py ast = rule.nudAst if rule.nudAst else rule.ast %}
            /* ({{rule.id}}) {{rule}} */
            ctx.nonterminal = "{{name}}";
            ctx.rule = rules.get({{rule.id}});

      {% if isinstance(ast, AstSpecification) %}
            LinkedHashMap<String, Integer> parameters = new LinkedHashMap<String, Integer>();
        {% for key, value in ast.parameters.items() %}
            parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
        {% endfor %}
            tree.setAstTransformation(new AstTransformNodeCreator("{{ast.name}}", parameters));
      {% elif isinstance(ast, AstTranslation) %}
            tree.setAstTransformation(new AstTransformSubstitution({{ast.idx}}));
      {% endif %}

            tree.setNudMorphemeCount({{len(rule.nud_production)}});

      {% for morpheme in rule.nud_production.morphemes %}
        {% if isinstance(morpheme, Terminal) %}
            tree.add(expect(ctx, {{prefix}}TerminalIdentifier.TERMINAL_{{morpheme.string.upper()}}));
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
          {% if isinstance(rule.operator, PrefixOperator) %}
            tree.add(parse_{{name}}_internal(ctx, get_prefix_binding_power_{{name}}({{rule.operator.operator.id}})));
            tree.setPrefix(true);
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

    private static ParseTree led_{{name}}(ParseTree left, ParserContext ctx) throws SyntaxError {
        ParseTree tree = new ParseTree( new NonTerminal({{expression_nonterminal.id}}, "{{name}}") );
        Terminal current = ctx.tokens.current();
        int modifier;

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) %}

        if (current.getId() == {{led[0].id}}) {
            /* {{rule}} */
            ctx.nonterminal = "{{name}}";
            ctx.rule = rules.get({{rule.id}});

      {% if isinstance(rule.ast, AstSpecification) %}
            LinkedHashMap<String, Integer> parameters = new LinkedHashMap<String, Integer>();
        {% for key, value in rule.ast.parameters.items() %}
            parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
        {% endfor %}
            tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
      {% elif isinstance(rule.ast, AstTranslation) %}
            tree.setAstTransformation(new AstTransformSubstitution({{rule.ast.idx}}));
      {% endif %}

      {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
        {% py nt = rule.nud_production.morphemes[0] %}
        {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
            tree.setExprNud(true);
        {% endif %}
      {% endif %}

            tree.add(left);

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
      {% for morpheme in led %}
        {% if isinstance(morpheme, Terminal) %}
            tree.add(expect(ctx, {{prefix}}TerminalIdentifier.TERMINAL_{{morpheme.string.upper()}}));
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
        {% if isinstance(rule.operator, InfixOperator) %}
            tree.setInfix(true);
        {% endif %}
            tree.add(parse_{{name}}_internal(ctx, get_infix_binding_power_{{name}}({{rule.operator.operator.id}}) - modifier));
        {% elif isinstance(morpheme, NonTerminal) %}
            tree.add(parse_{{morpheme.string.lower()}}(ctx));
        {% endif %}
      {% endfor %}
            return tree;
        }
        {% endif %}
      {% endfor %}

        return tree;
    }
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
    private static ParseTree parse_{{nonterminal.string.lower()}}(ParserContext ctx) throws SyntaxError {
        Terminal current = ctx.tokens.current();
        Terminal next;
        ParseTree subtree;
        int rule = (current != null) ? table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.getId()] : -1;
        ParseTree tree = new ParseTree( new NonTerminal({{nonterminal.id}}, "{{nonterminal.string}}"));

  {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
        tree.setList("slist");
  {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
        tree.setList("nlist");
  {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
        tree.setList("tlist");
  {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
        tree.setList("mlist");
  {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
        tree.setList("otlist");
  {% else %}
        tree.setList(null);
  {% endif %}

  {% if not grammar.must_consume_tokens(nonterminal) %}
        if ( current != null &&
             !nonterminal_first.get({{nonterminal.id}}).contains(terminal_map.get(current.getId())) &&
              nonterminal_follow.get({{nonterminal.id}}).contains(terminal_map.get(current.getId())) ) {
            return tree;
        }
  {% endif %}

        if (current == null) {
  {% if grammar.must_consume_tokens(nonterminal) %}
            throw new SyntaxError(ctx.error_formatter.unexpected_eof(
                "{{nonterminal.string.lower()}}",
                nonterminal_first.get({{nonterminal.id}}),
                nonterminal_rules.get({{nonterminal.id}})
            ));
  {% else %}
            return tree;
  {% endif %}
        }

  {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}
    {% if index == 0 %}
        if (rule == {{rule.id}}) {
    {% else %}
        else if (rule == {{rule.id}}) {
    {% endif %}
            /* {{rule}} */
            ctx.nonterminal = "{{nonterminal.string.lower()}}";
            ctx.rule = rules.get({{rule.id}});

    {% if isinstance(rule.ast, AstTranslation) %}
            tree.setAstTransformation(new AstTransformSubstitution({{rule.ast.idx}}));
    {% elif isinstance(rule.ast, AstSpecification) %}
            LinkedHashMap<String, Integer> parameters = new LinkedHashMap<String, Integer>();
      {% for key, value in rule.ast.parameters.items() %}
            parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
      {% endfor %}
            tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
    {% else %}
            tree.setAstTransformation(new AstTransformSubstitution(0));
    {% endif %}

    {% for index, morpheme in enumerate(rule.production.morphemes) %}
      {% if isinstance(morpheme, Terminal) %}
            next = expect(ctx, {{prefix}}TerminalIdentifier.TERMINAL_{{morpheme.string.upper()}});
            tree.add(next);
        {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
          {% if nonterminal.macro.separator == morpheme %}
            tree.setListSeparator(next);
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
        throw new SyntaxError(ctx.error_formatter.unexpected_symbol(
            "{{nonterminal.string.lower()}}",
            current,
            nonterminal_first.get({{nonterminal.id}}),
            rules.get({{rule.id}})
        ));
  {% else %}
        return tree;
  {% endif %}
    }
{% endfor %}
}
