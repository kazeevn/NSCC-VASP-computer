from pymongo.mongo_client import MongoClient
import os
import urllib.parse
from jobflow import SETTINGS

print("Initializing MongoDB client...")
client = MongoClient(
    host=SETTINGS.JOB_STORE.docs_store.host,
    port=SETTINGS.JOB_STORE.docs_store.port)
print(client)
print("Sending a ping to confirm a successful connection...")
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")
