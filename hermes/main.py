import sys
import os
import argparse
import pkg_resources
from xtermcolor import colorize

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter

import hermes
import hermes.factory
import hermes.code

def cli():
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 3):
      print("Python 3.3+ required. {}.{}.{} installed".format(version.major, version.minor, version.micro))
      sys.exit(-1)

    command_help = {
        "analyze": "Analyze a grammer, find conflicts, and print out first/follow sets",
        "generate": "Generate the code for a parser",
        "bootstrap": "Generate the parser for Hermes to parse its own grammar file format",
        "parse": "Parse source code through a grammar",
        "lex": "Tokenize source code through a grammar"
    }

    parser = argparse.ArgumentParser(description='Hermes Parser Generator', epilog='(c) 2011-2015 Scott Frazer')
    parser.add_argument(
        '--version', action='version', version=str(pkg_resources.get_distribution('hermes-parser'))
    )
    parser.add_argument(
        '--debug', required=False, action='store_true', help='Open the floodgates'
    )
    parser.add_argument(
        '--no-color', default=False, required=False, action='store_true', help='Don\'t colorize output'
    )

    subparsers = parser.add_subparsers(help='Parser Generator Actions', dest='action')
    commands = {}
    commands['bootstrap'] = subparsers.add_parser(
        'bootstrap', description=command_help['bootstrap'], help=command_help['bootstrap']
    )
    commands['analyze'] = subparsers.add_parser(
        'analyze', description=command_help['analyze'], help=command_help['analyze']
    )
    commands['analyze'].add_argument(
        'grammar', metavar='GRAMMAR', help='Grammar file'
    )
    commands['generate'] = subparsers.add_parser(
        'generate', description=command_help['generate'], help=command_help['generate']
    )
    commands['generate'].add_argument(
        '--name', help='The name of the grammar'
    )
    commands['generate'].add_argument(
        'grammar', metavar='GRAMMAR', help='Grammar file'
    )
    commands['generate'].add_argument(
        '-d', '--directory', required=False, default='.', help='Directory to write generated code to'
    )
    commands['generate'].add_argument(
        '-l', '--language', required=False, default='python', choices=['c', 'java', 'python', 'javascript'], help = 'Language for generated parser'
    )
    commands['generate'].add_argument(
        '--java-package', required=False, help='If generating Java code, this is the package.'
    )
    commands['generate'].add_argument(
        '--python-package', required=False, help='If generating Python code, this is the package.'
    )
    commands['generate'].add_argument(
        '--nodejs', action="store_true", required=False, help='If generating JavaScript, make it usable with Node.js'
    )
    commands['generate'].add_argument(
        '-m', '--add-main', required=False, action='store_true', help='If this is specified, a main() function will be generated in the source code.'
    )
    commands['parse'] = subparsers.add_parser(
        'parse', description=command_help['parse'], help=command_help['parse']
    )
    commands['parse'].add_argument(
        'grammar', metavar='GRAMMAR', help='Grammar file'
    )
    commands['parse'].add_argument(
        'input', metavar='INPUT', help='Source input'
    )
    commands['parse'].add_argument(
        '--base64', action='store_true', help='Base64 encode source'
    )
    commands['parse'].add_argument(
        '--tree', default=False, action='store_true', help='Print parse tree instead of AST'
    )
    commands['lex'] = subparsers.add_parser(
        'lex', description=command_help['lex'], help=command_help['lex']
    )
    commands['lex'].add_argument(
        'grammar', metavar='GRAMMAR', help='Grammar file'
    )
    commands['lex'].add_argument(
        'input', metavar='INPUT', help='Source input'
    )
    commands['lex'].add_argument(
        '--base64', action='store_true', help='Base64 encode source'
    )

    cli = parser.parse_args()

    def get_grammar_name(cli):
        if 'name' in cli and cli.name:
            return cli.name
        else:
            base = os.path.basename(cli.grammar)
            return base[:base.find('.')]

    def get_grammars(cli):
        grammar_path = os.path.expanduser(cli.grammar)
        if not os.path.isfile(grammar_path):
            sys.stderr.write("Error: Grammar file {0} doesn't exist\n".format(grammar_path))
            sys.exit(-1)
        with open(cli.grammar) as fp:
            return hermes.factory.parse(fp.read(), get_grammar_name(cli))

    if cli.action == 'bootstrap':
        with open('hermes.zgr') as fp:
            grammar = hermes.factory.parse(fp.read(), 'hermes')
        hermes.code.generate(grammar, 'python', directory='hermes')

    elif cli.action == 'analyze':
        grammar = get_grammars(cli)
        analyze(grammar, color=not cli.no_color)

    elif cli.action == 'generate':
        grammar = get_grammars(cli)
        cli.directory = os.path.abspath(os.path.expanduser(cli.directory))
        if not os.path.isdir(cli.directory):
            sys.stderr.write("Error: --directory {0} doesn't exist\n".format(cli.directory))
            sys.exit(-1)
        elif not os.access(cli.directory, os.W_OK):
            sys.stderr.write("Error: --directory {0} not writable\n".format(cli.directory))
            sys.exit(-1)

        hermes.code.generate(
            grammar,
            cli.language.lower(),
            directory=cli.directory,
            add_main=cli.add_main,
            java_package=cli.java_package,
            nodejs=cli.nodejs
        )

    elif cli.action == 'lex':
        if cli.grammar == '-':
            user_parser = hermes.hermes_parser
        else:
            with open(cli.grammar) as fp:
                user_parser = hermes.compile(fp)

        with open(cli.input) as fp:
            for token in user_parser.lex(fp.read(), '<string>', debug=cli.debug):
                print(token.dumps(b64_source=cli.base64))

    elif cli.action == 'parse':
        lexer = get_lexer_by_name("htree") if cli.tree else get_lexer_by_name("hast")
        formatter = TerminalFormatter()

        if cli.grammar == '-':
            parser = hermes.hermes_parser
        else:
            with open(cli.grammar) as fp:
                parser = hermes.compile(fp)

        with open(cli.input) as fp:
            tree = parser.parse(fp.read())

        string = tree.dumps(indent=2) if cli.tree else tree.toAst().dumps(indent=2)
        print(string if cli.no_color else highlight(string, lexer, formatter).strip())

