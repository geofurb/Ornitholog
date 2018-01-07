import json
import os
from uuid import uuid4
import tweet_parser

def enildaer(filename, buf_size=8388608):
    """
    A generator that returns the lines of a file in reverse order
    """
    fh = filename
    segment = None
    offset = 0
    file_size = fh.seek(0, os.SEEK_END)
    total_size = remaining_size = fh.tell()
    while remaining_size > 0:
        offset = min(total_size, offset + buf_size)
        fh.seek(file_size - offset)
        buffer = fh.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines = buffer.split('\n')
        # the first line of the buffer is probably not a complete line so
        # we'll save it and append it to the last line of the next buffer
        # we read
        if segment is not None:
            # if the previous chunk starts right from the beginning of line
            # do not concact the segment to the last line of new chunk
            # instead, yield the segment first 
            if buffer[-1] is not '\n':
                lines[-1] += segment
            else:
                yield segment
        segment = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]
    # Don't yield None if the file was empty
    if segment is not None:
        yield segment

def load_arx(job):
    """
    Load an archive index (ARX) json file.
    :param job: Path to the job file for the collection you wish to store in this archive
    :return: Python dictionary of the ARX
    """
    # Parse job from file
    arx_path = job['path'] + '/index.arx'
    # If ARX exists, load the JSON into a python dict
    try :
        with open(arx_path) as fin:
            arx = json.load(fin)
            job['arx'] = arx
            return arx
    # If ARX does not exist, create it and return the dict
    except FileNotFoundError:
        # First create the directory if necessary
        try:
            os.makedirs(job['path'], exist_ok=True)
        except (FileNotFoundError, FileExistsError):
            pass
        # Create the base ARX file
        with open(arx_path,'w+') as fout:
            # Create a blank archive file
            
            # Prepend a + to make a key required
            # All other keys are optional
            andkeys = []; orkeys = []
            for keyword in job['keywords']:
                if keyword[0] == '+':
                    andkeys.append(keyword[1:])
                else :
                    orkeys.append('\"'+keyword+'\"')
            query = ' '.join([
                ' '.join(andkeys),
                ' OR '.join(orkeys)
            ])
            
            # Initialize our archive index with this query
            arx = {
                'query' : query,
                'filters' : None,
                'unfinished' : None,
                'finished' : []
            }
            job['arx'] = arx
            json.dump(arx, fout, indent=4, sort_keys=True)
            return arx

def write_arx(job):
    """
    Write a new archive index json file
    :param job: The job whose archive index you want to update
    """
    arx = job['arx']
    arx_path = job['path'] + '/index.arx'
    with open(arx_path,'w+') as fout:
        json.dump(arx, fout, indent=4, sort_keys=True)


def findTAJbounds(taj_file, finished_file=True):
    """
    Scan the TAJ file from either end to determine when it begins and ends. This file could be hundreds of gigabytes
    long depending on the collection parameters, so we'll scan from the beginning and the end, rather than reading
    straight through the entire thing.
    :param taj_file: Path to the TAJ file we wish to parameterize
    :param finished_file: True if the first line of the file contains the oldest tweet
    :return: min_id, max_id, min_date, max_date
    """
    old_to_new = finished_file
    min_date = None; max_date = None
    min_id = None; max_id = None
    
    # Feed forward
    with open(taj_file) as taj:
        for line in taj:
            tweet = json.loads(line)
            
            # Get date and ID bounds from the top of the file
            if old_to_new:
                if min_date is None or min_id is None:
                    if min_date is None:
                        min_date = tweet_parser.getDate(tweet)
                    if min_id is None:
                        min_id = tweet_parser.getTweetID(tweet)
                else:
                    break
            else:
                if max_date is None or max_id is None:
                    if max_date is None:
                        max_date = tweet_parser.getDate(tweet)
                    if max_id is None:
                        max_id = tweet_parser.getTweetID(tweet)
                else:
                    break
                    
    # Feed in reverse
    with open(taj_file) as taj:
        for line in enildaer(taj):
            tweet = json.loads(line)
            
            # Get date and ID bounds from the bottom of the file
            if not old_to_new:
                if min_date is None or min_id is None:
                    if min_date is None:
                        min_date = tweet_parser.getDate(tweet)
                    if min_id is None:
                        min_id = tweet_parser.getTweetID(tweet)
                else:
                    break
            else:
                if max_date is None or max_id is None:
                    if max_date is None:
                        max_date = tweet_parser.getDate(tweet)
                    if max_id is None:
                        max_id = tweet_parser.getTweetID(tweet)
                else:
                    break
    # Return bounds
    return min_id, max_id, min_date, max_date

