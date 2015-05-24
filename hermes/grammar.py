from copy import copy, deepcopy
import re
from collections import OrderedDict


class Morpheme:
    def __init__(self, string, id=0):
        self.__dict__.update(locals())

    def __eq__(self, other):
        return str(other) == str(self)

    def __hash__(self):
        return hash(str(self))


class NonTerminal(Morpheme):
    def __init__(self, string, id=0, generated=False, macro=None):
        self.__dict__.update(locals())
        super().__init__(string, id)

    def id(self):
        return self.id

    def setMacro(self, macro):
        self.macro = macro

    def __str__(self):
        return '$e' if self.string == '_expr' else '$' + self.string

    def first(self):
        return


class Terminal(Morpheme):
    def __init__(self, string, id=0):
        super().__init__(string, id)

    def id(self):
        return self.id

    def __str__(self):
        return ':' + self.string

    def first(self):
        return {self}


class AbstractTerminal(Terminal):
    pass


class EmptyString(AbstractTerminal):
    def __init__(self, id):
        super().__init__('_empty', id)

    def __str__(self):
        return ':_empty'


class EndOfStream(AbstractTerminal):
    def __init__(self, id):
        super().__init__('_eos', id)

    def __str__(self):
        return ':_eos'


class Production:
    def __init__(self, morphemes=[]):
        self.__dict__.update(locals())

    def __len__(self):
        return len(self.morphemes)

    def __eq__(self, other):
        for index, morpheme in enumerate(self.morphemes):
            try:
                if other.morhemes[index] != morpheme:
                    return False
            except:
                return False
        return True

    def __str__(self):
        return ' '.join([str(p) for p in self.morphemes])


class Rule:
    def __init__(self, nonterminal, production, id=None, root=None, ast=None):
        self.__dict__.update(locals())

    def __copy__(self):
        return Rule(self.nonterminal, Production(copy(self.production.morphemes)), self.id, self.root, self.ast)

    def expand(self):
        morphemes = []
        rules = []
        for m in self.production.morphemes:
            if isinstance(m, Macro):
                rules.extend(m.rules)
                morphemes.append(m.start_nt)
            else:
                morphemes.append(m)
        rules.append(Rule(self.nonterminal, Production(morphemes), self.id, self.root, self.ast))
        return rules

    def __getattr__(self, name):
        if name == 'is_empty':
            return len(self.production.morphemes) == 1 and self.production.morphemes[0] == EmptyString(-1)
        if name == 'morphemes':
            # TODO: This is only around because Grammar.__init__() needs it for making ExprRule and Rule both able to do this
            return self.production.morphemes
        return self.__dict__[name]

    def __str__(self):
        ast = ''
        if self.ast and not (isinstance(self.ast, AstTranslation) and self.ast.idx == 0):
            ast = ' -> {0}'.format(self.ast)

        return "{0} = {1}{2}".format(str(self.nonterminal), str(self.production), ast)

    def __eq__(self, other):
        return str(other) == str(self)

    def __hash__(self):
        return hash(str(self))


class MacroGeneratedRule(Rule):
    pass


class AstSpecification:
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        return self.name + '( ' + ', '.join(['%s=$%s' % (k, str(v)) for k, v in self.parameters.items()]) + ' )'


class AstTranslation:
    def __init__(self, idx):
        self.idx = idx

    def __str__(self):
        return '$' + str(self.idx)


