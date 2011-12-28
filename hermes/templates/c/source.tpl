{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.h"

{% for nonterminal in LL1Nonterminals %}
static PARSE_TREE_T * parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
static PARSE_TREE_T * parse_{{exprGrammar.nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
static PARSE_TREE_T * _parse_{{exprGrammar.nonterminal.string.lower()}}(int, PARSER_CONTEXT_T *);
{% endfor %}

void
syntax_error( PARSER_CONTEXT_T * ctx, char * message );

static ABSTRACT_SYNTAX_TREE_T *
_parsetree_node_to_ast( PARSE_TREE_NODE_T * node );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_normal( PARSE_TREE_NODE_T * node );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_expr( PARSE_TREE_NODE_T * node );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node );

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent );

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent );

static char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent );

void
_free_parse_tree( PARSE_TREE_NODE_T * node );

typedef struct ast_object_specification_init {
  int rule_id;
  char * name;
  char * attr;
  int index;
} AST_CREATE_OBJECT_INIT;

/* index with TERMINAL_E or NONTERMINAL_E */
static char * morphemes[] = {
{% for terminal in sorted(nonAbstractTerminals, key=lambda x: x.id) %}
  "{{terminal.string}}", /* {{terminal.id}} */
{% endfor %}

{% for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.id) %}
  "{{nonterminal.string}}", /* {{nonterminal.id}} */
{% endfor %}
};

static char *
nonterminal_to_str(NONTERMINAL_E nonterminal)
{
  return morphemes[nonterminal];
}

static char *
terminal_to_str(TERMINAL_E terminal)
{
  return morphemes[terminal];
}

static int first[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.first[nonterminal]])}}{{', ' if len(grammar.first[nonterminal]) else ''}}-2 },
{% endfor %}
};

static int follow[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.follow[nonterminal]])}}{{', ' if len(grammar.follow[nonterminal]) else ''}}-2 },
{% endfor %}
};

