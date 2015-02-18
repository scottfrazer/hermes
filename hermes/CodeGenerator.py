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

class PythonTemplate(GrammarTemplate):
    template = 'python/template.py.tpl'
    def get_filename(self):
        return os.path.join(self.directory, '{0}_parser.py'.format(self.grammar.name))

class JavaTemplate(GrammarTemplate):
    template = 'java/template.java.tpl'
    def get_filename(self):
        prefix = underscore_to_camelcase(self.grammar.name)
        return os.path.join(self.directory, self.java_package_to_path(), prefix + "Parser.java")
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

class CSource(CTemplate):
    template = 'c/template.c.tpl'
    def get_filename(self):
        return os.path.join(self.directory, self.grammar.name.lower() + '_parser.c')

class CHeader(CTemplate):
    template = 'c/template.h.tpl'
    def get_filename(self):
        return os.path.join(self.directory, self.grammar.name.lower() + '_parser.h')

class JavascriptTemplate(GrammarTemplate):
    template = 'javascript/template.js.tpl'
    def get_filename(self):
        return os.path.join(self.directory, self.grammar.name.lower() + '_parser.js')
    def render(self, **kwargs):
        self.prefix = self.grammar.name + '_'
        return super().render()

class CodeGenerator:
    templates = {
        'python': [PythonTemplate()],
        'c': [CSource(), CHeader()],
        'java': [JavaTemplate()],
        'javascript': [JavascriptTemplate()]
    }

    def generate_internal(self, grammar):
        args = {
            'grammar': grammar,
            'language': 'python',
            'lexer': grammar.lexers['python'] if 'python' in grammar.lexers else None,
            'add_main': False
        }

        code = ''
        for template in self.templates['python']:
            template.__dict__.update(args)
            code += template.render()
            code += '\n'
        return code

    def generate(self, grammar, language, directory='.', add_main=False, java_package=None, nodejs=False):
        if language not in self.templates:
            raise Exception('Invalid language: ' + language)
        args = locals()
        del args['self']
        args['lexer'] = grammar.lexers[language] if language in grammar.lexers else None
        for template in self.templates[language]:
            template.__dict__.update(args)
            template.write()
