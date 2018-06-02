import pytz
import datetime as dt

def getTweetID(tweet):
    """
    If properly included, return the tweet ID
    :param tweet: Python dict containing a Twitter tweet object
    :return: Tweet ID 
    """
    if 'id' in tweet and \
    tweet['id'] is not None :
        return tweet['id']
    else :
        return None

def getUserID(tweet):
    """
    If properly included, return the ID of the user who sent this tweet.
    :param tweet: Tweet object
    :return: User ID
    """
    if 'user' in tweet and \
    tweet['user'] is not None and \
    'id' in tweet['user'] and \
    tweet['user']['id'] is not None :
        return tweet['user']['id']
    else :
        return None

def getTweets(response):
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

def getDate(tweet):
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

def getScreenName(tweet):
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

def getTweetUserLocation(tweet):
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

def getClockOffset(tweet):
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

def getTimezone(tweet):
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

def getTweetText(tweet):
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

def getHashtags(tweet):
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

def getSource(tweet):
    """
    If properly included, get Twitter client used to create this tweet
    :param tweet: Python dict containing a Twitter tweet object 
    :return: The string uniquely identifying the Twitter client used to create this tweet 
    """
    if 'source' in tweet :
        return tweet['source']
    else :
        return None

def read_timestamp(timestamp_string):
    """
    Parse a timestamp string into a datetime object
    :param timestamp_string: 
    :return: 
    """
    try :
        timestamp = dt.datetime.strptime(timestamp_string, '%a %b %d %H:%M:%S +0000 %Y').replace(
            tzinfo=pytz.timezone('UTC'))
        
        return timestamp.astimezone(pytz.timezone('UTC'))
    except ValueError :
        return None

def getTimeStamp(tweet):
    """
    If properly included, get the timestamp from the tweet from the 'created_at' field as a datetime object
    :param tweet: Python dict containing a Twitter tweet object
    :return: datetime object
    """
    
    if 'created_at' in tweet and tweet['created_at'] is not None :
        return read_timestamp(tweet['created_at'])
    else :
        return None

def getRetweetID(tweet):
    """
    If properly included, get the original author's ID for a retweet
    :param tweet: Tweet object
    :return: User ID
    """
    if 'retweeted_status' in tweet and \
            tweet['retweeted_status'] is not None and \
            'user' in tweet['retweeted_status'] and \
            tweet['retweeted_status']['user'] is not None and \
            'id' in tweet['retweeted_status']['user'] and \
            tweet['retweeted_status']['user']['id'] is not None :
        return tweet['retweeted_status']['user']['id']
    else :
        return None
    
def getReplyID(tweet):
    """
    Get the users this tweet is replying to
    :param tweet: Tweet object
    :return: User ID
    """
    if 'in_reply_to_user_id' in tweet and \
            tweet['in_reply_to_user_id'] is not None :
        return tweet['in_reply_to_user_id']
    else :
        return None

def getQuotedUserID(tweet):
    """
    If properly included, return the ID of the user quoted in a quote retweet.
    :param tweet: Tweet object
    :return: User ID
    """
    if 'quoted_status' in tweet and \
            tweet['quoted_status'] is not None and \
            'user' in tweet['quoted_status'] and \
            tweet['quoted_status']['user'] is not None and \
            'id' in tweet['quoted_status']['user'] and \
            tweet['quoted_status']['user']['id'] is not None :
        return tweet['quoted_status']['user']['id']
    else :
        return None

def getUserMentions(tweet):
    """
    If properly included, get all users mentioned in this tweet
    :param tweet: Tweet object
    :return: Set of user IDs
    """
    mentions = set()
    if 'entities' in tweet and \
            tweet['entities'] is not None and \
            'user_mentions' in tweet['entities'] :
        for mention in tweet['entities']['user_mentions'] :
            if 'id' in mention and \
                    mention['id'] is not None :
                mentions.add(mention['id'])
    return mentions


def getRetweetTuple(tweet) :
    """
    If properly included, get the original author's ID for a retweet
    :param tweet: Tweet object
    :return: User ID
    """
    if 'retweeted_status' in tweet and \
            tweet['retweeted_status'] is not None and \
            'user' in tweet['retweeted_status'] and \
            tweet['retweeted_status']['user'] is not None and \
            'id' in tweet['retweeted_status']['user'] and \
            tweet['retweeted_status']['user']['id'] is not None and \
            'screen_name' in tweet['retweeted_status']['user'] and \
            tweet['retweeted_status']['user']['screen_name'] is not None:
        return (tweet['retweeted_status']['user']['id'],
                tweet['retweeted_status']['user']['screen_name'])
    else :
        return None


def getReplyTuple(tweet) :
    """
    Get the users this tweet is replying to
    :param tweet: Tweet object
    :return: User ID
    """
    if 'in_reply_to_user_id' in tweet and \
            tweet['in_reply_to_user_id'] is not None and \
            'in_reply_to_screen_name' in tweet and \
            tweet['in_reply_to_screen_name'] is not None:
        return (tweet['in_reply_to_user_id'],
                tweet['in_reply_to_screen_name'])
    else :
        return None


def getQuotedUserTuple(tweet) :
    """
    If properly included, return the ID of the user quoted in a quote retweet.
    :param tweet: Tweet object
    :return: User ID
    """
    if 'quoted_status' in tweet and \
            tweet['quoted_status'] is not None and \
            'user' in tweet['quoted_status'] and \
            tweet['quoted_status']['user'] is not None and \
            'id' in tweet['quoted_status']['user'] and \
            tweet['quoted_status']['user']['id'] is not None and \
            'screen_name' in tweet['quoted_status']['user'] and \
            tweet['quoted_status']['user']['screen_name'] is not None:
        return (tweet['quoted_status']['user']['id'],
                tweet['quoted_status']['user']['screen_name'])
    else :
        return None


def getUserMentionTuples(tweet) :
    """
    If properly included, get all users mentioned in this tweet
    :param tweet: Tweet object
    :return: Set of user IDs
    """
    mentions = set()
    if 'entities' in tweet and \
            tweet['entities'] is not None and \
            'user_mentions' in tweet['entities'] :
        for mention in tweet['entities']['user_mentions'] :
            if 'id' in mention and \
                    mention['id'] is not None and \
                    'screen_name' in mention and \
                    mention['screen_name'] is not None:
                mentions.add((mention['id'],
                              mention['screen_name']))
    return mentions
