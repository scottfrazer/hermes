{% if java_package %}
package {{java_package}};
{% endif %}

public interface TerminalMap {
  int get(String string);
  String get(int id);
  boolean isValid(String string);
  boolean isValid(int id);
}
