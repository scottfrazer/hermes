{% if package %}
package {{package}};
{% endif %}

public interface ExpressionParser extends Parser {
  ParseTree parse(TokenStream tokens, int rbp) throws SyntaxError;
}
