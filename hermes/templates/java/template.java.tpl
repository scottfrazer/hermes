{% if len(header)%}
/*
{{'\n'.join([' * ' + s for s in header.split('\n')])}}
 */
{% endif %}

{% if java_package %}
package {{java_package}};
{% endif %}

{% import re %}
{% from hermes.grammar import * %}

import java.util.*;
import java.io.IOException;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.Arrays;
import java.nio.*;
import java.nio.channels.FileChannel;
import java.nio.charset.Charset;

{% if java_use_apache_commons %}
import org.apache.commons.codec.binary.Base64;
{% endif %}

{% if java_imports %}
  {% for java_import in java_imports%}
import {{java_import}};
  {% endfor %}
{% endif %}

{% if lexer %}
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.lang.reflect.Method;
{% endif %}

{% if add_main %}
import java.lang.reflect.Field;
import java.lang.reflect.Array;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.StringReader;
{% endif %}

public class {{prefix}}Parser {

    private static Map<Integer, List<TerminalIdentifier>> nonterminal_first;
    private static Map<Integer, List<TerminalIdentifier>> nonterminal_follow;
    private static Map<Integer, List<TerminalIdentifier>> rule_first;
    private static Map<Integer, List<String>> nonterminal_rules;
    private static Map<Integer, String> rules;
    public static {{prefix}}TerminalMap terminal_map = new {{prefix}}TerminalMap({{prefix}}TerminalIdentifier.values());

    public {{prefix}}Parser() {
        try {
            lexer_init();
        } catch(Exception e) {}
    }

    public static String join(Collection<?> s, String delimiter) {
        StringBuilder builder = new StringBuilder();
        Iterator iter = s.iterator();
        while (iter.hasNext()) {
            builder.append(iter.next());
            if (!iter.hasNext()) {
                break;
            }
            builder.append(delimiter);
        }
        return builder.toString();
    }

    public static String getIndentString(int spaces) {
        StringBuilder sb = new StringBuilder();
        for(int i = 0; i < spaces; i++) {
            sb.append(' ');
        }
        return sb.toString();
    }

    public static String readStdin() throws IOException {
        InputStreamReader stream = new InputStreamReader(System.in, "utf-8");
        char buffer[] = new char[System.in.available()];
        try {
            stream.read(buffer, 0, System.in.available());
        } finally {
            stream.close();
        }
        return new String(buffer);
    }

    public static String readFile(String path) throws IOException {
        FileInputStream stream = new FileInputStream(new File(path));
        try {
            FileChannel fc = stream.getChannel();
            MappedByteBuffer bb = fc.map(FileChannel.MapMode.READ_ONLY, 0, fc.size());
            /* Instead of using default, pass in a decoder. */
            return Charset.defaultCharset().decode(bb).toString();
        }
        finally {
            stream.close();
        }
    }

    public static class SyntaxError extends Exception {
        public SyntaxError(String message) {
            super(message);
        }
    }

    public interface SyntaxErrorFormatter {
        /* Called when the parser runs out of tokens but isn't finished parsing. */
        String unexpectedEof(String method, List<TerminalIdentifier> expected, List<String> nt_rules);

        /* Called when the parser finished parsing but there are still tokens left in the stream. */
        String excessTokens(String method, Terminal terminal);

        /* Called when the parser is expecting one token and gets another. */
        String unexpectedSymbol(String method, Terminal actual, List<TerminalIdentifier> expected, String rule);

        /* Called when the parser is expecing a tokens but there are no more tokens. */
        String noMoreTokens(String method, TerminalIdentifier expecting, Terminal last);

        /* Invalid terminal is found in the token stream. */
        String invalidTerminal(String method, Terminal invalid);
    }

    public static class TokenStream extends ArrayList<Terminal> {
        private int index;

        public TokenStream(List<Terminal> terminals) {
            super(terminals);
            reset();
        }

        public TokenStream() {
            reset();
        }

        public void reset() {
            this.index = 0;
        }

        public Terminal advance() {
            this.index += 1;
            return this.current();
        }

