var parser = require('./test_parser.js')
var tokens = parser.lex('{"a": 1, "b": 2}', '<string>')
for (var i=0; i< tokens.list.length; i++) {
  console.log(tokens.list[i].to_string());
}

var tree = parser.parse(tokens)
console.log(tree.to_string())
