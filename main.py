from __future__ import unicode_literals
import logging
from multiprocessing import Process
import os
from pathlib import Path
import socket
from uuid import uuid4

from flask import Flask, request, render_template, url_for, redirect, make_response
import yt_dlp

from config import DEST_VOL, DEFAULT_DIR
from model import save_log_message, get_job, get_job_logs, \
    save_new_job, update_job_status, get_all_jobs


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask('ytdl-web-smp')
app.logger.setLevel(logging.DEBUG)


class MyLogger(object):
    # Callback hook class - ytdl library calls into this class, event driven
    # Save job id for sqlite logger
    def __init__(self, job_id):
        self.job_id = job_id
        self.filename = ''
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.progress = 0
        self.speed = 0
        self.eta_secs = -0
        super(MyLogger, self).__init__()

    @staticmethod
    def _clean_str(msg):
        # Need to strip out newlines/CR/LF from strings - the progress is multiline
        a = msg.replace('\n', ' ')
        return a.strip()

    def debug(self, msg):
        # TODO pull download percentage out for progress indicator?
        save_log_message(self.job_id, f'DBG {self._clean_str(msg)}')

    def warning(self, msg):
        save_log_message(self.job_id, f'WARN {self._clean_str(msg)}')

    def error(self, msg):
        save_log_message(self.job_id, f'ERR {self._clean_str(msg)}')
        # app.logger.error(msg)

    @staticmethod
    def progress_hook(dl_dict):
        # See https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl
        # /YoutubeDL.py#L230-L250
        if dl_dict['status'] == 'finished':
            # TODO
            pass


def make_dirlist(parent):
    # Return a list of Path objects for all directories under parent. Used to
    # create a list of destination directories.
    all_things = Path(parent)
    all_dirs = [x.name for x in all_things.iterdir() if x.is_dir()]
    # Remove any directories with names starting with a dot
    filtered_dirs = [x for x in all_dirs if not x.startswith('.')]
    return sorted(filtered_dirs)


# Worker process - single download job
# TODO poll the DB for other new jobs
def worker(my_url: str, dest: Path, job_id: str):
    cur_dir = os.getcwd()
    try:
        os.chdir(dest)
        app.logger.debug(f'Destination looks OK, starting job{job_id} on {my_url}')
        log_object = MyLogger(job_id)
        ydl_opts = {'logger': MyLogger(job_id),
                    'progress_hooks': [log_object.progress_hook],
                    "ignoreerrors": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([my_url])
            update_job_status(job_id, 'DONE', 0)
    except OSError as ose:
        # This doesn't catch a lot of failed downloads. FIXME.
        app.logger.exception(ose)
        update_job_status(job_id, 'DONE', -1)
    finally:
        os.chdir(cur_dir)
    app.logger.info(f"Worker done with {my_url}")


# Display the to-be-downloaded page (index)
@app.route('/', methods=['GET'])
def index():
    job_list = get_all_jobs(0, 20)
    return render_template('index.html', dirs=make_dirlist(DEST_VOL), default_dir=DEFAULT_DIR, job_list=job_list)


# Display a single download job
@app.route('/job/<job_id>', methods=['GET'])
def poll_job(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    url = job_info['url']
    status = job_info['status']
    dest_dir = job_info['dest_dir']
    job_logs = get_job_logs(job_id)
    restart_url = url_for('index')
    return render_template('job.html', job_logs=job_logs,
                           url=url, status=status, dest_dir=dest_dir,
                           restart_url=restart_url)


@app.route('/submit', methods=['POST'])
def submit():
    job_id = uuid4().hex
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    dest_path = Path(DEST_VOL, dest_dir)
    # Save to DB
    save_new_job(job_id, url, dest_dir)
    update_job_status(job_id, 'RUNNING', 0)
    p = Process(target=worker, args=(url, dest_path, job_id))
    p.start()
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')


@app.route('/retry/<job_id>', methods=['POST'])
def retry(job_id):
    job_info = get_job(job_id)
    if job_info is None:
        return make_response(f'Job {job_id} not found', 404)

    url = job_info['url']
    dest_dir = job_info['dest_dir']
    update_job_status(job_id, 'RUNNING', 0)
    p = Process(target=worker, args=(url, dest_dir, job_id))
    p.start()
    # send to new in-process page, job_id as key
    return redirect(f'/job/{job_id}')


if __name__ == '__main__':
    app.logger.info(f'Configuration: {socket.gethostname()} {DEST_VOL} {DEFAULT_DIR}')
    app.logger.debug(f'Directories: {make_dirlist(DEST_VOL)}')
    app.run(debug=True, host='0.0.0.0', port=5050)
