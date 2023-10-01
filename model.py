#!/usr/bin/bin/env python3
# pfh 10/15/2021
# Data model for updated version - store jobs and logs in sqlite,
# use separate workers to DL. Trying raw sqlite without an ORM as a learning exercise.

import functools
import logging
import sqlite3
import time
from uuid import uuid4

from config import DB_PATH, LOG_TABLE, JOB_TABLE, JOB_STATES


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
log = logging.getLogger('model')


def _get_db():
    # Shared / common routine to open the DB in locked mode - this should block if another
    # process has it in use. A bit of a hack, but given our low transaction/use rates it works.
    # See https://stackoverflow.com/questions/43691588/python-multiprocessing-write-the-results-in-the-same-file
    conn = sqlite3.connect(DB_PATH, isolation_level="EXCLUSIVE")
    # I want key:value pairs, not a plain tuple
    # https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor


def db_wrapper(func):
    # Code reuse for the try/catch code. Combines DB access and a timer.
    # N.B. invokes commit every time - atomic but slower.
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        cursor: None
        conn = cursor = None

        try:
            conn, cursor = _get_db()
            start_time = time.perf_counter()
            value = func(*args, **kwargs, cursor=cursor)
            run_time = time.perf_counter() - start_time
            # log.debug(f'{func.__name__} in {run_time:.4f} seconds')
            return value
        except sqlite3.Error as e:
            log.exception(e)
        finally:
            conn.commit()
            conn.close()
    return wrapped_func


@db_wrapper
def make_database(fake_record=False, cursor=None):
    log.info('Creating jobs table')
    cursor.execute(f'''CREATE TABLE {JOB_TABLE}
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    url text NOT NULL, 
                    dest_dir text NOT NULL, 
                    job_id text NOT NULL,
                    status text NOT NULL, 
                    return_code INTEGER)''')
    # TODO Move logs to one file per UUID-named directory... this is overkill
    log.info('Log table')
    cursor.execute(f'''CREATE TABLE {LOG_TABLE}
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id text NOT NULL, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    message text NOT NULL)''')
    log.info('Committing the changes')

    if fake_record:
        log.info('Creating fake record')
        cursor.execute(f'''INSERT INTO {JOB_TABLE} (url, dest_dir, job_id, status, return_code) values 
            ("https://google.com/", "/tmp", "{uuid4().hex}", "NEW", 0)''')


@db_wrapper
def save_log_message(job_id, message, cursor=None):
    # TODO append to text file instead of DB
    cursor.execute(f'INSERT INTO {LOG_TABLE} (job_id, message) values ("{job_id}", "{message}")')


@db_wrapper
def save_new_job(job_id: str, url: str, dest_dir: str, cursor=None):
    cursor.execute(f'INSERT INTO {JOB_TABLE} (url, dest_dir, job_id, status) values (?,?,?,?)',
                   (url, dest_dir, job_id, "NEW"))


@db_wrapper
def update_job_status(job_id: str, status: str, return_code: int, cursor=None):
    assert(status in JOB_STATES)
    log.info(f'Updating job record {job_id} to {status} rc={return_code}')
    cursor.execute(f'''UPDATE {JOB_TABLE} 
                    SET status=?,
                    return_code=? 
                    WHERE job_id="{job_id}"''',
                   (status, return_code))


@db_wrapper
def get_next_job(cursor=None):
    # Get new job to DL, returns None if none to be had
    log.info('Checking for jobs...')
    row_cursor = cursor.execute(f'SELECT * FROM {JOB_TABLE} WHERE STATUS="NEW" LIMIT 1')
    row = row_cursor.fetchone()
    if row is None:
        log.info('No jobs found')
    else:
        # Cast into dict, otherwise its an sqlite.Row object
        record = dict(row)
        log.info(f'Starting job {record}')
        # Do the raw update here, since we are already in a decorated function.
        cursor.execute(f'UPDATE {JOB_TABLE} SET status="RUNNING" WHERE ID={record["ID"]}')
        return record


@db_wrapper
def get_job(job_id: str, cursor=None):
    query = cursor.execute(f'SELECT * FROM {JOB_TABLE} WHERE job_id=? LIMIT 1', (job_id,))
    row = query.fetchone()
    if row is None:
        log.error(f'Unable to locate job {job_id}')
        return None
    return dict(row)


@db_wrapper
def get_job_logs(job_id: str, cursor=None):
    query = cursor.execute(f'SELECT * from {LOG_TABLE} WHERE job_id=?', (job_id,))
    rows = query.fetchall()
    log.debug(f'{len(rows)} found for job {job_id}')
    # From array of Row objects to array of dicts
    dicts = [dict(x) for x in rows]
    # To array of 'timestamp message' strings
    msgs = [f"{x['timestamp']} {x['message']}" for x in dicts]
    return msgs


@db_wrapper
def get_all_jobs(start: int, limit: int, cursor=None):
    # TODO add pagination
    query = cursor.execute(f'SELECT * from {JOB_TABLE} ORDER BY timestamp DESC LIMIT {limit}')
    # TODO Extract this pattern into function?
    rows = query.fetchall()
    dicts = [dict(x) for x in rows]
    return dicts
