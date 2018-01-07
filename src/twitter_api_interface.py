from rauth import OAuth1Service
import requests
import time
from urllib.parse import quote
from base64 import b64encode

def generateUserSession(creds, gzip=True, verbose=False) :
    """
    Generate a user-specific OAuth session for Twitter 
    """
    # Load your API keys
    if verbose : print('\nSecrets loaded')
    
    # Create rauth service
    twitter = OAuth1Service(
        consumer_key=creds['consumer_key'],
        consumer_secret=creds['consumer_secret'],
        name='twitter',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize',
        request_token_url='https://api.twitter.com/oauth/request_token',
        base_url='https://api.twitter.com/1.1/')
    if verbose : print('oAuth service started')
    
    # Get a session
    session = twitter.get_session(
        (creds['token_key'], creds['token_secret']))
    if verbose : print('oAuth session created')
    
    if gzip :
        session.headers.update({'Accept-Encoding' : 'gzip'})
    
    return session

def oauth2(creds) :
    # Twitter Oauth2 token-dispensing endpoint
    ENDPOINT = 'https://api.twitter.com/oauth2/token'
    
    # Generate Bearer Token credentials
    secrets = creds
    con_key = quote(secrets['consumer_key'])
    con_sec = quote(secrets['consumer_secret'])
    bt_creds = b64encode((con_key + ':' + con_sec).encode('utf-8'))
    bt_creds = bt_creds[0 :len(bt_creds) - 2].decode('utf-8')
    
    # Prep headers
    headers = {
        'Authorization' : 'Basic ' + bt_creds,
        'Host' : 'api.twitter.com',
        'User-Agent' : creds['application_name']
    }
    
    # Prep request
    params = {
        'grant_type' : 'client_credentials'
    }
    
    # Moment of truth
    resp = requests.post(ENDPOINT, data=params, headers=headers)
    return creds['application_name'], resp.json()['access_token']

def generateAppSession(creds, gzip=True, verbose=False) :
    """
    Generate an application-only session for Twitter 
    """
    # Load bearer token
    user_agent_string = creds['application_name']
    bearer_token = creds['bearer_token']
    
    # Generate session
    sess = requests.Session()
    
    # Fill out headers with auth token
    headers = {
        'Host' : 'api.twitter.com',
        'User-Agent' : user_agent_string,
        'Authorization' : 'Bearer ' + bearer_token
    }
    
    if gzip :
        headers['Accept-Encoding'] = 'gzip'
    
    # Update headers in session object
    sess.headers.update(headers)
    return sess

def connect(creds, app_auth=True, verbose=False) :
    """
    Connect to Twitter API
    :return: rauth session object for Twitter Search API
    """
    if app_auth :
        session = generateAppSession(creds, verbose=verbose)
    else :
        session = generateUserSession(creds, verbose=verbose)
    
    return session

def disconnect(session=None) :
    """
    Disconnect the Twitter session specified.
    """
    session.close()
        
def searchQuery(session, query, bounds, lang=None, verbose=True):
    """
    Make a query to the Twitter Search API and return the response
    """
    
    # Fill out query parameters
    params = {'q': query,
              'result_type' : 'recent',
              'count': '100'}
    
    # Apply language filter
    
    
    # Apply bounds
    since_id = bounds[0]; max_id = bounds[1]
    if max_id is not None :
        params['max_id'] = max_id
    if since_id is not None:
        params['since_id'] = since_id

    # Send the request and return results
    if verbose :
        print('\nSending search request...')
        print('If this takes a long time, be sure to check availability:')
        print('https://dev.twitter.com/overview/status\n')
    TWITTER_URL = 'https://api.twitter.com/1.1/search/tweets.json'

    # Send the request to Twitter and give the result
    return session.get(TWITTER_URL, params=params)

def searchQuerySafe(session, creds, query, bounds, app_auth, retry_on_rate_limit=False, verbose=True) :
    """
    Wrapper for sendQuery to handle exceptions and rate-limiting by Twitter API.
    """
    # Watch network errors and wait if timed out
    failhard = False
    ctr = 0
    WAIT_INTERVAL = 60
    MAX_TRIES = 900 / WAIT_INTERVAL
    while not failhard :
    
        # Make requests until one succeeds or we surrender
        try :
        
            # Query until we get valid JSON
            brokentweetctr = 0
            while True :
                reply = searchQuery(session, query, bounds, verbose=False)
                
                try :
                    data = reply.json()
                except ValueError :
                    if brokentweetctr < 3 :
                        brokentweetctr += 1
                        continue
                    else :
                        print('WARNING: Mangled tweet in desired range.')
                        raise
                break
                
            # If we're being rate limited
            if reply.status_code == 429 or 'statuses' not in data :
                if verbose :
                    print('HTTP Code : ' + str(reply.status_code) + ' - Rate limited!')
                ctr += 1
            
                # If we haven't waited a full time period, keep waiting
                if ctr < MAX_TRIES and retry_on_rate_limit :
                    if verbose : print('Attempt ' + str(ctr + 1) + ' in ' + str(WAIT_INTERVAL) + ' seconds...\n')
                    time.sleep(WAIT_INTERVAL)
                else :
                    failhard = True
        
            # Not rate limited; not handling other HTTP errors yet
            else :
                return reply, False
    
        except ConnectionError :
            if verbose : print('Connection terminated: Reconnecting...')
            disconnect(session)
            connect(creds, app_auth)
            if verbose : print('Reconnection successful.')
            continue
    
        # Unmitigated network or data error
        except Exception :
            if verbose : print('Exception in search!')
            raise

    # Waited a full time period; give up.
    if verbose and retry_on_rate_limit : print('Failed hard! Not getting new rate-limiting periods!')
    return None, failhard
