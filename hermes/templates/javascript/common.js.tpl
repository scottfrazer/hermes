if (!String.prototype.format) {
    String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined' ? args[number]: match;
        });
    };
}

String.prototype.lstrip = function() {
    return this.replace(/^\s*/g, "");
}

function Terminal(id, str, source_string, resource, line, col) {
    this.id = id;
    this.str = str;
    this.source_string = source_string;
    this.resource = resource;
    this.line = line;
    this.col = col;
    this.to_ast = function() {
        return this;
    };
    this.to_string = function() {
        return '<{0} (line {1} col {2}) `{3}`>'.format(this.str, this.line, this.col, this.source_string);
    };
}

function NonTerminal(id, str) {
    this.id = id;
    this.str = str;
    this.to_string = function() {
        return this.str;
    };
}

function AstTransformSubstitution(idx) {
    this.idx = idx;
    this.to_string = function() {
        return '$' + this.idx;
    };
}

function AstTransformNodeCreator(name, parameters) {
    this.name = name;
    this.parameters = parameters;
    this.to_string = function() {
        var arr = [];
        for ( key in this.parameters ) {
            arr.push('{0}=${1}'.format(key, this.parameters[key]));
        }
        return '{0} ( {1} )'.format(this.name, arr.join(', '));
    };
}

function AstList(list) {
    this.list = list
    this.push = function(element) {
        this.list.push(element);
    };
    this.to_ast = function() {
        var arr = [];
        for (item in this.list) {
            arr.push(item.to_ast());
        }
        return arr;
    };
}

function ParseTree(nonterminal) {
    this.children = [];
    this.nonterminal = nonterminal;
    this.astTransform = null;
    this.isExpr = false;
    this.isNud = false;
    this.isPrefix = false;
    this.isInfix = false;
    this.nudMorphemeCount = 0;
    this.isExprNud = false;
    this.listSeparator = null;
    this.list = false;
    this.add = function(tree) {
        this.children.push(tree);
    }
    this.to_ast = function() {
        if (this.list == 'slist' || this.list == 'nlist') {
            if (this.children.length == 0) {
              return new AstList([]);
            }
            var offset = this.children[0] == this.listSeparator ? 1 : 0;
            var first = this.children[offset].to_ast();
            var list = [];
            if (first != null) {
                list.push(first);
            }
            list.push.apply(list, this.children[offset+1].to_ast().list);
            return new AstList(list);
        }
        else if (this.list == 'otlist') {
            if (this.children.length == 0) {
                return new AstList([]);
            }
            var list = [];
            if (this.children[0] != this.listSeparator ) {
                list.push(this.children[0].to_ast());
            }
            list.push.apply(list, this.children[1].to_ast().list);
            return new AstList(list);
        }
        else if (this.list == 'tlist') {
            if (this.children.length == 0) {
                return new AstList([]);
            }
            var list = [this.children[0].to_ast()];
            list.push.apply(list, this.children[2].to_ast().list);
            return new AstList(list);
        }
        else if (this.list == 'mlist') {
            if (this.children.length == 0) {
                return new AstList([]);
            }
            var lastElement = this.children.length - 1;
            var list = [];
            for (var i = 0; i < lastElement; i++) {
                list.push(this.children[i].to_ast());
            }
            list.push.apply(list, this.children[lastElement].to_ast().list);
            return new AstList(list);
        }
        else if (this.isExpr == true) {
            if (this.astTransform instanceof AstTransformSubstitution) {
                return this.children[this.astTransform.idx].to_ast();
            }
            else if (this.astTransform instanceof AstTransformNodeCreator) {
                var parameters = {}
                for (name in this.astTransform.parameters) {
                    var idx = this.astTransform.parameters[name];
                    var child = null;
                    if (idx == '$') {
                        child = this.children[0];
                    } else if (this.children[0] instanceof ParseTree && this.children[0].isNud && !this.children[0].isPrefix && !this.isExprNud && !this.isInfix) {
                        if (idx < this.children[0].nudMorphemeCount) {
                            child = this.children[0].children[idx]
                        } else {
                            index = idx - this.children[0].nudMorphemeCount + 1
                            child = this.children[index]
                        }
                    } else if (this.children.length == 1 && !(this.children[0] instanceof ParseTree) && !(this.children[0] instanceof Array)) {
                        return this.children[0];
                    } else {
                        child = this.children[idx];
                    }
                    parameters[name] = child.to_ast()
                }
                return new Ast(this.astTransform.name, parameters);
            }
        }
        else {
            if (this.astTransform instanceof AstTransformSubstitution) {
                return this.children[this.astTransform.idx].to_ast()
            } else if (this.astTransform instanceof AstTransformNodeCreator) {
                var parameters = {};
                for (name in this.astTransform.parameters) {
                    parameters[name] = this.children[this.astTransform.parameters[name]].to_ast();
                }
                return new Ast(this.astTransform.name, parameters);
                return x;
            } else if (this.children.length) {
                return this.children[0].to_ast();
            } else {
                return null;
            }
        }
    }
    this.to_string = function() {
        var children = []
        for (i in this.children) {
            var child = this.children[i];
            if (child instanceof Array) {
                var stringify = child.map(function(x) {return x.to_string()});
                children.push('[' + stringify.join(', ') + ']');
            } else {
                children.push(child.to_string());
            }
        }
        return '(' + this.nonterminal.to_string() + ': ' + children.join(', ') + ')'
    }
}

