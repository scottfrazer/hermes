{% if java_package %}
package {{java_package}};
{% endif %}

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

import java.util.*;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Arrays;

public class {{prefix}}Parser implements Parser {

  private TokenStream tokens;
  private HashMap<String, ExpressionParser> expressionParsers;
  private SyntaxErrorFormatter syntaxErrorFormatter;
  private Map<String, TerminalIdentifier[]> first;
  private Map<String, TerminalIdentifier[]> follow;
  private Map<String, List<String>> nonterminal_rules;
  private Map<Integer, String> rules;

  /* table[nonterminal][terminal] = rule */
  private static final int[][] table = {
    {% py parse_table = grammar.parse_table %}
    {% for i in range(len(grammar.nonterminals)) %}
    { {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} },
    {% endfor %}
  };

  public enum TerminalId implements TerminalIdentifier {
  {% for index, terminal in enumerate(grammar.standard_terminals) %}
    TERMINAL_{{terminal.string.upper()}}({{terminal.id}}, "{{terminal.string}}"){{',' if index!=len(grammar.standard_terminals)-1 else ';'}}
  {% endfor %}

    private final int id;
    private final String string;

    TerminalId(int id, String string) {
      this.id = id;
      this.string = string;
    }

    public int id() {return id;}
    public String string() {return string;}
  }

  private class {{prefix}}TerminalMap implements TerminalMap {
    private Map<Integer, String> id_to_str;
    private Map<String, Integer> str_to_id;

    {{prefix}}TerminalMap(TerminalId[] terminals) {
      id_to_str = new HashMap<Integer, String>();
      str_to_id = new HashMap<String, Integer>();
      for( TerminalId terminal : terminals ) {
        Integer id = new Integer(terminal.id());
        String str = terminal.string();
        id_to_str.put(id, str);
        str_to_id.put(str, id);
      }
    }

    public int get(String string) { return this.str_to_id.get(string); }
    public String get(int id) { return this.id_to_str.get(id); }
    public boolean isValid(String string) { return this.str_to_id.containsKey(string); }
    public boolean isValid(int id) { return this.id_to_str.containsKey(id); }
  }

