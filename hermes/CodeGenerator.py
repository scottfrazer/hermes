import re, moody, os
from pkg_resources import resource_filename
from hermes.Logger import Factory as LoggerFactory
from collections import OrderedDict

moduleLogger = LoggerFactory().getModuleLogger(__name__)
templates_dir = resource_filename(__name__, 'templates')
loader = moody.make_loader(templates_dir)

def remove_blank_lines(string):
  linereduce = re.compile('^[ \t]*$', re.M)
  string = linereduce.sub('', string)
  string = re.sub('\n+', '\n', string)
  return string

def underscore_to_camelcase(value):
  def camelcase(): 
    while True:
      yield str.capitalize

  c = camelcase()
  return "".join(next(c)(x) if x else '_' for x in value.split("_"))

#####
# Everything a template needs:
# 
# 1) grammar: CompositeGrammar
# 2) grammar modifications:
#    a) grammar.[non]terminal.varname (TERMINAL_X) 
#    b) egrammar.infix, egrammar.prefix, egrammar.precedence.- dictionaries of {operator ID -> associativity | bp}
#    c) (non-expr NT only) nonterminal.rules - set to expanded rules that are not empty rules.  Set 'empty' attribute on nonterminal
# 3) LL1NonTerminals - nonterminals that are not expression nonterminals
# 4) nonAbstractTerminals - terminals that are not empty string or end of stream tokens
# 5) prefix - Name used to prefix stuff in the generated code
# 6) package - java_package
# 7) lexer - lexer object (probably on grammar)
#
# Proposition:
#
# 1) grammar: CompositeGrammar
# 2) egrammar.infix,prefix,precedence probably not needed
# 3) Get rid of 2c?
# 4) nonAbstractTerminals is used in a lot of places... maybe make accessor on grammar for concrete_terminals
# 5) prefix stays... needs to be language dependent
# 6) LL1Nonterminals should be made as accessor on grammar.ll1_nonterminals
# 7) package -> java_package.  Defined on all Java templates, not defined elsewhere.
# 8) lexer stays
#
# grammar
#   .standard_terminals
#   .ll1_nonterminals
#   .lexer
# prefix
# java_package
#####

class GrammarTemplate:
  def __init__(self):
    super().__init__()
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
    self.__dict__.update(locals())
  def _prepare(self, grammar):

    # Operator precedence
    for index, egrammar in enumerate(grammar.getExpressionGrammars()):
      infixPrecedence = dict()
      prefixPrecedence = dict()
      thePrecedence = dict()
      for rule in egrammar.rules:
        if rule.operator:
          thePrecedence[rule.operator.operator.id] = rule.operator.associativity
          if rule.operator.associativity in ['left', 'right']:
            infixPrecedence[rule.operator.operator] = rule.operator.binding_power
          if rule.operator.associativity == 'unary':
            prefixPrecedence[rule.operator.operator] = rule.operator.binding_power

      infix = OrderedDict()
      prefix = OrderedDict()

      for key in sorted(infixPrecedence, key=lambda x: x.id):
        infix[key.id] = infixPrecedence[key]
      for key in sorted(prefixPrecedence, key=lambda x: x.id):
        prefix[key.id] = prefixPrecedence[key]

      egrammar.infix = infix
      egrammar.prefix = prefix
      egrammar.precedence = thePrecedence

    #  LL1 Rule helpers
    exprNonTerminals = list(map(lambda x: x.nonterminal, grammar.getExpressionGrammars()))
    for nonterminal in grammar.nonterminals:
      if nonterminal in exprNonTerminals:
        continue
      nonterminal.empty = False
      nonterminal.rules = grammar.getExpandedLL1Rules(nonterminal)
      for rule in nonterminal.rules:
        rule.empty = False
        if len(rule.production.morphemes) == 1 and rule.production.morphemes[0] == grammar._empty:
          rule.empty = True
          nonterminal.empty = True
      nonterminal.rules = list(filter(lambda x: not x.empty, nonterminal.rules))

  def render(self):
    self._prepare(self.grammar)

    try:
      if not self.prefix: self.prefix = self.grammar.name + '_'
    except AttributeError:
      self.prefix = self.grammar.name + '_'

    try:
      self.package = self.java_package
    except AttributeError:
      pass

    try:
      self.lexer = self.grammar.lexer
    except AttributeError:
      pass

    kwargs = {k: v for k, v in self.__dict__.items() if k not in ['self']}
    code = loader.render(
      self.template,
      **kwargs
    )
    return remove_blank_lines(code)
  def write(self):
    out_file_path = self.get_filename()
    try:
      os.makedirs(os.path.dirname(out_file_path))
    except FileExistsError:
      pass
    with open(out_file_path, 'w') as fp:
      fp.write(self.render())

class PythonTemplate(GrammarTemplate):
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name, self.filename)

class JavaTemplate(GrammarTemplate):
  pass

class CTemplate(GrammarTemplate):
  pass

class PythonInitTemplate(PythonTemplate):
  filename = '__init__.py'
  template = 'python/Init.py.tpl'

class PythonParserTemplate(PythonTemplate):
  filename = 'Parser.py'
  template = 'python/Parser.py.tpl'

class PythonLexerTemplate(PythonTemplate):
  filename = 'Lexer.py'
  template = 'python/Lexer.py.tpl'

class PythonCommonTemplate(PythonTemplate):
  filename = 'Common.py'
  template = 'python/Common.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.filename)

def java_package_to_path(package):
  return '/'.join(package.split('.')) if package else ''

