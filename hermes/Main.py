#!/usr/bin/env python

import sys, os, argparse
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from hermes.GrammarAnalyzer import GrammarAnalyzer
from hermes.GrammarCodeGenerator import GrammarCodeGenerator, PythonTemplate, Resources
from hermes.Logger import Factory as LoggerFactory
from hermes.Theme import AnsiStylizer, TerminalDefaultTheme, TerminalColorTheme

def Cli():

  ver = sys.version_info

  # Version 3.2 required for argparse
  if ver.major < 3 or (ver.major == 3 and ver.minor < 2):
    print("Python 3.2+ required. %d.%d.%d installed" %(ver.major, ver.minor, ver.micro))
    sys.exit(-1)

  parser = argparse.ArgumentParser(
              description = 'Hermes Parser Generator',
              epilog = '(c) 2011 Scott Frazer')

  parser.add_argument('action',
              choices = ['analyze', 'generate', 'parse'],
              help = 'Parser Generator Actions')

  parser.add_argument('grammar',
              metavar = 'GRAMMAR',
              nargs = 1,
              help = 'Grammar file')

  parser.add_argument('-D', '--debug',
              required = False,
              action='store_true',
              help = 'Open the floodgates')

  parser.add_argument('-s', '--start',
              required = False,
              help = 'The start symbol of the grammar.  Defaults to \'s\'')

  parser.add_argument('-d', '--directory',
              required = False,
              help = 'output file for parser generation')

  parser.add_argument('-l', '--language',
              required = False,
              default='python',
              help = 'Language to generate the parser in.  Currently not in use. Only generates Python')

  parser.add_argument('-p', '--pretty-print',
              action='store_true',
              default=False,
              help = 'Pretty prints all data structures.')

  parser.add_argument('-c', '--color',
              required = False,
              action = 'store_true',
              help = 'Prints things in color!  For the colorblind, this is a no-op.')

  parser.add_argument('-t', '--tokens',
              required = False,
              help = 'If used with the parse command, this is the token list.  If used with the generate command and -m, these tokens are put in the main() function of the generated parser.')

  parser.add_argument('-m', '--add-main',
              required = False,
              action = 'store_true',
              help = 'If this is specified, a main() function will be generated in the source code.  The tokens will be set to the -t option.')

  parser.add_argument('-a', '--ast',
              required = False,
              action = 'store_true',
              help = 'When used with the parse sub-command, the parse tree will be converted to an AST and printed out.')

  result = parser.parse_args()
  logger = LoggerFactory().initialize(result.debug)
  logger.debug('CLI Parameters: %s' % (result))

  if not os.path.isfile( result.grammar[0] ):
    sys.stderr.write("Error: File doesn't exist\n")
    sys.exit(-1)

  factory = HermesParserFactory()
  fp = GrammarFileParser(factory.create())

  #try:
  G = fp.parse( open(result.grammar[0]), result.start )
  #except Exception as e:
  #  print(e)
  #  sys.exit(-1)

  terminals = []
  if result.tokens:
    terminals = result.tokens.lower().split(',')
    error = False
    terminal_str = list(map(lambda x: x.string, G.terminals))
    for terminal in terminals:
      if terminal not in terminal_str:
        sys.stderr.write("Error: Token '%s' not recognized\n" %(terminal))
        error = True
    if error:
      sys.exit(-1)

  if result.color:
    theme = TerminalColorTheme(AnsiStylizer())
  else:
    theme = TerminalDefaultTheme()

  if result.action == 'analyze':
    analyzer = GrammarAnalyzer(G)
    analyzer.analyze( theme=theme )

  if result.action == 'generate':
    resources = Resources(G, terminals, result.add_main )
    template = PythonTemplate(resources)

    if result.directory:
      result.directory = os.path.abspath(result.directory)

    if not result.directory:
      result.directory = os.path.abspath('.')
    elif not os.path.isdir( result.directory ):
      sys.stderr.write("Error: Directory doesn't exist\n")
      sys.exit(-1)
    elif not os.access(result.directory, os.W_OK):
      sys.stderr.write("Error: Directory not writable\n")
      sys.exit(-1)

    generator = GrammarCodeGenerator(template, result.directory)
    return generator.generate()

  if result.action == 'parse':
    f = 'hermesparser.py'

    resources = Resources(G, terminals, True )
    template = PythonTemplate(resources)
    code = template.render()

    fp = open(f, 'w')
    fp.write(code)
    fp.close()

    import hermesparser
    parser = hermesparser.Parser()
    entry = list(parser.entry_points.keys())[0]
    terminals = list(map(lambda x: hermesparser.Terminal(parser.str_terminal[x]), terminals))
    parsetree = parser.parse(terminals, entry)
    if not result.ast:
      print(parsetree)
    else:
      ast = parsetree.toAst()
      ast = hermesparser.AstPrettyPrintable(ast) if result.pretty_print else ast
      if isinstance(ast, list):
        print('[%s]' % (', '.join([str(x) for x in ast])))
      else:
        print(ast)
    if os.path.isfile(f):
      os.remove(f)

if __name__ == '__main__':
    Cli()
