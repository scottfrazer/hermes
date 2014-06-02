{% if java_package %}
package {{java_package}};
{% endif %}

public interface TerminalMap {
  TerminalIdentifier get(String string);
  TerminalIdentifier get(int id);
  boolean isValid(String string);
  boolean isValid(int id);
}
