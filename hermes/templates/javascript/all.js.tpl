{% import re %}
{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro, OptionallyTerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

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

// Section: Parser

var terminals = {
{% for terminal in grammar.standard_terminals %}
    {{terminal.id}}: '{{terminal.string}}',
{% endfor %}

{% for terminal in grammar.standard_terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

// table[nonterminal][terminal] = rule
var table = [
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}}],
{% endfor %}
]

var nonterminal_first = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.first(nonterminal)])}}],
{% endfor %}
}

var nonterminal_follow = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.follow(nonterminal)])}}],
{% endfor %}
}

var rule_first = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: [{{', '.join([str(t.id) for t in grammar.first(rule.production)])}}],
{% endfor %}
}

var nonterminal_rules = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [
  {% for rule in grammar.get_expanded_rules() %}
    {% if rule.nonterminal.id == nonterminal.id %}
        "{{rule}}",
    {% endif %}
  {% endfor %}
    ],
{% endfor %}
}

var rules = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: "{{rule}}",
{% endfor %}
}

function is_terminal(id){
    return 0 <= id && id <= {{len(grammar.standard_terminals) - 1}};
}

function parse(tokens, error_formatter, start) {
    if (error_formatter === undefined) {
        error_formatter = new DefaultSyntaxErrorFormatter();
    }
    var ctx = new ParserContext(tokens, error_formatter);
    var tree = parse_{{grammar.start.string.lower()}}(ctx);
    if (tokens.current() != null) {
        throw new SyntaxError('Finished parsing without consuming all tokens.');
    }
    return tree;
}

function expect(ctx, terminal_id) {
    var current = ctx.tokens.current();
    if (current == null) {
        throw new SyntaxError(ctx.error_formatter.no_more_tokens(ctx.nonterminal, terminals[terminal_id], ctx.tokens.last()));
    }
    if (current.id != terminal_id) {
        throw new SyntaxError(ctx.error_formatter.unexpected_symbol(ctx.nonterminal, current, [terminals[terminal_id]], ctx.rule));
    }
    var next = ctx.tokens.advance();
    if (next && !is_terminal(next.id)) {
        throw new SyntaxError(ctx.error_formatter.invalid_terminal(ctx.nonterminal, next));
    }
    return current;
}

{% for expression_nonterminal in grammar.expression_nonterminals %}
    {% py name = expression_nonterminal.string %}

// START definitions for expression parser `{{name}}`
var infix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, // {{rule}}
        {% endif %}
    {% endfor %}
}

var prefix_binding_power_{{name}} = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['unary'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, // {{rule}}
        {% endif %}
    {% endfor %}
}

function get_infix_binding_power_{{name}}(terminal_id) {
    if (terminal_id in infix_binding_power_{{name}}) {
        return infix_binding_power_{{name}}[terminal_id];
    } else {
        return 0;
    }
}

function get_prefix_binding_power_{{name}}(terminal_id) {
    if (terminal_id in prefix_binding_power_{{name}}) {
        return prefix_binding_power_{{name}}[terminal_id];
    } else {
        return 0;
    }
}

function parse_{{name}}(ctx) {
    return parse_{{name}}_internal(ctx, 0);
}

function parse_{{name}}_internal(ctx, rbp) {
    left = nud_{{name}}(ctx);
    if (left instanceof ParseTree) {
        left.isExpr = true;
        left.isNud = true;
    }
    while (ctx.tokens.current() && rbp < get_infix_binding_power_{{name}}(ctx.tokens.current().id)) {
        left = led_{{name}}(left, ctx);
    }
    if (left) {
        left.isExpr = true;
    }
    return left;
}

function nud_{{name}}(ctx) {
    var tree = new ParseTree(new NonTerminal({{expression_nonterminal.id}}, '{{name}}'));
    var current = ctx.tokens.current();
    ctx.nonterminal = "{{name}}";

    if (!current) {
        return tree;
    }

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
    {{'if' if i == 0 else 'else if'}} (rule_first[{{rule.id}}].indexOf(current.id) != -1) {
        // {{rule}}
        ctx.rule = rules[{{rule.id}}];
        {% if isinstance(rule.nudAst, AstSpecification) %}
        ast_parameters = {
          {% for k,v in rule.nudAst.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
          {% endfor %}
        }
        tree.astTransform = new AstTransformNodeCreator('{{rule.nudAst.name}}', ast_parameters);
        {% elif isinstance(rule.nudAst, AstTranslation) %}
        tree.astTransform = new AstTransformSubstitution({{rule.nudAst.idx}});
        {% endif %}

        tree.nudMorphemeCount = {{len(rule.nud_production)}};

        {% for morpheme in rule.nud_production.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}}));
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add(parse_{{name}}_internal(ctx, get_prefix_binding_power_{{name}}({{rule.operator.operator.id}})));
        tree.isPrefix = true;
            {% else %}
        tree.add(parse_{{rule.nonterminal.string.lower()}}(ctx));
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx));
          {% endif %}
        {% endfor %}
    }
      {% endif %}
    {% endfor %}

    return tree;
}