class ExprRule:
    def __init__(self, nonterminal, nud_production, ledProduction, nudAst, ast, operator, id=0):
        self.__dict__.update(locals())
        self.production = Production(nud_production.morphemes + ledProduction.morphemes)
        if (not nud_production or not len(nud_production)) and \
                (not ledProduction or not len(ledProduction)):
            raise Exception('Rule must contain a NUD or a LED portion.')
        # TODO: this should be a conflict
        root = self.ledProduction.morphemes[0] if self.ledProduction and len(self.ledProduction) else None
        if root and not isinstance(root, Terminal):
            raise Exception('Root of expression rule must be a terminal.')

    def __copy__(self):
        np = Production(copy(self.nud_production.morphemes))
        lp = Production(copy(self.ledProduction.morphemes))
        return ExprRule(self.nonterminal, np, lp, self.nudAst, self.ast, self.operator)

    def __getattr__(self, name):
        if name == 'morphemes':
            all = []
            for morpheme in self.nud_production.morphemes:
                all.append(morpheme)
            for morpheme in self.ledProduction.morphemes:
                all.append(morpheme)
            return all
        return self.__dict__[name]

    def expand(self):
        nudMorphemes = []
        ledMorphemes = []
        rules = []
        for morpheme in self.nud_production.morphemes:
            if isinstance(morpheme, Macro):
                rules.extend(morpheme.rules)
                nudMorphemes.append(morpheme.start_nt)
            else:
                nudMorphemes.append(morpheme)
        for morpheme in self.ledProduction.morphemes:
            if isinstance(morpheme, Macro):
                rules.extend(morpheme.rules)
                ledMorphemes.append(morpheme.start_nt)
            else:
                ledMorphemes.append(morpheme)
        rules.append(
            ExprRule(self.nonterminal, Production(nudMorphemes), Production(ledMorphemes), self.nudAst, self.ast, self.operator)
        )
        return rules

    def __str__(self):
        def ast_to_str(ast):
            if isinstance(ast, AstTranslation) and ast.idx == 0:
                return ''
            return ' -> ' + str(ast) if ast else ''

        if isinstance(self.operator, InfixOperator):
            return '{nt} = {nt} {op} {nt}{ast}'.format(
                nt=self.nonterminal,
                op=self.operator.operator,
                ast=ast_to_str(self.ast)
            )
        elif isinstance(self.operator, PrefixOperator):
            return '{nt} = {op} {nt}{ast}'.format(
                nt=self.nonterminal,
                op=self.operator.operator,
                ast=ast_to_str(self.ast)
            )
        elif isinstance(self.operator, MixfixOperator):
            led = ' <=> {}'.format(str(self.ledProduction)) if len(self.ledProduction.morphemes) else ''
            return '{nt} = {nud}{nud_ast}{led}{ast}'.format(
                nt=self.nonterminal,
                nud=self.nud_production,
                nud_ast=ast_to_str(self.nudAst),
                led=led,
                ast=ast_to_str(self.ast)
            )
        else:
            return '{nt} = {nud}{nud_ast}'.format(
                nt=self.nonterminal,
                nud=self.nud_production,
                nud_ast=ast_to_str(self.nudAst)
            )


class Operator:
    def __init__(self, operator, binding_power, associativity):
        self.__dict__.update(locals())

    def __str__(self):
        return '<Operator {}, binding_power={}, associativity={}>'.format(
            self.operator,
            self.binding_power,
            self.associativity
        )


class InfixOperator(Operator):
    def str(self):
        return "<Infix {}>".format(super(InfixOperator, self))


class PrefixOperator(Operator):
    def str(self):
        return "<Prefix {}>".format(super(PrefixOperator, self))


class MixfixOperator(Operator):
    def str(self):
        return "<Mixfix {}>".format(super(MixfixOperator, self))


class Regex:
    def __init__(self, regex, options, outputs):
        self.__dict__.update(locals())

class EnumeratedRegex(OrderedDict):
    def __init__(self):
        super().__init__()
        self.__dict__.update(locals())

class RegexOutput:
    def __init__(self, terminal, group, function):
        self.__dict__.update(locals())

class LexerStackPush:
    def __init__(self, mode):
        self.__dict__.update(locals())

class LexerAction:
    def __init__(self, action):
        self.__dict__.update(locals())

class Lexer(OrderedDict):
    pass

