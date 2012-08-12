import org.json.*;
import java.io.*;
import java.util.List;
import java.util.ArrayList;

class ParserMain {

  private static class DefaultSyntaxErrorFormatter implements SyntaxErrorFormatter {

    private TerminalMap map;
   
    public void setTerminalMap(TerminalMap map) {
      this.map = map;
    }

    public String unexpected_eof(String method, List<Integer> expected) {
      return "Error: unexpected end of file";
    }

    public String excess_tokens(String method, Terminal terminal) {
      return "Finished parsing without consuming all tokens.";
    }

    public String unexpected_symbol(String method, Terminal actual, List<Integer> expected) {
      ArrayList<String> expected_terminals = new ArrayList<String>();
      for ( Integer e : expected ) {
        expected_terminals.add(this.map.get(e.intValue()));
      }
      return "Unexpected symbol when parsing " + method + ".  Expected " + Utility.join(expected_terminals, ", ") + ", got " + actual.getTerminalStr() + ".";
    }

    public String no_more_tokens(String method, int expecting) {
      return "No more tokens.  Expecting " + this.map.get(expecting);
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
      TokenStream tokens = new TokenStream(terminals);
      error_formatter.setTerminalMap(terminals);
      
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
