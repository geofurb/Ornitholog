import traceback
import requests
import twitter_api_interface
import tweet_parser
import arx_mgr
import time
import json



class RatelimitError(requests.exceptions.HTTPError) :
    """Twitter wants us to chill out and wait a little while before trying to reconnect."""


# Error handling for our REST API connection
def reset_errors(state) :
    state['tcp_err_ctr'] = 0
    state['http_err_ctr'] = 0
    state['http_eyc_ctr'] = 0
    state['other_errors'] = 0

def signal_TCP_err(state) :
    state['tcp_err_ctr'] += 1
    err_count = min([state['tcp_err_ctr'], 64])
    with open(state['error_log'], 'a+') as error_log :
        error_log.write('REST TIME: ' + str((0.25 * err_count)) + ' seconds for TCP.\n')
    time.sleep(0.25 * err_count)

def signal_HTTP_err(state) :
    state['http_err_ctr'] += 1
    err_count = min([state['http_err_ctr'], 7])
    with open(state['error_log'], 'a+') as error_log :
        error_log.write('REST TIME: ' + str((5.0 * 2 ** (err_count - 1))) + ' seconds for HTTP.\n')
    time.sleep(5.0 * 2 ** (err_count - 1))

def signal_ratelimit_err(state) :
    state['http_eyc_ctr'] += 1
    with open(state['error_log'], 'a+') as error_log :
        error_log.write('REST TIME: ' + str((60.0 * 2 ** (state['http_eyc_ctr'] - 1))) + ' seconds for ratelimit.\n')
    time.sleep(60.0 * 2 ** (state['http_eyc_ctr'] - 1))

def signal_other_error(state) :
    state['other_errors'] += 1
    err_count = min([state['tcp_err_ctr'], 10])
    with open(state['error_logs'], 'a+') as error_log :
        error_log.write('REST TIME: ' + str((5.0 * err_count)) + ' seconds for unexpected error.\n')
    time.sleep((5.0 * err_count))

def log_error(state, exc) :
    with open(state['error_log'], 'a+') as error_log :
        error_log.write('EXCEPTION: ' + str(exc) + '\n')
        error_log.write(time.strftime("%m-%d-%Y %H:%M:%S (UTC %z)"))
        error_log.write('\n-----------\n')
        traceback.print_exc(file=error_log)
        error_log.write('\n\n\n')

# Open a REST API connection, get some data
def collect(job,sample_evenness=float('inf'),verbose=False) :
    
    # Start with no errors
    state = {
        'tcp_err_ctr' : 0,
        'http_err_ctr' : 0,
        'http_eyc_err' : 0,
        'other_errors' : 0,
        'error_log' : 'logs/topic_tracking_errors.log'
    }
    connection_has_succeeded = False
    
    ############################
    # Exception Handling Block #
    ############################
    try :
        
        # Connect & collect
        if verbose: print('Initializing collection...')
        
        #########################
        # REST Collection Block #
        #########################
        
        ctr = 0
        while True :
            if verbose: print(job['name'],'collecting chunk',str(ctr))
            collectTweetBatch(job, sample_evenness,verbose=verbose)
            job['chunks_collected'] += 1
            reset_errors(state)
            break
            
        # Catch & wait on HTTP/network errors
    # We've been trying to collect data from Twitter's servers too quickly
    except RatelimitError :
        signal_ratelimit_err(state)
        return
    # Trouble communicating with the API
    except requests.exceptions.HTTPError as exc :  # HTTP Errors
        log_error(state, exc)
        if connection_has_succeeded :  # Speed bump errors
            signal_HTTP_err(state)  # Wait before continuing
            return
        else :
            raise
    # Trouble with our connection to Twitter's servers
    except ConnectionError :
        signal_TCP_err(state)
        return
    # Unexpected error
    except Exception as exc :  # Catch & log unexpected errors
        if verbose: print('Unhandled exception in REST API connection block!')
        log_error(state, exc)
        if connection_has_succeeded :
            signal_other_error(state)
            return
        else :
            raise

def collectTweetBatch(job, sample_evenness=450.0, verbose=False):
    """
    Collect an even sampling of tweets, up to all available Tweets in your rate-limiting period.
    :param job: The job defining your collection parameters
    :param sample_evenness: Increase for shorter collection intervals on each topic. (Warning: If set too high, this
    may cause you to undershoot your rate-limit because there is a small time-overhead in changing query topics.)
    :param verbose: Print status messages to console
    :return:
    """
    
    # Initialization
    if sample_evenness < 1.0: sample_evenness = 1.0
    if job['app_auth']:
        MAX_QUERIES = 450.0
    else:
        MAX_QUERIES = 180.0
    if sample_evenness > MAX_QUERIES : sample_evenness = MAX_QUERIES
    time_alloc = 15.05 * 60.0 / sample_evenness
    NUM_QUERIES = round(MAX_QUERIES / sample_evenness)
    
    # Begin cycle
    qstart = time.time()
    if verbose:
        print('\n\n\nProcessing: ' + job['arx']['query'] + '\nStart time: ' + str(qstart))
    
    # Connect to API
    try:
        session = twitter_api_interface.connect(job['creds'],job['app_auth'])
        job['session'] = session
    except:
        if verbose: print('Error connecting to Twitter API!')
        raise
    
    # Initialize archive
    try:
        ARX = job['arx']
    except:
        if verbose: print('ARX not found in job!')
        raise
    
    # Collect new tweets and append them to our archive
    try:
        #DONE_READING, RATE_LIMITED = api.archiveSearch(ARX, MAX_QUERIES, wait_on_rate_limit=True,
        #                                               auto_exhaust=True, lang=lang)
        for idx in range(NUM_QUERIES) :
            reply, RATE_LIMITED = twitter_api_interface.searchQuerySafe(
                session,
                job['creds'],
                job['arx']['query'],
                arx_mgr.get_append_bounds(job),
                job['app_auth']
            )
            tweets = [json.dumps(tweet) for tweet in reversed(tweet_parser.getTweets(reply))]
            if len(tweets) == 0:
                if verbose: print('Received zero tweets! Received HTTP',reply)
            else:
                arx_mgr.append_current_tweets(job, tweets)
            if RATE_LIMITED :
                if verbose: print('Warning! Rate limit reached. Verify that you aren\'t collecting too quickly.')
                break
    except:
        if verbose: print('Exception during archive search!')
        raise
    
    # Disconnect API session
    try:
        twitter_api_interface.disconnect(session)
    except:
        if verbose: print('Error disconnecting from Twitter API!')
        job['session'] = None
    
    # Preserve even query spacing; don't exceed rate-limit
    qfin = time.time()
    if verbose: print('End time: ' + str(qfin))
    t_interval = qfin - qstart
    if t_interval < time_alloc :
        if verbose: print('Finished early. Resting for ' + str(time_alloc - t_interval) + ' seconds.')
        time.sleep(time_alloc - t_interval)
        
