{% if package %}
package {{package}};
{% endif %}

import org.json.*;
import java.io.*;
import java.util.List;
import java.util.ArrayList;

public class ParserMain {

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

  private static Parser getParser(SyntaxErrorFormatter error_formatter) throws Exception {
    return new {{grammar.name[0].upper() + grammar.name[1:]}}Parser(error_formatter);
  }

  public static void main(String args[]) {
    if ( args.length < 2 ) {
      System.out.println("Usage: ParserMain <parsetree,ast> <tokens file>");
      System.exit(-1);
    }

    try {
      DefaultSyntaxErrorFormatter error_formatter = new DefaultSyntaxErrorFormatter();
      Parser parser = getParser(error_formatter);
      TerminalMap terminals = parser.getTerminalMap();
      TokenStream tokens = new TokenStream();
      
      String contents = Utility.readFile(args[1]);
      JSONArray arr = new JSONArray(contents);

      for ( int i = 0; i < arr.length(); i++ ) {
        JSONObject token = arr.getJSONObject(i);

        tokens.add(new Terminal(
          terminals.get(token.getString("terminal")),
          token.getString("terminal"),
          token.getString("source_string"),
          token.getString("resource"),
          token.getInt("line"),
          token.getInt("col")
        ));

      }

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
}
