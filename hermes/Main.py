import sys, os, argparse, pkg_resources
from hermes.GrammarParser import GrammarParser
from hermes.GrammarAnalyzer import GrammarAnalyzer
from hermes.CodeGenerator import CodeGenerator
from hermes.Logger import Factory as LoggerFactory
from hermes.Theme import TerminalDefaultTheme, TerminalColorTheme

def Cli():

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

    parser = argparse.ArgumentParser(description='Hermes Parser Generator', epilog='(c) 2011-2014 Scott Frazer')
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

    cli = parser.parse_args()
    logger = LoggerFactory().initialize(cli.debug)
    logger.debug('CLI Parameters: %s' % (cli))

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
        return GrammarParser().parse(get_grammar_name(cli), open(cli.grammar))

    if cli.action == 'bootstrap':
        grammar = GrammarParser().parse('hermes', open('hermes.zgr'))
        CodeGenerator().generate(grammar, 'python', python_package="parser", directory='hermes')

    elif cli.action == 'analyze':
        grammar = get_grammars(cli)
        theme = TerminalColorTheme() if cli.color else TerminalDefaultTheme()
        analyzer = GrammarAnalyzer(grammar)
        analyzer.analyze( theme=theme )

    elif cli.action == 'generate':
        grammar = get_grammars(cli)
        cli.directory = os.path.abspath(os.path.expanduser(cli.directory))
        if not os.path.isdir( cli.directory ):
            sys.stderr.write("Error: --directory {0} doesn't exist\n".format(cli.directory))
            sys.exit(-1)
        elif not os.access(cli.directory, os.W_OK):
            sys.stderr.write("Error: --directory {0} not writable\n".format(cli.directory))
            sys.exit(-1)
        CodeGenerator().generate(
            grammar,
            cli.language.lower(),
            directory=cli.directory,
            add_main=cli.add_main,
            java_package=cli.java_package,
            python_package=cli.python_package,
            nodejs=cli.nodejs
        )

    elif cli.action == 'parse':
        from hermes.parser.Common import AstPrettyPrintable
        ast = GrammarParser().get_ast('test', open(cli.grammar))
        print(AstPrettyPrintable(ast))

if __name__ == '__main__':
    Cli()
