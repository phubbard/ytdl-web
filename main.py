from __future__ import unicode_literals
from configparser import ConfigParser
from dataclasses import dataclass
import logging
import multiprocessing
import os
from pathlib import Path
import socket
import sys

from flask import Flask, make_response, request, render_template, redirect, url_for
import youtube_dl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask('ytdl-web-smp')
app.logger.setLevel(logging.DEBUG)

@dataclass
class Download:
    # Class for download info/sync across processes
    messages: list
    progress: int = 0
    size_bytes: int = 0
    fetched_bytes: int = 0

manager = multiprocessing.managers.SyncManager()
results = manager.dict()

# Global message buffer - see MyLogger
buffer = []

# Load per-host config froom config file
hostname = socket.gethostname()
config = ConfigParser()
config.read("config.ini")
try:
    dest_vol = config[hostname]['dest_vol']
    default_dir = config[hostname]['dest_default']
except KeyError:
    app.logger.error(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)


class MyLogger(object):
    def debug(self, msg):
        pass
        #buffer.append(msg)

    def warning(self, msg):
        buffer.append(f"WARN {msg}")
        app.logger.warning(msg)

    def error(self, msg):
        buffer.append(f"ERROR {msg}")
        app.logger.error(msg)


def make_dirlist(parent):
    # Return a list of Path objects for all directories under parent
    all_things = Path(parent)
    all_dirs = [x.name for x in all_things.iterdir() if x.is_dir()]
    # Remove any directories with names starting with a dot
    filtered_dirs = [x for x in all_dirs if not x.startswith(('.'))]
    return sorted(filtered_dirs)


def my_hook(d):
    # Event hook - status seems to be finished or downloading
    if d['status'] == 'finished':
        stats = f"{d['_total_bytes_str']} {d['filename']}"
        app.logger.info(f"Done OK: {stats}")
        buffer.append(f'Done {stats}')
    elif d['status'] == 'error':
        app.logger.error(f"==> {str(d)}")
        buffer.append(str(d))

# YTDL options - quality, etc. Defaults work here, so just add hooks.
ydl_opts = {
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

# Display the to-be-downloaded page
@app.route('/', methods=['GET'])
def index():
    global buffer
    buffer = []
    return render_template('index.html', dirs=make_dirlist(dest_vol), default_dir=default_dir)


# todo display something while downloading
@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['vidlink']
    dest_dir = request.form['destination']

    dest_path = Path(dest_vol, dest_dir)
    cur_dir = os.getcwd()
    try:
        os.chdir(dest_path)
        app.logger.debug(f'Destination looks OK, starting on {url}')
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        done_ok = True
    except OSError as ose:
        done_ok = False
        buffer.append(f'Error in target directory {str(ose)}')
    finally:
        os.chdir(cur_dir)

    app.logger.info(f'Done {done_ok}')
    return render_template('results.html', messages=buffer, status=done_ok,
                           url=url, dest_dir=dest_dir, restart_url=url_for('index'))


if __name__ == '__main__':
    app.logger.info(f'Configuration: {socket.gethostname()} {dest_vol} {default_dir}')
    app.logger.debug(f'Directories: {make_dirlist(dest_vol)}')
    app.run(debug=True, host='0.0.0.0')