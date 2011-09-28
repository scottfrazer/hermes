class Factory:
    def create(self, ansiColors = True):
        if ansiColors:
            colorizer = AnsiColorizer()
        else:
            colorizer = NullColorizer()
        return Styler(colorizer)

class Styler:
    def __init__(self, colorizer):
        self.__dict__.update(locals())
    def color(self, string, color):
        return self.colorizer.color(string, color)

class Colorizer:
    def color(self, string, color):
        raise Exception('Not implemented')

class NullColorizer:
    def color(self, string, color):
        return string

class AnsiColorizer:
    def __init__(self):
        self.colors = {
            'purple': '\033[95m',
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
        }
        self.endc = '\033[0m'

    def color(self, string, color):
        return "%s%s%s" % (self.colors[color], string, self.endc)