class JavaTemplate(GrammarTemplate):
  template = 'java/ParserTemplate.java.tpl'
  def get_java_package(self):
    name = self.grammar.name.lower()
    return "{0}.{1}".format(self.java_package, name) if self.java_package else ''
  def get_filename(self):
    prefix = underscore_to_camelcase(self.grammar.name)
    return os.path.join(self.directory, java_package_to_path(self.get_java_package()), prefix + 'Parser.java')
  def render(self, **kwargs):
    self.package = self.java_package
    self.prefix = underscore_to_camelcase(self.grammar.name)
    return super().render()

class JavaUtilityTemplate(GrammarTemplate):
  template = 'java/Utility.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Utility.java')

class JavaTerminalTemplate(GrammarTemplate):
  template = 'java/Terminal.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Terminal.java')

class JavaNonTerminalTemplate(GrammarTemplate):
  template = 'java/NonTerminal.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'NonTerminal.java')

class JavaAstTransformTemplate(GrammarTemplate):
  template = 'java/AstTransform.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransform.java')

class JavaAstTransformSubstitutionTemplate(GrammarTemplate):
  template = 'java/AstTransformSubstitution.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransformSubstitution.java')

class JavaAstTransformNodeCreatorTemplate(GrammarTemplate):
  template = 'java/AstTransformNodeCreator.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransformNodeCreator.java')

class JavaAstNodeTemplate(GrammarTemplate):
  template = 'java/AstNode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstNode.java')

class JavaAstListTemplate(GrammarTemplate):
  template = 'java/AstList.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstList.java')

class JavaAstTemplate(GrammarTemplate):
  template = 'java/Ast.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Ast.java')

class JavaParseTreeNodeTemplate(GrammarTemplate):
  template = 'java/ParseTreeNode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ParseTreeNode.java')

class JavaParseTreeTemplate(GrammarTemplate):
  template = 'java/ParseTree.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ParseTree.java')

class JavaParserTemplate(GrammarTemplate):
  template = 'java/Parser.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Parser.java')

class JavaExpressionParserTemplate(GrammarTemplate):
  template = 'java/ExpressionParser.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ExpressionParser.java')

class JavaTerminalIdentifierTemplate(GrammarTemplate):
  template = 'java/TerminalIdentifier.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TerminalIdentifier.java')

class JavaTerminalMapTemplate(GrammarTemplate):
  template = 'java/TerminalMap.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TerminalMap.java')

class JavaSyntaxErrorTemplate(GrammarTemplate):
  template = 'java/SyntaxError.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SyntaxError.java')

class JavaTokenStreamTemplate(GrammarTemplate):
  template = 'java/TokenStream.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TokenStream.java')

class JavaSourceCodeTemplate(GrammarTemplate):
  template = 'java/SourceCode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SourceCode.java')

class JavaSyntaxErrorFormatterTemplate(GrammarTemplate):
  template = 'java/SyntaxErrorFormatter.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SyntaxErrorFormatter.java')

class JavaMainTemplate(GrammarTemplate):
  template = 'java/ParserMain.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ParserMain.java')
  def render(self, **kwargs):
    self.package = self.java_package
    return super().render()

class CHeaderTemplate(GrammarTemplate):
  template = 'c/parser.h.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.h')
  
class CSourceTemplate(GrammarTemplate):
  template = 'c/parser.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.c')

class CCommonHeaderTemplate(GrammarTemplate):
  template = 'c/parser_common.h.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_common.h')

class CCommonSourceTemplate(GrammarTemplate):
  template = 'c/parser_common.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_common.c')

class CMainSourceTemplate(GrammarTemplate):
  template = 'c/parser_main.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_main.c')

class PythonTemplateFactory:
  def create(self, **kwargs):
    templates = [
        PythonCommonTemplate(),
        PythonParserTemplate(),
        PythonInitTemplate()
    ]
    if kwargs['grammar'].lexer:
      templates.extend([PythonLexerTemplate()])
    return templates

class JavaTemplateFactory:
  def create(self, **kwargs):
    templates = [
      JavaTerminalTemplate(),
      JavaUtilityTemplate(),
      JavaNonTerminalTemplate(),
      JavaAstTransformTemplate(),
      JavaAstTransformSubstitutionTemplate(),
      JavaAstTransformNodeCreatorTemplate(),
      JavaAstListTemplate(),
      JavaAstTemplate(),
      JavaAstNodeTemplate(),
      JavaParseTreeTemplate(),
      JavaParserTemplate(),
      JavaExpressionParserTemplate(),
      JavaTerminalMapTemplate(),
      JavaParseTreeNodeTemplate(),
      JavaSyntaxErrorTemplate(),
      JavaTokenStreamTemplate(),
      JavaSourceCodeTemplate(),
      JavaTerminalIdentifierTemplate(),
      JavaSyntaxErrorFormatterTemplate(),
    ]
    templates.extend([JavaTemplate()])
    if kwargs['add_main']:
      templates.append(JavaMainTemplate())
    return templates

class CTemplateFactory:
  def create(self, **kwargs):
    templates = [CCommonHeaderTemplate(), CCommonSourceTemplate()]
    templates.extend([CSourceTemplate(), CHeaderTemplate()])
    if kwargs['add_main']:
      templates.append(CMainSourceTemplate())
    return templates

class CodeGenerator:
  templates = {
    'python': PythonTemplateFactory,
    'c': CTemplateFactory,
    'java': JavaTemplateFactory
  }
  def get_template_factory(self, language):
    for (template_language, template_class) in self.templates.items():
      if template_language == language:
        return template_class()
    raise Exception('Invalid language: ' + language)

  def generate(self, grammar, language, directory='.', add_main=False, java_package=None):
      template_factory = self.get_template_factory(language)
      templates = template_factory.create(
          grammar=grammar, directory=directory, add_main=add_main, java_package=java_package 
      )
      for template in templates:
          template.grammar = grammar
          template.directory = directory
          template.add_main = add_main
          template.java_package = java_package
          code = template.write() 