def append_finished_file(job):
    """
    Create a new "finished" file at the end of the ARX's list of finished TAJ (tweet archive json) files
    :param job: The job that needs a new finished file
    :return: The index entry for the file you just created
    """
    arx = job['arx']
    fin_file = 'tweets-' + str(uuid4()) + '.taj'    # Generate a unique filename
    # Collision is theoretically possible; may the odds be ever in your favor.
    
    # Inspect the previous finished files to see where this one fits in
    with open(job['path']+'/'+fin_file,'w+'): pass
    if len(arx['finished']) > 0:
        prev_last = arx['finished'][-1]
        prior_latest_idx = prev_last[2]
        prior_latest_tstmp = prev_last[4]
    else:
        prior_latest_idx = None
        prior_latest_tstmp = None
        
    # Append the new finished file to the list
    arx['finished'].append([fin_file, prior_latest_idx, None, prior_latest_tstmp, None, 0])
    return arx['finished'][-1]
        
def finalize_taj(job):
    """
    Create a new "finished" TAJ out of your "unfinished" TAJ
    :param job: Archive with the TAJ you want to finalize
    """
    arx = job['arx']; path = job['path'] + '/'
    if arx['unfinished'] is None: return
    
    # If there are no finished files, create one
    if len(arx['finished']) == 0:
        append_finished_file(job)
    # Otherwise create a new finished file if the old one is full
    elif os.path.getsize(path+'/'+arx['finished'][-1][0]) > (job['max_taj_size']*1024*1024):
        append_finished_file(job)
        
    
    # Copy old-to-new tweets from unfinished file to new-to-old ordering for finished file.
    copybuffer = []
    with open(path+arx['unfinished'][0]) as fin, open(path+arx['finished'][-1][0],'a+') as fout:
        for idx, line in enumerate(enildaer(fin)) :
            copybuffer.append(line)
            if idx % 1000 == 999 :
                copybuffer.append('')   # For trailing \n
                fout.write('\n'.join(copybuffer))
                copybuffer = []
        copybuffer.append('')   # For trailing \n
        fout.write('\n'.join(copybuffer))
        
    # Add metadata from Tweets.
    with open(path + arx['unfinished'][0]) as funfin, open(path + arx['finished'][-1][0]) as ffin:
        
        # Iterate through the finished file to get the last tweet ID
        last_id = None  ## TODO: Debug cases where this might not get set.
        last_time = None
        for line in ffin:
            line = line.strip()
            if line:
                try :
                    tweet = json.loads(line)
                    if last_id is None: last_id = tweet_parser.getTweetID(tweet)
                    if last_time is None: last_time = tweet_parser.getDate(tweet)
                except ValueError:
                    pass
            if last_id is not None and last_time is not None: break
        arx['finished'][-1][2] = last_id
        arx['finished'][-1][4] = last_time
        
        # Iterate through the unfinished file to get the first tweet ID, if necessary
        if len(arx['finished']) == 1:
            first_id = None
            first_time = None
            for line in funfin:
                line = line.strip()
                if line:
                    try:
                        tweet = json.loads(line)
                        if first_id is None: first_id = tweet_parser.getTweetID(tweet)
                        if first_time is None: first_time = tweet_parser.getDate(tweet)
                    except ValueError:
                        continue
                if first_id is not None and first_time is not None: break
            arx['finished'][-1][1] = first_id-1
            arx['finished'][-1][3] = first_time
        
    arx['finished'][-1][5] = arx['unfinished'][5]   # The number of tweets didn't change

