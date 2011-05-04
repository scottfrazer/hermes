#!/usr/bin/env python

from types import *
from os import path
import sys, os, argparse
from hermes.GrammarFileParser import GrammarFileParser
from hermes.GrammarAnalyzer import GrammarAnalyzer
from hermes.GrammarCodeGenerator import GrammarCodeGenerator, PythonTemplate, Resources

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
              help = 'Zeus grammar file')

  parser.add_argument('-s', '--start',
              required = False,
              help = 'The start symbol of the grammar.  Defaults to \'s\'')

  parser.add_argument('-d', '--directory',
              required = False,
              help = 'output file for parser generation')

  parser.add_argument('-l', '--language',
              required = False,
              default='python',
              help = 'Language to generate the parser in.  Accepts C or Python (default).')

  parser.add_argument('-t', '--tokens',
              required = False,
              help = 'If this is specified, a main() function will be generated in the source code that is set to parse these tokens.')

  result = parser.parse_args()

  if not os.path.isfile( result.grammar[0] ):
    sys.stderr.write("Error: File doesn't exist\n")
    sys.exit(-1)

  fp = GrammarFileParser()

  try:
    G = fp.parse( open(result.grammar[0]), result.start )
  except Exception as e:
    print(e)
    sys.exit(-1)

  if result.action == 'analyze':
    analyzer = GrammarAnalyzer(G)
    analyzer.analyze()

  if result.action == 'generate':
    terminals = list(map(lambda x: 'TERMINAL_'+x, result.tokens.upper().split(','))) if result.tokens else []
    resources = Resources(G, terminals )
    template = PythonTemplate(resources)

    if result.directory:
      result.directory = path.abspath(result.directory)

    if not result.directory:
      result.directory = path.abspath('.')
    elif not os.path.isdir( result.directory ):
      sys.stderr.write("Error: Directory doesn't exist\n")
      sys.exit(-1)
    elif not os.access(result.directory, os.W_OK):
      sys.stderr.write("Error: Directory not writable\n")
      sys.exit(-1)

    generator = GrammarCodeGenerator(template, result.directory)
    return generator.generate()

  if result.action == 'parse':
    f = '__z_code_compile__.py'
    terminals = list(map(lambda x: 'TERMINAL_'+x, result.tokens.upper().split(','))) if result.tokens else []
    if len(terminals) == 0:
      sys.stderr.write("Warning: No tokens specified! (use --tokens)")

    resources = Resources(G, terminals )
    template = PythonTemplate(resources)
    code = template.render()

    fp = open(f, 'w')
    fp.write(code)
    fp.close()

    import subprocess
    output = subprocess.check_output(['python', f])
    output_str = output.decode('utf-8')
    if os.path.isfile(f):
      os.remove(f)
    sys.stdout.write(output_str)

if __name__ == '__main__':
    Cli()