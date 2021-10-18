from unittest import TestCase
from uuid import uuid4

from model import *
from tempfile import mkdtemp


class Test(TestCase):
    def setUp(self) -> None:
        global DB_PATH
        DB_PATH = mkdtemp()
        make_database()

    def test_make_database(self):
        pass

    def test_log_message(self):
        job_id = str(uuid4().hex)
        second_job_id = str(uuid4().hex)
        for x in range(50):
            save_log_message(job_id, f'for the {x}th time')
            save_log_message(second_job_id, f'2nd job {x} along')

    def test_write_read_job(self):
        job_id = str(uuid4().hex)
        save_new_job(job_id, 'https://youtu.be/B9FzVhw8_bY', 'test-temp')
        rc = get_next_job()
        self.assertIsNotNone(rc)
        self.assertEqual(rc['job_id'], job_id)
        rc = get_next_job()
        self.assertIsNone(rc)

    def test_update_jobstatus(self):
        job_id = str(uuid4().hex)
        save_new_job(job_id, 'https://youtu.be/B9FzVhw8_bY', 'test-temp')
        update_job_status(job_id, 'DONE', 990)
        rc = get_job(job_id)
        self.assertIsNotNone(rc)
        self.assertEqual(rc['return_code'], 990)

    def test_write_read_many_jobs(self):
        for x in range(100):
            job_id = uuid4().hex
            save_new_job(job_id, 'https://youtu.be/ZwVW1ttVhuQ', 'tmp')
            rc = get_job(job_id)
            self.assertIsNotNone(rc)
            self.assertEqual(rc['dest_dir'], 'tmp')
