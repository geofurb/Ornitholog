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

## Contents:
* [Required Libraries](https://github.com/geofurb/Ornitholog#required-libraries)  
* [Getting Started](https://github.com/geofurb/Ornitholog#getting-started)  
* [Defining a Collection Job](https://github.com/geofurb/Ornitholog#defining-a-collection-job)  
* [Using the Ornitholog terminal](https://github.com/geofurb/Ornitholog#using-the-ornitholog-terminal)  
* [The Archive Format](https://github.com/geofurb/Ornitholog#the-archive-format)  

## Required Libraries
Ornitholog requires Python 3.6+ with the `rauth` and `pytz` libraries to run. If you don't have `rauth` or `pytz`, you can acquire it by running `python -m pip install rauth` and `python -m pip install pytz` from the system shell. Additional dependencies may become necessary as development continues and additional features are added. (For instance, to export user-interaction graphs to gephi or import information to a SQL database.)

## Getting Started
To start using Ornitholog, you're going to have to [create a set of credentials](https://github.com/geofurb/Ornitholog#set-up-twitter-api-credentials) for using the Twitter API, save these to a file that Ornitholog can read, [define a `Job`](https://github.com/geofurb/Ornitholog#create-a-job) JSON file to tell Ornitholog what you want it to collect and how, and finally [run the collection](https://github.com/geofurb/Ornitholog#run-ornitholog) itself. This quick intro will walk you through those steps to make the first time easier.

### Set up Twitter API credentials:
Go to [apps.twitter.com](https://apps.twitter.com), and click `Create New App`
1. Create a text file in `Ornitholog/creds`, I'll refer to this as your `<creds_file>`
2. Give your application a unique name, copy this to `LINE 1` of your `<creds_file>`
3. In the `Permissions` tab of your app, set the permissions to `Read-Only`; Ornitholog does not need write access.
4. In the `Keys and Access Tokens` tab, now copy the `Consumer Key (API Key)` to `LINE 2` of your `<creds_file>`
5. In the `Keys and Access Tokens` tab, now copy the `Consumer Secret (API Secret)` to `LINE 3` of your `<creds_file>`
6. Under `Application Actions` in `Keys and Access Tokens`, click `Generate Consumer Key and Secret`
7. In the `Keys and Access Tokens` tab, now copy the `Access Token` to `LINE 4` of your `<creds_file>`
8. In the `Keys and Access Tokens` tab, now copy the `Access Token Secret` to `LINE 5` of your `<creds_file>`
* Remember to edit your `Job` to contain the name of your `<creds_file>`!


**Note:** None of the keys or tokens should contain spaces or line-breaks.



### Create a Job:
A `Job` is a JSON file defining the parameters for a certain Twitter collection. Read the [Defining a Collection Job](https://github.com/geofurb/Ornitholog#defining-a-collection-job) section for full instructions on what you can do. For your convenience, a sample job has been included in `Ornitholog/jobs/sample_job.json`  

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
will collect any tweet that contains either word. If you only want tweets where both words appear, use:
```
"keywords" : [
	"+climate",
	"+change"
]
```
If you only want the exact phrase "climate change", use:
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
The (approximate) maximum size (MB) a single file of tweets can grow to before it is segmented. (Default: 400MB) If you want to the entire archive in one big file, that can be accomplished using something like
```
"max_taj_size" : 999999999
```
but keep an eye on your disk usage, or Ornitholog might eat up every last bit!

#### app_auth
```
"app_auth" : true
```
Use application-only authentication to collect data. This nearly triples the rate-limit for collection, but can only be used concurrently once per-application, whereas regular auth can be used once per-user per-app concurrently.

#### streaming_api
```
"streaming_api" : false
``` 
Use Twitter's Streaming API to collect tweets instead of the REST API. This is a *massively* powerful tool and can collect up to 1% of Twitter's entire volume, which means it will usually capture *all* traffic for a given query. It is important to remember, however, that *only one streaming endpoint can be opened concurrently per user account!* That means if the same user tries to open streaming endpoints from a second application, the first application's collection will be interrupted.  
**Note:** This collection interface is not yet implemented.


## Using the Ornitholog terminal
Once you've added your credentials to a file and created a `Job`, you're ready to run `Ornitholog.py`. After a brief startup sequence, this will land you at a command terminal. Here you can start and stop jobs, check on the status of your jobs, or politely ask Ornitholog to end collection and exit. The command `?` will bring up the help menu, which lists all available commands. Typing `help <cmd>` will give instructions for using a specific command.

### Job States
In the Ornitholog terminal, you can type `status <job_name>` to check on a `Job`. It's probably `RUNNING` if you started it, `NOT_ACTIVE` if you haven't done anything with it, or `STOPPED` if you issued the `stop <job_name>` command. You might catch it in a transitional state such as `ISSUED` or `STOPPING`, which respectively indicate that the job is still preparing to collect data or that it is still in the process of ending its collection. If your `Job` is in a transitional state for more than a few seconds, something is probably wrong.

## The Archive Format

Ornitholog creates a separate directory for each job, and stores tweets in that directory. You will find two kinds of files in this directory: `index.arx` and `*.taj` files.

### The Archive Index (ARX) File
The Archive Index (ARX) file is always named `index.arx`, and contains metadata for each TAJ file to efficiently keep track of what data is stored where. The benefits here are many-fold:
* Tweets can be stored in individual chunks in case the archive grows too large for a single disk  
* Finished TAJ files can be compressed to save space, then individually decompressed later when you need to parse them  
* Chronological access to the entire archive can quickly be accomplished by navigating the ARX to find the appropriate TAJ before parsing tweets  

**Note:** For disk efficiency and chronological searching, Ornitholog's archive format is superb. However, its design makes it very tedious to further refine a query's search terms after collection, so it may be advisable to import the data into another format and index it for searching by keyword depending on your use-case.

### Tweet Archive JSON (TAJ) files
Ornitholog stores tweets as JSON-objects, one-per-line in Tweet Archive JSON (TAJ) files. There are two varieties of TAJ file:

Finished archives are named 'tweets-' + uuid4 + '.taj', where uuid4 is a unique hexadecimal identifier. Ornitholog does not need to edit these files anymore, and you can safely gzip them for long-term storage, or move them to another disk. (Be sure to move a copy of the ARX with them so that you can keep track of their ordering!) *Tweets in a finished file are ordered new-to-old.*  

Unfinished archives are named 'new-tweets-' + uuid4 + '.taj', where uuid4 is a unique hexadecimal identifier. You can't compress this file, since Ornitholog will need to scan it to update the ARX, and will eventually need to read the entire thing to create a finished file from it. *Tweets in the unfinished file are ordered old-to-new.*  

The reason for different ordering conventions in finished and unfinished files is to streamline later functionality, where Ornitholog will allow you to use the REST API to build finished archives further backwards in time and the Streaming API to collect tweets forward in time. Inserting into a finished file to fill the gaps may eventually be included, and would necessitate inserting a double line-break into the file wherever collection is interrupted to indicate possible missing tweets. Note that since the GET/Search function of the REST API only searches for tweets up to a week old, this functionality will necessarily be of limited utility except in capturing a recent event.

