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
  commands['dev-ast'] = subparsers.add_parser(
    'dev-ast'
  )
  commands['dev-gen'] = subparsers.add_parser(
    'dev-gen'
  )
  commands['bootstrap'] = subparsers.add_parser(
    'bootstrap'
  )
  commands['dev-cvt'] = subparsers.add_parser(
    'dev-cvt'
  )
  commands['dev-ast'].add_argument(
    'grammar', help='New-style grammar to show AST for'
  )
  commands['dev-gen'].add_argument(
    'grammar', help='New-style grammar to show generate into gen/'
  )
  commands['dev-cvt'].add_argument(
    '--undo', action="store_true", help='Undo conversion'
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

  def get_grammar_name(cli):
    if 'name' in cli and cli.name:
      return cli.name
    else:
      base = os.path.basename(cli.grammar)
      return base[:base.rfind('.')]

  if cli.action == 'bootstrap':
    grammar = GrammarFileParser(HermesParserFactory().create()).parse_new('hermes', open('hermes.zgr'))
    templateFactory = TemplateFactoryFactory().create(outputLanguage='python')
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write([grammar], 'hermes/parser', addMain=True)
    sys.exit(-1)

  if cli.action == 'dev-ast':
    from hermes.parser.Common import AstPrettyPrintable
    from hermes.parser.hermes import lex, parse
    for t in lex(cli.grammar):
      print(t)
    #sys.exit(-1)
    parser = GrammarFileParser(HermesParserFactory().create())
    ast = parser.get_ast(get_grammar_name(cli), open(cli.grammar))
    print(AstPrettyPrintable(ast, color=True))
    sys.exit(-1)

  if cli.action == 'dev':
    old = {
      'parser': GrammarFileParser(HermesParserFactory().create()),
      'file': 'sample3_old.zgr',
      'name': 'grammar'
    }
    new = {
      'parser': GrammarFileParser(HermesParserFactory().create()),
      'file': 'sample3_new.zgr',
      'name': 'grammar'
    }
    grammar_old = old['parser'].parse(old['name'], open(old['file']))
    grammar_new = new['parser'].parse_new(new['name'], open(new['file']))
    analyzer_new = GrammarAnalyzer(grammar_new)
    analyzer_new.analyze(theme=TerminalDefaultTheme(), file=open('new', 'w'))
    analyzer_old = GrammarAnalyzer(grammar_old)
    analyzer_old.analyze(theme=TerminalDefaultTheme(), file=open('old', 'w'))

    templateFactory = TemplateFactoryFactory().create(outputLanguage='python')
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write([grammar_new], '.', addMain=True)
    sys.exit(-1)

  if cli.action == 'dev-cvt':
    import shutil, re
    if cli.undo:
      for (root, _, files) in os.walk('test'):
        for file in files:
          if file.endswith('.zgr.old'):
            src = os.path.join(root, file)
            dst = os.path.join(root, re.sub(r'\.old$', '', file))
            shutil.move(src, dst)
            print("Moved {} -> {}".format(src, dst))
    else:
      for (root, _, files) in os.walk('test'):
        for file in files:
          if file.endswith('.zgr'):
            grammar_path = os.path.join(root, file)
            if os.path.islink(grammar_path):
              continue
            grammar_path_old = grammar_path + '.old'
            shutil.copyfile(grammar_path, grammar_path_old)
            print('{} -> {}'.format(grammar_path, grammar_path_old))
            try:
              grammar_old = GrammarFileParser(HermesParserFactory().create()).parse('test', open(grammar_path))
            except ValueError:
              print("Skipping {}".format(grammar_path))
              continue
            with open(grammar_path, 'w') as fp:
              fp.write(str(grammar_old))
    #grammar_new = GrammarFileParser(HermesParserFactory().create()).parse_new(get_grammar_name(cli), open(cli.grammar))
    #print(grammar_new)
    sys.exit(-1)

  if cli.action == 'dev-gen':
    grammar = GrammarFileParser(HermesParserFactory().create()).parse_new(get_grammar_name(cli), open(cli.grammar))
    templateFactory = TemplateFactoryFactory().create(outputLanguage='c')
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write([grammar], 'gen', addMain=True)
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
    grammars.append( fp.parse_new(name, open(grammar)) )

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
