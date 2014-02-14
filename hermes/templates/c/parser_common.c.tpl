#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "parser_common.h"

static char *
_get_indent_str(int length)
{
  char * str = malloc(length + 1 * sizeof(char));
  memset(str, ' ', length);
  str[length] = '\0';
  return str;
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

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  AST_LIST_T * lnode, * tail, * ast_list;
  ABSTRACT_SYNTAX_TREE_T * this, * next;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  int offset, i;

  ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
  ast->type = AST_NODE_TYPE_LIST;
  ast->object = NULL;

  if ( tree->nchildren == 0 )
    return ast;

  if ( !strcmp(tree->list, "slist") || !strcmp(tree->list, "nlist") )
  {
    offset = (tree->children[0].object == tree->listSeparator) ? 1 : 0;
    this = parsetree_node_to_ast(&tree->children[offset]);
    next = parsetree_node_to_ast(&tree->children[offset + 1]);

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
    this = parsetree_node_to_ast(&tree->children[0]);
    next = parsetree_node_to_ast(&tree->children[2]);

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
      lnode->tree = parsetree_node_to_ast(&tree->children[i]);

      if ( ast_list == NULL )
      {
        ast_list = tail = lnode;
        continue;
      }

      tail->next = (AST_LIST_T *) lnode;
      tail = tail->next;
    }

    next = parsetree_node_to_ast(&tree->children[tree->nchildren - 1]);
    
    if ( next == NULL ) tail->next = NULL;
    else tail->next = (AST_LIST_T *) next->object;
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
    ast = parsetree_node_to_ast( &tree->children[ast_return_index->index] );
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
        return parsetree_node_to_ast( &tree->children[0] );
      }
      else
      {
        child = &tree->children[index];
      }

      ast_object->children[i].tree = parsetree_node_to_ast(child);
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
    ast = parsetree_node_to_ast( &tree->children[ast_return_index->index] );
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
      ast_object->children[i].tree = parsetree_node_to_ast(&tree->children[ast_object_spec->attrs[i].index]);
    }
  }

  return ast;
}

int
token_to_string_bytes(TOKEN_T * token, int indent, PARSER_CONTEXT_T * ctx) {
  /* format: "<identifier (line 0 col 0) ``>" */
  int source_string_len = token->source_string ? strlen(token->source_string) : 5;
  return indent + 1 + strlen(ctx->morpheme_to_str(token->terminal->id)) + 7 + 5 + 5 + 5 + 3 + source_string_len + 2;
}

char *
token_to_string(TOKEN_T * token, int indent, PARSER_CONTEXT_T * ctx)
{
  int bytes;
  char * str, * indent_str = "";

  bytes = token_to_string_bytes(token, indent, ctx);
  bytes += 1; /* null byte */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  if ( indent )
    indent_str = _get_indent_str(indent);

  sprintf(str, "%s<%s (line %d col %d) `%s`>", indent_str, ctx->morpheme_to_str(token->terminal->id), token->lineno, token->colno, token->source_string);

  if ( indent )
    free(indent_str);

  return str;
}

static int
_parsetree_to_string_bytes( PARSE_TREE_NODE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_T * tree;
  int bytes, i;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      /* format: "(nonterminal: )" */
      return 4 + strlen(ctx->morpheme_to_str(tree->nonterminal));
    }
    else
    {
      bytes = (5 + indent + strlen(ctx->morpheme_to_str(tree->nonterminal)));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        bytes += 2 + indent + _parsetree_to_string_bytes(&tree->children[i], indent + 2, ctx);
      }
      bytes += (tree->nchildren - 1) * 2;
      return bytes;
    }
  }
  
  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    return 2 + token_to_string_bytes( (TOKEN_T *) node->object, indent, ctx );
  }

  return -1;
}

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_T * tree;
  TOKEN_T * token;
  char * str, * tmp, * indent_str;
  int bytes, i, len;

  bytes = _parsetree_to_string_bytes(node, indent, ctx);
  bytes += 1; /* null byte */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      snprintf(str, bytes, "(%s: )", ctx->morpheme_to_str(tree->nonterminal));
    }
    else
    {
      indent_str = _get_indent_str(indent);
      snprintf(str, bytes, "(%s:\n", ctx->morpheme_to_str(tree->nonterminal));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        if ( i != 0 )
        {
          strcat(str, ",\n");
        }

        len = strlen(str);
        tmp = _parsetree_to_string(&tree->children[i], indent + 2, ctx);
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
    return token_to_string((TOKEN_T *) node->object, 0, ctx);
  }

  return NULL;
}

static void
_free_parse_tree( PARSE_TREE_NODE_T * node )
{
  int i;
  TOKEN_T * token;
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
    token = (TOKEN_T *) node->object;
  }
}

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * list_node;
  TOKEN_T * token;
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
      bytes += (2 + 1 + strlen(attr) + _ast_to_string_bytes(child, -(indent + 2), ctx));
    }

    /*  <'\n', indent, ')'>  */
    bytes += (2 + indent);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list == NULL || ast_list->tree == NULL )
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
      bytes += 2 + _ast_to_string_bytes(list_node->tree, -(indent + 2), ctx);
    }

    /* <'\n', indent, ']'> */
    bytes += (indent + 2);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    return initial_indent + token_to_string_bytes( (TOKEN_T *) node->object, indent, ctx );
  }

  return 4; /* "None" */
}

static char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  AST_LIST_T * ast_list, * lnode;
  AST_OBJECT_T * ast_object;
  TOKEN_T * token;
  char * str, * key, * value, * indent_str, * tmp;
  int bytes, i;
  int initial_indent = (indent < 0) ? 0 : indent;
  indent = (indent < 0) ? -indent : indent;

  bytes = _ast_to_string_bytes(node, indent, ctx) + 1;
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
      value = _ast_to_string(ast_object->children[i].tree, indent + 2, ctx);

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
      value = _ast_to_string(lnode->tree, indent + 2, ctx);
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
    return token_to_string((TOKEN_T *) node->object, indent, ctx);
  }

  strcpy(str, "None");
  return str;
}

char *
ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree, PARSER_CONTEXT_T * ctx )
{
  return _ast_to_string(tree, 0, ctx);
}

char *
parsetree_to_string( PARSE_TREE_T * tree, PARSER_CONTEXT_T * ctx )
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
  str = _parsetree_to_string(&node, 0, ctx);
  return str;
}

ABSTRACT_SYNTAX_TREE_T *
parsetree_node_to_ast( PARSE_TREE_NODE_T * node )
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
	if ( tree == NULL ) return NULL;
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

