var parser = require('./{{prefix}}parser.js');
var common = require('./common.js');
var fs = require('fs');

function usage() {
    process.stderr.write('usage: ' + process.argv[0] + ' ' + process.argv[1] + ' [parsetree|ast] file\n');
    process.exit(-1);
}

if (process.argv.length < 4) {
    usage();
}

var output = process.argv[2];
var file = process.argv[3];

if (output != 'parsetree' && output != 'ast') {
    usage();
}

fs.readFile(file, 'utf-8', function (err, data) {
    if (err) throw err;
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
        //console.log(token);
        //console.log(file_tokens[i]);
    }
    //try {
        tree = parser.parse(new common.TokenStream(tokens));
        if (output == 'parsetree') {
            console.log(new common.ParseTreePrettyPrintable(tree).to_string());
        } else if (output == 'ast') {
            console.log(new common.AstPrettyPrintable(tree.to_ast()).to_string());
        }
    //} catch (err) {
    //    console.log(err.message);
    //}
});