def analyze(grammar, format='human', color=False, file=sys.stdout):
    lexer = get_lexer_by_name("hgr")
    formatter = TerminalFormatter()

    def boxed(s):
        line = '+{0}+'.format('-' * (len(s) + 2))
        return '{0}\n| {1} |\n{0}\n\n'.format(line, s)
    def title(s): return colorize(boxed(s), ansi=4) if color else boxed(s)
    def warning(s): return colorize(boxed(s), ansi=11) if color else boxed(s)
    def conflicts(s): return colorize(boxed(s), ansi=2) if color else boxed(s)
    def conflicts_found(s): return colorize(s, ansi=1) if color else s
    def no_conflicts(s): return colorize(s, ansi=2) if color else s
    def pygments_highlight(s): return highlight(s, lexer, formatter).strip() if color else s

    file.write(title('Terminals'))
    file.write(', '.join([pygments_highlight(str(x)) for x in sorted(grammar.terminals, key=lambda x: x.string)]) + "\n\n")
    file.write(title('Non-Terminals'))
    file.write(
        ', '.join([pygments_highlight(str(x)) for x in sorted(grammar.nonterminals, key=lambda x: x.string)])
    )
    file.write("\n\n")

    file.write(title('Expanded LL(1) Rules'))
    file.write("\n".join(
        [pygments_highlight(str(rule)) for rule in sorted(grammar.getExpandedLL1Rules(), key=lambda x: str(x))]
    ))
    file.write("\n\n")

    for expression_nonterminal in grammar.expression_nonterminals:
        rules = grammar.get_expanded_rules(expression_nonterminal)
        file.write(title('Expanded Expression Grammar ({})'.format(expression_nonterminal)))
        file.write("\n".join([pygments_highlight(str(rule)) for rule in sorted(rules, key=lambda x: str(x))]) + "\n\n")

    file.write(title('First sets'))
    for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.string):
        terminals = [pygments_highlight(str(x)) for x in sorted(grammar.first(nonterminal), key=lambda x: x.string)]
        file.write("%s: {%s}\n" % (pygments_highlight(str(nonterminal)), ', '.join(terminals)))
    file.write('\n')

    file.write(title('Follow sets'))
    for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.string):
        terminals = [pygments_highlight(str(x)) for x in
                     sorted(grammar.follow(nonterminal), key=lambda x: x.string)]
        file.write("%s: {%s}\n" % (pygments_highlight(str(nonterminal)), ', '.join(terminals)))
    file.write('\n')

    if len(grammar.warnings):
        file.write(warning('Warnings'))
        for warning in grammar.warnings:
            file.write(str(warning) + '\n\n')

    if len(grammar.conflicts):
        file.write(conflicts('Conflicts'))
        for conflict in grammar.conflicts:
            file.write(str(conflict) + '\n\n')
        file.write(conflicts_found('%d conflicts found\n' % len(grammar.conflicts)))
    else:
        file.write(no_conflicts("\nGrammar contains no conflicts!\n"))
