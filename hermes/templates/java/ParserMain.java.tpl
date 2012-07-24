class ParserMain {

  private static Parser getParser(String name) {
    {% for grammar in grammars %}
    if ( name == "{{grammar.name}}") {
      return {{grammar.name}}_Parser();
    }
    {% endfor %}
    throw new Exception("Invalid grammar name: {}".format(name));
  }

  public static void main(String[] args) {
    final String grammars = "{{','.join([grammar.name for grammar in grammars])}}";

    if ( args.length < 2 ) {
      System.out.println("Usage: {} <{}> <parsetree,ast>".format(args[0], grammars));
      System.exit(-1);
    }

    String grammar = args[1].toLowerCase()
    Parser parser = getParser(grammar)

    in_tokens = json.loads(sys.stdin.read())
    tokens = new ArrayList<Terminal>(); 

    for (token in in_tokens) {
      for (key in ["terminal", "line", "col", "resource", "source_string"]) {
        if (key not in token.keys()) {
          throw new Exception('Malformed token (missing key {0}): {1}'.format(key, json.dumps(token)));
        }
      }

      try {
        tokens.add(new Terminal(
          parser.terminals[token['terminal']],
          token['terminal'],
          token['source_string'],
          token['resource'],
          token['line'],
          token['col']
        ))
      } catch (Exception e) {
        System.err.println(e);
        System.exit(-1);
      }
    }

    tokens = TokenStream(tokens)

    try {
      parsetree = parser.parse( tokens )
      if ( args.length > 2 and args[2] == "ast" ) {
        ast = parsetree.toAst()
        print(AstPrettyPrintable(ast))
      } else {
        print(ParseTreePrettyPrintable(parsetree))
      }
    } catch (Exception as error) {
      System.err.println(error);
      System.exit(-1);
    }
  }
}