        public Terminal current() {
            try {
                return this.get(this.index);
            } catch (IndexOutOfBoundsException e) {
                return null;
            }
        }

        public Terminal last() {
          return this.get(this.size() - 1);
        }
    }

    public static class NonTerminal {
        private int id;
        private String string;

        NonTerminal(int id, String string) {
            this.id = id;
            this.string = string;
        }

        public int getId() {
            return this.id;
        }

        public String getString() {
            return this.string;
        }

        public String toString() {
            return this.string;
        }
    }

    public interface AstTransform {}

    public static class AstTransformNodeCreator implements AstTransform {
        private String name;
        private LinkedHashMap<String, Integer> parameters;

        AstTransformNodeCreator(String name, LinkedHashMap<String, Integer> parameters) {
            this.name = name;
            this.parameters = parameters;
        }

        public Map<String, Integer> getParameters() {
            return this.parameters;
        }

        public String getName() {
            return this.name;
        }

        public String toString() {
            LinkedList<String> items = new LinkedList<String>();
            for (final Map.Entry<String, Integer> entry : this.parameters.entrySet()) {
                items.add(entry.getKey() + "=$" + entry.getValue().toString());
            }
            return "AstNodeCreator: " + this.name + "( " + join(items, ", ") + " )";
        }
    }

    public static class AstTransformSubstitution implements AstTransform {
        private int index;

        AstTransformSubstitution(int index) {
            this.index = index;
        }

        public int getIndex() {
            return this.index;
        }

        public String toString() {
            return "AstSubstitution: $" + Integer.toString(this.index);
        }
    }

    public interface AstNode {
        public String toString();
        public String toPrettyString();
        public String toPrettyString(int indent);
    }

    public static class AstList extends ArrayList<AstNode> implements AstNode {
        public String toString() {
            return "[" + join(this, ", ") + "]";
        }

        public String toPrettyString() {
            return toPrettyString(0);
        }

        public String toPrettyString(int indent) {
            String spaces = getIndentString(indent);
            if (this.size() == 0) {
                return spaces + "[]";
            }

            ArrayList<String> elements = new ArrayList<String>();
            for ( AstNode node : this ) {
                elements.add(node.toPrettyString(indent + 2));
            }

            return spaces + "[\n" + join(elements, ",\n") + "\n" + spaces + "]";
        }
    }

    public static class Ast implements AstNode {
        private String name;
        private Map<String, AstNode> attributes;

        Ast(String name, Map<String, AstNode> attributes) {
            this.name = name;
            this.attributes = attributes;
        }

        public AstNode getAttribute(String name) {
            return this.attributes.get(name);
        }

        public Map<String, AstNode> getAttributes() {
            return this.attributes;
        }

        public String getName() {
            return this.name;
        }

        public String toString() {
            Formatter formatter = new Formatter(new StringBuilder(), Locale.US);

            LinkedList<String> attributes = new LinkedList<String>();
            for (final Map.Entry<String, AstNode> attribute : this.attributes.entrySet()) {
                final String name = attribute.getKey();
                final AstNode node = attribute.getValue();
                final String nodeStr = (node == null) ? "None" : node.toString();
                attributes.add(name + "=" + nodeStr);
            }

            formatter.format("(%s: %s)", this.name, join(attributes, ", "));
            return formatter.toString();
        }

        public String toPrettyString() {
            return toPrettyString(0);
        }

        public String toPrettyString(int indent) {
            String spaces = getIndentString(indent);

            ArrayList<String> children = new ArrayList<String>();
            for( Map.Entry<String, AstNode> attribute : this.attributes.entrySet() ) {
                String valueString = attribute.getValue() == null ? "None" : attribute.getValue().toPrettyString(indent + 2).trim();
                children.add(spaces + "  " + attribute.getKey() + "=" + valueString);
            }

            return spaces + "(" + this.name + ":\n" + join(children, ",\n") + "\n" + spaces + ")";
        }
    }

    public interface ParseTreeNode {
        public AstNode toAst();
        public String toString();
        public String toPrettyString();
        public String toPrettyString(int indent);
    }

