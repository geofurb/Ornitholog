import time
import networkx as nx
from tweet_parser import *


def build_graph(tweetgen, directed=True, multigraph=False, replies=True, mentions=False, retweets=False, quotes=False):
    
    # Initialize the appropriate graph type
    g = nx.Graph()
    if directed:
        if multigraph:
            g = nx.MultiDiGraph()
        else:
            g = nx.DiGraph()
    elif multigraph:
        g = nx.MultiGraph()
    
    # Iterate over tweets to build the user interaction graph
    for tweet in tweetgen:
        
        # Get the ID of the user and each connection
        source = (getUserID(tweet), getScreenName(tweet))
        if source is None : continue    # If the user isn't valid, we can't add connections
        sinks = set()
        if replies:
            rID = getReplyTuple(tweet)
            if rID is not None : sinks.add(rID)
        if mentions:
            mIDs = getUserMentionTuples(tweet)
            if mIDs is not None : sinks.update(mIDs)
        if retweets:
            rID = getRetweetTuple(tweet)
            if rID is not None : sinks.add(rID)
        if quotes:
            qID = getQuotedUserTuple(tweet)
            if qID is not None : sinks.add(qID)
        sinks.discard(source)
        
        if multigraph:
            tweet_id = getTweetID(tweet)
            timestamp = time.mktime(getTimeStamp(tweet).timetuple())
        else:
            tweet_id = None
            timestamp = None
        
        # Iterate over connections to populate the graph
        for sink in sinks:
            if multigraph:
                tweet_id = getTweetID(tweet)
                # Add a new edge, attach Tweet ID as key and POSIX timestamp as an edge property
                g.add_edge(source[0], sink[0], key=tweet_id, timestamp=timestamp)
                pass
            else:
                # Add weight to an existing edge if possible, otherwise add an edge
                if g.has_edge(source[0], sink[0]):
                    g.edges[source[0], sink[0]]['weight'] += 1
                else:
                    g.add_edge(source[0], sink[0])
                    g.edges[source[0], sink[0]]['weight'] = 1
            g.node[sink[0]]['handle'] = sink[1]
        if g.has_node(source[0]) : g.node[source[0]]['handle'] = source[1]
            
    return g

