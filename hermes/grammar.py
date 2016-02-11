from copy import copy, deepcopy
import re
from collections import OrderedDict
import itertools

def pairwise(iterable):
    i = list(range(len(iterable)))
    c = list(iterable)
    n = iterable[1:]
    n.append(None)
    return zip(i, c, n)

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

    def slice(self, start, stop=None):
        return Production(list(itertools.islice(self.morphemes, start, stop, 1)))

class ListProduction:
    def __init__(self, list_parser):
        self.__dict__.update(locals())

    def __getattr__(self, name):
        if name == 'is_empty':
            return False
        if name == 'morphemes':
            # TODO: This is only around because Grammar.__init__() needs it for making ExprRule and Rule both able to do this
            m = {self.list_parser.morpheme}
            if self.list_parser.separator is not None:
                m.add(self.list_parser.separator)
            return m
        return self.__dict__[name]

    def __len__(self):
        return 1

    def __eq__(self, other):
        return self.list_parser == other.list_parser

    def __str__(self):
        return str(self.list_parser)


class Rule:
    def __init__(self, nonterminal, production, id=None, root=None, ast=None):
        self.__dict__.update(locals())

    def __copy__(self):
        return Rule(self.nonterminal, Production(copy(self.production.morphemes)), self.id, self.root, self.ast)

    def expand(self):
        morphemes = []
        rules = []
        for m in self.production.morphemes:
            if isinstance(m, OptionalMacro):
                rules.extend(m.rules)
                morphemes.append(m.start_nt)
            elif isinstance(m, ListParser):
                morphemes.append(m.start_nt)
                rules.append(m.as_list_rule())
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


class ListRule:
    def __init__(self, nonterminal, list_parser, ast=None):
        self.__dict__.update(locals())

    def __getattr__(self, name):
        if name == 'morphemes':
            # TODO: This is only around because Grammar.__init__() needs it for making ExprRule and Rule both able to do this
            return self.production.morphemes
        if name == 'production':
            return ListProduction(self.list_parser)
        return self.__dict__[name]

    def __eq__(self, other):
        return self.nonterminal == other.nonterminal and self.list_parser == other.list_parser

    def must_consume_tokens(self):
        return self.list_parser.must_consume_tokens()

    def __str__(self):
        return "{} = {}".format(self.nonterminal, self.list_parser)


