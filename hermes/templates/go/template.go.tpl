package main // TODO

{% if len(header)%}
{{'\n'.join(['// ' + s for s in header.split('\n')])}}
{% endif %}

import (
  "fmt"
  "regexp"
  "encoding/base64"
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

func (t *Token) String() string {
  return fmt.Sprintf(`<%s:%d:%d %s "%s">`, t.resource, t.line, t.col, t.terminal.strId, base64.StdEncoding.EncodeToString([]byte(t.sourceString)))
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
  astTransform interface{}
  isExpr bool
  isNud bool
  isPrefix bool
  isInfix bool
  nudMorphemeCount int
  isExprNud bool // true for rules like _expr := {_expr} + {...}
  list_separator_id int
  list bool
}

func (tree *parseTree) Add(node *TreeNode) {
  tree.children = append(tree.children, node)
}

func (tree *parseTree) ToAst() AstNode {
    if tree.list == True {
			r := AstList{}
			if len(tree.children) == 0 {
				return r
			}
			for child := range tree.children {
				switch t := child.(type) {
				case *Terminal:
					if tree.list_separator_id == t.id {
						continue
					}
					fallthrough
				default:
					r = append(r, child.ast())
				}
			}
			return r
    } else if tree.isExpr {
			switch transform := tree.astTransform.(type) {
			case *AstTransformSubstitution:
				return tree.children[transform.idx].Ast()
			case *AstTransformNodeCreator:
				attributes = make(map[string]AstNode)
				var child interface{}
				_, is_tree := tree.(parseTree)
				_, is_list := tree.(astList)
				for s, i := range transform.parameters {
					if i == '$' {
							child = tree.children[0]
					} else if tree.isCompoundNud() {
							firstChild := tree.children[0]

							if ( i < firstChild.getNudMorphemeCount() ) {
									child = firstChild.children[i]
							} else {
									i = i - firstChild.getNudMorphemeCount() + 1
									child = tree.children[i]
							}
					} else if ( len(tree.children) == 1 && !is_tree && !is_list ) {
							// TODO: I don't think this should ever be called
							child = tree.children[0]
					} else {
							child = tree.children[i];
					}
					attributes[s] = child.Ast();
				}
				return Ast{transform.name, atttributes}
			}
    } else {
			switch transform := tree.astTransform.(type) {
			case *AstTransformSubstitution:
				return tree.children[transform.idx].Ast()
			case *AstTransformNodeCreator:
				attributes = make(map[string]AstNode)
				for s, i := range transform.parameters {
					attributes[s] = tree.children[i].Ast()
				}
				return Ast{transform.name, attributes}
			}

			if len(this.children) > 0 {
				return this.children[0].Ast()
			}

			return nil
    }
}

func (tree *parseTree) String() {
  return parseTreeToString(tree, 0, 1)
}

func (tree *parseTree) PrettyString() {
  return parseTreeToString(tree, 2, 1)
}

func parseTreeToString(treenode interface{}, indent int, indentLevel int) string {
	indentStr = ""
	if indent > 0 {
		indentStr = strings.Repeat(" ", indent * indent_level)
	}

	switch node := treenode.(type) {
	case *parseTree:
		childStrings := make([]string, len(node.children))
		for index, child := range node.children {
			childStrings[index] = parseTreeToString(child, indent, indentLevel+1)
		}
		if indent == 0 || len(node.children) == 0 {
			return fmt.Sprintf("%s(%s: %s)", indentStr, tree.nonterminal.idStr, strings.Join(", ", childStrings))
		} else {
			return fmt.Sprintf("%s(%s:\n%s\n%s)", indentStr, tree.nonterminal.idStr, strings.Join(",\n", childStrings), indentStr)
		}
	case *Token:
		return fmt.Sprintf("%s%s", indentStr, node.String())
	default:
		panic(fmt.Sprintf("parseTreeToString() called on %t", node))
	}
}

type AstNode interface {
	String() string
	PrettyString() string
}

type Ast struct {
  name string
  attributes map[string]AstNode
}

func (ast *Ast) String(indent int) {
  return astToString(ast, indent, 0)
}

func astToString(ast interface{}, indent int, indentLevel int) {
		indentStr := ""
		nextIndentStr := ""
		attrPrefix := ""

		if indent > 0 {
			indentStr = strings.Repeat(" ", indent * indent_level)
			nextIndentStr = strings.Repeat(" ", indent * (indent_level+1))
			attrPrefix = nextIndentStr
		}

		switch node := ast.(type) {
		case *Ast:
			childStrings := make([]string, len(node.attributes))
			for name, subnode := range node.attributes {
				childString := fmt.Sprintf("%s%s=%s", attrPrefix, name, astToString(subnode, indent, indentLevel+1))
				childStrings = append(childStrings, childString)
			}
			if indent > 0 {
				return fmt.Sprintf("(%s:\n%s\n%s)", node.name, strings.Join(",\n", childStrings), indentStr)
			} else {
				return fmt.Sprintf("(%s: %s)", node.name, strings.Join(", ", childStrings))
			}
		case *AstList:
			childStrings := make([]string, len(node))
			for subnode := range node {
				childString := fmt.Sprintf("%s%s", attrPrefix, astToString(subnode, indent, indentLevel+1))
				childStrings = append(childStrings, childString)
			}

			if indent == 0 || len(node) == 0 {
					return fmt.Sprintf("[%s]", strings.Join(", ", children))
			} else {
					return fmt.Sprintf("[\n%s\n%s]", indentStr, strings.Join(",\n", childStrings))
			}
		case *Token:
			return node.String()
		default:
		}
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
	strings := make([]string, len(t.parameters))
	for k, v := range t.parameters {
		strings = append(strings, fmt.Sprintf("%s=$%d", k, v))
	}

	return fmt.Sprintf("%s(%s)", t.name, strings.Join(", ", strings))
}


type AstList []AstNode

func (list *AstList) String() string {
	return astToString(list)
}

type SyntaxError struct {
  message string
}

type DefaultSyntaxErrorHandler struct {
  syntaxErrors []string
}

func (h *DefaultSyntaxErrorHandler) _error(string string) *SyntaxError{
    error = SyntaxError{string}
    self.errors.append(error)
    return &error
}
func (h *DefaultSyntaxErrorHandler) unexpected_eof() *SyntaxError {
    return h._error("Error: unexpected end of file")
}
func (h *DefaultSyntaxErrorHandler) excess_tokens() *SyntaxError {
    return h._error("Finished parsing without consuming all tokens.")
}
func (h *DefaultSyntaxErrorHandler) unexpected_symbol(nt *nonTerminal, actual_terminal *terminal, expected_terminals []*terminal, rule *rule) *SyntaxError {
	strings := make([]string, len(expected_terminals))
	for _, t := range expected_terminals {
		strings = append(strings, t.idStr)
	}
    return h._error(fmt.Sprintf("Unexpected symbol (line %d, col %d) when parsing parse_%s.  Expected %s, got %s.",
				actual_terminal.line,
        actual_terminal.col,
        nt.idStr,
        strings.Join(", ", strings),
        actual_terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) no_more_tokens(nt *nonTerminal, expected_terminal *terminal, last_terminal *terminal) *SyntaxError {
    return h._error(fmt.Sprintf("No more tokens.  Expecting %s", expected_terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) invalid_terminal(nt *nonTerminal, invalid_terminal *terminal) *SyntaxError {
    return h._error(fmt.Sprintf("Invalid symbol ID: %d (%s)", invalid_terminal.id, invalid_terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) unrecognized_token(s string, line, col int) *SyntaxError {
	lines := strings.Split(s, "\n")
	bad_line := lines[line-1]
	return h._error(fmt.Sprintf("Unrecognized token on line %d, column %d:\n\n%s\n%s",
		 line, col, bad_line, strings.Repeat(" ", col-1) + '^'))
}
func (h *DefaultSyntaxErrorHandler) missing_list_items(method string , required, found int, last string) *SyntaxError {
	return h._error("List for %s requires %d items but only %d were found.".format(method, required, found))
}
func (h *DefaultSyntaxErrorHandler) missing_terminator(method string, required *terminal, terminator *terminal, last *terminal) *SyntaxError {
	return h._error(fmt.Sprintf("List for %s is missing a terminator", method))
}

/*
 * Parser Code
 */

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

func (ctx *ParserContext) emit(terminal, sourceString, line, col) {
  if terminal {
    ctx.tokens.append(Terminal(terminals[terminal], terminal, sourceString, ctx.resource, line, col))
  }
}

{% if re.search(r'func\s+default_action', lexer.code) is None %}
func default_action(ctx *ParserContext, terminal, sourceString, line, col) {
    ctx.emit(terminal, sourceString, line, col)
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

type LexerContext struct {
  source string
  resource string
  handler *SyntaxErrorHandler
  userContext interface{}
  stack []string
  line int
  col int
  tokens []*Token
}

func (ctx *LexerContext) StackPush(mode string) {
  ctx.stack = append(ctx.stack, mode)
}

func (ctx *LexerContext) StackPop() {
  ctx.stack = ctx.stack[:len(ctx.stack)-1]
}

func (ctx *LexerContext) StackPeek() string {
  return ctx.stack[len(ctx.stack)-1]
}

type HermesRegex struct {
  regex *Regexp
  outputs []*HermesRegexOutput
}

type HermesLexerAction interface {
  HandleMatch(ctx *ParserContext, groups []string, indexes []int)
}

type LexerRegexOutput struct {
  terminal *terminal
  group int
  function func(*LexerContext, *terminal, sourceString string, line, col int)
}

func (lro *LexerRegexOutput) HandleMatch(ctx *ParserContext, groups []string, indexes []int) {
  sourceString := ""
  startIndex := 0
  if lro.group > 0 {
    sourceString = groups[group]
    startIndex := group*2
  }

  groupLine, groupCol = _advance_line_col(ctx.string, indexes[startIndex], ctx.line, ctx.col)

  function := lro.function
  if function == nil {
    function = default_action
  }

  function(ctx, lro.terminal, sourceString, groupLine, groupCol)
}

type LexerStackPush struct {
  mode string
}

func (lsp *LexerStackPush) HandleMatch(ctx *ParserContext, groups []string, indexes []int) {
  ctx.StackPush(output.mode)
}

type LexerAction struct {
  action string
}

func (la *LexerAction) HandleMatch(ctx *ParserContext, groups []string, indexes []int) {
  if la.action == "pop" {
    ctx.StackPop()
  }
}

var regex map[string][]*HermesRegex

func initRegexes() map[string][]*HermesRegex {
  if regex == nil {
    regex = make(map[string][]*HermesRegex)
    var matchActions []HermesLexerAction
    var r *regexp.Regexp
    var terminals = initTerminals() // TODO: don't require this
    var t *terminal
    var findTerminal = func(name string) {
      if name == nil {
        return nil
      }
      for terminal := range terminals {
        if terminal.strId == name {
          t = terminal
        }
      }
    }

{% for mode, regex_list in lexer.items() %}
    regex["{{mode}}"] = make([]*HermesRegex, {{len(regex_list)}})
  {% for index, regex in enumerate(regex_list) %}
    r = regexp.MustCompile({{regex.regex}})
    // TODO: set r.Flags
    matchActions = make([]HermesLexerAction, {{len(regex.outputs)}})
    {% for index2, output in enumerate(regex.outputs) %}
      {% if isinstance(output, RegexOutput) %}
    matchActions[{{index2}}] = &LexerRegexOutput{ findTerminal({{'"' + output.terminal.string.lower() + '"' if output.terminal else 'nil'}}), {{output.group}}, {{output.function}} }
      {% elif isinstance(output, LexerStackPush) %}
    matchActions[{{index2}}] = &LexerStackPush{ "{{output.mode}}" }
      {% elif isinstance(output, LexerAction) %}
    matchActions[{{index2}}] = &LexerAction{ "{{output.action}}" }
      {% endif %}
    {% endfor %}
    regex["{{mode}}"][{{index}}] = &HermesRegex{r, matchActions}
  {% endfor %}
{% endfor %}
  }
  return regex
}

type {{ccPrefix}}Lexer struct {
  regex map[string][]*HermesRegex
}

func New{{ccPrefix}}Lexer() *{{ccPrefix}}Lexer {
  return &{{ccPrefix}}Lexer{initRegexes()}
}

func (*{{ccPrefix}}Lexer) _advance_line_col(s string, length, line, col int) (int, int) {
  c := 0
  for r := range s {
    c += 1
    if r == '\n' {
      line += 1
      col = 1
    } else {
      col += 1
    }
    if c == length {
      break
    }
  }
  return line, col
}

func (lexer *{{ccPrefix}}Lexer) _advance_string(ctx *LexerContext, s string) {
    ctx.line, ctx.col = self._advance_line_col(s, ctx.line, ctx.col)
    ctx.string = ctx.string[len(string):]
}

func (lexer *{{ccPrefix}}Lexer) _next(ctx *LexerContext) bool {
    for regex := range lexer.regex[ctx.StackPeek()] {
        groups = regex.regex.FindStringSubmatch(ctx.source)
        indexes = regex.regex.FindStringSubmatchIndex(ctx.source)
        if groups != nil && indexes != nil {
            for output := range regex.outputs {
              output.HandleMatch(ctx, groups, indexes)
            }
            lexer._advance_string(ctx, groups[0])
            return len(groups[0]) > 0
        }
    }
    return false
}

func (lexer *{{ccPrefix}}Lexer) lex(source, resource  string, handler *SyntaxErrorHandler) ([]*Token, error) {
  sourceCopy := string // TODO copy string
  user_context := init()
  ctx := LexerContext{sourceCopy, resource, errors, user_context}

  for len(ctx.source) {
    matched := lexer._next(ctx)
    if matched == false {
      return nil, ctx.errors.unrecognized_token(sourceCopy, ctx.line, ctx.col)
    }
  }

  destroy(user_context)
  return ctx.tokens
}

func (lexer *{{ccPrefix}}Lexer) Lex(source, resource string, errors *SyntaxErrorHandler) {
    return TokenStream(HermesLexer().lex(source, resource, errors))
}

{% endif %}

{% if add_main %}

/*
 * Main
 */

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
