# Background process code
from __future__ import unicode_literals

from configparser import ConfigParser
from dataclasses import dataclass
import logging
import sqlite3
import os
from pathlib import Path
import socket
import sys
import typing
from uuid import uuid4

import youtube_dl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('ytdl-web-worker')

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
    polls: int = 0


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

