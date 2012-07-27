import java.util.ArrayList;

class AstList extends ArrayList<AstNode> implements AstNode {

  public String toString() {
    return "[" + Utility.join(this, ", ") + "]";
  }

  public String toPrettyString() {
    return "";
  }

  public String toPrettyString(int indent) {
    return "";
  }

}
