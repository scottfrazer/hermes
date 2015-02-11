var parser = require('./{{prefix}}parser.js');
var common = require('./common.js');
var fs = require('fs');

function usage() {
    process.stderr.write('usage: ' + process.argv[0] + ' ' + process.argv[1] + ' [parsetree|ast|tokens] file\n');
    process.exit(-1);
}

if (process.argv.length < 4) {
    usage();
}

var output = process.argv[2];
var file = process.argv[3];

if (output != 'parsetree' && output != 'ast' && output != 'tokens') {
    usage();
}

fs.readFile(file, 'utf-8', function (err, data) {
    if (err) throw err;
    if (output == 'tokens') {
      var lexer = require('./{{prefix}}lexer.js');

      try {
          var tokens = lexer.lex(data, 'source');
      } catch(err) {
          console.log(err.to_string());
          process.exit(0);
      }

      if (tokens.length == 0) {
          console.log('[]');
      } else {
          console.log('[');
          for(i = 0; i < tokens.list.length; i++) {
              var token = tokens.list[i]
              console.log('    {"terminal": "{0}", "resource": "{1}", "line": {2}, "col": {3}, "source_string": "{4}"}{5}'.format(
                  token.str,
                  token.resource,
                  token.line,
                  token.col,
                  common.Base64.encode(token.source_string),
                  i == tokens.list.length-1 ? '' : ','
              ))
          }
          console.log(']');
      }
      process.exit(0);
    }
    var file_tokens = JSON.parse(data);
    var tokens = [];
    for (i in file_tokens) {
        token = new common.Terminal(
            parser.terminals[file_tokens[i].terminal],
            file_tokens[i].terminal,
            file_tokens[i].source_string,
            file_tokens[i].resource,
            file_tokens[i].line,
            file_tokens[i].col
        );
        tokens.push(token);
    }
    try {
        tree = parser.parse(new common.TokenStream(tokens));
        if (output == 'parsetree') {
            console.log(new common.ParseTreePrettyPrintable(tree).to_string());
        } else if (output == 'ast') {
            console.log(new common.AstPrettyPrintable(tree.to_ast()).to_string());
        }
    } catch (err) {
        console.log(err.message);
    }
});