class AbstractLexer(OrderedDict):
    code = ''

    def __init__(self):
        super().__init__()
        self.regex_partials = OrderedDict()
        self.code = OrderedDict()

    def convert_regex_str(self, regex_str, language):
        if regex_str[0] == "'" and language in ['c', 'java']:
            regex_str = regex_str[1:-1].replace('"', '\\"')
            return '"{}"'.format(regex_str)

        if regex_str[:2] in ["r'", 'r"'] and language in ['c', 'java', 'javascript']:
            # http://en.wikipedia.org/wiki/Escape_sequences_in_C#Table_of_escape_sequences
            regex_str = re.sub(r'\\(?![abfnrtv\'\?"]|u[0-9a-fA-F]{4}|[0-7]{3}|x[0-9a-fA-F]{2})', r'\\\\', regex_str[2:-1])
            regex_str = re.sub(r'"(?<!\\)', r'\"', regex_str)
            regex_str = re.sub(r"'(?<!\\)", r"\'", regex_str)
            return '"{}"'.format(regex_str)

        return regex_str

    def get_language_regex(self, regex, partials, language):
        if isinstance(regex, EnumeratedRegex):
            if language not in regex:
                raise Exception('Regex enumeration does not contain a regex for language: ' + language)
            regex = regex[language]
        regex = deepcopy(regex)
        for partial_name, partial in partials.items():
            regex.regex = regex.regex.replace('{{%{0}%}}'.format(partial_name), partial)
        regex.regex = self.convert_regex_str(regex.regex, language)
        return regex

    def strip_quotes(self, regex_str):
        if regex_str[:2] in ['r"', "r'"]:
            return regex_str[2:-1]
        if regex_str[0] in ['"', "'"]:
            return regex_str[1:-1]

    # Return a NEW lexer specifically for this language
    def get_language_lexer(self, language):
        lexer = Lexer()

        # 1) Build a dictionary of the partials with partials replaced within partials
        partials = OrderedDict()
        for partial_name, partial in self.regex_partials.items():
            partials[partial_name] = self.strip_quotes(self.convert_regex_str(partial, language))
        for partial_name, partial in partials.items():
            for partial_name1, partial1 in partials.items():
                partials[partial_name] = partials[partial_name].replace('{{%{0}%}}'.format(partial_name1), partial1)

        # 2) Convert enumerated regular expressions based on language, get copies
        for mode, regex_list in self.items():
            lexer[mode] = [self.get_language_regex(regex, partials, language) for regex in regex_list]

        lexer.code = self.code[language] if language in self.code else ''
        return lexer

    def __str__(self):
        return ', '.join(self.keys())


