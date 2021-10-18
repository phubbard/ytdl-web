#!/usr/bin/env python3
# Code to read config file and create database

from __future__ import unicode_literals
import logging

from config import DB_PATH
from model import make_database


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('make-database')

if __name__ == '__main__':
    log.info(f'DB is {str(DB_PATH)}')
    make_database()