class ExprRule:
    def __init__(self, nonterminal, nud_production, led_production, nudAst, ast, operator, id=0):
        self.__dict__.update(locals())
        self.production = Production(nud_production.morphemes + led_production.morphemes)
        if (not nud_production or not len(nud_production)) and \
                (not led_production or not len(led_production)):
            raise Exception('Rule must contain a NUD or a LED portion.')
        # TODO: this should be a conflict
        root = self.led_production.morphemes[0] if self.led_production and len(self.led_production) else None
        if root and not isinstance(root, Terminal):
            raise Exception('Root of expression rule must be a terminal.')

    def __copy__(self):
        np = Production(copy(self.nud_production.morphemes))
        lp = Production(copy(self.led_production.morphemes))
        return ExprRule(self.nonterminal, np, lp, self.nudAst, self.ast, self.operator)

    def __getattr__(self, name):
        if name == 'morphemes':
            all = []
            for morpheme in self.nud_production.morphemes:
                all.append(morpheme)
            for morpheme in self.led_production.morphemes:
                all.append(morpheme)
            return all
        return self.__dict__[name]

    def expand(self):
        nudMorphemes = []
        ledMorphemes = []
        rules = []

        for morpheme in self.nud_production.morphemes:
            if isinstance(morpheme, OptionalMacro):
                rules.extend(morpheme.rules)
                nudMorphemes.append(morpheme.start_nt)
            elif isinstance(morpheme, ListParser):
                rules.append(morpheme.as_list_rule())
                nudMorphemes.append(morpheme.start_nt)
            else:
                nudMorphemes.append(morpheme)

        for morpheme in self.led_production.morphemes:
            if isinstance(morpheme, OptionalMacro):
                rules.extend(morpheme.rules)
                ledMorphemes.append(morpheme.start_nt)
            elif isinstance(morpheme, ListParser):
                rules.append(morpheme.as_list_rule())
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
            led = ' <=> {}'.format(str(self.led_production)) if len(self.led_production.morphemes) else ''
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
        self.list_nonterminals = set()
        self.expanded_rules = list()

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

                    if isinstance(expanded_rule, ListRule):
                        self.list_nonterminals.add(expanded_rule.nonterminal)

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
            other_nonterminals = self.expression_nonterminals | self.list_nonterminals # | is a union
            return [x for x in self.nonterminals if x not in other_nonterminals]
        elif name == 'standard_terminals':
            return [terminal for terminal in self.terminals if terminal not in [self._empty, self._end]]
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
                    for rule in self.get_expanded_ll1_rules(nonterminal):
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
                morpheme_first_set = {morpheme} if isinstance(morpheme, Terminal) else self.first_sets[morpheme]
                toks = morpheme_first_set.difference({self._empty})
                if len(toks) > 0:
                    first_set = first_set.union(toks)
                if self._empty not in morpheme_first_set:
                    add_empty_token = False
                    break
            if add_empty_token:
                first_set.add(self._empty)
            return first_set
        elif isinstance(element, ListProduction):
            morpheme = element.list_parser.morpheme
            first_set = {morpheme} if isinstance(morpheme, Terminal) else set(self.first_sets[morpheme])
            if not element.list_parser.must_consume_tokens():
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
                if isinstance(rule, ListRule):
                    morpheme = rule.list_parser.morpheme

                    # TODO: duplicated
                    morpheme_first = {self._empty} if not rule.must_consume_tokens() else set()
                    if isinstance(morpheme, NonTerminal):
                        morpheme_first = morpheme_first.union(first[morpheme])
                    elif isinstance(morpheme, Terminal):
                        morpheme_first.add(morpheme)
                    else:
                        raise Exception('Error: expected either terminal or nonterminal, got ' + morpheme)

                    if not first[rule.nonterminal].issuperset(morpheme_first.difference({self._empty})):
                        progress = changed = True
                        first[rule.nonterminal] = first[rule.nonterminal].union(morpheme_first)
                else:
                    try:
                        morpheme = rule.production.morphemes[0]
                    except IndexError:
                        continue

                    # TODO: filter out extraneous _empty's in grammar files (e.g. $x = :_empty + $a + :_empty)
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
                if isinstance(rule, ListRule):
                    list_morpheme = rule.list_parser.morpheme
                    list_separator = rule.list_parser.separator

                    if list_separator is not None:
                        morpheme_follow = {list_separator}
                    else:
                        morpheme_follow = set(first[list_morpheme]) if isinstance(list_morpheme, NonTerminal) else {list_morpheme}

                    if not rule.list_parser.sep_terminates:
                        morpheme_follow.update(follow[rule.nonterminal])

                    if isinstance(rule.list_parser.morpheme, NonTerminal) and not follow[rule.list_parser.morpheme].issuperset(morpheme_follow):
                        progress = changed = True
                        follow[rule.list_parser.morpheme].update(morpheme_follow)

                else:
                    for index, morpheme, next_morpheme in pairwise(rule.production.morphemes):
                        if isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString):
                            continue

                        if next_morpheme:
                            if isinstance(next_morpheme, Terminal):
                                next_first_set = {next_morpheme}
                            else:
                                next_first_set = first[next_morpheme].difference({self._empty})
                            if not follow[morpheme].issuperset(next_first_set):
                                progress = changed = True
                                follow[morpheme].update(next_first_set)

                        if not next_morpheme or self._empty in self.first(rule.production.slice(index + 1, None)):
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
                if len(rule.led_production):
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
                    for morpheme in rule.led_production.morphemes:
                        if str(morpheme) in morphemes:
                            morpheme.id = morphemes[str(morpheme)]

    def get_expanded_rules(self, nonterminal=None):
        if nonterminal:
            return [rule for rule in self.expanded_rules if str(rule.nonterminal) == str(nonterminal)]
        return self.expanded_rules

    def get_expanded_ll1_rules(self, nonterminal=None):
        return [rule for rule in self.get_expanded_rules(nonterminal) if isinstance(rule, Rule)]

    def get_expanded_list_rules(self, nonterminal=None):
        return [rule for rule in self.get_expanded_rules(nonterminal) if isinstance(rule, ListRule)]

    def get_rules(self, nonterminal=None):
        if nonterminal:
            return [rule for rule in self.rules if str(rule.nonterminal) == str(nonterminal)]
        return self.expanded_rule

    def list_parser(self, nonterminal):
        for rule in self.get_expanded_list_rules(nonterminal):
            if rule.nonterminal == nonterminal:
                return rule.list_parser

    def ruleFirst(self, rule):
        if isinstance(rule, ExprRule):
            if len(rule.nud_production) and rule.nud_production.morphemes[0] != rule.nonterminal:
                return self._pfirst(rule.nud_production)
        return self._pfirst(rule.production)


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


class ListParser(Morpheme):
    def __init__(self, start_nt, morpheme, separator, minimum, sep_terminates, string):
        self.__dict__.update(locals())

    def __repr__(self):
        return self.string

    def must_consume_tokens(self):
        return self.minimum > 0

    def as_list_rule(self):
        return ListRule(self.start_nt, self)

    def __eq__(self, other):
        for key in 'morpheme,separator,minimum,start_nt,sep_terminates'.split(','):
            if self.__dict__[key] != other.__dict__[key]:
                return False
        return True

    def __str__(self): return self.__repr__()

    def __hash__(self): return hash(str(self))


class OptionalMacro(Morpheme):
    def __init__(self, nonterminal, start_nt, rules):
        self.id = -1
        self.__dict__.update(locals())
        if start_nt:
            self.start_nt.setMacro(self)

    def __repr__(self):
        return 'optional({0})'.format(str(self.nonterminal))

    def __str__(self): return self.__repr__()
