import sys
import inspect
from collections import OrderedDict
from ..Common import *
def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]
def parse(tokens):
  return Parser().parse(tokens)
class Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
    0: 'nt',
    'nt': 0,
  }
  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
    1: 't',
    2: '_gen0',
    3: 's',
    4: '_gen1',
    't': 1,
    '_gen0': 2,
    's': 3,
    '_gen1': 4,
  }
  # table[nonterminal][terminal] = rule
  table = [
    [0],
    [1],
    [4],
    [2],
  ]
  TERMINAL_NT = 0
  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()
  def isTerminal(self, id):
    return 0 <= id <= 0
  def isNonTerminal(self, id):
    return 1 <= id <= 4
  def parse(self, tokens):
    self.tokens = tokens
    self.start = '$S'
    tree = self.parse_s()
    if self.tokens.current() != None:
      raise SyntaxError( 'Finished parsing without consuming all tokens.' )
    return tree
  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError( 'No more tokens.  Expecting %s' % (self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError( 'Unexpected symbol (line %d, col %d) when parsing %s.  Expected %s, got %s.' %(currentToken.line, currentToken.col, whosdaddy(), self.terminals[terminalId], currentToken) )
    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) )
    return currentToken
  def parse_t(self):
    current = self.tokens.current()
    rule = self.table[0][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(1, self.nonterminals[1]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 0:
      tree.astTransform = AstTransformSubstitution(0)
      t = self.expect(0) # nt
      tree.add(t)
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen0(self):
    current = self.tokens.current()
    rule = self.table[1][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(2, self.nonterminals[2]))
    tree.list = 'mlist'
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 1:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_t()
      tree.add( subtree )
      subtree = self.parse_t()
      tree.add( subtree )
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse_s(self):
    current = self.tokens.current()
    rule = self.table[2][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(3, self.nonterminals[3]))
    tree.list = False
    if current == None:
      raise SyntaxError('Error: unexpected end of file')
    if rule == 4:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse__gen0()
      tree.add( subtree )
      return tree
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
  def parse__gen1(self):
    current = self.tokens.current()
    rule = self.table[3][current.getId()] if current else -1
    tree = ParseTree( NonTerminal(4, self.nonterminals[4]))
    tree.list = False
    if current != None and (current.getId() in [-1]):
      return tree
    if current == None:
      return tree
    if rule == 2:
      tree.astTransform = AstTransformSubstitution(0)
      subtree = self.parse_t()
      tree.add( subtree )
      subtree = self.parse__gen1()
      tree.add( subtree )
      return tree
    return tree
if __name__ == '__main__':
    import argparse
    import json
    cli_parser = argparse.ArgumentParser(description='Grammar Parser')
    cli_parser.add_argument('--color', action='store_true', help="Print output in terminal colors")
    cli_parser.add_argument('--file')
    cli_parser.add_argument('--out', default='ast', choices=['ast', 'parsetree'])
    cli_parser.add_argument('--stdin', action='store_true')
    cli = cli_parser.parse_args()
    if (not cli.file and not cli.stdin) or (cli.file and cli.stdin):
      sys.exit('Either --file=<path> or --stdin required, but not both')
    cli.file = open(cli.file) if cli.file else sys.stdin
    json_tokens = json.loads(cli.file.read())
    cli.file.close()
    tokens = TokenStream() 
    for json_token in json_tokens:
        tokens.append(Terminal(
            Parser.terminals[json_token['terminal']],
            json_token['terminal'],
            json_token['source_string'],
            json_token['resource'],
            json_token['line'],
            json_token['col']
        ))
    try:
        tree = parse(tokens)
        if cli.out == 'parsetree':
          print(ParseTreePrettyPrintable(tree, color=cli.color))
        else:
          print(AstPrettyPrintable(tree.toAst(), color=cli.color))
    except SyntaxError as error:
        print(error)
