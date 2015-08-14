{% if len(header)%}
/*
{{'\n'.join([' * ' + s for s in header.split('\n')])}}
 */
{% endif %}

{% from hermes.grammar import * %}

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

{% if add_main %}
#include <fcntl.h>
{% endif %}

{% if lexer %}
#include <pcre.h>
{% endif %}

#include "{{prefix.lower()}}parser.h"

#define TRUE 1
#define FALSE 0
#define MAX(a, b) ((a)>(b)) ? a : b

/* Section: utility functions */

#define READ_FILE_BUFFER_SIZE 256

static int
read_file( char ** content, FILE * fp )
{
    int content_len = READ_FILE_BUFFER_SIZE * 4;
    char buf[READ_FILE_BUFFER_SIZE];
    int bytes, total_bytes_read = 0;

    *content = calloc(content_len + 1, sizeof(char));

    while ( (bytes = fread(buf, sizeof(char), READ_FILE_BUFFER_SIZE, fp)) != 0 ) {
        if (content_len - total_bytes_read < READ_FILE_BUFFER_SIZE) {
            content_len *= 2;
            *content = realloc(*content, (content_len * sizeof(char)) + 1);
        }

        memcpy(*content + total_bytes_read, buf, bytes);
        total_bytes_read += bytes;
    }

    *(*content + total_bytes_read) = '\0';
    return total_bytes_read;
}

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

static void
_prepend(char * s, const char * t)
{
    size_t len = strlen(t);
    size_t i;

    memmove(s + len, s, strlen(s) + 1);

    for (i = 0; i < len; ++i) {
        s[i] = t[i];
    }
}

/* Section: Base64 encoding/decoding */

#define BASE64_OUTPUT_TOO_SMALL 1
#define BASE64_INPUT_EQUALS_OUTPUT 2
#define BASE64_INPUT_MALFORMED 3
#define BASE64_NULL_OUTPUT 4

static char * encoding_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static int mod_table[] = {0, 2, 1};

static int
decode_byte(char c)
{
    if (c >= 'A' && c <= 'Z') return c - 65; /* 0 - 25 */
    if (c >= 'a' && c <= 'z') return c - 71; /* 26 - 51 */
    if (c >= '0' && c <= '9')  return c + 4;  /* 52 - 61 */
    if (c == '+')             return 62;
    if (c == '/')             return 63;
    return 0;
}

static int
base64_encode(const char * input, size_t input_length, char * output, size_t output_length)
{
    int i, j, pad;
    size_t encoded_length = 4 * ((input_length + 2) / 3);
    if (encoded_length + 1 > output_length) return BASE64_OUTPUT_TOO_SMALL;
    if (output == NULL) return BASE64_NULL_OUTPUT;
    if (input == output) return BASE64_INPUT_EQUALS_OUTPUT;

    for (i = 0, j = 0; i < input_length;) {
        int octet_a = i < input_length ? (unsigned char) input[i++] : 0;
        int octet_b = i < input_length ? (unsigned char) input[i++] : 0;
        int octet_c = i < input_length ? (unsigned char) input[i++] : 0;
        int triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c;
        output[j++] = encoding_table[(triple >> 3 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 2 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 1 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 0 * 6) & 0x3F];
    }


    for (i = 0, pad = mod_table[input_length % 3], j -= pad; i < pad; i++) {
        output[j++] = '=';
    }

    output[j++] = '\0';
    return 0;
}

static int
base64_decode(const char * input, char * output, size_t output_length, size_t * decoded_length)
{
    int input_length = strlen(input);

    if (input_length % 4 != 0) {
        return BASE64_INPUT_MALFORMED;
    }

    *decoded_length = input_length / 4 * 3;
    if (input[input_length - 1] == '=') (*decoded_length)--;
    if (input[input_length - 2] == '=') (*decoded_length)--;

    if (*decoded_length > output_length) {
        return BASE64_OUTPUT_TOO_SMALL;
    }

    if (output == NULL) {
        return BASE64_NULL_OUTPUT;
    }

    for (int i = 0, j = 0; i < input_length;) {
        int sextet_a = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_b = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_c = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_d = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int triple = (sextet_a << 3 * 6) + (sextet_b << 2 * 6) + (sextet_c << 1 * 6) + (sextet_d << 0 * 6);
        if (j < *decoded_length) output[j++] = (triple >> 2 * 8) & 0xFF;
        if (j < *decoded_length) output[j++] = (triple >> 1 * 8) & 0xFF;
        if (j < *decoded_length) output[j++] = (triple >> 0 * 8) & 0xFF;
    }

    return 0;
}

