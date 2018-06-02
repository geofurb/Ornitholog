import json
import os, time
from pathlib import Path
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

def first_bound(taj_file):
    """
    Scan from the beginning of the TAJ file and return the first tweet index and date found. Note that these might not
    necessarily be from the same tweet if Twitter didn't properly include a field!
    :param taj_file: Path to the TAJ file we're interested in reading
    :return: Tuple of (long int) first_id, (str) first_date
    """
    first_id = None; first_date = None
    with open(taj_file) as taj :
        for line in taj :
            line = line.strip()
            if line:
                try:
                    tweet = json.loads(line)
                    # Get date and ID bounds from the top of the file
                    if first_date is None: first_date = tweet_parser.getDate(tweet)
                    if first_id is None: first_id = tweet_parser.getTweetID(tweet)
                except ValueError:
                    continue
                if first_date is not None and first_id is not None: break
    return first_id, first_date

def last_bound(taj_file) :
    """
    Scan from the end of the TAJ file and return the first tweet index and date found. Note that these might not
    necessarily be from the same tweet if Twitter didn't properly include a field!
    :param taj_file: Path to the TAJ file we're interested in reading
    :return: Tuple of (long int) last_id, (str) last_date
    """
    last_id = None; last_date = None
    with open(taj_file) as taj :
        for line in enildaer(taj) :
            line = line.strip()
            if line:
                # Get date and ID bounds from the top of the file
                try:
                    tweet = json.loads(line)
                    if last_date is None: last_date = tweet_parser.getDate(tweet)
                    if last_id is None : last_id = tweet_parser.getTweetID(tweet)
                except ValueError:
                    continue
                if last_id is not None and last_date is not None: break
    return last_id, last_date

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
    
        
    # Add metadata from Tweets    
    # Iterate through the finished file to get the last tweet ID
    last_id, last_time = first_bound(path + arx['finished'][-1][0])
    arx['finished'][-1][2] = last_id
    arx['finished'][-1][4] = last_time
    # Iterate through the unfinished file to get the first tweet ID, if necessary
    if len(arx['finished']) == 1:
        first_id, first_time = first_bound(path + arx['unfinished'][0])
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
    
    # Add metadata from Tweets
    # Iterate through the unfinished file to get the last tweet ID
    last_id, last_time = last_bound(path + arx['unfinished'][0])
    arx['unfinished'][2] = last_id
    arx['unfinished'][4] = last_time
    # Iterate through the unfinished file to get the first tweet ID if it hasn't been set yet
    if arx['unfinished'][1] is None:
        first_id, first_time = first_bound(path + arx['unfinished'][0])
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

def iter_tweetfile(tweetfile, min_id=None, max_id=None, min_date=None, max_date=None, reverse=False):
    """
    
    :param tweetfile: File containing JSON tweets, one per line 
    :param min_id: Skip tweets with IDs lower than this
    :param max_id: Skip tweets with IDs higher than this
    :param min_date: Skip tweets before this POSIX timestamp
    :param max_date: Skip tweets after this POSIX timestamp
    :param reverse: Read the file backwards
    :return: Generator over tweet objects in the file
    """
    if min_id is None: min_id = -1
    if max_id is None: max_id = float('inf')
    if min_date is None: min_date = -1
    if max_date is None: max_date = float('inf')
    
    with open(tweetfile) as fin:
        if reverse: fin = enildaer(fin)
        for line in fin:
            line = line.strip()
            if line:
                try:
                    tweet = json.loads(line)
                    if (min_id <= tweet_parser.getTweetID(tweet) <= max_id) and \
                            (min_date <= time.mktime(tweet_parser.getTimeStamp(tweet).timetuple()) <= max_date) :
                        yield tweet
                except:
                    continue
                
