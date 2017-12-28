
# If properly included, return the tweet ID
def getTweetID(tweet) :
    if 'id' in tweet and \
    tweet['id'] is not None :
        return tweet['id']
    else :
        return None

# Extract the tweets from a given query
def getTweets(response) :
    """
    Get the tweets contained in an API response.
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

# If properly included, return the date of the tweet's creation
def getDate(tweet) :
    if 'created_at' in tweet and \
    tweet['created_at'] is not None :
        return tweet['created_at']
    else :
        return None

# If properly included, return the tweeter's screen name
def getScreenName(tweet) :
    if 'user' in tweet and \
            tweet['user'] is not None and \
            'screen_name' in tweet['user'] and \
            tweet['user']['screen_name'] is not None :
        return tweet['user']['screen_name']
    else :
        return None

# Get the user's self-supplied location from their user profile entity in this tweet
def getTweetUserLocation(tweet) :
    """ If included, read the user from the tweet and return their self-supplied location"""
    
    if 'user' in tweet and \
            tweet['user'] is not None and \
            'location' in tweet['user'] :
        return tweet['user']['location']
    else :
        return None

# Get UTC clock offset
def getClockOffset(tweet) :
    # Check to see if time-zone info is available
    if 'user' in tweet and \
        tweet['user'] is not None and \
        'utc_offset' in tweet['user'] and \
        tweet['user']['utc_offset'] is not None :
        return tweet['user']['utc_offset']
    else :
        return None

# Get user time zone
def getTimezone(tweet) :
    # Check to see if time-zone info is available
    if 'user' in tweet and \
        tweet['user'] is not None and \
        'time_zone' in tweet['user'] and \
        tweet['user']['time_zone'] is not None :
        return tweet['user']['time_zone']
    else :
        return None

# If properly included, return the tweet text
def getTweetText(tweet) :
    if 'text' in tweet and \
    tweet['text'] is not None :
        return tweet['text']
    else :
        return None

# If properly included, get the hashtags
def getHashtags(tweet) :
    hashtags = []
    if 'entities' in tweet and \
    tweet['entities'] is not None and \
    'hashtags' in tweet['entities'] :
        for hashtag in tweet['entities']['hashtags'] :
            if 'text' in hashtag and\
            hashtag['text'] is not None :
                hashtags.append(hashtag['text'])
    return hashtags

# If properly included, get Twitter client used to create this tweet
def getSource(tweet) :
    if 'source' in tweet :
        return tweet['source']
    else :
        return None