/* Section: AST and ParseTree functions */

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

  lnode = ast_list = tail = NULL;

  if ( tree->nchildren == 0 )
    return ast;

  if ( tree->list == TRUE )
  {
    int end = MAX(0, tree->nchildren - 1);

    for ( i = 0; i < end; i++ )
    {
      if ( tree->children[i].type == PARSE_TREE_NODE_TYPE_TERMINAL &&
           tree->listSeparator != NULL &&
           ((TOKEN_T *) tree->children[i].object)->terminal->id == ((TOKEN_T *) tree->listSeparator)->terminal->id ) {
          continue;
      }
      lnode = calloc(1, sizeof(AST_LIST_T));
      lnode->tree = {{prefix}}parsetree_node_to_ast(&tree->children[i]);

      if ( ast_list == NULL )
      {
        ast_list = tail = lnode;
        continue;
      }

      tail->next = (AST_LIST_T *) lnode;
      tail = tail->next;
    }

    next = {{prefix}}parsetree_node_to_ast(&tree->children[end]);
    if ( ast_list == NULL ) return next;
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
    ast = {{prefix}}parsetree_node_to_ast( &tree->children[ast_return_index->index] );
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
        return {{prefix}}parsetree_node_to_ast( &tree->children[0] );
      }
      else
      {
        child = &tree->children[index];
      }

      ast_object->children[i].tree = {{prefix}}parsetree_node_to_ast(child);
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
    ast = {{prefix}}parsetree_node_to_ast( &tree->children[ast_return_index->index] );
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
      ast_object->children[i].tree = {{prefix}}parsetree_node_to_ast(&tree->children[ast_object_spec->attrs[i].index]);
    }
  }

  return ast;
}

static int
token_to_string_bytes(TOKEN_T * token)
{
  /* format: "<resource:line:col terminal \"b64_source\">" */
  int source_string_len = token->source_string ? (strlen(token->source_string)*4/3) : 5;
  return 1 + strlen({{prefix}}morpheme_to_str(token->terminal->id)) + strlen(token->resource) + 7 + 5 + 5 + 5 + 3 + source_string_len + 2;
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
    return 2 + token_to_string_bytes((TOKEN_T *) node->object) + indent;
  }

  return -1;
}

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_T * tree;
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
    return {{prefix}}token_to_string((TOKEN_T *) node->object);
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
      return indent + 2; /* "[]" */
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
    return initial_indent + token_to_string_bytes((TOKEN_T *) node->object) + indent;
  }

  return 4; /* "None" */
}

static char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  AST_LIST_T * ast_list, * lnode;
  AST_OBJECT_T * ast_object;
  char * str, * key, * value, * indent_str, * tmp;
  int bytes, i;
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
      indent_str = _get_indent_str(indent);
      sprintf(str, "%s[]", indent_str);
      free(indent_str);
      return str;
    }

    indent_str = _get_indent_str(indent);
    snprintf(str, bytes, "%s[\n", indent_str);
    for ( i = 0, lnode = ast_list; lnode && lnode->tree; i++, lnode = lnode->next )
    {
      value = _ast_to_string(lnode->tree, indent + 2, ctx);
      snprintf(str + strlen(str), bytes - strlen(str), "%s", value);
      if ( lnode->next != NULL )
        strcat(str, ",\n");
      free(value);
    }
    snprintf(str + strlen(str), bytes - strlen(str), "\n%s]", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    char * token_str = {{prefix}}token_to_string((TOKEN_T *) node->object);
    indent_str = _get_indent_str(indent);
    if (indent_str != NULL) {
      token_str = realloc(token_str, strlen(token_str) + strlen(indent_str) + 1);
      _prepend(token_str, indent_str);
      free(indent_str);
    }
    return token_str;
  }

  strcpy(str, "None");
  return str;
}