class CompositeGrammar:
    _empty = EmptyString(-1)
    _end = EndOfStream(-1)

    def __init__(self, name, rules, lexer):
        self.__dict__.update(locals())
        self.start = None
        self.terminals = set()
        self.nonterminals = set()
        self.macros = set()
        self.expression_terminals = dict()
        self.expression_nonterminals = set()
        self.expanded_rules = list()

        expanded_rules = OrderedDict()
        for rule in rules.copy():
            self.nonterminals.add(rule.nonterminal)
            if self.start is None:
                self.start = rule.nonterminal
            if isinstance(rule, ExprRule):
                expression_terminal = Terminal(rule.nonterminal.string.lower())
                if expression_terminal not in self.terminals:
                    self.expression_nonterminals.add(rule.nonterminal)
                    self.expression_terminals[rule.nonterminal] = expression_terminal
                    self.terminals.add(expression_terminal)
            for expanded_rule in rule.expand():
                if expanded_rule not in self.expanded_rules:
                    self.expanded_rules.append(expanded_rule)
                    for morpheme in expanded_rule.production.morphemes:
                        if isinstance(morpheme, Terminal):
                            self.terminals.add(morpheme)
                        elif isinstance(morpheme, NonTerminal):
                            self.nonterminals.add(morpheme)
                            if morpheme.macro:
                                self.macros.add(morpheme.macro)

        if lexer:
            def iterate_outputs(outputs):
                for output in outputs:
                    if isinstance(output, RegexOutput) and output.terminal is not None:
                        self.terminals.add(output.terminal)
            for mode, regex_list in lexer.items():
                for regex in regex_list:
                    if isinstance(regex, Regex):
                        iterate_outputs(regex.outputs)
                    if isinstance(regex, EnumeratedRegex):
                        for language, regex in regex.items():
                            iterate_outputs(regex.outputs)

        self.first_sets = None
        self.follow_sets = None
        progress = True

        # Calculate first/follow sets
        while progress:
            self.first_sets, first_set_changed = self._compute_first(self.first_sets)
            self.follow_sets, follow_set_changed = self._compute_follow(self.first_sets, self.follow_sets)
            progress = first_set_changed | follow_set_changed

        self._compute_conflicts()

        for conflict in self.conflicts:
            if isinstance(conflict, FirstFirstConflict):
                conflict.grammar = self

        nonterminal_rules = {str(n): list() for n in self.nonterminals}
        for rule in self.expanded_rules:
            for morpheme in rule.morphemes:
                if isinstance(morpheme, NonTerminal):
                    nonterminal_rules[str(morpheme)].append(rule)

        for nonterminal in self.nonterminals:
            if not len(nonterminal_rules[
                str(nonterminal)]) and not nonterminal.generated and nonterminal is not self.start:
                self.warnings.append(UnusedNonterminalWarning(nonterminal))
            nRules = self.get_expanded_rules(nonterminal)
            if len(nRules) == 0 and nonterminal is not self.start and nonterminal not in self.expression_nonterminals:
                self.conflicts.append(UndefinedNonterminalConflict(nonterminal))
        self._assignIds()

    def __getattr__(self, name):
        if name == 'll1_nonterminals':
            return [x for x in self.nonterminals if x not in [n for n in self.expression_nonterminals]]
        elif name == 'standard_terminals':
            return [terminal for terminal in self.terminals if terminal not in [self._empty, self._end]]
        elif name == 'grammar_expanded_rules':
            return self.__dict__['grammar_expanded_rules']
        elif name == 'grammar_expanded_expr_rules':
            grammar_rules = {}
            for grammar, rules in self.grammar_expanded_rules.items():
                grammar_rules[grammar] = list(filter(lambda x: isinstance(x, ExprRule), rules))
            return grammar_rules
        elif name == 'parse_table':
            if 'parse_table' in self.__dict__:
                return self.__dict__['parse_table']
            nonterminals = {n.id: n for n in self.nonterminals}
            terminals = {t.id: t for t in self.standard_terminals}
            sort = lambda x: [x[key] for key in sorted(x.keys())]
            table = []
            for nonterminal in sort(nonterminals):
                rules = []
                for terminal in sort(terminals):
                    next = None
                    for rule in self.getExpandedLL1Rules(nonterminal):
                        Fip = self.first(rule.production)
                        if terminal in Fip or (self._empty in Fip and terminal in self.follow(nonterminal)):
                            next = rule
                            break
                    rules.append(next)
                table.append(rules)
            self.__dict__['parse_table'] = table
            return table
        else:
            return self.__dict__[name]

    def first(self, element):
        if isinstance(element, Production):
            first_set = set()
            add_empty_token = True
            for morpheme in element.morphemes:
                morpheme_first_set = set([morpheme]) if isinstance(morpheme, Terminal) else self.first_sets[morpheme]
                toks = morpheme_first_set.difference({self._empty})
                if len(toks) > 0:
                    first_set = first_set.union(toks)
                if self._empty not in morpheme_first_set:
                    add_empty_token = False
                    break
            if add_empty_token:
                first_set.add(self._empty)
            return first_set
        elif isinstance(element, Terminal):
            return {element}
        elif isinstance(element, NonTerminal):
            return self.first_sets[element]

    def follow(self, element):
        if isinstance(element, NonTerminal):
            return self.follow_sets[element]

    def must_consume_tokens(self, nonterminal):
        return self._empty not in self.first(nonterminal)

    def _compute_first(self, first=None):
        if first is None:
            first = {nt: set() for nt in self.nonterminals}
        for nt, t in self.expression_terminals.items():
            first[nt].add(t)
        changed = False
        progress = True
        while progress == True:
            progress = False
            for rule in self.expanded_rules:
                try:
                    morpheme = rule.production.morphemes[0]
                except IndexError:
                    continue

                # TODO: filter out extraneous _empty's in grammar files (e.g. x := _empty + 'a' + _empty)
                if (isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString)) and morpheme not in first[rule.nonterminal]:
                    progress = changed = True
                    first[rule.nonterminal] = first[rule.nonterminal].union({morpheme})

                elif isinstance(morpheme, NonTerminal):
                    add_empty_token = True
                    for morpheme in rule.production.morphemes:

                        if isinstance(morpheme, NonTerminal):
                            sub = first[morpheme]
                        elif isinstance(morpheme, Terminal):
                            sub = {morpheme}
                        else:
                            raise Exception('Error: expected either terminal or nonterminal, got ' + morpheme)
                        if not first[rule.nonterminal].issuperset(sub.difference({self._empty})):
                            progress = changed = True
                            first[rule.nonterminal] = first[rule.nonterminal].union(sub.difference({self._empty}))
                        if self._empty not in sub:
                            add_empty_token = False
                            break
                    if add_empty_token:
                        first[rule.nonterminal] = first[rule.nonterminal].union({self._empty})
        return (first, changed)

    def _compute_follow(self, first, follow=None):
        if follow is None:
            follow = {nt: set() for nt in self.nonterminals}
            follow[self.start] = {self._end}
        changed = False
        progress = True
        while progress == True:
            progress = False

            for rule in self.expanded_rules:
                for index, morpheme in enumerate(rule.production.morphemes):

                    if isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString):
                        continue

                    try:
                        next_morpheme = rule.production.morphemes[index + 1]
                    except IndexError:
                        next_morpheme = None

                    if next_morpheme:
                        next_first_set = set([next_morpheme]) if isinstance(next_morpheme, Terminal) else first[
                            next_morpheme].difference({self._empty})
                        if not follow[morpheme].issuperset(next_first_set):
                            progress = changed = True
                            follow[morpheme].update(next_first_set)

                    if not next_morpheme or self._empty in self.first(
                            Production(rule.production.morphemes[index + 1:])):
                        rule_follow_set = follow[rule.nonterminal]
                        morpheme_follow_set = follow[morpheme]

                        if not morpheme_follow_set.issuperset(rule_follow_set):
                            progress = changed = True
                            follow[morpheme] = morpheme_follow_set.union(rule_follow_set)
        return (follow, changed)

    def _compute_conflicts(self):
        self.conflicts = []
        self.warnings = []
        nud = {}
        led = {}

        nonterminal_rules = {n: list() for n in self.nonterminals}
        for rule in self.expanded_rules:
            for morpheme in rule.morphemes:
                if isinstance(morpheme, NonTerminal):
                    nonterminal_rules[morpheme].append(rule)
            if isinstance(rule, ExprRule):
                # For 'mixfix' rules... make sure no two nud/led functions start with the same thing.
                if rule.operator is None and len(rule.nud_production):
                    morpheme = rule.nud_production.morphemes[0]
                    if morpheme not in nud:
                        nud[morpheme] = list()
                    if len(nud[morpheme]):
                        self.conflicts.append(NudConflict(morpheme, [rule] + nud[morpheme]))
                    nud[morpheme].append(rule)
                if len(rule.ledProduction):
                    # TODO: no test for this code path
                    morpheme = rule.nud_production.morphemes[0]
                    if morpheme not in led:
                        led[morpheme] = list()
                    if rule in led[morpheme]:
                        self.conflicts.append(NudConflict(morpheme, [rule] + led[morpheme]))
                    led[morpheme].append(rule)

        for N in self.nonterminals:
            if self._empty in self.first(N) and len(self.first(N).intersection(self.follow(N))):
                self.conflicts.append(FirstFollowConflict(N, self.first(N), self.follow(N)))

            if len(nonterminal_rules[N]) == 0 and N != self.start:
                self.warnings.append(UnusedNonterminalWarning(N))

            NR = self.get_expanded_rules(N)
            if len(NR) == 0:
                self.conflicts.append(UndefinedNonterminalConflict(N))

            if N not in self.expression_nonterminals:
                for x in NR:
                    for y in NR:
                        if x == y:
                            continue

                        x_first = self.first(x.production)
                        y_first = self.first(y.production).difference({self._empty})
                        intersection = x_first.intersection(y_first)
                        if len(intersection) != 0:
                            self.conflicts.append(FirstFirstConflict(x, y, self))
        return self.conflicts

    def _assignIds(self):
        morphemes = {}
        i = 0
        for terminal in self.terminals:
            if not isinstance(terminal, AbstractTerminal):
                terminal.id = i
                morphemes[str(terminal)] = terminal.id
                i += 1
        for nonterminal in self.nonterminals:
            nonterminal.id = i
            morphemes[str(nonterminal)] = nonterminal.id
            i += 1

        for rule_set in [self.rules, self.expanded_rules]:
            for i, rule in enumerate(rule_set):
                rule.id = i
                if isinstance(rule, Rule):
                    for morpheme in rule.production.morphemes:
                        if str(morpheme) in morphemes:
                            morpheme.id = morphemes[str(morpheme)]
                if isinstance(rule, ExprRule):
                    for morpheme in rule.nud_production.morphemes:
                        if str(morpheme) in morphemes:
                            morpheme.id = morphemes[str(morpheme)]
                    for morpheme in rule.ledProduction.morphemes:
                        if str(morpheme) in morphemes:
                            morpheme.id = morphemes[str(morpheme)]

    def get_expanded_rules(self, nonterminal=None):
        if nonterminal:
            return [rule for rule in self.expanded_rules if str(rule.nonterminal) == str(nonterminal)]
        return self.expanded_rules

    def get_rules(self, nonterminal=None):
        if nonterminal:
            return [rule for rule in self.rules if str(rule.nonterminal) == str(nonterminal)]
        return self.expanded_rules

    def ruleFirst(self, rule):
        if isinstance(rule, ExprRule):
            if len(rule.nud_production) and rule.nud_production.morphemes[0] != rule.nonterminal:
                return self._pfirst(rule.nud_production)
        return self._pfirst(rule.production)

    def getExpressionTerminal(self):
        # TODO: this needs to be fixed.
        return self.expression_terminals

    def getExpandedLL1Rules(self, nonterminal=None):
        all_rules = [rule for rule in self.expanded_rules if isinstance(rule, Rule)]
        if nonterminal:
            return [rule for rule in all_rules if str(rule.nonterminal) == str(nonterminal)]
        return all_rules


