#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

#include "parser_util.h"

#include "parser_common.h"
#include "{{grammar.name}}_parser.h"
{% if lexer %}
#include "{{grammar.name}}_lexer.h"
{% endif %}

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

static char * strdup2(const char *str)
{
  int n = strlen(str) + 1;
  char *dup = malloc(n);
  if(dup)
  {
    strcpy(dup, str);
  }
  return dup;
}

#define strdup strdup2

TOKEN_LIST_T *
get_tokens(char * grammar, char * json_input, TOKEN_LIST_T * token_list) {
  TOKEN_T * tokens;
  TOKEN_T end_of_stream;
  int i, j, ntokens;
  json_value * json;
  TOKEN_FIELD_E field, field_mask;
  int (*terminal_str_to_id)(const char *);

  if ( strcmp("{{grammar.name}}", grammar) == 0 ) {
    terminal_str_to_id = {{grammar.name}}_str_to_morpheme;
  }

  memset(&end_of_stream, 0, sizeof(TOKEN_T));
  end_of_stream.terminal = calloc(1, sizeof(TERMINAL_T));
  end_of_stream.terminal->id = -1;

  json = json_parse(json_input);

  if ( json == NULL ) {
    fprintf(stderr, "get_tokens(): Invalid JSON input\n");
    exit(-1);
  }

  if ( json->type != json_array ) {
    fprintf(stderr, "get_tokens(): JSON input should be an array of tokens\n");
    exit(-1);
  }

  ntokens = json->u.array.length;
  tokens = calloc(ntokens+1, sizeof(TOKEN_T));
  memcpy(&tokens[ntokens], &end_of_stream, sizeof(TOKEN_T));

  for ( i = 0; i < json->u.array.length; i++ ) {

    json_value * json_token = json->u.array.values[i];
    TOKEN_T * token = &tokens[i];
    token->terminal = calloc(1, sizeof(TERMINAL_T));

    if ( json_token->type != json_object ) {
      fprintf(stderr, "get_tokens(): JSON input should be an array of tokens\n");
      exit(-1);
    }

    for ( j = 0, field_mask = TOKEN_FIELD_NONE_E; j < json_token->u.object.length; j++ ) {
      char * name = json_token->u.object.values[j].name;
      json_value * value = json_token->u.object.values[j].value;
      field = str_to_token_field(name);

      if ( field == TOKEN_FIELD_INVALID_E ) {
        fprintf(stderr, "'%s' field is invalid for a token", name);
        exit(-1);
      } else if ( field & (TOKEN_FIELD_TERMINAL_E | TOKEN_FIELD_RESOURCE_E | TOKEN_FIELD_SOURCE_STRING_E) && (value == NULL || value->type != json_string) ) {
        fprintf(stderr, "'%s' field must have a string value", name);
        exit(-1);
      } else if ( field == TOKEN_FIELD_TERMINAL_E && terminal_str_to_id(value->u.string.ptr) == -1 ) {
        fprintf(stderr, "'%s' field does not have a valid terminal identifier (%s)", name, value->u.string.ptr);
        exit(-1);
      } else if ( field & (TOKEN_FIELD_COL_E | TOKEN_FIELD_LINE_E) && (value == NULL || (value->type != json_string && value->type != json_integer)) ) {
        fprintf(stderr, "'%s' field must have a string or integer value", name);
        exit(-1);
      }

      field_mask |= field;
    }

    if ( (field_mask & TOKEN_FIELD_TERMINAL_E) == 0 ) {
      fprintf(stderr, "'terminal' field must be specified for all tokens");
      exit(-1);
    }

    for ( j = 0, field_mask = TOKEN_FIELD_NONE_E; j < json_token->u.object.length; j++ ) {
      char * name = json_token->u.object.values[j].name;
      json_value * value = json_token->u.object.values[j].value;
      field = str_to_token_field(name);

      switch ( field ) {
        case TOKEN_FIELD_COL_E:
          if ( value->type == json_string ) {
            token->colno = atoi(value->u.string.ptr);
          } else if ( value->type == json_integer ) {
            token->colno = value->u.integer;
          }
          break;

        case TOKEN_FIELD_LINE_E:
          if ( value->type == json_string ) {
            token->lineno = atoi(value->u.string.ptr);
          } else if ( value->type == json_integer ) {
            token->lineno = value->u.integer;
          }
          break;

        case TOKEN_FIELD_TERMINAL_E:
          token->terminal->string = strdup((const char *) value->u.string.ptr);
          token->terminal->id = terminal_str_to_id(value->u.string.ptr);
          break;

        case TOKEN_FIELD_RESOURCE_E:
          token->resource = strdup((const char *) value->u.string.ptr);
          break;

        case TOKEN_FIELD_SOURCE_STRING_E:
          token->source_string = strdup((const char *) value->u.string.ptr);
          break;

        default:
          fprintf(stderr, "Unknown error\n");
          exit(-1);
      }
    }
  }

  token_list->tokens = tokens;
  token_list->ntokens = ntokens;
  token_list->current = tokens[0].terminal->id;
  token_list->current_index = -1;
  return token_list;
}

