import logging
import os
import shutil
from pathlib import Path

from flask import Flask, make_response, request, render_template, redirect, url_for

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask('dirs-test')
app.logger.setLevel(logging.DEBUG)


dest_vol = '/Users/phubbard/dev/ytdl-web'

def make_dirlist(parent):
    # Return a list of Path objects for all directories under parent
    all_things = Path(parent)
    all_dirs = [x.name for x in all_things.iterdir() if x.is_dir()]
    # Remove any directories with names starting with a dot
    filtered_dirs = [x for x in all_dirs if not x.startswith(('.'))]
    return sorted(filtered_dirs)

@app.route('/')
def index():
    return render_template('dirs.html', dirs=make_dirlist(dest_vol))

if __name__ == '__main__':
    print(make_dirlist(dest_vol))
    app.run(debug=True)