    public static class Terminal implements AstNode, ParseTreeNode
    {
        private int id;
        private String terminal_str;
        private String source_string;
        private String resource;
        private int line;
        private int col;

        public Terminal(int id, String terminal_str, String source_string, String resource, int line, int col) {
            this.id = id;
            this.terminal_str = terminal_str;
            this.source_string = source_string;
            this.resource = resource;
            this.line = line;
            this.col = col;
        }

        public int getId() {
            return this.id;
        }

        public String getTerminalStr() {
            return this.terminal_str;
        }

        public String getSourceString() {
            return this.source_string;
        }

        public String getResource() {
            return this.resource;
        }

        public int getLine() {
            return this.line;
        }

        public int getColumn() {
            return this.col;
        }

        public String toString() {
            byte[] source_string_bytes;
            try {
                source_string_bytes = this.getSourceString().getBytes("UTF-8");
            } catch (java.io.UnsupportedEncodingException e) {
                source_string_bytes = this.getSourceString().getBytes();
            }
            return String.format("<%s:%d:%d %s \"%s\">",
                this.getResource(),
                this.getLine(),
                this.getColumn(),
                this.getTerminalStr(),
                {% if java_use_apache_commons %}
                Base64.encodeBase64String(source_string_bytes)
                {% else %}
                Base64.getEncoder().encodeToString(source_string_bytes)
                {% endif %}
            );
        }

        public String toPrettyString() {
            return toPrettyString(0);
        }

        public String toPrettyString(int indent) {
            return getIndentString(indent) + this.toString();
        }

        public AstNode toAst() { return this; }
    }

    public static class ParseTree implements ParseTreeNode {
        private NonTerminal nonterminal;
        private ArrayList<ParseTreeNode> children;

        private boolean isExpr, isNud, isPrefix, isInfix, isExprNud;
        private int nudMorphemeCount;
        private Terminal listSeparator;
        private boolean list;
        private AstTransform astTransform;

        ParseTree(NonTerminal nonterminal) {
            this.nonterminal = nonterminal;
            this.children = new ArrayList<ParseTreeNode>();
            this.astTransform = null;
            this.isExpr = false;
            this.isNud = false;
            this.isPrefix = false;
            this.isInfix = false;
            this.isExprNud = false;
            this.nudMorphemeCount = 0;
            this.listSeparator = null;
            this.list = false;
        }

        public void setExpr(boolean value) { this.isExpr = value; }
        public void setNud(boolean value) { this.isNud = value; }
        public void setPrefix(boolean value) { this.isPrefix = value; }
        public void setInfix(boolean value) { this.isInfix = value; }
        public void setExprNud(boolean value) { this.isExprNud = value; }
        public void setAstTransformation(AstTransform value) { this.astTransform = value; }
        public void setNudMorphemeCount(int value) { this.nudMorphemeCount = value; }
        public void setList(boolean value) { this.list = value; }
        public void setListSeparator(Terminal value) { this.listSeparator = value; }

        public int getNudMorphemeCount() { return this.nudMorphemeCount; }
        public List<ParseTreeNode> getChildren() { return this.children; }
        public boolean isInfix() { return this.isInfix; }
        public boolean isPrefix() { return this.isPrefix; }
        public boolean isExpr() { return this.isExpr; }
        public boolean isNud() { return this.isNud; }
        public boolean isExprNud() { return this.isExprNud; }

        public void add(ParseTreeNode tree) {
            if (this.children == null) {
                this.children = new ArrayList<ParseTreeNode>();
            }
            this.children.add(tree);
        }

        private boolean isCompoundNud() {
            if ( this.children.size() > 0 && this.children.get(0) instanceof ParseTree ) {
                ParseTree child = (ParseTree) this.children.get(0);

                if ( child.isNud() && !child.isPrefix() && !this.isExprNud() && !this.isInfix() ) {
                    return true;
                }
            }
            return false;
        }

