import pycron
import time
import sqlite_utils
from datetime import datetime, timedelta
import sched
import marshal
import sys
import logging
import time
from croniter import croniter

def log_job_status(status, misc=None):
    return {'job_id': id, 'status': status, 'misc': misc}

def make_wrapped_function(job, imports = {'sys': sys, 'print': logging.info}, next = None, cb = None):
    bytes = job['bytes']
    locals = {}
    if bytes is None:
        try:
            bytes = marshal.dumps(compile(job['source'], '<string>', 'exec'))
        except Exception as e:
            logging.error('Error compiling job: %s', job['id'])
            logging.exception(e)
            return None
    #if job['tracer'] is not None:
    #    tracer = types.FunctionType(marshal.loads(job['tracer']), imports, job['name'])
    #    return tracer(executable)

    def wrapped_function():
        logging.info('Executing job %s' % job['id'])
        logs = {job['id']:[]}
        logs[job['id']].append({'status': 'started', 'time': datetime.now()})
        try:
            logs[job['id']].append({'status': 'success', 'time': datetime.now(), 'misc': exec(marshal.loads(bytes), imports, locals)})
        except Exception as e:
            logs[job['id']].append({'status': 'error', 'time': datetime.now(), 'misc':str(e)})
        finally:
            logs[job['id']].append({'status': 'finished', 'time': datetime.now()})
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
    
        self.last_update_seen = self.db.execute('SELECT max(rowid) FROM job_audit_log').fetchone()[0]
        if self.last_update_seen is None:
            self.last_update_seen = 0
        for row in self.db['job'].rows:
            self.init_execution_ctx(row)
            
        
        logging.info(f'Initialized with {len(self.jobs.keys())} jobs, last change seen: {self.last_update_seen}')
        
            
    def init_execution_ctx(self, job):
        compiled = make_wrapped_function(job, cb = self.log_and_schedule_job)
        if compiled is not None:
            self.jobs[job['id']] = {'fn': compiled, 'next': croniter(job['cron']).get_next}
            self.schedule_job(job['id'])
        

    def update_active_jobs(self, job_id, action):
        if action == 'INSERT':
            logging.info(f'Adding job: {job_id}')
            self.init_execution_ctx(self.db['job'].get(job_id))
        elif action == 'UPDATE':
            logging.info(f'Update job: {job_id}')
            self.init_execution_ctx(self.db['job'].get(job_id))
        elif action == 'DELETE':
            logging.info(f'Deleting job: {job_id}')
            del self.jobs[job_id]

    def log_and_schedule_job(self, logs = {}):
        for job_id, logs in logs.items():
            for l in logs:
                l['job_id'] = job_id 
            self.db['job_log'].insert_all(logs)
            self.schedule_job(job_id)
        return True

    def schedule_job(self, job_id):
        try:
            j = self.jobs[job_id]
            if 'next' in j:
                next = j['next'](ret_type=float) 
                if next > time.time():
                    return self.enterabs(time = next, action = j['fn'], priority=1)
                self.enter(action = self.jobs[job_id]['fn'], priority=1, delay=0)
        
        except Exception as e:
            logging.ERROR(f'Error in job: {job_id} : {e}')
            return False

    def update(self):
        last_update = self.last_update_seen
        for job in self.db['job_audit_log'].rows_where(f"rowid > '{self.last_update_seen}'", select='rowid, job_id, status'):
            self.update_active_jobs(job['job_id'], job['status'])
            last_update = job['id']
        self.last_update_seen = last_update

    def loop(self):
        while True:
            logging.info(f"Active Running job count: {len(self.queue)}")
            self.current_queue = self.queue
            self.run(blocking=False)
            self.update()
            time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(filename='./simple_sched.log',format='%(asctime)s %(levelname)-8s %(message)s', encoding='utf-8', level=logging.DEBUG)
    s = schedule_ctx()
    s.loop()
