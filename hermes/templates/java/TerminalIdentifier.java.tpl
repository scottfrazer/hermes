{% if package %}
package {{package}};
{% endif %}

public interface TerminalIdentifier {
  public int id();
  public String string();
}
