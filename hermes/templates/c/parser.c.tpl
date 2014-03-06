{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser_common.h"
#include "{{prefix}}parser.h"

{% for nonterminal in grammar.ll1_nonterminals %}
static PARSE_TREE_T * parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
static PARSE_TREE_T * parse_{{exprGrammar.nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
static PARSE_TREE_T * _parse_{{exprGrammar.nonterminal.string.lower()}}(int, PARSER_CONTEXT_T *);
{% endfor %}

void syntax_error( PARSER_CONTEXT_T * ctx, char * message );

/* index with {{prefix.upper()}}TERMINAL_E or {{prefix.upper()}}NONTERMINAL_E */
static char * {{prefix}}morphemes[] = {
{% for terminal in sorted(grammar.standard_terminals, key=lambda x: x.id) %}
  "{{terminal.string}}", /* {{terminal.id}} */
{% endfor %}

{% for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.id) %}
  "{{nonterminal.string}}", /* {{nonterminal.id}} */
{% endfor %}
};

static int {{prefix}}first[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.first[nonterminal]])}}{{', ' if len(grammar.first[nonterminal]) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}follow[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.follow[nonterminal]])}}{{', ' if len(grammar.follow[nonterminal]) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}table[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)}}] = {
  {% py parseTable = grammar.getParseTable() %}
  {% for i in range(len(grammar.nonterminals)) %}
  { {{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}} },
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}nud_ast_types[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule, ExprRule) and isinstance(rule.nudAst, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}ast_types[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

static AST_CREATE_OBJECT_INIT {{prefix}}nud_ast_objects[] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule, ExprRule) and rule.nudAst and isinstance(rule.nudAst, AstSpecification) %}
      {% for i, key in enumerate(rule.nudAst.parameters.keys()) %}
  { {{rule.id}}, "{{rule.nudAst.name}}", "{{key}}", {{rule.nudAst.parameters[key] if rule.nudAst.parameters[key] != '$' else "'$'"}} },
      {% endfor %}

      {% if not len(rule.nudAst.parameters) %}
  { {{rule.id}}, "{{rule.nudAst.name}}", "", 0},
      {% endif %}
    {% endif %}
  {% endfor %}
  {0}
};

static AST_CREATE_OBJECT_INIT {{prefix}}ast_objects[] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
      {% for i, key in enumerate(rule.ast.parameters.keys()) %}
  { {{rule.id}}, "{{rule.ast.name}}", "{{key}}", {{rule.ast.parameters[key] if rule.ast.parameters[key] != '$' else "'$'"}} },
      {% endfor %}

      {% if not len(rule.ast.parameters) %}
  { {{rule.id}}, "{{rule.ast.name}}", "", 0},
      {% endif %}
    {% endif %}
  {% endfor %}
  {0}
};

static int {{prefix}}ast_index[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
  {{rule.ast.idx if isinstance(rule.ast, AstTranslation) else 0}}, /* ({{rule.id}}) {{rule}} */
  {% endfor %}
};

static int {{prefix}}nud_ast_index[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
  {{rule.nudAst.idx if isinstance(rule, ExprRule) and isinstance(rule.nudAst, AstTranslation) else 0}}, /* ({{rule.id}}) {{rule}} */
  {% endfor %}
};

static int
in_array(int * array, int element )
{
  /* -2 terminated arrays */
  int i;
  for ( i=0; array[i] != -2; i++ )
  {
    if ( array[i] == element )
      return 1;
  }
  return 0;
}

static int
advance(PARSER_CONTEXT_T * ctx)
{
  TOKEN_LIST_T * token_list = ctx->tokens;
  if ( token_list->current_index == token_list->ntokens )
  {
    return {{prefix.upper()}}TERMINAL_END_OF_STREAM;
  }
  token_list->current_index += 1;
  token_list->current = token_list->tokens[token_list->current_index].terminal->id;
  return token_list->current;
}