function Ast(name, attributes) {
    this.name = name;
    this.attributes = attributes;
    this.to_string = function() {
        var arr = [];
        for (var key in this.attributes) {
            var value = this.attributes[key];
            if (value instanceof Array) {
                var stringify = value.map(function(x) {return x.to_string()});
                value = '[{0}]'.format(stringify.join(', '));
            } else {
                value = value.to_string();
            }
            arr.push('{0}={1}'.format(key.to_string(), value))
        }
        return '({0}: {1})'.format(this.name, arr.join(', '));
    }
}

function AstPrettyPrintable(ast) {
    this.ast = ast;
    this.to_string = function() {
        return this._to_string(this.ast, 0);
    }
    this._to_string = function(ast, indent) {
        var arr = new Array(indent);
        for (i = 0; i < indent; i++) {arr[i] = ' ';}
        var indent_str = arr.join('');

        if (ast instanceof Ast) {
            var string = '{0}({1}:\n'.format(indent_str, ast.name);
            var arr = [];
            for (name in ast.attributes) {
                arr.push('{0}  {1}={2}'.format(indent_str, name, this._to_string(ast.attributes[name], indent+2).lstrip()));
            }
            string += arr.join(',\n');
            string += '\n{0})'.format(indent_str);
            return string;
        } else if (ast instanceof AstList) {
            if (ast.list.length == 0) {
                return '{0}[]'.format(indent_str)
            }
            var string = '{0}[\n'.format(indent_str);
            var arr = [];
            for (i in ast.list) {
                arr.push(this._to_string(ast.list[i], indent+2));
            }
            string += arr.join(',\n');
            string += '\n{0}]'.format(indent_str);
            return string
        } else if (ast instanceof Terminal) {
            return '{0}{1}'.format(indent_str, ast.to_string());
        } else {
            return '{0}{1}'.format(indent_str, (ast == null) ? 'None' : ast.to_string());
        }
    }
}

function ParseTreePrettyPrintable(parsetree) {
    this.parsetree = parsetree;
    this.to_string = function() {
        return this._to_string(this.parsetree, 0);
    }
    this._to_string = function(parsetree, indent) {
        var arr = new Array(indent);
        for (i = 0; i < indent; i++) {arr[i] = ' ';}
        var indent_str = arr.join('');

        if (parsetree instanceof ParseTree) {
            if (parsetree.children.length == 0) {
                return '({0}: )'.format(parsetree.nonterminal.to_string());
            }
            var string = '{0}({1}:\n'.format(indent_str, parsetree.nonterminal.to_string())
            var arr = [];
            for (i in parsetree.children) {
                child = parsetree.children[i];
                arr.push('{0}  {1}'.format(indent_str, this._to_string(child, indent+2).lstrip()));
            }
            string += arr.join(',\n');
            string += '\n{0})'.format(indent_str);
            return string
        } else if (parsetree instanceof Terminal) {
            return '{0}{1}'.format(indent_str, parsetree.to_string());
        } else {
            return '{0}{1}'.format(indent_str, parsetree.to_string());
        }
    }
}

function SyntaxError(message) {
    this.message = message;
    this.to_string = function() {
        return this.message;
    }
}

