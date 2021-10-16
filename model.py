#!/usr/share/bin/env python3
# pfh 10/15/2021
# Data model for updated version - store jobs and logs in sqlite,
# use separate workers to DL.

import logging
import sqlite3
import time
from uuid import uuid4

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('data model')

DB_NAME = "ytdl.sqlite"
LOG_TABLE = "logs"
JOB_TABLE = "jobs"
JOB_STATES = ['NEW', 'RUNNING', 'DONE']

def _get_db():
    # See https://stackoverflow.com/questions/43691588/python-multiprocessing-write-the-results-in-the-same-file
    conn = sqlite3.connect(DB_NAME, isolation_level="EXCLUSIVE")
    # I want key:value pairs, not a plain tuple
    # https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor


def make_database(fake_record = False):
    log.warning('Starting DB creation')
    try:
        conn, cursor = _get_db()
        log.warning('Dropping tables')
        cursor.execute(f'DROP TABLE {JOB_TABLE}')
        cursor.execute(f'DROP TABLE {LOG_TABLE}')
        conn.commit()
        log.warning('Jobs table')
        cursor.execute(f'''CREATE TABLE {JOB_TABLE}
                        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        url text NOT NULL, 
                        dest_dir text NOT NULL, 
                        job_id text NOT NULL,
                        status text NOT NULL, 
                        return_code INTEGER)''')
        log.warning('Log table')
        cursor.execute(f'''CREATE TABLE {LOG_TABLE}
                        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id text NOT NULL, 
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        message text NOT NULL)''')
        log.warning('Committing the changes')
        conn.commit()

        if fake_record:
            log.info('Creating fake record')
            cursor.execute(f'''INSERT INTO {JOB_TABLE} (url, dest_dir, job_id, status, return_code) values 
                ("https://google.com/", "/tmp", "{uuid4().hex}", "NEW", 0)''')
            conn.commit()
    except Exception as e:
        log.exception(e)
    finally:
        log.info('Closing the connection at end of DB creation')
        conn.close()


def save_log_message(job_id, message):
    try:
        conn, cursor = _get_db()
        cursor.execute(f'INSERT INTO {LOG_TABLE} (job_id, message) values ("{job_id}", "{message}")')
        conn.commit()
    except Exception as e:
        log.exception(e)
    finally:
        log.info('Closing the DB connection')
        conn.close()


def get_job():
    try:
        conn, cursor = _get_db()
        log.info('Checking for jobs...')
        iter = cursor.execute(f'SELECT * FROM {JOB_TABLE} WHERE STATUS="NEW" LIMIT 1')
        record = iter.fetchone()
        if not record:
            log.info('No jobs found')
        else:
            log.info(f'Starting job {dict(record)}')
            log.info(f'Updating job record')
            cursor.execute(f'UPDATE {JOB_TABLE} SET status="RUNNING" WHERE ID={record["ID"]}')
            conn.commit()
            log.warning('Working...done.')
            cursor.execute(f'UPDATE {JOB_TABLE} SET status="DONE" WHERE ID={record["ID"]}')
            conn.commit()
    except Exception as e:
        log.exception(e)
    finally:
        log.warning('Closing the connection')
        conn.close()


if __name__ == '__main__':
    # make_database(True)
    # get_job()
    job_id = str(uuid4().hex)
    for x in range(1000):
        save_log_message(job_id, f'for the {x}th time')