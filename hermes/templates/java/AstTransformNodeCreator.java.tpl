import java.util.LinkedList;
import java.util.Map;

class AstTransformNodeCreator implements AstTransform {

  private String name;
  private Map<String, Integer> parameters;

  AstTransformNodeCreator(String name, Map<String, Integer> parameters) {
    this.name = name;
    this.parameters = parameters;
  }

  public Map<String, Integer> getParameters() {
    return this.parameters;
  }

  public String getName() {
    return this.name;
  }

  public String toString() {
    LinkedList<String> items = new LinkedList<String>();
    for (final Map.Entry<String, Integer> entry : this.parameters.entrySet()) {
      items.add(entry.getKey() + "=$" + entry.getValue().toString());
    }
    return this.name + "( " + Utility.join(items, ", ") + " )";
  }

}
