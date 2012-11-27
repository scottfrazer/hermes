{% if package %}
package {{package}};
{% endif %}

public class SyntaxError extends Exception {
  public SyntaxError(String message) {
    super(message);
  }
}
