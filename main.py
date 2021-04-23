from __future__ import unicode_literals
from configparser import ConfigParser
import logging
from multiprocessing import Process
import os
from pathlib import Path
import socket
import sys

from flask import Flask, request, render_template, url_for
import youtube_dl

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
except KeyError:
    app.logger.error(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass
        # app.logger.error(msg)


def make_dirlist(parent):
    # Return a list of Path objects for all directories under parent
    all_things = Path(parent)
    all_dirs = [x.name for x in all_things.iterdir() if x.is_dir()]
    # Remove any directories with names starting with a dot
    filtered_dirs = [x for x in all_dirs if not x.startswith('.')]
    return sorted(filtered_dirs)


def worker(my_url: str, dest: Path):
    cur_dir = os.getcwd()
    try:
        os.chdir(dest)
        app.logger.debug(f'Destination looks OK, starting on {my_url}')
        with youtube_dl.YoutubeDL({'logger': MyLogger()}) as ydl:
            ydl.download([my_url])
    except OSError as ose:
        app.logger.exception(ose)
    finally:
        os.chdir(cur_dir)
    app.logger.info(f"Worker done with {my_url}")


# Display the to-be-downloaded page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', dirs=make_dirlist(dest_vol), default_dir=default_dir)


@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    dest_path = Path(dest_vol, dest_dir)
    p = Process(target=worker, args=(url, dest_path))
    p.start()
    return render_template('bg.html', restart_url=url_for('index'))


if __name__ == '__main__':
    app.logger.info(f'Configuration: {socket.gethostname()} {dest_vol} {default_dir}')
    app.logger.debug(f'Directories: {make_dirlist(dest_vol)}')
    app.run(debug=True, host='0.0.0.0')
