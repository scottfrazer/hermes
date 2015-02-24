import sys
import os
import argparse
import pkg_resources

import hermes.factory
import hermes.code
from hermes.theme import TerminalDefaultTheme, TerminalColorTheme

def cli():
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 3):
      print("Python 3.3+ required. {}.{}.{} installed".format(version.major, version.minor, version.micro))
      sys.exit(-1)

    command_help = {
        "analyze": "Analyze a grammer, find conflicts, and print out first/follow sets",
        "generate": "Generate the code for a parser",
        "parse": "Parse a Hermes grammar file",
        "bootstrap": "Generate the parser for Hermes to parse its own grammar file format"
    }

    parser = argparse.ArgumentParser(description='Hermes Parser Generator', epilog='(c) 2011-2015 Scott Frazer')
    parser.add_argument(
        '--version', action='version', version=str(pkg_resources.get_distribution('hermes-parser'))
    )
    parser.add_argument(
        '-D', '--debug', required=False, action='store_true', help='Open the floodgates'
    )
    parser.add_argument(
        '-c', '--color', required=False, action='store_true', help='Colorized output!'
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
        '--base64', action='store_true', help='Base64 encode source'
    )
    commands['parse'].add_argument(
        '--tree', action='store_true', help='Output Parse Tree instead of AST'
    )
    commands['parse'].add_argument(
        '--no-color', action='store_true', help='Don\'t colorize output'
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
        theme = TerminalColorTheme() if cli.color else TerminalDefaultTheme()
        analyze(grammar, theme=theme)

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

    elif cli.action == 'parse':
        with open(cli.grammar) as fp:
            tree = hermes.factory.get_parse_tree(fp.read())
        colorizer = hermes.hermes_parser.no_color if cli.no_color else hermes.hermes_parser.term_color
        element = tree if cli.tree else tree.toAst()
        print(element.dumps(indent=2, color=colorizer, b64_source=cli.base64))

def analyze(grammar, format='human', theme=None, file=sys.stdout):
    if theme == None:
        theme = TerminalDefaultTheme()

    file.write(theme.title('Terminals'))
    file.write(', '.join([x.str(theme) for x in sorted(grammar.terminals, key=lambda x: x.string)]) + "\n\n")
    file.write(theme.title('Non-Terminals'))
    file.write(
        ', '.join([x.str(theme) for x in sorted(grammar.nonterminals, key=lambda x: x.string)]) + "\n\n")
    file.write(theme.title('Expanded LL(1) Rules'))
    file.write("\n".join(
        [rule.str(theme) for rule in sorted(grammar.getExpandedLL1Rules(), key=lambda x: x.str())]) + "\n\n")

    for expression_nonterminal in grammar.expression_nonterminals:
        rules = grammar.get_expanded_rules(expression_nonterminal)
        file.write(theme.title('Expanded Expression Grammar ({})'.format(expression_nonterminal)))
        file.write("\n".join([rule.str(theme) for rule in sorted(rules, key=lambda x: x.str())]) + "\n\n")

    file.write(theme.title('First sets'))
    for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.string):
        terminals = [theme.terminal(str(x)) for x in sorted(grammar.first(nonterminal), key=lambda x: x.str())]
        file.write("%s: {%s}\n" % (theme.nonterminal(str(nonterminal)), ', '.join(terminals)))
    file.write('\n')

    file.write(theme.title('Follow sets'))
    for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.string):
        terminals = [theme.terminal(str(x)) for x in
                     sorted(grammar.follow(nonterminal), key=lambda x: x.str())]
        file.write("%s: {%s}\n" % (theme.nonterminal(str(nonterminal)), ', '.join(terminals)))
    file.write('\n')

    if ( len(grammar.warnings) ):
        file.write(theme.warning('Warnings'))
        for warning in grammar.warnings:
            file.write(str(warning) + '\n\n')

    if ( len(grammar.conflicts) ):
        file.write(theme.conflict('Conflicts'))
        for conflict in grammar.conflicts:
            file.write(str(conflict) + '\n\n')
        file.write(theme.conflicts_found('%d conflicts found\n' % len(grammar.conflicts)))
    else:
        file.write(theme.no_conflicts("\nGrammar contains no conflicts!\n"))
