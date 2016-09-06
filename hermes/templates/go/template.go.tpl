package main // TODO
{% if len(header)%}
{{'\n'.join(['// ' + s for s in header.split('\n')])}}
{% endif %}
import (
  "fmt"
  "regexp"
)

{% import re %}
{% from hermes.grammar import * %}

type terminal struct {
  id int
  idStr string
}

type nonTerminal struct {
  id int
  idStr string
  firstSet []int
  followSet []int
  rules[]int
}

func (nt *nonTerminal) CanStartWith(terminalId int) bool {
  for i := range nt.firstSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

func (nt *nonTerminal) CanBeFollowedBy(terminalId int) bool {
  for i := range nt.followSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

type rule struct {
  id int
  str string
  firstSet []int
}

func (rule *rule) CanStartWith(terminalId int) bool {
  for i := range rule.firstSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

type Token struct {
  terminal *terminal
  sourceString string
  resource string
  line int
  col int
}

func (t *Token) String() {

    /////////////////////////////////////////
      source_string = base64.b64encode(self.source_string.encode('utf-8')).decode('utf-8') if b64_source else self.source_string
      return '<{resource}:{line}:{col} {terminal} "{source}">'.format(
          resource=self.resource,
          line=self.line,
          col=self.col,
          terminal=self.str,
          source=source_string
      )
    /////////////////////////////////////////

}

type TokenStream struct {
  tokens []*Token
  index int
}

func (ts *TokenStream) current() *Terminal {
  if ts.index < len(ts.tokens) {
    return ts.tokens[ts.index]
  }
  return nil
}

func (ts *TokenStream) advance() *Terminal {
  ts.index = ts.index + 1
  return ts.current()
}

func (ts *TokenStream) last() *Terminal {
  if len(ts.tokens) > 0 {
    return ts.tokens[len(ts.tokens)-1]
  }
  return nil
}

type parseTree struct {
  nonterminal *NonTerminal
  children []*TreeNode
  astTransform ??????
  isExpr bool
  isNud bool
  isPrefix bool
  isInfix bool
  nudMorphemeCount int
  isExprNud bool // true for rules like _expr := {_expr} + {...}
  list_separator_id int ???
  list bool
}

func (tree *parseTree) Add(node *TreeNode) {
/////////////////////////////////
self.children.append( tree )
////////////////////////////////
}

func (tree *parseTree) ToAst() *AstNode {
/////////////////////////////////////
    if self.list == True:
        r = AstList()
        if len(self.children) == 0:
            return r
        for child in self.children:
            if isinstance(child, Terminal) and self.list_separator_id is not None and child.id == self.list_separator_id:
                continue
            r.append(child.ast())
        return r
    elif self.isExpr:
        if isinstance(self.astTransform, AstTransformSubstitution):
            return self.children[self.astTransform.idx].ast()
        elif isinstance(self.astTransform, AstTransformNodeCreator):
            parameters = OrderedDict()
            for name, idx in self.astTransform.parameters.items():
                if idx == '$':
                    child = self.children[0]
                elif isinstance(self.children[0], ParseTree) and \
                     self.children[0].isNud and \
                     not self.children[0].isPrefix and \
                     not self.isExprNud and \
                     not self.isInfix:
                    if idx < self.children[0].nudMorphemeCount:
                        child = self.children[0].children[idx]
                    else:
                        index = idx - self.children[0].nudMorphemeCount + 1
                        child = self.children[index]
                elif len(self.children) == 1 and not isinstance(self.children[0], ParseTree) and not isinstance(self.children[0], list):
                    return self.children[0]
                else:
                    child = self.children[idx]
                parameters[name] = child.ast()
            return Ast(self.astTransform.name, parameters)
    else:
        if isinstance(self.astTransform, AstTransformSubstitution):
            return self.children[self.astTransform.idx].ast()
        elif isinstance(self.astTransform, AstTransformNodeCreator):
            parameters = OrderedDict()
            for name, idx in self.astTransform.parameters.items():
                parameters[name] = self.children[idx].ast()
            return Ast(self.astTransform.name, parameters)
        elif len(self.children):
            return self.children[0].ast()
        else:
            return None
//////////////////////////////////////////////
}

func (tree *parseTree) String() {
//////////////////////////////////////////
    args = locals()
    del args['self']
    return parse_tree_string(self, **args)
/////////////////////////////////////////
}

func (tree *parseTree) String(indent int, b64Source bool) {
  return tree._String(indent, b64Source, 0)
}

func (tree *parseTree) _String(indent int, b64Source bool, indentLevel int) {

    /////////////////////////////////////
    indent_str = (' ' * indent * indent_level) if indent else ''
    if isinstance(parsetree, ParseTree):
        children = [parse_tree_string(child, indent, b64_source, indent_level+1, debug) for child in parsetree.children]
        debug_str = parsetree.debug_str() if debug else ''
        if indent is None or len(children) == 0:
            return '{0}({1}: {2}{3})'.format(indent_str, parsetree.nonterminal, debug_str, ', '.join(children))
        else:
            return '{0}({1}:{2}\n{3}\n{4})'.format(
                indent_str,
                parsetree.nonterminal,
                debug_str,
                ',\n'.join(children),
                indent_str
            )
    elif isinstance(parsetree, Terminal):
        return indent_str + parsetree.dumps(b64_source=b64_source)
    /////////////////////////////////////

}

type Ast struct {
  name string
  attributes map[string]*AstNode
}

func (ast *Ast) String() {
//////////////////////////////////////////
  args = locals()
  del args['self']
  return ast_string(self, **args)
/////////////////////////////////////////
}

func (ast *Ast) String(indent int, b64Source bool) {
  return ast._String(indent, b64Source, 0)
}

func (ast *Ast) _String(indent int, b64Source bool, indentLevel int) {

    /////////////////////////////////////
    indent_str = (' ' * indent * indent_level) if indent else ''
    next_indent_str = (' ' * indent * (indent_level+1)) if indent else ''
    if isinstance(ast, Ast):
        children = OrderedDict([(k, ast_string(v, indent, b64_source, indent_level+1)) for k, v in ast.attributes.items()])
        if indent is None:
            return '({0}: {1})'.format(
                ast.name,
                ', '.join('{0}={1}'.format(k, v) for k, v in children.items())
            )
        else:
            return '({0}:\n{1}\n{2})'.format(
                ast.name,
                ',\n'.join(['{0}{1}={2}'.format(next_indent_str, k, v) for k, v in children.items()]),
                indent_str
            )
    elif isinstance(ast, list):
        children = [ast_string(element, indent, b64_source, indent_level+1) for element in ast]
        if indent is None or len(children) == 0:
            return '[{0}]'.format(', '.join(children))
        else:
            return '[\n{1}\n{0}]'.format(
                indent_str,
                ',\n'.join(['{0}{1}'.format(next_indent_str, child) for child in children]),
            )
    elif isinstance(ast, Terminal):
        return ast.dumps(b64_source=b64_source)

    /////////////////////////////////////////
}

type AstTransformSubstitution int

func (t *AstTransformSubstitution) String() {
  return fmt.Sprintf("$%d", *t)
}

type AstTransformNodeCreator struct {
  name string
  parameters map[string]int // TODO: I think this is the right type?
}

func (t *AstTransformNodeCreator) String() {
    /////////////////////////////////////////
    return self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )'
    /////////////////////////////////////////
}


class AstList(list):
  def ast(self):
      retval = []
      for ast in self:
          retval.append(ast.ast())
      return retval
  def dumps(self, indent=None, b64_source=True):
      args = locals()
      del args['self']
      return ast_string(self, **args)

type SyntaxError struct {
  message string
}

type DefaultSyntaxErrorHandler struct {
  syntaxErrors []string
}

func (h *DefaultSyntaxErrorHandler) _error(string string) {
    error = SyntaxError(string)
    self.errors.append(error)
    return error
}
func (h *DefaultSyntaxErrorHandler) unexpected_eof() {
    return h._error("Error: unexpected end of file")
}
func (h *DefaultSyntaxErrorHandler) excess_tokens() {
    return h._error("Finished parsing without consuming all tokens.")
}
func (h *DefaultSyntaxErrorHandler) unexpected_symbol(nonterminal, actual_terminal, expected_terminals, rule) {
    return h._error("Unexpected symbol (line {line}, col {col}) when parsing parse_{nt}.  Expected {expected}, got {actual}.".format(
        line=actual_terminal.line,
        col=actual_terminal.col,
        nt=nonterminal,
        expected=', '.join(expected_terminals),
        actual=actual_terminal
    ))
}
func (h *DefaultSyntaxErrorHandler) no_more_tokens(nonterminal, expected_terminal, last_terminal) {
    return h._error("No more tokens.  Expecting " + expected_terminal)
}
func (h *DefaultSyntaxErrorHandler) invalid_terminal(nonterminal, invalid_terminal) {
    return h._error("Invalid symbol ID: {} ({})".format(invalid_terminal.id, invalid_terminal.string))
}
func (h *DefaultSyntaxErrorHandler) unrecognized_token(string, line, col int) {
    lines = string.split('\n')
    bad_line = lines[line-1]
    return h._error('Unrecognized token on line {}, column {}:\n\n{}\n{}'.format(
       line, col, bad_line, ''.join([' ' for x in range(col-1)]) + '^'
    ))
}
func (h *DefaultSyntaxErrorHandler) missing_list_items(method, required, found, last) {
    return h._error("List for {} requires {} items but only {} were found.".format(method, required, found))
}
func (h *DefaultSyntaxErrorHandler) missing_terminator(method, required, terminator, last) {
    return h._error("List for "+method+" is missing a terminator")
}

###############
# Parser Code #
###############

var table [][]int
var terminals []*terminal
var nonterminals []*nonTerminal
var rules []*rule

func initTable() [][]int {
  if table == nil {
    table = make([][]int, {{len(grammar.nonterminals)}})
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
    table[{{i}}] = []int{ {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} }
{% endfor %}
  }
  return table
}

func initTerminals() []*terminal {
  if terminals == nil {
    terminals = make([]*terminal, {{len(grammar.standard_terminals)}})
{% for index, terminal in enumerate(grammar.standard_terminals) %}
    terminals[{{index}}] = &terminal{ {{terminal.id}}, "{{terminal.string}}" }
{% endfor %}
  }
  return terminals
}

func initNonTerminals() []*nonTerminal {
  if nonterminals == nil {
    nonterminals = make([]*nonTerminal, {{len(grammar.nonterminals)}})
    var first []int
    var follow []int
{% for index, nt in enumerate(grammar.nonterminals) %}
    first = []int{ {{', '.join([str(t.id) for t in grammar.first(nt)])}} }
    follow = []int{ {{', '.join([str(t.id) for t in grammar.follow(nt)])}} }
    {% py nt_rules = [rule for rule in grammar.get_expanded_rules(nt)] %}
    rules = []int { {{ ', '.join([str(r.id) for r in nt_rules]) }} }
    nonterminals[{{index}}] = &nonTerminal{ {{nt.id}}, "{{nt.string}}", first, follow, rules }
{% endfor %}
  }
  return nonterminals
}

func initRules() []*rule {
  if rules == nil {
{% py rules = grammar.get_expanded_rules() %}
    rules = make([]*rule, {{len(rules)}})
    var firstSet []int
{% for index, rule in enumerate(rules) %}
    firstSet = []int{ {{', '.join([str(t.id) for t in grammar.first(rule.production)])}} }
    rules[{{index}}] = &rule{ {{rule.id}}, "{{rule}}", firstSet }
{% endfor %}
  }
  return rules
}

type ParserContext struct {
  tokens *TokenStream
  errors *SyntaxErrorHandler
  nonterminal_string string
  rule_string string
}

func (ctx *ParserContext) expect(terminal_id int) (*Terminal, error) {
    current := ctx.tokens.current()
    if current == nil {
        err := ctx.errors.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last())
        return nil, err
    }
    if current.id != terminal_id {
        err := ctx.errors.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule)
        return nil, err
    }
    next := ctx.tokens.advance()
    if next != nil && !ctx.IsValidTerminalId(next.id) {
        err := ctx.errors.invalid_terminal(ctx.nonterminal, next)
        return nil, err
    }
    return current, nil
}

