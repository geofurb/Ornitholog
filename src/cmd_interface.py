import cmd
import time, sys
import threading
import json
from arx_mgr import scan_tweets
from run_job import Job
from job_mgr import Dispatcher

# Import NetworkX if available, for user interaction graph export
try:
    import networkx as nx
    import twitter_graph
except:
    nx = None

class TestCmd(cmd.Cmd):
    
    intro = 'Welcome to Ornitholog data acquisition tool for Twitter. Try \'?\' for help'
    prompt = ': '
    use_rawinput = False
    
    def __init__(self, **kwargs):
        self.dispatcher = None
        kwargs.setdefault('stdin', None)
        kwargs.setdefault('stdout', None)
        super(TestCmd, self).__init__(completekey='tab', **kwargs)
        
    
    def do_quit(self, arg):
        if len(self.dispatcher.getActiveJobs()) > 0:
            print('QUITTING WILL TERMINATE ALL ACTIVE JOBS!!\n'
                     'There are currently',len(self.dispatcher.getActiveJobs()),'jobs still running.')
        conf = input('Really quit? (y/n) ')
        if conf.strip().lower() == 'y':
            if len(self.dispatcher.getActiveJobs()) > 0:
                print('Ending all collection threads...')
                for job in self.dispatcher.getJobs():
                    self.dispatcher.setJobStatus(job,Job.STOPPING)
                self.dispatcher.ex.shutdown(wait=True)
                time.sleep(0.1)
                sys.exit("Ornitholog was terminated by user command.")
            else:
                self.dispatcher.ex.shutdown(wait=True)
                time.sleep(0.1)
                sys.exit("Ornitholog was terminated by user command.")

    def help_quit(self):
        print('Exit Ornitholog, stopping all data collection.')
    
    def do_start(self, arg):
        if len(arg.strip()) == 0 :
            self.onecmd('help start')
        elif arg.lower() == '--all' :
            print('Starting all jobs is not currently implemented.')
        else:
            print('Starting', arg)
            self.dispatcher.pushRequest(arg)
    def help_start(self):
        print('Start a collection job defined by the supplied job file.\n'
              'ex: \'start my_job\' to start the job file jobs/my_job.json\n'
              'Use \'start --all\' to automatically execute all jobs in /jobs')
    
    def do_stop(self, arg):
        if len(arg.strip()) == 0 :
            self.onecmd('help stop')
        elif arg.lower() == '--all' :
            conf = input('This will stop ALL jobs! Are you sure? (y/n) ')
            if conf.strip().lower() == 'y' :
                print('All jobs are being terminated!')
                for job in self.dispatcher.getJobs():
                    self.dispatcher.setJobStatus(job,Job.STOPPING)
        else :
            self.dispatcher.setJobStatus(arg,Job.STOPPING)
            print('Stopping',arg)
            time.sleep(0.1)
    def help_stop(self):
        print('Stop a collection job already running. The \'--all\' flag stops all active jobs.')
        
    def do_status(self, arg):
        if len(arg.strip()) == 0 :
            self.onecmd('help status')
        elif arg.lower() == '--all':
            for job in sorted(self.dispatcher.getJobs()):
                print(job,'is',self.dispatcher.getJobStatus(job).name)
        else:
            print(arg,'is',self.dispatcher.getJobStatus(arg).name)
    def help_status(self):
        print('Return the status of an active job.\n'
              'ex: \'status my_job\' to check on the job defined in jobs/my_job.json')
        
    def do_list(self, arg):
        print('Not yet implemented.')
    def help_list(self):
        print('The functionality to list all available jobs and their status is not yet complete.')
    
    def do_delete(self, arg):
        print('Not yet implemented')
    def help_delete(self):
        print('The functionality to remove inactive jobs from the list is not yet complete.')
    
    def do_exportgraph(self, arg):
        
        # Make sure the user has NetworkX installed
        if nx is None:
            print('NetworkX library is required for this feature.')
            return
        
        # Initialize filename and flags to default values
        job = None; single_file = False; outfile = None
        min_id = None; max_id = None
        min_date = None; max_date = None
        undirected = False; multigraph = False
        replies = True; repl_explicit = False
        mentions = False; retweets = False; quotes = False
        
        # Scan filename and flags from the user input
        try:
            params = arg.strip()
            
            # Get the job or filename
            if params[0] == '"':
                end = params.find('"',start=1)+1
                job = params[:end]
            elif params[0] == "'":
                end = params.find("'",start=1)+1
                job = params[:end]
            else:
                job = params.split()[0]
            params = params[len(job):].strip()  # Remove the file/job name

            # Get the output filename
            if len(params) > 0 and params[0] != '-':
                if params[0] == '"' :
                    end = params.find('"', start=1) + 1
                    outfile = params[:end]
                elif params[0] == "'" :
                    end = params.find("'", start=1) + 1
                    outfile = params[:end]
                else :
                    outfile = params.split()[0]
                params = params[len(outfile):]  # Remove the output filename
            else:
                outfile = 'data/graph.gml'
                params = ' ' + params

            # Get the flags
            flags = params.split(' -')      # Split the remaining string into flags
            flags.pop(0)                    # Pop the leading empty string from the list of flags
            for flag in flags:              # Iterate through flags
                # Check multi-character flags
                if flag[0] == '-' and len(flag) > 1:
                    flag = flag[1:]
                    if flag.lower() == 'singlefile':
                        single_file = True
                    elif flag.split()[0].lower() == 'date':
                        bounds = flag.split()[1].split(':')
                        try:
                            min_date = int(bounds[0])
                        except:
                            pass
                        try:
                            max_date = int(bounds[1])
                        except:
                            pass
                    elif flag.split()[0].lower() == 'index':
                        bounds = flag.split()[1].split(':')
                        try :
                            min_id = int(bounds[0])
                        except :
                            pass
                        try :
                            max_id = int(bounds[1])
                        except :
                            pass
                # Check single-character flags
                else:
                    if 'U' in flag: undirected = True
                    if 'M' in flag: multigraph = True
                    if 'r' in flag: repl_explicit = True
                    if 'm' in flag: mentions = True
                    if 't' in flag: retweets = True
                    if 'q' in flag: quotes = True
                    
            # Check if user didn't want replies included
            if (mentions or retweets or quotes) and not repl_explicit: replies = False
            
        except:
            print('Syntax error in exportgraph request; check your entry.')
            raise
        
        try:
            if len(job) > 4 and job[-4:].lower() == '.arx' and '/' in job:
                job = {'path':job[0:job.rfind('/')]}
            elif len(job) > 4 and job[-4:].lower() == '.arx' and '\\' in job:
                job = {'path':job[0:job.rfind('\\')]}
            elif not single_file:
                with open('jobs/' + job + '.json') as jobfile :
                    job = json.load(jobfile)
        except:
            print('Unable to load specified job!')
            return
        
        # Iterate through tweets to build the graph
        tweetgen = scan_tweets(job, min_id, max_id, min_date, max_date)
        graph = twitter_graph.build_graph(tweetgen, not undirected, multigraph, replies, mentions, retweets, quotes)
        
        # Write the graph to file
        nx.write_gml(graph, outfile)
    def help_exportgraph(self):
        print('Build and export the user interaction graph of a specified job or index.arx'+
              '\nfile. If no output file is specified, the graph is saved to data/graph.gml.'+
              '\nSyntax:'+
              '\nexportgraph <jobname> <output file> [options]'+
              '\n\nAlternatively, any file containing one tweet JSON object per line can be'+
              '\nused with the "--singlefile" option.'+
              '\n\nSpecify the parameters for creating the graph using:'+
              '\n\t--index min:max\t to specify a minimum and maximum tweet ID when building'+
              '\n\t\t\t\t\t the graph (omit a min or max bound to include all tweets'+
              '\n\t\t\t\t\t before/after that index)'+
              '\n\t--date min:max\t to specify a minimum and maximum (local) POSIX time for'+
              '\n\t\t\t\t\t tweets to be included (omit a min or max bound to include'+
              '\n\t\t\t\t\t all tweets before/after that date)'+
              '\n\t-U\t to generate an undirected graph'+
              '\n\t-M\t to generate one edge per interaction instead of weighting edges by the'+
              '\n\t\t # of repeated interactions'+
              '\n\t-r\t to include Replies in user interactions (this is the default if no'+
              '\n\t\t other option is specified)'+
              '\n\t-m\t to include mentions in user interactions'+
              '\n\t-t\t to include reTweets in user interactions'+
              '\n\t-q\t to include quoted tweets in user interactions.'+
              '\n\nExample:\nexportgraph "C:\\Twitter Data\\tweets.json" C:\\tweetgraph.gml --singlefile --date\n 1525132800: -rmU\n')

class Commander(threading.Thread):
    """
    Easy interface for controlling Ornitholog via terminal. Starting this thread automatically creates a work
    dispatcher and attaches it to a command terminal on stdin+stdout.
    """
    
    
    def __init__(self,**kwargs):
        # Superclass constructor
        threading.Thread.__init__(self,name='CmdTerminal',**kwargs)
        
        # Create a dispatcher, attach it to a terminal so the user can control it
        print('Preparing terminal...')
        self.terminal = TestCmd()
        print('Creating dispatcher...')
        self.terminal.dispatcher = Dispatcher(name='Dispatcher')
        self.terminal.dispatcher.daemon = True
        print('System ready.\n')
    
    def run(self):
        # Initialize the dispatcher and its respective terminal for user-input.
        self.terminal.dispatcher.start()
        self.terminal.cmdloop()
        
