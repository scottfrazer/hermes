{% if java_package %}
package {{java_package}};
{% endif %}

public interface TerminalIdentifier {
  public int id();
  public String string();
}
