from waitress import serve

from libs.logger import logger, LOG_FILE
logger = logger.getChild('run')

import webapp

if __name__ == '__main__':
    try:
        app = webapp.create_app()
        logger.info("Starting web conosole at 0.0.0.0:5000")
        serve(app, host="0.0.0.0", port=5000)
    except (KeyboardInterrupt, SystemExit):
        exit
    pass