type {{ccPrefix}}Parser struct {
  table [][]int
  terminals []*Terminal
  nonterminals []*NonTerminal
  rules []*Rule
}

func New{{ccPrefix}}Parser() *{{ccPrefix}}Parser {
  return &{{ccPrefix}}Parser{
    initTable(),
    initTerminals(),
    initNonTerminals(),
    initRules()}
}

func (parser *{{ccPrefix}}Parser) ParseTokens(stream *TokenStream, handler *SyntaxErrorHandler) (*ParseTree, error) {
  ctx := ParserContext{stream, handler, "", ""}
  tree := parser.parse_{{grammar.start.string.lower()}}(ctx)
  if stream.current() != nil {
    ctx.errors.excess_tokens()
    return nil, ctx.errors
  }
  return tree, nil
}

func (parser *{{ccPrefix}}Parser) TerminalFromId(id int) *terminal {
  return parser.terminals[id]
}

func (parser *{{ccPrefix}}Parser) NonTerminalFromId(id int) *nonTerminal {
  return parser.nonTerminals[{{len(grammar.standard_terminals)}} - id]
}

func (parser *{{ccPrefix}}Parser) TerminalFromStringId(id string) *terminal {
  for t := range parser.terminals {
    if t.strId == id {
      return t
    }
  }
  return nil;
}

