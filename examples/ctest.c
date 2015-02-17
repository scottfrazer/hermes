#include <stdio.h>
#include "simple_parser.h"
#include "test_parser.h"

int main(int argc, char * argv[]) {
  char error[1024];
  char * buf;
  int i;
  TOKEN_LIST_T * test_tokens;
  PARSER_CONTEXT_T * test_ctx, * simple_ctx;
  PARSE_TREE_T * tree;
  ABSTRACT_SYNTAX_TREE_T * ast;

  test_lexer_init();
  simple_lexer_init();

  test_tokens = test_lex("{\"a\": 0, \"b\":[true,false,true]}", "<string>", &error[0]);

  printf("%d tokens:\n", test_tokens->ntokens);
  for(i = 0; test_tokens->tokens[i] != NULL; i++) {
    buf = test_token_to_string(test_tokens->tokens[i]);
    printf("(%d) %s\n", i, buf);
    free(buf);
  }

  test_ctx = test_parser_init(test_tokens);

  tree = test_parse(test_ctx, -1);
  buf = test_parsetree_to_string(tree, test_ctx);
  printf("\nParse Tree: \n\n");
  printf("%s\n", buf);
  free(buf);

  ast = test_ast(tree);
  buf = test_ast_to_string(ast, test_ctx);
  printf("\nAST: \n\n");
  printf("%s\n", buf);
  free(buf);

  test_free_parse_tree(tree);
  test_free_ast(ast);
  test_parser_exit(test_ctx);
  test_free_token_list(test_tokens);
  test_lexer_destroy();

  return 0;
}
