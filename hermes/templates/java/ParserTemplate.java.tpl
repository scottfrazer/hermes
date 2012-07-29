{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

import java.util.*;

class {{prefix}}Parser implements Parser {

  private TokenStream tokens;
  private HashMap<String, ExpressionParser> expressionParsers;

  /* table[nonterminal][terminal] = rule */
  private static final int[][] table = {
    {% py parseTable = grammar.getParseTable() %}
    {% for i in range(len(grammar.nonterminals)) %}
    { {{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}} },
    {% endfor %}
  };

  public enum TerminalId {
  {% for index, terminal in enumerate(nonAbstractTerminals) %}
    TERMINAL_{{terminal.string.upper()}}({{terminal.id}}, "{{terminal.string}}"){{',' if index!=len(nonAbstractTerminals)-1 else ';'}}
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

    {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}() {
      this.infixBp = new HashMap<Integer, Integer>();
      this.prefixBp = new HashMap<Integer, Integer>();

      {% for terminal_id, binding_power in exprGrammar.infix.items() %}
      this.infixBp.put({{terminal_id}}, {{binding_power}});
      {% endfor %}

      {% for terminal_id, binding_power in exprGrammar.prefix.items() %}
      this.prefixBp.put({{terminal_id}}, {{binding_power}});
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

      {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
        {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

        {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

        {% if len(ruleFirstSet) and not isOptional %}
      {{'if' if i == 0 else 'else if'}} ( {{' || '.join(['current.getId() == ' + str(x.id) for x in exprGrammar.ruleFirst(rule)])}} ) {

          {% if isinstance(rule.ast, AstSpecification) %}
        Map<String, Integer> parameters = new HashMap<String, Integer>();
            {% for key, value in rule.ast.parameters.items() %}
        parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
            {% endfor %}
        tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
          {% elif isinstance(rule.ast, AstTranslation) %}
        tree.setAstTransformation(new AstTransformSubstitution({{rule.ast.idx}}));
          {% endif %}

        tree.setNudMorphemeCount({{len(rule.nudProduction)}});

          {% for morpheme in rule.nudProduction.morphemes %}
            {% if isinstance(morpheme, Terminal) %}
        tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}.id()) );
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
      {% for rule in exprGrammar.getExpandedExpressionRules() %}
        {% py led = rule.ledProduction.morphemes %}
        {% if len(led) and led[0] not in seen %}

      {{'if' if len(seen)==0 else 'else if'}} (current.getId() == {{led[0].id}}) { 
        // {{led[0]}}

          {% if isinstance(rule.ast, AstSpecification) %}
        Map<String, Integer> parameters = new HashMap<String, Integer>();
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

          {% for morpheme in led %}
            {% if isinstance(morpheme, Terminal) %}
        tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}.id()) );
            {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in exprGrammar.precedence and exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}};
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

  {{prefix}}Parser() {
    this.expressionParsers = new HashMap<String, ExpressionParser>();
  }

  public TerminalMap getTerminalMap() {
    return new {{prefix}}TerminalMap(TerminalId.values());
  }

  public ParseTree parse(TokenStream tokens) throws SyntaxError {
    this.tokens = tokens;
    ParseTree tree = this.parse_{{str(grammar.start).lower()}}();
    if (this.tokens.current() != null) {
      throw new SyntaxError("Finished parsing without consuming all tokens\nCurrent token is " + this.tokens.current());
    }
    return tree;
  }

  private boolean isTerminal(TerminalId terminal) {
    return (0 <= terminal.id() && terminal.id() <= {{len(nonAbstractTerminals) - 1}});
  }

  private boolean isNonTerminal(TerminalId terminal) {
    return ({{len(nonAbstractTerminals)}} <= terminal.id() && terminal.id() <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}});
  }

  private boolean isTerminal(int terminal) {
    return (0 <= terminal && terminal <= {{len(nonAbstractTerminals) - 1}});
  }

  private boolean isNonTerminal(int terminal) {
    return ({{len(nonAbstractTerminals)}} <= terminal && terminal <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}});
  }
 
  {% for nonterminal in LL1Nonterminals %}

  private ParseTree parse_{{nonterminal.string.lower()}}() throws SyntaxError {
    Terminal current = this.tokens.current();
    Terminal next;
    ParseTree subtree;
    int rule = current != null ? this.table[{{nonterminal.id - len(nonAbstractTerminals)}}][current.getId()] : -1;
    ParseTree tree = new ParseTree( new NonTerminal({{nonterminal.id}}, "{{nonterminal.string}}"));

      {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.setList("slist");
      {% elif isinstance(nonterminal.macro, NonterminalListMacro) %}
    tree.setList("nlist");
      {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.setList("tlist");
      {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.setList("mlist");
      {% else %}
    tree.setList(null);
      {% endif %}

      {% if nonterminal.empty %}
    if ( current != null ) {
      {% if len(grammar.follow[nonterminal]) %}
      if ({{' || '.join(['current.getId() == ' + str(a.id) for a in grammar.follow[nonterminal]])}}) {
        return tree;
      }
      {% endif %}
    }
      {% endif %}

    if (current == null) {
      {% if nonterminal.empty or grammar._empty in grammar.first[nonterminal] %}
      return tree;
      {% else %}
      throw new SyntaxError("Error: unexpected end of file");
      {% endif %}
    }
    
      {% for index, rule in enumerate(nonterminal.rules) %}

        {% if index == 0 %}
    if (rule == {{rule.id}}) {
        {% else %}
    else if (rule == {{rule.id}}) {
        {% endif %}

        {% if isinstance(rule.ast, AstTranslation) %}
      tree.setAstTransformation(new AstTransformSubstitution({{rule.ast.idx}}));
        {% elif isinstance(rule.ast, AstSpecification) %}
      Map<String, Integer> parameters = new HashMap<String, Integer>();
          {% for key, value in rule.ast.parameters.items() %}
      parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
          {% endfor %}
      tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
        {% else %}
      tree.setAstTransformation(new AstTransformSubstitution(0));
        {% endif %}

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
      next = this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}.id());
      tree.add(next);
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
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
      Map<String, Integer> parameters = new HashMap<String, Integer>();
            {% for key, value in rule.ast.parameters.items() %}
      parameters.put("{{key}}", {{"(int) '$'" if value == '$' else value}});
            {% endfor %}
      tree.setAstTransformation(new AstTransformNodeCreator("{{rule.ast.name}}", parameters));
          {% else %}
      tree.setAstTransformation(new AstTransformSubstitution(0));
          {% endif %}

          {% for morpheme in rule.production.morphemes %}

            {% if isinstance(morpheme, Terminal) %}
      tree.add( this.tokens.expect(TerminalId.TERMINAL_{{morpheme.string.upper()}}.id()) );
            {% endif %}

            {% if isinstance(morpheme, NonTerminal) %}
      subtree = this.parse_{{morpheme.string.lower()}}();
      tree.add(subtree);
            {% endif %}
          {% endfor %}
    }
        {% endif %}
      {% endfor %}

      {% if not nonterminal.empty %}
    Formatter formatter = new Formatter(new StringBuilder(), Locale.US);
    StackTraceElement[] stack = Thread.currentThread().getStackTrace();
    formatter.format("Error: Unexpected symbol (%s) when parsing %s", current, stack[0].getMethodName());
    throw new SyntaxError(formatter.toString());
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
      this.expressionParsers.put(name, new {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}());
    }
    return this.expressionParsers.get(name).parse(this.tokens, rbp);
  }
  {% endfor %}
}

