import time, threading
import traceback
from run_job import collection_job, Job

def dummy_load(job_id, executor, name,wait_time=10) :
    print('Beginning dummy load',name)
    for idx in range(wait_time) :
        print(name,'ticks',idx+1)
        time.sleep(1.0)
        if executor.getJobStatus(job_id) == Job.STOPPING :
            executor.setJobStatus(job_id,Job.STOPPED)
            return Job.STOPPED
    print(name,'completed.')
    executor.setJobStatus(job_id,Job.COMPLETED)
    return Job.COMPLETED

    
from queue import Queue, Empty
import concurrent.futures as con



class Dispatcher(threading.Thread) :
    """
    Accept new work, dispatch to your jobs for completion. Manage results
    and optimize flow.
    """
    
    def __init__(self,**kwargs) :
        
        # Superclass constructor
        threading.Thread.__init__(self,daemon=True,**kwargs)
        self.log_file = 'logs/dispatcher_errors.log'
        
        # Initialize our process pool
        self.ex = con.ThreadPoolExecutor()
        
        # Futures dictionary to track jobs
        self.lock = threading.Lock()
        self.job_status = {}  # ALWAYS LOCK WHILE USING THIS DICT
        
        # Init query work queue so we can process queries smoothly
        self.job_queue = Queue()
        
        # Initialize workpool to watch ThreadPool futures
        # Future should return an indication about how the job finished
        self.workpool = []
    
    def log_error(self, exc, query=None) :
        with open(self.log_file, 'a+') as fout :
            fout.write('ERROR REPORT:\n')
            if query is not None :
                fout.write('QUERY: ' + str(query) + '\n')
            fout.write(time.strftime("%m-%d-%Y %H:%M:%S (UTC %z)"))
            fout.write('\n-----------\n')
            traceback.print_stack(file=fout)
            fout.write('\n-----------\n')
            traceback.print_exc(file=fout)
            fout.write('\n-----------\n\n\n\n\n')
    
    def run(self) :
        while True :
            
            # Dispatch everything in your queue
            while True :
                
                # Take a job from the queue
                try :
                    job_id = self.job_queue.get(block=True, timeout=0.1)
                except Empty :
                    break  # Nothing left in the queue
                
                # Dispatch the job to a thread
                job = self.ex.submit(collection_job, job_id, self)
                
                # Pool the future from that job
                self.workpool.append(job)
            
            # Resolve any futures whose computation has completed
            self.checkForCompletedWork()
            # Then check for more work all over again!
    
    def pushRequest(self, job) :
        """
        Push a new job to this Dispatcher
        :param job: Name of the JSON file in 'jobs/' with the job parameters 
        :return: 
        """
        
        # Add your job to the work queue and job_status list.
        if job not in self.job_status :
            self.setJobStatus(job, Job.ISSUED)
            self.job_queue.put(job)
        else :
            if self.job_status[job] in [Job.ERROR, Job.COMPLETED, Job.STOPPED, Job.NOT_ACTIVE]:
                self.setJobStatus(job, Job.REISSUED)
                self.job_queue.put(job)
            else:
                self.setJobStatus(job, Job.REISSUED)
    
    def stopJob(self, job_id) :
        """
        Signal a running job that it needs to stop.
        :param job_id: 
        :return: Returns True if the job was active and not in the process of stopping 
        """
        if self.getJobStatus(job_id) in [Job.RUNNING, Job.ISSUED, Job.REISSUED] :
            self.setJobStatus(job_id,Job.STOPPING)
            return True
        else :
            return False
    
    def getJobs(self):
        """
        Get a list of all jobs that have been added, whether active or not.
        :return: List of job names
        """
        return self.job_status.keys()
    
    def getActiveJobs(self):
        """
        Get a list of jobs whose threads are doing something interesting.
        :return: List of job names
        """
        keys = self.job_status.keys()
        active = []
        for key in keys:
            if self.job_status[key] not in [Job.ERROR, Job.COMPLETED, Job.STOPPED, Job.NOT_ACTIVE]:
                active.append(key)
        return active
    
    def getJobStatus(self, job_id):
        """
        Get the current status of a given job
        :param job_id: The job whose status you wish to check
        :return: The job's current status, as a Job enum entry
        """
        if job_id in self.job_status:
            return self.job_status[job_id]
        else:
            return Job.NOT_ACTIVE
    
    def setJobStatus(self, job_id, status):
        """
        Nice safe function for updating the job_status table
        :param job_id: The job whose status you wish to update
        :param status: The job's new status, from the Job enum
        :return: The job's previous status
        """
        if job_id in self.job_status :
            prev = self.job_status[job_id]
            
            self.lock.acquire()
            self.job_status[job_id] = status
            self.lock.release()
            
            return prev
        elif status == Job.ISSUED:
            self.lock.acquire()
            self.job_status[job_id] = Job.ISSUED
            self.lock.release()
            
            return Job.NOT_ACTIVE
        else:
            return Job.NOT_ACTIVE
    
    def checkForCompletedWork(self) :
        """
        Check if any of your workpool jobs are done, resolve appropriate futures
        """
        completed = []
        this_job = None
        for job in self.workpool :
            try :
                if job.done() :
                    res = job.result()
                    self.cleanupJob(res)
                    completed.append(job)
                    this_job = None
            except Exception as exc:
                print('Error checking on job result!')
                self.log_error(exc, this_job)
                this_job = None
                completed.append(job)
        
        # Clean up
        for job in completed :
            self.workpool.remove(job)
    
    def cleanupJob(self, job_id) :
        """
        Remove the job from our list when it is deleted.
        :param job_id: 
        """
        self.lock.acquire()
        if job_id in self.job_status :
            end_status = self.job_status.pop(job_id)
            print(end_status)
        self.lock.release()
    

