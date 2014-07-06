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
# All templates will have the following things specified:
#
# grammar
#   .standard_terminals
#   .ll1_nonterminals
#   .lexer
# prefix
# java_package
# python_package
# nodejs
# directory
# add_main
#####

class GrammarTemplate:
  def __init__(self):
    super().__init__()
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
    self.__dict__.update(locals())
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

class PythonTemplate(GrammarTemplate):
  def get_filename(self):
    return os.path.join(self.directory, self.python_package, self.grammar.name, self.filename)

class JavaTemplate(GrammarTemplate):
  def get_filename(self):
    prefix = underscore_to_camelcase(self.grammar.name)
    return os.path.join(self.directory, self.java_package_to_path(), self.filename)
  def java_package_to_path(self):
    return '/'.join(self.java_package.split('.')) if self.java_package else ''
  def render(self, **kwargs):
    self.prefix = underscore_to_camelcase(self.grammar.name)
    return super().render()

class CTemplate(GrammarTemplate):
  def get_filename(self):
    return os.path.join(self.directory, self.filename)
  def render(self, **kwargs):
    self.prefix = self.grammar.name + '_'
    return super().render()

class JavascriptTemplate(GrammarTemplate):
  def get_filename(self):
    return os.path.join(self.directory, self.filename)
  def render(self, **kwargs):
    self.prefix = self.grammar.name + '_'
    return super().render()

class PythonInitTemplate(PythonTemplate):
  filename = '__init__.py'
  template = 'python/Init.py.tpl'
  def render(self, **kwargs):
    self.prefix = self.grammar.name + '_'
    return super().render()

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
    return os.path.join(self.directory, self.python_package, self.filename)

class PythonMainTemplate(PythonTemplate):
  filename = 'main.py'
  template = 'python/Main.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name + '_' + self.filename)

class JavaParserTemplate(JavaTemplate):
  filename = 'Parser.java'
  template = 'java/ParserTemplate.java.tpl'
  def get_filename(self):
    prefix = underscore_to_camelcase(self.grammar.name)
    return os.path.join(self.directory, self.java_package_to_path(), prefix + self.filename)

class JavaUtilityTemplate(JavaTemplate):
  filename = 'Utility.java'
  template = 'java/Utility.java.tpl'

class JavaTerminalTemplate(JavaTemplate):
  filename = 'Terminal.java'
  template = 'java/Terminal.java.tpl'

class JavaNonTerminalTemplate(JavaTemplate):
  filename = 'NonTerminal.java'
  template = 'java/NonTerminal.java.tpl'

class JavaAstTransformTemplate(JavaTemplate):
  filename = 'AstTransform.java'
  template = 'java/AstTransform.java.tpl'

class JavaAstTransformSubstitutionTemplate(JavaTemplate):
  filename = 'AstTransformSubstitution.java'
  template = 'java/AstTransformSubstitution.java.tpl'

class JavaAstTransformNodeCreatorTemplate(JavaTemplate):
  filename = 'AstTransformNodeCreator.java'
  template = 'java/AstTransformNodeCreator.java.tpl'

class JavaAstNodeTemplate(JavaTemplate):
  filename = 'AstNode.java'
  template = 'java/AstNode.java.tpl'

class JavaAstListTemplate(JavaTemplate):
  filename = 'AstList.java'
  template = 'java/AstList.java.tpl'

class JavaAstTemplate(JavaTemplate):
  filename = 'Ast.java'
  template = 'java/Ast.java.tpl'

class JavaParseTreeNodeTemplate(JavaTemplate):
  filename = 'ParseTreeNode.java'
  template = 'java/ParseTreeNode.java.tpl'

class JavaParseTreeTemplate(JavaTemplate):
  filename = 'ParseTree.java'
  template = 'java/ParseTree.java.tpl'

class JavaTerminalIdentifierTemplate(JavaTemplate):
  filename = 'TerminalIdentifier.java'
  template = 'java/TerminalIdentifier.java.tpl'

class JavaTerminalMapTemplate(JavaTemplate):
  filename = 'TerminalMap.java'
  template = 'java/TerminalMap.java.tpl'