static int table[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)}}] = {
  {% py parseTable = grammar.getParseTable() %}
  {% for i in range(len(grammar.nonterminals)) %}
  { {{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}} },
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

static TERMINAL_E
advance(PARSER_CONTEXT_T * ctx)
{
  TOKEN_LIST_T * token_list = ctx->tokens;
  if ( token_list->current_index == token_list->ntokens )
  {
    return TERMINAL_END_OF_STREAM;
  }
  token_list->current_index += 1;
  token_list->current = token_list->tokens[token_list->current_index].id;
  return token_list->current;
}

static TERMINAL_T *
expect(TERMINAL_E terminal_id, PARSER_CONTEXT_T * ctx)
{
  TERMINAL_E current, next;
  TERMINAL_T * current_token;
  TOKEN_LIST_T * token_list = ctx->tokens;
  char * message, * fmt;

  if ( token_list == NULL || token_list->current == TERMINAL_END_OF_STREAM )
  {
    fmt = "No more tokens.  Expecting %s";
    message = calloc( strlen(fmt) + strlen(terminal_to_str(terminal_id)) + 1, sizeof(char) );
    sprintf(message, fmt, terminal_to_str(terminal_id));
    syntax_error(ctx, message);
  }

  current = token_list->tokens[token_list->current_index].id;
  if ( current != terminal_id )
  {
    fmt = "Unexpected symbol when parsing %s.  Expected %s, got %s.";
    message = calloc( strlen(fmt) + strlen(terminal_to_str(terminal_id)) + strlen(terminal_to_str(current)) + strlen(ctx->current_function) + 1, sizeof(char) );
    sprintf(message, fmt, ctx->current_function, terminal_to_str(terminal_id), current ? terminal_to_str(current) : "None");
    syntax_error(ctx, message);
  }

  current_token = &token_list->tokens[token_list->current_index];
  next = advance(ctx);

  if ( next != TERMINAL_END_OF_STREAM && !IS_TERMINAL(next) )
  {
    fmt = "Invalid symbol ID: %d (%s)";
    message = calloc( strlen(fmt) + strlen(terminal_to_str(next)) + 10, sizeof(char) );
    sprintf(message, fmt, next, terminal_to_str(next));
    syntax_error(ctx, message);
  }

  return current_token;
}

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E ast_types[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

static AST_CREATE_OBJECT_INIT ast_objects[] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
      {% for i, key in enumerate(rule.ast.parameters.keys()) %}
  { {{rule.id}}, "{{rule.ast.name}}", "{{key}}", {{rule.ast.parameters[key] if rule.ast.parameters[key] != '$' else "'$'"}} },
      {% endfor %}
    {% endif %}
  {% endfor %}
  {0}
};

static int ast_index[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
  {{rule.ast.idx if isinstance(rule.ast, AstTranslation) else 0}},
  {% endfor %}
};

static PARSETREE_TO_AST_CONVERSION_T *
get_ast_converter(int rule_id)
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

{% for exprGrammar in grammar.exprgrammars %}

static int infixBp_{{exprGrammar.nonterminal.string.lower()}}[{{len(grammar.terminals)}}] = {
  {% for i in range(len(grammar.terminals)) %}{{0 if i not in exprGrammar.infix else exprGrammar.infix[i]}}, {% endfor %}
};

static int prefixBp_{{exprGrammar.nonterminal.string.lower()}}[{{len(grammar.terminals)}}] = {
  {% for i in range(len(grammar.terminals)) %}{{0 if i not in exprGrammar.prefix else exprGrammar.prefix[i]}}, {% endfor %}
};

{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
{% py name = exprGrammar.nonterminal.string.lower() %}

static int
getInfixBp_{{name}}(TERMINAL_E id)
{
  return infixBp_{{name}}[id];
}

static int
getPrefixBp_{{name}}(TERMINAL_E id)
{
  return prefixBp_{{name}}[id];
}

static PARSE_TREE_T *
nud_{{name}}(PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  TERMINAL_E current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = _NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  current = list->current;

  if ( list == NULL )
    return tree;

  {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
    {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

    {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

    {% if len(ruleFirstSet) and not isOptional %}
  {{'if' if i == 0 else 'else if'}} ( {{' || '.join(['current == %d' % (x.id) for x in exprGrammar.ruleFirst(rule)])}} )
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(rule.nudProduction)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nudProduction)}};
    {% for index, morpheme in enumerate(rule.nudProduction.morphemes) %}
      {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( _TERMINAL_{{morpheme.string.upper()}}, ctx );
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
  }
  {% endif %}
  {% endfor %}

  return tree;
}

static PARSE_TREE_T *
led_{{name}}(PARSE_TREE_T * left, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  TERMINAL_E current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = _NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% py seen = list() %}
  {% for rule in exprGrammar.getExpandedExpressionRules() %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) and led[0] not in seen %}
  {{'if' if len(seen)==0 else 'else if'}} ( current == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nudProduction) == 1 and rule.nudProduction.morphemes[0] == rule.nonterminal%}
    tree->isExprNud = 1; 
    {% endif %}

    tree->children[0].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[0].object = left;

      {% for index, morpheme in enumerate(led) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) expect( _TERMINAL_{{morpheme.string.upper()}}, ctx );
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
    modifier = {{1 if rule.operator.operator.id in exprGrammar.precedence and exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}};
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

{% for nonterminal in LL1Nonterminals %}