char *
{{prefix}}token_to_string(TOKEN_T * token)
{
    int bytes, rc;
    static char * b64 = NULL;
    size_t b64_size = 2;
    char * str;

    if (b64 == NULL) {
        b64 = malloc(b64_size);
    }

    bytes = token_to_string_bytes(token);
    bytes += 1; /* null byte */

    while(1) {
        rc = base64_encode(
            (const char *) token->source_string,
            strlen(token->source_string),
            b64, b64_size
        );
        if (rc == 0) break;
        else if (rc == BASE64_OUTPUT_TOO_SMALL) {
            b64_size *= 2;
            b64 = realloc(b64, b64_size);
            continue;
        }
        else {
            printf("Error\n");
            exit(-1);
        }
    }

    str = calloc(bytes, sizeof(char));

    sprintf(
        str,
        "<%s:%d:%d %s \"%s\">",
        token->resource,
        token->lineno,
        token->colno,
        {{prefix}}morpheme_to_str(token->terminal->id),
        b64
    );

    return str;
}

char *
{{prefix}}ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree, PARSER_CONTEXT_T * ctx )
{
  return _ast_to_string(tree, 0, ctx);
}

char *
{{prefix}}parsetree_to_string( PARSE_TREE_T * tree, PARSER_CONTEXT_T * ctx )
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
{{prefix}}parsetree_node_to_ast( PARSE_TREE_NODE_T * node )
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
    if ( tree->list )
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
{{prefix}}free_parse_tree( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;

  if ( tree == NULL )
    return;

  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  _free_parse_tree(&node);
}

void
{{prefix}}free_ast( ABSTRACT_SYNTAX_TREE_T * ast )
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
        {{prefix}}free_ast(ast_object->children[i].tree);
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
          {{prefix}}free_ast(current->tree);
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

/* Section: Parser */

{% for nonterminal in grammar.ll1_nonterminals %}
static PARSE_TREE_T * parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
{% endfor %}

{% for expression_nonterminal in grammar.expression_nonterminals %}
static PARSE_TREE_T * parse_{{expression_nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
static PARSE_TREE_T * _parse_{{expression_nonterminal.string.lower()}}(int, PARSER_CONTEXT_T *);
{% endfor %}

static void syntax_error( PARSER_CONTEXT_T * ctx, char * message );

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
  { {{', '.join([str(x.id) for x in grammar.first(nonterminal)])}}{{', ' if len(grammar.first(nonterminal)) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}follow[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.follow(nonterminal)])}}{{', ' if len(grammar.follow(nonterminal)) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}table[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)}}] = {
  {% py parse_table = grammar.parse_table %}
  {% for i in range(len(grammar.nonterminals)) %}
  { {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} },
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}nud_ast_types[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule, ExprRule) and isinstance(rule.nudAst, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}ast_types[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

static AST_CREATE_OBJECT_INIT {{prefix}}nud_ast_objects[] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
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
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
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

static int {{prefix}}ast_index[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
  {{rule.ast.idx if isinstance(rule.ast, AstTranslation) else 0}}, /* ({{rule.id}}) {{rule}} */
  {% endfor %}
};

static int {{prefix}}nud_ast_index[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
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
  if ( token_list->current_index == token_list->ntokens ) {
    token_list->current = {{prefix.upper()}}TERMINAL_END_OF_STREAM;
    return token_list->current;
  }
  token_list->current_index += 1;
  token_list->current = token_list->tokens[token_list->current_index]->terminal->id;
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

  current = token_list->tokens[token_list->current_index]->terminal->id;
  current_token = token_list->tokens[token_list->current_index];

  if ( current != terminal_id )
  {
    char * token_string = (current != {{prefix.upper()}}TERMINAL_END_OF_STREAM) ?  {{prefix}}token_to_string(current_token) : strdup("(end of stream)");
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

{% for expression_nonterminal in grammar.expression_nonterminals %}
{% py name = expression_nonterminal.string.lower() %}

static int infixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in grammar.get_rules(expression_nonterminal) if rule.operator and rule.operator.associativity in ['left', 'right']} %}

  {% for i in range(len(grammar.terminals)) %}
  {{0 if i not in operators else operators[i]}},
  {% endfor %}
};

