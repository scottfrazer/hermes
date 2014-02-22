{% if java_package %}
package {{java_package}};
{% endif %}

public interface AstNode {
  public String toString();
  public String toPrettyString();
  public String toPrettyString(int indent);
}
