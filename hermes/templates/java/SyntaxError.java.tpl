{% if java_package %}
package {{java_package}};
{% endif %}

public class SyntaxError extends Exception {
  public SyntaxError(String message) {
    super(message);
  }
}