static PARSE_TREE_T *
parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  TERMINAL_E current;
  TOKEN_LIST_T * tokens = ctx->tokens;
  PARSE_TREE_T * tree, * subtree;
  char * message, * fmt;
  int rule = -1;

  ctx->current_function = "parse_{{nonterminal.string.lower()}}";

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = _NONTERMINAL_{{nonterminal.string.upper()}};

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
  tree->list = "slist";
    {% elif isinstance(nonterminal.macro, NonterminalListMacro) %}
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
    rule = table[{{nonterminal.id - len(nonAbstractTerminals)}}][current];
    {% if nonterminal.empty %}
    if ( in_array(follow[_NONTERMINAL_{{nonterminal.string.upper()}} - {{len(nonAbstractTerminals)}}], current))
    {
      return tree;
    }
    {% endif %}
  }

  if ( tokens == NULL || current == TERMINAL_END_OF_STREAM )
  {
    {% if nonterminal.empty or grammar.ε in grammar.first[nonterminal] %}
    return tree;
    {% else %}
    syntax_error(ctx, strdup("Error: unexpected end of file"));
    {% endif %}
  }

    {% for index0, rule in enumerate(nonterminal.rules) %}
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
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( _TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
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

  else if ( in_array(first[_NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}} - {{len(nonAbstractTerminals)}}], current) )
  {
    tree->ast_converter = get_ast_converter({{rule.id}});

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( _TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
          {% endif %}
        {% endfor %}
  }
      {% endif %}
    {% endfor %}

    {% if not nonterminal.empty %}
  fmt = "Error: Unexpected symbol (%s) when parsing %s";
  message = calloc( strlen(fmt) + strlen(terminal_to_str(tokens->tokens[tokens->current_index].id)) + strlen("parse_{{nonterminal.string.lower()}}") + 1, sizeof(char) );
  sprintf(message, fmt, terminal_to_str(tokens->tokens[tokens->current_index].id), "parse_{{nonterminal.string.lower()}}");
  syntax_error(ctx, message);
  return NULL;
    {% else %}
  return tree;
    {% endif %}
}
{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
static PARSE_TREE_T *
_parse_{{exprGrammar.nonterminal.string.lower()}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{name}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( ctx->tokens->current && rbp < getInfixBp_{{exprGrammar.nonterminal.string.lower()}}(ctx->tokens->current) )
  {
    left = led_{{name}}(left, ctx);
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
parser_init( TOKEN_LIST_T * tokens )
{
  PARSER_CONTEXT_T * ctx;
  ctx = calloc(1, sizeof(PARSER_CONTEXT_T));
  ctx->tokens = tokens;
  tokens->current_index = 0;
  tokens->current = tokens->tokens[0].id;
  return ctx;
}

void
parser_exit( PARSER_CONTEXT_T * ctx)
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
  syntax_error->terminal = &ctx->tokens->tokens[ctx->tokens->current_index];
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
parse(TOKEN_LIST_T * tokens, NONTERMINAL_E start, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;

  if ( start == -1 )
    start = _NONTERMINAL_{{grammar.start.string.upper()}};

  tree = functions[start - {{len(nonAbstractTerminals)}}](ctx);

  if ( tokens->current != TERMINAL_END_OF_STREAM )
  {
    syntax_error(ctx, strdup("Finished parsing without consuming all tokens."));
  }

  return tree;
}

ABSTRACT_SYNTAX_TREE_T *
parsetree_to_ast( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return _parsetree_node_to_ast(&node);
}

static ABSTRACT_SYNTAX_TREE_T *
_parsetree_node_to_ast( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  PARSE_TREE_T * tree;

  if ( node == NULL ) return NULL;

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast->type = AST_NODE_TYPE_TERMINAL;
    ast->object = (AST_NODE_U *) node->object;
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->list && strlen(tree->list) )
    {
      ast = __parsetree_node_to_ast_list(node);
    }
    else if ( tree->isExpr )
    {
      ast = __parsetree_node_to_ast_expr(node);
    }
    else
    {
      ast = __parsetree_node_to_ast_normal(node);
    }
  }

  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  AST_LIST_T * lnode, * tail, * ast_list;
  ABSTRACT_SYNTAX_TREE_T * this, * next;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  int offset, i;

  if ( tree->nchildren == 0 )
    return NULL;

  ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
  ast->type = AST_NODE_TYPE_LIST;
  ast->object = NULL;

  if ( !strcmp(tree->list, "slist") || !strcmp(tree->list, "nlist") )
  {
    offset = (tree->children[0].object == tree->listSeparator) ? 1 : 0;
    this = _parsetree_node_to_ast(&tree->children[offset]);
    next = _parsetree_node_to_ast(&tree->children[offset + 1]);

    ast_list = NULL;
    if ( this != NULL )
    {
      ast_list = calloc(1, sizeof(AST_LIST_T));
      ast_list->tree = this;
      ast_list->next = NULL;

      if ( next != NULL )
      {
        ast_list->next = (AST_LIST_T *) next->object;
      }
    }

    if ( next ) free(next);
  }
  else if ( !strcmp(tree->list, "tlist") )
  {
    this = _parsetree_node_to_ast(&tree->children[0]);
    next = _parsetree_node_to_ast(&tree->children[2]);

    ast_list = NULL;
    if ( this != NULL )
    {
      ast_list = calloc(1, sizeof(AST_LIST_T));
      ast_list->tree = this;
      ast_list->next = NULL;

      if ( next != NULL )
      {
        ast_list->next = (AST_LIST_T *) next->object;
      }
    }

    if ( next ) free(next);
  }
  else if ( !strcmp(tree->list, "mlist") )
  {
    lnode = ast_list = tail = NULL;
    for ( i = 0; i < tree->nchildren - 1; i++ )
    {
      lnode = calloc(1, sizeof(AST_LIST_T));
      lnode->tree = _parsetree_node_to_ast(&tree->children[i]);

      if ( ast_list == NULL )
      {
        ast_list = tail = lnode;
        continue;
      }

      tail->next = (AST_LIST_T *) lnode;
      tail = tail->next;
    }
    next = _parsetree_node_to_ast(&tree->children[tree->nchildren - 1]);
    tail->next = (next != NULL) ? next->object : NULL;
  }

  ast->object = (AST_NODE_U *) ast_list;
  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_expr( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object, * first;
  AST_OBJECT_T * ast_object;
  PARSETREE_TO_AST_CONVERSION_T * ast_converter = tree->ast_converter;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) ast_converter->object;
  AST_RETURN_INDEX_T * ast_return_index = (AST_RETURN_INDEX_T *) ast_converter->object;
  PARSE_TREE_NODE_T * child;
  int index, i;

  if ( tree->ast_converter->type == AST_RETURN_INDEX )
  {
    ast = _parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( tree->ast_converter->type == AST_CREATE_OBJECT )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name) + 1, sizeof(char));
    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));

    strcpy(ast_object->name, ast_object_spec->name);
    ast_object->nchildren = ast_object_spec->nattrs;

    ast->object = (AST_NODE_U *) ast_object;
    ast->type = AST_NODE_TYPE_OBJECT;

    for ( i = 0; i < ast_object_spec->nattrs; i++ )
    {
      ast_object->children[i].name = ast_object_spec->attrs[i].name;
      index = ast_object_spec->attrs[i].index;

      /* TODO: omg seriously? */
      if ( index == '$' )
      {
        child = &tree->children[0];
      }
      else if ( tree->children[0].type == PARSE_TREE_NODE_TYPE_PARSETREE &&
                ((PARSE_TREE_T *) tree->children[0].object)->isNud &&
                !((PARSE_TREE_T *) tree->children[0].object)->isPrefix &&
                !tree->isExprNud &&
                !tree->isInfix )
      {
        first = (PARSE_TREE_T *) tree->children[0].object;
        if ( index < first->nudMorphemeCount )
        {
          child = &first->children[index];
        }
        else
        {
          child = &tree->children[index - first->nudMorphemeCount + 1];
        }
      }
      else if ( tree->nchildren == 1 && tree->children[0].type != PARSE_TREE_NODE_TYPE_PARSETREE )
      {
        return _parsetree_node_to_ast( &tree->children[0] );
      }
      else
      {
        child = &tree->children[index];
      }

      ast_object->children[i].tree = _parsetree_node_to_ast(child);
    }

    return ast;
  }

  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_normal( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  AST_OBJECT_T * ast_object;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  PARSETREE_TO_AST_CONVERSION_TYPE_E ast_conversion_type;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;
  AST_RETURN_INDEX_T * ast_return_index;
  AST_RETURN_INDEX_T default_action = { .index = 0 };
  int i;

  if ( tree->ast_converter )
  {
    ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) tree->ast_converter->object;
    ast_return_index = (AST_RETURN_INDEX_T *) tree->ast_converter->object;
    ast_conversion_type = tree->ast_converter->type;
  }
  else
  {
    ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) NULL;
    ast_return_index = (AST_RETURN_INDEX_T *) &default_action;
    ast_conversion_type = AST_RETURN_INDEX;
  }

  if ( ast_conversion_type == AST_RETURN_INDEX )
  {
    ast = _parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( ast_conversion_type == AST_CREATE_OBJECT )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name)+1, sizeof(char));
    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));

    strcpy( ast_object->name, ast_object_spec->name );
    ast_object->nchildren = ast_object_spec->nattrs;

    ast->object = (AST_NODE_U *) ast_object;
    ast->type = AST_NODE_TYPE_OBJECT;

    for ( i = 0; i < ast_object_spec->nattrs; i++ )
    {
      ast_object->children[i].name = ast_object_spec->attrs[i].name;
      ast_object->children[i].tree = _parsetree_node_to_ast(&tree->children[ast_object_spec->attrs[i].index]);
    }
  }

  return ast;
}

