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

class Template:
  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  def render(self):
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

class MainTemplate(Template):
  def __init__(self, grammar):
    super().__init__()
    self.__dict__.update(locals())

class CommonTemplate(Template):
    def __init__(self):
        super().__init__()
    def render(self):
        try:
            self.package = self.java_package
        except AttributeError:
            pass
        return super().render() 

class GrammarTemplate(Template):
  def __init__(self, grammar):
    super().__init__()
    self.__dict__.update(locals())
  def _prepare(self, grammar):

    # Set the variable name for each terminal and nonterminal
    terminals = grammar.getSimpleTerminals()

    for terminal in terminals:
      terminal.varname = 'TERMINAL_' + str(terminal).strip("'").upper()

    for nonterminal in grammar.nonterminals:
      nonterminal.varname = 'NONTERMINAL_' + str(nonterminal).upper()

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
    self.LL1Nonterminals = [x for x in self.grammar.nonterminals if x not in map(lambda x: x.nonterminal, self.grammar.exprgrammars)]
    self.nonAbstractTerminals = self.grammar.getSimpleTerminals()
    try:
      if not self.prefix: self.prefix = self.grammar.name + '_'
    except AttributeError:
      self.prefix = self.grammar.name + '_'

    try:
      self.package = self.java_package
    except AttributeError:
      pass

    return super().render()

class LexerTemplate(Template):
  def __init__(self, grammar):
    super().__init__()
    self.__dict__.update(locals())
  def render(self):
    self.lexer = self.grammar.lexer
    return super().render()

class PythonInitTemplate(CommonTemplate):
  template = 'python/Init.py.tpl'
  def __init__(self, grammar):
    self.__dict__.update(locals())
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name, '__init__.py')
  def render(self, **kwargs):
    return super().render()

class PythonParserTemplate(GrammarTemplate):
  template = 'python/Parser.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name, 'Parser.py')

class PythonLexerTemplate(LexerTemplate):
  template = 'python/Lexer.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name, 'Lexer.py')

class PythonCommonTemplate(CommonTemplate):
  template = 'python/Common.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'Common.py')

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

class JavaUtilityTemplate(CommonTemplate):
  template = 'java/Utility.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Utility.java')

class JavaTerminalTemplate(CommonTemplate):
  template = 'java/Terminal.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Terminal.java')

class JavaNonTerminalTemplate(CommonTemplate):
  template = 'java/NonTerminal.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'NonTerminal.java')

class JavaAstTransformTemplate(CommonTemplate):
  template = 'java/AstTransform.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransform.java')

class JavaAstTransformSubstitutionTemplate(CommonTemplate):
  template = 'java/AstTransformSubstitution.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransformSubstitution.java')

class JavaAstTransformNodeCreatorTemplate(CommonTemplate):
  template = 'java/AstTransformNodeCreator.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstTransformNodeCreator.java')

class JavaAstNodeTemplate(CommonTemplate):
  template = 'java/AstNode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstNode.java')

class JavaAstListTemplate(CommonTemplate):
  template = 'java/AstList.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'AstList.java')

class JavaAstTemplate(CommonTemplate):
  template = 'java/Ast.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Ast.java')

class JavaParseTreeNodeTemplate(CommonTemplate):
  template = 'java/ParseTreeNode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ParseTreeNode.java')

class JavaParseTreeTemplate(CommonTemplate):
  template = 'java/ParseTree.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ParseTree.java')

class JavaParserTemplate(CommonTemplate):
  template = 'java/Parser.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'Parser.java')

class JavaExpressionParserTemplate(CommonTemplate):
  template = 'java/ExpressionParser.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'ExpressionParser.java')

class JavaTerminalIdentifierTemplate(CommonTemplate):
  template = 'java/TerminalIdentifier.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TerminalIdentifier.java')

class JavaTerminalMapTemplate(CommonTemplate):
  template = 'java/TerminalMap.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TerminalMap.java')

class JavaSyntaxErrorTemplate(CommonTemplate):
  template = 'java/SyntaxError.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SyntaxError.java')

class JavaTokenStreamTemplate(CommonTemplate):
  template = 'java/TokenStream.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'TokenStream.java')

class JavaSourceCodeTemplate(CommonTemplate):
  template = 'java/SourceCode.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SourceCode.java')

class JavaSyntaxErrorFormatterTemplate(CommonTemplate):
  template = 'java/SyntaxErrorFormatter.java.tpl'
  def get_filename(self):
    return os.path.join(self.directory, java_package_to_path(self.java_package), 'SyntaxErrorFormatter.java')

class JavaMainTemplate(MainTemplate):
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

class CCommonHeaderTemplate(CommonTemplate):
  template = 'c/parser_common.h.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_common.h')

class CCommonSourceTemplate(CommonTemplate):
  template = 'c/parser_common.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_common.c')

class CMainSourceTemplate(MainTemplate):
  template = 'c/parser_main.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'parser_main.c')

class PythonTemplateFactory:
  def create(self, grammar, directory='.', **kwargs):
    templates = [
        PythonCommonTemplate(),
        PythonParserTemplate(grammar),
        PythonInitTemplate(grammar)
    ]
    if grammar.lexer:
      templates.extend([PythonLexerTemplate(grammar)])
    for template in templates:
      template.directory = directory
      template.grammar = grammar
    return templates

class JavaTemplateFactory:
  def create(self, grammar, directory='.', add_main=False, java_package=None, **kwargs):
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
    templates.extend([JavaTemplate(grammar)])
    if add_main:
      templates.append(JavaMainTemplate(grammar))
    for template in templates:
      template.grammar = grammar
      template.java_package = java_package
      template.directory = directory
    return templates

class CTemplateFactory:
  def create(self, grammar, directory='.', add_main=False, **kwargs):
    templates = [CCommonHeaderTemplate(), CCommonSourceTemplate()]
    templates.extend([CSourceTemplate(grammar), CHeaderTemplate(grammar)])
    if add_main:
      templates.append(CMainSourceTemplate(grammar))
    for template in templates:
      template.directory = directory
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
          grammar, add_main=add_main, directory=directory, java_package=java_package
      )
      for template in templates:
          code = template.write() 
