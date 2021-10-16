import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('root')
logger.setLevel('INFO')

consoleHandler = logging.StreamHandler()
consoleFormatter = logging.Formatter('%(name)-5s - %(message)s')
consoleHandler.setFormatter(consoleFormatter)

LOG_FILE = 'logs/execution.log'

import os, sys
sys.path.insert(1, os.path.realpath(os.path.pardir))
fileHandler = TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=10)
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', '%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(fileFormatter)

logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)