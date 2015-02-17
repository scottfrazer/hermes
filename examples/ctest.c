#include <stdio.h>
#include "simple_parser.h"
#include "test_parser.h"

int main(int argc, char * argv[]) {
  char error[1024];
  char * buf;
  int i;
  TOKEN_LIST_T * test_tokens;
  PARSER_CONTEXT_T * test_ctx, * simple_ctx;

  test_lexer_init();
  simple_lexer_init();

  test_tokens = test_lex("{\"a\": 0, \"b\":[true,false,true]}", "<string>", &error[0]);

  for(i = 0; test_tokens->tokens[i] != NULL; i++) {
    buf = test_token_to_string(test_tokens->tokens[i]);
    printf("%s\n", buf);
    free(buf);
  }

  test_lexer_destroy();

  /*test_ctx = test_parser_init(TOKEN_LIST_T * tokens)

  printf("=============\n");

  simple_tokens = simple_lex("aaabbb", "<string>", &error[0]);

  for(i=0;y[i]!=NULL;i++) {
    buf = test_token_to_string(y[i]);
    printf("%s\n", buf);
    free(buf);
  }
  simple_lexer_destroy();
  */

  return 0;
}
