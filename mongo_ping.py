from pymongo.mongo_client import MongoClient
import os
import urllib.parse

if os.getenv("JOBFLOW_JOB_STORE__DOCS_STORE__PORT"):
    port_string = f":{os.getenv("JOBFLOW_JOB_STORE__DOCS_STORE__PORT")}"
else:
    port_string = ""

uri =  "mongodb://nscc-atomate2-kna-db-user:izUdNsZhU0lrYdTJHk9e80sGS@" + \
       urllib.parse.quote_plus(os.getenv("JOBFLOW_JOB_STORE__DOCS_STORE__HOST")) + \
       port_string + \
       "/nscc-atomate2-kna-db?directConnection=true&serverSelectionTimeoutMS=5000"

print("Initializing MongoDB client...")
client = MongoClient(uri)

print("Sending a ping to confirm a successful connection...")
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")