static int prefixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in grammar.get_rules(expression_nonterminal) if rule.operator and rule.operator.associativity in ['unary']} %}

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
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{expression_nonterminal.string.upper()}};

  current = list->current;

  if ( list == NULL )
  {
    tree->ast_converter = get_default_ast_converter();
    return tree;
  }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py ruleFirstSet = grammar.first(rule.production) %}

    {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first(expression_nonterminal))%}
  if ( {{' || '.join(['current == %d' % (x.id) for x in ruleFirstSet])}} )
  {
    // {{rule}}
    {% if isinstance(rule.operator, PrefixOperator) %}
    tree->ast_converter = get_ast_converter({{rule.id}});
    {% else %}
    tree->ast_converter = get_nud_ast_converter({{rule.id}});
    {% endif %}
    tree->nchildren = {{len(rule.nud_production)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nud_production)}};
    {% for index, morpheme in enumerate(rule.nud_production.morphemes) %}
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
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{expression_nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) %}
  if ( current == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
      {% py nt = rule.nud_production.morphemes[0] %}
      {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
    tree->isExprNud = 1;
      {% endif %}
    {% endif %}

    tree->children[0].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[0].object = (PARSE_TREE_NODE_U *) left;

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
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
        {% endif %}
      {% endfor %}
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
  PARSE_TREE_T * tree;
  char * message, * fmt;
  int rule = -1;

  ctx->current_function = "parse_{{nonterminal.string.lower()}}";

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}};

    {% if isinstance(nonterminal.macro, LL1ListMacro) %}
  tree->list = TRUE;
    {% else %}
  tree->list = FALSE;
    {% endif %}

  current = tokens->current;

  {% if not grammar.must_consume_tokens(nonterminal) %}
  if ( current != {{prefix.upper()}}TERMINAL_END_OF_STREAM &&
       in_array({{prefix}}follow[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) &&
       !in_array({{prefix}}first[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) )
  {
    return tree;
  }
  {% endif %}

  if ( current == {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    {% if not grammar.must_consume_tokens(nonterminal) %}
    return tree;
    {% else %}
    syntax_error(ctx, strdup("Error: unexpected end of file"));
    {% endif %}
  }

  rule = {{prefix}}table[{{nonterminal.id - len(grammar.standard_terminals)}}][current];

    {% for index0, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}
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
          {% if isinstance(nonterminal.macro, LL1ListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
    tree->listSeparator = tree->children[{{index}}].object;
            {% endif %}
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

    {% if grammar.must_consume_tokens(nonterminal) %}
  fmt = "Error: Unexpected symbol (%s) when parsing %s";
  message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index]->terminal->id)) + strlen("parse_{{nonterminal.string.lower()}}") + 1, sizeof(char) );
  sprintf(message, fmt, {{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index]->terminal->id), "parse_{{nonterminal.string.lower()}}");
  syntax_error(ctx, message);
  return NULL;
    {% else %}
  return tree;
    {% endif %}
}
{% endfor %}

#define HAS_MORE_TOKENS(ctx) (ctx->tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM)

{% for expression_nonterminals in grammar.expression_nonterminals %}

#define {{expression_nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) (rbp < getInfixBp_{{expression_nonterminal.string.lower()}}(ctx->tokens->current))

