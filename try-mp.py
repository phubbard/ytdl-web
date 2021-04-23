#!/usr/bin/evn python3
# Scratchpad to figure out SMP/shared datastructures code.
# pfh 4/22/2021
from __future__ import unicode_literals
from configparser import ConfigParser
import logging
from multiprocessing import Process
import os
from pathlib import Path
import socket
import sys

from flask import Flask, make_response, request, render_template, redirect, url_for
import youtube_dl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger()
app = Flask('ytdl-web-smp')


# Load per-host config from config file
hostname = socket.gethostname()
config = ConfigParser()
config.read("config.ini")
try:
    dest_vol = config[hostname]['dest_vol']
    default_dir = config[hostname]['dest_default']
except KeyError:
    log.error(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)


@app.route('/poll/{job_id}')
def poll(job_id):
    global jobs

    # Linear search for job id - can't pass URL as path param. FIXME
    for job in jobs:
        if job.id == job_id:
            if not job.done:
                job.polls += 1
                if job.polls >= 60:
                    # TODO
                    log.error(f"Polling maxed on {job}")
                else:
                    return render_template("working.html", progress=job.progress, msgs=job.messages)
            else:
                # done! happy path
                return render_template('results.html', messages=job.messages, status=not job.error,
                                       dest_dir='FIXME', restart_url=url_for('index'))
    # Job not found
    return make_response(f'Unable to locate {job_id}', 403)


def worker(my_url: str, dest: Path):
    cur_dir = os.getcwd()
    try:
        os.chdir(dest)
        app.logger.debug(f'Destination looks OK, starting on {my_url}')
        with youtube_dl.YoutubeDL() as ydl:
            ydl.download([my_url])
    except OSError as ose:
        app.logger.exception(ose)
    finally:
        os.chdir(cur_dir)

    log.info(f"Worker done with {my_url}")


def test_explicit(url: str, dest_dir: str):
    dest_path = Path(dest_vol, dest_dir)
    p = Process(target=worker, args=(url, dest_path))
    p.start()


@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    test_explicit(url, dest_dir)
    return render_template('bg.html', restart_url=url_for('index'))


def tester():
    # Exercise the MP code
    urls = [
        'https://www.youtube.com/watch?v=fyyiJc0Wk2M&feature=emb_imp_woyt',
        'https://youtu.be/yy0zS0ZENkA',
        'https://youtu.be/QWPytpiml5c'
    ]
    for url in urls:
        test_explicit(url, default_dir)


if __name__ == '__main__':
    tester()