def check_bounds(arx_entry, min_id=None, max_id=None, min_date=None, max_date=None):
    """
    Return True if the ARX entry's bounds overlap the constraints or False if there can be no
    tweets within the given constraints
    :param arx_entry: ARX tuple (filename, min_id, max_id, min_date, max_date, num_tweets)
    :param min_id: Minimum tweet ID
    :param max_id: Maximum tweet ID
    :param min_date: Minimum date (POSIX timestamp)
    :param max_date: Maximum date (POSIX timestamp)
    :return: True if the tweet file intersects the period defined by the supplied constraints
    """
    fstart_date = time.mktime(tweet_parser.read_timestamp(arx_entry[3]).timetuple())
    fstop_date = time.mktime(tweet_parser.read_timestamp(arx_entry[4]).timetuple())
    if (min_id is not None and arx_entry[2] < min_id) or \
        (max_id is not None and arx_entry[1] > max_id) or \
        (min_date > fstop_date) or (max_date < fstart_date):
        return False
    return True
    
def scan_tweets(job, min_id=None, max_id=None, min_date=None, max_date=None, reverse=False):
    """
    Generator for iterating through a Tweet archive, one JSON object at a time.
    :param job: Dictionary with a path to an archive index OR a tweet file with one JSON object per line
    can also supply a file handle directly to the tweets.
    :param min_id: Minimum tweet ID; tweets will be skipped if their ID is less
    than this value.
    :param max_id: Maximum tweet ID; tweets will be skipped if their ID is more
    than this value. 
    :param min_date: Minimum date (POSIX timestamp)
    :param max_date: Maximum date (POSIX timestamp)
    :param reverse: Read tweets new-to-old instead of old-to-new
    :return: Iterator over tweet objects.
    """
    
    if min_date is None: min_date = -1
    if max_date is None: max_date = float('inf')
    
    # If arx is a dict, we're reading an archive with an index
    if type(job) is dict:
        arx = load_arx(job)
        # Read unfinished file first if going backwards
        if reverse:
            if arx['unfinished'] is not None:
                ufinfile = arx['unfinished']
                # Skip files outside ID/date bounds
                try :
                    unfin_out_of_bounds = not check_bounds(ufinfile, min_id, max_id, min_date, max_date)
                except :  # In case a bound was included improperly in the ARX, just check through the whole file
                    unfin_out_of_bounds = False
                if not unfin_out_of_bounds:
                    # Relative path correction
                    ufinfile[0] = Path(job['path']).joinpath(Path(ufinfile[0]))
                    # Iterate through tweets
                    for tweet in iter_tweetfile(arx['unfinished'][0], min_id, max_id, min_date, max_date, reverse):
                        yield tweet

        # Read finished files
        if arx['finished'] is not None and len(arx['finished']) > 0:
            
            # Allow the tweets to be read new-to-old or old-to-new
            if reverse:
                fin_files = reversed(arx['finished'])
            else:
                fin_files = arx['finished']
            
            for finfile in fin_files:
                
                # Check bounds to avoid iterating through files unnecessarily
                try :
                    if not check_bounds(finfile, min_id, max_id, min_date, max_date):
                        continue
                except: # In case a bound was included improperly in the ARX, just check through the whole file
                    pass
                
                # Relative path correction
                finfile[0] = Path(job['path']).joinpath(Path(finfile[0]))
                
                # Iterate through tweets in the file
                for tweet in iter_tweetfile(finfile[0], min_id, max_id, min_date, max_date, reverse):
                    yield tweet
                                
        # Read unfinished file last if going old-to-new
        if not reverse:
            if arx['unfinished'] is not None:
                ufinfile = arx['unfinished']
                
                # Skip files outside ID/date bounds
                try:
                    unfin_out_of_bounds = not check_bounds(ufinfile, min_id, max_id, min_date, max_date)
                except:  # In case a bound was included improperly in the ARX, just check through the whole file
                    unfin_out_of_bounds = False
                    
                if not unfin_out_of_bounds:
                    # Relative path correction
                    ufinfile[0] = Path(job['path']).joinpath(Path(ufinfile[0]))
                    # Iterate through tweets
                    for tweet in iter_tweetfile(arx['unfinished'][0], min_id, max_id, min_date, max_date, reverse):
                        yield tweet
                                    
    # Reading a single file, not an ARX
    else:
        for tweet in iter_tweetfile(job, min_id, max_id, min_date, max_date, reverse):
            yield tweet
    