class Conflict:
    pass


class Warning:
    pass


class UnusedNonterminalWarning(Warning):
    def __init__(self, nonterminal):
        self.__dict__.update(locals())

    def __str__(self):
        string = ' -- Unused Nonterminal -- \n'
        string += 'Nonterminal %s is defined but not used' % (self.nonterminal)
        return string


class UndefinedNonterminalConflict(Conflict):
    def __init__(self, nonterminal):
        self.__dict__.update(locals())

    def __str__(self):
        string = ' -- Undefined Nonterminal Conflict-- \n'
        string += 'Nonterminal %s is used but not defined' % (self.nonterminal)
        return string


class ExprConflict(Conflict):
    def __init__(self, terminal, rules):
        self.terminal = terminal
        self.rules = rules

    def __str__(self):
        string = " -- %s conflict -- \n" % (self.type)
        string += "Terminal %s requires two different %s() functions.  Cannot choose between these rules:\n\n" % (
        self.terminal, self.type)
        for rule in self.rules:
            string += "%s\n" % (rule)
        return string


class NudConflict(ExprConflict):
    type = "NUD"


class LedConflict(ExprConflict):
    type = "LED"


class ListFirstFollowConflict(Conflict):
    def __init__(self, listMacro, firstNonterminal, followList):
        self.listMacro = listMacro
        self.firstNonterminal = firstNonterminal
        self.followList = followList

    def __str__(self):
        string = " -- LIST FIRST/FOLLOW conflict --\n"
        string += "FIRST(%s) = {%s}\n" % (
        self.listMacro.nonterminal, ', '.join([str(e) for e in self.firstNonterminal]))
        string += "FOLLOW(%s) = {%s}\n" % (self.listMacro, ', '.join([str(e) for e in self.followList]))
        string += "FIRST(%s) ∩ FOLLOW(%s): {%s}\n" % (self.listMacro.nonterminal, self.listMacro, ', '.join(
            [str(e) for e in self.firstNonterminal.intersection(self.followList)]))
        return string