func (parser *{{ccPrefix}}Parser) Rule(id int) *rule {
  for r := range parser.rules {
    if r.id == id {
      return r
    }
  }
  return nil;
}

func (ctx *ParserContext) IsValidTerminalId(id int) {
  return 0 <= id && id <= {{len(grammar.standard_terminals) - 1}}
}

{% for expression_nonterminal in sorted(grammar.expression_nonterminals, key=str) %}
    {% py name = expression_nonterminal.string %}

func (parser *{{ccPrefix}}Parser) parser.infixBindingPower_{{name}}(terminal_id int) int {
  switch terminal_id {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
      {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
  case {{rule.operator.operator.id}}: return {{rule.operator.binding_power}} // {{rule}}
      {% endif %}
    {% endfor %}
  }
}

func (parser *{{ccPrefix}}Parser) prefixBindingPower_{{name}}(terminal_id int) int {
  switch terminal_id {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
      {% if rule.operator and rule.operator.associativity in ['unary'] %}
  case {{rule.operator.operator.id}}: return {{rule.operator.binding_power}} // {{rule}}
      {% endif %}
    {% endfor %}
  }
}

func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx *ParserContext) (*ParseTree, error) {
    return parser._parse_{{name}}(ctx, 0)
}

func (parser *{{ccPrefix}}Parser) _parse_{{name}}(ctx *ParserContext, rbp int) (*ParseTree, error) {
    left := nud_{{name}}(ctx)
    if isinstance(left, ParseTree) {
      left.isExpr = True
      left.isNud = True
    }
    for ctx.tokens.current() != nil && rbp < parser.infixBindingPower_{{name}}(ctx.tokens.current().id) {
      left = led_{{name}}(left, ctx)
    }
    if left != nil {
      left.isExpr = True
    }
    return left
}