  {% for exprGrammar in grammar.exprgrammars %}
  private class {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}} implements ExpressionParser {

    private HashMap<Integer, Integer> infixBp, prefixBp;
    private TokenStream tokens;
    private SyntaxErrorFormatter syntaxErrorFormatter;
    private Map<String, List<String>> nonterminal_rules;
    private Map<Integer, String> rules;

    {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}(
        SyntaxErrorFormatter syntaxErrorFormatter,
        Map<String, List<String>> nonterminal_rules,
        Map<Integer, String> rules
    ) {
      this.syntaxErrorFormatter = syntaxErrorFormatter;
      this.rules = rules;
      this.nonterminal_rules = nonterminal_rules;
      this.infixBp = new HashMap<Integer, Integer>();
      this.prefixBp = new HashMap<Integer, Integer>();

      {% for rule in exprGrammar.rules %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
      this.infixBp.put({{rule.operator.operator.id}}, {{rule.operator.binding_power}});
        {% endif %}
      {% endfor %}

      {% for rule in exprGrammar.rules %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
      this.prefixBp.put({{rule.operator.operator.id}}, {{rule.operator.binding_power}});
        {% endif %}
      {% endfor %}
    }

    private int getInfixBp(int terminal) {
      try {
        return this.infixBp.get(new Integer(terminal)).intValue();
      } catch (Exception e) {
        return 0;
      }
    }

    private int getPrefixBp(int terminal) {
      try {
        return this.prefixBp.get(new Integer(terminal)).intValue();
      } catch (Exception e) {
        return 0;
      }
    }

    public ParseTree parse(TokenStream tokens) throws SyntaxError {
      return this.parse(tokens, 0);
    }

    public ParseTree parse(TokenStream tokens, int rbp) throws SyntaxError {
      this.tokens = tokens;
      this.tokens.setSyntaxErrorFormatter(this.syntaxErrorFormatter);
      this.tokens.setTerminalMap(this.getTerminalMap());
      ParseTree left = this.nud();

      if ( left instanceof ParseTree ) {
        left.setExpr(true);
        left.setNud(true);
      }

      while (this.tokens.current() != null && rbp < getInfixBp(this.tokens.current().getId())) {
        left = this.led(left);
      }

      if (left != null) {
        left.setExpr(true);
      }

      return left;
    }

    public TerminalMap getTerminalMap() {
      return new {{prefix}}TerminalMap(TerminalId.values());
    }

    private ParseTree nud() throws SyntaxError {
      ParseTree tree = new ParseTree( new NonTerminal({{exprGrammar.nonterminal.id}}, "{{exprGrammar.nonterminal.string.lower()}}") );
      Terminal current = this.tokens.current();

      if (current == null) {
        return tree;
      }

      {% for i, rule in enumerate(grammar.grammar_expanded_rules[exprGrammar]) %}
        {% py ruleFirstSet = grammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

        {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first[exprGrammar.nonterminal])%}
      {{'if' if i == 0 else 'else if'}} ( {{' || '.join(['current.getId() == ' + str(x.id) for x in ruleFirstSet])}} ) {

          {% py ast = rule.nudAst if rule.nudAst else rule.ast %}
        /* ({{rule.id}}) {{rule}} */
          {% if isinstance(ast, AstSpecification) %}
        LinkedHashMap<String, Integer> parameters = new LinkedHashMap<String, Integer>();
            {% for key, value in ast.parameters.items() %}
        parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
            {% endfor %}
        tree.setAstTransformation(new AstTransformNodeCreator("{{ast.name}}", parameters));
          {% elif isinstance(ast, AstTranslation) %}
        tree.setAstTransformation(new AstTransformSubstitution({{ast.idx}}));
          {% endif %}

        tree.setNudMorphemeCount({{len(rule.nudProduction)}});

          {% for morpheme in rule.nudProduction.morphemes %}
            {% if isinstance(morpheme, Terminal) %}
        tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}, "{{exprGrammar.nonterminal.string.lower()}}", this.rules.get({{rule.id}})));
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
              {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add( parse_{{rule.nonterminal.string.lower()}}( this.getPrefixBp({{rule.operator.operator.id}}) ) );
        tree.setPrefix(true);
              {% else %}
        tree.add( parse_{{rule.nonterminal.string.lower()}}() );
              {% endif %}
            {% elif isinstance(morpheme, NonTerminal) %}
        tree.add( parse_{{morpheme.string.lower()}}() );
            {% elif isinstance(morpheme, LL1ListMacro) %}
        tree.add( parse_{{morpheme.start_nt.string.lower()}}() );
            {% endif %}
          {% endfor %}
      }
        {% endif %}
      {% endfor %}

      return tree;
    }

    private ParseTree led(ParseTree left) throws SyntaxError {
      ParseTree tree = new ParseTree( new NonTerminal({{exprGrammar.nonterminal.id}}, "{{exprGrammar.nonterminal.string.lower()}}") );
      Terminal current = this.tokens.current();
      int modifier;

      {% py seen = list() %}
      {% for rule in grammar.grammar_expanded_expr_rules[exprGrammar] %}
        {% py led = rule.ledProduction.morphemes %}
        {% if len(led) and led[0] not in seen %}

      {{'if' if len(seen)==0 else 'else if'}} (current.getId() == {{led[0].id}}) { 
        // {{led[0]}}

          {% if isinstance(rule.ast, AstSpecification) %}
        LinkedHashMap<String, Integer> parameters = new LinkedHashMap<String, Integer>();
            {% for key, value in rule.ast.parameters.items() %}
        parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
            {% endfor %}
        tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
          {% elif isinstance(rule.ast, AstTranslation) %}
        tree.setAstTransformation(new AstTransformSubstitution({{rule.ast.idx}}));
          {% endif %}

          {% if len(rule.nudProduction) == 1 and isinstance(rule.nudProduction.morphemes[0], NonTerminal) %}
            {% py nt = rule.nudProduction.morphemes[0] %}
            {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
        tree.setExprNud(true);
            {% endif %}
          {% endif %}

        tree.add(left);

          {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in exprGrammar.rules if rule.operator} %}
          {% for morpheme in led %}
            {% if isinstance(morpheme, Terminal) %}
        tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}, "{{exprGrammar.nonterminal.string.lower()}}", this.rules.get({{rule.id}})) );
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
              {% if isinstance(rule.operator, InfixOperator) %}
        tree.setInfix(true);
              {% endif %}
        tree.add( parse_{{rule.nonterminal.string.lower()}}( this.getInfixBp({{rule.operator.operator.id}}) - modifier ) );
            {% elif isinstance(morpheme, NonTerminal) %}
        tree.add( parse_{{morpheme.string.lower()}}() );
            {% elif isinstance(morpheme, LL1ListMacro) %}
        tree.add( parse_{{morpheme.start_nt.string.lower()}}() );
            {% endif %}
          {% endfor %}
        return tree;
      }
        {% endif %}
      {% endfor %}

      return tree;
    }
  }
  {% endfor %}

  public {{prefix}}Parser(SyntaxErrorFormatter syntaxErrorFormatter) {
    this.syntaxErrorFormatter = syntaxErrorFormatter; 
    this.expressionParsers = new HashMap<String, ExpressionParser>();
    this.first = new HashMap<String, TerminalIdentifier[]>();
    this.follow = new HashMap<String, TerminalIdentifier[]>();
    this.nonterminal_rules = new HashMap<String, List<String>>();
    this.rules = new HashMap<Integer, String>();

    ArrayList<TerminalId> list;
    String rule;
    
    {% for nonterminal in grammar.nonterminals %}
    this.nonterminal_rules.put("{{nonterminal.string.lower()}}", new ArrayList<String>());
    {% endfor %}

    {% for rule in grammar.getExpandedRules() %}
    rule = "{{rule}}";
    this.nonterminal_rules.get("{{rule.nonterminal.string.lower()}}").add(rule);
    this.rules.put(new Integer({{rule.id}}), rule);
    {% endfor %}

    {% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
      {% py xTerminals = set(grammar.first[nonterminal]) %}
      {% py xTerminals = xTerminals.intersection(grammar.standard_terminals) %}
      {% py xTerminals = set("TerminalId.TERMINAL_" + t.string.upper() for t in xTerminals) %}
    this.first.put("{{nonterminal.string.lower()}}", new TerminalId[] { {{', '.join([t for t in xTerminals])}} });
    {% endfor %}

    {% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
      {% py xTerminals = set(grammar.follow[nonterminal]) %}
      {% py xTerminals = xTerminals.intersection(grammar.standard_terminals) %}
      {% py xTerminals = set("TerminalId.TERMINAL_" + t.string.upper() for t in xTerminals) %}
    this.follow.put("{{nonterminal.string.lower()}}", new TerminalId[] { {{', '.join([t for t in xTerminals])}} });
    {% endfor %}
  }

  public TerminalMap getTerminalMap() {
    return new {{prefix}}TerminalMap(TerminalId.values());
  }

  public ParseTree parse(TokenStream tokens) throws SyntaxError {
    this.tokens = tokens;
    this.tokens.setSyntaxErrorFormatter(this.syntaxErrorFormatter);
    this.tokens.setTerminalMap(this.getTerminalMap());

    ParseTree tree = this.parse_{{grammar.start.string.lower()}}();
    if (this.tokens.current() != null) {
      StackTraceElement[] stack = Thread.currentThread().getStackTrace();
      throw new SyntaxError(this.syntaxErrorFormatter.excess_tokens(stack[1].getMethodName(), this.tokens.current()));
    }
    return tree;
  }

  private boolean isTerminal(TerminalId terminal) {
    return (0 <= terminal.id() && terminal.id() <= {{len(grammar.standard_terminals) - 1}});
  }

  private boolean isNonTerminal(TerminalId terminal) {
    return ({{len(grammar.standard_terminals)}} <= terminal.id() && terminal.id() <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}});
  }

  private boolean isTerminal(int terminal) {
    return (0 <= terminal && terminal <= {{len(grammar.standard_terminals) - 1}});
  }

  private boolean isNonTerminal(int terminal) {
    return ({{len(grammar.standard_terminals)}} <= terminal && terminal <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}});
  }
 
  {% for nonterminal in grammar.ll1_nonterminals %}

  private ParseTree parse_{{nonterminal.string.lower()}}() throws SyntaxError {
    Terminal current = this.tokens.current();
    Terminal next;
    ParseTree subtree;
    int rule = current != null ? this.table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.getId()] : -1;
    ParseTree tree = new ParseTree( new NonTerminal({{nonterminal.id}}, "{{nonterminal.string}}"));

      {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.setList("slist");
      {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
    tree.setList("nlist");
      {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.setList("tlist");
      {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.setList("mlist");
      {% else %}
    tree.setList(null);
      {% endif %}

      {% if grammar.must_consume_tokens(nonterminal) %}
    if ( current != null ) {
      {% if len(grammar.follow[nonterminal]) %}
      if ( ({{' || '.join(['current.getId() == ' + str(a.id) for a in grammar.follow[nonterminal]])}}) && 
           ({{' && '.join(['current.getId() != ' + str(a.id) for a in grammar.first[nonterminal]])}}) ) {
        return tree;
      }
      {% endif %}
    }
      {% endif %}

    if (current == null) {
      {% if grammar.must_consume_tokens(nonterminal) or grammar._empty in grammar.first[nonterminal] %}
      return tree;
      {% else %}

      throw new SyntaxError(this.syntaxErrorFormatter.unexpected_eof(
        "{{nonterminal.string.lower()}}",
        Arrays.asList(this.first.get("{{nonterminal.string.lower()}}")),
        this.nonterminal_rules.get("{{nonterminal.string.lower()}}")
      ));

      {% endif %}
    }
    
      {% for index, rule in enumerate(filter(lambda r: not r.must_consume_tokens, grammar.getExpandedLL1Rules(nonterminal))) %}

        {% if index == 0 %}
    if (rule == {{rule.id}}) {
        {% else %}
    else if (rule == {{rule.id}}) {
        {% endif %}

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
      next = this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}, "{{nonterminal.string.lower()}}", this.rules.get({{rule.id}}));
      tree.add(next);
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and nonterminal.macro.separator == morpheme %}
      tree.setListSeparator(next);
            {% endif %}
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
      subtree = this.parse_{{morpheme.string.lower()}}();
      tree.add( subtree);
          {% endif %}

        {% endfor %}

      return tree;
    }
      {% endfor %}

      {% for exprGrammar in grammar.exprgrammars %}
        {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
          {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}
    else if ( {{' || '.join(['current.getId() == ' + str(a.id) for a in grammar.first[exprGrammar.nonterminal]])}} ) {
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

          {% for morpheme in rule.production.morphemes %}

            {% if isinstance(morpheme, Terminal) %}
      tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}, "{{nonterminal.string.lower()}}", this.rules.get({{rule.id}})) );
            {% endif %}

            {% if isinstance(morpheme, NonTerminal) %}
      subtree = this.parse_{{morpheme.string.lower()}}();
      tree.add(subtree);
            {% endif %}
          {% endfor %}
    }
        {% endif %}
      {% endfor %}

      {% if not grammar.must_consume_tokens(nonterminal) %}

    List<TerminalIdentifier> terminals = Arrays.asList(this.first.get("{{nonterminal.string.lower()}}"));
    throw new SyntaxError(this.syntaxErrorFormatter.unexpected_symbol(
      "{{nonterminal.string.lower()}}",
      current, 
      Arrays.asList(this.first.get("{{nonterminal.string.lower()}}")),
      this.rules.get({{rule.id}})
    ));
      {% else %}
    return tree;
      {% endif %}
  }
  {% endfor %}

  {% for exprGrammar in grammar.exprgrammars %}
  public ParseTree parse_{{exprGrammar.nonterminal.string.lower()}}() throws SyntaxError {
    return parse_{{exprGrammar.nonterminal.string.lower()}}(0);
  }

  public ParseTree parse_{{exprGrammar.nonterminal.string.lower()}}(int rbp) throws SyntaxError {
    String name = "{{exprGrammar.nonterminal.string.lower()}}";
    if ( !this.expressionParsers.containsKey(name) ) {
      this.expressionParsers.put(name, new {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}(
        this.syntaxErrorFormatter,
        this.nonterminal_rules,
        this.rules
      ));
    }
    return this.expressionParsers.get(name).parse(this.tokens, rbp);
  }
  {% endfor %}
}

