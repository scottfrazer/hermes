import logging

class Factory:
  def initialize(self, debug):
    if debug:
      mode = logging.DEBUG
    else:
      mode = logging.WARNING
    logger = logging.getLogger('hermes')
    logger.setLevel( mode )
    fileLogger = logging.FileHandler('hermes.log')
    fileLogger.setLevel( mode )
    stdoutLogger = logging.StreamHandler()
    stdoutLogger.setLevel( mode )
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    fileLogger.setFormatter(formatter)
    stdoutLogger.setFormatter(formatter)
    logger.addHandler(fileLogger)
    logger.addHandler(stdoutLogger)
    return logger
  def getProgramLogger(self):
    return logging.getLogger('cast')
  def getModuleLogger(self, module):
    return logging.getLogger('%s' % (module))
  def getClassLogger(self, module, className):
    return logging.getLogger('%s.%s' % (module, className))