static char *
_get_indent_str(int length)
{
  char * str = malloc(length + 1 * sizeof(char));
  memset(str, ' ', length);
  str[length] = '\0';
  return str;
}

char *
parsetree_to_string( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  char * str;

  if ( tree == NULL )
  {
    str = calloc(3, sizeof(char));
    strcpy(str, "()");
    return str;
  }

  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return _parsetree_to_string(&node, 0);
}

static int
_parsetree_to_string_bytes( PARSE_TREE_NODE_T * node, int indent )
{
  PARSE_TREE_T * tree;
  TERMINAL_T * terminal;
  int bytes, i;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      /* format: "(nonterminal: )" */
      return 4 + strlen(nonterminal_to_str(tree->nonterminal));
    }
    else
    {
      bytes = (5 + indent + strlen(nonterminal_to_str(tree->nonterminal)));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        bytes += 2 + indent + _parsetree_to_string_bytes(&tree->children[i], indent + 2);
      }
      bytes += (tree->nchildren - 1) * 2;
      return bytes;
    }
  }
  
  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    return strlen(terminal_to_str(terminal->id));
  }

  return -1;
}

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent )
{
  PARSE_TREE_T * tree;
  TERMINAL_T * terminal;
  char * str, * tmp, * indent_str;
  int bytes, i, len;

  bytes = _parsetree_to_string_bytes(node, indent);
  bytes += 1; /* null bytes */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      snprintf(str, bytes, "(%s: )", nonterminal_to_str(tree->nonterminal));
    }
    else
    {
      indent_str = _get_indent_str(indent);
      snprintf(str, bytes, "(%s:\n", nonterminal_to_str(tree->nonterminal));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        if ( i != 0 )
        {
          strcat(str, ",\n");
        }

        len = strlen(str);
        tmp = _parsetree_to_string(&tree->children[i], indent + 2);
        snprintf(str + len, bytes - len, "%s  %s", indent_str, tmp);
        free(tmp);
      }
      len = strlen(str);
      snprintf(str + len, bytes - len, "\n%s)", indent_str);
      free(indent_str);
    }
    return str;
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    strcpy(str, terminal_to_str(terminal->id));
    return str;
  }

  return NULL;
}

