import pycron
import time
import sqlite_utils
from datetime import datetime, timedelta
import sched
import types
import marshal
import sys
import logging
import time
import os 

def cron_query(cron):
    return pycron.has_been(cron, since = datetime.now() - timedelta(seconds = 1), dt = datetime.now())

def log_job_status(status, misc=None):
    return {'job_id': id, 'status': status, 'misc': misc}

def make_wrapped_function(job, imports = {'sys': sys, 'print': logging.info}, cb = None):
    executable = types.FunctionType(marshal.loads(job['bytes']), imports, job['name'])

    #if job['tracer'] is not None:
    #    tracer = types.FunctionType(marshal.loads(job['tracer']), imports, job['name'])
    #    return tracer(executable)

    def wrapped_function():
        logs = [log_job_status(job['id'],'started')]
        try:
            logs.append(log_job_status(job['id'],'success', misc=executable()))
        except Exception as e:
            logs.append(log_job_status(job['id'],'error', misc=str(e)))
        finally:
            logs.append(log_job_status(job['id'],'finished'))
            if cb is not None:
                return cb(logs)
            return logs

    return wrapped_function

class schedule_ctx(sched.scheduler):
    def __init__(self, db = './jobs.db'):
        super().__init__(time.time, time.sleep)
        self.jobs = {}
        self.db = sqlite_utils.Database(db)
        self.db.executescript(open('./init.sql','r').read())
        self.db.register_function(self.update_active_jobs)
        self.db.register_function(self.schedule_job)
        self.db.register_function(cron_query)
        

        for row in self.db['job'].rows:
            self.jobs[row['id']] = make_wrapped_function(row)

        self.schedule_query = "select schedule_job(id) from job where cron_query(cron) = 1"
        
            
    def init_execution_ctx(self, job):
        self.active_jobs[job] = make_wrapped_function(job, cb = self.default_tracer_callback)

    def update_active_jobs(self, job_id, action):
        print(job_id, action)
        if action == 'INSERT':
            self.jobs[job_id] = self.init_execution_ctx(self.db['job'].get(job_id))
        elif action == 'UPDATE':
            self.jobs[job_id] = self.init_execution_ctx(self.db['job'].get(job_id))
        elif action == 'DELETE':
            del self.jobs[job_id]

    def schedule_job(self, job_id):
        try:
            self.enter(action = self.jobs[job_id], priority=1, delay=0)
            return job_id
        except Exception as e:
            logging.ERROR(f'Error in job: {job_id} : {e}')
            return False

    def cron_query_jobs(self):
        return [row.values() for row in self.db.query(self.schedule_query)]

    def loop(self):
        while True:
            self.current_time = datetime.now()
            jobs = self.cron_query_jobs()
            logging.info(f"Running jobs: {str(self.queue)}")
            self.current_queue = self.queue
            self.run()
            time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(filename='./simple_sched.log',format='%(asctime)s %(levelname)-8s %(message)s', encoding='utf-8', level=logging.DEBUG)
    s = schedule_ctx()
    s.loop()