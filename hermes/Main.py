import sys, os, argparse, pkg_resources
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from hermes.GrammarAnalyzer import GrammarAnalyzer
from hermes.GrammarCodeGenerator import FactoryFactory as TemplateFactoryFactory
from hermes.GrammarCodeGenerator import TemplateWriter
from hermes.Logger import Factory as LoggerFactory
from hermes.Theme import TerminalDefaultTheme, TerminalColorTheme

def Cli():

  ver = sys.version_info

  # Version 3.2 required for argparse
  if ver.major < 3 or (ver.major == 3 and ver.minor < 2):
    print("Python 3.2+ required. {}.{}.{} installed".format(ver.major, ver.minor, ver.micro))
    sys.exit(-1)

  command_help = {
    "analyze": "Analyze a grammer, find conflicts, and print out first/follow sets",
    "generate": "Generate the code for a parser"
  }

  parser = argparse.ArgumentParser(description='Hermes Parser Generator', epilog='(c) 2011-2013 Scott Frazer')
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

  commands['dev'] = subparsers.add_parser(
    'dev'
  )
  commands['analyze'] = subparsers.add_parser(
    'analyze', description=command_help['analyze'], help=command_help['analyze']
  )
  commands['analyze'].add_argument(
    'grammar', metavar='GRAMMAR', nargs='+', help='Grammar file'
  )
  commands['analyze'].add_argument(
    '--dev', required=False, action='store_true'
  )
  commands['generate'] = subparsers.add_parser(
    'generate', description=command_help['generate'], help=command_help['generate']
  )
  commands['generate'].add_argument(
    '--name', help='The name of the module'
  )
  commands['generate'].add_argument(
    'grammar', metavar='GRAMMAR', nargs='+', help='Grammar file'
  )
  commands['generate'].add_argument(
    '-d', '--directory', required=False, default='.', help='Directory to write generated code to'
  )
  commands['generate'].add_argument(
    '-l', '--language', required=False, default='python', choices=['c', 'java', 'python'], help = 'Language for generated parser'
  )
  commands['generate'].add_argument(
    '--java-package', required=False, help='If generating Java code, this is the package.'
  )
  commands['generate'].add_argument(
    '-m', '--add-main', required=False, action='store_true', help='If this is specified, a main() function will be generated in the source code.'
  )

  cli = parser.parse_args()
  logger = LoggerFactory().initialize(cli.debug)
  logger.debug('CLI Parameters: %s' % (cli))

  factory = HermesParserFactory()
  fp = GrammarFileParser(factory.create())

  if cli.action == 'dev':
    old = {
      'parser': GrammarFileParser(HermesParserFactory().create()),
      'file': 'sample3_old.zgr',
      'name': 'grammar'
    }
    new = {
      'parser': GrammarFileParser(HermesParserFactory().create()),
      'file': 'sample3_new.zgr',
      'name': 'hermes'
    }
    grammar_old = old['parser'].parse(old['name'], open(old['file']))
    grammar_new = new['parser'].parse_new(new['name'], open(new['file']))
    analyzer = GrammarAnalyzer(grammar_new)
    analyzer.analyze( theme=TerminalColorTheme() )
    sys.exit(-1)

  grammars = []
  for grammar in cli.grammar:
    if not os.path.isfile( grammar ):
      sys.stderr.write("Error: Grammar file doesn't exist\n")
      sys.exit(-1)

    name = os.path.basename(grammar)

    if not name.endswith('.zgr'):
      sys.stderr.write("Error: Grammar file must have .zgr extension\n")
      sys.exit(-1)

    name = name[:-4]
    grammars.append( fp.parse(name, open(grammar)) )

  if cli.action == 'analyze':

    if cli.color:
      theme = TerminalColorTheme()
    else:
      theme = TerminalDefaultTheme()

    for grammar in grammars:
      analyzer = GrammarAnalyzer(grammar)
      analyzer.analyze( theme=theme )

  if cli.action == 'generate':
    cli.directory = os.path.abspath(os.path.expanduser(cli.directory))

    if not os.path.isdir( cli.directory ):
      sys.stderr.write("Error: Directory doesn't exist\n")
      sys.exit(-1)
    elif not os.access(cli.directory, os.W_OK):
      sys.stderr.write("Error: Directory not writable\n")
      sys.exit(-1)

    templateFactory = TemplateFactoryFactory().create(outputLanguage=cli.language.lower())
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write(grammars, cli.directory, addMain=cli.add_main, javaPackage=cli.java_package)

if __name__ == '__main__':
    Cli()