        public AstNode toAst() {
            if ( this.list == true ) {
                AstList astList = new AstList();
                int end = this.children.size() - 1;

                if ( this.children.size() == 0 ) {
                    return astList;
                }

                for (int i = 0; i < this.children.size() - 1; i++) {
                    if (this.children.get(i) instanceof Terminal && this.listSeparator != null && ((Terminal)this.children.get(i)).id == this.listSeparator.id)
                        continue;
                    astList.add(this.children.get(i).toAst());
                }

                astList.addAll((AstList) this.children.get(this.children.size() - 1).toAst());
                return astList;
            } else if ( this.isExpr ) {
                if ( this.astTransform instanceof AstTransformSubstitution ) {
                    AstTransformSubstitution astSubstitution = (AstTransformSubstitution) astTransform;
                    return this.children.get(astSubstitution.getIndex()).toAst();
                } else if ( this.astTransform instanceof AstTransformNodeCreator ) {
                    AstTransformNodeCreator astNodeCreator = (AstTransformNodeCreator) this.astTransform;
                    LinkedHashMap<String, AstNode> parameters = new LinkedHashMap<String, AstNode>();
                    ParseTreeNode child;
                    for ( final Map.Entry<String, Integer> parameter : astNodeCreator.getParameters().entrySet() ) {
                        String name = parameter.getKey();
                        int index = parameter.getValue().intValue();

                        if ( index == '$' ) {
                            child = this.children.get(0);
                        } else if ( this.isCompoundNud() ) {
                            ParseTree firstChild = (ParseTree) this.children.get(0);

                            if ( index < firstChild.getNudMorphemeCount() ) {
                                child = firstChild.getChildren().get(index);
                            } else {
                                index = index - firstChild.getNudMorphemeCount() + 1;
                                child = this.children.get(index);
                            }
                        } else if ( this.children.size() == 1 && !(this.children.get(0) instanceof ParseTree) && !(this.children.get(0) instanceof List) ) {
                            // TODO: I don't think this should ever be called
                            child = this.children.get(0);
                        } else {
                            child = this.children.get(index);
                        }
                        parameters.put(name, child.toAst());
                    }
                    return new Ast(astNodeCreator.getName(), parameters);
                }
            } else {
                AstTransformSubstitution defaultAction = new AstTransformSubstitution(0);
                AstTransform action = this.astTransform != null ? this.astTransform : defaultAction;

                if (this.children.size() == 0) return null;

                if (action instanceof AstTransformSubstitution) {
                    AstTransformSubstitution astSubstitution = (AstTransformSubstitution) action;
                    return this.children.get(astSubstitution.getIndex()).toAst();
                } else if (action instanceof AstTransformNodeCreator) {
                    AstTransformNodeCreator astNodeCreator = (AstTransformNodeCreator) action;
                    LinkedHashMap<String, AstNode> evaluatedParameters = new LinkedHashMap<String, AstNode>();
                    for ( Map.Entry<String, Integer> baseParameter : astNodeCreator.getParameters().entrySet() ) {
                        String name = baseParameter.getKey();
                        int index2 = baseParameter.getValue().intValue();
                        evaluatedParameters.put(name, this.children.get(index2).toAst());
                    }
                    return new Ast(astNodeCreator.getName(), evaluatedParameters);
                }
            }
            return null;
        }

        public String toString() {
          ArrayList<String> children = new ArrayList<String>();
          for (ParseTreeNode child : this.children) {
            children.add(child.toString());
          }
          return "(" + this.nonterminal.getString() + ": " + join(children, ", ") + ")";
        }

        public String toPrettyString() {
          return toPrettyString(0);
        }

        public String toPrettyString(int indent) {

          if (this.children.size() == 0) {
            return "(" + this.nonterminal.toString() + ": )";
          }

          String spaces = getIndentString(indent);

          ArrayList<String> children = new ArrayList<String>();
          for ( ParseTreeNode node : this.children ) {
            String sub = node.toPrettyString(indent + 2).trim();
            children.add(spaces + "  " +  sub);
          }

          return spaces + "(" + this.nonterminal.toString() + ":\n" + join(children, ",\n") + "\n" + spaces + ")";
        }
    }

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
        public String unexpectedEof(String method, List<TerminalIdentifier> expected, List<String> nt_rules) {
            return "Error: unexpected end of file";
        }

