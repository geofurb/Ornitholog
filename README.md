# Ornitholog

To use:

Create any missing directories:

Ornitholog

  /creds

  /data

  /jobs

  /logs
  
  /src

TO SET UP CREDENTIALS:

Go to https://apps.twitter.com, click "Create New App"

Create a text file in Ornitholog/creds, I'll refer to this as <creds_file>

Give your application a unique name, copy this to LINE 1 of your <creds_file>

In the "Permissions" tab of your app, set the permissions to Read-Only; Ornitholog does not need write access.

In the "Keys and Access Tokens" tab, now copy the "Consumer Key (API Key)" to LINE 2 of your <creds_file>

In the "Keys and Access Tokens" tab, now copy the "Consumer Secret (API Secret)" to LINE 3 of your <creds_file>

Under "Application Actions" in "Keys and Access Tokens", click "Generate Consumer Key and Secret"

In the "Keys and Access Tokens" tab, now copy the "Access Token" to LINE 4 of your <creds_file>

In the "Keys and Access Tokens" tab, now copy the "Access Token Secret" to LINE 5 of your <creds_file>


Note:

None of the keys or tokens should contain spaces or line-breaks!



TO CREATE A JOB:

A Job is a JSON file defining the parameters for a certain Twitter collection. Read the comments in src/run_job.py for full instructions on what you can do to define a job. For your convenience, a sample job has been included in Ornitholog/jobs/sample_job.json


RUN ORNITHOLOG:

Navigate to Ornitholog/src and run:

python Ornitholog.py

To begin collection, try "start sample_job"

You can type "?" into the terminal for help.
