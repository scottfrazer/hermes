from xtermcolor import colorize


class Theme:
    def rule(self, string):
        return string

    def production(theme, string):
        return string

    def nonterminal(theme, string):
        return string

    def terminal(self, string):
        return string

    def end_of_stream(self, string):
        return string

    def empty_string(self, string):
        return string

    def expression(self, string):
        return string

    def expression_rule(self, string):
        return string

    def infix_operator(self, string):
        return string

    def prefix_operator(self, string):
        return string

    def mixfix_operator(self, string):
        return string

    def title(self, string):
        return string

    def warning(self, string):
        return string

    def conflict(self, string):
        return string

    def conflicts_found(self, string):
        return string

    def no_conflicts(self, string):
        return string

    def ast_translation(self, string):
        return string

    def ast_specification(self, string):
        return string


class TerminalDefaultTheme(Theme):
    def title(self, string):
        return string + '\n'

    def warning(self, string):
        return string + '\n'

    def conflict(self, string):
        return string + '\n'


class TerminalColorTheme(Theme):
    def __init__(self):
        self.__dict__.update(locals())

    def rule(self, string):
        return string

    def production(self, string):
        return string

    def nonterminal(self, string):
        return colorize(string, ansi=2)

    def terminal(self, string):
        return colorize(string.strip("'"), ansi=14)

    def end_of_stream(self, string):
        return string

    def empty_string(self, string):
        return string

    def expression(self, string):
        return string

    def expression_rule(self, string):
        return string

    def infix_operator(self, string):
        return string

    def prefix_operator(self, string):
        return string

    def mixfix_operator(self, string):
        return string

    def title(self, string):
        return self._boxed(string, ansi=4)

    def warning(self, string):
        return self._boxed(string, ansi=11)

    def conflict(self, string):
        return self._boxed(string, ansi=2)

    def conflicts_found(self, string):
        return colorize(string, ansi=2)

    def no_conflicts(self, string):
        return colorize(string, ansi=2)

    def ast_translation(self, string):
        return string

    def ast_specification(self, string):
        return colorize(string, ansi=13)

    def _boxed(self, string, ansi):
        line = '+%s+' % (''.join(['-' for i in range(len(string) + 2)]))
        return colorize('%s\n| %s |\n%s\n\n' % (line, string, line), ansi=ansi)