function TokenStream(list) {
    this.list = list;
    this.index = 0;
    this.advance = function() {
        this.index += 1;
        return this.current();
    }
    this.last = function() {
        return this.list[this.list.length - 1];
    }
    this.current = function() {
        if (this.index < this.list.length) {
            return this.list[this.index];
        } else {
            return null;
        }
    }
}

function DefaultSyntaxErrorFormatter() {
    this.unexpected_eof = function(nonterminal, expected_terminals, nonterminal_rules) {
        return "Error: unexpected end of file";
    }
    this.excess_tokens = function(nonterminal, terminal) {
        return "Finished parsing without consuming all tokens.";
    }
    this.unexpected_symbol = function(nonterminal, actual_terminal, expected_terminals, rule) {
        return "Unexpected symbol (line {0}, col {1}) when parsing parse_{2}.  Expected {3}, got {4}.".format(
          actual_terminal.line,
          actual_terminal.col,
          nonterminal,
          expected_terminals.join(', '),
          actual_terminal.to_string()
        );
    }
    this.no_more_tokens = function(nonterminal, expected_terminal, last_terminal) {
        return "No more tokens.  Expecting " + expected_terminal;
    }
    this.invalid_terminal = function(nonterminal, invalid_terminal) {
        return "Invalid symbol ID: {0} ({1})".format(invalid_terminal.id, invalid_terminal.string);
    }
}

function ParserContext(tokens, error_formatter) {
    this.tokens = tokens;
    this.error_formatter = error_formatter;
    this.nonterminal_string = null;
    this.rule_string = null;
}

var Base64 = {
    // private property
    _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

    // public method for encoding
    encode : function (input) {
        var output = "";
        var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
        var i = 0;

        input = Base64._utf8_encode(input);

        while (i < input.length) {

            chr1 = input.charCodeAt(i++);
            chr2 = input.charCodeAt(i++);
            chr3 = input.charCodeAt(i++);

            enc1 = chr1 >> 2;
            enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
            enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
            enc4 = chr3 & 63;

            if (isNaN(chr2)) {
                enc3 = enc4 = 64;
            } else if (isNaN(chr3)) {
                enc4 = 64;
            }

            output = output +
            Base64._keyStr.charAt(enc1) + Base64._keyStr.charAt(enc2) +
            Base64._keyStr.charAt(enc3) + Base64._keyStr.charAt(enc4);

        }

        return output;
    },

    // public method for decoding
    decode : function (input) {
        var output = "";
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;

        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

        while (i < input.length) {

            enc1 = Base64._keyStr.indexOf(input.charAt(i++));
            enc2 = Base64._keyStr.indexOf(input.charAt(i++));
            enc3 = Base64._keyStr.indexOf(input.charAt(i++));
            enc4 = Base64._keyStr.indexOf(input.charAt(i++));

            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;

            output = output + String.fromCharCode(chr1);

            if (enc3 != 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
                output = output + String.fromCharCode(chr3);
            }

        }

        output = Base64._utf8_decode(output);

        return output;

    },

    // private method for UTF-8 encoding
    _utf8_encode : function (string) {
        string = string.replace(/\r\n/g,"\n");
        var utftext = "";

        for (var n = 0; n < string.length; n++) {

            var c = string.charCodeAt(n);

            if (c < 128) {
                utftext += String.fromCharCode(c);
            }
            else if((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            }
            else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }

        }

        return utftext;
    },

    // private method for UTF-8 decoding
    _utf8_decode : function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;

        while ( i < utftext.length ) {

            c = utftext.charCodeAt(i);

            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            }
            else if((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            }
            else {
                c2 = utftext.charCodeAt(i+1);
                c3 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }

        }
        return string;
    }
}

{% if nodejs %}
module.exports = {
    ParserContext: ParserContext,
    DefaultSyntaxErrorFormatter: DefaultSyntaxErrorFormatter,
    TokenStream: TokenStream,
    SyntaxError: SyntaxError,
    ParseTreePrettyPrintable: ParseTreePrettyPrintable,
    AstPrettyPrintable: AstPrettyPrintable,
    Ast: Ast,
    ParseTree: ParseTree,
    AstList: AstList,
    AstTransformNodeCreator: AstTransformNodeCreator,
    AstTransformSubstitution: AstTransformSubstitution,
    NonTerminal: NonTerminal,
    Terminal: Terminal,
    Base64: Base64
}
{% endif %}
