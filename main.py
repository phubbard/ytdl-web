from __future__ import unicode_literals
from configparser import ConfigParser
import logging
from multiprocessing import Process
import os
from pathlib import Path
import socket
import sys
from uuid import uuid4

from flask import Flask, request, render_template, url_for, redirect, make_response
import youtube_dl

from model import save_log_message, get_job, get_job_logs, get_next_job, save_new_job, update_job_status


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask('ytdl-web-smp')
app.logger.setLevel(logging.DEBUG)


# Load per-host config froom config file
hostname = socket.gethostname()
config = ConfigParser()
config.read("config.ini")
try:
    dest_vol = config[hostname]['dest_vol']
    default_dir = config[hostname]['dest_default']
    DB_DIR = config[hostname]['db_dir']
except KeyError:
    app.logger.error(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)


class MyLogger(object):
    # TODO save job id for sqlite logger™
    def __init__(self, job_id):
        self.job_id = job_id
        super(MyLogger, self).__init__()

    def debug(self, msg):
        save_log_message(self.job_id, f'DBG {msg}')

    def warning(self, msg):
        save_log_message(self.job_id, f'WARN {msg}')

    def error(self, msg):
        save_log_message(self.job_id, f'ERR {msg}')
        # app.logger.error(msg)


def make_dirlist(parent):
    # Return a list of Path objects for all directories under parent
    all_things = Path(parent)
    all_dirs = [x.name for x in all_things.iterdir() if x.is_dir()]
    # Remove any directories with names starting with a dot
    filtered_dirs = [x for x in all_dirs if not x.startswith('.')]
    return sorted(filtered_dirs)


def worker(my_url: str, dest: Path, job_id: str):
    # TODO move to sqlite
    cur_dir = os.getcwd()
    try:
        os.chdir(dest)
        app.logger.debug(f'Destination looks OK, starting job{job_id} on {my_url}')
        with youtube_dl.YoutubeDL({'logger': MyLogger(job_id)}) as ydl:
            ydl.download([my_url])
            update_job_status(job_id, 'DONE', 0)
    except OSError as ose:
        app.logger.exception(ose)
        update_job_status(job_id, 'DONE', -1)
    finally:
        os.chdir(cur_dir)
    app.logger.info(f"Worker done with {my_url}")


# Display the to-be-downloaded page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', dirs=make_dirlist(dest_vol), default_dir=default_dir)


# Display a single download job
@app.route('/job/<job_id>', methods=['GET'])
def poll_job(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    # FIXME 404 page if none
    url = job_info['url']
    status = job_info['status']
    dest_dir = job_info['dest_dir']
    job_logs = get_job_logs(job_id)
    return render_template('job.html', job_logs=job_logs, url=url, status=status, dest_dir=dest_dir)


@app.route('/submit', methods=['POST'])
def submit():
    job_id = uuid4().hex
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    dest_path = Path(dest_vol, dest_dir)
    # Save to DB
    save_new_job(job_id, url, dest_dir)
    update_job_status(job_id, 'RUNNING', 0)
    p = Process(target=worker, args=(url, dest_path, job_id))
    p.start()
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')
    # return render_template('bg.html', restart_url=url_for('index'))


if __name__ == '__main__':
    app.logger.info(f'Configuration: {socket.gethostname()} {dest_vol} {default_dir}')
    app.logger.debug(f'Directories: {make_dirlist(dest_vol)}')
    app.run(debug=True, host='0.0.0.0')
