var parser = require('./test_parser.js')
var tokens = parser.lex('{"a": 1, "b": 2}', '<string>')

console.log("Tokens:\n")
for (var i=0; i< tokens.list.length; i++) {
  console.log(tokens.list[i].to_string());
}

var tree = parser.parse(tokens)
console.log("\nParse Tree:\n")
console.log(parser.parse_tree_string(tree, 2, true))

var ast = tree.to_ast()
console.log("\nAbstract Syntax Tree:\n")
console.log(parser.ast_string(ast, 2, false))
