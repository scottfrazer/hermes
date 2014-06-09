{% if java_package %}
package {{java_package}};
{% endif %}

import org.json.*;
import java.io.*;

public class ParserMain {
    public static void main(String args[]) {
        if ( args.length < 2 ) {
            System.out.println("Usage: ParserMain <parsetree,ast> <tokens file>");
            System.exit(-1);
        }

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
}