        public String excessTokens(String method, Terminal terminal) {
            return "Finished parsing without consuming all tokens.";
        }

        public String unexpectedSymbol(String method, Terminal actual, List<TerminalIdentifier> expected, String rule) {
            ArrayList<String> expected_terminals = new ArrayList<String>();
            for ( TerminalIdentifier e : expected ) {
                expected_terminals.add(e.string());
            }
            return String.format(
                "Unexpected symbol (line %d, col %d) when parsing parse_%s.  Expected %s, got %s.",
                actual.getLine(), actual.getColumn(), method, join(expected_terminals, ", "), actual.toPrettyString()
            );
        }

        public String noMoreTokens(String method, TerminalIdentifier expecting, Terminal last) {
            return "No more tokens.  Expecting " + expecting.string();
        }

        public String invalidTerminal(String method, Terminal invalid) {
            return "Invalid symbol ID: "+invalid.getId()+" ("+invalid.getTerminalStr()+")";
        }
    }

    public interface TerminalMap {
        TerminalIdentifier get(String string);
        TerminalIdentifier get(int id);
        boolean isValid(String string);
        boolean isValid(int id);
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

    public interface TerminalIdentifier {
        public int id();
        public String string();
    }

    public enum {{prefix}}TerminalIdentifier implements TerminalIdentifier {
{% for index, terminal in enumerate(grammar.standard_terminals) %}
        TERMINAL_{{terminal.string.upper()}}({{terminal.id}}, "{{terminal.string}}"),
{% endfor %}
        END_SENTINAL(-3, "END_SENTINAL");

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

    public ParseTree parse(TokenStream tokens) throws SyntaxError {
        return parse(tokens, new DefaultSyntaxErrorFormatter());
    }

    public ParseTree parse(List<Terminal> tokens) throws SyntaxError {
        return parse(new TokenStream(tokens));
    }

    public ParseTree parse(TokenStream tokens, SyntaxErrorFormatter error_formatter) throws SyntaxError {
        ParserContext ctx = new ParserContext(tokens, error_formatter);
        ParseTree tree = parse_{{grammar.start.string.lower()}}(ctx);
        if (ctx.tokens.current() != null) {
            StackTraceElement[] stack = Thread.currentThread().getStackTrace();
            throw new SyntaxError(ctx.error_formatter.excessTokens(stack[1].getMethodName(), ctx.tokens.current()));
        }
        return tree;
    }

    public ParseTree parse(List<Terminal> tokens, SyntaxErrorFormatter error_formatter) throws SyntaxError {
        return parse(new TokenStream(tokens), error_formatter);
    }

    private static Terminal expect(ParserContext ctx, TerminalIdentifier expecting) throws SyntaxError {
        Terminal current = ctx.tokens.current();
        if (current == null) {
            throw new SyntaxError(ctx.error_formatter.noMoreTokens(ctx.nonterminal, expecting, ctx.tokens.last()));
        }
        if (current.getId() != expecting.id()) {
            ArrayList<TerminalIdentifier> expectedList = new ArrayList<TerminalIdentifier>();
            expectedList.add(expecting);
            throw new SyntaxError(ctx.error_formatter.unexpectedSymbol(ctx.nonterminal, current, expectedList, ctx.rule));
        }
        Terminal next = ctx.tokens.advance();
        if ( next != null && !is_terminal(next.getId()) ) {
            throw new SyntaxError(ctx.error_formatter.invalidTerminal(ctx.nonterminal, next));
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

    public ParseTree parse_{{name}}(List<Terminal> tokens, SyntaxErrorFormatter error_formatter) throws SyntaxError {
        ParserContext ctx = new ParserContext(new TokenStream(tokens), error_formatter);
        return parse_{{name}}_internal(ctx, 0);
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
        ctx.nonterminal = "{{name}}";

        if (current == null) {
            return tree;
        }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py ruleFirstSet = grammar.first(rule.production) %}

    {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first(expression_nonterminal))%}
        {{'if' if i == 0 else 'else if'}} (rule_first.get({{rule.id}}).contains(terminal_map.get(current.getId()))) {

      {% py ast = rule.nudAst if not isinstance(rule.operator, PrefixOperator) else rule.ast %}
            /* ({{rule.id}}) {{rule}} */
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
        ctx.nonterminal = "{{name}}";
        int modifier;

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) %}

        if (current.getId() == {{led[0].id}}) {
            /* {{rule}} */
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

    public ParseTree parse_{{nonterminal.string.lower()}}(List<Terminal> tokens, SyntaxErrorFormatter error_formatter) throws SyntaxError {
        ParserContext ctx = new ParserContext(new TokenStream(tokens), error_formatter);
        return parse_{{nonterminal.string.lower()}}(ctx);
    }

    private static ParseTree parse_{{nonterminal.string.lower()}}(ParserContext ctx) throws SyntaxError {
        Terminal current = ctx.tokens.current();
        Terminal next;
        ParseTree subtree;
        int rule = (current != null) ? table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.getId()] : -1;
        ParseTree tree = new ParseTree( new NonTerminal({{nonterminal.id}}, "{{nonterminal.string}}"));
        ctx.nonterminal = "{{nonterminal.string.lower()}}";

  {% if isinstance(nonterminal.macro, LL1ListMacro) %}
        tree.setList(true);
  {% else %}
        tree.setList(false);
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
            throw new SyntaxError(ctx.error_formatter.unexpectedEof(
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
        {% if isinstance(nonterminal.macro, LL1ListMacro) %}
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
        throw new SyntaxError(ctx.error_formatter.unexpectedSymbol(
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

    {% if lexer %}
    /* Section: Lexer */
    private Map<String, List<HermesRegex>> regex = null;

    private interface LexerOutput {}

    private class LexerRegexOutput implements LexerOutput {
        public {{prefix}}TerminalIdentifier terminal;
        public int group;
        public Method function;

        LexerRegexOutput({{prefix}}TerminalIdentifier terminal, int group, Method function) {
            this.terminal = terminal;
            this.group = group;
            this.function = function;
        }

        public String toString() {
            return String.format("<LexerRegexOutput terminal=%s, group=%d, func=%s>", this.terminal, this.group, this.function);
        }
    }

    private class LexerStackPush implements LexerOutput {
        public String mode;

        LexerStackPush(String mode) {
            this.mode = mode;
        }
    }

    private class LexerAction implements LexerOutput {
        public String action;

        LexerAction(String action) {
            this.action = action;
        }
    }

    private class HermesRegex {
        public Pattern pattern;
        public List<LexerOutput> outputs;

        HermesRegex(Pattern pattern, List<LexerOutput> outputs) {
            this.pattern = pattern;
            this.outputs = outputs;
        }

        public String toString() {
            return String.format("<HermesRegex pattern=%s, outputs=%s>", this.pattern, this.outputs);
        }
    }

    private class LineColumn {
        public int line, col;
        public LineColumn(int line, int col) {
            this.line = line;
            this.col = col;
        }
        public String toString() {
            return String.format("<LineColumn: line=%d column=%d>", this.line, this.col);
        }
    }

    private class LexerContext {
        public String string;
        public String resource;
        public int line;
        public int col;
        public Stack<String> stack;
        public Object context;
        public List<Terminal> terminals;

        LexerContext(String string, String resource) {
            this.string = string;
            this.resource = resource;
            this.line = 1;
            this.col = 1;
            this.stack = new Stack<String>();
            this.stack.push("default");
            this.terminals = new ArrayList<Terminal>();
        }

        public void advance(String match) {
            LineColumn lc = advance_line_col(match, match.length());
            this.line = lc.line;
            this.col = lc.col;
            this.string = this.string.substring(match.length());
        }

        public LineColumn advance_line_col(String match, int length) {
            LineColumn lc = new LineColumn(this.line, this.col);
            for (int i = 0; i < length && i < match.length(); i++) {
                if (match.charAt(i) == '\n') {
                    lc.line += 1;
                    lc.col = 1;
                } else {
                    lc.col += 1;
                }
            }
            return lc;
        }
    }

    private void emit(LexerContext lctx, TerminalIdentifier terminal, String source_string, int line, int col) {
        lctx.terminals.add(new Terminal(terminal.id(), terminal.string(), source_string, lctx.resource, line, col));
    }

    {% if re.search(r'public\s+void\s+default_action', lexer.code) is None %}
    /**
     * The default function that is called on every regex match during lexical analysis.
     * By default, this simply calls the emit() function with all of the same parameters.
     * This can be overridden in the grammar file to provide a different default action.
     *
     * @param lctx The current state of the lexical analyzer
     * @param terminal The current terminal that was matched
     * @param source_string The source code that was matched
     * @param line The line where the match happened
     * @param col The column where the match happened
     * @return void
     */
    public void default_action(LexerContext lctx, TerminalIdentifier terminal, String source_string, int line, int col) {
        emit(lctx, terminal, source_string, line, col);
    }
    {% endif %}

    /* START USER CODE */
    {{lexer.code}}
    /* END USER CODE */

    {% if re.search(r'public\s+Object\s+init', lexer.code) is None %}
    public Object init() {
        return null;
    }
    {% endif %}

    {% if re.search(r'public\s+void\s+destroy', lexer.code) is None %}
    public void destroy(Object context) {
        return;
    }
    {% endif %}

    private Method getFunction(String name) throws SyntaxError {
        try {
            return getClass().getMethod(
                name,
                LexerContext.class,
                TerminalIdentifier.class,
                String.class,
                int.class,
                int.class
            );
        } catch (NoSuchMethodException e) {
            throw new SyntaxError("No such method: " + name);
        }
    }

    private void lexer_init() throws SyntaxError {
        this.regex = new HashMap<String, List<HermesRegex>>();
{% for mode, regex_list in lexer.items() %}
        this.regex.put("{{mode}}", Arrays.asList(new HermesRegex[] {
  {% for regex in regex_list %}
            new HermesRegex(
                Pattern.compile({{regex.regex}}{{', {0}'.format(' | '.join(['Pattern.'+x for x in regex.options])) if len(regex.options) else ''}}),
                Arrays.asList(new LexerOutput[] {
    {% for output in regex.outputs %}
       {% if isinstance(output, RegexOutput) %}
                    new LexerRegexOutput(
                        {{prefix+'TerminalIdentifier.TERMINAL_' + output.terminal.string.upper() if output.terminal else 'null'}},
                        {{output.group if output.group is not None else -1}},
                        getFunction({{'"'+output.function+'"' if output.function is not None else '"default_action"'}})
                    ),
       {% elif isinstance(output, LexerStackPush) %}
                    new LexerStackPush("{{output.mode}}"),
       {% elif isinstance(output, LexerAction) %}
                    new LexerAction("{{output.action}}"),
       {% endif %}
    {% endfor %}
                })
            ),
  {% endfor %}
        }));
{% endfor %}
    }

    private void unrecognized_token(String string, int line, int col) throws SyntaxError {
        String[] a = string.split("\n");
        String bad_line = string.split("\n")[line-1];
        StringBuffer spaces = new StringBuffer();
        for (int i = 0; i < col-1; i++) {
          spaces.append(' ');
        }
        String message = String.format(
            "Unrecognized token on line %d, column %d:\n\n%s\n%s^",
            line, col, bad_line, spaces
        );
        throw new SyntaxError(message);
    }

    private int next(LexerContext lctx) throws SyntaxError {
        String mode = lctx.stack.peek();
        for (int i = 0; i < this.regex.get(mode).size(); i++) {
            HermesRegex regex = this.regex.get(mode).get(i);
            Matcher matcher = regex.pattern.matcher(lctx.string);
            if (matcher.lookingAt()) {
                for (LexerOutput output : regex.outputs) {
                    if (output instanceof LexerStackPush) {
                        lctx.stack.push(((LexerStackPush) output).mode);
                    } else if (output instanceof LexerAction) {
                        LexerAction action = (LexerAction) output;
                        if (!action.action.equals("pop")) {
                            throw new SyntaxError("Invalid action");
                        }
                        if (action.action.equals("pop")) {
                            if (lctx.stack.empty()) {
                                throw new SyntaxError("Stack empty, cannot pop");
                            }
                            lctx.stack.pop();
                        }
                    } else if (output instanceof LexerRegexOutput) {
                        LexerRegexOutput regex_output = (LexerRegexOutput) output;
                        int group_line = lctx.line;
                        int group_col = lctx.col;

                        if (regex_output.group > 0) {
                            LineColumn lc = lctx.advance_line_col(matcher.group(0), matcher.start(regex_output.group));
                            group_line = lc.line;
                            group_col = lc.col;
                        }

                        try {
                            String source_string = (regex_output.group >= 0) ? matcher.group(regex_output.group) : "";
                            regex_output.function.invoke(
                                this,
                                lctx,
                                regex_output.terminal,
                                source_string,
                                group_line,
                                group_col
                            );
                        } catch (Exception e) {
                            e.printStackTrace();
                            throw new SyntaxError("Invalid method: " + regex_output.function);
                        }
                    }
                }
                lctx.advance(matcher.group(0));
                return matcher.group(0).length();
            }
        }
        return 0;
    }

    /**
     * Lexically analyze WDL source code, return a sequence of tokens.  Output of this
     * method should be used to construct a TerminalStream and then pass that to parse()
     *
     * @param string The WDL source code to analyze
     * @param resource A descriptor of where this code came from (usually a file path)
     * @return List of Terminal objects.
     * @throws SyntaxError If part of the source code could not lexically analyzed
     */

    public List<Terminal> lex(String string, String resource) throws SyntaxError {
        LexerContext lctx = new LexerContext(string, resource);
        Object context = this.init();
        lctx.context = context;
        String string_copy = new String(string);
        if (this.regex == null) {
            lexer_init();
        }
        while (lctx.string.length() > 0) {
            int match_length = this.next(lctx);

            if (match_length == 0) {
                this.unrecognized_token(string_copy, lctx.line, lctx.col);
            }
        }
        this.destroy(context);
        return lctx.terminals;
    }
    {% endif %}

    /* Section: Main */

    {% if add_main %}

    public static void main(String args[]) {
        if (args.length != 2 || (!"parsetree".equals(args[0]) && !"ast".equals(args[0]) {% if lexer %} && !"tokens".equals(args[0]){% endif %})) {
          System.out.println("Usage: {{prefix}}Parser parsetree <source>");
          System.out.println("Usage: {{prefix}}Parser ast <source>");
          {% if lexer %}
          System.out.println("Usage: {{prefix}}Parser tokens <source>");
          {% endif %}
          System.exit(-1);
        }

        {{prefix}}Parser parser = new {{prefix}}Parser();
        List<Terminal> terminals = null;

        try {
            String contents = readFile(args[1]);
            terminals = parser.lex(contents, args[1]);
        } catch (Exception e) {
            System.err.println(e.getMessage());
            System.exit(-1);
        }

        if ("parsetree".equals(args[0]) || "ast".equals(args[0])) {
            try {
                TokenStream tokens = new TokenStream();
                tokens.addAll(terminals);
                ParseTreeNode parsetree = parser.parse(tokens);

                if ( args.length > 1 && args[0].equals("ast") ) {
                    AstNode ast = parsetree.toAst();
                    if ( ast != null ) {
                        System.out.println(ast.toPrettyString());
                    } else {
                        System.out.println("None");
                    }
                } else {
                    System.out.println(parsetree.toPrettyString());
                }
            } catch (Exception e) {
                System.err.println(e.getMessage());
                System.exit(-1);
            }
        }

        {% if lexer %}
        if ("tokens".equals(args[0])) {
            for (Terminal terminal : terminals) {
                System.out.println(terminal);
            }
        }
        {% endif %}
    }
    {% endif %}
}