static PARSE_TREE_T *
_parse_{{expression_nonterminal.string.lower()}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{expression_nonterminal.string.lower()}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( HAS_MORE_TOKENS(ctx) && {{expression_nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) )
  {
    left = led_{{expression_nonterminal.string.lower()}}(left, ctx);
  }

  if ( left != NULL )
  {
    left->isExpr = 1;
  }

  return left;
}

static PARSE_TREE_T *
parse_{{expression_nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  ctx->current_function = "parse_{{expression_nonterminal.string.lower()}}";
  return _parse_{{expression_nonterminal.string.lower()}}(0, ctx);
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
  tokens->current = tokens->tokens[0]->terminal->id;
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
  syntax_error->terminal = ctx->tokens->tokens[ctx->tokens->current_index]->terminal;
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
{{prefix}}parse(PARSER_CONTEXT_T * ctx, ENUM_{{prefix.upper()}}NONTERMINAL start)
{
  PARSE_TREE_T * tree;

  if ( start == -1 ) {
    start = {{prefix.upper()}}NONTERMINAL_{{grammar.start.string.upper()}};
  }

  tree = functions[start - {{len(grammar.standard_terminals)}}](ctx);

  if ( ctx->tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM ) {
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
  return {{prefix}}parsetree_node_to_ast(&node);
}

/* Section: Main */

{% if add_main %}
typedef enum token_field_e {
  TOKEN_FIELD_TERMINAL_E = 0x1,
  TOKEN_FIELD_LINE_E = 0x2,
  TOKEN_FIELD_COL_E = 0x4,
  TOKEN_FIELD_RESOURCE_E = 0x8,
  TOKEN_FIELD_SOURCE_STRING_E = 0x10,
  TOKEN_FIELD_ALL_E = 0x20 - 1,
  TOKEN_FIELD_NONE_E = 0,
  TOKEN_FIELD_INVALID_E = -1
} TOKEN_FIELD_E;

static TOKEN_FIELD_E str_to_token_field(char * str) {
  if ( !strcmp(str, "terminal") ) return TOKEN_FIELD_TERMINAL_E;
  else if ( !strcmp(str, "line") ) return TOKEN_FIELD_LINE_E;
  else if ( !strcmp(str, "col") ) return TOKEN_FIELD_COL_E;
  else if ( !strcmp(str, "resource") ) return TOKEN_FIELD_RESOURCE_E;
  else if ( !strcmp(str, "source_string") ) return TOKEN_FIELD_SOURCE_STRING_E;
  else return TOKEN_FIELD_INVALID_E;
}

static char * strdup2(const char *str) {
  int n = strlen(str) + 1;
  char *dup = malloc(n);
  if(dup) {
    strcpy(dup, str);
  }
  return dup;
}

#define strdup strdup2

int
main(int argc, char * argv[])
{
  PARSE_TREE_T * parse_tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * abstract_syntax_tree;
  char * str;
  int i, rval = 0, rc;
  char * file_contents, * b64;
  int file_length;
  size_t b64_size = 2;
  FILE * fp;

  b64 = malloc(b64_size);

  char err[512];
  TOKEN_LIST_T * lexer_tokens;

  if (argc != 3 || (strcmp(argv[1], "parsetree") != 0 && strcmp(argv[1], "ast") != 0 {% if lexer %} && strcmp(argv[1], "tokens") != 0{% endif %})) {
    fprintf(stderr, "Usage: %s parsetree <source>\n", argv[0]);
    fprintf(stderr, "Usage: %s ast <source>\n", argv[0]);
    {% if lexer %}
    fprintf(stderr, "Usage: %s tokens <source>\n", argv[0]);
    {% endif %}
    return -1;
  }

  fp = fopen(argv[2], "r");
  file_length = read_file(&file_contents, fp);

  {{prefix}}lexer_init();
  if ( {{prefix}}lexer_has_errors() ) {
      {{prefix}}lexer_print_errors();
  }
  lexer_tokens = {{prefix}}lex(file_contents, argv[2], &err[0]);
  if (lexer_tokens == NULL) {
      printf("%s\n", err);
      exit(1);
  }

  {% if lexer %}
  if (!strcmp(argv[1], "tokens")) {
    for (i = 0; lexer_tokens->tokens[i]->terminal->id != {{prefix.upper()}}TERMINAL_END_OF_STREAM; i++) {
        printf("%s\n", {{prefix}}token_to_string(lexer_tokens->tokens[i]));
    }
    return 0;
  }
  {% endif %}

  if (!strcmp(argv[1], "parsetree") || !strcmp(argv[1], "ast")) {
      ctx = {{prefix}}parser_init(lexer_tokens);
      parse_tree = {{prefix}}parse(ctx, -1);
      abstract_syntax_tree = {{grammar.name}}_ast(parse_tree);

      if ( ctx->syntax_errors ) {
        rval = 1;
        printf("%s\n", ctx->syntax_errors->message);
        goto exit;
        /*for ( error = ctx->syntax_errors; error; error = error->next )
        {
          printf("%s\n", error->message);
        }*/
      }

      if ( argc >= 3 && !strcmp(argv[1], "ast") ) {
        str = {{prefix}}ast_to_string(abstract_syntax_tree, ctx);
      } else {
        str = {{prefix}}parsetree_to_string(parse_tree, ctx);
      }

      printf("%s", str);

      {{grammar.name}}_parser_exit(ctx);
      {{prefix}}free_parse_tree(parse_tree);
      {{prefix}}free_ast(abstract_syntax_tree);
  }

exit:
  {{prefix}}lexer_destroy();
  free(b64);
  return rval;
}
{% endif %}

/* Section: Lexer */

{% if lexer %}
{% import re %}

{{prefix.upper()}}LEXER_MODE_E {{prefix}}lexer_mode_enum(const char * mode) {
{% for mode, regex_list in lexer.items() %}
    if (strcmp(mode, "{{mode}}") == 0) {
        return {{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E;
    }
{% endfor %}
    return {{prefix.upper()}}LEXER_INVALID_MODE_E;
}

char * {{prefix}}lexer_mode_string({{prefix.upper()}}LEXER_MODE_E mode) {
{% for mode, regex_list in lexer.items() %}
    if ({{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E == mode) {
        return "{{mode}}";
    }
{% endfor %}
    return NULL;
}

static LEXER_REGEX_T *** lexer = NULL;

static TOKEN_T *
emit(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col)
{
    TOKEN_T * token;
    if (ctx->token_list->current_index + 2 == ctx->token_list->ntokens) {
        ctx->token_list->ntokens += 100;
        ctx->token_list->tokens = realloc(ctx->token_list->tokens, ctx->token_list->ntokens * sizeof(TOKEN_T *));
    }
    token = ctx->token_list->tokens[ctx->token_list->current_index++] = calloc(1, sizeof(TOKEN_T));
    token->lineno = line;
    token->colno = col;
    token->source_string = strdup(source_string);
    token->resource = strdup(ctx->resource);
    token->terminal = calloc(1, sizeof(TERMINAL_T));
    memcpy(token->terminal, terminal, sizeof(TERMINAL_T));
    return token;
}

{% if re.search(r'void\s*\*\s*default_action', lexer.code) is None %}
static void
default_action(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col)
{
    emit(ctx, terminal, source_string, line, col);
}
{% endif %}

/* START USER CODE */
{{lexer.code}}
/* END USER CODE */

{% if re.search(r'void\s*\*\s*init', lexer.code) is None %}
static void *
init() {
    return NULL;
}
{% endif %}

{% if re.search(r'void\s*destroy', lexer.code) is None %}
static void
destroy(void * context) {
    return;
}
{% endif %}

void
{{prefix}}lexer_init()
{
    LEXER_REGEX_T * r;
    LEXER_REGEX_OUTPUT_T * o;
    if (lexer != NULL) {
        return;
    }
    lexer = calloc({{len(lexer.keys())}} + 1, sizeof(LEXER_REGEX_T **));
{% for mode, regex_list in lexer.items() %}
    lexer[{{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E] = calloc({{len(regex_list)}} + 1, sizeof(LEXER_REGEX_T *));
  {% for i, regex in enumerate(regex_list) %}
    r = calloc(1, sizeof(LEXER_REGEX_T));
    r->regex = pcre_compile({{regex.regex}}, {{' | '.join(regex.options + ['PCRE_UTF8'])}}, &r->pcre_errptr, &r->pcre_erroffset, NULL);
    r->pattern = {{regex.regex}};
    {% if len(regex.outputs) %}
    r->outputs = calloc({{len(regex.outputs)}}, sizeof(LEXER_REGEX_OUTPUT_T));

      {% for j, output in enumerate(regex.outputs) %}
    o = &r->outputs[{{j}}];
        {% if isinstance(output, RegexOutput) %}
    o->group = {{output.group if output.group is not None else -1}};
          {% if output.terminal %}
    o->terminal = calloc(1, sizeof(TERMINAL_T));
    o->terminal->string = "{{output.terminal.string.lower()}}";
    o->terminal->id = {{output.terminal.id}};
          {% else %}
    o->terminal = NULL;
          {% endif %}
    o->match_func = {{output.function if output.function else 'default_action'}};
        {% elif isinstance(output, LexerStackPush) %}
    o->stack_push = "{{output.mode}}";
        {% elif isinstance(output, LexerAction) %}
    o->action = "{{output.action}}";
        {% endif %}
      {% endfor %}

    {% else %}
    r->outputs = NULL;
    {% endif %}
    r->outputs_count = {{len(regex.outputs)}};
    lexer[{{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E][{{i}}] = r;
  {% endfor %}
{% endfor %}
}

int
{{prefix}}lexer_has_errors()
{
    int i, j;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            if (lexer[i][j]->regex == NULL) {
                return 1;
            }
        }
    }
    return 0;
}

void
{{prefix}}lexer_print_errors()
{
    int i, j, k;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            if (lexer[i][j]->regex == NULL) {
                char * prefix = "Error compiling regex: ";
                printf("%s%s\n", prefix, lexer[i][j]->pattern);
                for (k = 0; k < strlen(prefix) + lexer[i][j]->pcre_erroffset - 1; k++) {
                    printf(" ");
                }
                printf("^\n");
                printf("%s\n\n", lexer[i][j]->pcre_errptr);
            }
        }
    }
}

void
{{prefix}}lexer_destroy() {
    int i, j, k;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            pcre_free(lexer[i][j]->regex);
            for (k = 0; k < lexer[i][j]->outputs_count; k++) {
                free(lexer[i][j]->outputs[k].terminal);
            }
            free(lexer[i][j]->outputs);
            free(lexer[i][j]);
        }
    }
    free(lexer);
    lexer = NULL;
}

static char *
get_line(char * s, int line)
{
    char * p, * start, * rval;
    int current_line = 1, length = 0;
    if ( line < 1 ) {
        return NULL;
    }
    for( p = start = s; *p; p++ ) {
        if (*p == '\n') {
            if ( line == current_line ) {
                break;
            }
            current_line++;
            length = 0;
            start = p + 1;
        } else {
            length++;
        }
    }
    if (current_line < line) {
        return NULL;
    }
    rval = calloc(length + 1, sizeof(char));
    strncpy(rval, start, length);
    return rval;
}

static void
unrecognized_token(char * string, int line, int col, char * message) {
    char * bad_line = get_line(string, line);
    char * spaces = calloc(col+1, sizeof(char));
    memset(spaces, ' ', col-1);
    sprintf(message, "Unrecognized token on line %d, column %d:\n\n%s\n%s^",
        line, col, bad_line, spaces
    );
    free(spaces);
    free(bad_line);
}

static void
advance_line_col(char * string, int length, int * line, int * col) {
    int i;
    for (i = 0; i < length; i++) {
        if (string[i] == '\n') {
            *line += 1;
            *col = 1;
        } else {
            if ((string[i] & 0xc0) != 0x80) {
                *col += 1;
            }
        }
    }
}

static void
advance_string(LEXER_CONTEXT_T * ctx, int length) {
    advance_line_col(ctx->string, length, &ctx->line, &ctx->col);
    ctx->string += length;
}

static int
next(LEXER_CONTEXT_T * ctx) {
    int rc, i, j;
    int group_line, group_col;
    int ovector_count = 30, group_strlen, match_length;
    int ovector[ovector_count];
    char ** match_groups;
    {{prefix.upper()}}LEXER_MODE_E mode = ({{prefix.upper()}}LEXER_MODE_E) ctx->stack[ctx->stack_top];

    for (i = 0; lexer[mode][i]; i++) {
        rc = pcre_exec(lexer[mode][i]->regex, NULL, ctx->string, strlen(ctx->string), 0, PCRE_ANCHORED, ovector, ovector_count);
        if (rc >= 0) {
            match_length = ovector[1] - ovector[0];

            if (lexer[mode][i]->outputs_count == 0 || lexer[mode][i]->outputs == NULL) {
                advance_string(ctx, match_length);
                return TRUE;
            }

            match_groups = calloc(rc+1, sizeof(char *));
            for (j = 0; j < rc; j++) {
                char * substring_start = ctx->string + ovector[2*j];
                group_strlen = ovector[2*j+1] - ovector[2*j];
                match_groups[j] = calloc(group_strlen + 1, sizeof(char));
                strncpy(match_groups[j], substring_start, group_strlen);
            }

            for (j = 0; j < lexer[mode][i]->outputs_count; j++) {
                if (lexer[mode][i]->outputs[j].stack_push != NULL) {
                    if (ctx->stack_top + 1 == ctx->stack_size) {
                        ctx->stack_size *= 2;
                        ctx->stack = realloc(ctx->stack, ctx->stack_size);
                    }
                    ctx->stack[++ctx->stack_top] = {{prefix}}lexer_mode_enum(lexer[mode][i]->outputs[j].stack_push);
                } else if (lexer[mode][i]->outputs[j].action != NULL) {
                    if (ctx->stack_top == 0) {
                        printf("Error: stack empty, can't pop\n");
                        exit(-1);
                    }
                    ctx->stack_top--;
                } else {
                    lexer_match_function match_func = lexer[mode][i]->outputs[j].match_func;
                    group_line = ctx->line;
                    group_col = ctx->col;
                    if (lexer[mode][i]->outputs[j].group > 0) {
                        advance_line_col(ctx->string, ovector[2*lexer[mode][i]->outputs[j].group] - ovector[0], &group_line, &group_col);
                    }
                    match_func(
                        ctx,
                        lexer[mode][i]->outputs[j].terminal,
                        lexer[mode][i]->outputs[j].group >= 0 ? match_groups[lexer[mode][i]->outputs[j].group] : "",
                        group_line,
                        group_col
                    );
                }
            }

            for (j = 0; match_groups[j]; j++) {
                free(match_groups[j]);
            }
            free(match_groups);
            advance_string(ctx, match_length);
            return TRUE;
        }
    }
    return FALSE;
}

TOKEN_LIST_T *
{{prefix}}lex(char * string, char * resource, char * error) {
    char * string_current = string;
    TERMINAL_T end_of_stream;
    LEXER_CONTEXT_T * ctx = NULL;
    TOKEN_LIST_T * token_list;

    ctx = calloc(1, sizeof(LEXER_CONTEXT_T));
    ctx->string = string_current;
    ctx->resource = resource;
    ctx->token_list = calloc(1, sizeof(TOKEN_LIST_T));
    ctx->token_list->ntokens = 100;
    ctx->token_list->current_index = 0;
    ctx->token_list->tokens = calloc(ctx->token_list->ntokens, sizeof(TOKEN_LIST_T *));
    ctx->stack_size = 10;
    ctx->stack_top = 0;
    ctx->stack = calloc(ctx->stack_size, sizeof(int));
    ctx->stack[0] = {{prefix.upper()}}LEXER_DEFAULT_MODE_E;
    ctx->line = 1;
    ctx->col = 1;
    ctx->user_context = init();

    while (strlen(ctx->string)) {
        int matched = next(ctx);

        if (matched == FALSE) {
            unrecognized_token(string, ctx->line, ctx->col, error);
            free(ctx->token_list);
            free(ctx->stack);
            free(ctx);
            return NULL;
        }
    }

    end_of_stream.id = {{prefix.upper()}}TERMINAL_END_OF_STREAM;
    emit(ctx, &end_of_stream, "<end of stream>", ctx->line, ctx->col);

    token_list = ctx->token_list;
    token_list->ntokens = token_list->current_index - 1;
    token_list->current_index = 0;

    destroy(ctx->user_context);
    free(ctx->stack);
    free(ctx);
    return token_list;
}

void
{{prefix}}free_token_list(TOKEN_LIST_T * list) {
    if (list != NULL) {
        if (list->tokens != NULL) free(list->tokens);
        free(list);
    }
}
{% endif %}
