#!/usr/bin/evn python3
# Scratchpad to figure out SMP/shared datastructures code.
# pfh 4/22/2021
from __future__ import unicode_literals
from configparser import ConfigParser
from dataclasses import dataclass
import logging
from multiprocessing import Manager, freeze_support, Process
import os
from pathlib import Path
import socket
import sys
import typing
from uuid import uuid4

from flask import Flask, make_response, request, render_template, redirect, url_for
import youtube_dl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger()
app = Flask('ytdl-web-smp')


@dataclass
class Download:
    # Class for download info/sync across processes
    id: str
    url: str
    messages: typing.List[str]
    progress: int = 0
    size_bytes: int = 0
    fetched_bytes: int = 0
    done: bool = False
    error: bool = False


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
    global results
    if results[job_id].done == False:
        return render_template("working.html", progress=results[job_id].progress,
                               msgs=results[job_id].messages)

    return render_template('results.html', messages=results[job_id].messages,
                           status=not results[job_id].error, dest_dir='foo',
                           restart_url=url_for('index'))


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def progress_hook(d):
    # Event hook - see https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L230-L253
    global result
    global url

    if d['status'] == 'downloading':
        result.fetched_bytes = d['downloaded_bytes']
        result.size_bytes = d['total_bytes']
        result.progress = 100.0 * (result.fetched_bytes / result.size_bytes)
        log.info(f"{url} {result.progress}% done")
    if d['status'] == 'finished':
        stats = f"{d['_total_bytes_str']} {d['filename']}"
        log.info(f"Done OK: {stats}")
        result.messages.append(f'Done {stats}')
        result.done = True
    elif d['status'] == 'error':
        result.messages.append(f'Error {str(d)}')
        log.error(f"==> {str(d)}")
        result.done = True
        result.error = True


def worker(my_url: str, proxy_obj: Download, dest: Path):
    # Per-process globals - the second is a shared proxy object
    global url
    global result
    url = my_url
    result = proxy_obj
    cur_dir = os.getcwd()

    try:
        os.chdir(dest)
        app.logger.debug(f'Destination looks OK, starting on {url}')
        with youtube_dl.YoutubeDL({'progress_hooks': [progress_hook],
                                  'logger': MyLogger()}) as ydl:
            ydl.download([url])
    except OSError as ose:
        app.logger.exception(ose)
    finally:
        os.chdir(cur_dir)

    log.info(f"Worker done with {url} {str(result)}")


def test_explicit(url, dest_dir) -> str:

    dest_path = Path(dest_vol, dest_dir)
    jobid = uuid4().hex
    d = Download(jobid, url, [])
    results[jobid] = d
    p = Process(target=worker, args=(url, d, dest_path))
    p.start()
    return jobid


# todo display something while downloading
@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['vidlink']
    dest_dir = request.form['destination']
    jobid = test_explicit(url, dest_dir)
    return redirect(f'/poll/{jobid}')


def tester():
    # Exercise the MP code
    urls = ['https://www.youtube.com/watch?v=fyyiJc0Wk2M&feature=emb_imp_woyt',
            'https://youtu.be/yy0zS0ZENkA',
            'https://youtu.be/QWPytpiml5c']
    for url in urls:
        test_explicit(url, default_dir)

if __name__ == '__main__':
    manager = Manager()
    global results
    results = manager.dict()
    tester()