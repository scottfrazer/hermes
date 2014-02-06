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
    raise Exception('not implemented')

class MainTemplate(Template):
  def __init__(self, grammars):
    super().__init__()
    self.__dict__.update(locals())
  def get_filename(self):
    return os.path.basename(self.template[:-4])
  def render(self, javaPackage=None):
    code = loader.render(
      self.template,
      grammars=self.grammars,
      package=javaPackage
    )
    
    return remove_blank_lines(code)

class CommonTemplate(Template):
  def __init__(self):
    super().__init__()
  def get_filename(self):
    return os.path.basename(self.template[:-4])
  def render(self, javaPackage=None):
    code = loader.render(
      self.template,
      package=javaPackage
    )

    return remove_blank_lines(code)
    

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

  def get_filename(self):
    return self.grammar.name + '_' + os.path.basename(self.template[:-4])
  def getPrefix(self):
    return self.grammar.name + '_'
  def render(self, javaPackage=None):
    self._prepare(self.grammar)
    LL1Nonterminals = [x for x in self.grammar.nonterminals if x not in map(lambda x: x.nonterminal, self.grammar.exprgrammars)]

    code = loader.render(
      self.template,
      grammar=self.grammar,
      LL1Nonterminals=LL1Nonterminals,
      nonAbstractTerminals=self.grammar.getSimpleTerminals(),
      prefix=self.getPrefix(),
      package=javaPackage
    )

    return remove_blank_lines(code)

class LexerTemplate(Template):
  def __init__(self, grammar):
    super().__init__()
    self.__dict__.update(locals())
  def render(self, javaPackage=None):
    code = loader.render(
      self.template,
      lexer=self.grammar.lexer
    )
    return remove_blank_lines(code)

class PythonInitTemplate(CommonTemplate):
  template = 'python/Init.py.tpl'
  def __init__(self, grammar):
    self.__dict__.update(locals())
  def get_filename(self):
    return self.grammar.name + '/__init__.py'
  def render(self, **kwargs):
    return loader.render(self.template)

class PythonParserTemplate(GrammarTemplate):
  template = 'python/Parser.py.tpl'
  def get_filename(self):
    return self.grammar.name + '/Parser.py'

class PythonLexerTemplate(LexerTemplate):
  template = 'python/Lexer.py.tpl'
  def get_filename(self):
    return self.grammar.name + '/Lexer.py'

class PythonCommonTemplate(CommonTemplate):
  template = 'python/Common.py.tpl'
  def get_filename(self):
    return 'Common.py'

class JavaTemplate(GrammarTemplate):
  template = 'java/ParserTemplate.java.tpl'
  def get_filename(self):
    return self.getPrefix() + "Parser.java"
  def getPrefix(self):
    return underscore_to_camelcase(self.grammar.name.lower())

class JavaUtilityTemplate(CommonTemplate):
  template = 'java/Utility.java.tpl'

class JavaTerminalTemplate(CommonTemplate):
  template = 'java/Terminal.java.tpl'

class JavaNonTerminalTemplate(CommonTemplate):
  template = 'java/NonTerminal.java.tpl'

class JavaAstTransformTemplate(CommonTemplate):
  template = 'java/AstTransform.java.tpl'

class JavaAstTransformSubstitutionTemplate(CommonTemplate):
  template = 'java/AstTransformSubstitution.java.tpl'

class JavaAstTransformNodeCreatorTemplate(CommonTemplate):
  template = 'java/AstTransformNodeCreator.java.tpl'

class JavaAstNodeTemplate(CommonTemplate):
  template = 'java/AstNode.java.tpl'

class JavaAstListTemplate(CommonTemplate):
  template = 'java/AstList.java.tpl'

class JavaAstTemplate(CommonTemplate):
  template = 'java/Ast.java.tpl'

class JavaParseTreeNodeTemplate(CommonTemplate):
  template = 'java/ParseTreeNode.java.tpl'

class JavaParseTreeTemplate(CommonTemplate):
  template = 'java/ParseTree.java.tpl'

class JavaParserTemplate(CommonTemplate):
  template = 'java/Parser.java.tpl'

class JavaExpressionParserTemplate(CommonTemplate):
  template = 'java/ExpressionParser.java.tpl'

class JavaTerminalIdentifierTemplate(CommonTemplate):
  template = 'java/TerminalIdentifier.java.tpl'

class JavaTerminalMapTemplate(CommonTemplate):
  template = 'java/TerminalMap.java.tpl'

class JavaSyntaxErrorTemplate(CommonTemplate):
  template = 'java/SyntaxError.java.tpl'

class JavaTokenStreamTemplate(CommonTemplate):
  template = 'java/TokenStream.java.tpl'

class JavaSourceCodeTemplate(CommonTemplate):
  template = 'java/SourceCode.java.tpl'

class JavaSyntaxErrorFormatterTemplate(CommonTemplate):
  template = 'java/SyntaxErrorFormatter.java.tpl'

class JavaMainTemplate(MainTemplate):
  template = 'java/ParserMain.java.tpl'

class CHeaderTemplate(GrammarTemplate):
  template = 'c/parser.h.tpl'
  
class CSourceTemplate(GrammarTemplate):
  template = 'c/parser.c.tpl'

class CCommonHeaderTemplate(CommonTemplate):
  template = 'c/parser_common.h.tpl'

class CCommonSourceTemplate(CommonTemplate):
  template = 'c/parser_common.c.tpl'

class CMainSourceTemplate(MainTemplate):
  template = 'c/parser_main.c.tpl'

class FactoryFactory:
  def create(self, outputLanguage):
    templates = {
      'python': PythonTemplateFactory,
      'c': CTemplateFactory,
      'java': JavaTemplateFactory
    }

    for (language, templateClass) in templates.items():
      if language == outputLanguage:
        return templateClass()
    raise Exception('invalid language')

class PythonTemplateFactory:
  def create(self, grammars, addMain):
    templates = [PythonCommonTemplate()]
    for grammar in grammars:
      templates.extend([PythonParserTemplate(grammar)])
      if grammar.lexer:
        templates.extend([PythonLexerTemplate(grammar)])
      templates.extend([PythonInitTemplate(grammar)])
    return templates

class JavaTemplateFactory:
  def create(self, grammars, addMain=False):
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
    for grammar in grammars:
      templates.extend([JavaTemplate(grammar)])
    if addMain:
      templates.append(JavaMainTemplate(grammars))
    return templates

class CTemplateFactory:
  def create(self, grammars, addMain=False):
    templates = [CCommonHeaderTemplate(), CCommonSourceTemplate()]
    for grammar in grammars:
      templates.extend([CSourceTemplate(grammar), CHeaderTemplate(grammar)])
    if addMain:
      templates.append(CMainSourceTemplate(grammars))
    return templates

class TemplateWriter:
  def __init__(self, templateFactory):
    self.__dict__.update(locals())
  def write(self, grammars, directory, addMain=False, javaPackage=None):
    templates = self.templateFactory.create(grammars, addMain)
    for template in templates:
      code = template.render(javaPackage=javaPackage) 
      subdir = os.path.join(directory, os.path.dirname(template.get_filename()))
      if not os.path.isdir(subdir):
        os.makedirs(subdir)
      with open(os.path.join(directory, template.get_filename()), 'w') as fp:
        fp.write(code)