static char *
_lstrip(char * string)
{
  char * tmp, * stripped;
  for ( tmp = string; *tmp == ' '; tmp++ );
  stripped = calloc(strlen(tmp) + 1, sizeof(char));
  strcpy(stripped, tmp);
  return stripped;
}

char *
ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree )
{
  return _ast_to_string(tree, 0);
}

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * list_node;
  TERMINAL_T * terminal;
  ABSTRACT_SYNTAX_TREE_T * child;
  char * attr;
  int i, bytes;
  int initial_indent = (indent < 0) ? 0 : indent;
  indent = (indent < 0) ? -indent : indent;

  if ( node == NULL ) return 4; /* "none" */

  if ( node->type == AST_NODE_TYPE_OBJECT )
  {
    ast_object = (AST_OBJECT_T *) node->object;

    /*  <initial_indent, '(', ast_object->name, ':', '\n', indent>  */
    bytes = (initial_indent + indent + strlen(ast_object->name) + 3);

    for ( i = 0; i < ast_object->nchildren; i++ )
    {
      if ( i != 0 )
        /* <',', '\n', indent> as the separator */
        bytes += (2 + indent);

      attr = ast_object->children[i].name;
      child = ast_object->children[i].tree;

      /* <' ', ' ', attr, '=', _ast_to_string_bytes(child)> */
      bytes += (2 + 1 + strlen(attr) + _ast_to_string_bytes(child, -(indent + 2)));
    }

    /*  <'\n', indent, ')'>  */
    bytes += (2 + indent);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list->tree == NULL )
    {
      return 2; /* "[]" */
    }

    /* <initial_indent, '[', '\n', indent> */
    bytes = (initial_indent + 2 + indent);

    for ( i = 0, list_node = ast_list; list_node && list_node->tree; i++, list_node = list_node->next )
    {
      if ( i != 0 )
        /* <',', '\n', indent> as the separator */
        bytes += (2 + indent);

      /* <' ', ' ', _ast_to_string_bytes(list_node->tree)> */
      bytes += 2 + _ast_to_string_bytes(list_node->tree, -(indent + 2));
    }

    /* <'\n', indent, ']'> */
    bytes += (indent + 2);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    return initial_indent + strlen(terminal_to_str(terminal->id));
  }

  return 4; /* "None" */
}

