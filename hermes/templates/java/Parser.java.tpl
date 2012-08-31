{% if package %}
package {{package}};
{% endif %}

public interface Parser {
  ParseTree parse(TokenStream tokens) throws SyntaxError;
  TerminalMap getTerminalMap();
}