static TOKEN_T *
expect(int terminal_id, PARSER_CONTEXT_T * ctx)
{
  int current, next;
  TOKEN_T * current_token;
  TOKEN_LIST_T * token_list = ctx->tokens;
  char * message, * fmt;

  if ( token_list == NULL || token_list->current == {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    fmt = "No more tokens.  Expecting %s";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(terminal_id)) + 1, sizeof(char) );
    sprintf(message, fmt, {{prefix}}morpheme_to_str(terminal_id));
    syntax_error(ctx, message);
  }

  current = token_list->tokens[token_list->current_index].terminal->id;
  current_token = &token_list->tokens[token_list->current_index];

  if ( current != terminal_id )
  {
    char * token_string = (current != {{prefix.upper()}}TERMINAL_END_OF_STREAM) ?  token_to_string(current_token, 0, ctx) : strdup("(end of stream)");
    fmt = "Unexpected symbol (line %d, col %d) when parsing %s.  Expected %s, got %s.";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(terminal_id)) + strlen(token_string) + strlen(ctx->current_function) + 20, sizeof(char) );
    sprintf(message, fmt, current_token->lineno, current_token->colno, ctx->current_function, {{prefix}}morpheme_to_str(terminal_id), token_string);
    free(token_string);
    syntax_error(ctx, message);
  }

  next = advance(ctx);

  if ( next != {{prefix.upper()}}TERMINAL_END_OF_STREAM && !{{prefix.upper()}}IS_TERMINAL(next) )
  {
    fmt = "Invalid symbol ID: %d (%s)";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(next)) + 10, sizeof(char) );
    sprintf(message, fmt, next, {{prefix}}morpheme_to_str(next));
    syntax_error(ctx, message);
  }

  return current_token;
}

static PARSETREE_TO_AST_CONVERSION_T *
get_default_ast_converter()
{
  PARSETREE_TO_AST_CONVERSION_T * converter = NULL;
  AST_RETURN_INDEX_T * ast_return_index;

  converter = calloc(1, sizeof(PARSETREE_TO_AST_CONVERSION_T));
  ast_return_index = calloc(1, sizeof(AST_RETURN_INDEX_T));
  ast_return_index->index = 0;
  converter->type = AST_RETURN_INDEX;
  converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_return_index;
  return converter;
}

static PARSETREE_TO_AST_CONVERSION_T *
_get_ast_converter(int rule_id, PARSETREE_TO_AST_CONVERSION_TYPE_E * ast_types, AST_CREATE_OBJECT_INIT * ast_objects, int * ast_index)
{
  PARSETREE_TO_AST_CONVERSION_T * converter = NULL;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;
  AST_RETURN_INDEX_T * ast_return_index;
  PARSETREE_TO_AST_CONVERSION_TYPE_E conversion_type;
  int i, j, nattrs;

  converter = calloc(1, sizeof(PARSETREE_TO_AST_CONVERSION_T));
  conversion_type = ast_types[rule_id];

  /* Create map (rule_id -> PARSETREE_TO_AST_CONVERSION_T) if it doesn't exist.  Then return result */
  if (conversion_type == AST_RETURN_INDEX)
  {
    ast_return_index = calloc(1, sizeof(AST_RETURN_INDEX_T));
    ast_return_index->index = ast_index[rule_id];
    converter->type = AST_RETURN_INDEX;
    converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_return_index;
  }
  
  if (conversion_type == AST_CREATE_OBJECT)
  {
    ast_object_spec = calloc(1, sizeof(AST_OBJECT_SPECIFICATION_T));
    for ( i = 0, nattrs = 0; ast_objects[i].name != NULL; i++ )
    {
      if ( ast_objects[i].rule_id == rule_id )
        nattrs += 1;
    }

    ast_object_spec->attrs = calloc(nattrs, sizeof(AST_OBJECT_ATTR_T));
    ast_object_spec->nattrs = nattrs;

    for ( i = 0, j = 0; ast_objects[i].name != NULL; i++ )
    {
      if ( ast_objects[i].rule_id == rule_id )
      {
        ast_object_spec->name = ast_objects[i].name;
        ast_object_spec->attrs[j].name = ast_objects[i].attr;
        ast_object_spec->attrs[j].index = ast_objects[i].index;
        j += 1;
      }
    }
    converter->type = AST_CREATE_OBJECT;
    converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_object_spec;
  }

  return converter;
}

static PARSETREE_TO_AST_CONVERSION_T *
get_nud_ast_converter(int rule_id)
{
  return _get_ast_converter(rule_id, &{{prefix}}nud_ast_types[0], &{{prefix}}nud_ast_objects[0], &{{prefix}}nud_ast_index[0]);
}

static PARSETREE_TO_AST_CONVERSION_T *
get_ast_converter(int rule_id)
{
  return _get_ast_converter(rule_id, &{{prefix}}ast_types[0], &{{prefix}}ast_objects[0], &{{prefix}}nud_ast_index[0]);
}

{% for exprGrammar in grammar.exprgrammars %}
{% py name = exprGrammar.nonterminal.string.lower() %}

static int infixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in exprGrammar.rules if rule.operator and rule.operator.associativity in ['left', 'right']} %}

  {% for i in range(len(grammar.terminals)) %}
  {{0 if i not in operators else operators[i]}},
  {% endfor %}
};

static int prefixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in exprGrammar.rules if rule.operator and rule.operator.associativity in ['unary']} %}

  {% for i in range(len(grammar.terminals)) %}
  {{0 if i not in operators else operators[i]}},
  {% endfor %}
};

