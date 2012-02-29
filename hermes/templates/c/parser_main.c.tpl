#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

#include "parser_common.h"

{% for grammar in grammars %}
#include "{{grammar.name}}_parser.h"
{% endfor %}

#define STDIN_BUF_SIZE 1024

typedef struct token_stream_t {

	TOKEN_T * token;
	struct token_stream_t * next;

} TOKEN_STREAM_T;

static int stdin_nlines = 0;
static TOKEN_STREAM_T * stdin_tokens = NULL;

static TOKEN_T *
parse_token( const char * string, str_to_morpheme_func convert, TOKEN_T * token)
{
  TERMINAL_T * terminal = NULL;
  char * terminal_str_start, * filename_start;
  char * terminal_str_end, * filename_end;

  if ( token == NULL || string == NULL )
    return NULL;
  
  /* <string_literal [test/cases/0/source.c line 23, col 12]> */

  if ( *string != '<' )
  {
    fprintf(stderr, "Inproperly formatted token (doesn't start with <): %s", string);
    goto error_exit;
  }
  
  terminal_str_start = (char *) string + 1;
  terminal_str_end = strchr(terminal_str_start, ' ');

  if ( terminal_str_end == NULL )
  {
    fprintf(stderr, "Inproperly formatted token: %s", string);
    goto error_exit;
  }
  
  filename_start = (char *) terminal_str_end + 2;
  filename_end = strchr(filename_start, ' ');
  
  terminal = calloc(1, sizeof(TERMINAL_T));
  terminal->string = calloc((terminal_str_end - terminal_str_start) + 1, sizeof(char));
  token->resource = calloc((filename_end - filename_start) + 1, sizeof(char));
  token->terminal = terminal;

  sscanf(string, "<%s [%s line %d, col %d]>", terminal->string, token->resource, &token->lineno, &token->colno);
  terminal->id = convert(terminal->string);

  return token;
  
  error_exit:
  if ( terminal ) free(terminal);
  return NULL;
}

TOKEN_STREAM_T *
read_stdin()
{
  char line[2048];
  TOKEN_STREAM_T * tokens = NULL, * last = NULL, * node = NULL;

  while( fgets(line, 2048, stdin) )
  {
    stdin_nlines++;
    node = calloc(1, sizeof(TOKEN_STREAM_T));
    node->token = calloc(1, sizeof(TOKEN_T));
    node->next = NULL;
    parse_token(line, {{grammar.name}}_str_to_morpheme, node->token);
    if ( last ) last->next = node;
    if ( !tokens ) { tokens = last = node;}
    else { last = node; }
  }
	
  return tokens;
}

int
main(int argc, char * argv[])
{
  PARSE_TREE_T * parse_tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * abstract_syntax_tree;
  TOKEN_LIST_T token_list;
  SYNTAX_ERROR_T * error;
  char * str, * buffer, ** lines, * line;
  int i, rval;
  TOKEN_T * token, * tokens;
	TOKEN_STREAM_T * current;
  char * grammars = "{{','.join([grammar.name for grammar in grammars])}}";

  TOKEN_T eos;
  memset(&eos, 0, sizeof(TOKEN_T));
  eos.terminal = calloc(1, sizeof(TERMINAL_T));
  eos.terminal->id = -1;
	
  if ( argc < 2 )
  {
    fprintf(stderr, "Usage: %s <%s> <parsetree,ast>\n", argv[0], grammars);
    exit(-1);
  }

  stdin_tokens = read_stdin();

  do
  {
    {% for grammar in grammars %}
    if ( strcmp(argv[1], "{{grammar.name}}") == 0 )
    {
      tokens = calloc(stdin_nlines + 1, sizeof(TOKEN_T));

      for ( current = stdin_tokens, i = 0; current != NULL; current = current->next, i++ )
      {
        memcpy(&tokens[i], current->token, sizeof(TOKEN_T));
      }

      memcpy(&tokens[i], &eos, sizeof(TOKEN_T));

      token_list.tokens = tokens;
      token_list.ntokens = stdin_nlines;
      token_list.current = tokens[0].terminal->id;
      token_list.current_index = 0;

      ctx = {{grammar.name}}_parser_init(&token_list);
      parse_tree = {{grammar.name}}_parse(&token_list, -1, ctx);
      abstract_syntax_tree = {{grammar.name}}_ast(parse_tree);

      if ( argc >= 3 && !strcmp(argv[2], "ast") )
      {
        str = ast_to_string(abstract_syntax_tree, ctx);
      }
      else
      {
        str = parsetree_to_string(parse_tree, ctx);
      }

      free_parse_tree(parse_tree);
      free_ast(abstract_syntax_tree);

      if ( ctx->syntax_errors )
      {
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
      break;
    }
    {% endfor %}

    fprintf(stderr, "Invalid grammar '%s', expected {'%s'}\n", argv[1], grammars);
    exit(-1);

  } while(0);

  if (eos.terminal) free(eos.terminal);
  if (tokens) free(tokens);
  if (str) free(str);
  return rval;
}
