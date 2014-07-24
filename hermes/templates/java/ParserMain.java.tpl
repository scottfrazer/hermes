{% if java_package %}
package {{java_package}};
{% endif %}

import org.json.*;
import java.io.*;

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
        if (!"tokens".equals(args[0])) {
          /*
          {{prefix}}lexer_init();
          if ( {{prefix}}lexer_has_errors() ) {
              {{prefix}}lexer_print_errors();
          }
          tokens = {{prefix}}lex(file_contents, argv[2], &err[0]);
          if (tokens == NULL) {
              printf("Error: %s\n", err);
          }

          System.out.print("[\n");
          for (int i = 0; tokens[i]; tokens++) {
              while(1) {
                  rc = base64_encode((const char *) tokens[i]->source_string, strlen(tokens[i]->source_string), b64, b64_size);
                  if (rc == 0) break;
                  else if (rc == BASE64_OUTPUT_TOO_SMALL) {
                      b64_size *= 2;
                      b64 = realloc(b64, b64_size);
                      continue;
                  }
                  else {
                      printf("Error\n");
                      exit(-1);
                  }
              }

              printf(
                "    %c\"terminal\": \"%s\", \"resource\": \"%s\", \"line\": %d, \"col\": %d, \"source_string\": \"%s\"%c%s\n",
                '{',
                tokens[i]->terminal->string,
                tokens[i]->resource,
                tokens[i]->lineno,
                tokens[i]->colno,
                b64,
                '}',
                tokens[i+1] == NULL ? "" : ","
              );
          }
          printf("]\n");
          {{prefix}}lexer_destroy();
          return 0;
          */
        }
        {% endif %}
    }
}
