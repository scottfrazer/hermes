{% if java_package %}
package {{java_package}};
{% endif %}

import java.lang.reflect.Method;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;

{% import re %}

public class {{prefix}}Lexer {

    private Map<String, List<HermesRegex>> regex = null;

    private class HermesRegex {
        public Pattern pattern;
        public {{prefix}}TerminalIdentifier terminal;
        public String function;

        HermesRegex(Pattern pattern, {{prefix}}TerminalIdentifier terminal, String function) {
            this.pattern = pattern;
            this.terminal = terminal;
            this.function = function;
        }
    }

    private class LexerMatch {
        public List<Terminal> terminals;
        public String mode;
        public Object context;

        public LexerMatch(List<Terminal> terminals, String mode, Object context) {
            this.terminals = terminals;
            this.mode = mode;
            this.context = context;
        }
    }

    public enum {{prefix}}TerminalIdentifier implements TerminalIdentifier {
    {% for terminal in lexer.terminals %}
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

    private class LexerContext {
        public String string;
        public int line;
        public int col;
        public String mode;
        public Object context;
        public List<Terminal> terminals;

        LexerContext(String string) {
            this.string = string;
            this.line = 1;
            this.col = 1;
            this.mode = "default";
            this.terminals = new ArrayList<Terminal>();
        }

        public void advance(String match) {
            for (int i = 0; i < match.length(); i++) {
                if (match.charAt(i) == '\n') {
                    this.line += 1;
                    this.col = 1;
                } else {
                    this.col += 1;
                }
            }
            this.string = this.string.substring(match.length());
        }
    }

    /* START USER CODE */
    {{lexer.code}}
    /* END USER CODE */

    {% if re.search(r'private\s+LexerMatch\s+default_action', lexer.code) is None %}
    private LexerMatch default_action(Object context, String mode, String match, {{prefix}}TerminalIdentifier terminal, String resource, int line, int col) {
        //tokens = [Terminal(terminals[terminal], terminal, match, resource, line, col)] if terminal else []
        //return (tokens, mode, context)
        return null;
    }
    {% endif %}

    {% if re.search(r'private\s+Object\s+init', lexer.code) is None %}
    private Object init() {
        return null;
    }
    {% endif %}

    {% if re.search(r'private\s+void\s+destroy', lexer.code) is None %}
    private void destroy(Object context) {
        return;
    }
    {% endif %}

    public {{prefix}}Lexer() {
        this.regex = new HashMap<String, List<HermesRegex>>();
{% for mode, regex_list in lexer.items() %}
        this.regex.put("{{mode}}", Arrays.asList(new HermesRegex[] {
  {% for regex in regex_list %}
            new HermesRegex(Pattern.compile({{regex.regex}}), {{prefix+'TerminalIdentifier.TERMINAL_' + regex.terminal.string.upper() if regex.terminal else 'null'}}, {{regex.function if regex.function is not None else 'null'}}),
  {% endfor %}
        }));
{% endfor %}
    }

    private void update_line_col(String match, LexerContext lctx) {

    }

    private void unrecognized_token(String string, int line, int col) throws SyntaxError {
        String bad_line = string.split("\n")[line-1];
        StringBuffer spaces = new StringBuffer();
        for (int i = 0; i < col; i++) {
          spaces.append(' ');
        }
        String message = String.format(
            "Unrecognized token on line %d, column %d:\n\n%s\n%s^",
            line, col, bad_line, spaces
        );
        throw new SyntaxError(message);
    }

    private List<Terminal> next(LexerContext lctx, String resource) {
        for (int i = 0; i < this.regex.get(lctx.mode).size(); i++) {
            HermesRegex regex = this.regex.get(lctx.mode).get(i);
            Matcher matcher = regex.pattern.matcher(lctx.string);
            if (matcher.lookingAt()) {
                if (regex.terminal == null && regex.function == null) {
                    lctx.advance(matcher.group(0));
                    i = -1;
                    continue;
                }
                String function = regex.function != null ? regex.function : "default_action";
                try {
                    Method method = getClass().getMethod(function, Object.class, String.class, String.class, {{prefix}}TerminalIdentifier.class, String.class, int.class, int.class);
                    LexerMatch lexer_match = (LexerMatch) method.invoke(
                        this,
                        lctx.context,
                        lctx.mode,
                        matcher.group(0),
                        regex.terminal,
                        resource,
                        lctx.line,
                        lctx.col
                    );

                    lctx.terminals.addAll(lexer_match.terminals);
                    lctx.mode = lexer_match.mode;
                    lctx.context = lexer_match.context;
                    lctx.advance(matcher.group(0));
                    return lexer_match.terminals;
                } catch (Exception e) {
                    continue;
                }
            }
        }
        return null;
    }

    public List<Terminal> lex(String string, String resource) throws SyntaxError {
        LexerContext lctx = new LexerContext(string);
        Object context = this.init();
        String string_copy = new String(string);
        while (lctx.string.length() > 0) {
            List<Terminal> matched_terminals = this.next(lctx, resource);

            if (matched_terminals.size() == 0) {
                this.unrecognized_token(string_copy, lctx.line, lctx.col);
            }
        }
        this.destroy(context);
        return lctx.terminals;
    }
}
