from flask import Blueprint, render_template, request, Response
from pygtail import Pygtail
import os, sys, time, errno
from zipfile import ZipFile
from io import BytesIO

from libs.logger import logger, LOG_FILE
logger = logger.getChild('webapp')

from libs.nrgreader import Reader

main = Blueprint('main', __name__)

@main.route('/')
def index():
    #togeher with read_from_end parameter for Pygtail, below ensures Pygtail does not load logfile history when loading web console
    remove_pygtail_offset() 
    #time.sleep(0.5)
    logger.info("Application console open")
    return render_template('index.html')


@main.route('/log')
def progress_log():
    def generate():
        for line in Pygtail(LOG_FILE, every_n=1, read_from_end=True):
            yield "data:" + str(line) + "\n\n"
            time.sleep(0.2)
    return Response(generate(), mimetype= 'text/event-stream')


@main.route('/trigger')
def trigger():
    period = request.args.get('period')
    logger.info(f"/trigger called with period '{period}'")
    rp = Reader(period)
    rp.execute()
    return ('', 204)


@main.route('/read_now')
def read_now():
    rp = Reader()
    rp.execute()
    return ('', 204)


@main.route('/get_logs')
def download_logs():
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zip_obj:
        # Iterate over all the files in directory
        for dirpath, dirnames, filenames in os.walk('logs'):
            for filename in filenames:
                zip_obj.write(os.path.join(dirpath, filename), 
                              os.path.relpath(os.path.join(dirpath, filename), os.path.join(dirpath, '..')))
    memory_file.seek(0)
    return Response(
        memory_file,
        mimetype="application/zip",
        headers={"Content-disposition":
                 "attachment; filename=logs.zip"})


def remove_pygtail_offset():
    try:
        os.remove(LOG_FILE+".offset")
    except OSError as e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise