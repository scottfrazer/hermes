#include <stdio.h>
#include <pcre.h>
#include <string.h>
#include "json_parser.h"

int main(int argc, char * argv[]) {
  char error[1024];
  char * buf;
  int i;
  TOKEN_LIST_T * json_tokens;
  PARSER_CONTEXT_T * json_ctx;
  PARSE_TREE_T * tree;
  ABSTRACT_SYNTAX_TREE_T * ast;

  json_lexer_init();
  if (json_lexer_has_errors()) {
      json_lexer_print_errors();
      exit(-1);
  }

  json_tokens = json_lex("{\"a\": 0, \"b\":[true,2e4,true]}, \"cde\": 0.44e5", "<string>", &error[0]);

  if (json_tokens == NULL) {
      printf("%s\n", error);
      exit(-1);
  }

  printf("%d tokens:\n\n", json_tokens->ntokens);
  for(i = 0; json_tokens->tokens[i]->terminal->id != JSON_TERMINAL_END_OF_STREAM; i++) {
    buf = json_token_to_string(json_tokens->tokens[i]);
    printf("(%d) %s\n", i, buf);
    free(buf);
  }

  json_ctx = json_parser_init(json_tokens);

  tree = json_parse(json_ctx, -1);
  buf = json_parsetree_to_string(tree, json_ctx);
  printf("\nParse Tree: \n\n");
  printf("%s\n", buf);
  free(buf);

  ast = json_ast(tree);
  buf = json_ast_to_string(ast, json_ctx);
  printf("\nAST: \n\n");
  printf("%s\n", buf);
  free(buf);

  json_free_parse_tree(tree);
  json_free_ast(ast);
  json_parser_exit(json_ctx);
  json_free_token_list(json_tokens);
  json_lexer_destroy();

  return 0;
}
