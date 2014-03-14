{% if java_package %}
package {{java_package}};
{% endif %}

public interface Parser {
  ParseTree parse(TokenStream tokens) throws SyntaxError;
  TerminalMap getTerminalMap();
}