char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent )
{
  AST_LIST_T * ast_list, * lnode;
  AST_OBJECT_T * ast_object;
  TERMINAL_T * terminal;
  char * str, * key, * value, * indent_str, * tmp;
  int bytes, i;
  int initial_indent = (indent < 0) ? 0 : indent;
  indent = (indent < 0) ? -indent : indent;

  bytes = _ast_to_string_bytes(node, indent) + 1;
  str = calloc( bytes, sizeof(char) );

  if ( node == NULL )
  {
    strcpy(str, "None");
    return str;
  }

  if ( node->type == AST_NODE_TYPE_OBJECT )
  {
    indent_str = _get_indent_str(indent);
    ast_object = (AST_OBJECT_T *) node->object;
    snprintf(str, bytes,"%s(%s:\n", indent_str, ast_object->name);

    for ( i = 0; i < ast_object->nchildren; i++ )
    {
      if ( i != 0 )
        strcat(str, ",\n");

      key = ast_object->children[i].name;
      value = _ast_to_string(ast_object->children[i].tree, indent + 2);

      if ( *value == ' ' )
      {
        tmp = value;
        value = _lstrip(value);
        free(tmp);
      }

      snprintf(str + strlen(str), bytes - strlen(str), "%s  %s=%s", indent_str, key, value);
      free(value);
    }

    snprintf(str + strlen(str), bytes - strlen(str), "\n%s)", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list == NULL )
    {
      strcpy(str, "[]");
      return str;
    }
    
    snprintf(str, bytes, "[\n");
    for ( i = 0, lnode = ast_list; lnode && lnode->tree; i++, lnode = lnode->next )
    {
      value = _ast_to_string(lnode->tree, indent + 2);
      snprintf(str + strlen(str), bytes - strlen(str), "%s", value);
      if ( lnode->next != NULL )
        strcat(str, ",\n");
      free(value);
    }
    indent_str = _get_indent_str(indent);
    snprintf(str + strlen(str), bytes - strlen(str), "\n%s]", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    indent_str = "";
    if ( initial_indent )
      indent_str = _get_indent_str(indent);
    sprintf(str, "%s%s", indent_str, terminal_to_str(terminal->id));
    if ( initial_indent )
      free(indent_str);
    return str;
  }

  strcpy(str, "None");
  return str;
}

void
free_parse_tree( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;

  if ( tree == NULL )
    return;

  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  _free_parse_tree(&node);
}

void
_free_parse_tree( PARSE_TREE_NODE_T * node )
{
  int i;
  TERMINAL_T * terminal;
  PARSE_TREE_T * tree;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->ast_converter )
    {
      if ( tree->ast_converter->object )
      {
        if ( tree->ast_converter->type == AST_CREATE_OBJECT )
        {
          ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) tree->ast_converter->object;
          free(ast_object_spec->attrs);
        }
        free(tree->ast_converter->object);
      }

      free(tree->ast_converter);
    }

    for ( i = 0; i < tree->nchildren; i++ )
    {
      _free_parse_tree(&tree->children[i]);
    }

    free(tree->children);
    free(tree);
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    /* Terminals are provided by the user and don't need to be freed */
    terminal = (TERMINAL_T *) node->object;
  }
}