func (parser *{{ccPrefix}}Parser) nud_{{name}}(ctx *ParserContext) (*ParseTree, error) {
  tree := ParseTree{NonTerminal{ {{expression_nonterminal.id}}, "{{name}}" }}
  current = ctx.tokens.current()
  ctx.nonterminal = "{{name}}"

  if current == nil {
    return tree
  }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py first_set = grammar.first(rule.production) %}
    {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
  {{'if' if i == 0 else 'else if'}} parser.Rule({{rule,id}}).CanStartWith(current.id) {
      ctx.rule = getRuleString({{rule.id}})

      {% py ast = rule.nudAst if not isinstance(rule.operator, PrefixOperator) else rule.ast %}

      {% if isinstance(ast, AstSpecification) %}
      var astParameters = make(map[string]string)
        {% for k,v in ast.parameters.items() %}
      astParameters["{{k}}"] = {% if v == '$' %}"{{v}}"{% else %}{{v}}{% endif %}
        {% endfor %}
      tree.astTransform = &AstTransformNodeCreator{"{{ast.name}}", astParameters}
      {% elif isinstance(ast, AstTranslation) %}
      tree.astTransform = &AstTransformSubstitution{ {{ast.idx}} }
      {% endif %}

      tree.nudMorphemeCount = {{len(rule.nud_production)}}

      {% for morpheme in rule.nud_production.morphemes %}
        {% if isinstance(morpheme, Terminal) %}
      token, err := expect(ctx, {{morpheme.id}})
      if err != nil {
        return nil, err
      }
      tree.Add(token)
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
          {% if isinstance(rule.operator, PrefixOperator) %}
      subtree, err := parser._parse_{{name}}(ctx, parser.prefixBindingPower_{{name}}({{rule.operator.operator.id}}))
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
      tree.isPrefix = True
          {% else %}
      subtree, err := parser.Parse_{{rule.nonterminal.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.add(subtree)
          {% endif %}
        {% elif isinstance(morpheme, NonTerminal) %}
      subtree, err := parser.Parse_{{morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.add(subtree)
        {% endif %}
      {% endfor %}
  }
    {% endif %}
  {% endfor %}

  return tree
}

func (parser *{{ccPrefix}}Parser) led_{{name}}(left *ParseTree, ctx *ParserContext) {
  tree = ParseTree{NonTerminal{ {{expression_nonterminal.id}}, "{{name}}" }}
  current = ctx.tokens.current()
  ctx.nonterminal = "{{name}}"

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.led_production.morphemes %}
    {% if len(led) %}

  if current.id == {{led[0].id}} {
      // {{rule}}
      ctx.rule = parser.Rule({{rule.id}}).string

      {% if isinstance(rule.ast, AstSpecification) %}
      var astParameters = make(map[string]string)
        {% for k,v in rule.ast.parameters.items() %}
      astParameters["{{k}}"] = {% if v == '$' %}"{{v}}"{% else %}{{v}}{% endif %}
        {% endfor %}
      tree.astTransform = &AstTransformNodeCreator{"{{rule.ast.name}}", astParameters}
      {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = &AstTransformSubstitution{ {{rule.ast.idx}} }
      {% endif %}

      {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
        {% py nt = rule.nud_production.morphemes[0] %}
        {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
      tree.isExprNud = True
        {% endif %}
      {% endif %}

      tree.Add(left)

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
      {% for morpheme in led %}
        {% if isinstance(morpheme, Terminal) %}
      token, err := expect(ctx, {{morpheme.id}}) // {{morpheme}}
      if err != nil {
        return nil, err
      }
      tree.Add(token)
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
      modifier := {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
          {% if isinstance(rule.operator, InfixOperator) %}
      tree.isInfix = True
          {% endif %}
      subtree, err := parser._parse_{{name}}(ctx, parser.infixBindingPower_{{name}}({{rule.operator.operator.id}}) - modifier)
      if err != nil {
        return nil, err
      }
      tree.add(subtree)
        {% elif isinstance(morpheme, NonTerminal) %}
      subtree, err := parser.parse_{{morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.add(subtree)
        {% endif %}
      {% endfor %}
    {% endif %}
  }
  {% endfor %}

  return tree, nil
}

{% endfor %}

{% for list_nonterminal in sorted(grammar.list_nonterminals, key=str) %}
  {% py list_parser = grammar.list_parser(list_nonterminal) %}
  {% py name = list_nonterminal.string %}
func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx) (*ParseTree, error) {
    current = ctx.tokens.current()
    tree := ParseTree{NonTerminal{ {{list_nonterminal.id}}, "{{name}}" }}
    tree.list = True
  {% if list_parser.separator is not None %}
    tree.list_separator_id = {{list_parser.separator.id}}
  {% endif %}
    ctx.nonterminal = "{{name}}"

  {% if not grammar.must_consume_tokens(list_nonterminal) %}
    list_nonterminal = parser.NonTerminalFromId({{list_nonterminal.id}})
    if current != nil && list_nonterminal.CanBeFollowedBy(current.id) && list_nonterminal.CanStartWith(current.id) {
      return tree
    }
  {% endif %}

    if current == nil {
  {% if grammar.must_consume_tokens(list_nonterminal) %}
      return nil, ctx.error_formatter.unexpected_eof()
  {% else %}
      return tree
  {% endif %}
    }

    minimum := {{list_parser.minimum}}
    for minimum > 0 || (current != nil && parser.NonTerminalFromId({{list_nonterminal.id}}).CanStartWith(current.id) {
  {% if isinstance(list_parser.morpheme, NonTerminal) %}
      subtree, err := Parse_{{list_parser.morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
      ctx.nonterminal = "{{name}}" // Horrible -- because parse_* can reset this
  {% else %}
      token, err := expect(ctx, {{list_parser.morpheme.id}})
      if err != nil {
        return nil, err
      }
      tree.Add(token)
  {% endif %}

  {% if list_parser.separator is not None %}
      if current != nil && current.id == {{list_parser.separator.id}} {
        token, err := expect(ctx, {{list_parser.separator.id}})
        if err != nil {
          return nil, err
        }
        tree.Add(token)
      }
    {% if list_parser.sep_terminates %}
      else {
        raise ctx.errors.missing_terminator(
          "{{nonterminal.string.lower()}}",
          "{{list_parser.separator.string.upper()}}",
          None
        )
      }
    {% else %}
      else {
      {% if list_parser.minimum > 0 %}
        if minimum > 1 {
          raise ctx.errors.missing_list_items(
            "{{list_nonterminal.string.lower()}}",
            {{list_parser.minimum}},
            {{list_parser.minimum}} - minimum + 1,
            None
          )
        }
      {% endif %}
        break
      }
    {% endif %}
  {% endif %}

      minimum = max(minimum - 1, 0)
    }
    return tree
}
{% endfor %}

{% for nonterminal in sorted(grammar.ll1_nonterminals, key=str) %}
  {% py name = nonterminal.string %}
func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx *ParserContext) (*ParseTree, error):
  current = ctx.tokens.current()
  rule = table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] if current else -1
  tree = ParseTree(NonTerminal({{nonterminal.id}}, '{{name}}'))
  ctx.nonterminal = "{{name}}"

    {% if not grammar.must_consume_tokens(nonterminal) %}
  nt := parser.NonTerminalFromId({{nonterminal.id}})
  if current != nil && nt.CanBeFollwedBy(current.id) && nt.CanStartWith(current.id) {
    return tree
  }
    {% endif %}

  if current == nil {
    {% if grammar.must_consume_tokens(nonterminal) %}
    raise ctx.errors.unexpected_eof()
    {% else %}
    return tree
    {% endif %}
  }

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

      {% if index == 0 %}
  if rule == {{rule.id}} { // {{rule}}
      {% else %}
  else if rule == {{rule.id}} { // {{rule}}
      {% endif %}

    ctx.rule = rules[{{rule.id}}]

      {% if isinstance(rule.ast, AstTranslation) %}
    tree.astTransform = &AstTransformSubstitution{ {{rule.ast.idx}} }
      {% elif isinstance(rule.ast, AstSpecification) %}
    var astParameters = make(map[string]string)
        {% for k,v in rule.ast.parameters.items() %}
    astParameters["{{k}}"] = {% if v == '$' %}"{{v}}"{% else %}{{v}}{% endif %}
        {% endfor %}
    tree.astTransform = &AstTransformNodeCreator{ "{{rule.ast.name}}", astParameters }
      {% else %}
    tree.astTransform = &AstTransformSubstitution(0)
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
    token, err := ctx.expect(ctx, {{morpheme.id}}) // {{morpheme}}
    if err != nil {
      return nil, err
    }
    tree.Add(token)
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
    subtree, err := parser.Parse_{{morpheme.string.lower()}}(ctx)
    if err != nil {
      return nil, err
    }
    tree.Add(subtree)
        {% endif %}

      {% endfor %}
    return tree
  }
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
  raise ctx.errors.unexpected_symbol(
    ctx.nonterminal,
    ctx.tokens.current(),
    [terminals[x] for x in nonterminal_first[{{nonterminal.id}}] if x >=0],
    rules[{{rule.id}}]
  )
    {% else %}
  return tree
    {% endif %}
}
{% endfor %}

{% if lexer %}

/*
 * Lexer Code
 */

/* START USER CODE */
{{lexer.code}}
/* END USER CODE */

func (ctx *ParserContext) emit(terminal, source_string, line, col) {
  if terminal {
    ctx.tokens.append(Terminal(terminals[terminal], terminal, source_string, ctx.resource, line, col))
  }
}

{% if re.search(r'func\s+default_action', lexer.code) is None %}
func default_action(ctx *ParserContext, terminal, source_string, line, col) {
    ctx.emit(terminal, source_string, line, col)
}
{% endif %}

{% if re.search(r'def\s+init', lexer.code) is None %}
func init() interface{} {
    return interface{}{}
}
{% endif %}

{% if re.search(r'def\s+destroy', lexer.code) is None %}
func destroy(context interface{}) {}
{% endif %}

class LexerStackPush:
    def __init__(self, mode):
        self.mode = mode

class LexerAction:
    def __init__(self, action):
        self.action = action

class LexerContext:
    def __init__(self, string, resource, errors, user_context):
        self.__dict__.update(locals())
        self.stack = ['default']
        self.line = 1
        self.col = 1
        self.tokens = []
        self.user_context = user_context
        self.re_match = None # https://docs.python.org/3/library/re.html#match-objects

type HermesRegex struct {
  regex *Regexp
  outputs []*HermesRegexOutput
}

var regex map[string][]*HermesRegex

func initRegex() map[string][]*HermesRegex {
  if regex == nil {
    regex = make(map[string][]*HermesRegex)
{% for mode, regex_list in lexer.items() %}
    regex["{{mode}}"] = make([]*HermesRegex, {{len(regex_list)}})
  {% for index, regex in enumerate(regex_list) %}
    r := regexp.MustCompile({{regex.regex}})
    // TODO: set r.Flags
    matchActions := make([]*HermesLexerAction, {{len(regex.outputs)}})
    {% for index, output in enumerate(regex.outputs) %}
      {% if isinstance(output, RegexOutput) %}
    matchActions[{{index}}] = &LexerRegexOutput{ {{'"' + output.terminal.string.lower() + '"' if output.terminal else 'nil'}}, {{output.group}}, {{output.function}} }
      {% elif isinstance(output, LexerStackPush) %}
    matchActions[{{index}}] = &LexerStackPush{ "{{output.mode}}" }
      {% elif isinstance(output, LexerAction) %}
    matchActions[{{index}}] = &LexerAction{ "{{output.action}}" }
      {% endif %}
    {% endfor %}
    regex["{{mode}}"][index] = &HermesRegex{r, matchActions}
  {% endfor %}
{% endfor %}
  }
  return regex
}

class HermesLexer:
    regex = {
      {% for mode, regex_list in lexer.items() %}
        '{{mode}}': OrderedDict([
          {% for regex in regex_list %}
          (re.compile({{regex.regex}}{{", "+' | '.join(['re.'+x for x in regex.options]) if regex.options else ''}}), [
              # (terminal, group, function)
            {% for output in regex.outputs %}
              {% if isinstance(output, RegexOutput) %}
              ({{"'" + output.terminal.string.lower() + "'" if output.terminal else 'None'}}, {{output.group}}, {{output.function}}),
              {% elif isinstance(output, LexerStackPush) %}
              LexerStackPush('{{output.mode}}'),
              {% elif isinstance(output, LexerAction) %}
              LexerAction('{{output.action}}'),
              {% endif %}
            {% endfor %}
          ]),
          {% endfor %}
        ]),
      {% endfor %}
    }

    def _advance_line_col(self, string, length, line, col):
        for i in range(length):
            if string[i] == '\n':
                line += 1
                col = 1
            else:
                col += 1
        return (line, col)

    def _advance_string(self, ctx, string):
        (ctx.line, ctx.col) = self._advance_line_col(string, len(string), ctx.line, ctx.col)
        ctx.string = ctx.string[len(string):]

    def _next(self, ctx, debug=False):
        for regex, outputs in self.regex[ctx.stack[-1]].items():

            if debug:
                from xtermcolor import colorize
                token_count = len(ctx.tokens)
                print('{1} ({2}, {3}) regex: {0}'.format(
                    colorize(regex.pattern, ansi=40), colorize(ctx.string[:20].replace('\n', '\\n'), ansi=15), ctx.line, ctx.col)
                )

            match = regex.match(ctx.string)
            if match:
                ctx.re_match = match
                for output in outputs:
                    if isinstance(output, tuple):
                        (terminal, group, function) = output
                        function = function if function else default_action
                        source_string = match.group(group) if group is not None else ''
                        (group_line, group_col) = self._advance_line_col(ctx.string, match.start(group) if group else 0, ctx.line, ctx.col)
                        function(
                            ctx,
                            terminal,
                            source_string,
                            group_line,
                            group_col
                        )
                        if debug:
                            print('    matched: {}'.format(colorize(match.group(0).replace('\n', '\\n'), ansi=3)))
                            for token in ctx.tokens[token_count:]:
                                print('    emit: [{}] [{}, {}] [{}] stack:{} context:{}'.format(
                                    colorize(token.str, ansi=9),
                                    colorize(str(token.line), ansi=5),
                                    colorize(str(token.col), ansi=5),
                                    colorize(token.source_string, ansi=3),
                                    colorize(str(ctx.stack), ansi=4),
                                    colorize(str(ctx.user_context), ansi=13)
                                ))
                            token_count = len(ctx.tokens)
                    if isinstance(output, LexerStackPush):
                        ctx.stack.append(output.mode)
                        if debug:
                            print('    push on stack: {}'.format(colorize(output.mode, ansi=4)))
                    if isinstance(output, LexerAction):
                        if output.action == 'pop':
                            mode = ctx.stack.pop()
                            if debug:
                                print('    pop off stack: {}'.format(colorize(mode, ansi=4)))

                self._advance_string(ctx, match.group(0))
                return len(match.group(0)) > 0
        return False

    def lex(self, string, resource, errors=None, debug=False):
        if errors is None:
            errors = DefaultSyntaxErrorHandler()
        string_copy = string
        user_context = init()
        ctx = LexerContext(string, resource, errors, user_context)

        while len(ctx.string):
            matched = self._next(ctx, debug)
            if matched == False:
                raise ctx.errors.unrecognized_token(string_copy, ctx.line, ctx.col)

        destroy(ctx.user_context)
        return ctx.tokens

def lex(source, resource, errors=None, debug=False):
    return TokenStream(HermesLexer().lex(source, resource, errors, debug))

{% endif %}

{% if add_main %}

########
# Main #
########

func main() {
    if len(os.Args) != 3 || (os.Args[1] != "parsetree" && os.Args[1] != "ast"{% if lexer %} && os.Args[1] != "tokens"{% endif %}) {
        fmt.Printf("Usage: %s parsetree <source>\n".format(os.Args[0]))
        fmt.Printf("Usage: %s ast <source>\n".format(os.Args[0]))
        {% if lexer %}
        fmt.Printf("Usage: %s tokens <source>\n".format(os.Args[0]))
        {% endif %}
        os.Exit(-1)
    }

    bytes, err := ioutil.ReadFile(os.Args[2])
    if err != nil {
      fmt.Printf("Error reading file %s: %s", os.Args[2], err)
      os.Exit(-1)
    }

    parser := New{{ccPrefix}}Parser()
    tokens := parser.Lex(string(bytes))

    if os.Args[1] == "parsetree" || os.Args[1] == "ast" {
      tree := parser.ParseTokens(tokens)
      if os.Args[1] == "parsetree" {
        fmt.Println(tree.String(2))
      } else {
        ast := tree.toAst()
        if ast != nil {
          fmt.Println(ast.String(2))
        }
      }
    }
    if os.Args[1] == "tokens" {
      for token := range tokens {
        fmt.Println(token.String())
      }
    }
}
{% endif %}
