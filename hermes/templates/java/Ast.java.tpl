import java.util.Map;
import java.util.LinkedList;
import java.util.Formatter;
import java.util.Locale;

class Ast implements AstNode {

  private String name;
  private Map<String, AstNode> attributes;

  Ast(String name, Map<String, AstNode> attributes) {
    this.name = name;
    this.attributes = attributes;
  }

  public AstNode getAttribute(String name) {
    return this.attributes.get(name);
  }

  public Map<String, AstNode> getAttributes() {
    return this.attributes;
  }

  public String getName() {
    return this.name;
  }

  public String toString() {
    Formatter formatter = new Formatter(new StringBuilder(), Locale.US);

    LinkedList<String> attributes = new LinkedList<String>();
    for (final Map.Entry<String, AstNode> attribute : this.attributes.entrySet()) {
      final String name = attribute.getKey();
      final AstNode node = attribute.getValue();
      attributes.add(name + "=" + node.toString());
    }

    formatter.format("(%s: %s)", this.name, Utility.join(attributes, ", "));
    return formatter.toString();
  }

  public String toPrettyString() {
    return "";
  }

  public String toPrettyString(int indent) {
    return "";
  }
}