def append_current_tweets(job, tweets):
    """
    Append the tweets to the end of the latest TAJ in the ARX
    :param job: The collection job these tweets belong to
    :param tweets: List of stringified tweet JSON objects sorted first-to-last by ID. Must not contain line breaks!
    """
    
    if len(tweets) == 0 : raise ValueError
    
    arx = job['arx']; path = job['path'] + '/'
    
    # Finalize the old unfinished file if it is full
    if 'unfinished' in arx and arx['unfinished'] is not None:
        if os.path.getsize(path+arx['unfinished'][0]) > (job['max_taj_size']*1024*1024):
            finalize_taj(job)
            
            # Create a new unfinished file
            if len(arx['finished']) > 0 :
                prev_last = arx['finished'][-1]
                prior_latest_idx = prev_last[2]
                prior_latest_tstmp = prev_last[4]
            else :
                prior_latest_idx = None
                prior_latest_tstmp = None
            unfin_file = 'new-tweets-' + str(uuid4()) + '.taj'
            with open(path + unfin_file, 'w+'): pass
            arx['unfinished'] = [unfin_file, prior_latest_idx, None, prior_latest_tstmp, None, 0]
    else :
        # Create a new unfinished file
        if len(arx['finished']) > 0 :
            prev_last = arx['finished'][-1]
            prior_latest_idx = prev_last[2]
            prior_latest_tstmp = prev_last[4]
        else :
            prior_latest_idx = None
            prior_latest_tstmp = None
        unfin_file = 'new-tweets-' + str(uuid4()) + '.taj'
        with open(path + unfin_file, 'w+') :
            pass
        arx['unfinished'] = [unfin_file, prior_latest_idx, None, prior_latest_tstmp, None, 0]
    
    # Append our tweets to the unfinished file
    num_tweets = len(tweets)
    with open(path+arx['unfinished'][0],'a+') as fout:
        tweets.append('') # For trailing \n
        fout.write('\n'.join(tweets))
    arx['unfinished'][5] += num_tweets
    
    # Add metadata from Tweets.
    with open(path + arx['unfinished'][0]) as funfin:
        
        # Iterate through the unfinished file to get the last tweet ID
        last_id = None  ## TODO: Debug cases where this might not get set.
        last_time = None
        for line in enildaer(funfin):
            line = line.strip()
            if line:
                try:
                    tweet = json.loads(line)
                    last_id = tweet_parser.getTweetID(tweet)
                    last_time = tweet_parser.getDate(tweet)
                except ValueError:
                    continue
            if last_id is not None and last_time is not None: break
        arx['unfinished'][2] = last_id
        arx['unfinished'][4] = last_time
    
    # Iterate through the unfinished file to get the first tweet ID if it hasn't been set yet
    with open(path + arx['unfinished'][0]) as funfin :
        if arx['unfinished'][1] is None:
            first_id = None
            first_time = None
            for line in funfin:
                line = line.strip()
                if line:
                    try:
                        tweet = json.loads(line)
                        first_id = tweet_parser.getTweetID(tweet)
                        first_time = tweet_parser.getDate(tweet)
                    except ValueError:
                        continue
                if first_id is not None and first_time is not None: break
            arx['unfinished'][1] = first_id
            arx['unfinished'][3] = first_time
    
    # Commit our updated archive index to disk
    write_arx(job)

def get_append_bounds(job):
    """
    Return the bounds list for tweets to append to our archive
    :param job: The job defining this collection
    :return: since_id, max_id 
    """
    arx = job['arx']
    if 'unfinished' in arx and arx['unfinished'] is not None:
        since_id = job['arx']['unfinished'][2]
        return since_id, None
    elif 'finished' in arx and arx['finished'] is not None and len(arx['finished']) > 0:
        since_id = job['arx']['finished'][-1][2]
        return since_id, None
    else:
        return None, None

def get_prepend_bounds(job):
    """
    Return the bounds list for tweets to prepend to our archive
    :param job: The job defining this collection
    :return: since_id, max_id 
    """
    arx = job['arx']
    if 'finished' in arx and arx['finished'] is not None and len(arx['finished']) > 0 :
        max_id = job['arx']['finished'][0][1]
        return None, max_id
    elif 'unfinished' in arx and arx['unfinished'] is not None :
        max_id = job['arx']['unfinished'][1]
        return None, max_id
    else :
        return None, None
