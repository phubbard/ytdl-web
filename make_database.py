#!/usr/bin/env python3
# Code to read config file and create database

from __future__ import unicode_literals
from configparser import ConfigParser
import logging
from multiprocessing import Process
import os
from pathlib import Path
import socket
import sys

from model import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('make-database')

# Load per-host config froom config file
hostname = socket.gethostname()
config = ConfigParser()
config.read("config.ini")
try:
    dest_vol = config[hostname]['dest_vol']
    default_dir = config[hostname]['dest_default']
    DB_DIR = config[hostname]['db_dir']
except KeyError:
    log.fatal(f"Add a {socket.gethostname()} section in config.ini")
    sys.exit(1)

if __name__ == '__main__':
    make_database()