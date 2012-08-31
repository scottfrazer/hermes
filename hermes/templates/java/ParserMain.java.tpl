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
      return "Unexpected symbol when parsing parse_" + method + ".  Expected " + Utility.join(expected_terminals, ", ") + ", got " + actual.getTerminalStr() + ".";
    }

    public String no_more_tokens(String method, TerminalIdentifier expecting, Terminal last) {
      return "No more tokens.  Expecting " + expecting.string();
    }

    public String invalid_terminal(String method, Terminal invalid) {
      return "Invalid symbol ID: "+invalid.getId()+" ("+invalid.getTerminalStr()+")";
    }

  }

  private static Parser getParser(String name, SyntaxErrorFormatter error_formatter) throws Exception {
    {% for grammar in grammars %}
    if (name.equals("{{grammar.name}}")) {
      return new {{grammar.name[0].upper() + grammar.name[1:]}}Parser(error_formatter);
    }
    {% endfor %}
    throw new Exception("Invalid grammar name: " + name);
  }

  public static void main(String args[]) {
    final String grammars = "{{','.join([grammar.name for grammar in grammars])}}";

    if ( args.length < 2 ) {
      System.out.println("Usage: ParserMain <" + grammars + "> <parsetree,ast>");
      System.exit(-1);
    }

    final String grammar = args[0].toLowerCase();

    try {
      DefaultSyntaxErrorFormatter error_formatter = new DefaultSyntaxErrorFormatter();
      Parser parser = getParser(grammar, error_formatter);
      TerminalMap terminals = parser.getTerminalMap();
      TokenStream tokens = new TokenStream();
      
      String contents = Utility.readStdin();
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

      if ( args.length > 1 && args[1].equals("ast") ) {
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
