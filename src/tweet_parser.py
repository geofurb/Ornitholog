import pytz
import datetime as dt

def getTweetID(tweet) :
    """
    If properly included, return the tweet ID
    :param tweet: Python dict containing a Twitter tweet object
    :return: 
    """
    if 'id' in tweet and \
    tweet['id'] is not None :
        return tweet['id']
    else :
        return None

def getTweets(response) :
    """
    Get the tweets contained in an API response.
    :param response: Reply from Twitter API as a rauth response object
    :return: List of Tweet objects sorted new-to-old their tweet IDs
    """
    
    # Parse the json data
    if response is not None :
        data = response.json()
    else :
        return []
    
    # Find the tweets if they exist
    tweets = []
    if 'statuses' in data \
            and data['statuses'] is not None :
        tweets = data['statuses']
    
    tweets = sorted(tweets, key=getTweetID, reverse=True)
    
    return tweets

def getDate(tweet) :
    """
    If properly included, get the timestamp of the tweet from the 'created_at' field. This method parses a datetime
    object, then re-prints the time to ensure that only valid timestamp strings are accepted.
    :param tweet: Python dict containing a Twitter tweet object
    :return: Date string
    """
    
    if 'created_at' in tweet and tweet['created_at'] is not None :
        try :
            timestamp = dt.datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y').replace(
                tzinfo=pytz.timezone('UTC'))
            
            return timestamp.astimezone(pytz.timezone('UTC')).strftime('%a %b %d %H:%M:%S +0000 %Y')
        except ValueError :
            return None
    else :
        return None

def getScreenName(tweet) :
    """
    Get the user's screenname string if properly included
    :param tweet: Python dict containing a Twitter tweet object 
    :return: User's screenname as a string
    """
    if 'user' in tweet and \
            tweet['user'] is not None and \
            'screen_name' in tweet['user'] and \
            tweet['user']['screen_name'] is not None :
        return tweet['user']['screen_name']
    else :
        return None

def getTweetUserLocation(tweet) :
    """
    Get the user's self-supplied location from their user profile entity in this tweet
    :param tweet: Python dict containing a Twitter tweet object 
    :return: User's self-supplied location string
    """
    
    if 'user' in tweet and \
            tweet['user'] is not None and \
            'location' in tweet['user'] :
        return tweet['user']['location']
    else :
        return None

def getClockOffset(tweet) :
    """
    Get the UTC clock offset of this tweet
    :param tweet: Python dict containing a Twitter tweet object
    :return: UTC clock offset
    """
    # Check to see if time-zone info is available
    if 'user' in tweet and \
        tweet['user'] is not None and \
        'utc_offset' in tweet['user'] and \
        tweet['user']['utc_offset'] is not None :
        return tweet['user']['utc_offset']
    else :
        return None

def getTimezone(tweet) :
    """
    Get the user's timezone string from the tweet
    :param tweet: Python dict containing a Twitter tweet object
    :return: Timezone string from the tweet object
    """
    # Check to see if time-zone info is available
    if 'user' in tweet and \
        tweet['user'] is not None and \
        'time_zone' in tweet['user'] and \
        tweet['user']['time_zone'] is not None :
        return tweet['user']['time_zone']
    else :
        return None

def getTweetText(tweet) :
    """
    If properly included, return the tweet text
    :param tweet: Python dict containing a Twitter tweet object 
    :return: Text from the tweet body
    """
    if 'text' in tweet and \
    tweet['text'] is not None :
        return tweet['text']
    else :
        return None

def getHashtags(tweet) :
    """
    If properly included, get the hashtags attached to this tweet
    :param tweet: Python dict containing a Twitter tweet object 
    :return: List of hashtags
    """
    hashtags = []
    if 'entities' in tweet and \
    tweet['entities'] is not None and \
    'hashtags' in tweet['entities'] :
        for hashtag in tweet['entities']['hashtags'] :
            if 'text' in hashtag and\
            hashtag['text'] is not None :
                hashtags.append(hashtag['text'])
    return hashtags

def getSource(tweet) :
    """
    If properly included, get Twitter client used to create this tweet
    :param tweet: Python dict containing a Twitter tweet object 
    :return: The string uniquely identifying the Twitter client used to create this tweet 
    """
    if 'source' in tweet :
        return tweet['source']
    else :
        return None

def getTimeStamp(tweet) :
    """
    If properly included, get the timestamp from the tweet from the 'created_at' field as a datetime object
    :param tweet: Python dict containing a Twitter tweet object
    :return: datetime object
    """
    
    if 'created_at' in tweet and tweet['created_at'] is not None :
        try :
            timestamp = dt.datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=pytz.timezone('UTC'))
            
            return timestamp.astimezone(pytz.timezone('UTC'))
        except ValueError :
            return None
    else :
        return None