static int
getInfixBp_{{name}}(int id)
{
  return infixBp_{{name}}[id];
}

static int
getPrefixBp_{{name}}(int id)
{
  return prefixBp_{{name}}[id];
}

static PARSE_TREE_T *
nud_{{name}}(PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  int current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  current = list->current;

  if ( list == NULL )
  {
    tree->ast_converter = get_default_ast_converter();
    return tree;
  }

  {% for i, rule in enumerate(grammar.grammar_expanded_rules[exprGrammar]) %}
    {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

    {% if len(ruleFirstSet) %}
  if ( {{' || '.join(['current == %d' % (x.id) for x in ruleFirstSet])}} )
  {
    // {{rule}}
    tree->ast_converter = get_nud_ast_converter({{rule.id}});
    tree->nchildren = {{len(rule.nudProduction)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nudProduction)}};
    {% for index, morpheme in enumerate(rule.nudProduction.morphemes) %}
      {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect({{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
    {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}

        {% if isinstance(rule.operator, PrefixOperator) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) _parse_{{rule.nonterminal.string.lower()}}( getPrefixBp_{{name}}({{rule.operator.operator.id}}) - modifier, ctx );
    tree->isPrefix = 1;
        {% else %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{rule.nonterminal.string.lower()}}(ctx);
        {% endif %}

    {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
      {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.start_nt.string.lower()}}(ctx);
      {% endif %}
    {% endfor %}
    return tree;
  }
  {% endif %}
  {% endfor %}

  tree->ast_converter = get_default_ast_converter();
  return tree;
}

static PARSE_TREE_T *
led_{{name}}(PARSE_TREE_T * left, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  int current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% py seen = list() %}

  {% for rule in grammar.grammar_expanded_expr_rules[exprGrammar] %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) and led[0] not in seen %}
  {{'if' if len(seen)==0 else 'else if'}} ( current == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nudProduction) == 1 and isinstance(rule.nudProduction.morphemes[0], NonTerminal) %}
      {% py nt = rule.nudProduction.morphemes[0] %}
      {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
    tree->isExprNud = 1; 
      {% endif %}
    {% endif %}

    tree->children[0].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[0].object = (PARSE_TREE_NODE_U *) left;

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in exprGrammar.rules if rule.operator} %}
      {% for index, morpheme in enumerate(led) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) expect( {{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
    modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
          {% if isinstance(rule.operator, InfixOperator) %}
    tree->isInfix = 1;
          {% endif %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) _parse_{{rule.nonterminal.string.lower()}}( getInfixBp_{{name}}({{rule.operator.operator.id}}) - modifier, ctx );
        {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
        {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.start_nt.string.lower()}}(ctx);
        {% endif %}
      {% endfor %}
      {% py seen.append(led[0]) %}
  }
    {% endif %}
  {% endfor %}

  return tree;
}
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}

static PARSE_TREE_T *
parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  int current;
  TOKEN_LIST_T * tokens = ctx->tokens;
  PARSE_TREE_T * tree, * subtree;
  char * message, * fmt;
  int rule = -1;

  ctx->current_function = "parse_{{nonterminal.string.lower()}}";

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}};

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
  tree->list = "slist";
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
  tree->list = "nlist";
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
  tree->list = "tlist";
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
  tree->list = "mlist";
    {% else %}
  tree->list = NULL;
    {% endif %}

  if ( tokens != NULL )
  {
    current = tokens->current;
    rule = {{prefix}}table[{{nonterminal.id - len(grammar.standard_terminals)}}][current];
    {% if grammar.is_empty(nonterminal) %}
    if ( in_array({{prefix}}follow[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) &&
         !in_array({{prefix}}first[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current))
    {
      return tree;
    }
    {% endif %}
  }

  if ( tokens == NULL || current == {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    {% if grammar.is_empty(nonterminal) or grammar._empty in grammar.first[nonterminal] %}
    return tree;
    {% else %}
    syntax_error(ctx, strdup("Error: unexpected end of file"));
    {% endif %}
  }

    {% for index0, rule in enumerate(filter(lambda r: not r.is_empty, grammar.getExpandedLL1Rules(nonterminal))) %}
      {% if index0 == 0 %}
  if ( rule == {{rule.id}} )
      {% else %}
  else if ( rule == {{rule.id}} )
      {% endif %}
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->children = calloc({{len(rule.production.morphemes)}}, sizeof(PARSE_TREE_NODE_T));
    tree->nchildren = {{len(rule.production.morphemes)}};
      {% for index, morpheme in enumerate(rule.production.morphemes) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( {{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% if isinstance(nonterminal.macro, SeparatedListMacro) and nonterminal.macro.separator == morpheme %}
    tree->listSeparator = tree->children[{{index}}].object;
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
        {% endif %}
      {% endfor %}

    return tree;
  }
    {% endfor %}

    {% for exprGrammar in grammar.exprgrammars %}
      {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
        {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}

  else if ( in_array({{prefix}}first[{{prefix.upper()}}NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) )
  {
    tree->ast_converter = get_ast_converter({{rule.id}});

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( {{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
          {% endif %}
        {% endfor %}
  }
      {% endif %}
    {% endfor %}

    {% if not grammar.is_empty(nonterminal) %}
  fmt = "Error: Unexpected symbol (%s) when parsing %s";
  message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index].terminal->id)) + strlen("parse_{{nonterminal.string.lower()}}") + 1, sizeof(char) );
  sprintf(message, fmt, {{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index].terminal->id), "parse_{{nonterminal.string.lower()}}");
  syntax_error(ctx, message);
  return NULL;
    {% else %}
  return tree;
    {% endif %}
}
{% endfor %}

#define HAS_MORE_TOKENS(ctx) (ctx->tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM)

{% for exprGrammar in grammar.exprgrammars %}

#define {{exprGrammar.nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) (rbp < getInfixBp_{{exprGrammar.nonterminal.string.lower()}}(ctx->tokens->current))

static PARSE_TREE_T *
_parse_{{exprGrammar.nonterminal.string.lower()}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{exprGrammar.nonterminal.string.lower()}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( HAS_MORE_TOKENS(ctx) && {{exprGrammar.nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) )
  {
    left = led_{{exprGrammar.nonterminal.string.lower()}}(left, ctx);
  }

  if ( left != NULL )
  {
    left->isExpr = 1;
  }

  return left;
}

static PARSE_TREE_T *
parse_{{exprGrammar.nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  ctx->current_function = "parse_{{exprGrammar.nonterminal.string.lower()}}";
  return _parse_{{exprGrammar.nonterminal.string.lower()}}(0, ctx);
}
{% endfor %}

typedef PARSE_TREE_T * (*parse_function)(PARSER_CONTEXT_T *);

static parse_function
functions[{{len(grammar.nonterminals)}}] = {

  {% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  parse_{{nonterminal.string.lower()}},
  {% endfor %}

};

PARSER_CONTEXT_T *
{{prefix}}parser_init( TOKEN_LIST_T * tokens )
{
  PARSER_CONTEXT_T * ctx;
  ctx = calloc(1, sizeof(PARSER_CONTEXT_T));
  ctx->tokens = tokens;
  ctx->morpheme_to_str = {{prefix}}morpheme_to_str;
  tokens->current_index = 0;
  tokens->current = tokens->tokens[0].terminal->id;
  return ctx;
}

void
{{prefix}}parser_exit( PARSER_CONTEXT_T * ctx)
{
  SYNTAX_ERROR_T * error, * next;
  for ( error = ctx->syntax_errors; error != NULL; error = next )
  {
    next = error->next;
    free(error->message);
    free(error);
  }
  free(ctx);
}

void
syntax_error( PARSER_CONTEXT_T * ctx, char * message )
{
  SYNTAX_ERROR_T * syntax_error = calloc(1, sizeof(SYNTAX_ERROR_T));
  syntax_error->message = message;
  syntax_error->terminal = ctx->tokens->tokens[ctx->tokens->current_index].terminal;
  syntax_error->next = NULL;

  if ( ctx->syntax_errors == NULL )
  {
    ctx->syntax_errors = syntax_error;
  }
  else
  {
    ctx->last->next = syntax_error;
  }

  ctx->last = syntax_error;
}

PARSE_TREE_T *
{{prefix}}parse(TOKEN_LIST_T * tokens, int start, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;

  if ( start == -1 )
    start = {{prefix.upper()}}NONTERMINAL_{{grammar.start.string.upper()}};

  tree = functions[start - {{len(grammar.standard_terminals)}}](ctx);

  if ( tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    syntax_error(ctx, strdup("Finished parsing without consuming all tokens."));
  }

  return tree;
}

char *
{{prefix}}morpheme_to_str(int id)
{
  if ( id == -1 ) return "<end of stream>";
  return {{prefix}}morphemes[id];
}

int
{{prefix}}str_to_morpheme(const char * str)
{
  {% for terminal in grammar.standard_terminals %}
  if ( !strcmp(str, "{{terminal.string}}") )
    return {{terminal.id}};
  {% endfor %}

  {% for nonterminal in grammar.nonterminals %}
  if ( !strcmp(str, "{{nonterminal.string}}") )
    return {{nonterminal.id}};
  {% endfor %}
  
  return -1;
}

ABSTRACT_SYNTAX_TREE_T *
{{prefix}}ast( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return parsetree_node_to_ast(&node);
}
