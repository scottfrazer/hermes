var parser = require('./json_parser.js')
var tokens = parser.lex('{"a": 1, "b": [-1,2e4,-0.003e4,0], "this is a key":[false, true, false]}', '<string>')

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