function led_{{name}}(left, ctx) {
    var tree = new ParseTree(new NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    var current = ctx.tokens.current()
    ctx.nonterminal = "{{name}}";

    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) %}
    if (current.id == {{led[0].id}}) { // {{led[0]}}
        // {{rule}}
        ctx.rule = rules[{{rule.id}}];
        {% if isinstance(rule.ast, AstSpecification) %}
        ast_parameters = {
          {% for k,v in rule.ast.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
          {% endfor %}
        }
        tree.astTransform = new AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters);
        {% elif isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = new AstTransformSubstitution({{rule.ast.idx}});
        {% endif %}

        {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
          {% py nt = rule.nud_production.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
        tree.isExprNud = true;
          {% endif %}
        {% endif %}

        tree.add(left);

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect(ctx, {{morpheme.id}})); // {{morpheme}}
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
            {% if isinstance(rule.operator, InfixOperator) %}
        tree.isInfix = true;
            {% endif %}
        tree.add(parse_{{name}}_internal(ctx, get_infix_binding_power_{{name}}({{rule.operator.operator.id}}) - modifier));
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}(ctx));
          {% endif %}
        {% endfor %}
    }
      {% endif %}
    {% endfor %}

    return tree;
}

// END definitions for expression parser `{{name}}`
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
function parse_{{name}}(ctx) {
    var current = ctx.tokens.current();
    var rule = current != null ? table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] : -1;
    var tree = new ParseTree(new NonTerminal({{nonterminal.id}}, '{{name}}'));
    ctx.nonterminal = "{{name}}";

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist';
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
    tree.list = 'nlist';
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist';
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist';
    {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
    tree.list = 'otlist';
    {% else %}
    tree.list = false;
    {% endif %}

    {% if not grammar.must_consume_tokens(nonterminal) %}
    if (current != null && nonterminal_follow[{{nonterminal.id}}].indexOf(current.id) != -1 && nonterminal_first[{{nonterminal.id}}].indexOf(current.id) == -1) {
        return tree;
    }
    {% endif %}

    if (current == null) {
    {% if grammar.must_consume_tokens(nonterminal) %}
        throw new SyntaxError('Error: unexpected end of file');
    {% else %}
        return tree;
    {% endif %}
    }

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

      {% if index == 0 %}
    if (rule == {{rule.id}}) { // {{rule}}
      {% else %}
    else if (rule == {{rule.id}}) { // {{rule}}
      {% endif %}

        ctx.rule = rules[{{rule.id}}];

      {% if isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = new AstTransformSubstitution({{rule.ast.idx}});
      {% elif isinstance(rule.ast, AstSpecification) %}
        ast_parameters = {
        {% for k,v in rule.ast.parameters.items() %}
            '{{k}}': {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %},
        {% endfor %}
        }
        tree.astTransform = new AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters);
      {% else %}
        tree.astTransform = new AstTransformSubstitution(0);
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
        t = expect(ctx, {{morpheme.id}}); // {{morpheme}}
        tree.add(t);
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
        tree.listSeparator = t;
            {% endif %}
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
        subtree = parse_{{morpheme.string.lower()}}(ctx);
        tree.add(subtree);
        {% endif %}

      {% endfor %}
        return tree;
    }
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
    throw new SyntaxError(ctx.error_formatter.unexpected_symbol(
        ctx.nonterminal,
        ctx.tokens.current(),
        nonterminal_first[{{nonterminal.id}}],
        rules[{{rule.id}}]
    ));
    {% else %}
    return tree;
    {% endif %}
}
{% endfor %}

// Section: Lexer

{% if lexer %}

// START USER CODE
{{lexer.code}}
// END USER CODE

{% if re.search(r'function\s+default_action', lexer.code) is None %}
function default_action(context, mode, match, terminal, resource, line, col) {
    var tokens = []
    if (terminal) {
        tokens = [new Terminal(terminals[terminal], terminal, match, resource, line, col)]
    }
    return {tokens: tokens, mode: mode, context: context}
}

{% endif %}

{% if re.search(r'function\s+init', lexer.code) is None %}
function init() {
    return {}
}
{% endif %}

{% if re.search(r'function\s+destroy', lexer.code) is None %}
function destroy(context) {
    return 0;
}
{% endif %}

var regex = {
  {% for mode, regex_list in lexer.items() %}
    '{{mode}}': [
      {% for regex in regex_list %}
      [new RegExp({{regex.regex}}{{", "+' | '.join(['re.'+x for x in regex.options]) if regex.options else ''}}), {{"'" + regex.terminal.string.lower() + "'" if regex.terminal else 'null'}}, {{regex.function if regex.function else 'null'}}],
      {% endfor %}
    ],
  {% endfor %}
}

function _update_line_col(string, lexer_context) {
    var match_lines = string.split("\n")
    lexer_context.line += match_lines.length - 1
    if (match_lines.length == 1) {
        lexer_context.col += match_lines[0].length
    } else {
        lexer_context.col = match_lines[match_lines.length-1].length + 1
    }
}

function _unrecognized_token(string, line, col) {
    var lines = string.split('\n')
    var bad_line = lines[line-1]
    var message = 'Unrecognized token on line {0}, column {1}:\n\n{2}\n{3}'.format(
        line, col, bad_line, Array(col).join(' ') + '^'
    )
    throw new SyntaxError(message)
}

function _next(string, mode, context, resource, line, col) {
    for (i = 0; i < regex[mode].length; i++) {
        regexp = regex[mode][i][0];
        terminal = regex[mode][i][1];
        func = regex[mode][i][2];

        match = regexp.exec(string);

        if (match != null && match.index == 0) {
            if (func == null) {
                func = default_action;
            }

            lexer_match = func(context, mode, match[0], terminal, resource, line, col)
            tokens = lexer_match.tokens
            mode = lexer_match.mode
            context = lexer_match.context

            return {tokens: tokens, string: match[0], mode: mode}
        }
    }
    return {tokens: [], string: '', mode: mode}
}

function lex(string, resource) {
    lexer_context = {
        mode: 'default',
        line: 1,
        col: 1
    }
    user_context = init()

    string_copy = string
    parsed_tokens = []
    while (string.length) {
        lexer_match = _next(string, lexer_context.mode, user_context, resource, lexer_context.line, lexer_context.col)

        if (lexer_match.string.length == 0) {
            _unrecognized_token(string_copy, lexer_context.line, lexer_context.col)
        }

        string = string.substring(match[0].length)

        if (lexer_match.tokens == null) {
            _unrecognized_token(string_copy, lexer_context.line, lexer_context.col)
        }

        parsed_tokens.push.apply(parsed_tokens, lexer_match.tokens)

        lexer_context.mode = lexer_match.mode
        _update_line_col(lexer_match.string, lexer_context)

        if (false) {
            for (j=0; j<tokens.length; j++) {
                var token = tokens[j];
                console.log('token --> [{0}] [{1}, {2}] [{3}] [{4}] [{5}]'.format(
                    token.str,
                    token.line,
                    token.col,
                    token.source_string,
                    lexer_context.mode,
                    user_context
                ))
            }
        }
    }
    destroy(user_context)
    return new TokenStream(parsed_tokens)
}

{% endif %}

// Section: Main

{% if add_main %}

var main = function() {
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

          try {
              var tokens = lex(data, 'source');
          } catch(err) {
              console.log(err.to_string());
              process.exit(0);
          }

          if (tokens.list.length == 0) {
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
                      Base64.encode(token.source_string),
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
            token = new Terminal(
                terminals[file_tokens[i].terminal],
                file_tokens[i].terminal,
                file_tokens[i].source_string,
                file_tokens[i].resource,
                file_tokens[i].line,
                file_tokens[i].col
            );
            tokens.push(token);
        }
        try {
            tree = parse(new TokenStream(tokens));
            if (output == 'parsetree') {
                console.log(new ParseTreePrettyPrintable(tree).to_string());
            } else if (output == 'ast') {
                console.log(new AstPrettyPrintable(tree.to_ast()).to_string());
            }
        } catch (err) {
            console.log(err.message);
        }
    });
}

if (require.main === module) {
    main();
}

{% endif %}

// Section: Exports

{% if nodejs %}
module.exports = {
  {% if lexer %}
  lex: lex,
  {% endif %}
  parse: parse,
  terminals: terminals
}
{% endif %}
