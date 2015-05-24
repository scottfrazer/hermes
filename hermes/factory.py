import re
from copy import deepcopy
from collections import OrderedDict

from hermes.grammar import *
from hermes.hermes_parser import Terminal as HermesTerminal
from hermes.hermes_parser import Ast, AstList
from hermes.hermes_parser import lex as hermes_lex
from hermes.hermes_parser import parse as hermes_parse

supported_languages = ['python', 'c', 'java', 'javascript']

class GrammarFactory:
    # TODO: I want to get rid of name and start parameters
    def create(self, name, ast):
        self.next_id = 0
        self.binding_power = 0
        self.macros = {}

        all_rules = []
        all_nonterminals = {}
        all_terminals = {'_empty': EmptyString(-1)}
        all_macros = {}

        lexer = None
        lexer_asts = self.walk_ast(ast, 'Lexer')
        if lexer_asts:
            if len(lexer_asts) > 1:
                raise Exception("Expecting only one Lexer")
            lexer = self.parse_lexer(lexer_asts[0], all_terminals)

        expression_parser_asts = []
        start = None
        parser_ast = self.walk_ast(ast, 'Parser')

        if len(parser_ast) == 0:
            if lexer: lexer.terminals = all_terminals.values()
            return CompositeGrammar(
                name,
                [Rule(NonTerminal('start', 0), Production([all_terminals['_empty']]))],
                lexer
            )
        elif len(parser_ast) > 1:
            raise Exception('Expecting only one parser')
        else:
            for rule_ast in self.walk_ast(parser_ast[0], 'Rule'):
                if start is None:
                    start = self.get_morpheme_from_lexer_token(
                        rule_ast.attr('nonterminal'),
                        all_terminals,
                        all_nonterminals
                    )
                production_ast = rule_ast.attr('production')
                if isinstance(production_ast, Ast) and production_ast.name == 'ExpressionParser':
                    expression_parser_asts.append(rule_ast)
                else:
                    new_rules = self.parse_ll1_rule(rule_ast, all_terminals, all_nonterminals, all_macros)
                    all_rules.extend(new_rules)

            expression_grammars = []
            for expression_parser_ast in expression_parser_asts:
                nonterminal = self.get_morpheme_from_lexer_token(expression_parser_ast.attr('nonterminal'),
                                                                 all_terminals, all_nonterminals)
                for expression_rule_ast in expression_parser_ast.attr('production').attr('rules'):
                    rules = self.parse_expr_rule(expression_rule_ast, nonterminal, all_terminals, all_nonterminals,
                                                 all_macros)
                    all_rules.extend(rules)

            if lexer: lexer.terminals = all_terminals.values()
            return CompositeGrammar(name, all_rules, lexer)

    def get_macro_from_ast(self, ast, terminals, nonterminals):
        macro_string = self.macro_ast_to_string(ast)
        if macro_string not in self.macros:
            if ast.attr('name').source_string == 'list':
                macro = self.list(ast, terminals, nonterminals)
            elif ast.attr('name').source_string in ['tlist', 'otlist']:
                macro = self.tlist(
                    ast, terminals, nonterminals,
                    optional_termination=(ast.attr('name').source_string == 'otlist')
                )
            elif ast.attr('name').source_string == 'optional':
                macro = self.optional(ast, terminals, nonterminals)
            else:
                raise Exception("Invalid macro: " + str(macro_string))
            self.macros[macro_string] = macro
        return self.macros[macro_string]

    def parse_lexer(self, lexer_ast, terminals={}, nonterminals={}):
        lexer = AbstractLexer()
        lexer['default'] = []
        for lexer_atom in lexer_ast.attr('atoms'):
            if lexer_atom.name == 'Regex':
                regex = self.parse_regex(lexer_atom, terminals, nonterminals)
                lexer['default'].append(regex)
            if lexer_atom.name == 'Mode':
                mode_name = lexer_atom.attr('name').source_string
                if mode_name in lexer:
                    raise Exception("Lexer mode '{}' already exists".format(mode_name))
                lexer[mode_name] = self.parse_lexer_mode(lexer_atom, terminals, nonterminals)
            if lexer_atom.name == 'EnumeratedRegex':
                enumerated_regex = self.parse_enumerated_regex(lexer_atom, terminals, nonterminals)
                lexer['default'].append(enumerated_regex)
            if lexer_atom.name == 'RegexPartials':
                for partial in lexer_atom.attr('list'):
                    name = partial.attr('name').source_string
                    regex = partial.attr('regex').source_string
                    lexer.regex_partials[name] = regex
            if lexer_atom.name == 'LexerCode':
                language = lexer_atom.attr('language').source_string
                code = lexer_atom.attr('code').source_string.strip('\r\n')

                # Get rid of blank lines, remove leading spaces or tabs common to each line
                code_lines = [line for line in re.split(r'\r?\n', code) if len(line) > 0]
                leading_spaces = min([len(re.match('^\s*', line).group(0)) for line in code_lines])
                code_lines = [line[leading_spaces:] for line in code_lines]

                if language in lexer.code:
                    raise Exception('Lexer already defined code for language: ' + language)
                lexer.code[language] = '\n'.join(code_lines)
        return lexer

    def parse_enumerated_regex(self, enumerated_regex_ast, terminals, nonterminals):
        enumerated_regex = EnumeratedRegex()
        regex_outputs = self.parse_regex_outputs(enumerated_regex_ast.attr('onmatch'), terminals, nonterminals)
        for regex_enum_ast in enumerated_regex_ast.attr('enums'):
            language = regex_enum_ast.attr('language').source_string
            options_ast = regex_enum_ast.attr('options')
            if language not in supported_languages:
                raise Exception("Language not supported: " + language)
            enumerated_regex[language] = Regex(
                regex_enum_ast.attr('regex').source_string,
                [option.source_string for option in options_ast] if options_ast else [],
                regex_outputs
            )
        return enumerated_regex

    def parse_regex_outputs(self, outputs_ast, terminals, nonterminals):
        regex_outputs = []
        for regex_output in outputs_ast:
            if isinstance(regex_output, HermesTerminal):
                if regex_output.str == 'stack_push':
                    regex_outputs.append(LexerStackPush(regex_output.source_string))
                if regex_output.str == 'action':
                    if regex_output.source_string != 'pop':
                        raise Exception('parse_regex(): action must be "pop"')
                    regex_outputs.append(LexerAction(regex_output.source_string))
            elif regex_output.name == 'Terminal':
                (terminal, group) = self.parse_terminal(regex_output, terminals, nonterminals)
                regex_outputs.append(RegexOutput(
                    terminal, group, None
                ))
            elif regex_output.name == 'LexerFunctionCall':
                terminal_ast = regex_output.attr('terminal')
                (terminal, group) = self.parse_terminal(terminal_ast, terminals, nonterminals) if terminal_ast else (None, None)
                regex_outputs.append(RegexOutput(
                    terminal, group, regex_output.attr('name').source_string
                ))
                function = regex_output.attr('name').source_string
            elif regex_output.name == 'Null':
                if len(regex_outputs) != 0:
                    raise Exception('parse_regex(): "null" must be the only target of a regex')
        return regex_outputs

    def parse_regex(self, regex_ast, terminals, nonterminals):
        regex_outputs = self.parse_regex_outputs(regex_ast.attr('onmatch'), terminals, nonterminals)
        options = []
        if regex_ast.attr('options') is not None:
            for option in regex_ast.attr('options'):
                options.append(option.source_string)

        return Regex(
            regex_ast.attr('regex').source_string,
            options,
            regex_outputs
        )

    def parse_terminal(self, terminal_ast, terminals, nonterminals):
        terminal = self.get_morpheme_from_lexer_token(terminal_ast.attr('name'), terminals, nonterminals)
        group_terminal = terminal_ast.attr('group')
        group = 0
        if group_terminal and group_terminal.str == 'no_group':
            group = None
        if group_terminal and group_terminal.str == 'integer':
            group = int(group_terminal.source_string)
        return (terminal, group)

    def parse_lexer_mode(self, mode_ast, terminals, nonterminals):
        regex_list = []
        for ast in mode_ast.attr('atoms'):
            if ast.name == 'Regex':
                regex_list.append(self.parse_regex(ast, terminals, nonterminals))
            if ast.name == 'EnumeratedRegex':
                regex_list.append(self.parse_enumerated_regex(ast, terminals, nonterminals))
        return regex_list

    def parse_expr_rule(self, rule_ast, expr_nonterminal, terminals, nonterminals, macros):
        rules = []
        operator = None

        nonterminal = self.get_morpheme_from_lexer_token(rule_ast.attr('nonterminal'), terminals, nonterminals)
        production = rule_ast.attr('production')
        precedence = rule_ast.attr('precedence')

        associativity = None
        if precedence is not None:
            if precedence.attr('marker').str == 'asterisk':
                self.binding_power += 1000
            associativity = precedence.attr('associativity').source_string

        if nonterminal != expr_nonterminal:
            raise Exception('parse_expr_rule(): Expecting rule nonterminal to match parser nonterminal')

        if production.name == 'InfixProduction':
            morphemes = production.attr('morphemes')
            ast = production.attr('ast')

            if len(morphemes) != 3:
                raise Exception('parse_expr_rule(): InfixProduction needs 3 morphemes')

            first = self.get_morpheme_from_lexer_token(morphemes[0], terminals, nonterminals)
            operator = self.get_morpheme_from_lexer_token(morphemes[1], terminals, nonterminals)
            third = self.get_morpheme_from_lexer_token(morphemes[2], terminals, nonterminals)

            if not (first == third == expr_nonterminal):
                raise Exception("parse_expr_rule(): first == third == expr_nonterminal")
            if not isinstance(operator, Terminal):
                raise Exception("parse_expr_rule(): operator needs to be a terminal")

            rules.append(ExprRule(
                expr_nonterminal,
                Production([expr_nonterminal]),
                Production([operator, expr_nonterminal]),
                AstTranslation(0),
                self.parse_ast(ast),
                InfixOperator(operator, self.binding_power, associativity)
            ))

        elif production.name == 'MixfixProduction':
            nud_morphemes_ast = production.attr('nud')
            led_morphemes_ast = production.attr('led')
            led_ast = production.attr('ast')
            nud_ast = production.attr('nud_ast')

            nud_morphemes = []
            if nud_morphemes_ast:
                for nud_morpheme in nud_morphemes_ast:
                    if isinstance(nud_morpheme, Ast) and nud_morpheme.name == 'Macro':
                        macro = self.get_macro_from_ast(nud_morpheme, terminals, nonterminals)
                        macro_string = self.macro_ast_to_string(nud_morpheme)
                        if macro_string not in macros:
                            macros[macro_string] = macro
                        nud_morphemes.append(macro)
                    else:
                        nud_morphemes.append(self.get_morpheme_from_lexer_token(nud_morpheme, terminals, nonterminals))

            led_morphemes = []
            if led_morphemes_ast:
                for led_morpheme in led_morphemes_ast:
                    if isinstance(led_morpheme, Ast) and led_morpheme.name == 'Macro':
                        macro = self.get_macro_from_ast(led_morpheme, terminals, nonterminals)
                        macro_string = self.macro_ast_to_string(led_morpheme)
                        if macro_string not in macros:
                            macros[macro_string] = macro
                        led_morphemes.append(macro)
                    else:
                        led_morphemes.append(self.get_morpheme_from_lexer_token(led_morpheme, terminals, nonterminals))

            operator = None
            if len(led_morphemes):
                operator = MixfixOperator(led_morphemes[0], self.binding_power, associativity)

            rules.append(ExprRule(
                expr_nonterminal,
                Production(nud_morphemes),
                Production(led_morphemes),
                self.parse_ast(nud_ast),
                self.parse_ast(led_ast) if led_ast else None,
                operator
            ))

        elif production.name == 'PrefixProduction':
            morphemes = production.attr('morphemes')
            ast = production.attr('ast')

            if len(morphemes) != 2:
                raise Exception('parse_expr_rule(): InfixProduction needs 2 morphemes')

            operator = self.get_morpheme_from_lexer_token(morphemes[0], terminals, nonterminals)
            operand = self.get_morpheme_from_lexer_token(morphemes[1], terminals, nonterminals)

            if not operand == expr_nonterminal:
                raise Exception("parse_expr_rule(): operand == expr_nonterminal")
            if not isinstance(operator, Terminal):
                raise Exception("parse_expr_rule(): operator needs to be a terminal")

            rules.append(ExprRule(
                expr_nonterminal,
                Production([operator, expr_nonterminal]),
                Production(),
                AstTranslation(0),
                self.parse_ast(ast),
                PrefixOperator(operator, self.binding_power, associativity)
            ))

        else:
            raise Exception("Improperly formatted rule")

        return rules

    def parse_ll1_rule(self, rule_ast, terminals, nonterminals, macros):
        nonterminal = self.get_morpheme_from_lexer_token(rule_ast.attr('nonterminal'), terminals, nonterminals)
        production_list_ast = rule_ast.attr('production')

        rules = []
        for production_ast in production_list_ast:
            morphemes_list_ast = production_ast.attr('morphemes')
            ast_ast = production_ast.attr('ast')
            morphemes = []
            for morpheme_ast in morphemes_list_ast:
                if isinstance(morpheme_ast, HermesTerminal):
                    morpheme = self.get_morpheme_from_lexer_token(morpheme_ast, terminals, nonterminals)
                elif isinstance(morpheme_ast, Ast) and morpheme_ast.name == 'Macro':
                    morpheme = self.get_macro_from_ast(morpheme_ast, terminals, nonterminals)
                    macro_string = self.macro_ast_to_string(morpheme_ast)
                    if macro_string not in macros:
                        macros[macro_string] = morpheme
                else:
                    raise Exception('Unknown AST element: ' + morpheme_ast)
                morphemes.append(morpheme)
            ast = self.parse_ast(ast_ast)
            rules.append(Rule(nonterminal, Production(morphemes), id=0, root=0, ast=ast))
        return rules

    def parse_ast(self, ast_ast):
        if ast_ast is None:
            return AstTranslation(0)
        elif isinstance(ast_ast, Ast) and ast_ast.name == 'AstTransformation':
            node_name = ast_ast.attr('name').source_string
            parameters = OrderedDict()
            for parameter_ast in ast_ast.attr('parameters'):
                name = parameter_ast.attr('name').source_string
                index = parameter_ast.attr('index').source_string
                parameters[name] = index
            return AstSpecification(node_name, parameters)
        elif isinstance(ast_ast, HermesTerminal) and ast_ast.str == 'nonterminal_reference':
            return AstTranslation(int(ast_ast.source_string))
        else:
            raise Exception('parse_ast(): invalid AST: ' + ast_ast)

    def macro_ast_to_string(self, ast):
        return '{}({})'.format(ast.attr('name').source_string,
                               ','.join([self.morpheme_to_string(x) for x in ast.attr('parameters')]))

    def morpheme_to_string(self, morpheme):
        return ':' + morpheme.source_string if morpheme.str == 'terminal' else '$' + morpheme.source_string

    def get_morpheme_from_lexer_token(self, token, terminals, nonterminals):
        if token.str == 'nonterminal':
            nonterminal = token.source_string.lower()
            if nonterminal not in nonterminals:
                nonterminals[nonterminal] = NonTerminal(nonterminal, len(nonterminals))
            return nonterminals[nonterminal]
        if token.str == 'terminal':
            terminal = token.source_string.lower()
            if terminal not in terminals:
                terminals[terminal] = Terminal(terminal, len(terminals))
            return terminals[terminal]

    def generate_nonterminal(self, nonterminals):
        name = '_gen' + str(self.next_id)
        self.next_id += 1
        nt = NonTerminal(name, len(nonterminals), generated=True)
        nonterminals[nt.string] = nt
        return nt

    def list(self, ast, terminals, nonterminals):
        morpheme = self.get_morpheme_from_lexer_token(ast.attr('parameters')[0], terminals, nonterminals)

        separator = None
        if len(ast.attr('parameters')) > 1 and ast.attr('parameters')[1].str is not 'null':
            separator = self.get_morpheme_from_lexer_token(ast.attr('parameters')[1], terminals, nonterminals)

        minimum = 0
        if len(ast.attr('parameters')) > 2:
            minimum = int(ast.attr('parameters')[2].source_string)

        nt0 = self.generate_nonterminal(nonterminals)
        nt1 = self.generate_nonterminal(nonterminals)
        empty = terminals['_empty']

        prod = [morpheme] * max(minimum, 1)
        if separator is not None and minimum > 0:
            prod = [m if i % 2 == 0 else separator for i, m in enumerate([morpheme] * (minimum * 2 - 1))]
        prod.append(nt1)

        rules = [
            MacroGeneratedRule(nt0, Production(prod)),
            MacroGeneratedRule(nt1, Production([separator, morpheme, nt1] if separator else [morpheme, nt1])),
            MacroGeneratedRule(nt1, Production([empty]))
        ]

        if minimum == 0:
            rules.append(MacroGeneratedRule(nt0, Production([empty])))

        macro = LL1ListMacro(morpheme, separator, minimum, nt0, False, False, rules)

        for rule in rules:
            rule.nonterminal.macro = macro

        return macro

    def tlist(self, ast, terminals, nonterminals, optional_termination=False):
        morpheme = self.get_morpheme_from_lexer_token(ast.attr('parameters')[0], terminals, nonterminals)
        separator = self.get_morpheme_from_lexer_token(ast.attr('parameters')[1], terminals, nonterminals)
        minimum = int(ast.attr('parameters')[2].source_string) if len(ast.attr('parameters')) > 2 else 0
        nt0 = self.generate_nonterminal(nonterminals)
        nt1 = self.generate_nonterminal(nonterminals)
        empty = terminals['_empty']

        start_production = []
        if minimum > 0:
            for x in range(minimum):
                start_production.extend([morpheme, separator])
            start_production = start_production[:-1]
        else:
            start_production.append(morpheme)
        start_production.append(nt1)

        if optional_termination:
            nt2 = self.generate_nonterminal(nonterminals)
            termination_rules = [
                MacroGeneratedRule(nt1, Production([separator, nt2])),
                MacroGeneratedRule(nt1, Production([empty])),
                MacroGeneratedRule(nt2, Production([morpheme, nt1])),
                MacroGeneratedRule(nt2, Production([empty]))
            ]
        else:
            termination_rules = [
                MacroGeneratedRule(nt1, Production([separator, nt0]))
            ]

        rules = [
            MacroGeneratedRule(nt0, Production(start_production)),
        ]
        rules.extend(termination_rules)
        if minimum == 0:
            rules.append(MacroGeneratedRule(nt0, Production([empty])))
        macro = LL1ListMacro(morpheme, separator, minimum, nt0, True, optional_termination, rules)

        for rule in rules:
            rule.nonterminal.macro = macro

        return macro

    def optional(self, ast, terminals, nonterminals):
        morpheme = self.get_morpheme_from_lexer_token(ast.attr('parameters')[0], terminals, nonterminals)
        nt0 = self.generate_nonterminal(nonterminals)
        empty = terminals['_empty']
        rules = [
            MacroGeneratedRule(nt0, Production([morpheme])),
            MacroGeneratedRule(nt0, Production([empty]))
        ]

        macro = OptionalMacro(morpheme, nt0, rules)

        for rule in rules:
            rule.nonterminal.macro = macro

        return macro

    def walk_ast_terminal(self, ast, terminal):
        nodes = []
        if isinstance(ast, HermesTerminal) and ast.str == terminal:
            return [ast]
        if not isinstance(ast, Ast): return nodes
        for key, sub in ast.attributes.items():
            if isinstance(sub, HermesTerminal) and sub.str == terminal:
                nodes.append(sub)
            elif isinstance(sub, Ast):
                nodes.extend(self.walk_ast_terminal(sub, terminal))
            elif isinstance(sub, AstList):
                for ast1 in sub:
                    nodes.extend(self.walk_ast_terminal(ast1, terminal))
        return nodes

    def walk_ast(self, ast, node_name):
        nodes = []
        if not isinstance(ast, Ast): return nodes
        if ast.name == node_name: nodes.append(ast)
        for key, sub in ast.attributes.items():
            if isinstance(sub, Ast):
                nodes.extend(self.walk_ast(sub, node_name))
            elif isinstance(sub, AstList):
                for ast in sub:
                    nodes.extend(self.walk_ast(ast, node_name))
        return nodes

def get_parse_tree(source, resource='<string>'):
    return hermes_parse(hermes_lex(source, resource))

def get_ast(source, resource='<string>'):
    tree = hermes_parse(hermes_lex(source, resource))
    return tree.ast()

def parse(source, name, resource='<string>'):
    ast = get_ast(source, resource)
    return GrammarFactory().create(name, ast)
