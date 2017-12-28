# Ornitholog
Twitter data acquisition and archiving tool

```
Ornitholog
  /creds
  /data
  /jobs
  /logs
  /src
```

## Getting Started

### Set up Twitter API credentials:
Go to [https://apps.twitter.com], click `Create New App`
1. Create a text file in `Ornitholog/creds`, I'll refer to this as your `<creds_file>`
2. Give your application a unique name, copy this to LINE 1 of your `<creds_file>`
3. In the `Permissions` tab of your app, set the permissions to `Read-Only`; Ornitholog does not need write access.
4. In the `Keys and Access Tokens` tab, now copy the `Consumer Key (API Key)` to LINE 2 of your `<creds_file>`
5. In the `Keys and Access Tokens` tab, now copy the `Consumer Secret (API Secret)` to LINE 3 of your `<creds_file>`
6. Under `Application Actions` in `Keys and Access Tokens`, click `Generate Consumer Key and Secret`
7. In the `Keys and Access Tokens` tab, now copy the `Access Token` to LINE 4 of your `<creds_file>`
8. In the `Keys and Access Tokens` tab, now copy the `Access Token Secret` to LINE 5 of your `<creds_file>`
* Remember to edit your job to contain the name of your `<creds_file>`!


**Note:**  
None of the keys or tokens should contain spaces or line-breaks!



### Create a Job:
A `Job` is a JSON file defining the parameters for a certain Twitter collection. Read the comments in `src/run_job.py` for full instructions on what you can do to define a job. For your convenience, a sample job has been included in `Ornitholog/jobs/sample_job.json`  

In the `credfile` field, add the filename of your `<creds_file>`. Ornitholog will look for this file in `Ornitholog/creds/` when it tries to access the Twitter API.


### Run Ornitholog:
Navigate to `Ornitholog/src` and run:  
`python Ornitholog.py`

To begin collection, try `start sample_job`. You can type `?` into the terminal for help, or `help <cmd>` to get help for a specific command, `<cmd>`.


## Defining a Collection Job

A collection job, or `Job`, is a JSON file that tells Ornitholog what kind of data you want to collect and how. Ornitholog doesn't change this file at runtime, but you can update the `Job` without exiting Ornitholog by making changes to the `Job` file in your favorite text editor and then reissuing the `Job` to Ornitholog using the `start <Job>` command, where `<Job>` is the name of your job file (minus the '.json' extension). A `Job` file contains some mandatory entries, which must be included for data collection to succeed, and some optional entries, which give you finer control over some of the ways a `Job` works.

### Mandatory Fields
#### keywords
List containing strings of case-insensitive search terms to be OR'd together. Words in the same string must occur together and in that order. To specify that a keyword *must* occur, prefix that keyword with a `+`. For instance, the keyword list:
```
"keywords" : [
	"climate",
	"change"
]
```
Will collect any tweet that contains either word. If you want both words to appear, you would use:
```
"keywords" : [
	"+climate",
	"+change"
]
```
If you only want the exact phrase "climate change", you would use:
```
"keywords" : [
	"climate change"
]
```
**Note:** The first example will include all tweets that the second and third examples would collect. The second example would include all tweets that the third example would collect.

#### path
```
"path" : "data/sample_job"
```
The directory to store data collected. If it does not exist, Ornitholog will attempt to create it. If you wish to change this directory after collection has begun, you must move all files *and* edit the JSON job file to reflect the new path. It is *highly inadvisable* to move a `Job` while collection on that `Job` is still running, and may result in a corrupted archive index or lost data.

#### credfile
```
"credfile" : "test_creds.txt"
```
The file in `creds/` containing the credentials you wisht o use for this collection job. This should be a text file with the keys stored one-per-line, ordered as:
```
<Application Name>
<Consumer Key>
<Consumer Secret>
<Access Token>
<Access Secret>
```
If the `<Application Name>` entry is included incorrectly, you will be unable to use `app_auth` to connect to the Twitter API, and will instead have to use the lower, user-auth rate-limit in collecting data. Furthermore, for `app_auth` to succeed, the `Access Token` and `Access Secret` must belong to the application's owner.    
**Note:** None of these entries should contain spaces or line-breaks.  

### Optional Entries
#### langs
```
"langs" : [
	"en",
	"fr"
]
```
List of language-code strings to search, per Twitter API. If none are included, *all* languages will be considered! If the entire field is omitted, the language defaults to `en`.

#### max_taj_size
```
"max_taj_size" : 400
```
The (approximate) maximum size (MB) a single file of tweets can grow to before it is segmented. (Default: 400MB)

#### app_auth
```
"app_auth" : true
```
Use application-only authentication to collect data. This nearly triples the rate-limit for collection, but can only be used concurrently once per-application, whereas regular auth can be used once per-user per-app concurrently.

#### streaming_api
```
"streaming_api" : false
``` 
Use Twitter's Streaming API to collect tweets instead of the REST API. This is a *massively* powerful tool and can collect up to 1% of Twitter's entire volume, which means it will usually capture *all* traffic for a given query. It is important to remember, however, that *only one streaming endpoint can be opened concurrently per user account!* That means if the same user tries to open streaming endpoints from a second application, the first application's collection will be interrupted. (**Note:** This collection interface is not yet implemented.)


### Using the Ornitholog terminal
Once you've added your credentials to a file and created a `Job`, you're ready to run `Ornitholog.py`. After a brief startup sequence, this will land you at a command terminal. Here you can start and stop jobs, check on the status of your jobs, or politely ask Ornitholog to end collection and exit. The command `?` will bring up the help menu, which lists all available commands. Typing `help <cmd>` will give instructions for using a specific command.

#### Job States
In the Ornitholog terminal, you can type `status <job_name>` to check on a `Job`. It's probably `RUNNING` if you started it, `NOT_ACTIVE` if you haven't done anything with it, or `STOPPED` if you issued the `stop <job_name>` command. You might catch it in a transitional state such as `ISSUED` or `STOPPING`, which respectively indicate that the job is still preparing to collect data or that it is still in the process of ending its collection. If your `Job` is in a transitional state for more than a few seconds, something is probably wrong.

## Required Libraries
Ornitholog requires Python 3.6+ and the `rauth` library to run. If you don't have `rauth`, you can acquire it by running `python -m pip install rauth` from the system shell. Additional dependencies may become necessary as development continues and additional features are added. (For instance, to export user-interaction graphs to gephi or import information to a SQL database.)


