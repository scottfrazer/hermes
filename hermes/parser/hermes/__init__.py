try:
  from .Lexer import lex
except ImportError:
  pass
from .Parser import parse