void
free_ast( ABSTRACT_SYNTAX_TREE_T * ast )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * current, * tmp;
  int i;
  
  if ( ast )
  {
    if ( ast->type == AST_NODE_TYPE_OBJECT )
    {
      ast_object = (AST_OBJECT_T *) ast->object;
      free(ast_object->name);

      for ( i = 0; i < ast_object->nchildren; i++ )
      {
        free_ast(ast_object->children[i].tree);
      }

      free(ast_object->children);
      free(ast_object);
    }
    
    if ( ast->type == AST_NODE_TYPE_LIST )
    {
      ast_list = (AST_LIST_T *) ast->object;

      for ( current = ast_list; current != NULL; current = current->next )
      {
        if ( current->tree != NULL )
          free_ast(current->tree);
      }

      current = ast_list;
      while ( current )
      {
        tmp = current;
        current = current->next;
        if ( tmp != NULL )
          free(tmp);
      }
    }

    if (ast->type == AST_NODE_TYPE_TERMINAL )
    {
      /* this data structure provided by the user */
    }

    free(ast);
  }
}

{% if addMain %}
int
main(int argc, char * argv[])
{
  PARSE_TREE_T * tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * ast;
  TOKEN_LIST_T token_list;
  SYNTAX_ERROR_T * error;
  char * str;

  {% if len(initialTerminals) %}

  TERMINAL_T tokens[{{len(initialTerminals)}} + 1] = {
    {% for terminal in initialTerminals %}
    {_TERMINAL_{{terminal.upper()}}, "" },
    {% endfor %}
    {TERMINAL_END_OF_STREAM, ""}
  };

  {% else %}

  TERMINAL_T tokens[1] = {
    {TERMINAL_END_OF_STREAM, ""}
  };

  {% endif %}

  token_list.tokens = tokens;
  token_list.ntokens = {{len(initialTerminals)}};
  token_list.current = tokens[0].id;
  token_list.current_index = 0;

  ctx = parser_init(&token_list);
  tree = parse(&token_list, -1, ctx);

  if ( ctx->syntax_errors )
  {
    for ( error = ctx->syntax_errors; error; error = error->next )
    {
      printf("%s\n", error->message);
      exit(1);
    }
  }

  if ( argc <= 1 || (argc > 1 && !strcmp(argv[1], "parsetree")) )
  {
    str = parsetree_to_string(tree);
  }
  else if ( argc > 1 && !strcmp(argv[1], "ast") )
  {
    ast = parsetree_to_ast(tree);
    str = ast_to_string(ast);
    free_ast(ast);
  }

  printf("%s", str);
  free_parse_tree(tree);
  parser_exit(ctx);
  if (str) free(str);

  return 0;
}
{% endif %}