class FirstFirstConflict(Conflict):
    def __init__(self, rule1, rule2, grammar):
        self.__dict__.update(locals())

    def __str__(self):
        rule1_first = self.grammar.first(self.rule1.production)
        rule2_first = self.grammar.first(self.rule2.production)
        string = " -- FIRST/FIRST conflict --\n"
        string += "Two rules for nonterminal %s have intersecting first sets.  Can't decide which rule to choose based on terminal.\n\n" % (
        self.rule1.nonterminal)
        string += "(Rule-%d)  %s\n" % (self.rule1.id, self.rule1)
        string += "(Rule-%d)  %s\n\n" % (self.rule2.id, self.rule2)
        string += "first(Rule-%d) = {%s}\n" % (self.rule1.id, ', '.join(sorted([str(e) for e in rule1_first])))
        string += "first(Rule-%d) = {%s}\n" % (self.rule2.id, ', '.join(sorted([str(e) for e in rule2_first])))
        string += "first(Rule-%d) ∩ first(Rule-%d): {%s}\n" % (
        self.rule1.id, self.rule2.id, ', '.join(sorted([str(e) for e in rule1_first.intersection(rule2_first)])))

        return string


class FirstFollowConflict(Conflict):
    def __init__(self, N, firstN, followN):
        self.N = N
        self.firstN = firstN
        self.followN = followN

    def __str__(self):
        string = ' -- FIRST/FOLLOW conflict --\n'
        string += 'Nonterminal %s has a first and follow set that overlap.\n\n' % (self.N)
        string += "first(%s) = {%s}\n" % (self.N, ', '.join(sorted([str(e) for e in self.firstN])))
        string += "follow(%s) = {%s}\n\n" % (self.N, ', '.join(sorted([str(e) for e in self.followN])))
        string += 'first(%s) ∩ follow(%s) = {%s}\n' % (
        self.N, self.N, ', '.join([str(e) for e in self.firstN.intersection(self.followN)]))

        return string


class Macro(Morpheme):
    id = -1


class ListMacro(Macro):
    def setFollow(self, follow):
        self.__dict__.update(locals())


class LL1ListMacro(ListMacro):
    def __init__(self, nonterminal, separator, minimum, start_nt, sep_terminates, terminator_optional, rules):
        self.__dict__.update(locals())
        if start_nt:
            self.start_nt.setMacro(self)

    def __repr__(self):
        return 'list(nt={0}, sep={1}, min={2}, sep_terminates={3})'.format(str(self.nonterminal), str(self.separator), str(self.minimum), self.sep_terminates)

    def __str__(self): return self.__repr__()

class OptionalMacro(Macro):
    def __init__(self, nonterminal, start_nt, rules):
        self.__dict__.update(locals())
        if start_nt:
            self.start_nt.setMacro(self)

    def __repr__(self):
        return 'optional({0})'.format(str(self.nonterminal))
