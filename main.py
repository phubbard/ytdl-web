from __future__ import unicode_literals
import logging
import os
import shutil
from pathlib import Path
import tempfile

from flask import Flask, make_response, request, render_template, redirect, url_for
import youtube_dl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask('ytdl-web')
app.logger.setLevel(logging.DEBUG)


buffer = []
dest_vol = '/Volumes/video'
dest_vol = '/Users/phubbard/dev/ytdl-web'
# TODO Dropdown of choices
#dest_dir = 'New'
default_dir = 'tmp'

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


def save_files(dest_dir=default_dir):
    # Given file(s) in CWD, move them all into the destination directory.
    # If error, throws OSError or shutil.Error
    filenames = sorted(Path('.').glob('*'))
    if len(filenames) == 0:
        app.logger.error('No files found to move!')
        return

    dest_path = Path(dest_vol, dest_dir)
    if dest_path.exists() and dest_path.is_dir():
        app.logger.debug(f'Destination looks OK, {len(filenames)} file(s) found')
        for file in filenames:
            app.logger.info(f"Moving {file} to {dest_path}")
            shutil.move(file, dest_path)
    else:
        app.logger.error(f'Unable to use destination directory {dest_path}')


def my_hook(d):
    # Event hook - status seems to be finished or downloading
    if d['status'] == 'finished':
        stats = f"{d['_total_bytes_str']} {d['filename']}"
        app.logger.info(f"Done OK: {stats}")
        buffer.append(f'Done {stats}')
    elif d['status'] == 'error':
        app.logger.error(f"==> {str(d)}")
        buffer.append(str(d))

ydl_opts = {
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

# Display the to-be-downloaded page
@app.route('/', methods=['GET'])
def index():
    buffer = []
    return render_template('index.html', dirs=make_dirlist(dest_vol), default_dir=default_dir)


# todo display something while downloading
@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    app.logger.info(f"Starting on {url} to {dest_dir}")
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        try:
            save_files(dest_dir)
            done_ok = True
        except shutil.Error as err:
            done_ok = False
            buffer.append(str(err))

    app.logger.info(f'Done {done_ok}')
    return render_template('results.html', messages=buffer, status=done_ok,
                           url=url, dest_dir=dest_dir, restart_url=url_for('index'))


if __name__ == '__main__':
    app.logger.debug(make_dirlist(dest_vol))
    app.run(debug=True)