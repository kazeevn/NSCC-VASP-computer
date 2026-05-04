from pymongo.mongo_client import MongoClient
from jobflow import SETTINGS

print("Initializing MongoDB client...")
client = MongoClient(
    host=SETTINGS.JOB_STORE.docs_store.host,
    port=SETTINGS.JOB_STORE.docs_store.port,
    username=SETTINGS.JOB_STORE.docs_store.username,
    password=SETTINGS.JOB_STORE.docs_store.password,
    authSource=SETTINGS.JOB_STORE.docs_store.auth_source,
    )
print(client)
print("Sending a ping to confirm a successful connection...")
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")
db = client.get_database(SETTINGS.JOB_STORE.docs_store.database)
doc_count = db[SETTINGS.JOB_STORE.docs_store.collection_name].count_documents({})
print(f"Document count: {doc_count}")