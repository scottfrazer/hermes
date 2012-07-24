import java.util.ArrayList;

class ParseTree implements ParseTreeNode {

  private NonTerminal nonterminal;
  private ArrayList<ParseTreeNode> children;

  ParseTree(NonTerminal nonterminal) {
    this.nonterminal = nonterminal;
    this.children = new ArrayList<ParseTreeNode>();
    this.astTransform = None
    this.isExpr = false;
    this.isNud = false;
    this.isPrefix = false;
    this.isInfix = false;
    this.isExprNud = false;
    this.nudMorphemeCount = 0;
    this.listSeparator = None;
    this.list = "";
  }

  public void add(tree) {
    this.children.add(tree);
  }

  public Ast toAst() {
    if ( this.list == "slist" or this.list == "nlist" ) {
      if ( this.children.size() == 0 ) {
        return new AstList();
      }
      offset = 1 if this.children[0] == this.listSeparator else 0
      r = AstList([this.children[offset].toAst()])
      r.extend(this.children[offset+1].toAst())
      return r
    } else if ( this.list == "tlist" ) {
      if len(this.children) == 0:
        return AstList()
      r = AstList([this.children[0].toAst()])
      r.extend(this.children[2].toAst())
      return r
    } else if ( this.list == "mlist" ) {
      r = AstList()
      if len(this.children) == 0:
        return r
      lastElement = len(this.children) - 1
      for i in range(lastElement):
        r.append(this.children[i].toAst())
      r.extend(this.children[lastElement].toAst())
      return r
    } else if ( this.isExpr ) {
      if isinstance(this.astTransform, AstTransformSubstitution) {
        return this.children[this.astTransform.idx].toAst()
      } else if isinstance(this.astTransform, AstTransformNodeCreator) {
        parameters = {}
        for name, idx in this.astTransform.parameters.items() {
          if ( idx == '$' ) {
            child = this.children[0]
          } else if ( isinstance(this.children[0], ParseTree) && this.children[0].isNud && !this.children[0].isPrefix and && !this.isExprNud and && !this.isInfix ) {
            if ( idx < this.children[0].nudMorphemeCount ) {
              child = this.children[0].children[idx]
            } else {
              index = idx - this.children[0].nudMorphemeCount + 1
              child = this.children[index]
            }
          } else if ( len(this.children) == 1 and not isinstance(this.children[0], ParseTree) and not isinstance(this.children[0], list) ) {
            return this.children[0];
          } else {
            child = this.children[idx];
          }

          parameters[name] = child.toAst();
        }
        return Ast(this.astTransform.name, parameters)
      }
    } else {
      if (isinstance(this.astTransform, AstTransformSubstitution) {
        return this.children[this.astTransform.idx].toAst();
      } else if (isinstance(this.astTransform, AstTransformNodeCreator)) {
        parameters = {name: this.children[idx].toAst() for name, idx in this.astTransform.parameters.items()};
        return Ast(this.astTransform.name, parameters);
      } else if (len(this.children)) {
        return this.children[0].toAst();
      } else {
        return None;
      }
    }
  }

  public String toString() {
    children = []
    for ( child in this.children) {
      if isinstance(child, list) {
        children.append('[' + ', '.join([str(a) for a in child]) + ']');
      } else {
        children.append(str(child));
      }
    }
    return '(' + str(this.nonterminal) + ': ' + ', '.join(children) + ')'
  }
}
