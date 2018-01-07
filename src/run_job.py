import rest_collector
from arx_mgr import load_arx
from twitter_api_interface import oauth2
import json

from enum import Enum
class Job(Enum) :
    """
    Enumeration defining possible states for a job.
    """
    ISSUED = 2      # The job was started, but hasn't done anything yet
    RUNNING = 1     # The job has begun doing work
    STOPPED = 0     # The job was told to stop and is no longer doing work
    STOPPING = 6    # The job has been told to stop but is still working
    ERROR = 4       # The job encountered a problem that forced it to stop
    REISSUED = 3    # The job already exists, but was told to start
    NOT_ACTIVE = 7  # The job is not on the job list
    COMPLETED = 8   # The job completed its work and is no longer active



def load_secrets(job):
    """
    Load credentials from file and label them in the job's creds dictionary
    :param job: The job whose credfile you're loading
    """
    
    with open('creds/'+job['credfile']) as fin:
        credlines = []
        for line in fin:
            line = line.strip()
            if line:
                credlines.append(line)
                
        job['creds'] = {
            'application_name':credlines[0],
            'consumer_key':credlines[1],
            'consumer_secret':credlines[2],
            'token_key':credlines[3],
            'token_secret':credlines[4]
        }
        
        if job['app_auth']:
            job['creds']['bearer_token'] = oauth2(job['creds'])[1]
            
def collection_job(job_id, dispatcher,verbose=False):
    """
    Load the collection parameters from jobs/<job_id>.json and begin collection.
    A job communicates with its dispatcher about its state via the dispatcher
    functions getJobStatus() and setJobStatus(Job.STATUS)
    :param job_id: Filename of the job in the 'jobs/' folder
    :param dispatcher: The Dispatcher object running the producer-consumer pool
    :param verbose: Print an annoying and obstructive number of debug messages to terminal
    :return: Error code when collection terminates: 0 for success, 1 for error
    """
    
    job = None
    
    """
    Job dictionary with the following entries:
    
    MANDATORY ENTRIES:
    -------------------------------------------------------------------------
    These entries must be included properly for collection to run. 
    
    keywords    List containing strings of case-insensitive search terms to be OR'd
                together. Words within a string are combined with AND
                
    path        The directory to store data collected. If it does not exist,
                Ornitholog will attempt to create it. If you wish to change
                this directory after collection has begun, you must move
                all files AND edit the JSON job file to reflect the new path.
                
    credfile    The file in creds/ containing the credentials you wish to use
                for this collection job. This should be a regular text file with
                the keys stored one-per-line, ordered as:
                <Application Name>
                <Consumer Key>
                <Consumer Secret>
                <Access Token>
                <Access Secret>
                If you do not properly include the Application Name, app_auth
                will fail to authenticate. For app_auth to succeed, the Access
                Token and Access Secret must belong to the application's owner.
                
    OPTIONAL ENTRIES:
    -------------------------------------------------------------------------
    Further options for adjusting collection parameters. These will default to boring
    behavior if you do not specify them yourself.
    
    langs       List of language-code strings to search, per Twitter API
                If none are included, ALL languages will be considered!
                (default: ['en'])
                
    max_taj_size    The maximum size (MB) a single file of tweets can grow to before
                    it is segmented.
                    (default: 400)
    
    app_auth    Use application-only authentication to collect data. This nearly
                triples the rate-limit for collection, but can only be used
                concurrently once per-application, whereas regular auth can be
                used once per-user per-app concurrently.
                
    streaming_api   Use the streaming API to collect data. This has the potential
                    to collect a great amount of data (1% volume of all Twitter),
                    but only one stream can be active at once PER USER ACCOUNT. If
                    you wish to collect multiple streams at once, you must provide
                    each with a different set of user credentials.
    
    ENTRIES CREATED AT RUNTIME:
    -------------------------------------------------------------------------
    Please do not fill these entries, or leave them null.
    
    arx         The corresponding archive index dict loaded at runtime the ARX on disk
    
    status      The job's current state of execution
    
    creds       The credentials as a dict, once loaded from the credfile
    
    session     The API session this job is attached to
    """
    
    # Activity loop
    while True:
    
        # Get the state of your job from the dispatcher
        job_state = dispatcher.getJobStatus(job_id)
        
        #################
        # State machine #
        #################
        
        # Continue collecting data
        if job_state == Job.RUNNING:
            
            # Do your regular collecting and storing thing
            try :
                rest_collector.collect(job,verbose=verbose)
            except:
                dispatcher.setJobStatus(job_id,Job.ERROR)
                return 1
            
        # Initialize and begin collection or update collection parameters
        elif job_state == Job.ISSUED or job_state == Job.REISSUED:
            
            # Load your parameters from the job file
            with open('jobs/'+job_id+'.json') as jobfile:
                job = json.load(jobfile)
            job['name'] = job_id
            
            # Load your archive index file
            job['chunks_collected'] = 0
            load_arx(job)
            
            # Unpack your auth keys from file
            load_secrets(job)
            
            # You have successfully started
            dispatcher.setJobStatus(job_id,Job.RUNNING)
        
        # Stop collection
        elif job_state == Job.STOPPING:
            
            # You have successfully stopped
            dispatcher.setJobStatus(job_id,Job.STOPPED)
            print(job_id,'has stopped.')
            return 0
        
        elif job_state == Job.COMPLETED:
            
            # You finished your work. Usually not applicable.
            dispatcher.setJobStatus(job_id,Job.COMPLETED)
            return 0
        