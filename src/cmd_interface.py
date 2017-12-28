import cmd
import time, sys
import threading
from run_job import Job
from job_mgr import Dispatcher

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
              'ex: \'start my_job\' to start the job file jobs/my_job.txt\n'
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
              'ex: \'status my_job\' to check on the job defined in jobs/my_job.txt')
        
    def do_list(self, arg):
        print('Not yet implemented.')
    def help_list(self):
        print('The functionality to list all available jobs and their status is not yet complete.')
    
    def do_delete(self, arg):
        print('Not yet implemented')
    def help_delete(self):
        print('The functionality to remove inactive jobs from the list is not yet complete.')
    

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
        
