#!/usr/bin/env python3
# Code to read config file and create database

from __future__ import unicode_literals
from configparser import ConfigParser
import logging
from pathlib import Path
import socket
import sys


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('make-database')

# Load per-host config from config file
hostname = socket.gethostname()
config = ConfigParser()
config.read("config.ini")
try:
    DEST_VOL = config[hostname]['dest_vol']
    DEFAULT_DIR = config[hostname]['dest_default']
    DB_DIR = config[hostname]['db_dir']
except KeyError:
    log.fatal(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)

DB_NAME = "ytdl.sqlite"
LOG_TABLE = "logs"
JOB_TABLE = "jobs"
JOB_STATES = ['NEW', 'RUNNING', 'DONE']

# We need absolute path for DB otherwise os.cwd breaks this
DB_PATH = str(Path(DB_DIR) / DB_NAME)