class JavaSyntaxErrorTemplate(JavaTemplate):
  filename = 'SyntaxError.java'
  template = 'java/SyntaxError.java.tpl'

class JavaTokenStreamTemplate(JavaTemplate):
  filename = 'TokenStream.java'
  template = 'java/TokenStream.java.tpl'

class JavaSourceCodeTemplate(JavaTemplate):
  filename = 'SourceCode.java'
  template = 'java/SourceCode.java.tpl'

class JavaSyntaxErrorFormatterTemplate(JavaTemplate):
  filename = 'SyntaxErrorFormatter.java'
  template = 'java/SyntaxErrorFormatter.java.tpl'

class JavaMainTemplate(JavaTemplate):
  filename = 'ParserMain.java'
  template = 'java/ParserMain.java.tpl'

class CHeaderTemplate(CTemplate):
  template = 'c/parser.h.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.h')

class CSourceTemplate(CTemplate):
  template = 'c/parser.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.c')

class CCommonHeaderTemplate(CTemplate):
  filename = 'parser_common.h'
  template = 'c/parser_common.h.tpl'

class CCommonSourceTemplate(CTemplate):
  filename = 'parser_common.c'
  template = 'c/parser_common.c.tpl'

class CMainSourceTemplate(CTemplate):
  filename = 'parser_main.c'
  template = 'c/parser_main.c.tpl'

class JavascriptParserTemplate(JavascriptTemplate):
  template = 'javascript/parser.js.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.js')

class JavascriptCommonTemplate(JavascriptTemplate):
  template = 'javascript/common.js.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'common.js')

class JavascriptMainTemplate(JavascriptTemplate):
  template = 'javascript/main.js.tpl'
  def get_filename(self):
    return os.path.join(self.directory, 'main.js')

class PythonTemplateFactory:
  def create(self, **kwargs):
    templates = [
        PythonCommonTemplate(),
        PythonParserTemplate(),
        PythonInitTemplate()
    ]
    if kwargs['grammar'].lexer:
      templates.extend([PythonLexerTemplate()])
    if kwargs['add_main']:
      templates.append(PythonMainTemplate())
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
      JavaTerminalMapTemplate(),
      JavaParseTreeNodeTemplate(),
      JavaSyntaxErrorTemplate(),
      JavaTokenStreamTemplate(),
      JavaSourceCodeTemplate(),
      JavaTerminalIdentifierTemplate(),
      JavaSyntaxErrorFormatterTemplate(),
      JavaParserTemplate()
    ]
    if kwargs['add_main']:
      templates.append(JavaMainTemplate())
    return templates

class CTemplateFactory:
  def create(self, **kwargs):
    templates = [
        CCommonHeaderTemplate(),
        CCommonSourceTemplate(),
        CSourceTemplate(),
        CHeaderTemplate()
    ]
    if kwargs['add_main']:
      templates.append(CMainSourceTemplate())
    return templates

class JavascriptTemplateFactory:
  def create(self, **kwargs):
    templates = [
        JavascriptCommonTemplate(),
        JavascriptParserTemplate()
    ]
    if kwargs['add_main'] and kwargs['nodejs']:
      templates.append(JavascriptMainTemplate())
    return templates

class CodeGenerator:
  templates = {
    'python': PythonTemplateFactory,
    'c': CTemplateFactory,
    'java': JavaTemplateFactory,
    'javascript': JavascriptTemplateFactory
  }
  def get_template_factory(self, language):
    for (template_language, template_class) in self.templates.items():
      if template_language == language:
        return template_class()
    raise Exception('Invalid language: ' + language)

  def generate(self, grammar, language, directory='.', add_main=False, java_package=None, python_package=None, nodejs=False):
      template_factory = self.get_template_factory(language)
      templates = template_factory.create(
          grammar=grammar,
          directory=directory,
          add_main=add_main,
          java_package=java_package,
          python_package=python_package,
          nodejs=nodejs
      )
      for template in templates:
          template.grammar = grammar
          template.directory = directory
          template.add_main = add_main
          template.java_package = java_package
          template.python_package = python_package
          template.nodejs = nodejs
          code = template.write()
