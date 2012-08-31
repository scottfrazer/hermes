{% if package %}
package {{package}};
{% endif %}

public class SyntaxError extends Exception {
  SyntaxError(String message) {
    super(message);
  }
}