int
main(int argc, char * argv[])
{
  PARSE_TREE_T * parse_tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * abstract_syntax_tree;
  TOKEN_LIST_T token_list;
  char * str;
  int i, j, rval, rc;
  char * file_contents, * b64;
  int file_length;
  size_t b64_size = 2;
  FILE * fp;

  b64 = malloc(b64_size);

  char err[512];
  TOKEN_T ** tokens;

  if (argc != 3 || (strcmp(argv[1], "parsetree") != 0 && strcmp(argv[1], "ast") != 0 {% if lexer %} && strcmp(argv[1], "tokens") != 0{% endif %})) {
    fprintf(stderr, "Usage: %s <parsetree|ast> <tokens_file>\n", argv[0]);
    {% if lexer %}
    fprintf(stderr, "Usage: %s <tokens> <source_file>\n", argv[0]);
    {% endif %}
    return -1;
  }

  fp = fopen(argv[2], "r");
  file_length = read_file(&file_contents, fp);

  {% if lexer %}
  if (!strcmp(argv[1], "tokens")) {
    {{prefix}}lexer_init();
    if ( {{prefix}}lexer_has_errors() ) {
        {{prefix}}lexer_print_errors();
    }
    tokens = {{prefix}}lex(file_contents, argv[2], &err[0]);
    if (tokens == NULL) {
        printf("Error: %s\n", err);
    }

    printf("[\n");
    for (i=0;tokens[i];tokens++) {
        while(1) {
            rc = base64_encode((const char *) tokens[i]->source_string, strlen(tokens[i]->source_string), b64, b64_size);
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


        /* {"terminal": "a", "resource": "resource", "line": 1, "col": 1, "source_string": "YQ=="}, */
        printf(
          "    %c\"terminal\": \"%s\", \"resource\": \"%s\", \"line\": %d, \"col\": %d, \"source_string\": \"%s\"%c%s\n",
          '{',
          tokens[i]->terminal->string,
          tokens[i]->resource,
          tokens[i]->lineno,
          tokens[i]->colno,
          b64,
          '}',
          tokens[i+1] == NULL ? "" : ","
        );
    }
    printf("]\n");
    {{prefix}}lexer_destroy();
    return 0;
  }
  {% endif %}

  get_tokens("{{grammar.name}}", file_contents, &token_list);
  ctx = {{grammar.name}}_parser_init(&token_list);
  parse_tree = {{grammar.name}}_parse(&token_list, -1, ctx);
  abstract_syntax_tree = {{grammar.name}}_ast(parse_tree);

  if ( argc >= 3 && !strcmp(argv[1], "ast") ) {
    str = ast_to_string(abstract_syntax_tree, ctx);
  } else {
    str = parsetree_to_string(parse_tree, ctx);
  }

  free_parse_tree(parse_tree);
  free_ast(abstract_syntax_tree);

  if ( ctx->syntax_errors ) {
    rval = 1;
    printf("%s\n", ctx->syntax_errors->message);
    /*for ( error = ctx->syntax_errors; error; error = error->next )
    {
      printf("%s\n", error->message);
    }*/
  }
  else
  {
    rval = 0;
    printf("%s", str);
  }

  {{grammar.name}}_parser_exit(ctx);

  free(b64);
  return rval;
}
