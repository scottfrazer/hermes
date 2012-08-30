import logging

class Factory:
  def initialize(self, debug):
    if debug:
      mode = logging.DEBUG
    else:
      mode = logging.WARNING

    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    if debug:
      fileLogger = logging.FileHandler('hermes.log')
      fileLogger.setLevel( mode )
      fileLogger.setFormatter(formatter)

    stdoutLogger = logging.StreamHandler()
    stdoutLogger.setLevel( mode )
    stdoutLogger.setFormatter(formatter)

    logger = logging.getLogger('hermes')
    logger.addHandler(stdoutLogger)
    logger.setLevel( mode )
    return logger
  def getProgramLogger(self):
    return logging.getLogger('hermes')
  def getModuleLogger(self, module):
    return logging.getLogger('%s' % (module))
  def getClassLogger(self, module, className):
    return logging.getLogger('%s.%s' % (module, className))
