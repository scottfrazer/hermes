import re, moody, os
from pkg_resources import resource_filename
from collections import OrderedDict

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
# nodejs
# directory
# add_main
#####

class GrammarTemplate:
  def __init__(self):
    super().__init__()
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
    return out_file_path

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

class PythonTemplate(GrammarTemplate):
  template = 'python/Template.py.tpl'
  def get_filename(self):
    return os.path.join(self.directory, '{0}_parser.py'.format(self.grammar.name))

class JavaParserTemplate(JavaTemplate):
  filename = 'Parser.java'
  template = 'java/ParserTemplate.java.tpl'
  def get_filename(self):
    prefix = underscore_to_camelcase(self.grammar.name)
    return os.path.join(self.directory, self.java_package_to_path(), prefix + self.filename)

class JavaLexerTemplate(JavaTemplate):
  filename = 'Lexer.java'
  template = 'java/LexerTemplate.java.tpl'
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

class CSource(CTemplate):
  template = 'c/template.c.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.c')

class CHeader(CTemplate):
  template = 'c/template.h.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.h')

class JavascriptParserTemplate(JavascriptTemplate):
  template = 'javascript/parser.js.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_parser.js')

class JavascriptLexerTemplate(JavascriptTemplate):
  template = 'javascript/lexer.js.tpl'
  def get_filename(self):
    return os.path.join(self.directory, self.grammar.name.lower() + '_lexer.js')

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
    return [PythonTemplate()]

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
    if 'lexer' in kwargs and kwargs['lexer'] is not None:
      templates.append(JavaLexerTemplate())
    if kwargs['add_main']:
      templates.append(JavaMainTemplate())
    return templates

class CTemplateFactory:
  def create(self, **kwargs):
    return [CSource(), CHeader()]

class JavascriptTemplateFactory:
  def create(self, **kwargs):
    templates = [
        JavascriptCommonTemplate(),
        JavascriptParserTemplate()
    ]
    if 'lexer' in kwargs and kwargs['lexer'] is not None:
      templates.append(JavascriptLexerTemplate())
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

    def generate_internal(self, grammar):
        template_factory = self.get_template_factory('python')
        args = {
            'grammar': grammar,
            'language': 'python',
            'lexer': grammar.lexers['python'] if 'python' in grammar.lexers else None,
            'add_main': False
        }

        code = ''
        templates = template_factory.create(**args)
        for template in templates:
            template.__dict__.update(args)
            code += template.render()
            code += '\n'
        return code

    def generate(self, grammar, language, directory='.', add_main=False, java_package=None, nodejs=False):
        template_factory = self.get_template_factory(language)
        args = locals()
        del args['self']
        args['lexer'] = grammar.lexers[language] if language in grammar.lexers else None
        args['python_internal'] = False
        templates = template_factory.create(**args)
        for template in templates:
            template.__dict__.update(args)
            template.write()
