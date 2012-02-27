#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

#include "parser_common.h"

{% for grammar in grammars %}
#include "{{grammar.name}}_parser.h"
{% endfor %}

#define STDIN_BUF_SIZE 1024

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

static char *
read_stdin()
{
  char buffer[STDIN_BUF_SIZE];
  size_t size = 0, bytes;
  int flags;
  char * content, * old;

  flags = fcntl(fileno(stdin), F_GETFL, 0);
  flags |= O_NONBLOCK;
  fcntl(fileno(stdin), F_SETFL, flags);

  while(1)
  {
    old = content;
    bytes = fread(buffer, 1, STDIN_BUF_SIZE-1, stdin);

    if ( bytes == -1 )
    {
      perror("read");
      exit(-1);
    }

    if ( bytes == 0 )
    {
      break;
    }

    buffer[bytes] = '\0';
    content = realloc(content, size + bytes + 1);

    if ( content == NULL )
    {
      perror("realloc");
      free(old);
      exit(-1);
    }

    if ( size == 0 )
      *content = '\0';
    size += bytes;
    strcat(content, buffer);
  }

  return content;
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
  int i, nlines = 0;
  TOKEN_T * tokens;
  char * grammars = "{{','.join([grammar.name for grammar in grammars])}}";
  
  TOKEN_T eos;
  memset(&eos, 0, sizeof(TOKEN_T));
  eos.terminal = calloc(1, sizeof(TERMINAL_T));
  eos.terminal->id = -1;

  buffer = read_stdin();
  if ( buffer != NULL && strlen(buffer) != 0 )
  {
    for( i = 1, str = buffer; *str; str++ )
    {
      if ( *str == '\n' )
        i++;
    }

    lines = calloc(i + 1, sizeof(char *));

    line = strtok(buffer, "\n");
    for( nlines = 0; line; line = strtok(NULL, "\n") )
    {
      lines[nlines++] = line;
    }
  }
	
  if ( argc < 2 )
  {
    fprintf(stderr, "Usage: %s <%s> <parsetree,ast>\n", argv[0], grammars);
    exit(-1);
  }

  do
  {
    {% for grammar in grammars %}
    if ( strcmp(argv[1], "{{grammar.name}}") == 0 )
    {
      tokens = calloc(nlines + 1, sizeof(TOKEN_T));

      for ( i = 0; i < nlines; i++ )
      {
        parse_token(lines[i], {{grammar.name}}_str_to_morpheme, &tokens[i]);
      }

      memcpy(&tokens[i], &eos, sizeof(TOKEN_T));

      token_list.tokens = tokens;
      token_list.ntokens = nlines;
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
      {{grammar.name}}_parser_exit(ctx);
      break;
    }
    {% endfor %}

    fprintf(stderr, "Invalid grammar '%s', expected {'%s'}\n", argv[1], grammars);
    exit(-1);

  } while(0);

  if ( ctx->syntax_errors )
  {
    for ( error = ctx->syntax_errors; error; error = error->next )
    {
      printf("%s\n", error->message);
      exit(1);
    }
  }
  else
  {
    printf("%s", str);
  }

  if (str) free(str);
  return 0;
}
