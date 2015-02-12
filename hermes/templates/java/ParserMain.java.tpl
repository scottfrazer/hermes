{% if java_package %}
package {{java_package}};
{% endif %}

import org.json.*;
import java.io.*;
import java.util.List;

public class ParserMain {
    public static void main(String args[]) {
        if (args.length != 2 || (!"parsetree".equals(args[0]) && !"ast".equals(args[0]) {% if lexer %} && !"tokens".equals(args[0]){% endif %})) {
          System.out.println("Usage: ParserMain <parsetree,ast> <tokens file>");
          {% if lexer %}
          System.out.println("Usage: ParserMain <tokens> <source file>");
          {% endif %}
          System.exit(-1);
        }

        if ("parsetree".equals(args[0]) || "ast".equals(args[0])) {
            try {
                TokenStream tokens = new TokenStream();
                String contents = Utility.readFile(args[1]);
                JSONArray arr = new JSONArray(contents);

                for ( int i = 0; i < arr.length(); i++ ) {
                    JSONObject token = arr.getJSONObject(i);
                    tokens.add(new Terminal(
                        {{prefix}}Parser.terminal_map.get(token.getString("terminal")).id(),
                        token.getString("terminal"),
                        token.getString("source_string"),
                        token.getString("resource"),
                        token.getInt("line"),
                        token.getInt("col")
                    ));
                }

                ParseTreeNode parsetree = {{prefix}}Parser.parse(tokens);

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
          {{prefix}}Lexer lexer = new {{prefix}}Lexer();
          try {
            String contents = Utility.readFile(args[1]);
            List<Terminal> terminals = lexer.lex(contents, args[1]);
            if (terminals.size() == 0) {
                System.out.println("[]");
            } else {
                System.out.println(String.format("[\n    %s\n]", Utility.join(terminals, ",\n    ")));
            }
          } catch (Exception e) {
            System.err.println(e.getMessage());
            System.exit(-1);
          }
        }
        {% endif %}
    }
}
